"""Regresiones offline para la dolarización de depósitos del ITCM."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import macro


def _fuentes_base():
    return {
        macro.BCRA_DEP_PRIV_ME_USD_ID: {
            "2025-05": 100.0,
            "2026-05": 127.76,
            "2026-06": 130.0,
        },
        macro.BCRA_DEP_PRIV_ID: {
            "2025-05": 100.0,
            "2026-05": 197.38,
            "2026-06": 205.0,
        },
    }


def _parchear_fuentes(monkeypatch, fuentes=None, ipc=None):
    fuentes = fuentes or _fuentes_base()
    ipc = ipc or {"2025-05": 100.0, "2026-05": 200.0}
    monkeypatch.setattr(
        macro,
        "_bcra_fin_de_mes",
        lambda var_id, _meses: fuentes[var_id],
    )
    monkeypatch.setattr(macro, "_ipc_indice_mensual", lambda _limit: ipc)


def test_serie_calcula_brecha_y_usa_ultimo_mes_comun(monkeypatch):
    _parchear_fuentes(monkeypatch)

    serie = macro._dolarizacion_depositos_serie_mensual(meses_hist=24)

    assert serie == [("2026-05", 29.07, 27.76, -1.31)]
    assert all(ym != "2026-06" for ym, *_ in serie)


def test_serie_exige_panel_completo_en_t_menos_12(monkeypatch):
    fuentes = _fuentes_base()
    del fuentes[macro.BCRA_DEP_PRIV_ID]["2025-05"]
    _parchear_fuentes(monkeypatch, fuentes=fuentes)

    assert macro._dolarizacion_depositos_serie_mensual() == []


def test_serie_conserva_cera_y_ordena_ascendente(monkeypatch):
    fuentes = {
        macro.BCRA_DEP_PRIV_ME_USD_ID: {
            "2023-09": 100.0,
            "2023-10": 100.0,
            "2024-09": 238.88,
            "2024-10": 265.43,
        },
        macro.BCRA_DEP_PRIV_ID: {
            "2023-09": 100.0,
            "2023-10": 100.0,
            "2024-09": 200.0,
            "2024-10": 200.0,
        },
    }
    ipc = {
        "2023-09": 100.0,
        "2023-10": 100.0,
        "2024-09": 200.0,
        "2024-10": 200.0,
    }
    _parchear_fuentes(monkeypatch, fuentes=fuentes, ipc=ipc)

    serie = macro._dolarizacion_depositos_serie_mensual()

    assert [fila[0] for fila in serie] == ["2024-09", "2024-10"]
    assert serie[0][1] == 138.88
    assert serie[1][1] == 165.43


def test_fetcher_publica_ultima_fila_y_componentes(monkeypatch):
    monkeypatch.setattr(
        macro,
        "_dolarizacion_depositos_serie_mensual",
        lambda: [("2026-05", 29.07, 27.76, -1.31)],
    )

    resultado = macro.fetch_dolarizacion_depositos()

    assert resultado == {
        "valor": 29.07,
        "unidad": "pp (brecha i.a.)",
        "fuente": "BCRA — depósitos privados por moneda + INDEC — IPC nacional",
        "fecha_dato": "2026-05-01",
        "desactualizado": False,
        "crecimiento_usd_ia": 27.76,
        "crecimiento_pesos_real_ia": -1.31,
    }


def test_fetcher_devuelve_none_sin_observaciones(monkeypatch):
    monkeypatch.setattr(macro, "_dolarizacion_depositos_serie_mensual", lambda: [])
    assert macro.fetch_dolarizacion_depositos() is None


def test_backfill_reutiliza_helper_y_arranca_en_diciembre_2023(monkeypatch):
    llamadas = []

    def serie(meses_hist):
        llamadas.append(meses_hist)
        return [
            ("2023-11", -3.0, 1.0, 4.0),
            ("2023-12", -2.0, 2.0, 4.0),
            ("2024-01", 1.5, 3.0, 1.5),
        ]

    monkeypatch.setattr(macro, "_dolarizacion_depositos_serie_mensual", serie)

    assert descargar_series.fetch_dolarizacion_depositos_serie(meses=3) == [
        ["2023-12-01", -2.0],
        ["2024-01-01", 1.5],
    ]
    assert llamadas == [7]


def test_indicador_esta_registrado_en_colector_y_backfill():
    assert "dolarizacion_depositos" in macro.INDICADORES_ESPERADOS
    assert "dolarizacion_depositos" in {
        nombre for nombre, _unidad, _fuente, _fetcher in descargar_series.MACRO_DERIVADAS
    }
