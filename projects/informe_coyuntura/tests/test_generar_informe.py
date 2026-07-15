"""generar_informe.py DEBE recalcular ITCM/ITCG/ITCP desde los valores crudos
persistidos con el código VIGENTE de itcm.py/itcg.py/itcp.py, no confiar en
el bloque ya calculado que el colector dejó en el caché (stale si el motor
de scoring cambió sin volver a correr el colector — ver el ADR que agrega
este fix)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generar_informe
import itcp


def _resultado_fake(valor):
    return {"valor": valor, "banda": "x", "banda_legible": "y",
            "dimensiones": {}, "ajustes_aplicados": []}


def _escribir_cache(tmp_path, cinturon, payload):
    (tmp_path / f"{cinturon}.json").write_text(json.dumps(payload), encoding="utf-8")


def _parchear_indice(monkeypatch, nombre, clave, calcular, tension_de):
    """_INDICES_PARAMETRICOS liga las funciones por REFERENCIA al importar
    generar_informe.py (a propósito: cada corrida del script es un proceso
    nuevo que reimporta itcm.py/itcg.py/itcp.py con el código vigente). Para
    testear hay que reemplazar la entrada del dict, no la función del módulo
    origen — parchear macro.calcular_itcm_cinturon después de que el dict ya
    capturó la referencia vieja no tiene efecto."""
    monkeypatch.setitem(generar_informe._INDICES_PARAMETRICOS, nombre, (clave, calcular, tension_de))


def test_recalcula_itcp_e_ignora_el_bloque_y_score_cacheados(tmp_path, monkeypatch):
    monkeypatch.setattr(generar_informe, "CACHE_DIR", tmp_path)
    _escribir_cache(tmp_path, "politica", {
        "cinturon": "politica",
        "score": 1.0,                                    # stale, no debe usarse
        "itcp": _resultado_fake(99.0),                    # stale, no debe usarse
        "indicadores": {"ratio_dnu": {"valor": 2.19}},
    })
    _parchear_indice(monkeypatch, "politica", "itcp", lambda ind: _resultado_fake(42.0), lambda v: 3.3)

    informe = generar_informe.construir_informe(generar_informe.load_caches())
    pol = informe["cinturones"]["politica"]

    assert pol["itcp"]["valor"] == 42.0
    assert pol["score"] == 3.3


def test_recalcula_itcm(tmp_path, monkeypatch):
    monkeypatch.setattr(generar_informe, "CACHE_DIR", tmp_path)
    _escribir_cache(tmp_path, "macro", {
        "cinturon": "macro",
        "score": 1.0,
        "itcm": _resultado_fake(99.0),
        "indicadores": {"saldo_comercial_12m": {"valor": 20000.0}},
    })
    _parchear_indice(monkeypatch, "macro", "itcm", lambda ind: _resultado_fake(55.0), lambda v: 4.5)

    informe = generar_informe.construir_informe(generar_informe.load_caches())
    mac = informe["cinturones"]["macro"]

    assert mac["itcm"]["valor"] == 55.0
    assert mac["score"] == 4.5


def test_recalcula_itcg(tmp_path, monkeypatch):
    monkeypatch.setattr(generar_informe, "CACHE_DIR", tmp_path)
    _escribir_cache(tmp_path, "gestion", {
        "cinturon": "gestion",
        "score": 1.0,
        "itcg": _resultado_fake(99.0),
        "indicadores": {"cepo_mulc": {"valor": 5.0}},
    })
    _parchear_indice(monkeypatch, "gestion", "itcg", lambda ind: _resultado_fake(60.0), lambda v: 4.0)

    informe = generar_informe.construir_informe(generar_informe.load_caches())
    ges = informe["cinturones"]["gestion"]

    assert ges["itcg"]["valor"] == 60.0
    assert ges["score"] == 4.0


def test_cinturon_sin_parametrica_usa_score_cacheado_sin_bloque_de_indice(tmp_path, monkeypatch):
    """vida_cotidiana / espiritu_epoca no tienen ITCM/ITCG/ITCP: el score
    cacheado se conserva tal cual y no se agrega ninguna clave de índice."""
    monkeypatch.setattr(generar_informe, "CACHE_DIR", tmp_path)
    _escribir_cache(tmp_path, "vida_cotidiana", {
        "cinturon": "vida_cotidiana",
        "score": 4.2,
        "indicadores": {"ipc_alimentos": {"valor": 2.0}},
    })

    informe = generar_informe.construir_informe(generar_informe.load_caches())
    vida = informe["cinturones"]["vida_cotidiana"]

    assert vida["score"] == 4.2
    assert "itcm" not in vida and "itcg" not in vida and "itcp" not in vida


def test_si_calcular_devuelve_none_conserva_score_cacheado(tmp_path, monkeypatch):
    """Sin ningún indicador utilizable (calcular_itc*_cinturon -> None), el
    score cae al cacheado (mismo criterio que usa el propio colector) y no
    se agrega bloque de índice — no se inventa un score de la nada."""
    monkeypatch.setattr(generar_informe, "CACHE_DIR", tmp_path)
    _escribir_cache(tmp_path, "politica", {
        "cinturon": "politica",
        "score": 5.0,
        "indicadores": {},
    })
    _parchear_indice(monkeypatch, "politica", "itcp", lambda ind: None, itcp.tension_de_itcp)

    informe = generar_informe.construir_informe(generar_informe.load_caches())
    pol = informe["cinturones"]["politica"]

    assert pol["score"] == 5.0
    assert "itcp" not in pol
