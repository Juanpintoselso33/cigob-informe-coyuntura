# -*- coding: utf-8 -*-
"""Las bandas que publican las fichas son las que usa el motor (ADR-0157).

EL HUECO QUE CIERRA. `test_fichas_pesos.py` cuida los PESOS que afirman las
fichas; las ANCLAS DE BANDA —los cortes y los puntajes con los que se traduce el
valor de un indicador a 0-100— no tenían nada. Son la misma clase de problema:
texto público escrito a mano que queda viejo cuando se recalibra, sin que falle
nada. Y este proyecto recalibra seguido: hay ADRs enteros dedicados a mover
anclas (0050, 0058/0059, 0061, 0063…).

Cada ficha declara sus bandas de una de dos maneras, y las dos se cruzan acá:

  1. el campo estructurado `anclas: { bandas: [{ banda: "≤ 1", puntaje: 100 }…] }`
  2. la frase «El puntaje del índice se asigna por bandas … → el más bajo.»

Se verifican dos cosas distintas: los PUNTAJES (que la ficha no invente una
escala que el motor no da) y los CORTES (que los números publicados sean los
umbrales reales). El orden no importa: varias fichas listan las bandas de peor a
mejor y el motor las tiene al revés.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcg  # noqa: E402
import itcm  # noqa: E402
import itcp  # noqa: E402

BANDAS = {}
for _mod, _attr in ((itcm, "BANDAS_ITCM"), (itcg, "BANDAS_ITCG"), (itcp, "BANDAS_ITCP")):
    BANDAS.update(getattr(_mod, _attr))

FICHAS_TXT = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")

ITEM = re.compile(r'\{\s*banda:\s*"([^"]+)"\s*,\s*puntaje:\s*(\d+)\s*\}')
FRASE = re.compile(r"El puntaje del índice se asigna por bandas[^\"]*?el más bajo\.")
# es-AR: el punto separa miles y la coma decimales ("15.000", "0,3")
NUM = re.compile(r"[+−-]?\d[\d.]*(?:,\d+)?")

# El ITVC no tiene bandas: promedia índices base-100 directamente (ADR-0018), así
# que sus fichas describen la escala de otra forma y no entran acá.


def _fichas() -> dict:
    out = {}
    for m in re.finditer(r"^  (\w+): \{$", FICHAS_TXT, re.M):
        fin = FICHAS_TXT.find("\n  },", m.end())
        out[m.group(1)] = FICHAS_TXT[m.end():fin]
    return out


def _num(s: str) -> float:
    s = s.replace("−", "-").lstrip("+").replace(".", "").replace(",", ".")
    return round(float(s), 4)


def _bandas_declaradas(cuerpo: str):
    """[(texto de la banda, puntaje)] del campo estructurado, o None."""
    m = re.search(r"anclas:\s*\{(.*?)\n    \}", cuerpo, re.S)
    if not m:
        return None
    items = ITEM.findall(m.group(1))
    return [(b, int(p)) for b, p in items] or None


def _cortes_motor(nombre: str) -> set:
    vals = set()
    for lo, hi, _ in BANDAS[nombre]:
        for x in (lo, hi):
            if abs(x) != float("inf"):
                vals.add(round(float(x), 4))
    return vals


def _con_bandas():
    """{indicador: cuerpo de su ficha} para los que puntúan por bandas."""
    return {k: v for k, v in _fichas().items() if k in BANDAS}


def test_los_puntajes_que_publican_las_fichas_son_los_del_motor():
    problemas = []
    for clave, cuerpo in _con_bandas().items():
        declaradas = _bandas_declaradas(cuerpo)
        if not declaradas:
            continue
        dichos = [p for _, p in declaradas]
        motor = [p for _, _, p in BANDAS[clave]]
        # el orden es indistinto: hay fichas que listan de peor a mejor
        if dichos != motor and dichos != list(reversed(motor)):
            problemas.append(f"{clave}: ficha {dichos} · motor {motor}")
    assert not problemas, (
        "fichas que publican una escala de puntajes que el motor no usa:\n  "
        + "\n  ".join(problemas)
    )


def test_los_cortes_que_publican_las_fichas_son_los_del_motor():
    problemas = []
    for clave, cuerpo in _con_bandas().items():
        declaradas = _bandas_declaradas(cuerpo)
        frase = FRASE.search(cuerpo)
        if not declaradas and not frase:
            continue
        dichos = set()
        for texto, _ in (declaradas or []):
            dichos.update(_num(x) for x in NUM.findall(texto))
        if frase:
            dichos.update(_num(x) for x in NUM.findall(frase.group(0)))
        faltan = _cortes_motor(clave) - dichos
        if faltan:
            problemas.append(f"{clave}: el motor corta en {sorted(faltan)} y la ficha "
                             f"no lo dice (publica {sorted(dichos)})")
    assert not problemas, (
        "anclas de banda stale: se recalibró el motor y el texto público quedó "
        "con los umbrales viejos.\n  " + "\n  ".join(problemas)
    )


def test_todo_indicador_con_bandas_y_ficha_declara_sus_bandas():
    """Si un indicador puntúa por bandas, su ficha tiene que decir cuáles: es la
    mitad de la explicación de por qué su puntaje es el que es."""
    mudos = [k for k, cuerpo in _con_bandas().items()
             if not _bandas_declaradas(cuerpo) and not FRASE.search(cuerpo)]
    assert not mudos, (
        f"fichas de indicadores que puntúan por bandas y no publican ninguna: {sorted(mudos)}"
    )


def test_el_test_mira_algo():
    """Contra el falso verde: si cambia el formato de fichas.ts y el parseo deja
    de encontrar bandas, los tres tests de arriba pasan vacíos."""
    con = _con_bandas()
    assert len(con) >= 40, f"sólo {len(con)} fichas cruzadas contra el motor; el parseo se rompió"
    declaradas = sum(1 for c in con.values() if _bandas_declaradas(c))
    assert declaradas >= 30, f"sólo {declaradas} fichas con `anclas.bandas` parseadas"
