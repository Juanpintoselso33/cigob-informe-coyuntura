"""Tests de costo_financiamiento_tesoro (ADR-0071): TIREA implícita de una
colocación, filtro de instrumentos comparables, escala de U invertida y
composición de la dimensión de financiamiento.

Los casos de la TIREA usan colocaciones REALES verificadas contra las
gacetillas de la Secretaría de Finanzas, para que el test falle si alguien
cambia la convención de cálculo sin querer.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import macro
import itcm
import parametrica


# ── TIREA implícita de una colocación ────────────────────────────────────────

def test_tirea_capitalizable_reproduce_la_gacetilla():
    """LECAP S27F6, reapertura del 16-01-2026 a precio 1.202,40. Capitaliza a
    TEM 3,95% desde su emisión (28-08-2025) hasta el vencimiento (27-02-2026),
    según la nota al pie de la propia gacetilla. Finanzas publicó TIREA 49,16%.

    Se admite ±3,5 pp: el cálculo capitaliza por meses enteros y el oficial usa
    días exactos, una diferencia de convención que a estos plazos vale ~2,8 pp.
    El test protege contra un cambio de convención accidental, no busca el
    decimal."""
    t = macro._tirea_de_fila(
        "Tasa efectiva mensual capitalizable 3,95%.",
        datetime(2025, 8, 29), datetime(2026, 2, 27), datetime(2026, 1, 16),
        1202.40,
    )
    assert t is not None
    assert abs(t * 100 - 49.16) < 3.5, f"TIREA {t * 100:.2f}% lejos del 49,16% oficial"


def test_tirea_a_descuento_letra_de_2023():
    """Las LEDE de 2023 no capitalizan: pagan 1.000 al vencimiento. Con precio
    de corte por debajo de 1.000, la TIREA tiene que dar muy alta (la primera
    licitación de la gestión cortó a TEM 8,66% ≈ 169% efectiva anual)."""
    t = macro._tirea_de_fila(
        "A descuento",
        datetime(2023, 12, 20), datetime(2024, 1, 18), datetime(2023, 12, 20),
        926.0,
    )
    assert t is not None and t > 1.0, f"TIREA {t} — se esperaba > 100% anual"


def test_instrumentos_no_comparables_quedan_afuera():
    """CER, dólar linked y tasa variable no tienen una tasa fija comparable:
    promediarlos con las LECAP mezclaría semánticas distintas."""
    for cupon in ("Cupón cero con ajuste por CER",
                  "Tasa efectiva mensual “TAMAR TEM”",
                  "Vinculada al dólar estadounidense"):
        assert macro._tirea_de_fila(
            cupon, datetime(2025, 1, 1), datetime(2026, 1, 1),
            datetime(2025, 6, 1), 1000.0,
        ) is None, f"{cupon!r} no debería puntuar"


def test_fila_corrupta_no_rompe():
    """Vencimiento anterior a la colocación → sin TIREA, sin excepción."""
    assert macro._tirea_de_fila(
        "Tasa efectiva mensual capitalizable 2,00%.",
        datetime(2025, 1, 1), datetime(2025, 6, 1), datetime(2025, 12, 1), 1000.0,
    ) is None


# ── Escala de U invertida ────────────────────────────────────────────────────

def _p(valor):
    return parametrica.puntaje_interpolado(
        valor, itcm.BANDAS_ITCM["costo_financiamiento_tesoro"])


def test_los_dos_extremos_estan_castigados():
    """Es la única banda no monótona del ITCM: represión y bola de nieve
    puntúan mal, el óptimo está en el medio."""
    assert _p(-12.2) == 20.0      # dic-2023, licuación
    assert _p(33.5) == 15.0       # ago-2025, bola de nieve
    assert _p(3.0) == 100.0       # zona sana


def test_la_curva_sube_y_despues_baja():
    """Verificación explícita de la forma de U invertida."""
    tramo_sube = [_p(v) for v in (-10, -5, -2.5, 0, 3)]
    tramo_baja = [_p(v) for v in (3, 6, 9, 16, 20, 30)]
    assert tramo_sube == sorted(tramo_sube), tramo_sube
    assert tramo_baja == sorted(tramo_baja, reverse=True), tramo_baja


def test_valor_vigente_puntua_en_zona_alta():
    """+8,1% real (jun-2026) es 'caro pero manejable', no óptimo ni crisis."""
    assert 70.0 < _p(8.07) < 90.0


# ── Dimensión de financiamiento ──────────────────────────────────────────────

def test_la_dimension_incluye_el_costo_y_suma_uno():
    dim = itcm.DIMENSIONES_ITCM["financiamiento"]
    assert "costo_financiamiento_tesoro" in dim["indicadores"]
    assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9


def test_el_costo_toma_un_cuarto_de_la_dimension():
    """ADR-0071: el nuevo indicador toma 25%, y reservas conserva el recorte
    proporcional (45 × 0,75)."""
    ind = itcm.DIMENSIONES_ITCM["financiamiento"]["indicadores"]
    assert ind["costo_financiamiento_tesoro"] == 0.25
    assert abs(ind["reservas_bcra"] - 0.45 * 0.75) < 0.011


def test_la_capacidad_de_fondeo_no_pesa_mas_que_el_credito_realizado():
    """ADR-0074: el IdC declara en su propia validación que NO anticipa el
    crédito futuro; es un descriptor de condiciones, no un pronóstico. Que
    pesara 2,7× el crédito efectivamente otorgado invertía la jerarquía."""
    ind = itcm.DIMENSIONES_ITCM["financiamiento"]["indicadores"]
    assert abs(ind["idc"] - ind["credito_privado"]) <= 0.01, (
        f'idc {ind["idc"]} vs credito {ind["credito_privado"]}')


def test_el_indicador_esta_declarado_como_esperado():
    assert "costo_financiamiento_tesoro" in macro.INDICADORES_ESPERADOS
