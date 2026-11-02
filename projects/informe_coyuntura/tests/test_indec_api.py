"""El EMAE y el índice de salarios salen de la API del INDEC (ADR-0417).

`datos_gob.get` deriva a `indec_api` los pedidos de esas series y tiene que
recibir lo mismo que daba datos.gob.ar: misma forma, mismas unidades. Un token
rechazado no vuelve a la copia (tiene que verse); cualquier otra falla, sí.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aviso_slack  # noqa: E402
import datos_gob  # noqa: E402
import indec_api  # noqa: E402
import macro  # noqa: E402

EMAE_IA = "143.3_ICE_SERVIA_2004_A_25"
SALARIOS = "149.1_TL_INDIIOS_OCTU_0_21"


class _R:
    def __init__(self, cuerpo, status=200):
        self._cuerpo, self.status_code = cuerpo, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise indec_api.requests.HTTPError(f"{self.status_code} Server Error")

    def json(self):
        return self._cuerpo


def _api(monkeypatch, filas_por_servicio, status=200):
    """Simula la API: filtra las filas como PostgREST (`eq.`) y pagina."""
    pedidos = []

    def get(url, params=None, headers=None, **kw):
        assert url.startswith(indec_api.BASE), url
        pedidos.append((url, dict(params)))
        if status != 200:
            return _R({}, status)
        filas = filas_por_servicio[url[len(indec_api.BASE):]]
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("eq."):
                filas = [f for f in filas if str(f.get(k)) == v[3:]]
        o, n = params["offset"], params["limit"]
        return _R(filas[o:o + n])

    monkeypatch.setenv("INDEC_API_TOKEN", "x.y.z")
    monkeypatch.setattr(indec_api.requests, "get", get)
    return pedidos


def _emae(periodos_valores):
    return [{"periodo": p, "tipo_de_indicador_descripcion": "Var % interanual serie original",
             "valor": v} for p, v in periodos_valores]


def test_el_emae_vuelve_en_fraccion_como_en_datos_gob(monkeypatch):
    _api(monkeypatch, {indec_api._EMAE: _emae([("202607", -1.47), ("202608", -1.74)])})
    r = datos_gob.get("https://apis.datos.gob.ar/series/api/series/",
                      params={"ids": EMAE_IA, "format": "json", "limit": 2, "sort": "desc"})
    assert r.json()["data"] == [["2026-08-01", pytest.approx(-0.0174)],
                                ["2026-07-01", pytest.approx(-0.0147)]]
    assert indec_api.via(EMAE_IA) == "Catálogo API-INDEC"


def test_la_coma_decimal_de_salarios_se_convierte(monkeypatch):
    filas = [{"periodo": "202608", "codigo": "0", "tipo_de_indicador": "Indice", "valor": "9973,55"},
             {"periodo": "202608", "codigo": "0", "tipo_de_indicador": "v_m", "valor": "2,6"},
             {"periodo": "202608", "codigo": "120", "tipo_de_indicador": "Indice", "valor": "8307,48"}]
    _api(monkeypatch, {"indice_salarios": filas})
    r = datos_gob.get("u", params={"ids": SALARIOS, "limit": 5, "sort": "desc"})
    assert r.json()["data"] == [["2026-08-01", 9973.55]]


def test_pagina_hasta_traer_todo(monkeypatch):
    monkeypatch.setattr(indec_api, "PAGINA", 2)
    meses = [(f"2026{m:02d}", float(m)) for m in range(1, 6)]
    pedidos = _api(monkeypatch, {indec_api._EMAE: _emae(meses)})
    r = indec_api.get({"ids": EMAE_IA, "limit": 100})
    assert len(r.json()["data"]) == 5 and len(pedidos) == 3


def test_varios_sectores_salen_alineados_por_id(monkeypatch):
    ids = list(macro.INDEC_EMAE_SECTORES)[:2]
    filas = [{"periodo": "202608", "codigo": c, "tipo_de_indicador": indec_api._INDICE_SECTOR,
              "valor": v} for c, v in (("A", 100.0), ("B", 200.0))]
    _api(monkeypatch, {indec_api._EMAE_SECTORES: filas})
    cuerpo = indec_api.get({"ids": ",".join(ids), "sort": "desc"}).json()
    assert [m["field"]["id"] for m in cuerpo["meta"] if "field" in m] == ids
    assert cuerpo["data"] == [["2026-08-01", 100.0, 200.0]]


def test_los_quince_sectores_de_macro_estan_mapeados_a_los_codigos_a_o():
    codigos = [indec_api.SERIES[s][1]["codigo"] for s in macro.INDEC_EMAE_SECTORES]
    assert codigos == list("ABCDEFGHIJKLMNO")


def test_si_la_api_cae_se_lee_la_copia(monkeypatch):
    _api(monkeypatch, {}, status=503)
    copia = _R({"data": [["2026-07-01", -0.0144]], "count": 1, "meta": []})
    monkeypatch.setattr(datos_gob, "_get", lambda url, params, **kw: copia)
    r = datos_gob.get("u", params={"ids": EMAE_IA, "limit": 1, "sort": "desc"})
    assert r is copia
    assert indec_api.via(EMAE_IA) == "vía datos.gob.ar"


@pytest.mark.parametrize("status", [401, 403])
def test_un_token_rechazado_no_vuelve_a_la_copia_y_no_parece_error_de_red(monkeypatch, status):
    _api(monkeypatch, {}, status=status)
    monkeypatch.setattr(datos_gob, "_get", lambda *a, **k: pytest.fail("volvió a la copia"))
    with pytest.raises(indec_api.TokenRechazado) as e:
        datos_gob.get("u", params={"ids": EMAE_IA, "limit": 1})
    assert not aviso_slack.RUIDO_DE_RED.search(str(e.value))


def test_token_vacio_en_la_corrida_falla(monkeypatch):
    monkeypatch.setenv("INDEC_API_TOKEN", "")
    with pytest.raises(indec_api.TokenRechazado):
        indec_api.get({"ids": EMAE_IA})


def test_sin_token_ni_variable_sigue_en_datos_gob(monkeypatch):
    assert not indec_api.atiende({"ids": EMAE_IA})
    copia = _R({"data": [], "count": 0, "meta": []})
    monkeypatch.setattr(datos_gob, "_get", lambda url, params, **kw: copia)
    assert datos_gob.get("u", params={"ids": EMAE_IA}) is copia


def test_un_pedido_con_variaciones_va_a_la_copia(monkeypatch):
    monkeypatch.setenv("INDEC_API_TOKEN", "x.y.z")
    assert not indec_api.atiende({"ids": EMAE_IA, "representation_mode": "percent_change"})
    assert not indec_api.atiende({"ids": EMAE_IA + ",otra"})
    assert indec_api.atiende({"ids": EMAE_IA, "format": "json", "limit": 2, "sort": "desc"})
