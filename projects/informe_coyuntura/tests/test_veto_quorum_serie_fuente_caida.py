"""Si la Cámara de Diputados no responde, la serie de sesiones en minoría falla
como fuente caída, no como «el fetcher no devolvió puntos».

El 10 y 11-nov-2026 hcdn.gob.ar no respondía a los runners de GitHub, la serie
se tragaba el timeout y devolvía una lista vacía, y el aviso de Slack decía
«casi seguro es del código». El error tiene que subir con su texto de red.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aviso_slack
import descargar_series


def test_el_timeout_de_la_camara_sube_tal_cual(monkeypatch):
    def caida():
        raise TimeoutError("HTTPSConnectionPool(host='www.hcdn.gob.ar', port=443): Read timed out.")

    monkeypatch.setattr(descargar_series.politica, "_hcdn_sesiones_legislativas", caida)
    with pytest.raises(TimeoutError, match="timed out"):
        descargar_series.fetch_veto_quorum_serie()


def test_el_aviso_lo_lee_como_red():
    msg = "HTTPSConnectionPool(host='www.hcdn.gob.ar', port=443): Read timed out. (read timeout=20)"
    assert aviso_slack.RUIDO_DE_RED.search(msg)
    assert not aviso_slack.RUIDO_DE_RED.search("el fetcher no devolvió puntos")
