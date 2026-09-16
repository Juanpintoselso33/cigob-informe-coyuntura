"""Un universo vacío observado no es cero por ciento ni un fallo de fuente."""
from datetime import date
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica
CLASIFICADOR_DIPUTADOS = politica._bloqueo_clasificar_diputados


@pytest.mark.parametrize('contenido', [b'PDF sin fecha interpretable', None])
def test_acta_ilegible_no_acredita_hueco_ni_cobertura(monkeypatch, contenido):
    monkeypatch.setattr(politica, '_diputados_acta_pdf', lambda *a: contenido)
    monkeypatch.setattr(politica, '_diputados_acta_fecha', lambda *a: None)
    monkeypatch.setattr(politica, '_hcdn_votaciones_session', lambda: None)
    monkeypatch.setattr(politica, '_diputados_acta_id_maximo', lambda *a: 1)
    cache = {}
    monkeypatch.setattr(politica, '_cargar_cache_cohesion_diputados', lambda: cache)
    assert politica._acta_diputados_cacheada(None, 1, cache) is politica._ACTA_FALLO
    assert not cache
    assert politica.fetch_cohesion_bloque()['recorrido_completo'] is False
    assert politica.fetch_cohesion_bloque_diputados_actas_anio(2026) is None


@pytest.fixture
def registro_vacio(monkeypatch):
    registro = {"vetos": [], "decretos": []}
    monkeypatch.setattr(politica, "_cargar_derrotas_registro", lambda: registro)
    monkeypatch.setattr(politica, "_guardar_derrotas_registro", lambda r: None)
    monkeypatch.setattr(politica, "_bloqueo_clasificar_diputados", lambda r: None)
    monkeypatch.setattr(politica, "_bloqueo_detectar_insistencias_senado", lambda r: None)
    return registro


def test_cero_desafios_no_es_cero_por_ciento(registro_vacio):
    tasa = politica.fetch_bloqueo_sostenido()
    conteo = politica.fetch_desafios_legislativos()
    assert tasa["valor"] is None
    assert tasa["estado"] == "sin_universo"
    assert tasa["desafiadas_12m"] == conteo["valor"] == 0
    assert not tasa["desactualizado"]


def test_fallo_de_consulta_no_declara_universo_vacio(monkeypatch, registro_vacio):
    def falla(_):
        raise ConnectionError("fuente no disponible")
    monkeypatch.setattr(politica, "_bloqueo_detectar_insistencias_senado", falla)
    assert politica.fetch_bloqueo_sostenido() is None


def test_clasificador_interrumpido_conserva_progreso_y_no_declara_vacio(monkeypatch, registro_vacio):
    # Ejecutar el clasificador real, no reemplazarlo por una excepción externa.
    monkeypatch.setattr(politica, '_bloqueo_clasificar_diputados', CLASIFICADOR_DIPUTADOS)
    monkeypatch.setattr(politica, '_hcdn_votaciones_session', lambda: None)
    monkeypatch.setattr(politica, '_cargar_cache_cohesion_diputados', lambda: {
        '1': {'fecha': '2026-08-01'}, '2': {'fecha': '2026-08-02'}})
    def clasificar(s, r, i):
        if i == 2:
            raise ConnectionError('PDF no disponible')
        return True, None
    monkeypatch.setattr(politica, '_bloqueo_clasificar_acta_diputados', clasificar)
    assert politica.fetch_bloqueo_sostenido() is None
    assert registro_vacio['actas_diputados_bloqueo']['clasificadas_hasta_id'] == 1


def test_pendiente_de_triage_no_acredita_universo_vacio(registro_vacio):
    registro_vacio['actas_diputados_bloqueo'] = {'pendientes': {'1': 'moción ambigua'}}
    assert politica.fetch_bloqueo_sostenido() is None


def test_sin_universo_elimina_puntaje_arrastrado(registro_vacio):
    tasa = politica.fetch_bloqueo_sostenido()
    tasa.update(puntaje_itcp=35, puntaje_banda=35, peso_efectivo=.0252)
    indicadores = {"bloqueo_sostenido": tasa}
    politica._anotar_indicadores_itcp(indicadores, None)
    assert tasa["en_indice"] is False
    assert "peso_efectivo" not in tasa
    assert not any(k.startswith("puntaje_") for k in tasa)


