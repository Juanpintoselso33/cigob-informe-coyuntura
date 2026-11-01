"""Hallazgo Codex (vida cotidiana #1): sin la serie del IVI, `inseguridad` se
rellenaba dividiendo HECHOS delictivos del SNIC 2023 (2.435.858) por un
porcentaje de HOGARES víctimas: unidades incompatibles. Ahora el componente
queda sin dato y el motor renormaliza, como cualquier otro."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import itvc

BASELINES_VIEJOS = {"inseguridad": {"valor": 2435858}}
VIDA_IND = {"inseguridad": {"valor": 27.3}}


def test_sin_serie_ivi_el_componente_queda_sin_dato_aunque_haya_baseline():
    idx = itvc.indices_desde_series(VIDA_IND, {}, BASELINES_VIEJOS)
    assert idx["inseguridad"] is None


def test_con_serie_ivi_el_componente_sale_de_la_serie_rebaseada():
    serie = [{"fecha": f"2023-{m:02d}-01", "valor": 25.0} for m in (10, 11, 12)]
    serie.append({"fecha": "2026-08-01", "valor": 27.3})
    idx = itvc.indices_desde_series(VIDA_IND, {"inseguridad": serie}, BASELINES_VIEJOS)
    assert idx["inseguridad"] == round(25.0 / 27.3 * 100.0, 1)
