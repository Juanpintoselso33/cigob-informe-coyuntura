"""La historia del ITCM aplica la MISMA regla automática del saldo comercial
que la tarjeta (ADR-0056 / ADR-0404): un superávit que se explica sobre todo por
caída de importaciones se penaliza hacia 60 puntos.

Hasta nov-2026 `validacion_externa.construir_serie_itcm` llamaba al motor sin
ajustes, así que un mes «por contracción» valía más en la historia que en la
tarjeta (oct-2024: 40,4 en la historia, 40,3 con la regla). Excluir los
overrides del analista no justifica excluir una regla automática."""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import itcm
import macro
import validacion_externa as ve

# Mismo caso que test_itcm.test_ajuste_automatico_saldo_por_contraccion, en
# acumulados: expo +1.500, impo −9.000 → share_impo 85,7 % → puntaje 67,1.
VALORES = {
    "ipc_total": 2.58, "rem_ipc_12m": 23.3, "desequilibrio_monetario": 35.2,
    "recaudacion": 94.4, "resultado_primario": 16.6, "saldo_comercial_12m": 17.5,
    "reservas_bcra": 1881, "idc": -0.31, "credito_privado": 18.09,
    "costo_financiamiento_tesoro": 8.07, "emae_ia": 5.48, "tcrm": 85.87,
    "terminos_intercambio": 145.1401, "iai": -20.47,
}


def _p(ym, v):
    return {"fecha": f"{ym}-01", "valor": v}


SERIES = {
    "saldo_comercial_12m": [_p("2025-10", 17.5)],
    "saldo_comercial_expo_12m": [_p("2024-10", 75000.0), _p("2025-10", 76500.0)],
    "saldo_comercial_impo_12m": [_p("2024-10", 69000.0), _p("2025-10", 60000.0)],
}


def test_la_historia_lee_la_composicion_y_aplica_la_regla(monkeypatch):
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: SERIES)
    aj = ve._ajustes_itcm_por_mes()
    assert set(aj) == {"2025-10"}
    assert aj["2025-10"]["saldo_comercial_12m"]["puntaje"] == 67.1
    assert aj["2025-10"]["saldo_comercial_12m"]["origen"] == "automatico"


def test_tarjeta_e_historia_dan_el_mismo_ajuste(monkeypatch):
    """La tarjeta arma la composición con itcm.composicion_saldo y la regla con
    itcm.ajustes_automaticos; la historia, con las mismas dos funciones."""
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: SERIES)
    tarjeta = {"saldo_comercial_12m": {
        "valor": 17.5, **itcm.composicion_saldo(76500.0, 75000.0, 60000.0, 69000.0)}}
    assert itcm.ajustes_automaticos(tarjeta) == ve._ajustes_itcm_por_mes()["2025-10"]
    # y la tarjeta efectivamente pasa por ajustes_automaticos
    r_tarjeta = macro.calcular_itcm_cinturon({k: {"valor": v} for k, v in VALORES.items()}
                                             | tarjeta)
    assert r_tarjeta["dimensiones"]["sector_externo"]["indicadores"][
        "saldo_comercial_12m"]["puntaje_aplicado"] == 67.1


def test_la_serie_reconstruida_usa_el_ajuste(monkeypatch):
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: SERIES)
    monkeypatch.setattr(ve, "_valores_itcm_por_mes", lambda: {"2025-10": dict(VALORES)})
    serie = ve.construir_serie_itcm()
    con = itcm.calcular_itcm(dict(VALORES), ve._ajustes_itcm_por_mes()["2025-10"])
    sin = itcm.calcular_itcm(dict(VALORES))
    assert con["valor"] != sin["valor"]
    assert serie["2025-10"] == con["valor"]


def test_sin_composicion_no_hay_ajuste(monkeypatch):
    """Un mes sin expo/impo del año anterior no se ajusta: no se inventa la
    composición desde el saldo en % del comercio."""
    series = dict(SERIES, saldo_comercial_expo_12m=[_p("2025-10", 76500.0)])
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: series)
    assert ve._ajustes_itcm_por_mes() == {}
