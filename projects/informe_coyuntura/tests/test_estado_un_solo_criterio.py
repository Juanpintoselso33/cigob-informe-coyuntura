# -*- coding: utf-8 -*-
"""Un cinturón "tensionado" cuenta para la alerta. Siempre (ADR-0195).

Había tres criterios para lo mismo: `generar_informe._estado`, una réplica en
`publicar._estado`, y adentro de `detectar_barbarismo` un tercero
(`score >= EN_TENSION_MAX + 1`) para contar los cinturones de la alerta.

El `+1` sólo coincide con `> EN_TENSION_MAX` si los scores son enteros, y no lo
son. Entre 6 y 7 quedaba una zona muerta: el informe llamaba "tensionado" al
cinturón y la regla "dos o más señalan inestabilidad" no lo contaba. Le pasaba a
vida cotidiana en 6,9.

Estos tests fijan la propiedad, no los números: si mañana se mueven los
umbrales, siguen valiendo.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from config import UMBRALES, estado_de_score, es_tensionado  # noqa: E402
import generar_informe  # noqa: E402
import publicar  # noqa: E402


def test_no_hay_zona_muerta_entre_en_tension_y_la_alerta():
    """La propiedad: no existe score que sea "tensionado" y no cuente."""
    for centesimo in range(0, 1001):
        score = centesimo / 100
        if estado_de_score(score) == "tensionado":
            assert es_tensionado(score), (
                f"score {score} es tensionado pero no cuenta para la alerta")


def test_los_bordes_del_tramo():
    corte = UMBRALES["EN_TENSION_MAX"]
    assert estado_de_score(corte) == "en_tension"
    assert not es_tensionado(corte)
    # El primer valor por encima del corte YA cuenta. Con el criterio viejo
    # (`>= corte + 1`) esto era False hasta el 7,00.
    assert estado_de_score(corte + 0.01) == "tensionado"
    assert es_tensionado(corte + 0.01)


def test_el_caso_que_lo_destapo():
    """Vida cotidiana en 6,9: tensionada y, antes, invisible para la alerta."""
    assert estado_de_score(6.9) == "tensionado"
    assert es_tensionado(6.9)


def test_las_tres_definiciones_son_la_misma_funcion():
    """No réplicas que puedan desincronizarse: la misma función."""
    assert generar_informe._estado is estado_de_score
    assert publicar._estado is estado_de_score


@pytest.mark.parametrize("scores, esperada", [
    ({"a": 6.9, "b": 6.5}, True),    # dos en la ex zona muerta: antes daba False
    ({"a": 6.9, "b": 3.0}, False),
    ({"a": 7.5, "b": 8.1}, True),
    ({"a": 6.0, "b": 6.0}, False),   # el corte NO es tensionado
])
def test_la_alerta_cuenta_con_el_mismo_criterio(scores, esperada):
    datos = {k: {"score": v} for k, v in scores.items()}
    _, alerta = generar_informe.detectar_barbarismo(datos)
    assert alerta is esperada
