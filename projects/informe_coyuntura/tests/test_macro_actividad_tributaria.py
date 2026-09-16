"""Tests del proxy de actividad tributaria: 0,6×IVA-DGI + 0,4×cheque, ambos
en variación interanual real (ADR-0329).

Corrige el alcance de ADR-0318/0319 (control dentro de `recaudacion`, dimensión
fiscal): el pedido original era un proxy de ACTIVIDAD y acá puntúa como tal.
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import itcm
import macro


def _series(nominal_iva, nominal_cheque, ipc):
    """{YYYY-MM: valor} para cada insumo, mismo shape que devuelve `_indec_serie`
    ya reindexado por `fetch_actividad_tributaria`."""
    return dict(nominal_iva), dict(nominal_cheque), dict(ipc)


def test_el_compuesto_pondera_60_iva_40_cheque():
    """Caso de mano: IVA sube 20% real i.a., cheque sube 10% real i.a. — el
    compuesto tiene que ser 0,6×20 + 0,4×10 = 16, no el promedio simple (15)
    ni el peso invertido (0,4×20+0,6×10=14)."""
    ipc = {"2024-08": 100.0, "2025-08": 120.0}   # +20% inflación en el año
    iva = {"2024-08": 100.0, "2025-08": 144.0}   # +44% nominal → +20% real
    cheque = {"2024-08": 100.0, "2025-08": 132.0}  # +32% nominal → +10% real

    serie = macro._actividad_tributaria_serie_mensual(iva, cheque, ipc)

    assert serie.keys() == {"2025-08"}
    assert serie["2025-08"] == 0.6 * 20.0 + 0.4 * 10.0 == 16.0


def test_pesos_del_compuesto_suman_uno():
    assert macro.PESO_IVA_ACTIVIDAD_TRIBUTARIA + macro.PESO_CHEQUE_ACTIVIDAD_TRIBUTARIA == 1.0


def test_un_mes_sin_las_dos_series_no_se_calcula():
    """No se imputa: si cheque no tiene el mes (o su t-12), ese mes no entra,
    aunque IVA sí lo tenga completo."""
    ipc = {"2024-08": 100.0, "2025-08": 120.0, "2024-09": 100.0, "2025-09": 121.0}
    iva = {"2024-08": 100.0, "2025-08": 144.0, "2024-09": 100.0, "2025-09": 150.0}
    cheque = {"2024-08": 100.0, "2025-08": 132.0}  # falta 2025-09 y su t-12

    serie = macro._actividad_tributaria_serie_mensual(iva, cheque, ipc)

    assert serie.keys() == {"2025-08"}


def test_fetch_actividad_tributaria_publica_los_dos_componentes(monkeypatch):
    """El detalle publica IVA y cheque por separado, no sólo el compuesto —
    quien lea la card puede ver de dónde vino el número."""
    ipc = {"2024-08": 100.0, "2025-08": 120.0}
    iva = {"2024-08": 100.0, "2025-08": 144.0}
    cheque = {"2024-08": 100.0, "2025-08": 132.0}

    def _fake_indec_serie(series_id, limit=2):
        datos = {
            macro.INDEC_IVA_DGI_ID: iva,
            macro.INDEC_CHEQUE_ID: cheque,
            macro.INDEC_IPC_ID: ipc,
        }[series_id]
        return [(f"{ym}-01", v) for ym, v in datos.items()]

    monkeypatch.setattr(macro, "_indec_serie", _fake_indec_serie)
    resultado = macro.fetch_actividad_tributaria()

    assert resultado is not None
    assert resultado["valor"] == 16.0
    assert resultado["iva_var_ia_real"] == 20.0
    assert resultado["cheque_var_ia_real"] == 10.0
    assert resultado["fecha_dato"] == "2025-08-01"


# ── Bandas (ADR-0329): cero como frontera conceptual, cortes de 5 puntos ────

def test_bandas_actividad_tributaria():
    b = itcm.BANDAS_ITCM["actividad_tributaria"]
    assert itcm.puntaje_banda(10.1, b) == 100
    assert itcm.puntaje_banda(10.0, b) == 80      # low excl./high incl.: 10,0 cae en (5, 10]
    assert itcm.puntaje_banda(5.1, b) == 80
    assert itcm.puntaje_banda(0.1, b) == 60
    assert itcm.puntaje_banda(0.0, b) == 40
    assert itcm.puntaje_banda(-4.9, b) == 40
    assert itcm.puntaje_banda(-5.0, b) == 20
    assert itcm.puntaje_banda(-10.0, b) == 5


def test_peso_de_la_dimension_actividad_suma_uno():
    ind = itcm.DIMENSIONES_ITCM["actividad"]["indicadores"]
    assert set(ind) == {"emae_ia", "emae_difusion", "ipi_manufacturero", "actividad_tributaria"}
    assert abs(sum(ind.values()) - 1.0) < 1e-9


def test_actividad_tributaria_pesa_020_de_la_dimension():
    """ADR-0329: entra con 0,20, y los tres INDEC se recortan proporcionalmente
    (×0,80) preservando su proporción interna 80/20 EMAE/IPI (ADR-0124)."""
    ind = itcm.DIMENSIONES_ITCM["actividad"]["indicadores"]
    assert ind["actividad_tributaria"] == 0.20
    assert ind["emae_ia"] == 0.48
    assert ind["emae_difusion"] == 0.16
    assert ind["ipi_manufacturero"] == 0.16
