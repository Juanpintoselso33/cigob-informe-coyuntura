"""El buscador de proyectos de Diputados reemplaza al CKAN caído (ADR-0432).

Sin red: se reemplazan `buscar` y `detalle` por fixtures con la forma que
devuelve la API (`www.hcdn.gob.ar/proyectos/buscador/api/v1/proyectos`).
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import hcdn_buscador as hb  # noqa: E402
import politica  # noqa: E402


def _item(clave, exp, titulo, fecha, ley=None, camara="Diputados", autor="PODER EJECUTIVO",
          numero=100):
    return {"clave": clave, "expediente": exp, "titulo": titulo, "publicacion_fecha": fecha,
            "ley_nro": ley, "camara_origen": camara, "autor_bloque": autor,
            "periodo": 143, "publicacion_tipo": "TP", "publicacion_numero": numero}


def test_los_avisos_del_ejecutivo_no_son_proyectos_de_ley():
    for t in ("COMUNICA EL DICTADO DEL DECRETO DE NECESIDAD Y URGENCIA 274/25",
              "COMUNICACION DEL DICTADO DEL DECRETO 782",
              "REMITE INFORME SOBRE LAS OPERACIONES DE CREDITO PUBLICO",
              "SOLICITA ACUERDO PARA DESIGNAR EMBAJADOR",
              "SOLICITAR ACUERDO PARA PROMOVER AL GRADO INMEDIATO SUPERIOR"):
        assert not hb.es_proyecto_de_ley({"titulo": t}), t
    for t in ("REFORMA PARA EL FORTALECIMIENTO ELECTORAL.",
              "PRESUPUESTO GENERAL DE LA ADMINISTRACION NACIONAL PARA EL EJERCICIO FISCAL 2026",
              "SE AUTORIZA LA SALIDA DE PERSONAL Y/O MEDIOS DEL ESTADO MAYOR CONJUNTO"):
        assert hb.es_proyecto_de_ley({"titulo": t}), t


def test_la_clave_del_buscador_es_el_proyecto_id_del_ckan():
    assert hb.proyecto_id("pap-290726") == "HCDN290726"
    assert hb.proyecto_id("folio-102861") is None


def test_la_sancion_es_el_ultimo_movimiento_de_sancion_con_fecha():
    det = {"movimientos": [
        {"fecha": None, "texto": "PASA A SENADO"},
        {"fecha": "2026-05-20", "texto": "CONSIDERACION Y APROBACION CON MODIFICACIONES"},
        {"fecha": "2026-06-01", "texto": "TEXTO DE LA MEDIA SANCION"},
        {"fecha": "2026-09-24", "texto": "CONSIDERACION Y SANCION"},
        {"fecha": "2026-09-24", "texto": "INSERCIONES"}]}
    assert hb.fecha_sancion(det) == "2026-09-24"
    assert hb.fecha_sancion({"movimientos": [{"fecha": "2026-06-01",
                                              "texto": "TEXTO DE LA MEDIA SANCION"}]}) is None


@pytest.fixture
def buscador(monkeypatch):
    items = {
        "PE": [_item("pap-1", "0022-PE-2024", "REFORMA PARA EL FORTALECIMIENTO ELECTORAL.",
                     "2024-11-21", ley=27783),
               _item("pap-2", "0021-PE-2024", "REFORMAS A LA LEY 23298", "2024-11-21"),
               _item("pap-3", "0125-PE-2024", "COMUNICACION DEL DICTADO DEL DECRETO 985/24",
                     "2024-11-19"),
               _item("pap-4", "0294-PE-2026", "APRUEBESE EL ACUERDO", "2024-11-20",
                     camara="Senado"),
               _item("pap-5", "0139-PE-2024", "PROYECTO SIN FECHA", None)],
        "JGM": [_item("pap-6", "0014-JGM-2025", "PRESUPUESTO GENERAL", "2024-12-01",
                      ley=27798)],
    }
    sanciones = {"pap-1": "2025-02-20", "pap-6": "2025-12-26"}
    monkeypatch.setattr(hb, "buscar", lambda **f: items[f["sigla"]])
    monkeypatch.setattr(hb, "detalle", lambda c: {"movimientos": [
        {"fecha": sanciones[c], "texto": "CONSIDERACION Y SANCION"}]})
    return items


def test_proyectos_pe_deja_solo_los_de_ley_que_entran_por_diputados(buscador):
    filas = {f["PROYECTO_ID"]: f for f in hb.proyectos_pe("2023-01-01")}
    assert set(filas) == {"HCDN1", "HCDN2", "HCDN6"}
    assert filas["HCDN1"]["SANCION_DEFINITIVA"] == "2025-02-20"
    assert filas["HCDN2"]["SANCION_DEFINITIVA"] is None
    assert filas["HCDN1"]["PUBLICACION_ID"] == "HCDN143TP100"


def test_eficacia_usa_el_buscador_si_el_ckan_no_responde(buscador, monkeypatch):
    import requests

    def caido(*a, **k):
        raise requests.ConnectionError("datos.hcdn.gob.ar 503")
    monkeypatch.setattr(politica, "_hcdn_paginate", caido)

    class Hoy(politica.date):
        @classmethod
        def today(cls):
            return politica.date(2026, 1, 15)
    monkeypatch.setattr(politica, "date", Hoy)
    r = politica.fetch_eficacia_legislativa()
    # Cohorte 2024-01-15 … 2025-01-15: HCDN1 (sancionado), HCDN2 y HCDN6 (sancionado).
    assert (r["aprobados_n"], r["enviados_n"], r["valor"]) == (2, 3, 66.7)
    assert "buscador" in r["fuente"]


def test_una_ley_sin_fecha_de_sancion_hace_fallar_el_calculo(buscador, monkeypatch):
    monkeypatch.setattr(hb, "detalle", lambda c: {"movimientos": []})
    with pytest.raises(ValueError, match="sin fecha de sanción"):
        politica._eficacia_filas_buscador("2023-01-01")


def test_indice_por_od_sin_numeracion_del_senado(monkeypatch):
    monkeypatch.setattr(hb, "buscar", lambda **f: (
        [_item("pap-290725", "0032-S-2026", "INVIOLABILIDAD DE LA PROPIEDAD PRIVADA.", "2026-03-01"),
         _item("pap-292009", "2248-D-2026", "CODIGO PENAL. VANDALISMO RURAL", "2026-05-01",
               autor="PRO")]
        if f["od_anio"] == 2026 else []))
    dictamenes = {"pap-290725": [{"camara": "Senado", "od_nro": 104, "od_anio": 2026, "fecha": "2026-05-20"},
                                 {"camara": "Diputados", "od_nro": 448, "od_anio": 2026, "fecha": "2026-10-16"}],
                  "pap-292009": [{"camara": "Diputados", "od_nro": 448, "od_anio": 2026, "fecha": "2026-10-09"}]}
    monkeypatch.setattr(hb, "detalle", lambda c: {"dictamenes": dictamenes[c]})
    idx = hb.indice_origen_por_od({448}, 2025)
    assert idx["claves"] is None
    assert idx["ids"] == {"HCDN290725"}
    assert sorted(idx["dictamenes"][448]) == [("2026-10-09", "HCDN292009"), ("2026-10-16", "HCDN290725")]
    acta = {"titulo": "O.D. 448 - LEY DE INVIOLABILIDAD", "fecha": "2026-10-21"}
    assert politica._vsb_origen_pe_diputados(acta, idx) is True


def test_sin_numeracion_del_senado_la_votacion_del_senado_espera():
    entrada = {"expedientes": ["CD-12/25-PL"]}
    assert politica._vsb_origen_pe_senado(entrada, {"ids": set(), "dictamenes": {}, "claves": None}) is None
    assert politica._vsb_origen_pe_senado(entrada, {"ids": set(), "dictamenes": {}, "claves": set()}) is False


def test_la_serie_del_buscador_conserva_los_meses_anteriores(monkeypatch, tmp_path):
    import descargar_series as ds
    previas = [["2025-11-01", "eficacia_legislativa", "28.0"], ["2025-12-01", "eficacia_legislativa", "25.0"],
               ["2026-01-01", "eficacia_legislativa", "99.0"]]
    monkeypatch.setattr(ds, "_filas_previas", lambda c, i: previas)
    monkeypatch.setattr(ds, "_hcdn_ventanas_12m", lambda: [
        ("2025-12", "2024-12-31", "2025-12-31"), ("2026-01", "2025-01-31", "2026-01-31")])
    monkeypatch.setattr(politica, "_eficacia_filas_buscador", lambda d: [
        {"PROYECTO_ID": "HCDN1", "PUBLICACION_ID": "x", "PUBLICACION_FECHA": "2024-06-01",
         "LEY": 1, "SANCION_DEFINITIVA": "2025-02-20"},
        {"PROYECTO_ID": "HCDN2", "PUBLICACION_ID": "x", "PUBLICACION_FECHA": "2024-07-01",
         "LEY": None, "SANCION_DEFINITIVA": None}])
    serie = dict(map(tuple, ds._eficacia_serie_buscador()))
    assert serie["2025-11-01"] == 28.0 and serie["2025-12-01"] == 25.0   # del CKAN
    assert serie["2026-01-01"] == 50.0                                    # recalculado


def test_se_remite_tambien_es_aviso():
    assert not hb.es_proyecto_de_ley({"titulo": "SE REMITE LA CUENTA DE INVERSION DEL EJERCICIO 2025"})


def test_un_proyecto_en_dos_od_queda_anotado_en_las_dos(monkeypatch):
    """Revisión del 16-nov: con `vistos` por clave, la segunda OD perdía el
    dictamen del proyecto del Ejecutivo y su votación se guardaba como False."""
    por_od = {100: [_item("pap-1", "0001-PE-2026", "LEY X", "2026-03-01")],
              448: [_item("pap-1", "0001-PE-2026", "LEY X", "2026-03-01"),
                    _item("pap-2", "0002-D-2026", "LEY Y", "2026-03-01", autor="PRO")]}
    monkeypatch.setattr(hb, "buscar", lambda **f: por_od[f["od_nro"]] if f["od_anio"] == 2026 else [])
    dets = {"pap-1": [{"camara": "Diputados", "od_nro": 100, "od_anio": 2026, "fecha": "2026-09-01"},
                      {"camara": "Diputados", "od_nro": 448, "od_anio": 2026, "fecha": "2026-10-16"}],
            "pap-2": [{"camara": "Diputados", "od_nro": 448, "od_anio": 2026, "fecha": "2026-10-16"}]}
    monkeypatch.setattr(hb, "detalle", lambda c: {"dictamenes": dets[c]})
    idx = hb.indice_origen_por_od({100, 448}, 2025)
    assert ("2026-10-16", "HCDN1") in idx["dictamenes"][448]
    acta = {"titulo": "O.D. 448 - LEY", "fecha": "2026-10-21"}
    assert politica._vsb_origen_pe_diputados(acta, idx) is True


def test_el_paginado_corta_por_el_total_y_no_por_el_tamano(monkeypatch):
    paginas = {1: {"total": 25, "items": [{"clave": f"pap-{i}"} for i in range(15)]},
               2: {"total": 25, "items": [{"clave": f"pap-{i}"} for i in range(15, 25)]},
               3: {"total": 25, "items": []}}
    monkeypatch.setattr(hb, "_get", lambda url, p: paginas[p["pagina"]])
    assert len(hb.buscar(sigla="PE")) == 25


def test_un_ckan_con_dato_invalido_no_pasa_al_buscador(monkeypatch):
    def invalido(*a, **k):
        raise ValueError("CKAN sin result")
    monkeypatch.setattr(politica, "_hcdn_paginate", invalido)
    monkeypatch.setattr(politica, "_eficacia_filas_buscador",
                        lambda d: pytest.fail("un error de datos no debe ir al buscador"))
    assert politica.fetch_eficacia_legislativa() is None


def test_con_el_buscador_caido_la_votacion_queda_pendiente_no_en_false(monkeypatch):
    import requests
    cache = {"diputados": {"6019": {"fecha": "2026-10-21", "resultado": "AFIRMATIVO",
                                    "titulo": "O.D. 448 - LEY DE INVIOLABILIDAD. VOT. EN GRAL.",
                                    "origen_pe": None}},
             "senado": {}, "diputados_ausentes": []}
    monkeypatch.setattr(politica, "_vsb_titulo_diputados_es_ley_general", lambda t: True)
    monkeypatch.setattr(politica, "_vsb_guardar_cache", lambda c: None)

    def caido(*a, **k):
        raise requests.ConnectionError("caído")
    monkeypatch.setattr(politica, "_hcdn_paginate", caido)
    monkeypatch.setattr(hb, "buscar", caido)
    assert politica._vsb_resolver_origen(cache) is False
    assert cache["diputados"]["6019"]["origen_pe"] is None


# ── comisiones_caidas con caché incremental (ADR-0436) ────────────────────────

def _items_od():
    return [dict(_item("pap-10", "0010-D-2026", "LEY A", "2026-01-01"), tipo="LEY"),
            dict(_item("pap-11", "0011-D-2026", "DECLARAR DE INTERES", "2026-01-01"), tipo="DECLARACION")]


def test_la_cache_es_incremental(monkeypatch, tmp_path):
    pedidos = []
    monkeypatch.setattr(hb, "buscar", lambda **f: _items_od() if f["od_anio"] == 2026 else [])
    monkeypatch.setattr(hb, "detalle", lambda c: pedidos.append(c) or {
        "dictamenes": [{"camara": "Diputados", "od_nro": 5, "od_anio": 2026, "fecha": "2026-05-01"},
                       {"camara": "Senado", "od_nro": 9, "od_anio": 2026, "fecha": "2026-06-01"}],
        "movimientos": []})
    ruta = tmp_path / "cache.json"
    p = hb.dictamenes_diputados([2026], ruta, "2026-11-16")
    assert sorted(pedidos) == ["pap-10", "pap-11"]
    assert p["pap-10"]["dictamenes"] == [[5, 2026, "2026-05-01"]]       # sólo el de Diputados
    pedidos.clear()
    hb.dictamenes_diputados([2026], ruta, "2026-11-16")                  # mismo día: nada
    assert pedidos == []
    hb.dictamenes_diputados([2026], ruta, "2026-11-17")                  # otro día: sólo la ley sin sanción
    assert pedidos == ["pap-10"]


def test_comisiones_caidas_cuenta_la_ventana():
    proyectos = {"a": {"pid": "HCDN1", "dictamenes": [[5, 2026, "2026-05-01"]], "sanciones": ["2026-06-10"]},
                 "b": {"pid": "HCDN2", "dictamenes": [[6, 2026, "2026-05-02"]], "sanciones": []},
                 "c": {"pid": "HCDN3", "dictamenes": [[7, 2024, "2024-05-02"]], "sanciones": ["2026-06-01"]}}
    assert hb.comisiones_caidas(proyectos, "2025-11-16", "2026-11-16") == (2, 1)
    assert hb.comisiones_caidas(proyectos, "2020-01-01", "2020-12-31") is None
