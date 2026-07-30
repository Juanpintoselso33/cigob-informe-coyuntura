# -*- coding: utf-8 -*-
"""Tests del factor común (primer componente principal, ADR-0161)."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import factor_comun as fc  # noqa: E402


def _meses(n, desde=1):
    return ["2024-%02d" % m if m <= 12 else "2025-%02d" % (m - 12)
            for m in range(desde, desde + n)]


def _serie(valores):
    return dict(zip(_meses(len(valores)), valores))


SUBE = [float(i) for i in range(24)]
BAJA = [float(-i) for i in range(24)]
RUIDO = [float((i * 7919) % 13) for i in range(24)]


def test_jacobi_reproduce_autovalores_conocidos():
    # matriz simétrica con autovalores exactos 3 y 1
    lams, vecs = fc._jacobi([[2.0, 1.0], [1.0, 2.0]])
    assert sorted(round(x, 9) for x in lams) == [1.0, 3.0]
    # los autovectores son ortonormales
    for v in vecs:
        assert math.isclose(sum(x * x for x in v), 1.0, abs_tol=1e-9)
    assert math.isclose(sum(a * b for a, b in zip(vecs[0], vecs[1])), 0.0, abs_tol=1e-9)


def test_series_opuestas_reciben_cargas_de_signo_opuesto():
    """Regresión del bug que tuvo la primera implementación.

    Con iteración de potencia arrancando en (1,1,…), un panel donde dos series
    van al revés devolvía TODAS las cargas positivas: el vector inicial ya era un
    autovector y la iteración no se movía de ahí. Sobre dos series pasaba
    siempre, y el factor resultante era la resta de dos cosas que se cancelan.
    """
    r = fc.primer_componente({"sube": _serie(SUBE), "sube2": _serie([v * 2 for v in SUBE]),
                              "baja": _serie(BAJA)})
    assert r is not None
    cargas = r["cargas"]
    assert cargas["sube"] * cargas["baja"] < 0, cargas
    assert cargas["sube"] * cargas["sube2"] > 0, cargas


def test_la_serie_de_ruido_pesa_menos_que_las_que_comparten_movimiento():
    r = fc.primer_componente({"a": _serie(SUBE), "b": _serie([v * 1.1 for v in SUBE]),
                              "ruido": _serie(RUIDO)})
    assert abs(r["cargas"]["ruido"]) < abs(r["cargas"]["a"])


def test_series_identicas_explican_toda_la_varianza():
    r = fc.primer_componente({"a": _serie(SUBE), "b": _serie(SUBE), "c": _serie(SUBE)})
    assert r["varianza_explicada"] == 100.0


def test_varianza_explicada_nunca_baja_del_promedio_trivial():
    """Un componente explica al menos 1/n: si diera menos, la extracción falló."""
    r = fc.primer_componente({"a": _serie(SUBE), "b": _serie(RUIDO),
                              "c": _serie(list(reversed(RUIDO)))})
    assert r["varianza_explicada"] >= 100.0 / 3


def test_la_orientacion_no_depende_del_orden_de_las_series():
    panel = {"a": _serie(SUBE), "b": _serie(BAJA), "c": _serie(RUIDO)}
    r1 = fc.primer_componente(panel)
    r2 = fc.primer_componente({k: panel[k] for k in ("c", "b", "a")})
    assert r1["cargas"] == r2["cargas"]
    assert r1["factor"] == r2["factor"]


def test_panel_corto_no_devuelve_factor():
    """Con dos series el factor es un promedio con el signo de una sola
    correlación: no se publica."""
    assert fc.primer_componente({"a": _serie(SUBE), "b": _serie(BAJA)}) is None


def test_pocos_meses_no_devuelven_factor():
    corta = {"a": dict(list(_serie(SUBE).items())[:6]),
             "b": dict(list(_serie(BAJA).items())[:6]),
             "c": dict(list(_serie(RUIDO).items())[:6])}
    assert fc.primer_componente(corta) is None


def test_serie_constante_no_rompe():
    plana = _serie([5.0] * 24)
    assert fc.primer_componente({"a": _serie(SUBE), "b": _serie(BAJA), "c": plana}) is None


def test_contraste_devuelve_correlacion_perfecta_si_el_indice_es_el_factor():
    panel = {"a": _serie(SUBE), "b": _serie([v * 1.3 for v in SUBE]),
             "c": _serie([v * 0.8 for v in SUBE])}
    r = fc.contraste(_serie(SUBE), panel)
    assert r["r"] == 1.0
    assert r["n_series"] == 3


def test_contraste_en_diferencias_usa_variaciones():
    """En diferencias, una serie que sólo sube en línea recta se vuelve constante
    y el panel deja de tener factor: es el filtro de tendencia común."""
    panel = {"a": _serie(SUBE), "b": _serie([v * 2 for v in SUBE]),
             "c": _serie([v * 3 for v in SUBE])}
    assert fc.contraste(_serie(SUBE), panel, en_diferencias=True) is None


def test_el_indice_no_participa_del_calculo_del_factor():
    """La propiedad que hace que esto no sea circular: cambiar el índice no
    cambia ni las cargas ni la varianza explicada."""
    panel = {"a": _serie(SUBE), "b": _serie(BAJA), "c": _serie(RUIDO)}
    uno = fc.contraste(_serie(RUIDO), panel)
    otro = fc.contraste(_serie(BAJA), panel)
    assert uno["cargas"] == otro["cargas"]
    assert uno["varianza_explicada"] == otro["varianza_explicada"]
    assert uno["r"] != otro["r"]


@pytest.mark.parametrize("panel", [{}, {"a": _serie(SUBE)}, {"a": {}, "b": {}, "c": {}}])
def test_paneles_vacios_o_incompletos(panel):
    assert fc.primer_componente(panel) is None
