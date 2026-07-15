"""Regresiones offline para ratio_dnu con ventana móvil de 365 días (ADR-0058)."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import politica


class _RespuestaHome:
    text = '<form action="/infolegInternet/buscarNormas.do">'

    def raise_for_status(self):
        return None


class _RespuestaBusqueda:
    def __init__(self, texto):
        self.text = texto

    def raise_for_status(self):
        return None


def test_infoleg_session_count_arma_rango_de_fechas_explicito():
    """El POST usa desde/hasta explícitos (día/mes/año), no un año calendario
    completo — el cambio que habilita la ventana móvil (ADR-0058)."""
    capturado = {}

    class _SesionFake:
        def post(self, url, data, **kwargs):
            capturado["url"] = url
            capturado["data"] = data
            return _RespuestaBusqueda("Encontradas: 17")

    n = politica._infoleg_session_count(
        _SesionFake(), "https://x/buscar", "1",
        date(2025, 7, 16), date(2026, 7, 15),
    )

    assert n == 17
    assert capturado["data"]["tipoNorma"] == "1"
    assert capturado["data"]["diaPubDesde"] == "16"
    assert capturado["data"]["mesPubDesde"] == "07"
    assert capturado["data"]["anioPubDesde"] == "2025"
    assert capturado["data"]["diaPubHasta"] == "15"
    assert capturado["data"]["mesPubHasta"] == "07"
    assert capturado["data"]["anioPubHasta"] == "2026"


def test_infoleg_session_count_pasa_texto_de_dnu():
    class _SesionFake:
        def post(self, url, data, **kwargs):
            assert data["texto"] == "necesidad y urgencia"
            return _RespuestaBusqueda("Encontradas: 27")

    n = politica._infoleg_session_count(
        _SesionFake(), "https://x/buscar", "2",
        date(2025, 7, 16), date(2026, 7, 15), texto="necesidad y urgencia",
    )
    assert n == 27


def test_infoleg_session_count_falla_sin_conteo():
    class _SesionFake:
        def post(self, url, data, **kwargs):
            return _RespuestaBusqueda("sin resultados")

    try:
        politica._infoleg_session_count(
            _SesionFake(), "https://x/buscar", "1", date(2025, 1, 1), date(2026, 1, 1),
        )
        assert False, "debía lanzar ValueError"
    except ValueError as e:
        assert "Conteo no encontrado" in str(e)


def test_fetch_ratio_dnu_usa_ventana_movil_365_dias(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(politica, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(politica.requests, "Session", lambda: _SesionFake())

    llamadas = []

    def fake_count(session, action_url, tipo, desde, hasta, texto=""):
        llamadas.append((tipo, desde, hasta, texto))
        return {"1": 17, "2": 27}[tipo]

    monkeypatch.setattr(politica, "_infoleg_session_count", fake_count)

    ind = politica.fetch_ratio_dnu()

    assert ind["valor"] == round(27 / 17, 3)
    assert ind["dnu_count"] == 27
    assert ind["leyes_count"] == 17
    assert ind["ventana_dias"] == 365
    assert "periodo" not in ind
    assert len(llamadas) == 2
    for tipo, desde, hasta, texto in llamadas:
        assert hasta == date(2026, 7, 15)
        assert desde == date(2025, 7, 15)  # 365 días antes, sin resetear en enero
        if tipo == "2":
            assert texto == "necesidad y urgencia"


def test_fetch_ratio_dnu_none_si_cero_leyes(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(politica, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(politica.requests, "Session", lambda: _SesionFake())
    monkeypatch.setattr(politica, "_infoleg_session_count", lambda *a, **k: 0)

    assert politica.fetch_ratio_dnu() is None
