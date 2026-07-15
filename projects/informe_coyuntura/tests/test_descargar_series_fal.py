"""Regresión offline: serie mensual del índice FAL re-apuntada al régimen
de la Ley 27.802 (ADR-0068) — cero antes de mar-2026, menciones acumuladas
del "fondo de asistencia laboral" después."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import gestion


def test_fetch_fal_serie_cero_antes_del_regimen(monkeypatch):
    """Los meses previos a mar-2026 valen 0,0 SIN consultar el BO (el régimen
    FAL no existía y la adopción financiera CNV fue siempre 0); desde
    mar-2026 cada mes consulta las menciones acumuladas desde la sanción."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)

    consultas = []

    def fake_conteo(texto, desde="10/12/2023", hasta=None):
        consultas.append((texto, desde, hasta))
        # mar=1 (ley), abr=1, may=2, jun=3 acumuladas
        return {"31/03/2026": 1, "30/04/2026": 1,
                "31/05/2026": 2, "30/06/2026": 3}[hasta]

    monkeypatch.setattr(gestion, "_bo_conteo", fake_conteo)

    serie = descargar_series.fetch_fal_serie()

    # dic-2023 a jun-2026 = 31 puntos; los primeros 27 (hasta feb-2026) en 0
    assert len(serie) == 31
    assert serie[0] == ["2023-12-01", 0.0]
    assert all(v == 0.0 for _, v in serie[:27])
    # solo 4 consultas al BO (mar-jun), todas con el texto y corte nuevos
    assert len(consultas) == 4
    assert all(t == "fondo de asistencia laboral" for t, _, _ in consultas)
    assert all(d == "01/03/2026" for _, d, _ in consultas)
    # 3 menciones/420 de pleno → cobertura 0,714 → índice 0,4 (financiera=0)
    assert serie[-1] == ["2026-06-01", 0.4]
    assert serie[27] == ["2026-03-01", 0.1]


def test_fetch_fal_serie_fallback_historico(monkeypatch):
    """Si el BO no responde, cae al histórico acumulado sin romper."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)

    def fake_conteo(texto, desde="10/12/2023", hasta=None):
        raise ValueError("BO caído")

    monkeypatch.setattr(gestion, "_bo_conteo", fake_conteo)
    monkeypatch.setattr(gestion, "fetch_fal_modernizacion_laboral",
                        lambda: {"valor": 0.4})

    serie = descargar_series.fetch_fal_serie()

    # dic-2023 a jul-2026 (el fallback incluye el mes corriente con el live)
    assert serie[0] == ["2023-12-01", 0.0]
    assert serie[-1] == ["2026-07-01", 0.4]