def test_corte_diario_no_incluye_votacion_futura_del_mismo_mes():
    eventos = [{"fecha_desafio": "2026-09-18", "fecha_caida": None}]
    assert politica._bloqueo_tasa_12m(eventos, date(2026, 9, 8)) is None
    assert politica._bloqueo_tasa_12m(eventos, date(2026, 9, 30))[1] == 1


@pytest.mark.parametrize("cambio", [None, {"valor": 0}, {"desafiadas_12m": 2},
                                  {"puntaje_itcp": 10}, {"en_indice": True},
                                  {"sostenidas_12m": 1}])
def test_gate_admite_solo_ausencia_explicita_y_coherente(tmp_path, registro_vacio, cambio):
    tasa = politica.fetch_bloqueo_sostenido()
    politica._anotar_indicadores_itcp({"bloqueo_sostenido": tasa}, None)
    tasa.update(cambio or {})
    snapshot = {"generated_at": date.today().isoformat(), "score_global": 5,
                "cinturones": {"politica": {"score": 5,
                "indicadores": {"bloqueo_sostenido": tasa}}}}
    (tmp_path / "informe.json").write_text(json.dumps(snapshot))
    (tmp_path / "series.json").write_text("{}")
    ruta = Path(politica.__file__).parent / "gate_calidad.py"
    r = subprocess.run([sys.executable, str(ruta), "--snapshot", str(tmp_path)],
                       capture_output=True, text=True)
    assert "Traceback" not in r.stderr, r.stderr
    if cambio:
        assert "G1 politica/bloqueo_sostenido: estado sin universo contradictorio" in r.stdout
        assert r.returncode != 0
    else:
        assert "[FALLA] G1" not in r.stdout, r.stdout


@pytest.mark.parametrize("registro_ok,diputados_ok,recorrido_completo", [
    (True, True, True), (False, True, True), (True, False, True), (True, True, False)])
def test_main_actualiza_el_par_solo_con_cobertura(monkeypatch, registro_vacio, registro_ok, diputados_ok, recorrido_completo):
    tasa_vacia = politica.fetch_bloqueo_sostenido()
    conteo_cero = politica.fetch_desafios_legislativos()
    for nombre in dir(politica):
        if nombre.startswith("fetch_"):
            monkeypatch.setattr(politica, nombre, lambda *a, **kw: None)
    for nombre in ("detectar_novedades_judiciales", "detectar_novedades_empresarias"):
        monkeypatch.setattr(politica, nombre, lambda: {})
    monkeypatch.setattr(politica, "fetch_derrotas_legislativas",
                        lambda: {"valor": 0} if registro_ok else None)
    monkeypatch.setattr(politica, "fetch_cohesion_bloque",
                        lambda: {"valor": None, "corrida_exitosa_en": date.today().isoformat(),
                                 "recorrido_completo": recorrido_completo}
                        if diputados_ok else None)
    llamadas = []
    def bloqueo():
        llamadas.append("bloqueo")
        return tasa_vacia.copy()
    def desafios():
        llamadas.append("desafios")
        return conteo_cero.copy()
    monkeypatch.setattr(politica, "fetch_bloqueo_sostenido", bloqueo)
    monkeypatch.setattr(politica, "fetch_desafios_legislativos", desafios)
    monkeypatch.setattr(politica, "load_cache", lambda: {"indicadores": {
        "bloqueo_sostenido": {"valor": 33.3, "obtenido_en": "2026-08-31"},
        "desafios_legislativos": {"valor": 3, "obtenido_en": "2026-08-31"}}})
    guardados = []
    monkeypatch.setattr(politica, "save_cache", guardados.append)
    with pytest.raises(SystemExit):
        politica.main()
    ind = guardados[0]["indicadores"]
    if registro_ok and diputados_ok and recorrido_completo:
        assert llamadas == ["bloqueo", "desafios"]
        assert ind["bloqueo_sostenido"]["valor"] is None
        assert ind["bloqueo_sostenido"]["en_indice"] is False
        assert ind["desafios_legislativos"]["valor"] == 0
    else:
        assert llamadas == []
        for clave, valor in (("bloqueo_sostenido", 33.3), ("desafios_legislativos", 3)):
            assert ind[clave]["valor"] == valor
            assert ind[clave]["desactualizado"] is True
            assert ind[clave]["obtenido_en"] == "2026-08-31"


