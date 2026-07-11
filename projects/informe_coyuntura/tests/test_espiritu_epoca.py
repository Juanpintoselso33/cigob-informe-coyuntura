"""Tests de espiritu_epoca (indice_intencion_migratoria, ADR-0035/0049):
scoring con la intención migratoria como único puntuable (los otros 3 proxies
se siguen cacheando pero no puntúan, ADR-0049) y el gate de frescura mensual
del store compartido con descargar_series.py -- no debe llamar a pytrends si
el store ya tiene el mes calendario actual (el diseño explícitamente evita
pedir Trends para meses ya registrados, ver ADR-0035)."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import espiritu_epoca as ee


def _import_trends(monkeypatch):
    # Hay más de un módulo "config" en el repo (raíz del proyecto, scripts/,
    # scripts/vida_cotidiana/...) -- en producción nunca chocan porque cada
    # script corre en su propio proceso, pero dentro de una misma sesión de
    # pytest sys.modules["config"] cachea el PRIMERO que se importó (p.ej. el
    # de la raíz, vía test_publicar.py) y lo reusa para todos los imports
    # posteriores, incluido este. monkeypatch.delitem fuerza una recarga
    # limpia del "config" de vida_cotidiana y RESTAURA el original al
    # terminar el test, para no dejarle ese caché pisado a los tests que
    # corren después.
    root = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(root / "vida_cotidiana"))
    sys.path.insert(0, str(root / "vida_cotidiana" / "collectors"))
    monkeypatch.delitem(sys.modules, "config", raising=False)
    monkeypatch.delitem(sys.modules, "trends", raising=False)
    import trends
    return trends


# ── calcular_score(): único puntuable = intención migratoria (ADR-0049) ─────

def test_indicadores_esperados_sigue_relevando_los_4():
    # los 3 ocultos se siguen fetcheando/cacheando (seguimiento interno)
    assert ee.INDICADORES_ESPERADOS == [
        "icc_utdt", "sentimiento_digital", "clima_electoral", "indice_intencion_migratoria",
    ]


def test_score_es_solo_la_intencion_migratoria():
    indicadores = {
        "icc_utdt": {"valor": 45.0},
        "sentimiento_digital": {"valor": 80.0},
        "clima_electoral": {"valor": -10.0},
        "indice_intencion_migratoria": {"valor": 30.0},   # -> 3.0
    }
    assert ee.calcular_score(indicadores) == 3.0


def test_score_ignora_los_ocultos_aunque_esten_tensos():
    # con los 3 ocultos al máximo de tensión y migración en 0, el score es 0
    indicadores = {
        "icc_utdt": {"valor": 30.0},               # tensión 10 si puntuara
        "sentimiento_digital": {"valor": 100.0},   # tensión 10 si puntuara
        "clima_electoral": {"valor": -15.0},       # tensión 10 si puntuara
        "indice_intencion_migratoria": {"valor": 0.0},
    }
    assert ee.calcular_score(indicadores) == 0.0


def test_score_sin_intencion_migratoria_devuelve_default_5():
    # aunque los otros 3 estén presentes: no puntúan
    indicadores = {
        "icc_utdt": {"valor": 60.0},
        "sentimiento_digital": {"valor": 0.0},
        "clima_electoral": {"valor": 15.0},
    }
    assert ee.calcular_score(indicadores) == 5.0
    assert ee.calcular_score({}) == 5.0


def test_score_clampea_a_0_10():
    assert ee.calcular_score({"indice_intencion_migratoria": {"valor": 130.0}}) == 10.0


# ── Gate de frescura del store compartido (ADR-0035) ────────────────────────

def test_store_no_llama_a_trends_si_ya_tiene_el_mes_actual(tmp_path, monkeypatch):
    trends = _import_trends(monkeypatch)
    mes_actual = datetime.today().strftime("%Y-%m")
    store_path = tmp_path / "intencion_migratoria_serie.json"
    store_path.write_text(json.dumps({
        "_meta": {"actualizado": f"{mes_actual}-05"},
        "mensual": {"2024-01": 10.0},
        "contexto": {},
    }), encoding="utf-8")

    def _falla_si_se_llama(*a, **k):
        raise AssertionError("no debería intentar pytrends si el store ya está al día este mes")
    monkeypatch.setattr(trends, "_patch_urllib3", _falla_si_se_llama)

    resultado = trends.fetch_intencion_migratoria_store(store_path)
    assert resultado["mensual"] == {"2024-01": 10.0}


def test_store_intenta_refrescar_si_es_de_un_mes_anterior(tmp_path, monkeypatch):
    trends = _import_trends(monkeypatch)
    store_path = tmp_path / "intencion_migratoria_serie.json"
    store_path.write_text(json.dumps({
        "_meta": {"actualizado": "2020-01-01"},
        "mensual": {"2019-12": 5.0},
        "contexto": {},
    }), encoding="utf-8")

    llamado = {"si": False}

    def _marca_llamado():
        llamado["si"] = True
        raise RuntimeError("sin red en test")
    monkeypatch.setattr(trends, "_patch_urllib3", _marca_llamado)

    resultado = trends.fetch_intencion_migratoria_store(store_path)
    assert llamado["si"], "debería haber intentado refrescar (store de un mes anterior)"
    # el intento de fetch falló (RuntimeError) -> el store queda igual, nunca
    # se pisa con datos parciales
    assert resultado["mensual"] == {"2019-12": 5.0}


def test_store_default_cuando_no_existe(tmp_path, monkeypatch):
    trends = _import_trends(monkeypatch)
    store_path = tmp_path / "no_existe_todavia.json"
    monkeypatch.setattr(trends, "_patch_urllib3",
                         lambda: (_ for _ in ()).throw(RuntimeError("sin red en test")))
    resultado = trends.fetch_intencion_migratoria_store(store_path)
    assert resultado["mensual"] == {}
    assert resultado["contexto"] == {}
