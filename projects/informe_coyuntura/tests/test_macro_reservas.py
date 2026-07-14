"""Regresiones offline para la reconciliación de reservas netas."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import macro


def test_reservas_usa_depositos_del_tesoro_del_mes_de_la_planilla_sdds(monkeypatch):
    monkeypatch.setattr(
        macro,
        "_reservas_netas_sdds",
        lambda: {
            "netas": -1_000.0,
            "brutas": 10_000.0,
            "prestamos_dep": -4_000.0,
            "swaps": -3_000.0,
            "repos": -4_000.0,
            "bopreal_12m": 200.0,
            "fecha": "31/05/26",
        },
    )
    monkeypatch.setattr(
        macro,
        "_bcra_ultimo",
        lambda _variable: {"valor": 10_000.0, "fecha": "2026-05-31"},
    )

    meses_solicitados = []

    def tesoro(mes=None):
        meses_solicitados.append(mes)
        return 300.0 if mes == "2026-05" else 500.0

    monkeypatch.setattr(macro, "_tesoro_deposits_usd", tesoro)

    resultado = macro.fetch_reservas_netas()

    assert meses_solicitados == ["2026-05"]
    assert resultado["depositos_tesoro"] == 300.0
    assert resultado["valor"] == -500.0


def test_reservas_no_publica_como_fresco_si_falta_tesoro(monkeypatch):
    monkeypatch.setattr(
        macro,
        "_reservas_netas_sdds",
        lambda: {
            "netas": -1_000.0,
            "brutas": 10_000.0,
            "prestamos_dep": -4_000.0,
            "swaps": -3_000.0,
            "repos": -4_000.0,
            "bopreal_12m": 200.0,
            "fecha": "31/05/26",
        },
    )
    monkeypatch.setattr(
        macro,
        "_bcra_ultimo",
        lambda _variable: {"valor": 10_000.0, "fecha": "2026-05-31"},
    )
    monkeypatch.setattr(
        macro,
        "_tesoro_deposits_usd",
        lambda _mes=None: (_ for _ in ()).throw(ValueError("mes no disponible")),
    )

    assert macro.fetch_reservas_netas() is None


def test_reservas_no_cae_a_otro_mes_si_falta_tesoro_del_sdds(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        macro,
        "_reservas_netas_sdds",
        lambda: {
            "netas": -1_000.0,
            "brutas": 10_000.0,
            "prestamos_dep": -4_000.0,
            "swaps": -3_000.0,
            "repos": -4_000.0,
            "bopreal_12m": 200.0,
            "fecha": "31/05/26",
        },
    )
    monkeypatch.setattr(
        macro,
        "_bcra_ultimo",
        lambda _variable: {"valor": 11_000.0, "fecha": "2026-06-30"},
    )
    cfg = tmp_path / "reservas.json"
    cfg.write_text(
        '{"drenajes_seccion_ii": 12000, "actualizado": "2026-05-31"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(macro, "RESERVAS_PASIVOS_PATH", cfg)
    meses_solicitados = []

    def tesoro(mes=None):
        meses_solicitados.append(mes)
        if mes == "2026-05":
            raise ValueError("mes no disponible")
        return 300.0

    monkeypatch.setattr(macro, "_tesoro_deposits_usd", tesoro)

    assert macro.fetch_reservas_netas() is None
    assert meses_solicitados == ["2026-05"]


def test_reservas_no_publica_fallback_con_drenajes_de_otro_mes(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        macro,
        "_reservas_netas_sdds",
        lambda: (_ for _ in ()).throw(ValueError("SDDS no disponible")),
    )
    monkeypatch.setattr(
        macro,
        "_bcra_ultimo",
        lambda _variable: {"valor": 11_000.0, "fecha": "2026-06-30"},
    )
    cfg = tmp_path / "reservas.json"
    cfg.write_text(
        '{"drenajes_seccion_ii": 12000, "actualizado": "2026-05-31"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(macro, "RESERVAS_PASIVOS_PATH", cfg)
    meses_solicitados = []
    monkeypatch.setattr(
        macro,
        "_tesoro_deposits_usd",
        lambda mes=None: meses_solicitados.append(mes) or 300.0,
    )

    assert macro.fetch_reservas_netas() is None
    assert meses_solicitados == []