def test_recorrido_con_pdf_fallido_no_acredita_cobertura(monkeypatch):
    monkeypatch.setattr(politica, '_hcdn_votaciones_session', lambda: None)
    monkeypatch.setattr(politica, '_diputados_acta_id_maximo', lambda s: 2)
    monkeypatch.setattr(politica, '_cargar_cache_cohesion_diputados', lambda: {})
    monkeypatch.setattr(politica, '_acta_diputados_cacheada',
                        lambda s, i, c: politica._ACTA_FALLO if i == 2 else None)
    assert politica.fetch_cohesion_bloque()['recorrido_completo'] is False


def test_publicacion_y_censo_con_componente_sin_universo(monkeypatch, tmp_path, registro_vacio):
    import publicar
    import auditoria_coherencia
    raiz = Path(politica.__file__).resolve().parents[1]
    snapshot = json.loads((raiz / "web/src/data/informe.json").read_text())
    bloque = snapshot["cinturones"]["politica"]
    indicadores = bloque["indicadores"]
    indicadores["bloqueo_sostenido"] = politica.fetch_bloqueo_sostenido()
    indicadores["desafios_legislativos"] = politica.fetch_desafios_legislativos()
    indice = politica.calcular_itcp_cinturon(indicadores)
    politica._anotar_indicadores_itcp(indicadores, indice)
    bloque["itcp"] = indice
    bloque["score"] = politica.itcp.tension_de_itcp(indice["valor"])
    publicar._scoring_indice(bloque, "itcp", politica.itcp, "Contexto", lambda *a: None)
    publicar._semaforos(snapshot)
    tasa = indicadores["bloqueo_sostenido"]
    assert tasa["aporte_score"] is None
    assert "denominador" in tasa["aporte_nota"]
    assert not tasa.get("semaforo")
    dimension = indice["dimensiones"]["poder_legislativo"]
    assert "bloqueo_sostenido" not in dimension["indicadores"]
    componentes = dimension["indicadores"].values()
    suma_nominal = sum(i["peso"] for i in componentes)
    for i in componentes:
        assert i["peso_efectivo"] == round(dimension["peso"] * i["peso"] / suma_nominal, 4)
    # El motor publica cada peso efectivo redondeado a cuatro decimales.
    assert sum(i["peso_efectivo"] for i in componentes) == pytest.approx(dimension["peso"], abs=.0003)
    destino = tmp_path / "web/src/data"
    destino.mkdir(parents=True)
    (destino / "informe.json").write_text(json.dumps(snapshot))
    monkeypatch.setattr(auditoria_coherencia, "RAIZ", tmp_path)
    resumen, _, _ = auditoria_coherencia.auditar()
    assert resumen["fallas_estructura_y_aritmetica"] == []
    # 63 → 64: vuelve apoyo_empresario (ADR-0310). 64 → 63: sale `icc_utdt`
    # del ITCIS, que pasa a ancla externa (ADR-0314). 63 → 64: `consumo_carnes_total`
    # se parte en `consumo_carne_vacuna` + `consumo_carnes_otras`, que puntúan
    # cada uno por su cuenta (ADR-0322) — una card más que antes.
    # 64 → 68: entra `actividad_tributaria` al ITCM (ADR-0329), y al ITCIS
    # entran `tasa_homicidios` + `tasa_robos` (ADR-0327) y `ratio_motos_autos`
    # (ADR-0328) a puntuar como indicadores propios — cuatro cards más.
    assert resumen["indicadores"] == 68
    assert resumen["indicadores_observados_en_calculo"] == 67   # 62 → 63 (ADR-0310) → 62 (ADR-0314) → 63 (ADR-0322) → 64 (ADR-0329) → 67 (ADR-0327/0328)
    assert resumen["indicadores_sin_universo"] == 1
