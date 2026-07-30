# -*- coding: utf-8 -*-
"""Tests del ajuste estacional (ADR-0163)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import desestacionalizar as des  # noqa: E402

# patrón estacional realista: pico en invierno, valle en verano (hemisferio sur)
ESTACION = {1: -0.20, 2: -0.18, 3: -0.08, 4: 0.04, 5: 0.14, 6: 0.22,
            7: 0.24, 8: 0.18, 9: 0.08, 10: -0.02, 11: -0.10, 12: -0.16}


def _serie(anios=8, base=100.0, crecimiento=0.0, estacional=True, ruido=0.0):
    out, t = {}, 0
    for a in range(2018, 2018 + anios):
        for m in range(1, 13):
            e = ESTACION[m] if estacional else 0.0
            r = ((t * 7919) % 11 - 5) / 100.0 * ruido
            out["%04d-%02d" % (a, m)] = base * math.exp(crecimiento * t + e + r)
            t += 1
    return out


def test_detecta_la_estacionalidad_que_se_le_puso():
    amp = des.amplitud_estacional(_serie())
    esperado = 100 * (max(ESTACION.values()) - min(ESTACION.values()))
    assert abs(amp - esperado) < 3, (amp, esperado)


def test_el_ajuste_deja_la_serie_practicamente_plana():
    """Lo que el módulo promete: después del ajuste el almanaque casi no explica
    nada. Sin esta verificación, un ajuste que no funciona pasa inadvertido."""
    s = _serie()
    antes = des.amplitud_estacional(s)
    despues = des.amplitud_estacional(des.desestacionalizar(s))
    assert antes > 40
    assert despues < antes / 10, (antes, despues)


def test_sobre_una_serie_ya_ajustada_es_casi_la_identidad():
    """Por eso se aplica a TODAS y no sólo a las que parecen sucias: aplicarlo de
    más no rompe nada."""
    s = _serie(estacional=False, crecimiento=0.004)
    ajustada = des.desestacionalizar(s)
    assert all(abs(ajustada[m] / s[m] - 1) < 0.01 for m in s)


def test_no_mueve_el_nivel_de_la_serie():
    """Los efectos se centran: el ajuste redistribuye dentro del año, no corre
    la serie para arriba o para abajo."""
    s = _serie()
    ajustada = des.desestacionalizar(s)
    prom_a = sum(s.values()) / len(s)
    prom_d = sum(ajustada.values()) / len(ajustada)
    assert abs(prom_d / prom_a - 1) < 0.02


def test_conserva_la_tendencia():
    s = _serie(crecimiento=0.005)          # 0,5% mensual sobre 95 meses ≈ ×1,61
    ajustada = des.desestacionalizar(s)
    meses = sorted(s)
    assert ajustada[meses[-1]] > ajustada[meses[0]] * 1.5


def test_la_media_movil_no_cuenta_dos_veces_el_mismo_mes():
    """Una media simple de 13 meses incluye enero dos veces y sobreestima la
    amplitud (daba 47,4% donde el patrón real era 44,0%). La 2×12 la recupera."""
    amp = des.amplitud_estacional(_serie())
    esperado = 100 * (max(ESTACION.values()) - min(ESTACION.values()))
    assert abs(amp - esperado) < 1.0, (amp, esperado)


def test_historia_corta_devuelve_la_serie_sin_tocar():
    """Estimar 12 efectos mensuales con dos años daría factores de ruido; es
    preferible un contraste con estacionalidad declarada."""
    corta = {k: v for k, v in list(_serie().items())[:24]}
    assert des.desestacionalizar(corta) == corta
    assert des.amplitud_estacional(corta) is None


def test_no_rompe_con_ceros_ni_negativos():
    s = _serie()
    s["2019-05"] = 0.0
    s["2019-06"] = -1.0
    ajustada = des.desestacionalizar(s)
    assert len(ajustada) == len(s)
    assert ajustada["2019-05"] == 0.0


def test_es_determinista():
    s = _serie(ruido=1.0)
    assert des.desestacionalizar(s) == des.desestacionalizar(s)
