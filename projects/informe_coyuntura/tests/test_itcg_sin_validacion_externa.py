"""ADR-0336: el ITCG no tiene validación externa, por definición.

Mide lo que el gobierno hace; una estadística de afuera o es parte de la misma
agenda o mezcla la ejecución con todo lo demás. Estas pruebas fijan que no
vuelva a aparecer un número de «validación» para el ITCG en ninguna de las tres
capas donde vivía: el panel, el JSON intermedio y el snapshot publicado.
"""
import json
import sys
from pathlib import Path

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO / "scripts"))
import panel_validacion  # noqa: E402
import publicar  # noqa: E402

SNAPSHOT = json.loads((PROYECTO / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
VALIDACION = json.loads((PROYECTO / "output" / "validacion_externa.json").read_text(encoding="utf-8"))


def test_el_panel_no_arma_factor_para_el_itcg():
    assert "itcg" not in panel_validacion.FACTOR


def test_las_estadisticas_del_capital_privado_siguen_como_contraste_ajeno():
    for k in ("merval_usd", "inversion_directa_externa",
              "inversion_portafolio_externa", "financiamiento_externo_privado"):
        assert k in panel_validacion.FAMILIA


def test_la_seccion_declara_y_no_publica_numeros():
    bloque = {}
    publicar._validacion_itcg(bloque)
    val = bloque["validacion"]
    assert val["sin_contraste"] is True
    for clave in ("pares", "r_niveles", "r_diferencias", "panel"):
        assert clave not in val, clave
    assert val["titulo"] and "no tiene validación externa" in val["sub"]


def test_el_json_intermedio_no_trae_validacion_del_itcg():
    assert "correlaciones_itcg" not in VALIDACION
    assert "itcg" not in (VALIDACION.get("panel_validacion") or {})
    assert VALIDACION.get("serie_itcg"), "la serie reconstruida se sigue calculando"


def test_el_snapshot_publicado_no_valida_al_itcg():
    val = SNAPSHOT["cinturones"]["gestion"]["itcg"]["validacion"]
    assert val.get("sin_contraste") is True
    assert "pares" not in val and "r_niveles" not in val


def test_la_matriz_cruzada_es_de_tres_sin_el_itcg():
    cruz = SNAPSHOT["validacion_cruzada"]
    assert {f["indice"] for f in cruz["filas"]} == {"ITCM", "ITCIS", "ITCP"}
    externas = [k for k, _ in cruz["externas"]]
    assert "capital_privado" not in externas and len(externas) == 3
    for f in cruz["filas"]:
        assert "capital_privado" not in f
