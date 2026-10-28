"""ADR-0387: «Cuentas fiscales» y «Sector externo» se separan sin mover el índice.

Es una reorganización: cada indicador conserva el peso efectivo que tenía
(peso de dimensión × peso interno) y el ITCM no cambia."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itcm  # noqa: E402
import parametrica  # noqa: E402
import terminos_intercambio as ti  # noqa: E402

D = itcm.DIMENSIONES_ITCM

# Pesos efectivos en el índice ANTES de ADR-0387 (dimensión × peso interno).
# ADR-0409 movió las reservas a estabilidad y estos siguen siendo los mismos.
EFECTIVOS = {
    "ipc_total": 0.156, "rem_ipc_12m": 0.052, "desequilibrio_monetario": 0.052,
    "resultado_primario": 0.12, "recaudacion": 0.072, "saldo_comercial_12m": 0.048,
    "reservas_bcra": 0.0544, "idc": 0.0336, "costo_financiamiento_tesoro": 0.04,
    "credito_privado": 0.032,
    "emae_ia": 0.0966, "emae_difusion": 0.0322, "ipi_manufacturero": 0.0322, "iai": 0.069,
    "tcrm": 0.055, "terminos_intercambio": 0.055,
}


def test_composicion_de_las_dimensiones():
    assert list(D) == ["estabilidad_monetaria", "cuentas_fiscales", "sector_externo",
                       "financiamiento", "actividad"]
    assert "viabilidad_fiscal_comercial" not in D and "competitividad_externa" not in D
    assert set(D["cuentas_fiscales"]["indicadores"]) == {"resultado_primario", "recaudacion"}
    # ADR-0409: las reservas netas pasan a estabilidad monetaria-inflacionaria.
    assert set(D["sector_externo"]["indicadores"]) == {
        "saldo_comercial_12m", "tcrm", "terminos_intercambio"}
    assert set(D["estabilidad_monetaria"]["indicadores"]) == {
        "ipc_total", "rem_ipc_12m", "desequilibrio_monetario", "reservas_bcra"}
    assert D["estabilidad_monetaria"]["peso"] == 0.3144 and D["sector_externo"]["peso"] == 0.158
    assert set(D["financiamiento"]["indicadores"]) == {
        "idc", "costo_financiamiento_tesoro", "credito_privado"}
    assert D["cuentas_fiscales"]["nombre"] == "Cuentas fiscales"
    assert D["sector_externo"]["nombre"] == "Sector externo"


def test_los_pesos_suman_uno_y_cada_indicador_conserva_el_suyo():
    assert sum(d["peso"] for d in D.values()) == pytest.approx(1.0)
    efectivos = {}
    for d in D.values():
        assert sum(d["indicadores"].values()) == pytest.approx(1.0)
        for k, w in d["indicadores"].items():
            efectivos[k] = d["peso"] * w
    assert efectivos == pytest.approx(EFECTIVOS)


def test_el_cruce_sigue_siendo_un_grupo_del_sector_externo():
    g, = D["sector_externo"]["grupos"]
    assert set(g["indicadores"]) == {"tcrm", "terminos_intercambio"}
    assert g["combinar"] is ti.combinar_dimension


def test_el_itcm_no_se_mueve_con_los_datos_completos():
    """Mismos números que antes de la reagrupación (60,6 con el ejemplo del
    test de ITCM; 59,4 y 59,8 con los dos ajustes del saldo comercial)."""
    from test_itcm import EJEMPLO
    assert itcm.calcular_itcm(EJEMPLO)["valor"] == 60.6
    aj = lambda p: {"saldo_comercial_12m": {"puntaje": p, "justificacion": "x"}}
    assert itcm.calcular_itcm(EJEMPLO, aj(60))["valor"] == 59.4
    assert itcm.calcular_itcm(EJEMPLO, aj(67.1))["valor"] == 59.8


def test_grupo_incompleto_no_se_calcula_ni_se_promedia():
    p, usados = parametrica.puntaje_dimension(
        {"tcrm": 40.0, "saldo_comercial_12m": 60.0},
        D["sector_externo"]["indicadores"], D["sector_externo"]["grupos"])
    assert usados == {"saldo_comercial_12m"} and p == 60.0
    p, usados = parametrica.puntaje_dimension(
        {"tcrm": 40.0}, D["sector_externo"]["indicadores"], D["sector_externo"]["grupos"])
    assert p is None and usados == set()
