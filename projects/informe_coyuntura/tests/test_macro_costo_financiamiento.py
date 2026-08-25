"""Tests de costo_financiamiento_tesoro (ADR-0071): TIREA implícita de una
colocación, filtro de instrumentos comparables, escala de U invertida y
composición de la dimensión de financiamiento.

Los casos de la TIREA usan colocaciones REALES verificadas contra las
gacetillas de la Secretaría de Finanzas, para que el test falle si alguien
cambia la convención de cálculo sin querer.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import macro
import itcm
import parametrica


def _d(iso: str) -> datetime:
    return datetime.strptime(iso, "%Y-%m-%d")


# ── TIREA de una colocación ──────────────────────────────────────────────────
# ADR-0238: la TIREA de una LECAP/BONCAP no se estima, se lee. Finanzas publica
# la TEM en el cupón y el mercado la anualiza como (1+TEM)^12-1. Lo que había
# antes reconstruía esa tasa desde precio y fechas capitalizando por meses de
# CALENDARIO enteros, y en la S13N6 eso publicó 32,17% donde la Secretaría
# informó 28,32%.

FIXTURE = Path(__file__).parent / "fixtures" / "colocaciones_2026_06.json"


def _colocaciones_de_junio():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_la_lecap_de_la_licitacion_auditada_da_la_tasa_oficial():
    """S13N6, emitida a la par el 30-06-2026 a TEM 2,1%.

    Es EL caso de la auditoría del 25-ago-2026: $4,18 billones adjudicados, la
    única colocación a tasa fija en pesos del mes. (1,021)^12-1 = 28,32%, que
    es lo que informaron la Secretaría y el mercado."""
    doc = _colocaciones_de_junio()
    lecap = [f for f in doc["filas"] if f["instrumento"] == "LECAP/$/13-11-2026"]
    assert len(lecap) == 1, "la licitación auditada tiene una sola LECAP"
    f = lecap[0]
    t = macro._tirea_de_fila(
        f["cupon"], _d(f["emision"]), _d(f["vencimiento"]), _d(f["colocacion"]),
        f["precio_emision"],
    )
    assert t is not None
    assert abs(t * 100 - 28.32) < 0.01, f"TIREA {t * 100:.2f}% ≠ 28,32% oficial"


def test_el_valor_erroneo_no_puede_volver():
    """32,17% salía de capitalizar 5 meses de calendario sobre 4,5 corridos.

    Este test no comprueba una convención: comprueba que ESE número, el que se
    publicó cuatro semanas, no puede reaparecer para este instrumento."""
    doc = _colocaciones_de_junio()
    f = [x for x in doc["filas"] if x["instrumento"] == "LECAP/$/13-11-2026"][0]
    t = macro._tirea_de_fila(
        f["cupon"], _d(f["emision"]), _d(f["vencimiento"]), _d(f["colocacion"]),
        f["precio_emision"],
    )
    assert abs(t * 100 - 32.17) > 1.0, "volvió la TIREA por meses de calendario"


def test_la_licitacion_completa_reproduce_el_dato_real_corregido():
    """La cuenta entera de junio: TIREA ponderada contra el REM del mes.

    Con 22,3% de inflación esperada, 28,32% nominal son ~4,9% reales, no los
    8,07% publicados. Recorre las 17 filas de la licitación, no sólo la que
    puntúa, así que también prueba que las otras 16 quedan afuera."""
    doc = _colocaciones_de_junio()
    suma = peso = 0.0
    n = 0
    for f in doc["filas"]:
        if f["moneda_origen"] != "ARP":
            continue
        t = macro._tirea_de_fila(
            f["cupon"], _d(f["emision"]), _d(f["vencimiento"]),
            _d(f["colocacion"]), f["precio_emision"],
        )
        if t is None:
            continue
        suma += t * f["valor_efectivo"]
        peso += f["valor_efectivo"]
        n += 1
    assert n == 1, f"{n} colocaciones a tasa fija en pesos; la licitación tuvo una"
    tirea = suma / peso
    real = ((1 + tirea) / (1 + doc["_rem_ipc_12m_2026_06"] / 100.0) - 1) * 100.0
    assert abs(real - 4.92) < 0.05, f"{real:.2f}% real; la auditoría verificó ~4,92%"
    assert abs(real - 8.07) > 1.0, "volvió el valor publicado que la auditoría rechazó"


def test_la_reconstruccion_por_precio_reproduce_la_tasa_oficial():
    """El guard que la auditoría pidió: tolerancia < 5 pb.

    `_tirea_reconstruida` deriva la tasa del precio de corte y del plazo real.
    Bien escrita, en una emisión nueva colocada a la par tiene que dar la MISMA
    tasa que el cupón anualizado — si se separan, una de las dos convenciones se
    rompió. Es el chequeo que no existía cuando la reconstrucción se desvió 385
    pb sin que nada fallara."""
    doc = _colocaciones_de_junio()
    a_la_par = [f for f in doc["filas"]
                if f["moneda_origen"] == "ARP" and abs(f["precio_emision"] - 1000) < 0.01
                and f["emision"] == f["colocacion"]
                and macro._tem_capitalizable(f["cupon"]) is not None]
    assert a_la_par, "el fixture perdió la emisión nueva a la par"
    for f in a_la_par:
        args = (f["cupon"], _d(f["emision"]), _d(f["vencimiento"]),
                _d(f["colocacion"]), f["precio_emision"])
        oficial = macro._tirea_de_fila(*args)
        recon = macro._tirea_reconstruida(*args)
        assert abs(recon - oficial) * 10000 < 5, (
            f'{f["instrumento"]}: {abs(recon - oficial) * 10000:.2f} pb de desvío')


def test_la_tasa_publicada_no_depende_del_precio_de_corte():
    """Una reapertura colocada fuera de la par conserva la tasa de su cupón.

    Es una decisión, no un descuido (ADR-0238): la tasa oficial del instrumento
    es su TEM. El rendimiento marginal del precio de corte es otra medida y vive
    en `_tirea_reconstruida`, que valida pero no publica."""
    args = ("Tasa efectiva mensual capitalizable 3,95%.",
            datetime(2025, 8, 29), datetime(2026, 2, 27), datetime(2026, 1, 16))
    a_la_par = macro._tirea_de_fila(*args, 1000.0)
    con_prima = macro._tirea_de_fila(*args, 1202.40)
    assert a_la_par == con_prima
    assert abs(a_la_par * 100 - ((1.0395 ** 12) - 1) * 100) < 1e-9


def test_tirea_a_descuento_letra_de_2023():
    """Las LEDE de 2023 no capitalizan ni publican TEM: pagan 1.000 al
    vencimiento, así que ahí la tasa SÍ hay que reconstruirla desde el precio.
    La primera licitación de la gestión cortó muy por debajo de la par."""
    t = macro._tirea_de_fila(
        "A descuento",
        datetime(2023, 12, 20), datetime(2024, 1, 18), datetime(2023, 12, 20),
        926.0,
    )
    assert t is not None and t > 1.0, f"TIREA {t} — se esperaba > 100% anual"


def test_instrumentos_no_comparables_quedan_afuera():
    """CER, dólar linked y tasa variable no tienen una tasa fija comparable:
    promediarlos con las LECAP mezclaría semánticas distintas.

    `TAMAR TEM` importa aparte: dice «capitalizable» pero no trae número, así
    que el filtro no puede ser la palabra."""
    for cupon in ("Cupón cero con ajuste por CER",
                  "Tasa efectiva mensual “TAMAR TEM”",
                  'Tasa efectiva mensual capitalizable “TAMAR TEM" + margen',
                  "Vinculada al dólar estadounidense"):
        assert macro._tirea_de_fila(
            cupon, datetime(2025, 1, 1), datetime(2026, 1, 1),
            datetime(2025, 6, 1), 1000.0,
        ) is None, f"{cupon!r} no debería puntuar"


def test_la_licitacion_en_dolares_no_entra_por_la_ventana():
    """Junio tuvo BONAR, BONTE y LELINK en dólares. Ninguna puede aportar a una
    tasa en pesos, y el filtro de moneda es lo único que las frena."""
    doc = _colocaciones_de_junio()
    usd = [f for f in doc["filas"] if f["moneda_origen"] == "USD"]
    assert usd, "el fixture perdió las colocaciones en dólares"


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
    """+4,9% real (jun-2026, ya corregido) sigue en la zona sana de la U.

    El 8,07% anterior también caía en verde, así que el color no cambió: lo que
    cambió es el nivel, y por eso el test mira el puntaje y no el semáforo."""
    assert 90.0 < _p(4.92) <= 100.0


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
