"""Tests del detector de novedades de privatizaciones (ADR-0129)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import gestion


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
    # La forma de publicación no necesita consultar la red ni descubrir normas.
    monkeypatch.setattr(gestion, "_infoleg_buscar_mes", lambda *a, **kw: [])
    card = gestion.fetch_privatizaciones()
    if card is None:
        pytest.skip("colector sin datos")
    assert "novedades_pendientes" in card
    for nid, d in card["novedades_pendientes"].items():
        assert d.get("empresa") in gestion.PRIVATIZACIONES_TERMINOS, d
        assert d.get("url", "").startswith("https://servicios.infoleg.gob.ar"), d
        assert d.get("titulo") and "\n" not in d["titulo"], d


def _detector_aislado(tmp_path, monkeypatch, texto, previo=None):
    ruta = tmp_path / 'novedades.json'
    ruta.write_text(json.dumps(previo or {}))
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_NOVEDADES_PATH', ruta)
    monkeypatch.setattr(gestion, '_infoleg_buscar_mes', lambda *a, **kw: [('123', 'Resolución')])
    monkeypatch.setattr(gestion, '_infoleg_texto', lambda nid: texto)
    return gestion.detectar_novedades_privatizaciones(meses_atras=1)


def test_busqueda_or_no_prueba_mencion_de_empresa(tmp_path, monkeypatch):
    # Caso real Dto. 590/2026: concurso offshore, devuelto al buscar YCRT.
    s = _detector_aislado(tmp_path, monkeypatch,
        'Convócase a concurso público internacional para explorar hidrocarburos CAN_200.')
    assert not s['pendientes']
    assert s['revisadas']['123']['del_proceso'] is False


def test_texto_vacio_se_reintenta_en_otra_corrida(tmp_path, monkeypatch):
    s = _detector_aislado(tmp_path, monkeypatch, '')
    assert '123' not in s['revisadas']
    monkeypatch.setattr(gestion, '_infoleg_texto', lambda nid:
        'Apruébase el pliego de AGUA Y SANEAMIENTOS ARGENTINOS S.A.')
    s = gestion.detectar_novedades_privatizaciones(meses_atras=1)
    assert s['pendientes']['123']['empresa'] == 'AySA'


def test_cache_anterior_se_revalida_y_atribuye_por_texto(tmp_path, monkeypatch):
    previo = {'revisadas': {'123': {'empresa': 'AySA', 'del_proceso': False}}}
    s = _detector_aislado(tmp_path, monkeypatch,
        'BELGRANO CARGAS Y LOGÍSTICA. Apruébanse los pliegos de licitación pública.', previo)
    assert s['pendientes']['123']['empresa'] == 'Belgrano Cargas'
    assert s['revisadas']['123']['version_filtro'] == 2
    monkeypatch.setattr(gestion, '_infoleg_texto', lambda nid: pytest.fail('ya clasificada'))
    gestion.detectar_novedades_privatizaciones(meses_atras=1)


def test_revalidacion_retira_pendiente_falso_sin_tocar_revision_manual(tmp_path, monkeypatch):
    previo = {'revisadas': {'123': {'empresa': 'YCRT', 'del_proceso': True}},
              'pendientes': {'123': {'empresa': 'YCRT'}}}
    s = _detector_aislado(tmp_path, monkeypatch, 'Concurso público offshore CAN_200.', previo)
    assert not s['pendientes']
    previo['revision_auditoria'] = {'123': {'resolucion': 'Revisión ya documentada'}}
    s = _detector_aislado(tmp_path, monkeypatch, 'AySA privatización', previo)
    assert s['revision_auditoria'] == previo['revision_auditoria']
    assert s['pendientes'] == previo['pendientes']


def test_menciones_normalizadas_y_varias_empresas():
    assert gestion._privat_empresas_en_texto('NUCLEOELECTRICA y Energía\nArgentina S.A.') == ['Enarsa', 'Nucleoeléctrica']
    assert gestion._privat_empresas_en_texto('intercargosa y energía de Argentina') == []


def test_cobertura_distingue_fallo_de_cero_y_preserva_revision(tmp_path, monkeypatch):
    ruta = tmp_path / 'novedades.json'
    ruta.write_text(json.dumps({'_meta': {'revision_manual_en': '2026-08-01'},
                                'pendientes': {'99': {'empresa': 'AySA'}}}))
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_NOVEDADES_PATH', ruta)
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_TERMINOS', {'AySA': 'Agua', 'Enarsa': 'Energía'})
    def buscar(termino, *a, **kw):
        if termino == 'Agua':
            raise RuntimeError('fuente caída')
        return []
    monkeypatch.setattr(gestion, '_infoleg_buscar_mes', buscar)
    s = gestion.detectar_novedades_privatizaciones(meses_atras=1)
    c = s['_meta']['cobertura']
    assert c['estado'] == 'incompleta'
    assert c['consultas_previstas'] == 2 and c['consultas_sin_error'] == 1
    assert len(c['consultas_fallidas']) == 1
    assert s['_meta']['revision_manual_en'] == '2026-08-01'
    assert '99' in s['pendientes']
    monkeypatch.setattr(gestion, '_infoleg_buscar_mes', lambda *a, **kw: [])
    c = gestion.detectar_novedades_privatizaciones(meses_atras=1)['_meta']['cobertura']
    assert c['estado'] == 'sin_fallos_detectados'
    assert c['consultas_fallidas'] == []


def test_texto_fallido_impide_declarar_busqueda_sin_fallos(tmp_path, monkeypatch):
    s = _detector_aislado(tmp_path, monkeypatch, '')
    assert s['_meta']['cobertura']['estado'] == 'incompleta'
    assert s['_meta']['cobertura']['textos_fallidos'] == ['123']


def test_card_conserva_pendientes_y_avisa_si_detector_falla(tmp_path, monkeypatch):
    ruta = tmp_path / 'novedades.json'
    pendiente = {'99': {'empresa': 'AySA', 'titulo': 'Pliego', 'url': 'https://example.test/norma'}}
    ruta.write_text(json.dumps({'pendientes': pendiente}))
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_NOVEDADES_PATH', ruta)
    def fallar():
        raise RuntimeError('detector caído')
    monkeypatch.setattr(gestion, 'detectar_novedades_privatizaciones', fallar)
    card = gestion.fetch_privatizaciones()
    assert card is not None and card['valor'] is not None
    assert card['novedades_pendientes'] == pendiente
    assert card['novedades_cobertura']['estado'] == 'incompleta'
    assert 'consulta de novedades incompleta' in card['detalle_txt']


def test_la_relectura_con_el_filtro_vigente_va_por_lotes_y_no_marca_sin_leer(tmp_path, monkeypatch):
    previo = {'revisadas': {n: {'empresa': 'AySA', 'del_proceso': False} for n in ('1', '2', '3')}}
    ruta = tmp_path / 'novedades.json'
    ruta.write_text(json.dumps(previo))
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_NOVEDADES_PATH', ruta)
    monkeypatch.setattr(gestion, 'PRIVATIZACIONES_LOTE_RELECTURA', 2)
    monkeypatch.setattr(gestion, '_infoleg_buscar_mes',
                        lambda *a, **kw: [('1', 'a'), ('2', 'b'), ('3', 'c'), ('4', 'nueva')])
    leidas = []
    monkeypatch.setattr(gestion, '_infoleg_texto', lambda nid: leidas.append(nid) or
                        'Apruébase el pliego de AGUA Y SANEAMIENTOS ARGENTINOS S.A.')
    s = gestion.detectar_novedades_privatizaciones(meses_atras=1)
    assert leidas == ['1', '2', '4']
    assert s['revisadas']['3'] == {'empresa': 'AySA', 'del_proceso': False}
    assert s['revisadas']['4']['version_filtro'] == 2
    assert s['_meta']['cobertura']['relectura_pendiente'] == ['3']
    leidas.clear()
    s = gestion.detectar_novedades_privatizaciones(meses_atras=1)
    assert leidas == ['3']
    assert s['revisadas']['3']['version_filtro'] == 2
    assert s['_meta']['cobertura']['relectura_pendiente'] == []
