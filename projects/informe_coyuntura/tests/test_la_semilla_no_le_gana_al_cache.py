# -*- coding: utf-8 -*-
"""La semilla escrita a mano no le gana al último valor bueno (ADR-0269).

El 29-ago-2026 `contratar.gob.ar` dio timeout y la card de concesiones publicó
**28,7%** —la foto del 2-jul, con dos etapas sin adjudicar— teniendo el **100%**
bueno en el cache de la noche anterior. `_manual_entry()` consultaba
`manuales.json` ANTES que el cache, así que ante un corte la card retrocedía a
un número tipeado a mano en julio.

Lo que hace de esto una clase de error y no una anécdota: de los seis
indicadores con semilla, dos están en OTRA MAGNITUD respecto de su último valor
en vivo (`desregulacion_normativa` 57 contra 16.771; `fal_modernizacion_laboral`
0,4 contra 50,0). Un corte los habría hecho saltar dos órdenes de magnitud con
el badge de "desactualizado" puesto, que es exactamente lo que ese badge NO
comunica.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import gestion


SEMILLA = {
    "concesiones_infraestructura": {
        "valor": 28.7,
        "unidad": "% de km adjudicados / km del plan",
        "fuente": "CONTRAT.AR (UOC 504) + página oficial RFC",
        "fecha_dato": "2026-07-02",
    }
}


def _cache(**campos):
    return {"indicadores": {"concesiones_infraestructura": campos}}


def test_el_ultimo_valor_en_vivo_le_gana_a_la_semilla():
    """El caso exacto del 29-ago-2026."""
    cache = _cache(valor=100.0, unidad="% de km adjudicados / km del plan",
                   fuente="CONTRAT.AR + Boletín Oficial", fecha_dato="2026-08-28",
                   obtenido_en="2026-08-28T05:42:54", desactualizado=False)

    salida = gestion._manual_entry("concesiones_infraestructura", SEMILLA, cache)

    assert salida["valor"] == 100.0, (
        "la semilla de julio le ganó al valor en vivo del cache: la card "
        "retrocede en vez de envejecer")
    assert salida["desactualizado"] is True, "sigue siendo un valor viejo, y se declara"


def test_la_semilla_se_usa_cuando_el_cache_nunca_tuvo_un_valor_en_vivo():
    """La razón por la que manuales.json existe: arrancar sin cache."""
    assert gestion._manual_entry("concesiones_infraestructura", SEMILLA, {})["valor"] == 28.7
    assert gestion._manual_entry("concesiones_infraestructura", SEMILLA,
                                 _cache(valor=None))["valor"] == 28.7


def test_un_valor_de_cache_sin_sello_no_le_gana_a_la_semilla():
    """Sin `obtenido_en` el valor del cache salió de la semilla misma (ADR-0191),
    así que no hay nada mejor que preferir — y preferirlo congelaría para siempre
    la primera semilla que se haya escrito."""
    cache = _cache(valor=28.7, fecha_dato="2026-07-02", desactualizado=True)
    assert gestion._manual_entry("concesiones_infraestructura",
                                 {"concesiones_infraestructura": {"valor": 55.0}},
                                 cache)["valor"] == 55.0


def test_ninguna_semilla_publicada_esta_en_otra_magnitud_que_su_ultimo_valor_en_vivo():
    """La guarda que le habría puesto nombre al problema el 29-ago.

    No exige que la semilla esté al día —envejecer es su naturaleza— sino que
    esté en la MISMA magnitud que lo que baja el colector. Una semilla en otra
    escala no es un dato viejo: es un dato equivocado esperando un corte de red.
    """
    manuales = json.loads((RAIZ / "data" / "gestion" / "manuales.json")
                          .read_text(encoding="utf-8-sig"))
    cache = json.loads((RAIZ / "output" / "cache" / "gestion.json")
                       .read_text(encoding="utf-8"))["indicadores"]

    problemas = []
    for nombre, m in manuales.items():
        if nombre.startswith("_"):
            continue
        semilla = m.get("valor", m.get("avance_pct"))
        vivo = cache.get(nombre, {})
        if semilla is None or not vivo.get("obtenido_en") or vivo.get("valor") is None:
            continue
        a, b = abs(float(semilla)), abs(float(vivo["valor"]))
        if max(a, b) > 10 * max(min(a, b), 1e-9):
            problemas.append(f"{nombre}: semilla {semilla} vs último valor en vivo "
                             f"{vivo['valor']} — no es un dato viejo, es otra magnitud")

    assert not problemas, "\n".join(problemas)
