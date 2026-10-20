"""El IPC de la API se completa con la planilla del INDEC cuando la API se
atrasa (20-oct-2026: el INDEC llevaba una semana con septiembre y la API
seguía en agosto). Sin red: la planilla y la API se simulan."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import datos_gob   # noqa: E402
import ipc_indec   # noqa: E402

ORIGINAL = [["2026-07-01", 12076.3937], ["2026-08-01", 12276.766], ["2026-09-01", 12514.1508]]
API = [["2026-08-01", 12276.766], ["2026-07-01", 12076.3937]]


class Resp:
    def __init__(self, cuerpo):
        self.c = cuerpo

    def json(self):
        return self.c


def _con(monkeypatch, original=ORIGINAL):
    monkeypatch.setattr(ipc_indec, "serie", lambda: original)


def test_agrega_el_mes_que_la_api_todavia_no_tiene(monkeypatch):
    _con(monkeypatch)
    r = datos_gob._completar_ipc(Resp({"data": API, "count": 120}),
                                 {"ids": ipc_indec.SERIE_ID, "sort": "desc", "limit": 2})
    assert r.json()["data"] == [["2026-09-01", 12514.1508], ["2026-08-01", 12276.766]]


def test_no_empalma_si_el_mes_comun_no_coincide(monkeypatch):
    _con(monkeypatch, [["2026-08-01", 99.0], ["2026-09-01", 100.0]])
    r = datos_gob._completar_ipc(Resp({"data": API, "count": 120}),
                                 {"ids": ipc_indec.SERIE_ID, "sort": "desc"})
    assert r.json()["data"] == API


def test_una_variacion_o_un_corte_de_fechas_no_se_tocan(monkeypatch):
    _con(monkeypatch)
    for extra in ({"representation_mode": "percent_change"}, {"end_date": "2026-08-01"},
                  {"collapse": "year"}):
        r = datos_gob._completar_ipc(Resp({"data": API, "count": 120}),
                                     {"ids": ipc_indec.SERIE_ID, "sort": "desc", **extra})
        assert r.json()["data"] == API, extra


def test_ascendente_recortado_no_deja_un_hueco(monkeypatch):
    _con(monkeypatch)
    cuerpo = {"data": [["2016-12-01", 100.0]], "count": 120}
    r = datos_gob._completar_ipc(Resp(cuerpo), {"ids": ipc_indec.SERIE_ID, "limit": 1})
    assert r.json() is cuerpo


def test_ascendente_completo_suma_al_final(monkeypatch):
    _con(monkeypatch)
    asc = list(reversed(API))
    r = datos_gob._completar_ipc(Resp({"data": asc, "count": 2}),
                                 {"ids": ipc_indec.SERIE_ID, "limit": 1000})
    assert r.json()["data"][-1] == ["2026-09-01", 12514.1508]
    assert r.json()["count"] == 3


def test_si_la_planilla_falla_queda_la_api(monkeypatch):
    def rota():
        raise OSError("sin red")
    monkeypatch.setattr(ipc_indec, "serie", rota)
    cuerpo = {"data": API, "count": 120}
    assert datos_gob._completar_ipc(Resp(cuerpo), {"ids": ipc_indec.SERIE_ID}).json() is cuerpo


def test_respeta_start_date(monkeypatch):
    _con(monkeypatch)
    r = datos_gob._completar_ipc(Resp({"data": API, "count": 2}),
                                 {"ids": ipc_indec.SERIE_ID, "sort": "desc",
                                  "start_date": "2026-10-01"})
    assert r.json()["data"] == API


def test_un_mes_vacio_en_la_api_lo_reemplaza_el_original(monkeypatch):
    """Revisión de Codex: el mes nulo quedaba junto al completado, duplicado."""
    _con(monkeypatch)
    r = datos_gob._completar_ipc(Resp({"data": [["2026-09-01", None]] + API, "count": 121}),
                                 {"ids": ipc_indec.SERIE_ID, "sort": "desc", "limit": 2})
    assert r.json()["data"] == [["2026-09-01", 12514.1508], ["2026-08-01", 12276.766]]


def test_la_paginacion_no_se_completa(monkeypatch):
    _con(monkeypatch)
    for extra in ({"start": 1}, {"last": 1000}):
        cuerpo = {"data": API, "count": 120}
        r = datos_gob._completar_ipc(Resp(cuerpo), {"ids": ipc_indec.SERIE_ID, "sort": "desc", **extra})
        assert r.json() is cuerpo, extra


def test_la_metadata_acompana_a_los_datos(monkeypatch):
    _con(monkeypatch)
    meta = [{"frequency": "R/P1M"},
            {"field": {"id": ipc_indec.SERIE_ID, "time_index_end": "2026-08-01", "time_index_size": 117}}]
    r = datos_gob._completar_ipc(Resp({"data": API, "count": 117, "meta": meta}),
                                 {"ids": ipc_indec.SERIE_ID, "sort": "desc"})
    campo = r.json()["meta"][1]["field"]
    assert (campo["time_index_end"], campo["time_index_size"]) == ("2026-09-01", 118)
