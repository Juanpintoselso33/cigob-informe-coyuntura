"""Regresiones offline del Monte Carlo paramétrico."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm
import sensibilidad


class _RuidoMaximo:
    def uniform(self, minimo, maximo):
        return maximo


def test_itcm_declara_anclas_explicitas_en_sensibilidad():
    assert sensibilidad.INDICES["itcm"]["anclas"] == itcm.ANCLAS_ITCM


def test_perturbacion_de_presion_repuntua_con_anclas_explicitas():
    dims = {
        "estabilidad_monetaria": {
            "peso": 1.0,
            "ind": {
                "presion_dolarizacion": {
                    "peso": 1.0,
                    "puntaje": 64.8,
                    "banda": 64.8,
                    "valor": 45.24,
                }
            },
        }
    }

    # ADR-0082: _perturbar recibe la ESCALA del índice —bandas, anclas y
    # transformaciones juntas— y no las tablas por separado.
    resultado = sensibilidad._perturbar(
        dims,
        _RuidoMaximo(),
        pesos=False,
        escala=itcm.ESCALA_ITCM,
    )

    # +5% del rango crudo 0-100: 45,24 → 50,24; anclas ITCM → 59,8.
    assert resultado == 59.8
