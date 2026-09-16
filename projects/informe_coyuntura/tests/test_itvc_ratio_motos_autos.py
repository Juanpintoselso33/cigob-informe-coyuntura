"""ADR-0328, CORRECCIÓN post-merge: `ratio_motos_autos` nacía saturado en el
techo de tensión (10,58 recortado a 10,0) con sólo +38,8% de crecimiento
sobre su base 4T-2023 — la revisión adversarial probó 5 mutaciones contra la
suite y ninguna guarda cazó ni siquiera invertir la polaridad
(`invertido=True` → `False`). Este archivo prueba, contra la integración real
(`itvc.indices_desde_series`, no sólo funciones en aislamiento):

1. sin amortiguar, el dato real satura (control negativo: reproduce el
   defecto que motivó la corrección);
2. con el factor vigente, no satura;
3. la polaridad declarada (más motos por auto = deterioro) es la que
   efectivamente corre en `itvc.py`.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itvc  # noqa: E402
import parametrica  # noqa: E402

# Base 4T-2023 y último punto real (ago-2026) tomados de
# web/src/data/series.json al 16-sep-2026 — el mismo dato que produjo el
# índice 72,1 saturado que encontró la revisión.
SERIE = [
    {"fecha": "2023-10-01", "valor": 1.0562},
    {"fecha": "2023-11-01", "valor": 1.0636},
    {"fecha": "2023-12-01", "valor": 1.0750},
    {"fecha": "2026-08-01", "valor": 1.4777},
]


def test_control_negativo_sin_amortiguar_el_dato_real_satura():
    """Reproduce el defecto original: si el factor de amortiguación se pisa
    a 1,0 (equivalente a no amortiguar), el índice de hoy da 72,1 y la
    tensión publicada satura en 10,0. Si este test no reprodujera la
    saturación, el fixture no estaría probando lo que dice probar."""
    series = {"ratio_motos_autos": SERIE}
    idx_crudo = itvc.rebase_amortiguado(series, "ratio_motos_autos",
                                        invertido=True, factor=1.0)
    assert idx_crudo == pytest.approx(72.1, abs=0.05)
    tension_cruda = itvc.tension_de_itvc(idx_crudo)
    assert tension_cruda == 10.0, (
        f"el control negativo no reproduce la saturación (tensión "
        f"{tension_cruda}): revisar el fixture SERIE")
    assert parametrica.color_de_indice_base100(idx_crudo) == "rojo"


def test_con_el_factor_vigente_no_satura():
    series = {"ratio_motos_autos": SERIE}
    idx = itvc.rebase_amortiguado(
        series, "ratio_motos_autos", invertido=True,
        factor=itvc.FACTOR_AMORTIGUACION_RATIO_MOTOS_AUTOS)
    assert idx == pytest.approx(86.0, abs=0.05)
    tension = itvc.tension_de_itvc(idx)
    assert tension < 10.0, f"sigue naciendo saturado: tensión {tension}"
    assert tension > 0.0


def test_indices_desde_series_ratio_no_nace_saturado():
    """Integración real: `itvc.indices_desde_series` —el código que corre en
    producción, no la función en aislamiento— tiene que devolver un índice
    que no sature. Si alguien saca `rebase_amortiguado`/el factor de acá sin
    tocar este test, el test lo dice."""
    series = {"ratio_motos_autos": SERIE}
    idx = itvc.indices_desde_series({}, series)
    tension = itvc.tension_de_itvc(idx["ratio_motos_autos"])
    assert tension < 10.0, (
        f"ratio_motos_autos nace saturado en tensión {tension}: {idx}")


def test_indices_desde_series_usa_la_polaridad_declarada():
    """ADR-0328: más motos por auto es DETERIORO, así que un ratio que SUBE
    desde la base tiene que dar un índice por DEBAJO de 100. La revisión
    adversarial encontró que invertir esta polaridad en itvc.py no rompía
    ningún test — esto es lo que la haría romper."""
    series = {"ratio_motos_autos": SERIE}
    idx = itvc.indices_desde_series({}, series)
    assert idx["ratio_motos_autos"] < 100.0, (
        "el ratio subió sobre su base y el índice no bajó de 100: "
        "¿se invirtió la polaridad de ratio_motos_autos en itvc.py?")


def test_control_negativo_polaridad_opuesta_da_el_signo_contrario():
    """Con la misma serie pero `invertido=False`, el mismo crecimiento del
    ratio tiene que leerse como MEJORA (índice > 100) — confirma que el test
    de arriba depende de verdad de `invertido`, no de otra cosa."""
    series = {"ratio_motos_autos": SERIE}
    idx_opuesto = itvc.rebase_amortiguado(
        series, "ratio_motos_autos", invertido=False,
        factor=itvc.FACTOR_AMORTIGUACION_RATIO_MOTOS_AUTOS)
    assert idx_opuesto > 100.0
