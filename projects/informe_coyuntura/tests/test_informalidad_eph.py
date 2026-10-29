"""Informalidad sin aportes propios (ADR-0413): parseo de las planillas del
INDEC con filas sintéticas, sin red."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import informalidad_eph as m  # noqa: E402


def _anual():
    return [
        ["Cuadro 4.1. Población asalariada"],
        ["Población asalariada", "  Año 2023", None, "   Año 2024", None],
        [None, "4° trimestre", None, "1° trimestre", "2° trimestre"],
        ["Informal", 35.4, None, 35.3, 35.9],
        ["  con aportes propios", 5.4, None, 5.3, 5.5],
        ["  sin aportes propios", 30, None, 30, 30.4],
    ]


def _trimestral(con_2t=15.9):
    return [
        ["Cuadro 1.5"],
        ["Indicador", "Año 2025", "", "", "", "", "Año 2026", ""],
        ["", "1° trimestre", "2° trimestre", "3° trimestre", "4° trimestre", "", "1° trimestre", "2° trimestre*"],
        ["Sin descuento jubilatorio (informal)", 36.3, 37.7, 36.7, 36.3, "", 37.9, 37.9],
        ["Asalariados sin descuento jubilatorio (informales) (5)", 100, 100, 100, 100, "", 100, 100],
        ["Con aportes propios", 17.1, 62.3, 13.9, 15.7, "", 15.5, con_2t],
        ["Sin aportes propios", 82.9, 37.7, 86.1, 84.3, "", 84.5, 100 - con_2t],
    ]


def test_planilla_anual():
    assert m.parsear_anual(_anual()) == {"2023-10-01": 30.0, "2024-01-01": 30.0, "2024-04-01": 30.4}


def test_trimestral_calcula_y_descarta_la_errata():
    t = m.parsear_trimestral(_trimestral())
    assert "2025-04-01" not in t                       # 62,3 % con aportes: errata
    assert t["2026-04-01"] == 31.9 and t["2026-01-01"] == 32.0
    assert t["2025-10-01"] == 30.6


def test_la_planilla_anual_manda_y_la_cuenta_rellena_lo_posterior():
    anual = {"2023-10-01": 30.0, "2025-10-01": 30.3}
    trim = {"2023-10-01": 30.3, "2025-10-01": 30.6, "2026-01-01": 32.0, "2026-04-01": 31.9}
    s = m.combinar(anual, trim)
    assert s == [["2023-10-01", 30.0], ["2025-10-01", 30.3],
                 ["2026-01-01", 32.0], ["2026-04-01", 31.9]]


def test_ultimo_es_proporcion_y_ultimo_punto(monkeypatch):
    m.serie.cache_clear()
    monkeypatch.setattr(m, "serie", lambda: [["2026-01-01", 32.0], ["2026-04-01", 31.9]])
    assert m.ultimo() == {"valor": 0.319, "fecha": "2026-04-01"}


def test_sin_la_base_del_4t_2023_falla_en_voz_alta(monkeypatch):
    # hallazgo de Codex (29-oct): si la planilla anual no se puede leer y la
    # trimestral sí, la serie arrancaría después del 4T-2023 y el componente
    # quedaría sin puntaje sin que nada avise
    import pytest
    def falso(plantilla, meses, anios_atras, hoy, leer, parsear):
        if plantilla == m.PLANILLA_ANUAL:
            return {}, None
        return {"2026-01-01": 32.0, "2026-04-01": 31.9}, "https://trimestral"
    monkeypatch.setattr(m, "_primero", falso)
    m.serie.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="falta la base"):
            m.serie()
    finally:
        m.serie.cache_clear()
