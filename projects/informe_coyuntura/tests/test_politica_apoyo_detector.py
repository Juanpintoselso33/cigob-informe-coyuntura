"""Detector de postura empresaria (ADR-0149).

Lo que se protege: que AVISE de comunicados nuevos y que NO avise dos veces del
mismo. El registro de ADR-0148 se codificó a mano; sin este detector queda viejo
apenas una cámara publica algo, y el trabajo se pierde.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import politica  # noqa: E402


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Registro codificado con un caso por cámara y un store vacío."""
    cod = tmp_path / "codificacion.json"
    cod.write_text(json.dumps({"casos": [
        {"camara": "UIA", "id": "4239", "fecha": "2026-05-06",
         "titulo": "La UIA viajó a Córdoba"},
        {"camara": "AEA", "fecha": "2026-03-31", "titulo": "Nuevo presidente de AEA"},
    ]}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", cod)
    monkeypatch.setattr(politica, "APOYO_NOVEDADES_PATH", tmp_path / "novedades.json")
    monkeypatch.setattr(politica, "UIA_MARGEN_IDS", 3)
    monkeypatch.setattr(politica, "_aea_comunicados", lambda s: [])
    return tmp_path


def test_no_reavisa_lo_ya_codificado(entorno, monkeypatch):
    """El caso central: los 103 comunicados que alguien ya clasificó no pueden
    volver a aparecer como pendientes."""
    monkeypatch.setattr(politica, "_uia_comunicado", lambda i, s: {
        "camara": "UIA", "id": str(i), "fecha": "2026-05-06",
        "titulo": "La UIA viajó a Córdoba", "url": ""} if i == 4239 else None)
    store = politica.detectar_novedades_empresarias()
    assert store["pendientes"] == {}
    assert "UIA|4239" in store["revisadas"]


def test_avisa_lo_nuevo_una_sola_vez(entorno, monkeypatch):
    # el barrido arranca en el último id conocido + 1 (acá 4239 → 4240)
    nuevo = {"camara": "UIA", "id": "4240", "fecha": "2026-07-20",
             "titulo": "Comunicado nuevo", "url": "u"}
    monkeypatch.setattr(politica, "_uia_comunicado",
                        lambda i, s: dict(nuevo) if i == 4240 else None)
    a = politica.detectar_novedades_empresarias()
    assert list(a["pendientes"]) == ["UIA|4240"]
    assert a["_meta"]["nuevos_en_la_corrida"] == 1
    assert a["pendientes"]["UIA|4240"]["postura"] is None, "no clasifica: eso es humano"
    b = politica.detectar_novedades_empresarias()
    assert b["_meta"]["nuevos_en_la_corrida"] == 0, "avisó dos veces del mismo"


def test_la_clave_de_aea_distingue_dos_del_mismo_dia():
    """AEA no numera y publica más de un comunicado por día: con la fecha sola
    como clave, uno de los dos se re-avisaría para siempre."""
    a = politica._apoyo_clave_aea("2021-03-07", "Apoyo empresario tras el embate oficial")
    b = politica._apoyo_clave_aea("2021-03-07", "Jaime Campos: para que la economía crezca")
    assert a != b


def test_las_claves_cubren_el_registro_real():
    """Contra el registro de verdad: si la construcción de claves se desalinea,
    el detector re-avisa comunicados ya codificados."""
    casos = json.loads(politica.APOYO_CODIFICACION_PATH.read_text(
        encoding="utf-8-sig"))["casos"]
    assert len(politica._apoyo_ya_codificados()) == len(casos)


def test_una_camara_caida_no_tumba_la_otra(entorno, monkeypatch):
    def explota(s):
        raise RuntimeError("sitio caído")
    monkeypatch.setattr(politica, "_aea_comunicados", explota)
    monkeypatch.setattr(politica, "_uia_comunicado", lambda i, s: {
        "camara": "UIA", "id": str(i), "fecha": "2026-07-20",
        "titulo": "x", "url": ""} if i == 4241 else None)
    store = politica.detectar_novedades_empresarias()
    assert "UIA|4241" in store["pendientes"]


def test_no_alimenta_ningun_indice(entorno, monkeypatch):
    """Garantía de ADR-0149: es un aviso. El indicador no se publica hasta que
    haya segunda pasada con kappa ≥ 0,70."""
    monkeypatch.setattr(politica, "_uia_comunicado", lambda i, s: None)
    store = politica.detectar_novedades_empresarias()
    assert "valor" not in store and "serie" not in store
    assert "NO puntúa" in store["_meta"]["descripcion"]
    assert "apoyo_empresario" not in (RAIZ / "scripts" / "itcp.py").read_text(
        encoding="utf-8"), "el detector no puede entrar al ITCP"


def test_el_store_esta_en_el_git_add_del_cron():
    """feedback_cache_persistence_cron: sin esto no sobrevive a la corrida
    nocturna y el detector no sirve para nada."""
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml"
          ).read_text(encoding="utf-8")
    assert "apoyo_empresario_novedades.json" in wf
