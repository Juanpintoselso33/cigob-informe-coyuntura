"""datos_gob.get no se queda con una respuesta vacía ni recortada de la API de series.

Desde el 12-oct-2026 la API contesta 200 con la serie vacía o con menos filas según
el servidor que atienda; las cuatro corridas del 12 al 15-oct cayeron por eso.
"""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import datos_gob  # noqa: E402


class _R:
    def __init__(self, filas):
        self._cuerpo = {"data": [["2026-08-01", 1.0]] if filas else [], "count": filas}

    def raise_for_status(self):
        pass

    def json(self):
        return self._cuerpo


def _servidor(monkeypatch, respuestas):
    pedidos = []

    def get(url, params=None, **kw):
        pedidos.append(dict(params))
        r = respuestas[len(pedidos) - 1]
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(datos_gob.requests, "get", get)
    monkeypatch.setattr(datos_gob, "ESPERA", 0)
    return pedidos


def _filas(monkeypatch, respuestas):
    return datos_gob.get("u", params={"ids": "x"}).json()["count"]


def test_cada_lectura_es_un_pedido_distinto(monkeypatch):
    """La misma URL repetida devuelve la misma respuesta: no confirma nada."""
    pedidos = _servidor(monkeypatch, [_R(271)] * 3)
    datos_gob.get("u", params={"ids": "x"})
    assert len({p["_lectura"] for p in pedidos}) == 3
    assert all(p["ids"] == "x" for p in pedidos)


def test_una_lectura_recortada_no_gana(monkeypatch):
    _servidor(monkeypatch, [_R(167), _R(271), _R(167)])
    assert _filas(monkeypatch, None) == 271


def test_las_vacias_no_cuentan(monkeypatch):
    pedidos = _servidor(monkeypatch, [_R(0), _R(117), _R(0), _R(117), _R(0), _R(117)])
    assert _filas(monkeypatch, None) == 117
    assert len(pedidos) == 6


def test_todas_vacias_devuelve_vacia(monkeypatch):
    pedidos = _servidor(monkeypatch, [_R(0)] * datos_gob.LECTURAS_MAX)
    assert datos_gob.get("u", params={"ids": "x"}).json()["data"] == []
    assert len(pedidos) == datos_gob.LECTURAS_MAX


def test_pocas_buenas_igual_devuelve_la_mejor(monkeypatch):
    _servidor(monkeypatch, [_R(0)] * (datos_gob.LECTURAS_MAX - 1) + [_R(210)])
    assert _filas(monkeypatch, None) == 210


def test_la_red_caida_se_reintenta_una_sola_vez(monkeypatch):
    pedidos = _servidor(monkeypatch, [requests.Timeout("t"), requests.Timeout("t"), _R(9)])
    with pytest.raises(requests.Timeout):
        datos_gob.get("u", params={"ids": "x"})
    assert len(pedidos) == 2


def test_sin_count_es_una_sola_lectura(monkeypatch):
    class _SinCount(_R):
        def json(self):
            return {"data": [["2026-08-01", 1.0]]}
    pedidos = _servidor(monkeypatch, [_SinCount(1)])
    datos_gob.get("u", params={"ids": "x"})
    assert len(pedidos) == 1
