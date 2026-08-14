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
    monkeypatch.setattr(politica, "_aea_comunicados", lambda s: [])
    return tmp_path


def test_no_reavisa_lo_ya_codificado(entorno, monkeypatch):
    """El caso central: los 103 comunicados que alguien ya clasificó no pueden
    volver a aparecer como pendientes."""
    monkeypatch.setattr(politica, "_uia_comunicados", lambda s, omitidos: [])
    store = politica.detectar_novedades_empresarias()
    assert store["pendientes"] == {}
    assert "UIA|4239" in store["revisadas"]


def test_avisa_lo_nuevo_una_sola_vez(entorno, monkeypatch):
    nuevo = {"camara": "UIA", "id": "comunicado-nuevo", "fecha": "2026-07-20",
             "titulo": "Comunicado nuevo", "url": "u"}
    monkeypatch.setattr(politica, "_uia_comunicados",
                        lambda s, omitidos: [] if "comunicado-nuevo" in omitidos else [dict(nuevo)])
    a = politica.detectar_novedades_empresarias()
    assert list(a["pendientes"]) == ["UIA|comunicado-nuevo"]
    assert a["_meta"]["nuevos_en_la_corrida"] == 1
    assert a["pendientes"]["UIA|comunicado-nuevo"]["postura"] is None, "no clasifica: eso es humano"
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
    monkeypatch.setattr(politica, "_uia_comunicados", lambda s, omitidos: [{
        "camara": "UIA", "id": "nueva", "fecha": "2026-07-20",
        "titulo": "x", "url": ""}])
    store = politica.detectar_novedades_empresarias()
    assert "UIA|nueva" in store["pendientes"]


def test_el_detector_avisa_pero_no_clasifica(entorno, monkeypatch):
    """El detector sigue siendo un AVISO: detecta y deja pendiente, la postura
    la asigna una persona. Lo que cambió con ADR-0150 es que el indicador que
    alimenta ya se publica (antes este test verificaba que NO estuviera en
    itcp.py); el reparto detección-automática / clasificación-humana no."""
    monkeypatch.setattr(politica, "_uia_comunicados", lambda s, omitidos: [])
    store = politica.detectar_novedades_empresarias()
    assert "valor" not in store and "serie" not in store
    itcp = (RAIZ / "scripts" / "itcp.py").read_text(encoding="utf-8")
    assert '"apoyo_empresario"' in itcp, "ADR-0150: ahora sí integra el índice"


def test_el_aviso_trae_el_texto_del_comunicado(monkeypatch):
    """La causa raíz de ADR-0150: sin cuerpo, quien codifica sólo tiene el
    título, y títulos como «Comunicado de la UIA» no dicen nada. El scraper
    viejo devolvía el menú de navegación del sitio."""
    html = ('<html><head><meta property="og:title" content="Comunicado de la UIA">'
            '<meta property="article:published_time" content="2026-03-11"></head>'
            '<nav>Institucional Novedades Documentos Contacto</nav>'
            r'55:T4ed,\u003cp data-block-key=\"a\"\u003eExpresamos nuestro profundo malestar.\u003c/p\u003e'
            r'\u003cp data-block-key=\"b\"\u003eMiles de empresas atraviesan un momento difícil.\u003c/p\u003e4b:['
            '</html>')

    class R:
        status_code, text = 200, html
    monkeypatch.setattr(politica, "HTTP_TIMEOUT", 1)
    c = politica._uia_comunicado(
        "https://www.uia.org.ar/uia/novedades/comunicado-de-la-uia",
        type("S", (), {"get": lambda *a, **k: R()})())
    assert "malestar" in c["texto"] and "momento difícil" in c["texto"]
    assert "Institucional Novedades" not in c["texto"], "volvió a leer el menú"


def test_el_listado_nuevo_no_vuelve_a_descargar_slugs_ya_vistos(monkeypatch):
    html = ('<a href="/uia/novedades/ya-vista">A</a>'
            '<a href="/uia/novedades/nueva/">B</a>')
    pedidos = []

    class R:
        status_code, text = 200, html
        def raise_for_status(self): pass

    class S:
        def get(self, url, **kwargs):
            pedidos.append(url)
            return R()

    monkeypatch.setattr(politica, "_uia_comunicado",
                        lambda url, session: {"id": url.rsplit("/", 1)[-1]})
    out = politica._uia_comunicados(S(), {"ya-vista"})
    assert [c["id"] for c in out] == ["nueva"]
    assert pedidos == [politica.UIA_NOVEDADES_URL]


def test_una_url_migrada_no_reavisa_un_comunicado_ya_codificado(entorno, monkeypatch):
    monkeypatch.setattr(politica, "_uia_comunicados", lambda s, omitidos: [{
        "camara": "UIA", "id": "la-uia-viajo-a-cordoba-2",
        "fecha": "2026-05-06", "titulo": "La UIA viajó a Córdoba", "url": "u"}])
    store = politica.detectar_novedades_empresarias()
    assert store["pendientes"] == {}
    assert "UIA|la-uia-viajo-a-cordoba-2" in store["revisadas"]


def test_el_store_esta_en_el_git_add_del_cron():
    """feedback_cache_persistence_cron: sin esto no sobrevive a la corrida
    nocturna y el detector no sirve para nada."""
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml"
          ).read_text(encoding="utf-8")
    assert "apoyo_empresario_novedades.json" in wf
