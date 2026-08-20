"""La card de `consumo_carne` y la serie que puntúa en el índice salen de
fuentes DISTINTAS, y eso es deliberado desde ADR-0215:

- card  → tablero de SAGYP, de donde salen también el total y el ratio, así que
          la matriz A×B de la ficha compara la misma medición consigo misma;
- serie → CICCRA, la única con historia mensual reconstruible hasta el 4T-2023,
          que es la base contra la que se rebasean los dieciséis componentes.

El tablero de SAGYP no puede sostener la serie porque es una FOTO del mes: pisa
el promedio móvil vigente en cada edición, así que el índice se quedaría con un
punto y sin base.

Lo que este test cuida son las dos mitades del arreglo. Que cada lado siga
saliendo de donde el ADR dice, y —lo importante— que la distancia entre los dos
no crezca. Hoy esa distancia (0,22 sobre 47) cae por debajo de la tolerancia de
G3 (1%, o sea 0,47), así que el pipeline pasa. Pero pasa por una propiedad del
mes, no del diseño: el día que las dos fuentes se separen, G3 va a bloquear la
publicación por una causa que nadie escribió. Este test avisa antes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DESCARGAR = (ROOT / "scripts" / "descargar_series.py").read_text(encoding="utf-8")
SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))

# Más chico que la tolerancia de G3 (max(0,11 · |v|×1%) ≈ 0,47) a propósito:
# el punto de este test es fallar ANTES que el gate, con un mensaje que explica
# por qué hay dos fuentes, en vez de que el pipeline se caiga sin contexto.
MARGEN = 0.40


def _card(clave):
    return SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"][clave]


def test_la_serie_del_indice_sigue_saliendo_de_ciccra():
    """Si alguien muda la serie a SAGYP sin más, el índice se queda con un
    punto y sin base 4T-2023. La mudanza necesita el ADR que supersede al 0215
    y una base 2023 de fuente externa (la del propio tablero sería circular)."""
    fila = next(l for l in DESCARGAR.splitlines()
                if l.strip().startswith('("consumo_carne"'))
    assert "CICCRA" in fila, fila
    assert "fetch_carne_serie" in fila, fila


def test_la_serie_del_total_sale_de_sagyp():
    bloque = DESCARGAR[DESCARGAR.index('("consumo_carnes_total"'):]
    assert "SAGYP" in bloque[:220], bloque[:220]


def test_la_card_sale_de_sagyp():
    """El Componente A pasó a SAGYP el 12-ago-2026 para que A, B y C salgan del
    mismo PDF. Si vuelve a CICCRA, la matriz A×B compara dos fuentes."""
    fuente = _card("consumo_carne").get("fuente", "")
    assert "SAGYP" in fuente, f"la card dice fuente {fuente!r}"
    assert "SAGYP" in _card("consumo_carnes_total").get("fuente", "")


def test_las_dos_fuentes_no_se_separaron():
    card = _card("consumo_carne").get("valor")
    serie = SERIES.get("consumo_carne") or []
    assert card is not None and serie, "sin card o sin serie de consumo_carne"
    ultimo = serie[-1]["valor"]
    assert abs(card - ultimo) <= MARGEN, (
        f"La card (SAGYP, {card}) y la serie (CICCRA, {ultimo}) se separaron "
        f"{round(abs(card - ultimo), 2)} > {MARGEN}. NO es un bug: son dos "
        f"fuentes distintas por decisión declarada en ADR-0215, y hasta hoy "
        f"caían dentro de la tolerancia de G3. Si la brecha vino para quedarse, "
        f"la salida es mudar la serie (necesita base 2023 de fuente externa) o "
        f"exceptuar el indicador de G3 con motivo escrito — no subir este margen."
    )
