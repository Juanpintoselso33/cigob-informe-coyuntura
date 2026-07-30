"""Las fichas metodológicas públicas no pueden afirmar ponderaciones que el
índice ya no usa.

Las fichas de /metodologia dicen cosas como «Pertenece a la dimensión de
prospectivas de empleo (20% interno · 3% del ITVC)». Ese número es verdadero el
día que se escribe y queda mentiroso la próxima vez que entra un indicador a la
misma dimensión: los existentes ceden peso proporcionalmente y nadie vuelve al
texto. Cuando `empleo_registrado` entró con 35%, los cuatro componentes de
prospectivas de empleo cedieron ×0,65 y las cuatro fichas siguieron publicando
los pesos viejos.

Lo encontró una auditoría de UI (29-jul-2026) de casualidad, mirando el Índice
Líder: la ficha decía 20% interno · 3% del ITVC cuando el real era 13% · 1,95%.
Al medirlo en todas, había DOCE fichas con el peso stale, y varias además con el
nombre de la dimensión anterior a su reorganización («confianza y seguridad»,
que hoy son dos dimensiones distintas).

Ningún gate podía verlo: gate_calidad.py valida datos y estructura del snapshot,
nunca cruza la prosa de la capa de display contra los pesos que usa el motor.
Mismo hueco que cerró test_web_labels.py para los rótulos.

Qué NO se valida acá, a propósito:
  · las entradas de `cambios`, que son un changelog — dicen el peso que tenía el
    indicador ESE día y tienen que quedar como están;
  · las frases que citan el peso de la DIMENSIÓN («la dimensión de vulnerabilidad
    financiera (10% del ITVC), donde pesa 50%»), que son otra afirmación.
Sólo se cruza el par «N% interno · M% del ÍNDICE», que es la forma que se copió
y quedó vieja.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FICHAS = (ROOT / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
INFORME = json.loads((ROOT / "web/src/data/informe.json").read_text(encoding="utf-8-sig"))

TOLERANCIA_PP = 0.6      # el texto redondea; 0,6 pp deja pasar 3,15 vs 3,1


def _pesos_reales() -> dict:
    out = {}
    for c in INFORME["cinturones"].values():
        for sigla in ("itvc", "itcm", "itcg", "itcp"):
            idx = c.get(sigla)
            if not idx:
                continue
            for dv in (idx.get("dimensiones") or {}).values():
                for ikey, iv in (dv.get("indicadores") or {}).items():
                    out[ikey] = {"interno": (iv.get("peso") or 0) * 100,
                                 "efectivo": (iv.get("peso_efectivo") or 0) * 100}
    return out


def _incidencia_por_ficha() -> dict:
    """{clave: texto de incidenciaTexto}. Excluye `cambios` (changelog)."""
    out = {}
    for m in re.finditer(r"^  (\w+): \{$", FICHAS, re.M):
        fin = FICHAS.find("\n  },", m.end())
        cuerpo = FICHAS[m.end():fin]
        inc = re.search(r"incidenciaTexto:\s*\[(.*?)\]", cuerpo, re.S)
        if inc:
            out[m.group(1)] = inc.group(1)
    return out


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def test_los_pesos_que_afirman_las_fichas_son_los_vigentes():
    reales = _pesos_reales()
    problemas = []
    for clave, texto in _incidencia_por_ficha().items():
        real = reales.get(clave)
        if not real:
            continue
        mi = re.search(r"(\d+(?:,\d+)?)\s*%\s*interno", texto)
        if mi and abs(_num(mi.group(1)) - real["interno"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice {mi.group(1)}% interno, "
                             f"real {real['interno']:.1f}%")
        # sólo la forma "· M% del ÍNDICE", que acompaña al peso interno; la que
        # cita el peso de la dimensión tiene otra redacción y no se toca
        me = re.search(r"·\s*(\d+(?:,\d+)?)\s*%\s*del\s*(?:ITVC|ITCM|ITCG|ITCP)", texto)
        if me and abs(_num(me.group(1)) - real["efectivo"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice {me.group(1)}% del índice, "
                             f"real {real['efectivo']:.2f}%")
    assert not problemas, (
        "fichas públicas con ponderación stale (entró un indicador a la dimensión "
        "y los demás cedieron peso sin que se actualice el texto):\n  "
        + "\n  ".join(problemas))


def test_el_test_mira_algo():
    """Guarda contra que el parseo quede vacío y el test pase por no leer nada."""
    inc = _incidencia_por_ficha()
    reales = _pesos_reales()
    con_peso = [k for k, t in inc.items()
                if k in reales and re.search(r"\d+(?:,\d+)?\s*%\s*interno", t)]
    # Al 29-jul-2026: 32 fichas con incidenciaTexto, 12 de ellas declarando peso
    # interno — que son justo las 12 que estaban stale. Los pisos van por debajo
    # para no romper cada vez que se suma una ficha, pero lo bastante alto como
    # para que un parseo roto no pase inadvertido.
    assert len(inc) >= 28, f"sólo se parsearon {len(inc)} fichas: ¿cambió el formato?"
    assert len(con_peso) >= 10, f"sólo {len(con_peso)} fichas declaran peso interno"
