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
    """Dos etapas por CONTRAT.AR y dos por el Boletín. Si el indicador no dijera
    cuál es cuál, la discrepancia entre las dos fuentes sería invisible."""
    card = gestion.fetch_concesiones_infraestructura()
    por_fuente = {}
    for i in card["inventario_etapas"]:
        por_fuente.setdefault(i["fuente_estado"], []).append(i["etapa"])
    assert sorted(por_fuente["CONTRAT.AR"]) == ["I", "II"]
    assert sorted(por_fuente["Boletín Oficial"]) == ["II-B", "III"]


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


def test_sin_resolucion_publicada_una_etapa_no_cuenta(sin_red, datos, monkeypatch):
    """La otra dirección: el Boletín SUMA etapas, no las regala.

    Si InfoLeg no encuentra la resolución, la etapa vuelve a valer lo que diga
    CONTRAT.AR — que para la III y la II-B es «Disponible Para Adjudicar»."""
    monkeypatch.setattr(gestion, "_adjudicacion_publicada", lambda proc: None)
    card = gestion.fetch_concesiones_infraestructura()
    assert card["km_adjudicados"] == datos["esperado"]["km_adjudicados_erroneo"]
    assert abs(card["valor"] - datos["esperado"]["valor_erroneo"]) < 0.2


def test_infoleg_caido_no_tumba_el_indicador(sin_red, datos, monkeypatch):
    """La RFC no puede depender de que InfoLeg conteste: si falla, el indicador
    informa lo que sabe —el estado del portal— en vez de no publicar nada."""
    def _explota(proc):
        raise RuntimeError("InfoLeg no responde")

    monkeypatch.setattr(gestion, "_adjudicacion_publicada", _explota)
    card = gestion.fetch_concesiones_infraestructura()
    assert card is not None
    assert card["km_adjudicados"] == datos["esperado"]["km_adjudicados_erroneo"]


def test_no_se_consulta_el_boletin_si_el_portal_ya_lo_declara(sin_red):
    """Cuatro procesos, dos consultas: si CONTRAT.AR ya dice Adjudicado no hay
    nada que dirimir, y cada consulta abre una sesión contra InfoLeg."""
    consultados = []

    import types
    original = gestion._adjudicacion_publicada

    def _espia(proc):
        consultados.append(proc)
        return original(proc)

    gestion._adjudicacion_publicada = _espia
    try:
        gestion.fetch_concesiones_infraestructura()
    finally:
        gestion._adjudicacion_publicada = original
    assert sorted(consultados) == ["504-0001-LPU26", "504-0015-LPU25"]


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
