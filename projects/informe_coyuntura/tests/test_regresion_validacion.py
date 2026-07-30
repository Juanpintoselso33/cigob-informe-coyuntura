# -*- coding: utf-8 -*-
"""Tests de la regresión de validación (ADR-0162), sin red.

Una regresión mal resuelta es peor que no tenerla: publica un número con aire de
autoridad. Por eso se verifica contra casos de respuesta CONOCIDA —ajuste
perfecto, predictor irrelevante, colinealidad— y no sólo contra que no explote.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import regresion_validacion as rv


def _serie(vals, desde=(2024, 1)):
    y, m = desde
    out = {}
    for v in vals:
        out[f"{y:04d}-{m:02d}"] = float(v)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def test_ajuste_perfecto_da_r2_uno():
    """y = 3 + 2x exactamente: R² debe ser 1 y el coeficiente 2."""
    x = [float(i) for i in range(20)]
    y = [3 + 2 * v for v in x]
    coef, r2 = rv.ols(y, [x])
    assert r2 == 1.0
    assert abs(coef[0] - 3) < 1e-9 and abs(coef[1] - 2) < 1e-9


def test_dos_predictores_se_resuelven_bien():
    """y = 1 + 2a + 3b, con a y b independientes."""
    a = [float(i) for i in range(24)]
    b = [float((i * 7) % 5) for i in range(24)]
    y = [1 + 2 * ai + 3 * bi for ai, bi in zip(a, b)]
    coef, r2 = rv.ols(y, [a, b])
    assert r2 == 1.0
    assert abs(coef[1] - 2) < 1e-9 and abs(coef[2] - 3) < 1e-9


def test_predictores_colineales_no_devuelven_numeros_inventados():
    a = [float(i) for i in range(20)]
    b = [2 * v for v in a]                    # exactamente colineal
    y = [float(i) for i in range(20)]
    coef, r2 = rv.ols(y, [a, b])
    assert coef is None and r2 is None


def test_un_indice_que_es_pura_tendencia_no_aporta_nada():
    """EL CASO QUE MOTIVA TODO: si el índice sólo repite la tendencia, el aporte
    sobre un modelo que YA tiene tendencia tiene que ser ~0."""
    tendencia = _serie([100 + i for i in range(30)])
    externa = _serie([50 + 0.5 * i for i in range(30)])
    r = rv.aporte_sobre_tendencia(tendencia, externa)
    assert r["suficiente"]
    assert abs(r["aporte"]) <= 0.02, r


def test_un_indice_con_señal_propia_si_aporta():
    """La externa tiene tendencia MÁS un ciclo que sólo el índice reproduce."""
    ciclo = [(-1) ** i * 5 for i in range(30)]
    indice = _serie([100 + c for c in ciclo])
    externa = _serie([50 + 0.5 * i + 2 * c for i, c in enumerate(ciclo)])
    r = rv.aporte_sobre_tendencia(indice, externa)
    assert r["aporte"] > 0.5, r
    assert r["signo"] == "positivo"


def test_serie_corta_no_devuelve_regresion():
    corta = _serie([1, 2, 3, 4, 5])
    r = rv.aporte_sobre_tendencia(corta, _serie([2, 4, 6, 8, 10]))
    assert r["suficiente"] is False
    assert rv.lectura(r) == ""


def test_el_texto_declara_cuando_el_indice_no_aporta():
    r = {"suficiente": True, "n": 30, "r2_tendencia": 0.8, "r2_con_indice": 0.805,
         "aporte": 0.005, "signo": "positivo", "coef": 0.01}
    txt = rv.lectura(r)
    assert "no agrega prácticamente nada" in txt
    assert "no porque confirme" in txt


def test_el_texto_marca_cuando_el_coeficiente_contradice_a_la_correlacion():
    """No es una expectativa a priori —la orientación del factor la fija su carga
    dominante— sino coherencia: si la correlación publicada es positiva y el
    coeficiente sale negativo, quitada la tendencia se mueven al revés."""
    r = {"suficiente": True, "n": 30, "r2_tendencia": 0.6, "r2_con_indice": 0.8,
         "aporte": 0.2, "signo": "negativo", "coef": -0.5}
    txt = rv.lectura(r, "positivo")
    assert "lado contrario" in txt
    assert "Se declara" in txt


def test_sin_signo_de_referencia_no_inventa_una_advertencia():
    r = {"suficiente": True, "n": 30, "r2_tendencia": 0.6, "r2_con_indice": 0.8,
         "aporte": 0.2, "signo": "negativo", "coef": -0.5}
    assert "lado contrario" not in rv.lectura(r)


def test_la_colinealidad_exacta_se_declara_como_tal():
    """Un índice que es una función lineal exacta del tiempo deja el sistema
    singular. Eso no es falta de datos —el caso tiene respuesta— y hay que poder
    distinguirlo de un aporte nulo estimado."""
    r = rv.aporte_sobre_tendencia(_serie([100 + i for i in range(30)]),
                                  _serie([50 + 0.5 * i for i in range(30)]))
    assert r["colineal"] is True
    assert "no es más que esa misma tendencia" in rv.lectura(r)


def test_un_aporte_real_no_se_marca_como_colineal():
    ciclo = [(-1) ** i * 5 for i in range(30)]
    r = rv.aporte_sobre_tendencia(_serie([100 + c for c in ciclo]),
                                  _serie([50 + 0.5 * i + 2 * c for i, c in enumerate(ciclo)]))
    assert r["colineal"] is False


def test_un_aporte_chico_no_se_redondea_a_cero_exacto():
    """Decir «0 puntos porcentuales» cuando son 0,4 es una afirmación más fuerte
    que la real."""
    r = {"suficiente": True, "n": 30, "r2_tendencia": 0.466, "r2_con_indice": 0.470,
         "aporte": 0.004, "signo": "positivo", "coef": 0.01}
    txt = rv.lectura(r)
    assert "0,4 puntos porcentuales" in txt, txt
