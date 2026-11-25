"""ADR-0430: la card de alimentos muestra cuánto subió la comida por encima del
IPC general desde fines de 2023, la misma cuenta que pinta (itvc_alimentos)."""
import sys
from pathlib import Path

import pytest

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "vida_cotidiana"))
import publicar  # noqa: E402


@pytest.fixture
def indec_series(monkeypatch):
    """El colector importa el `config` de vida cotidiana, no el del proyecto:
    se carga como lo hace test_actividad_original."""
    raiz = ROOT / "scripts" / "vida_cotidiana"
    spec = importlib.util.spec_from_file_location("config_social_alimentos", raiz / "config.py")
    configuracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(configuracion)
    monkeypatch.setitem(sys.modules, "config", configuracion)
    spec = importlib.util.spec_from_file_location("indec_series_alimentos", raiz / "collectors/indec_series.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

BASE = {"2023-10": 100.0, "2023-11": 110.0, "2023-12": 120.0}


def test_cero_si_subieron_lo_mismo(indec_series):
    alim = dict(BASE, **{"2026-10": 300.0})
    gen = dict(BASE, **{"2026-10": 300.0})
    assert indec_series.alimentos_sobre_ipc(alim, gen)["2026-10"] == 0.0


def test_positivo_si_la_comida_subio_mas(indec_series):
    alim = dict(BASE, **{"2026-10": 330.0})
    gen = dict(BASE, **{"2026-10": 300.0})
    assert indec_series.alimentos_sobre_ipc(alim, gen)["2026-10"] == 10.0


def test_es_itvc_alimentos_al_reves(indec_series):
    alim = dict(BASE, **{"2026-10": 280.0})
    gen = dict(BASE, **{"2026-10": 300.0})
    pct = indec_series.alimentos_sobre_ipc(alim, gen)["2026-10"]
    itvc = (110.0 / 280.0) * (300.0 / 110.0) * 100     # fetch_itvc_alimentos
    assert pct == pytest.approx(100 * 100 / itvc - 100, abs=0.05)


def test_sin_base_completa_no_calcula(indec_series):
    with pytest.raises(ValueError):
        indec_series.alimentos_sobre_ipc({"2026-10": 1.0}, {"2026-10": 1.0})


def test_la_card_sale_del_porcentaje_sobre_el_ipc():
    raw = {"indec": {"ipc_alimentos": {"variacion_mensual_pct": 1.97, "fecha": "2026-10-01",
                                       "sobre_ipc_pct": -7.2, "fecha_sobre_ipc": "2026-10-01"}}}
    card = publicar.build_vida(raw)["ipc_alimentos"]
    assert card["valor"] == -7.2
    assert card["unidad"].startswith("% frente al IPC")
    assert "2,0 %" in card["detalle_txt"]


def test_no_se_arrastra_un_valor_de_otra_unidad():
    nuevo = {"ipc_alimentos": {"valor": None, "unidad": "% frente al IPC general desde fines de 2023"}}
    previo = {"ipc_alimentos": {"valor": 1.97, "unidad": "% mensual", "fecha_dato": "2026-10-01"}}
    assert publicar._carry_forward(nuevo, previo)["ipc_alimentos"]["valor"] is None
    previo["ipc_alimentos"]["unidad"] = nuevo["ipc_alimentos"]["unidad"]
    assert publicar._carry_forward(nuevo, previo)["ipc_alimentos"]["valor"] == 1.97


def test_una_fuente_caida_arrastra_su_valor_aunque_la_card_no_sepa_la_unidad():
    """25-nov-2026: el INDEC no contestó, la card de supermercados llegó con la unidad
    escrita en publicar.py («índice (desestacionalizado)») y no con la del colector
    («índice (2017 = 100, desestacionalizado)»); el arrastre la tomó por otra unidad,
    la card quedó sin valor y el gate frenó la corrida."""
    previo = {"consumo_supermercados": {"valor": 80.5, "fecha_dato": "2026-08-01",
                                        "unidad": "índice (2017 = 100, desestacionalizado)"},
              "motorizacion_total": {"valor": 31.2, "fecha_dato": "2026-10-01",
                                     "unidad": "vehículos 0km cada 1.000 habitantes"}}
    out = publicar._carry_forward(publicar.build_vida({}), previo)
    for clave in previo:
        assert out[clave]["valor"] == previo[clave]["valor"], clave
        assert out[clave]["unidad"] == previo[clave]["unidad"], clave
