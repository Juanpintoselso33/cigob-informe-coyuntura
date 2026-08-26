# -*- coding: utf-8 -*-
"""Suspender un indicador libera su peso, y nadie lo reasigna a mano (ADR-0245).

La Entrega 2 de la remediación saca tres indicadores del score:
`apoyo_empresario` (ITCP), `reestructuracion_organismos` (ITCG) y
`sentimiento_digital` (ITVC); `judicializacion` (ITCP) se sumó después, con
ADR-0255. El riesgo de una suspensión no es el indicador que sale — es lo que
pasa con su peso.

Dos formas de hacerlo mal, las dos vistas en proyectos parecidos:

1. **Reasignar pesos a mano** para que el índice quede donde estaba. Eso ya no
   es una suspensión: es una recalibración disfrazada.
2. **Borrarlo de la tabla de pesos** y reescribir los de sus pares. Funciona,
   pero deja los pesos renormalizados escritos como si fueran de diseño, y
   reponer el indicador obliga a recalcular de memoria los originales.

Acá el indicador se saca del CÁLCULO y la tabla de diseño no se toca: los que
quedan en su dimensión absorben el hueco solos, que es lo mismo que el motor ya
hacía con un indicador sin dato.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import itcg
import itcp
import itvc
import parametrica
import publicar

# (módulo, indicador suspendido, dimensión, cómo se pasan los valores)
CASOS = [
    (itcp, "apoyo_empresario", "sector_privado"),
    (itcp, "judicializacion", "poder_judicial"),
    (itcg, "reestructuracion_organismos", "reforma_estado"),
    (itvc, "sentimiento_digital", "percepcion"),
]

MODULOS = {"itcp": itcp, "itcg": itcg, "itvc": itvc}
CALCULO = {"itcp": lambda v: itcp.calcular_itcp(v),
           "itcg": lambda v: itcg.calcular_itcg(v),
           "itvc": lambda v: itvc.calcular_itvc(v)}
DIMS = {"itcp": lambda: itcp.DIMENSIONES_ITCP,
        "itcg": lambda: itcg.DIMENSIONES_ITCG,
        "itvc": lambda: itvc.DIMENSIONES_ITVC}


def _sigla(mod):
    return {id(itcp): "itcp", id(itcg): "itcg", id(itvc): "itvc"}[id(mod)]


def _todos_los_valores(sigla, valor=60.0):
    return {i: valor for d in DIMS[sigla]().values() for i in d["indicadores"]}


def _resultado(sigla):
    return CALCULO[sigla](_todos_los_valores(sigla))


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_esta_declarado_como_suspendido_con_su_motivo(mod, indicador, dimension):
    """Un indicador que sale del score sin decir por qué es indistinguible de
    uno que se cayó."""
    meta = mod.INDICADORES_SUSPENDIDOS[indicador]
    assert meta["dimension"] == dimension
    assert meta["desde"] and meta["desde_txt"]
    assert len(meta["por_que"]) > 80, "el motivo tiene que explicar, no rotular"
    assert len(meta["condicion_reingreso"]) > 60, (
        "sin condición de reingreso, la suspensión es una baja encubierta")
    assert meta["adr"].isdigit() and len(meta["adr"]) == 4


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_no_puntua_ni_pesa(mod, indicador, dimension):
    sigla = _sigla(mod)
    r = _resultado(sigla)
    presentes = {i for d in r["dimensiones"].values() for i in d["indicadores"]}
    assert indicador not in presentes


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_el_peso_de_diseno_sigue_en_la_tabla(mod, indicador, dimension):
    """Lo que hace reversible la suspensión: el peso original no se perdió.

    Reponer el indicador es sacar una línea de `INDICADORES_SUSPENDIDOS`, no
    reconstruir de memoria los pesos que tenía la dimensión antes."""
    sigla = _sigla(mod)
    assert indicador in DIMS[sigla]()[dimension]["indicadores"]


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_los_pesos_de_la_dimension_suman_uno(mod, indicador, dimension):
    sigla = _sigla(mod)
    d = _resultado(sigla)["dimensiones"][dimension]
    interno = sum(i["peso_efectivo"] for i in d["indicadores"].values())
    assert abs(interno - d["peso_efectivo"]) < 1e-3


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_los_pesos_efectivos_del_cinturon_suman_uno(mod, indicador, dimension):
    sigla = _sigla(mod)
    r = _resultado(sigla)
    total = sum(i["peso_efectivo"] for d in r["dimensiones"].values()
                for i in d["indicadores"].values())
    assert abs(total - 1.0) < 1e-3


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_los_pares_absorben_el_hueco_en_proporcion(mod, indicador, dimension):
    """El reparto es proporcional, no discrecional: nadie eligió a quién darle
    el peso liberado."""
    sigla = _sigla(mod)
    tabla = DIMS[sigla]()[dimension]["indicadores"]
    vivos = {k: p for k, p in tabla.items() if k != indicador}
    resto = sum(vivos.values())
    d = _resultado(sigla)["dimensiones"][dimension]
    for k, info in d["indicadores"].items():
        esperado = vivos[k] / resto
        assert abs(info["peso_efectivo"] / d["peso_efectivo"] - esperado) < 1e-3


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_la_renormalizacion_no_toca_las_otras_dimensiones(mod, indicador, dimension):
    """El peso liberado se queda en su dimensión. Si se derramara, la
    suspensión estaría moviendo el reparto entre dimensiones, que es una
    decisión editorial distinta y no la que se tomó."""
    sigla = _sigla(mod)
    r = _resultado(sigla)
    for dkey, d in r["dimensiones"].items():
        esperado = DIMS[sigla]()[dkey]["peso"]
        assert abs(d["peso_efectivo"] - esperado) < 1e-3, (
            f"{dkey} pesa {d['peso_efectivo']} y su diseño dice {esperado}")


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_no_se_muestra_como_card(mod, indicador, dimension):
    """La regla del tablero, cerrada tres veces (ADR-0051/0153/0189): si no
    puntúa, no es card. Una card sin semáforo ni aporte se lee como componente
    igual, que es exactamente lo que ADR-0153 vino a evitar."""
    ocultos = {"itcp": publicar.POLITICA_OCULTOS,
               "itcg": publicar.GESTION_OCULTOS,
               "itvc": publicar.VIDA_OCULTOS}[_sigla(mod)]
    assert indicador in ocultos


@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_reponerlo_devuelve_el_reparto_original(mod, indicador, dimension):
    """La prueba de que no se reasignó nada: sacar la suspensión restituye los
    pesos de diseño, sin recalcular nada."""
    sigla = _sigla(mod)
    original = mod.INDICADORES_SUSPENDIDOS
    mod.INDICADORES_SUSPENDIDOS = {k: v for k, v in original.items() if k != indicador}
    try:
        d = _resultado(sigla)["dimensiones"][dimension]
        tabla = DIMS[sigla]()[dimension]["indicadores"]
        assert set(d["indicadores"]) == set(tabla)
        for k, info in d["indicadores"].items():
            assert abs(info["peso_efectivo"] / d["peso_efectivo"] - tabla[k]) < 1e-3
    finally:
        mod.INDICADORES_SUSPENDIDOS = original


def test_sin_suspendidos_no_toca_nada():
    """El helper es identidad cuando no hay nada suspendido: no puede alterar
    en silencio un índice que no tiene suspensiones."""
    v = {"a": 1.0, "b": 2.0}
    assert parametrica.sin_suspendidos(v, None) == v
    assert parametrica.sin_suspendidos(v, {}) == v
    assert parametrica.sin_suspendidos(v, {"b": {}}) == {"a": 1.0}


@pytest.mark.parametrize("sigla", ["itcp", "itcg", "itvc"])
def test_el_indice_es_el_promedio_ponderado_de_los_que_quedan(sigla):
    """El control de que no hay peso escondido en ningún lado.

    Se rehace el índice a mano desde el resultado —puntaje por peso efectivo,
    sumado— y tiene que dar lo mismo. Si la suspensión reasignara peso, lo
    duplicara o lo perdiera, esta identidad se rompe."""
    r = CALCULO[sigla](_todos_los_valores(sigla))
    a_mano = sum(i["puntaje_aplicado"] * i["peso_efectivo"]
                 for d in r["dimensiones"].values()
                 for i in d["indicadores"].values())
    assert abs(a_mano - r["valor"]) < 0.15


@pytest.mark.parametrize("sigla", ["itcp", "itcg", "itvc"])
def test_el_peso_liberado_se_queda_en_su_dimension(sigla):
    """Lo mismo, mirado por dimensión: el hueco no se derrama hacia afuera.

    Es la diferencia entre «los pares absorben el peso» y «el índice
    redistribuye»: lo segundo cambiaría el reparto editorial entre dimensiones
    sin que nadie lo haya decidido."""
    r = CALCULO[sigla](_todos_los_valores(sigla))
    for dkey, d in r["dimensiones"].items():
        interno = sum(i["puntaje_aplicado"] * i["peso_efectivo"]
                      for i in d["indicadores"].values())
        assert abs(interno / d["peso_efectivo"] - d["puntaje"]) < 0.15


# ── Y qué queda de él en el artefacto crudo (ADR-0259) ────────────────────────
# El peso liberado es sólo la mitad de la historia. La otra es qué dice de él
# `output/informe.json`, que hasta el 25-ago-2026 lo seguía declarando
# componente vigente. El contrato y sus guardas viven en
# `test_suspendido_es_archivo_no_componente.py`; acá se ancla el puente para
# que no queden como dos temas sin relación.

@pytest.mark.parametrize("mod,indicador,dimension", CASOS)
def test_el_artefacto_crudo_lo_archiva_en_vez_de_publicarlo(mod, indicador, dimension):
    sys.path.insert(0, str(RAIZ / "scripts"))
    import generar_informe as gi

    cinturon = {"itcp": "politica", "itcg": "gestion",
                "itvc": "vida_cotidiana"}[_sigla(mod)]
    assert indicador in gi.suspendidos_de(cinturon), (
        f"{indicador} está suspendido en {_sigla(mod)} pero "
        "generar_informe.py no lo ve: el contrato de archivo no se le aplica")
