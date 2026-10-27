"""ADR-0383: la dimensión Empleo se mide con la ocupación de la EPH.

Sin red: el cálculo interanual, la conversión a base 100, el reparto de pesos
y los suspendidos se prueban sobre datos armados a mano.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc  # noqa: E402

SUSPENDIDOS = {"empleo_registrado", "mortalidad_pymes", "subocupacion_demandante",
               "trabajo_independiente", "despacho_cemento"}


@pytest.fixture
def variacion(monkeypatch):
    """Carga el colector por ruta: su `config` es el del cinturón, no el de la
    raíz, así que se lo sustituye mientras dura la prueba."""
    import importlib.util
    raiz = ROOT / "scripts" / "vida_cotidiana"
    spec = importlib.util.spec_from_file_location("config_vida_ocupacion", raiz / "config.py")
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)
    monkeypatch.setitem(sys.modules, "config", conf)
    spec = importlib.util.spec_from_file_location(
        "indec_series_ocupacion", raiz / "collectors" / "indec_series.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.variacion_interanual_empleo


FILAS = [["2026-04-01", 0.45], ["2026-01-01", 0.448], ["2025-10-01", 0.45],
         ["2025-07-01", 0.454], ["2025-04-01", 0.44483062866737]]


def test_variacion_interanual_compara_el_mismo_trimestre(variacion):
    r = variacion(FILAS)
    assert r["fecha"] == "2026-04-01"
    assert r["valor"] == 0.5          # 45,0 − 44,5
    assert r["tasa"] == 45.0 and r["tasa_anio_previo"] == 44.5


def test_sin_el_trimestre_del_anio_previo_falla_en_voz_alta(variacion):
    # restar el trimestre anterior mediría estacionalidad y la publicaría
    with pytest.raises(ValueError):
        variacion(FILAS[:4])


def test_indice_base_100():
    assert itvc.indice_de_ocupacion(0) == 100.0
    assert itvc.indice_de_ocupacion(0.5) == pytest.approx(101.1, abs=0.05)
    assert itvc.indice_de_ocupacion(-0.5) < 100          # no invertido
    assert itvc.indice_ocupacion_eph({}) is None
    assert itvc.indice_ocupacion_eph({"ocupacion_eph": []}) is None


def test_la_dimension_empleo_pesa_60_40_y_suma_uno():
    dim = itvc.DIMENSIONES_ITVC["empleo"]
    assert dim["nombre"] == "Empleo"
    assert dim["peso"] == 0.2419                          # el nominal no se toca
    assert sum(dim["indicadores"].values()) == pytest.approx(1.0, abs=1e-4)
    vivos = {i: p for i, p in dim["indicadores"].items()
             if i not in itvc.INDICADORES_SUSPENDIDOS}
    assert set(vivos) == {"ocupacion_eph", "informalidad"}
    assert vivos["ocupacion_eph"] / sum(vivos.values()) == pytest.approx(0.60, abs=1e-3)
    assert vivos["informalidad"] == 0.3419                # su peso de siempre


def test_los_cinco_estan_suspendidos_con_adr():
    for k in SUSPENDIDOS:
        meta = itvc.INDICADORES_SUSPENDIDOS[k]
        assert meta["adr"] == "0383" and meta["dimension"] == "empleo"
        assert meta["por_que"] and meta["condicion_reingreso"]


def test_el_indice_solo_usa_ocupacion_e_informalidad():
    indices = {k: 50.0 for k in SUSPENDIDOS}              # si puntuaran, se notaría
    indices.update({"ocupacion_eph": 101.0, "informalidad": 94.0})
    r = itvc.calcular_itvc(indices)
    emp = r["dimensiones"]["empleo"]
    assert set(emp["indicadores"]) == {"ocupacion_eph", "informalidad"}
    assert emp["puntaje"] == pytest.approx(0.6 * 101.0 + 0.4 * 94.0, abs=0.1)


def test_rezago_de_la_ocupacion_igual_al_de_las_otras_eph():
    import config
    assert config.MAX_DIAS["ocupacion_eph"] == config.MAX_DIAS["informalidad"] == 280
