"""Un acta de Diputados que no baja por requests se reintenta por curl.

Desde CI el acta 6026 dio ReadTimeout cuatro noches seguidas (nov-2026) y
congeló votos_sobre_bancas, que exige la lectura entera de las actas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica  # noqa: E402

_CURL_REAL = politica._curl_pdf   # conftest lo reemplaza en cada test


def test_si_requests_falla_se_usa_curl(monkeypatch):
    monkeypatch.setattr(politica, "_paced_get", lambda *a, **k: None)
    monkeypatch.setattr(politica, "_curl_pdf", lambda url: b"%PDF-1.4 acta")
    assert politica._diputados_acta_pdf(None, 6026) == b"%PDF-1.4 acta"


def test_si_curl_tambien_falla_es_fallo(monkeypatch):
    monkeypatch.setattr(politica, "_paced_get", lambda *a, **k: None)
    monkeypatch.setattr(politica, "_curl_pdf", lambda url: None)
    monkeypatch.setattr(politica, "_avisar_fallo_acta_diputados", lambda i: None)
    assert politica._diputados_acta_pdf(None, 6026) is politica._ACTA_FALLO


def test_curl_rechaza_lo_que_no_es_pdf(monkeypatch):
    class R:
        returncode, stdout = 0, b"<html>error</html>"
    monkeypatch.setattr(politica.subprocess, "run", lambda *a, **k: R())
    assert _CURL_REAL("https://x/acta.pdf") is None
