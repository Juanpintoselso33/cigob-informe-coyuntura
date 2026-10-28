# -*- coding: utf-8 -*-
"""Escalas del ITCM con cortes de la historia previa al mandato (ADR-0403, ADR-0404).

Cuatro indicadores dejaron cortes puestos sobre 2024-2026 (o en dólares
corrientes) y pasaron a desvíos de ene-2004 a nov-2023. Los desvíos se midieron
una vez y quedan declarados en `itcm.py` (DESVIO_*); acá se fija que los cortes
del motor salgan de ellos, que los centros conceptuales no se muevan y que el
saldo comercial se mida como % del comercio de punta a punta (tarjeta y serie).
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcm  # noqa: E402
import macro  # noqa: E402
import descargar_series  # noqa: E402
import procedencia_anclas  # noqa: E402

INF = float("inf")
P = itcm.ESCALA_ITCM.puntaje


def _cortes(ind):
    return sorted({round(x, 4) for lo, hi, _ in itcm.BANDAS_ITCM[ind]
                   for x in (lo, hi) if abs(x) != INF})


def test_resultado_primario_equilibrio_50_y_uno_y_dos_desvios():
    s = round(itcm.DESVIO_RESULTADO_PRIMARIO, 1)
    assert s == 11.9
    assert itcm.ANCLAS_ITCM["resultado_primario"] == (
        (-2 * s, 10.0), (-s, 30.0), (0.0, 50.0), (s, 80.0), (2 * s, 100.0))
    # el motor puntúa por las anclas, no por los puntos medios de los tramos
    assert P(0.0, "resultado_primario") == 50.0
    assert P(11.9, "resultado_primario") == 80.0
    assert P(-23.8, "resultado_primario") == 10.0
    assert P(40.0, "resultado_primario") == 100.0
    # los tramos publicados cortan EN las anclas
    assert _cortes("resultado_primario") == [-11.9, 0.0, 11.9, 23.8]


def test_iai_desvios_robustos_centrados_en_la_poblacion():
    s = round(itcm.DESVIO_ROBUSTO_IAI, 1)
    c = itcm.CRECIMIENTO_POBLACION_PCT
    assert s == 18.9
    assert _cortes("iai") == [round(c - 2 * s, 4), round(c - s, 4),
                              round(c + s, 4), round(c + 2 * s, 4)]
    assert P(c, "iai") == 60.0
    # el desvío robusto es más chico que el clásico (26,8): la cola de rebotes
    # no ensancha la escala
    assert s < 26.8


def test_credito_centro_en_cero_y_uno_y_dos_desvios():
    s = itcm.DESVIO_CREDITO_PRIVADO
    assert (round(s, 1), round(2 * s, 1)) == (14.5, 28.9)
    assert _cortes("credito_privado") == [-28.9, -14.5, 0.0, 14.5, 28.9]
    # el mandato está fuera del rango previo: sus extremos saturan, y eso es dato
    assert P(-38.4, "credito_privado") == 10.0
    assert P(117.8, "credito_privado") == 100.0


def test_saldo_comercial_en_desvios_del_porcentaje_del_comercio():
    s = itcm.DESVIO_SALDO_COMERCIAL
    esperado = [round(-2 * s, 1), round(-s, 1), round(s, 1), round(1.5 * s, 1), round(2 * s, 1)]
    assert _cortes("saldo_comercial_12m") == esperado == [-17.0, -8.5, 8.5, 12.7, 17.0]
    assert P(0.0, "saldo_comercial_12m") == 50.0          # equilibrio
    assert P(50.0, "saldo_comercial_12m") == 85.0         # techo institucional (ADR-0120)
    assert max(p for _, _, p in itcm.BANDAS_ITCM["saldo_comercial_12m"]) == 85
    # anclas que publica la ficha
    for v, p in ((-17, 10), (-12.75, 30), (10.6, 60), (14.85, 75), (17, 85)):
        assert P(v, "saldo_comercial_12m") == p


def test_umbral_de_la_regla_reexpresa_los_5000_millones():
    """5.000 M USD era el borde del superávit relevante; en % del comercio cae
    entre el 2,9 % (ago-2026) y el 3,6 % (dic-2023)."""
    u = itcm.SUPERAVIT_RELEVANTE_PCT_COMERCIO
    assert u == 3.0
    assert 5000 / 173447 * 100 <= u + 0.1 and u <= 5000 / 140502 * 100
    base = {"expo_var_ia": 0.0, "impo_var_ia": -20.0, "expo_delta_12m": 0,
            "impo_delta_12m": -8000}
    assert itcm.ajuste_automatico_saldo(dict(base, valor=u)) is None
    # por encima de 60 de banda (más de 10,6 %) la regla opina
    assert itcm.ajuste_automatico_saldo(dict(base, valor=16.0))["puntaje"] == 60.0


def test_puntajes_del_snapshot_del_28_oct():
    """Los números que declaran ADR-0403/0404 y las fichas."""
    assert P(6.02, "resultado_primario") == 65.2
    assert P(-1.74, "iai") == 58.3
    assert P(-1.2, "credito_privado") == 53.3
    assert P(round(26472 / (100845 + 74373) * 100, 2), "saldo_comercial_12m") == 76.2


def test_los_cuatro_quedan_como_historia_larga():
    for ind in ("resultado_primario", "iai", "credito_privado", "saldo_comercial_12m"):
        assert procedencia_anclas.PROCEDENCIA[ind][0] == "historia_larga", ind


def _ica_falso(n=30):
    puntos = []
    for k in range(n):                         # más reciente primero, como ica.completar
        mes = 2026 * 12 + 8 - k
        puntos.append((f"{mes // 12}-{mes % 12 + 1:02}-01", 9000.0 + 10 * k, 6000.0 + 25 * k))
    return {"puntos": puntos, "url": "https://www.indec.gob.ar/cuadro.xls",
            "advertencia": None, "consulta_oficial_exitosa": True}


def test_la_tarjeta_y_la_serie_del_saldo_dicen_el_mismo_porcentaje(monkeypatch):
    """G3 compara la tarjeta con el último punto de la serie: los dos tienen que
    ser el % del comercio de la misma ventana, y la serie en dólares aparte."""
    monkeypatch.setattr(macro, "_ica_mensual", lambda limit=60: _ica_falso())
    tarjeta = macro.fetch_saldo_comercial_12m()
    serie = descargar_series.fetch_saldo_12m_serie()
    usd = descargar_series.fetch_saldo_12m_usd_serie()
    ex = sum(9000.0 + 10 * k for k in range(12))
    im = sum(6000.0 + 25 * k for k in range(12))
    assert tarjeta["valor"] == round((ex - im) / (ex + im) * 100, 2) == serie[-1][1]
    assert serie[-1][0] == tarjeta["fecha_dato"] == usd[-1][0]
    assert tarjeta["saldo_musd"] == round(ex - im, 0)
    assert usd[-1][1] == pytest.approx(ex - im, abs=0.1)
    assert "%" in tarjeta["unidad"] and "US$" in tarjeta["detalle_txt"]
