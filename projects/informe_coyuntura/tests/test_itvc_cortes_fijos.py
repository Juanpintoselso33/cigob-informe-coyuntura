"""ADR-0425: pobreza, mora y carga de la deuda puntúan contra cortes fijos."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itvc  # noqa: E402
import parametrica  # noqa: E402
import validacion_externa as ve  # noqa: E402


@pytest.mark.parametrize("indicador,valor,color", [
    ("pobreza_nowcast", 15.0, "verde"), ("pobreza_nowcast", 20.0, "verde"),
    ("pobreza_nowcast", 20.2, "amarillo"), ("pobreza_nowcast", 30.0, "amarillo"),
    ("pobreza_nowcast", 31.3, "naranja"), ("pobreza_nowcast", 40.0, "naranja"),
    ("pobreza_nowcast", 40.2, "rojo"),
    ("mora_familias", 3.0, "verde"), ("mora_familias", 6.5, "amarillo"),
    ("mora_familias", 10.0, "naranja"), ("mora_familias", 14.61, "rojo"),
    ("carga_servicio_deuda_hogares", 12.0, "verde"), ("carga_servicio_deuda_hogares", 18.0, "amarillo"),
    ("carga_servicio_deuda_hogares", 24.1, "naranja"), ("carga_servicio_deuda_hogares", 31.0, "rojo"),
])
def test_los_cortes_caen_en_los_bordes_de_color(indicador, valor, color):
    idx = itvc.indice_por_cortes(valor, itvc.CORTES_FIJOS_ITVC[indicador])
    assert parametrica.color_de_indice_base100(idx) == color


def test_la_escala_es_monotona_y_acotada():
    for cortes in itvc.CORTES_FIJOS_ITVC.values():
        vals = [itvc.indice_por_cortes(x / 10, cortes) for x in range(0, 800)]
        assert vals == sorted(vals, reverse=True)
        assert min(vals) >= 75.0 and max(vals) <= 125.0


def test_la_card_usa_el_ultimo_punto_crudo():
    series = {"mora_familias": [{"fecha": "2026-07-01", "valor": 3.0},
                                {"fecha": "2026-08-01", "valor": 14.61}],
              "carga_servicio_deuda_hogares": [{"fecha": "2026-04-01", "valor": 24.1}]}
    idx = itvc.indices_desde_series({}, series)
    assert idx["mora_familias"] == itvc.indice_por_cortes(14.61, (5.0, 8.0, 12.0))
    assert idx["carga_servicio_deuda_hogares"] == itvc.indice_por_cortes(24.1, (15.0, 20.0, 30.0))


def test_la_reconstruccion_usa_la_misma_funcion(monkeypatch):
    series = {"mora_familias": [{"fecha": "2026-08-01", "valor": 14.61}],
              "carga_servicio_deuda_hogares": [{"fecha": "2026-04-01", "valor": 24.1}]}
    monkeypatch.setattr(ve, "cargar_series", lambda: series)
    por_comp = ve._indices_itvc_por_componente()
    assert por_comp["mora_familias"]["2026-08"] == itvc.indice_por_cortes(14.61, (5.0, 8.0, 12.0))
    assert por_comp["carga_servicio_deuda_hogares"]["2026-04"] == itvc.indice_por_cortes(24.1, (15.0, 20.0, 30.0))


def test_la_card_publica_los_tramos_en_su_unidad():
    tramos = itvc.umbrales_cortes_fijos("pobreza_nowcast")
    assert [t["color"] for t in tramos] == ["verde", "amarillo", "naranja", "rojo"]
    assert tramos[0]["hasta"] == 20.0 and tramos[-1]["desde"] == 40.0
