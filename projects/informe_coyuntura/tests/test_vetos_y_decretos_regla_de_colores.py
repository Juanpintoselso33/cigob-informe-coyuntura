"""ADR-0377: cero insistencias o derogaciones en 12 meses = verde, una o dos =
amarillo, tres = naranja, cuatro o más = rojo. Con la escala de ADR-0427 el 2
caía en naranja; se ancla en el borde del amarillo (revisión del 15-nov-2026)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itcp  # noqa: E402
import parametrica  # noqa: E402

REGLA = {0: "verde", 1: "amarillo", 2: "amarillo", 3: "naranja", 4: "rojo", 6: "rojo"}


def _color(p):
    t = (100 - p) / 10
    c1, c2, c3 = parametrica.TENSIONES_DE_CORTE
    return "verde" if t <= c1 else "amarillo" if t <= c2 else "naranja" if t <= c3 else "rojo"


@pytest.mark.parametrize("ind", ["insistencias_vetos", "rechazos_decretos"])
@pytest.mark.parametrize("n,color", sorted(REGLA.items()))
def test_cada_cantidad_da_el_color_de_la_regla(ind, n, color):
    p = parametrica.puntaje_de(float(n), ind, itcp.BANDAS_ITCP, itcp.ANCLAS_ITCP,
                               getattr(itcp, "TRANSFORMACIONES_ITCP", None))
    assert _color(p) == color, (ind, n, p)
