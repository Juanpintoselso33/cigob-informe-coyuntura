"""Regresión offline: serie mensual de ratio_dnu con ventana móvil (ADR-0058)."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import politica


class _RespuestaHome:
    text = '<form action="/infolegInternet/buscarNormas.do">'

    def raise_for_status(self):
        return None


def test_fetch_ratio_dnu_serie_ventana_movil_por_mes(monkeypatch):
    """Un punto por MES (no por año), cada uno con su propia consulta a
    InfoLeg sobre la ventana móvil de 365 días que cierra ese mes."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 2, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(descargar_series.requests, "Session", lambda: _SesionFake())

    ventanas_vistas = []

    def fake_count(session, action_url, tipo, desde, hasta, texto=""):
        ventanas_vistas.append((tipo, desde, hasta, texto))
        return {"1": 10, "2": 15}[tipo]

    monkeypatch.setattr(politica, "_infoleg_session_count", fake_count)
    monkeypatch.setattr(politica, "_infoleg_contar_dnus",
                        lambda ses, au, desde, hasta:
                            (fake_count(ses, au, "2", desde, hasta,
                                        "necesidad y urgencia"), []))

    serie = descargar_series.fetch_ratio_dnu_serie()

    assert serie == [
        ["2023-12-01", 1.5],
        ["2024-01-01", 1.5],
        ["2024-02-01", 1.5],
    ]
    # 3 meses × 2 consultas (leyes + dnus) = 6 llamadas, ninguna ventana repetida
    assert len(ventanas_vistas) == 6
    ventanas_dnu = [(desde, hasta) for tipo, desde, hasta, _ in ventanas_vistas if tipo == "2"]
    assert len(set(ventanas_dnu)) == 3
    assert all(texto == "necesidad y urgencia" for tipo, *_, texto in ventanas_vistas if tipo == "2")


def test_fetch_ratio_dnu_serie_omite_mes_sin_leyes(monkeypatch):
    """Si un mes trae 0 leyes (fallo de búsqueda), se omite ese punto en vez
    de dividir por cero — mismo criterio que el indicador titular."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 1, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(descargar_series.requests, "Session", lambda: _SesionFake())

    def fake_count(session, action_url, tipo, desde, hasta, texto=""):
        # diciembre sin leyes, enero con datos normales
        if hasta == date(2023, 12, 31):
            return 0 if tipo == "1" else 5
        return {"1": 10, "2": 15}[tipo]

    monkeypatch.setattr(politica, "_infoleg_session_count", fake_count)
    monkeypatch.setattr(politica, "_infoleg_contar_dnus",
                        lambda ses, au, desde, hasta:
                            (fake_count(ses, au, "2", desde, hasta,
                                        "necesidad y urgencia"), []))

    serie = descargar_series.fetch_ratio_dnu_serie()

    assert serie == [["2024-01-01", 1.5]]
