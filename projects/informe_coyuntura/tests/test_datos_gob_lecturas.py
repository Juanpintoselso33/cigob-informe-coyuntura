"""datos_gob.get no se queda con una respuesta vacía ni recortada de la API de series.

Desde el 12-oct-2026 la API contesta 200 con la serie vacía o con menos filas según
el servidor que atienda, y hay series que ningún servidor devuelve enteras; las
cuatro corridas del 12 al 15-oct cayeron por eso. El catálogo (`time_index_size`)
sí dice cuántas filas tiene la serie, y el CSV oficial las trae todas.
"""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import datos_gob  # noqa: E402

CSV = ("indice_tiempo,salarios,otros\n"
       "2026-06-01,10,1\n2026-07-01,20,\n2026-08-01,30,3\n")


class _R:
    def __init__(self, filas, declaradas=None, sid="x"):
        campo = {"id": sid, "title": "salarios", "downloadURL": "csv://imig"}
        if declaradas is not None:
            campo["time_index_size"] = str(declaradas)
        self._cuerpo = {"data": [["2026-08-01", float(filas)]] if filas else [],
                        "count": filas,
                        "meta": [{"frequency": "month"}, {"field": campo}]}

    def raise_for_status(self):
        pass

    def json(self):
        return self._cuerpo


class _Archivo:
    content = CSV.encode()

    def raise_for_status(self):
        pass


def _servidor(monkeypatch, respuestas):
    pedidos = []

    def get(url, params=None, **kw):
        if url == "csv://imig":
            return _Archivo()
        pedidos.append(dict(params))
        r = respuestas[len(pedidos) - 1]
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(datos_gob.requests, "get", get)
    monkeypatch.setattr(datos_gob, "ESPERA", 0)
    monkeypatch.setattr(datos_gob, "_csvs", {})
    return pedidos


def _pedir(**params):
    return datos_gob.get("u", params={"ids": "x", **params}).json()


def test_completa_a_la_primera_es_un_solo_pedido(monkeypatch):
    pedidos = _servidor(monkeypatch, [_R(128, 128)])
    assert _pedir()["count"] == 128
    assert len(pedidos) == 1
    assert pedidos[0]["metadata"] == "full"


def test_vacia_o_recortada_no_se_acepta(monkeypatch):
    pedidos = _servidor(monkeypatch, [_R(0, 128), _R(28, 128), _R(128, 128)])
    assert _pedir()["count"] == 128
    assert len(pedidos) == 3


def test_cada_lectura_es_un_pedido_distinto(monkeypatch):
    """La misma URL repetida devuelve la misma respuesta: no confirma nada."""
    pedidos = _servidor(monkeypatch, [_R(28, 128), _R(128, 128)])
    _pedir()
    assert len({p["_lectura"] for p in pedidos}) == 2


def test_nunca_completa_usa_el_csv_oficial(monkeypatch):
    _servidor(monkeypatch, [_R(28, 128), _R(0, 128)] * 3)
    d = _pedir(sort="desc", limit=2)
    assert d["data"] == [["2026-08-01", 30.0], ["2026-07-01", 20.0]]
    assert d["count"] == 3


def test_el_csv_salta_las_celdas_vacias(monkeypatch):
    _servidor(monkeypatch, [_R(0, 128)] * datos_gob.LECTURAS_MAX)
    monkeypatch.setattr(datos_gob, "_campo",
                        lambda c: {"downloadURL": "csv://imig", "title": "otros",
                                   "time_index_size": "128"})
    d = _pedir()
    assert d["data"] == [["2026-06-01", 1.0], ["2026-08-01", 3.0]]


def test_varias_series_se_piden_de_a_una(monkeypatch):
    pedidos = _servidor(monkeypatch, [_R(5, 5, "a"), _R(7, 7, "b")])
    d = datos_gob.get("u", params={"ids": "a,b", "sort": "desc"}).json()
    assert [p["ids"] for p in pedidos] == ["a", "b"]
    assert [m["field"]["id"] for m in d["meta"] if "field" in m] == ["a", "b"]
    assert d["data"] == [["2026-08-01", 5.0, 7.0]]


def test_sin_catalogo_gana_la_mas_larga(monkeypatch):
    _servidor(monkeypatch, [_R(167), _R(271), _R(167)])
    assert _pedir()["count"] == 271


def test_la_red_caida_se_reintenta_una_sola_vez(monkeypatch):
    pedidos = _servidor(monkeypatch, [requests.Timeout("t"), requests.Timeout("t"), _R(9, 9)])
    with pytest.raises(requests.Timeout):
        _pedir()
    assert len(pedidos) == 2


def test_sin_count_es_una_sola_lectura(monkeypatch):
    class _SinCount(_R):
        def json(self):
            return {"data": [["2026-08-01", 1.0]]}
    pedidos = _servidor(monkeypatch, [_SinCount(1)])
    _pedir()
    assert len(pedidos) == 1


def test_el_csv_se_corta_en_el_fin_que_declara_el_catalogo(monkeypatch):
    """El CSV se actualiza antes que la API: el mes que el catálogo todavía no
    declara no entra, o dos series del mismo indicador terminan en meses
    distintos (16-oct-2026, SIPA: 174 filas por la API, 175 en el CSV)."""
    _servidor(monkeypatch, [_R(0, 128)] * datos_gob.LECTURAS_MAX)
    monkeypatch.setattr(datos_gob, "_campo",
                        lambda c: {"downloadURL": "csv://imig", "title": "salarios",
                                   "time_index_size": "128", "time_index_end": "2026-07-01"})
    d = _pedir()
    assert d["data"] == [["2026-06-01", 10.0], ["2026-07-01", 20.0]]
    assert d["count"] == 2
