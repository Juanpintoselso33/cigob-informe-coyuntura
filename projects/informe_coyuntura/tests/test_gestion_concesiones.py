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


def test_un_proceso_nuevo_en_contratar_produce_aviso(sin_red, monkeypatch, capsys):
    """Una Etapa IV que aparece en el portal y no está en el store: no suma km
    (nadie la adjudicó), pero hay que enterarse."""
    base = [(p["proceso"], p["nombre"], p["estado_contratar"])
            for p in sin_red["procesos"]]
    base.append(("504-0020-LPU26", "RED FEDERAL DE CONCESIONES - ETAPA IV -", "Publicado"))
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", lambda: list(base))
    monkeypatch.setattr(gestion, "_adjudicacion_publicada",
                        lambda proc: sin_red["adjudicaciones_boletin"].get(proc))
    card = gestion.fetch_concesiones_infraestructura()
    salida = capsys.readouterr().out
    assert "[AVISO]" in salida and "504-0020-LPU26" in salida and "IV" in salida
    assert "504-0020-LPU26" in card["advertencia_fuente"]
    assert card["valor"] == 100.0               # no regala km
    assert card["procesos"] == 5


def test_una_etapa_nueva_adjudicada_en_el_portal_cuenta_y_avisa(sin_red, monkeypatch, capsys):
    """Mismo criterio de hoy para lo que el store no conoce: el portal que dice
    Adjudicado suma. Y pide cargarla en el store."""
    monkeypatch.setattr(gestion, "_rfc_km_por_etapa",
                        lambda: {**sin_red["km_por_etapa"], "IV": 1000.0})
    base = [(p["proceso"], p["nombre"], p["estado_contratar"]) for p in sin_red["procesos"]]
    base.append(("504-0020-LPU26", "RED FEDERAL DE CONCESIONES - ETAPA IV -", "Adjudicado"))
    monkeypatch.setattr(gestion, "_contratar_procesos_rfc", lambda: list(base))
    card = gestion.fetch_concesiones_infraestructura()
    assert "[AVISO]" in capsys.readouterr().out
    iv = [i for i in card["inventario_etapas"] if i["etapa"] == "IV"][0]
    assert iv["adjudicado"] and iv["fuente_estado"] == "CONTRAT.AR"


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
