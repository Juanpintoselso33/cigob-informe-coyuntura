"""La web declara pesos y pertenencias del ITCIS en prosa, a mano, y el motor
los calcula en `itvc.DIMENSIONES_ITVC`. Cuando una recalibración mueve un peso,
la prosa no se entera: nada la vincula al número.

Ya pasó, y quedó publicado durante semanas:

- `descripciones.ts` decía que `pobreza_nowcast` "se publica como contexto: no
  integra el índice" cuando pesa 9,31% desde ADR-0153 — y la ficha del MISMO
  indicador, en `fichas.ts`, decía lo correcto. La web se desmentía a sí misma
  en dos archivos.
- `endeudamiento_familiar` e `indice_lider` seguían descritos como si
  puntuaran; salieron del índice en ADR-0154.
- La ficha de `brecha_salario_cbt` declaraba 17,06% en un párrafo y 22,75% en
  otro (el valor previo a ADR-0111/0153).

Ningún gate podía verlo: `gate_calidad.py` compara la card contra su serie, y
los tests de reconciliación comparan el snapshot consigo mismo. Nadie cruzaba
la PROSA contra la paramétrica. Este test hace eso.
"""
import bisect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc  # noqa: E402
from publicar import VIDA_OCULTOS  # noqa: E402

DESCRIPCIONES = (ROOT / "web" / "src" / "lib" / "descripciones.ts").read_text(encoding="utf-8")
FICHAS = (ROOT / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")

# {indicador: (peso interno, peso efectivo en el índice)}
PESOS = {
    ind: (interno, round(interno * dim["peso"] * 100, 2))
    for dim in itvc.DIMENSIONES_ITVC.values()
    for ind, interno in dim["indicadores"].items()
}


def _bloque(texto: str, clave: str) -> str:
    """El objeto literal de un indicador: desde `clave: {` hasta el `},` que lo
    cierra en la misma indentación. Alcanza para no cruzar de vecino."""
    m = re.search(rf"^(\s*){re.escape(clave)}: \{{$", texto, re.M)
    if not m:
        return ""
    fin = re.compile(rf"^{m.group(1)}\}},?$", re.M).search(texto, m.end())
    return texto[m.end():fin.start()] if fin else texto[m.end():]


@pytest.mark.parametrize("indicador", sorted(PESOS))
def test_lo_que_puntua_no_se_describe_como_contexto(indicador):
    bloque = _bloque(DESCRIPCIONES, indicador)
    if not bloque:
        pytest.skip(f"{indicador} no tiene entrada en descripciones.ts")
    for frase in ("no integra el índice", "se publica como contexto",
                  "NO puntúa", "no puntúa"):
        assert frase not in bloque, (
            f"descripciones.ts dice «{frase}» de {indicador}, que integra el "
            f"ITCIS con {PESOS[indicador][1]}% del índice."
        )


@pytest.mark.parametrize("indicador", sorted(VIDA_OCULTOS))
def test_lo_que_salio_del_indice_lo_dice(indicador):
    bloque = _bloque(DESCRIPCIONES, indicador)
    if not bloque:
        pytest.skip(f"{indicador} no tiene entrada en descripciones.ts")
    assert "NO puntúa" in bloque or "no puntúa" in bloque, (
        f"{indicador} salió del ITCIS (ADR-0154) y descripciones.ts no lo dice. "
        f"Si se describe sin aclararlo, se lee como componente."
    )
    assert "En el ITCIS puntúa" not in bloque, (
        f"descripciones.ts todavía afirma que {indicador} puntúa en el índice."
    )


def _declarados(texto: str) -> list[tuple[str, float]]:
    """Los porcentajes «X% del ITCIS» de fichas.ts, cada uno atribuido al
    indicador en cuyo bloque cae: el último `  clave: {` que lo precede."""
    claves = [(m.start(), m.group(1))
              for m in re.finditer(r"^  ([a-z_0-9]+): \{$", texto, re.M)]
    fuera = []
    # "del índice" tambien cuenta: la ficha de la brecha declaraba su peso así,
    # y así fue como se quedó con el valor previo a ADR-0111/0153. Los que
    # hablan de OTRO índice (los del ITCM) caen en claves que no están en
    # PESOS y el comparador los saltea.
    for m in re.finditer(r"([0-9]+,[0-9]+)% del (?:ITCIS|índice)", texto):
        i = bisect.bisect_right(claves, (m.start(), "\uffff")) - 1
        if i >= 0:
            fuera.append((claves[i][1], float(m.group(1).replace(",", "."))))
    return fuera


def test_las_fichas_declaran_el_peso_que_calcula_la_parametrica():
    malos = []
    for indicador, declarado in _declarados(FICHAS):
        esperado = PESOS.get(indicador, (None, None))[1]
        if esperado is None:
            continue
        # Tolerancia de un decimal: las fichas redondean a dos y a uno.
        if abs(declarado - esperado) > 0.06:
            malos.append(f"{indicador}: la ficha dice {declarado}%, "
                         f"la paramétrica da {esperado}%")
    assert not malos, "fichas.ts declara pesos que ya no son:\n  " + "\n  ".join(malos)


def test_hay_pesos_que_verificar():
    """Si el patrón de la prosa cambia y el parser deja de encontrar nada, el
    test de arriba pasaría vacío."""
    assert len(_declarados(FICHAS)) >= 6
