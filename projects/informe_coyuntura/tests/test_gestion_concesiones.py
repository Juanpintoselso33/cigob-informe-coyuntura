# -*- coding: utf-8 -*-
"""Concesiones viales: el acto jurídico manda sobre el estado del portal (ADR-0244).

El indicador leía el estado de cada proceso en CONTRAT.AR. CONTRAT.AR **se queda
viejo**: al 25-ago-2026 mostraba «Disponible Para Adjudicar» dos etapas ya
adjudicadas por resolución publicada —la II-B desde el 28-jul y la III desde el
24-ago—, y el tablero publicaba **28,7%** con el plan **entero** adjudicado.

La auditoría del 25-ago-2026 detectó la Etapa III y estimó el indicador en ~71,6%.
No detectó la II-B, que estaba adjudicada desde un mes antes: el número correcto
es 100%.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import gestion

FIXTURE = Path(__file__).parent / "fixtures" / "rfc_concesiones.json"


@pytest.fixture(scope="module")
def datos():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def sin_red(datos, monkeypatch):
    """Enchufa el fixture donde el colector iría a las tres fuentes."""
    monkeypatch.setattr(gestion, "_rfc_km_por_etapa", lambda: dict(datos["km_por_etapa"]))
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc",
                        lambda: [(p["proceso"], p["nombre"], p["estado_contratar"])
                                 for p in datos["procesos"]])
    monkeypatch.setattr(gestion, "_adjudicacion_publicada",
                        lambda proc: datos["adjudicaciones_boletin"].get(proc))
    return datos


def test_el_plan_entero_esta_adjudicado(sin_red, datos):
    card = gestion.fetch_concesiones_infraestructura()
    assert card is not None
    assert card["valor"] == datos["esperado"]["valor"] == 100.0
    assert card["km_adjudicados"] == datos["esperado"]["km_adjudicados"]
    assert card["km_totales"] == datos["esperado"]["km_totales"]


def test_el_valor_erroneo_no_puede_volver(sin_red, datos):
    """28,7% era contar sólo lo que CONTRAT.AR declaraba adjudicado."""
    card = gestion.fetch_concesiones_infraestructura()
    assert abs(card["valor"] - datos["esperado"]["valor_erroneo"]) > 10
    assert card["valor"] == 100.0          # y no 0%: alejarse de 28,7 no alcanza


def test_supera_la_cota_que_estimo_la_auditoria(sin_red, datos):
    """La auditoría, viendo sólo la Etapa III, estimó ≈71,65% como piso.

    Que el resultado quede por encima no la contradice: la II-B agrega 2.557 km
    que la auditoría no había visto."""
    card = gestion.fetch_concesiones_infraestructura()
    assert card["valor"] > datos["esperado"]["cota_inferior_auditoria"]


def test_la_suma_es_trazable_tramo_por_tramo(sin_red, datos):
    """Un porcentaje de avance sin el inventario que lo forma no es auditable:
    fue lo que dejó pasar 28,7% durante semanas."""
    card = gestion.fetch_concesiones_infraestructura()
    inv = card["inventario_etapas"]
    assert len(inv) == 4
    suma = sum(i["km"] for i in inv if i["adjudicado"])
    assert round(suma) == card["km_adjudicados"]
    assert round(sum(datos["km_por_etapa"].values())) == card["km_totales"]


def test_cada_etapa_declara_de_donde_sale_su_estado(sin_red):
    """El estado sale del store fechado (resoluciones del Boletín), no del portal.
    Las cuatro etapas citan el Boletín; CONTRAT.AR sólo aparece como dato aparte."""
    card = gestion.fetch_concesiones_infraestructura()
    assert {i["etapa"]: i["fuente_estado"] for i in card["inventario_etapas"]} == {
        "I": "Boletín Oficial", "II": "Boletín Oficial",
        "II-B": "Boletín Oficial", "III": "Boletín Oficial"}


def test_las_adjudicadas_por_boletin_citan_su_resolucion(sin_red):
    card = gestion.fetch_concesiones_infraestructura()
    por_boletin = [i for i in card["inventario_etapas"]
                   if i["fuente_estado"] == "Boletín Oficial"]
    assert por_boletin
    for i in por_boletin:
        assert i["resolucion"] and i["fecha_adjudicacion"]
        assert i["resolucion"] in card["detalle_txt"]
    resoluciones = {i["etapa"]: i["resolucion"] for i in por_boletin}
    assert "1379" in resoluciones["III"]
    assert "1149" in resoluciones["II-B"]


def test_la_card_avisa_que_el_portal_esta_atrasado(sin_red):
    """El desacople entre las dos fuentes es información, no ruido a esconder."""
    card = gestion.fetch_concesiones_infraestructura()
    assert "CONTRAT.AR todavía no refleja" in card["detalle_txt"]


def test_las_adjudicadas_por_boletin_citan_su_resolucion_incluso_las_viejas(sin_red):
    card = gestion.fetch_concesiones_infraestructura()
    res = {i["etapa"]: i["resolucion"] for i in card["inventario_etapas"]}
    assert "80" in res["I"] and "706" in res["II"]


def test_contratar_caido_el_indicador_sale_fresco(sin_red, datos, monkeypatch, capsys):
    """El caso de 15 de 33 noches: CONTRAT.AR da ConnectTimeout desde los runners.
    El estado sale del store fechado: el indicador se calcula, NO queda
    desactualizado y el timeout es una línea [WARN], no una caída."""
    import requests

    def _timeout():
        raise requests.exceptions.ConnectTimeout("contratar.gob.ar timeout")

    llamadas = []
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", _timeout)
    monkeypatch.setattr(gestion, "_adjudicacion_publicada",
                        lambda proc: llamadas.append(proc))
    card = gestion.fetch_concesiones_infraestructura()
    assert card is not None
    assert card["desactualizado"] is False
    assert card["valor"] == 100.0
    assert card["km_adjudicados"] == datos["esperado"]["km_adjudicados"]
    assert len(card["inventario_etapas"]) == 4
    assert "[WARN]" in capsys.readouterr().out
    assert llamadas == []                    # sin detector no hay nada que consultar
    assert "no se pudo contrastar" in card["advertencia_fuente"].lower()


def test_contratar_arriba_el_resultado_es_el_mismo(sin_red, datos, capsys):
    card = gestion.fetch_concesiones_infraestructura()
    assert card["valor"] == 100.0
    assert card["advertencia_fuente"] == "CONTRAT.AR todavía no refleja la adjudicación de II-B, III, que constan en el Boletín Oficial"
    assert "[AVISO]" not in capsys.readouterr().out


def _con_etapa_iv(monkeypatch, sin_red, estado, resolucion):
    """Misma base y MISMO denominador (con IV: 10.091 km) para el caso negativo
    y el positivo, así el cálculo cambia de verdad según IV entre o no."""
    monkeypatch.setattr(gestion, "_rfc_km_por_etapa",
                        lambda: {**sin_red["km_por_etapa"], "IV": 1000.0})
    base = [(p["proceso"], p["nombre"], p["estado_contratar"]) for p in sin_red["procesos"]]
    base.append(("504-0020-LPU26", "RED FEDERAL DE CONCESIONES - ETAPA IV -", estado))
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", lambda: list(base))
    adj = dict(sin_red["adjudicaciones_boletin"])
    if resolucion:
        adj["504-0020-LPU26"] = resolucion
    monkeypatch.setattr(gestion, "_adjudicacion_publicada", lambda proc: adj.get(proc))


def test_un_proceso_nuevo_en_contratar_produce_aviso(sin_red, monkeypatch, capsys):
    """Una Etapa IV publicada, sin resolución: no suma (90,1% con su denominador)
    y hay que enterarse."""
    _con_etapa_iv(monkeypatch, sin_red, "Publicado", None)
    card = gestion.fetch_concesiones_infraestructura()
    salida = capsys.readouterr().out
    assert "[AVISO]" in salida and "504-0020-LPU26" in salida and "IV" in salida
    assert "504-0020-LPU26" in card["advertencia_fuente"]
    assert card["valor"] == pytest.approx(90.1, abs=0.05)
    assert card["procesos"] == 5


def test_contratar_adjudicado_sin_resolucion_solo_avisa(sin_red, monkeypatch, capsys):
    """CONTRAT.AR dice Adjudicado pero no hay resolución en el Boletín: es un
    aviso, NO suma (el acto jurídico manda, ADR-0244)."""
    _con_etapa_iv(monkeypatch, sin_red, "Adjudicado", None)
    card = gestion.fetch_concesiones_infraestructura()
    assert "[AVISO]" in capsys.readouterr().out
    iv = [i for i in card["inventario_etapas"] if i["etapa"] == "IV"][0]
    assert not iv["adjudicado"]
    assert card["valor"] == pytest.approx(90.1, abs=0.05)


def test_una_etapa_nueva_con_resolucion_en_el_boletin_cuenta_y_avisa(sin_red, monkeypatch, capsys):
    """Control positivo, mismo denominador: con la resolución IV entra al
    numerador y el valor pasa de 90,1 a 100."""
    _con_etapa_iv(monkeypatch, sin_red, "Publicado",
                  {"norma": "Resolución 9 / 2027", "fecha_pub": "2027-01-10"})
    card = gestion.fetch_concesiones_infraestructura()
    assert "[AVISO]" in capsys.readouterr().out
    iv = [i for i in card["inventario_etapas"] if i["etapa"] == "IV"][0]
    assert iv["adjudicado"] and iv["fuente_estado"] == "Boletín Oficial"
    assert card["valor"] == 100.0
    assert card["km_adjudicados"] == 10091


# ── Parser de km: las etapas salen de la página, no de una lista fija ───────

def _pagina_rfc(etapas):
    filas = lambda km: ("<tr><td>Tramo</td><td>Total Km</td></tr>"
                        f"<tr><td>T</td><td>{km}</td></tr>")
    return "".join(f"<h3>Etapa {e}</h3><table>{filas(km)}</table>"
                   for e, km in etapas).encode()


def test_el_parser_de_km_toma_una_etapa_iv(monkeypatch):
    html = _pagina_rfc([("I", "100,5"), ("II-A", "200"), ("II-B", "300"),
                        ("III", "400"), ("IV", "500")])
    monkeypatch.setattr(gestion, "_http_get_resiliente", lambda url: html)
    km = gestion._rfc_km_por_etapa()
    assert km == {"I": 100.5, "II": 200.0, "II-B": 300.0, "III": 400.0, "IV": 500.0}


def test_el_parser_de_km_sin_encabezados_no_inventa_etapas(monkeypatch):
    html = b"<table><tr><td>T</td><td>100</td></tr></table>" * 4
    monkeypatch.setattr(gestion, "_http_get_resiliente", lambda url: html)
    with pytest.raises(ValueError):
        gestion._rfc_km_por_etapa()


# ── fecha_dato: no es "hoy" si no se consultó ninguna fuente de estado ──────

def test_contratar_caido_la_fecha_es_la_de_la_ultima_resolucion(sin_red, monkeypatch):
    import requests
    from datetime import date

    def _timeout():
        raise requests.exceptions.ConnectTimeout("t")
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", _timeout)
    card = gestion.fetch_concesiones_infraestructura()
    assert card["fecha_dato"] == "2026-08-24"          # Res. 1379/2026, la última
    assert card["fecha_dato"] != date.today().isoformat()
    antig = (date.today() - date(2026, 8, 24)).days
    assert card["desactualizado"] is (antig > 110)


def test_contratar_caido_y_store_viejo_queda_desactualizado(sin_red, monkeypatch):
    import requests

    def _timeout():
        raise requests.exceptions.ConnectTimeout("t")
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", _timeout)
    viejo = {e: {**d, "fecha_pub": "2025-01-01"} for e, d in gestion._etapas_adjudicadas_store().items()}
    monkeypatch.setattr(gestion, "_etapas_adjudicadas_store", lambda: viejo)
    card = gestion.fetch_concesiones_infraestructura()
    assert card["fecha_dato"] == "2025-01-01" and card["desactualizado"] is True


def test_contratar_respondio_la_fecha_es_la_del_chequeo(sin_red):
    from datetime import date
    card = gestion.fetch_concesiones_infraestructura()
    assert card["fecha_dato"] == date.today().isoformat()
    assert card["desactualizado"] is False


# ── La serie: CONTRAT.AR no escribe en el store (P1) ───────────────────────

@pytest.fixture
def serie_aislada(sin_red, monkeypatch, tmp_path):
    import descargar_series as ds
    store = json.loads(ds.CONCESIONES_FECHAS_STORE.read_text(encoding="utf-8-sig"))
    del store["etapas"]["III"]                  # que III sea la "nueva"
    ruta = tmp_path / "store.json"
    ruta.write_text(json.dumps(store), encoding="utf-8")
    monkeypatch.setattr(ds, "CONCESIONES_FECHAS_STORE", ruta)
    return ds, ruta


def test_la_serie_no_agrega_etapa_solo_porque_contratar_dice_adjudicado(serie_aislada, monkeypatch):
    ds, ruta = serie_aislada
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc",
                        lambda: [("504-0001-LPU26", "RED FEDERAL - ETAPA III -", "Adjudicado")])
    monkeypatch.setattr(gestion, "_adjudicacion_publicada", lambda p: None)
    ds.fetch_concesiones_serie()
    assert "III" not in json.loads(ruta.read_text(encoding="utf-8"))["etapas"]


def test_la_serie_agrega_etapa_con_resolucion_del_boletin(serie_aislada, monkeypatch):
    """Control positivo de lo anterior: misma entrada, pero con resolución."""
    ds, ruta = serie_aislada
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc",
                        lambda: [("504-0001-LPU26", "RED FEDERAL - ETAPA III -", "Disponible Para Adjudicar")])
    monkeypatch.setattr(gestion, "_adjudicacion_publicada",
                        lambda p: {"norma": "Resolución 1379 / 2026", "fecha_pub": "2026-08-24"})
    ds.fetch_concesiones_serie()
    e = json.loads(ruta.read_text(encoding="utf-8"))["etapas"]["III"]
    assert e["fecha"] == "2026-08" and e["fecha_pub"] == "2026-08-24"
    assert e["resolucion"] == "Resolución 1379 / 2026" and e["proceso"] == "504-0001-LPU26"


def test_etapa_del_store_no_consulta_infoleg(sin_red, monkeypatch):
    """Las cuatro etapas ya están en el store: InfoLeg no se toca."""
    def _no(proc):
        raise AssertionError("InfoLeg no debía consultarse")
    monkeypatch.setattr(gestion, "_adjudicacion_publicada", _no)
    assert gestion.fetch_concesiones_infraestructura()["valor"] == 100.0


def test_preadjudicado_sigue_sin_contar():
    """ADR-0087: `'ADJUDICADO' in 'PREADJUDICADO'` es True. La frontera de
    palabra es lo único que separa una preadjudicación de una adjudicación, y
    ahora hay una segunda fuente que podría tapar el error si se rompiera."""
    assert gestion._esta_adjudicado("Adjudicado")
    assert gestion._esta_adjudicado("Adjudicado Parcial")
    assert not gestion._esta_adjudicado("Preadjudicado")
    assert not gestion._esta_adjudicado("Disponible Para Adjudicar")


def test_la_fecha_de_infoleg_se_parsea():
    assert gestion._fecha_infoleg_rfc("24-ago-2026") == "2026-08-24"
    assert gestion._fecha_infoleg_rfc("5-jul-2026") == "2026-07-05"
    assert gestion._fecha_infoleg_rfc("sin fecha") is None
