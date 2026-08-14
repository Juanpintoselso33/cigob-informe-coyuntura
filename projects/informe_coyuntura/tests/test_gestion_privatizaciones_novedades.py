"""Tests del detector de novedades de privatizaciones (ADR-0129)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import gestion


@pytest.fixture(autouse=True)
def _novedades_escribe_en_tmp(tmp_path, monkeypatch):
    """El detector persiste su store en cada corrida —es parte de su trabajo—,
    así que un test que lo ejercita escribe en el árbol versionado y el guardián
    de conftest lo marca en teardown. Se redirige la constante a tmp_path con
    una copia de los datos reales: los tests siguen leyendo el store de verdad
    y la escritura cae afuera del repo. Mismo patrón que
    test_gestion_desregulacion.py."""
    origen = gestion.PRIVATIZACIONES_NOVEDADES_PATH
    if origen.exists():
        destino = tmp_path / origen.name
        destino.write_bytes(origen.read_bytes())
        monkeypatch.setattr(gestion, "PRIVATIZACIONES_NOVEDADES_PATH", destino)


def test_las_nueve_empresas_tienen_termino_de_busqueda():
    """Si se agrega una empresa al registro y no se le pone término, el
    detector la ignora en silencio y nadie se entera."""
    registro = json.loads(
        gestion.PRIVATIZACIONES_FECHAS_PATH.read_text(encoding="utf-8-sig"))["empresas"]
    faltan = set(registro) - set(gestion.PRIVATIZACIONES_TERMINOS)
    assert not faltan, f"empresas del registro sin término de búsqueda: {sorted(faltan)}"


def test_el_filtro_de_proceso_acepta_los_verbos_reales():
    """Casos tomados de normas que sí movieron una etapa."""
    reales = [
        "declárase sujeta a privatización a la empresa",
        "apruébase el pliego de bases y condiciones",
        "llámase a licitación pública nacional e internacional",
        "adjudícase el paquete accionario",
        "transferencia accionaria del noventa por ciento",
        "venta de las acciones clase A",
    ]
    for texto in reales:
        assert gestion._PRIVAT_PROCESO.search(texto), texto


def test_el_filtro_rechaza_el_ruido_administrativo():
    """El motivo de existir del filtro: sin él la primera corrida devolvió 180
    novedades en tres meses, casi todas trámites de rutina."""
    ruido = [
        "desígnase transitoriamente en el cargo de director de AySA",
        "apruébase el cuadro tarifario de Agua y Saneamientos Argentinos",
        "otórgase licencia sin goce de haberes al agente",
        "prorrógase la vigencia del convenio colectivo de trabajo",
    ]
    for texto in ruido:
        assert not gestion._PRIVAT_PROCESO.search(texto), texto


def test_el_detector_no_asigna_etapas():
    """La decisión central de ADR-0129: el detector AVISA, no clasifica.
    ADR-0101 documenta un caso donde el analista se mantuvo por debajo de lo
    que la norma habilitaba; automatizar eso borraría un juicio publicado."""
    fuente = Path(gestion.__file__).read_text(encoding="utf-8")
    ini = fuente.index("def detectar_novedades_privatizaciones")
    cuerpo = fuente[ini:fuente.index("def fetch_privatizaciones")]
    for prohibido in ("PRIVATIZACIONES_PATH", '"etapa"', "etapa ="):
        assert prohibido not in cuerpo, (
            f"el detector toca {prohibido}: debería sólo avisar")


def test_el_store_se_versiona_en_el_cron():
    """Un caché que no se commitea se reconstruye entero cada noche y el
    'ya revisado' no sobrevive — el detector volvería a avisar lo mismo."""
    wf = (Path(__file__).parents[3] / ".github" / "workflows"
          / "data-pipeline.yml").read_text(encoding="utf-8")
    assert "privatizaciones_novedades.json" in wf


def test_la_card_publica_las_pendientes(tmp_path, monkeypatch):
    # El fetch ejecuta el detector y persiste el store. La prueba tiene que
    # observar ese comportamiento sin reescribir el registro versionado cuando
    # InfoLeg publica una novedad durante la suite.
    store = tmp_path / "privatizaciones_novedades.json"
    store.write_bytes(gestion.PRIVATIZACIONES_NOVEDADES_PATH.read_bytes())
    monkeypatch.setattr(gestion, "PRIVATIZACIONES_NOVEDADES_PATH", store)
    card = gestion.fetch_privatizaciones()
    if card is None:
        pytest.skip("colector sin datos")
    assert "novedades_pendientes" in card
    for nid, d in card["novedades_pendientes"].items():
        assert d.get("empresa") in gestion.PRIVATIZACIONES_TERMINOS, d
        assert d.get("url", "").startswith("https://servicios.infoleg.gob.ar"), d
        assert d.get("titulo") and "\n" not in d["titulo"], d
