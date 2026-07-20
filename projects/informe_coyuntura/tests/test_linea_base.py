# -*- coding: utf-8 -*-
"""La línea de base no puede publicarse sin su cobertura (ADR-0106)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import publicar
import validacion_externa as ve


def test_la_base_sale_de_la_misma_reconstruccion_que_valida_el_indice():
    """Base y serie publicada no pueden divergir: son el mismo cálculo.

    Si la línea de base se computara aparte, con el tiempo diría un número
    distinto del que el propio informe usa para validarse contra el riesgo
    país, y no habría forma de saber cuál de los dos está bien.
    """
    serie = ve.construir_serie_itcm()
    base = ve.linea_base_itcm(serie)
    assert base is not None
    assert base["periodo"] == ve.LINEA_BASE_YM
    assert base["valor"] == serie[ve.LINEA_BASE_YM]


def test_la_base_declara_sobre_que_porcion_del_indice_se_calculo():
    """El mes del traspaso es el peor cubierto de toda la serie.

    Varias series arrancan con el mandato, así que publicar el número sin decir
    sobre qué porción del índice se calculó lo haría parecer más firme de lo
    que es.
    """
    base = ve.linea_base_itcm(ve.construir_serie_itcm())
    assert 0 < base["cobertura"] <= 1
    assert isinstance(base["sin_dato"], list)
    # los componentes sin dato tienen que ser justamente los que faltan
    for ind in base["sin_dato"]:
        assert ind not in (ve._valores_itcm_por_mes()[ve.LINEA_BASE_YM] or {}) or \
               ve._valores_itcm_por_mes()[ve.LINEA_BASE_YM][ind] is None


def test_no_se_publica_con_cobertura_insuficiente(monkeypatch):
    """El guard que evita una distancia recorrida que parece medida y no lo está."""
    bloque = {"valor": 60.0}
    monkeypatch.setattr(publicar, "_cargar_validacion", lambda: {
        "linea_base_itcm": {"periodo": "2023-12", "valor": 26.3,
                            "cobertura": publicar.COBERTURA_MINIMA_BASE - 0.01,
                            "sin_dato": []}
    })
    publicar._linea_base(bloque)
    assert "linea_base" not in bloque, (
        "se publicó una base por debajo del piso de cobertura"
    )


def test_la_brecha_es_la_resta_y_el_texto_la_acompaña(monkeypatch):
    """El número del texto público y el del dato tienen que ser el mismo.

    Es el error que ya ocurrió en otras cards: la conclusión en prosa se
    escribe una vez y después el cálculo cambia sin que nadie reescriba el
    texto.
    """
    bloque = {"valor": 62.1}
    monkeypatch.setattr(publicar, "_cargar_validacion", lambda: {
        "linea_base_itcm": {"periodo": "2023-12", "valor": 26.3,
                            "cobertura": 0.83, "sin_dato": ["iai"]}
    })
    publicar._linea_base(bloque)
    lb = bloque["linea_base"]
    assert lb["brecha"] == round(62.1 - 26.3, 1)
    assert "35,8" in lb["conclusion"]
    assert "26,3" in lb["conclusion"] and "62,1" in lb["conclusion"]
    # y la salvedad de cobertura tiene que estar dicha, no sólo estar el número
    assert "83%" in lb["conclusion"]


def test_el_texto_publico_no_tiene_jerga_ni_numeros_de_adr(monkeypatch):
    """Regla G6: la card es texto público."""
    bloque = {"valor": 62.1}
    monkeypatch.setattr(publicar, "_cargar_validacion", lambda: {
        "linea_base_itcm": {"periodo": "2023-12", "valor": 26.3,
                            "cobertura": 0.83, "sin_dato": []}
    })
    publicar._linea_base(bloque)
    lb = bloque["linea_base"]
    for campo in ("titulo", "sub", "conclusion"):
        txt = lb[campo].lower()
        assert "adr" not in txt, f"{campo} menciona un ADR"
        assert "itcm" not in txt, f"{campo} usa la sigla interna"
