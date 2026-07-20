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
    """La serie sigue la escala de tres etapas de la card (ADR-0098).

    Antes de mar-2026 no se consulta el BO —no había instrumento que adoptar—
    pero la serie NO vale cero desde el arranque: cada hito normativo la sube
    en el mes en que se publicó su norma. El primero es el marco financiero de
    la CNV (Resolución General 1071/2025, jun-2025), así que dic-2023 →
    may-2025 son los únicos meses en cero.
    """
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

    # dic-2023 a jun-2026 = 31 puntos
    assert len(serie) == 31
    assert serie[0] == ["2023-12-01", 0.0]
    # sólo dic-2023 → may-2025 están en cero: después entra el primer hito
    assert all(v == 0.0 for _, v in serie[:18])
    assert serie[18] == ["2025-06-01", 13.3]      # marco financiero CNV: 1 de 3 hitos
    assert serie[27] == ["2026-03-01", 26.7]      # + Ley 27.802: 2 de 3
    assert serie[-1] == ["2026-06-01", 40.2]      # + Decreto 408/2026: 3 de 3
    # el BO se consulta sólo desde mar-2026 (4 meses), con el texto y corte nuevos
    assert len(consultas) == 4
    assert all(t == "fondo de asistencia laboral" for t, _, _ in consultas)
    assert all(d == "01/03/2026" for _, d, _ in consultas)
    # el techo antes de la vigencia (1-nov-2026) es 60: ningún punto lo supera
    assert all(v <= 60.0 for _, v in serie), "sin vigencia, la serie no puede pasar de 60"


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
