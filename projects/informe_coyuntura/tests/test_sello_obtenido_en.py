# -*- coding: utf-8 -*-
"""El sello `obtenido_en` sólo lo pone un fetch exitoso (ADR-0191).

G2b es tan bueno como este sello. Si el sello se pusiera también en el
carry-forward, mediría la hora de la corrida en vez de la edad del dato y el
chequeo no serviría para nada — que es exactamente el agujero que G2 ya tenía
con `fecha_dato`.
"""
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import espiritu_epoca
import macro
import politica
import publicar


def test_sellar_marca_el_resultado_fresco():
    sellado = politica._sellar({"valor": 1.64, "fecha_dato": "2026-01-01"})
    assert "obtenido_en" in sellado
    # Parseable por el gate, que es el único consumidor.
    datetime.fromisoformat(sellado["obtenido_en"])
    assert sellado["valor"] == 1.64, "el sello no puede tocar el resto de la card"


def test_sellar_no_muta_el_original():
    """Los fetchers devuelven dicts que a veces vienen del cache en memoria."""
    original = {"valor": 1.64}
    politica._sellar(original)
    assert "obtenido_en" not in original


def test_todos_los_colectores_sellan_igual():
    """Cuatro copias del helper: si divergen, G2b miente en un cinturón."""
    for modulo in (macro, politica, espiritu_epoca):
        sellado = modulo._sellar({"valor": 1})
        assert "obtenido_en" in sellado, modulo.__name__
        datetime.fromisoformat(sellado["obtenido_en"])


def test_el_carry_forward_de_vida_arrastra_el_sello_viejo():
    """El caso que importa: la fuente no contestó, el sello NO se renueva."""
    enriquecido = {"inseguridad": {"valor": None, "fecha_dato": None}}
    previo = {"inseguridad": {"valor": 42.0, "fecha_dato": "2026-05-01",
                              "fuente": "SNIC", "obtenido_en": "2026-06-01T03:00:00"}}
    salida = publicar._carry_forward(enriquecido, previo)
    assert salida["inseguridad"]["valor"] == 42.0
    assert salida["inseguridad"]["obtenido_en"] == "2026-06-01T03:00:00", (
        "el carry-forward renovó el sello: G2b nunca podría detectar una fuente caída")


def test_vida_se_sella_con_la_hora_del_crudo_y_no_con_la_de_la_corrida():
    """Si el colector de vida no corrió hoy, la card se rearma del crudo viejo.

    Sellarla con `datetime.now()` diría que es fresca cuando no lo es — el
    mismo error, una capa más abajo.
    """
    raw = {"trends": {"sentimiento_digital": {"interes_relativo": {"inflacion": 26.1}}},
           "metadata": {"timestamp": "2026-07-09T00:00:00"}}
    enriquecido = publicar._sellar_vida(publicar.build_vida(raw), raw)
    sd = enriquecido["sentimiento_digital"]
    assert sd["valor"] is not None
    assert sd["obtenido_en"] == "2026-07-09T00:00:00"


def test_vida_no_sella_lo_que_vino_sin_valor():
    """Sin valor no hubo fetch exitoso: sellarlo sería declarar frescura falsa."""
    raw = {"trends": {"sentimiento_digital": {"interes_relativo": None}},
           "metadata": {"timestamp": "2026-07-09T00:00:00"}}
    enriquecido = publicar._sellar_vida(publicar.build_vida(raw), raw)
    assert enriquecido["sentimiento_digital"]["valor"] is None
    assert "obtenido_en" not in enriquecido["sentimiento_digital"]
