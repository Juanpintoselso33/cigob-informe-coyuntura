"""movilizacion_cepa mide el promedio mensual de casos del último tramo (ADR-0433).

Fragmento REAL del informe 893 de centrocepa.com.ar (12-nov-2026), que dejó de
traer el acumulado del año que medía el indicador.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import politica  # noqa: E402

FRAGMENTO_893 = (
    '<meta property="datePublished" content="2026-11-12T10:00:00-03:00">'
    "<p>Entre enero de 2024 y noviembre de 2026 se registraron al menos 953 casos de "
    "conflictividad laboral en todo el país.</p><p>Desde octubre de 2025, la conflictividad "
    "laboral se intensificó. Entre enero de 2024 y octubre de 2025 hubo en promedio 25 casos "
    "por mes. Entre noviembre de 2025 y octubre de 2026, el promedio subió a 33 casos "
    "mensuales. Ese agravamiento denota que el aumento no es de un primer momento.</p>"
)


def test_toma_el_tramo_mas_reciente_y_no_el_primero():
    r = politica._promedio_mensual_cepa(FRAGMENTO_893)
    assert r["cifra_cruda"] == 33.0
    assert (r["periodo_desde"], r["periodo_hasta"]) == ("2025-11", "2026-10")
    assert r["valor"] == round(33.0 / politica.CEPA_MAX_CASOS_MES * 100.0, 1)


def test_el_acumulado_sin_tramo_no_es_promedio():
    """«953 casos» desde enero de 2024 es un acumulado: no se toma."""
    solo_acumulado = ("Entre enero de 2024 y noviembre de 2026 se registraron al menos "
                      "953 casos de conflictividad laboral en todo el país.")
    assert politica._promedio_mensual_cepa(solo_acumulado) is None


def test_un_informe_sin_promedio_por_tramo_queda_afuera():
    assert politica._promedio_mensual_cepa(
        "Desde inicios del 2026 se registraron, al menos, 101 conflictos laborales.") is None
