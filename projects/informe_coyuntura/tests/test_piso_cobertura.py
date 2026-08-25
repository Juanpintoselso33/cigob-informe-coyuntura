# -*- coding: utf-8 -*-
"""Ninguna serie reconstruida publica un mes armado sobre media docena de
componentes (ADR-0197).

El motor renormaliza pesos ante faltantes, que es lo correcto para el índice
del mes: si un indicador no llegó, el resto se reparte su peso. Pero aplicado a
la COLA de una serie histórica eso deja de ser renormalizar y pasa a ser otra
cosa — el índice de los pocos que llegaron, publicado con el nombre del índice
completo y metido en una correlación donde pesa igual que un mes completo.

Estos tests fijan las tres piezas: cómo se mide la cobertura, que el piso
recorte, y que el mes en curso no entre.
"""
import statistics
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import validacion_externa as ve  # noqa: E402
import itcg  # noqa: E402


def _r(dimensiones):
    """Forma mínima de lo que devuelve el motor: sólo lo que mira la cobertura."""
    return {"dimensiones": dimensiones}


def test_cobertura_cuenta_peso_de_indicador_y_no_dimensiones():
    """El caso que se escapaba: una dimensión con un solo indicador vivo de
    cinco aporta su peso entero al conteo dimensional. Medida por peso, la
    misma foto da 20%."""
    r = _r({"d1": {"peso": 1.0, "indicadores": {"a": {"peso": 0.2}}}})
    assert ve._cobertura_de_peso(r) == pytest.approx(0.2)


def test_cobertura_pondera_por_dimension():
    r = _r({
        "d1": {"peso": 0.7, "indicadores": {"a": {"peso": 0.5}, "b": {"peso": 0.5}}},
        "d2": {"peso": 0.3, "indicadores": {"c": {"peso": 0.4}}},
    })
    assert ve._cobertura_de_peso(r) == pytest.approx(0.7 * 1.0 + 0.3 * 0.4)


def test_el_piso_recorta_el_mes_flaco_y_deja_el_lleno():
    llamados = {"lleno": {"x": 1}, "flaco": {"x": 1}}

    def calcular(v):
        if v is llamados["lleno"]:
            return {"valor": 80.0, "dimensiones": {
                "d": {"peso": 1.0, "indicadores": {"a": {"peso": 0.9}}}}}
        return {"valor": 65.0, "dimensiones": {
            "d": {"peso": 1.0, "indicadores": {"a": {"peso": 0.3}}}}}

    serie = ve._serie_con_piso("TEST", {"2026-01": llamados["lleno"],
                                        "2026-02": llamados["flaco"]}, calcular)
    assert serie == {"2026-01": 80.0}


def test_el_mes_en_curso_no_entra_aunque_tenga_cobertura():
    """El tope es independiente del piso: un mes a mitad de camino puede tener
    mucha cobertura y aun así describir una muestra arbitraria del mes."""
    calcular = lambda v: {"valor": 70.0, "dimensiones": {
        "d": {"peso": 1.0, "indicadores": {"a": {"peso": 1.0}}}}}
    serie = ve._serie_con_piso("TEST", {"2026-06": {}, "2026-07": {}},
                               calcular, hasta="2026-06")
    assert list(serie) == ["2026-06"]


@pytest.mark.parametrize("constructor", ["itcm", "itcg", "itcp"])
def test_ninguna_serie_publicada_baja_del_piso(constructor):
    """El contrato de verdad: se reconstruye con datos reales y se verifica que
    todo mes que sobrevive llega al piso. Es lo que no existía cuando el ITCG
    publicaba jul-2026 con 44,8% y ago-2026 con 29,2%."""
    serie = getattr(ve, f"construir_serie_{constructor}")()
    assert serie, f"la serie {constructor} quedó vacía"
    valores = {"itcm": ve._valores_itcm_por_mes,
               "itcg": ve._valores_itcg_por_mes,
               "itcp": ve._valores_itcp_por_mes}[constructor]()
    calc = {"itcm": "calcular_itcm", "itcg": "calcular_itcg",
            "itcp": "calcular_itcp"}[constructor]
    mod = __import__(constructor)
    for ym in serie:
        r = getattr(mod, calc)(valores[ym])
        assert ve._cobertura_de_peso(r) >= ve.PISO_COBERTURA, (
            f"{constructor} publica {ym} con "
            f"{ve._cobertura_de_peso(r):.1%} del peso")


def test_itcg_no_publica_el_mes_en_curso():
    serie = ve.construir_serie_itcg()
    assert max(serie) <= ve._ultimo_mes_completo()


def test_la_ausencia_de_componentes_del_itcg_sesga_el_indice():
    """Por qué el piso y no una advertencia: el faltante NO es aleatorio.

    Un mes incompleto no queda ruidoso alrededor del valor real: queda **muy
    lejos**, y siempre para el mismo lado dentro de una misma composición del
    índice. Recalcular meses de cobertura plena con el subconjunto que llega
    temprano lo demuestra: la mediana del desvío son ~10 puntos y en 30 de 31
    meses supera los 3.

    Hasta agosto de 2026 este test afirmaba algo más fuerte —que el recorte
    siempre daba **por debajo**— y era cierto en los 31 meses. Dejó de serlo al
    suspender `reestructuracion_organismos` (ADR-0247): era el único componente
    de Reforma del Estado que llegaba temprano, y puntuaba bajo. Sin él, la
    dimensión entera desaparece del subconjunto rápido y lo que queda puntúa
    alto, así que desde may-2025 el recorte da por encima.

    El signo depende de qué componentes integran el índice y de cuáles se
    demoran; las dos cosas cambian. Lo que no cambia es que el desvío es grande
    y sistemático, y eso es lo que justifica un piso de cobertura en vez de una
    nota al pie.
    """
    vals = ve._valores_itcg_por_mes()
    presentes = {k for k, v in (vals.get("2026-08") or {}).items() if v is not None}
    if not presentes:
        pytest.skip("sin mes parcial contra el cual comparar")

    desvios = []
    for ym, v in sorted(vals.items()):
        if sum(1 for x in v.values() if x is not None) < 10:
            continue
        completo = itcg.calcular_itcg(v)
        recortado = itcg.calcular_itcg({k: x for k, x in v.items() if k in presentes})
        if completo and recortado:
            desvios.append(abs(recortado["valor"] - completo["valor"]))
    if len(desvios) < 10:
        pytest.skip("pocos meses de cobertura plena para medir el sesgo")

    grandes = sum(1 for d in desvios if d > 3.0)
    assert grandes >= 0.8 * len(desvios), (
        f"sólo {grandes} de {len(desvios)} meses se desvían más de 3 puntos al "
        "recortar: si el faltante fuera casi inocuo, el piso de cobertura no "
        "haría falta")
    assert statistics.median(desvios) > 5.0, (
        f"mediana del desvío {statistics.median(desvios):.1f}: el piso existe "
        "porque un mes incompleto está lejos del valor real, no al lado")
