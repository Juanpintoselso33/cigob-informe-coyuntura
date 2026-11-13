"""Un sitio caído de la Cámara no congela el cinturón político entero.

Del 10 al 12-nov-2026 datos.hcdn.gob.ar y votaciones.hcdn.gob.ar no respondían:
cada pedido esperaba 20 s, politica.py se pasaba de sus 10 minutos y TODAS las
cards de política salían de caché. Tras dos fallas de red seguidas contra un
host de la Cámara, el resto de la corrida no le pide más.
"""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica


@pytest.fixture
def red(monkeypatch):
    llamadas = []

    def falsa(self, method, url, *a, **k):
        llamadas.append(url)
        if "hcdn.gob.ar" in url and "caido" in url:
            raise requests.ReadTimeout("Read timed out. (read timeout=20)")
        r = requests.Response()
        r.status_code = 200
        return r

    monkeypatch.setattr(requests.Session, "request", falsa)
    monkeypatch.setattr(politica, "_hcdn_fallas", {})
    politica._instalar_corte_hcdn()
    return llamadas


def test_tras_dos_fallas_el_host_se_corta_sin_esperar(red):
    for _ in range(2):
        with pytest.raises(requests.Timeout):
            requests.get("https://datos.hcdn.gob.ar/caido")
    with pytest.raises(requests.ConnectionError, match="cortado"):
        requests.get("https://datos.hcdn.gob.ar/caido/otra")
    assert len(red) == 2  # el tercero ni salió a la red


def test_el_corte_es_por_host_y_no_toca_otras_fuentes(red):
    for _ in range(2):
        with pytest.raises(requests.Timeout):
            requests.get("https://votaciones.hcdn.gob.ar/caido")
    assert requests.get("https://www.hcdn.gob.ar/sesiones/").status_code == 200
    assert requests.get("https://www.boletinoficial.gob.ar/caido").status_code == 200


def test_una_respuesta_buena_reinicia_la_cuenta(red):
    with pytest.raises(requests.Timeout):
        requests.get("https://datos.hcdn.gob.ar/caido")
    requests.get("https://datos.hcdn.gob.ar/anda")
    with pytest.raises(requests.Timeout):
        requests.get("https://datos.hcdn.gob.ar/caido")
    with pytest.raises(requests.Timeout):  # todavía no cortó: la cuenta volvió a cero
        requests.get("https://datos.hcdn.gob.ar/caido")


def test_las_pruebas_no_corren_con_el_corte_puesto():
    """Sólo se instala en `__main__`: importar el módulo no lo activa."""
    texto = (Path(politica.__file__)).read_text(encoding="utf-8")
    assert texto.rstrip().endswith('if __name__ == "__main__":\n    _instalar_corte_hcdn()\n    main()')
