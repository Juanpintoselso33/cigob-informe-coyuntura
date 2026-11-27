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
    monkeypatch.setattr(ipc_indec, "serie", lambda *a: original)


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


def test_alimentos_tambien_se_completa_desde_la_planilla(monkeypatch):
    """27-nov-2026: la card de alimentos leía sólo la API y septiembre entró tres
    semanas tarde (ADR-0443)."""
    pedidas = []
    monkeypatch.setattr(ipc_indec, "serie", lambda sid=ipc_indec.SERIE_ID: pedidas.append(sid) or
                        [["2026-08-01", 13000.0], ["2026-09-01", 13384.1945]])
    sid = "146.3_IALIMENNAL_DICI_M_45"
    r = datos_gob._completar_ipc(Resp({"data": [["2026-08-01", 13000.0]]}), {"ids": sid, "sort": "desc"})
    assert r.json()["data"][0] == ["2026-09-01", 13384.1945]
    assert pedidas == [sid]


def test_la_planilla_trae_la_fila_de_alimentos(monkeypatch):
    filas = [["Total nacional", 46266.0, 46296.0], ["", "", ""], ["Nivel general", 12514.15, 12785.93],
             ["Alimentos y bebidas no alcohólicas", 13384.19, 13647.83]]

    class Hoja:
        nrows = len(filas)
        def cell_value(self, r, c): return filas[r][c]
        def row_values(self, r): return filas[r]

    class Libro:
        datemode = 0
        def sheet_by_name(self, nombre): return Hoja()

    monkeypatch.setattr(ipc_indec.xlrd, "open_workbook", lambda **k: Libro())
    assert ipc_indec.parsear(b"", ipc_indec.SERIES["146.3_IALIMENNAL_DICI_M_45"])[-1] == ["2026-10-01", 13647.83]
    assert ipc_indec.parsear(b"")[-1] == ["2026-10-01", 12785.93]
