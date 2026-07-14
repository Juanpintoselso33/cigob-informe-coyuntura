"""Regresiones offline para la reconstrucción externa del ITCM."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validacion_externa


def test_carga_itcm_prioriza_csv_fresco_y_preserva_historico(monkeypatch, tmp_path):
    snapshot = tmp_path / "series.json"
    snapshot.write_text(json.dumps({
        "idm": [{"fecha": "2023-12-01", "valor": 1.0}],
        "dolarizacion_depositos": [{"fecha": "2023-12-01", "valor": -99.0}],
    }), encoding="utf-8")
    monkeypatch.setattr(validacion_externa, "SERIES", snapshot)
    monkeypatch.setattr(validacion_externa.publicar, "build_series", lambda: {
        "dolarizacion_depositos": [
            {"fecha": "2023-12-01", "valor": -2.0},
            {"fecha": "2024-01-01", "valor": 1.5},
        ],
    })

    series = validacion_externa._cargar_series_itcm()

    assert series["idm"] == [{"fecha": "2023-12-01", "valor": 1.0}]
    assert series["dolarizacion_depositos"][-1] == {
        "fecha": "2024-01-01",
        "valor": 1.5,
    }


def test_reconstruccion_itcm_incluye_dolarizacion(monkeypatch):
    monkeypatch.setattr(validacion_externa, "_cargar_series_itcm", lambda: {
        "ipc_total": [{"fecha": "2023-12-01", "valor": 25.5}],
        "dolarizacion_depositos": [{"fecha": "2023-12-01", "valor": -2.0}],
    })
    recibidos = []

    def calcular(valores):
        recibidos.append(valores)
        return {"valor": 42.0}

    monkeypatch.setattr(validacion_externa.itcm, "calcular_itcm", calcular)

    assert validacion_externa.construir_serie_itcm() == {"2023-12": 42.0}
    assert recibidos == [{
        "ipc_total": 25.5,
        "rem_ipc_12m": None,
        "saldo_comercial_12m": None,
        "idm": None,
        "dolarizacion_depositos": -2.0,
        "recaudacion": None,
        "reservas_bcra": None,
        "idc": None,
        "credito_privado": None,
        "emae_ia": None,
        "tcrm": None,
    }]
