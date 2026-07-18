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
        "presion_dolarizacion": [{"fecha": "2023-12-01", "valor": -99.0}],
    }), encoding="utf-8")
    monkeypatch.setattr(validacion_externa, "SERIES", snapshot)
    monkeypatch.setattr(validacion_externa.publicar, "build_series", lambda: {
        "presion_dolarizacion": [
            {"fecha": "2023-12-01", "valor": -2.0},
            {"fecha": "2024-01-01", "valor": 1.5},
        ],
    })

    series = validacion_externa._cargar_series_itcm()

    assert series["idm"] == [{"fecha": "2023-12-01", "valor": 1.0}]
    assert series["presion_dolarizacion"][-1] == {
        "fecha": "2024-01-01",
        "valor": 1.5,
    }


def test_reconstruccion_itcm_incluye_dolarizacion(monkeypatch):
    monkeypatch.setattr(validacion_externa, "_cargar_series_itcm", lambda: {
        "ipc_total": [{"fecha": "2023-12-01", "valor": 25.5}],
        "presion_dolarizacion": [{"fecha": "2023-12-01", "valor": -2.0}],
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
        "presion_dolarizacion": -2.0,
        "recaudacion": None,
        "reservas_bcra": None,
        "idc": None,
        "credito_privado": None,
        "emae_ia": None,
        "tcrm": None,
        "costo_financiamiento_tesoro": None,
        "resultado_primario": None,
    }]


def test_reconstruccion_itcp_mascara_de_era_para_eficacia(monkeypatch, tmp_path):
    # ADR-0070: eficacia_legislativa se excluye de la reconstrucción hasta
    # nov-2025 inclusive (cohorte madura 12-24m 100% de la era actual recién
    # desde dic-2025); desde dic-2025 entra con su valor
    snapshot = tmp_path / "series.json"
    snapshot.write_text(json.dumps({
        "eficacia_legislativa": [
            {"fecha": "2025-11-01", "valor": 30.0},
            {"fecha": "2025-12-01", "valor": 25.0},
        ],
        "votometro_ventaja_lla": [
            {"fecha": "2025-11-01", "valor": 5.0},
            {"fecha": "2025-12-01", "valor": 6.0},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(validacion_externa, "SERIES", snapshot)
    recibidos = {}

    def calcular(valores):
        if all(v is None for v in valores.values()):
            return None   # como el motor real: sin ningún indicador no hay índice
        recibidos[len(recibidos)] = dict(valores)
        return {"valor": 50.0, "dimensiones": {"x": {"peso": 1.0}}}

    monkeypatch.setattr(validacion_externa.itcp, "calcular_itcp", calcular)

    serie = validacion_externa.construir_serie_itcp()

    assert set(serie) == {"2025-11", "2025-12"}
    por_mes = {"2025-11": recibidos[0], "2025-12": recibidos[1]}
    assert por_mes["2025-11"]["eficacia_legislativa"] is None   # enmascarada
    assert por_mes["2025-12"]["eficacia_legislativa"] == 25.0   # cohorte 100% era
    # bloqueo_sostenido integra la reconstrucción (ADR-0069)
    assert "bloqueo_sostenido" in por_mes["2025-12"]
