import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta


@pytest.fixture(autouse=True)
def _cache_diputados_aislado(monkeypatch, tmp_path):
    # ningún test de este archivo debe leer/escribir la caché PERMANENTE
    # real (data/politica/cohesion_bloque_diputados_actas_cache.json) --
    # aislada acá una sola vez para que sea imposible olvidarlo en un test
    # nuevo (regresión real: la primera corrida de esta suite escribió en el
    # archivo real antes de que existiera este fixture).
    monkeypatch.setattr(politica, "DIPUTADOS_COHESION_CACHE_PATH", tmp_path / "cohesion_diputados_cache_test.json")


def test_indice_rice_unanime_afirmativo():
    assert politica.indice_rice(93, 0) == 100.0


def test_indice_rice_dividido_parejo():
    assert politica.indice_rice(50, 50) == 0.0


def test_indice_rice_mayoria_parcial():
    # 93 a favor, 1 en contra -> |93-1|/94*100 = 97.87
    assert politica.indice_rice(93, 1) == 97.87


def test_indice_rice_sin_votos():
    assert politica.indice_rice(0, 0) is None


def test_es_bloque_lla_variantes():
    assert politica.es_bloque_lla("LA LIBERTAD AVANZA")
    assert politica.es_bloque_lla("Libertad Avanza")
    assert politica.es_bloque_lla("  la libertad avanza  ")


def test_es_bloque_lla_excluye_aliados_y_otros():
    assert not politica.es_bloque_lla("Fuerzas del Cielo - Espacio Liberal F.C.E.")
    assert not politica.es_bloque_lla("PRO")
    assert not politica.es_bloque_lla("Unión por la Patria")
    assert not politica.es_bloque_lla("")


def test_hcdn_votaciones_get_reintenta_ante_403(monkeypatch):
    session = MagicMock()
    resp_403 = MagicMock(status_code=403)
    resp_200 = MagicMock(status_code=200)
    session.get.side_effect = [resp_403, resp_403, resp_200]
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert resultado is resp_200
    assert session.get.call_count == 3


def test_hcdn_votaciones_get_agota_reintentos(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=403)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert resultado is None
    assert session.get.call_count == 3


def test_hcdn_votaciones_get_devuelve_none_ante_excepcion(monkeypatch):
    session = MagicMock()
    session.get.side_effect = politica.requests.RequestException("timeout")
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    assert politica._hcdn_votaciones_get(session, "/votaciones/actas") is None


def test_hcdn_votaciones_session_setea_headers():
    session = politica._hcdn_votaciones_session()
    assert session.headers["User-Agent"] == politica.HTTP_HEADERS["User-Agent"]


# NOTA (verificación en vivo, Tarea 4): el estilo real del span de fecha en
# votaciones.hcdn.gob.ar es 'display: none' CON espacio (confirmado vía
# snapshot de Wayback Machine de ene-2026), no 'display:none' sin espacio como
# se asumió originalmente por analogía con Senado. El fixture usa la forma
# real confirmada. También se confirmó que en producción actual el 3er
# argumento de redirectActa (slug) viene siempre vacío (''); se deja no-vacío
# acá para seguir cubriendo la extracción genérica del grupo por regex.
FIXTURE_LISTADO_ACTAS = """
<table>
<tr>
  <td><span style="display: none">20260211</span> 11/02/2026</td>
  <td>Modernización Laboral. Título I.
    <a onclick="redirectActa(2623,1,'modernizacion-laboral-titulo-i')">Ver</a>
  </td>
</tr>
<tr>
  <td><span style="display: none">20260520</span> 20/05/2026</td>
  <td>Régimen de Zona Fría
    <a onclick="redirectActa(5939,1,'regimen-de-zona-fria')">Ver</a>
  </td>
</tr>
</table>
"""


def test_descubrir_actas_empareja_fecha_con_acta():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_ACTAS)
    actas = politica._descubrir_actas(session, 2026)
    assert actas == [
        {"id": "2623", "slug": "modernizacion-laboral-titulo-i", "fecha": datetime(2026, 2, 11)},
        {"id": "5939", "slug": "regimen-de-zona-fria", "fecha": datetime(2026, 5, 20)},
    ]


def test_descubrir_actas_ignora_filas_sin_fecha_o_sin_acta():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text="<table><tr><td>sin nada util</td></tr></table>")
    assert politica._descubrir_actas(session, 2026) == []


def test_descubrir_actas_deduplica_por_id():
    session = MagicMock()
    texto = FIXTURE_LISTADO_ACTAS.replace("5939", "2623")  # simula id repetido
    session.post.return_value = MagicMock(status_code=200, text=texto)
    actas = politica._descubrir_actas(session, 2026)
    assert len(actas) == 1


def test_descubrir_actas_request_fallido_devuelve_none():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=500, text="")
    assert politica._descubrir_actas(session, 2026) is None


def test_descubrir_actas_acepta_slug_vacio():
    # Caso real confirmado en vivo (Tarea 4): redirectActa(id, orden, '') con
    # slug vacío es el dato real en producción, no una fila a descartar.
    fixture = """
    <table><tr>
      <td><span style="display: none">20260211</span> 11/02/2026</td>
      <td><a onclick="redirectActa(2623,1,'')">Ver</a></td>
    </tr></table>
    """
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=fixture)
    actas = politica._descubrir_actas(session, 2026)
    assert actas == [{"id": "2623", "slug": "", "fecha": datetime(2026, 2, 11)}]


def test_descubrir_actas_excepcion_de_red_devuelve_none():
    session = MagicMock()
    session.post.side_effect = politica.requests.RequestException("timeout")
    assert politica._descubrir_actas(session, 2026) is None


def test_url_acta_con_slug():
    assert politica._url_acta({"id": "5939", "slug": "regimen-de-zona-fria"}) == "/votacion/regimen-de-zona-fria/5939"


def test_url_acta_sin_slug():
    # Caso real de producción (Tarea 4: slug vacío en 500/500 filas reales)
    assert politica._url_acta({"id": "5840", "slug": ""}) == "/votacion/5840"


# NOTA (verificación en vivo, Tarea 5): la estructura de 3 columnas asumida
# originalmente (`<td>nombre</td><td class="ocultar">bloque</td><td>voto</td>`)
# NUNCA fue observada en Diputados — era inferencia por analogía con Senado.
# Confirmado contra un snapshot real de Wayback Machine (2026-01-15, acta id
# 5840, votaciones.hcdn.gob.ar, tabla #myTable con 257 filas = las 257 bancas):
# cada fila real tiene 6 <td> (foto vacía, DIPUTADO, BLOQUE, PROVINCIA, voto
# anidado en <span class="label ..."> dentro de <center>, "¿QUÉ DIJO?"); CERO
# ocurrencias de class="ocultar" en la página real. El fixture reproduce esa
# estructura real (incluida la celda de foto vacía y el voto anidado en
# <span>), no la asumida originalmente. El bloque real se ve en Title Case
# ("La Libertad Avanza", no "LA LIBERTAD AVANZA") — se preserva así en el
# fixture porque es exactamente como llega de la fuente y es case-insensitive
# para es_bloque_lla.
FIXTURE_ACTA = """
<table id="myTable">
<thead>
<tr class="tr-oficial"><th></th><th>DIPUTADO</th><th>BLOQUE</th><th>PROVINCIA</th><th>¿CÓMO VOTÓ?</th><th>¿QUÉ DIJO?</th></tr>
</thead>
<tbody>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="juez, luis alfredo">JUEZ, LUIS ALFREDO</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-success col-sm-9 force-square">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="kueider, edgardo">KUEIDER, EDGARDO</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="entre rios">Entre Ríos</td>
  <td><center><span class="label label-danger col-sm-9 force-square">NEGATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="alguien, ausente">ALGUIEN, AUSENTE</td>
  <td data-order="pro">Pro</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-warning col-sm-9 force-square">AUSENTE</span></center></td>
  <td></td>
</tr>
</tbody>
</table>
"""


def test_parsear_acta_extrae_filas():
    filas = politica._parsear_acta(FIXTURE_ACTA)
    assert filas == [
        {"nombre": "JUEZ, LUIS ALFREDO", "bloque": "La Libertad Avanza", "provincia": "Córdoba", "voto": "AFIRMATIVO"},
        {"nombre": "KUEIDER, EDGARDO", "bloque": "Union Por La Patria", "provincia": "Entre Ríos", "voto": "NEGATIVO"},
        {"nombre": "ALGUIEN, AUSENTE", "bloque": "Pro", "provincia": "CABA", "voto": "AUSENTE"},
    ]


def test_parsear_acta_ignora_filas_incompletas():
    assert politica._parsear_acta("<table><tr><td>Solo una celda</td></tr></table>") == []


def test_parsear_acta_ignora_fila_de_encabezado():
    # La fila <thead> real tiene solo <th> (0 <td>) — no debe colarse como dato.
    html = """
    <table id="myTable">
    <thead><tr class="tr-oficial"><th></th><th>DIPUTADO</th><th>BLOQUE</th><th>PROVINCIA</th><th>VOTO</th><th></th></tr></thead>
    <tbody></tbody>
    </table>
    """
    assert politica._parsear_acta(html) == []


def test_parsear_acta_html_vacio():
    assert politica._parsear_acta("") == []


def test_parsear_acta_incluye_provincia():
    filas = politica._parsear_acta(FIXTURE_ACTA)
    assert filas[0]["provincia"] == "Córdoba"
    assert filas[1]["provincia"] == "Entre Ríos"


def test_parsear_acta_ignora_fila_sin_bloque():
    # Regresión: fila real "PENDIENTE DE INCORPORACIÓN" (legislador sin asignar)
    # tiene nombre no-vacío pero bloque vacío — debe ser filtrada.
    # Estructura: 6 <td> (pasar el gate de longitud), pero bloque data-order=""
    html = """
    <table id="myTable">
    <tbody>
    <tr>
      <td><div><a><img></a></div></td>
      <td data-order="pendiente">PENDIENTE DE INCORPORACIÓN</td>
      <td data-order=""></td>
      <td data-order="">—</td>
      <td><center><span class="label label-default">INEXISTENTE</span></center></td>
      <td></td>
    </tr>
    </tbody>
    </table>
    """
    assert politica._parsear_acta(html) == []


# ── Diputados vía PDF directo (ADR-0040 — reemplaza el mock de la SPA bloqueada) ──

FIXTURE_ACTA_DIPUTADOS_PDF = (Path(__file__).parent / "fixtures" / "acta_diputados_5959.pdf").read_bytes()


def test_parsear_acta_diputados_pdf_extrae_filas_reales():
    filas = politica._parsear_acta_diputados_pdf(FIXTURE_ACTA_DIPUTADOS_PDF)
    # Acta real (O.D. 149, RIGI, 24-jun-2026): 131 AFIRMATIVO + 103 NEGATIVO
    # + 16 AUSENTE + 2 ABSTENCION = 252 filas -- verificado contra el PDF real.
    assert len(filas) == 252
    from collections import Counter
    assert Counter(f["voto"] for f in filas) == {
        "AFIRMATIVO": 131, "NEGATIVO": 103, "AUSENTE": 16, "ABSTENCION": 2,
    }
    lla = [f for f in filas if politica.es_bloque_lla(f["bloque"])]
    assert Counter(f["voto"] for f in lla) == {"AFIRMATIVO": 93, "AUSENTE": 1}
    assert filas[0] == {"nombre": "AGUERO, GUILLERMO CESAR", "bloque": "Ucr - Union Civica Radical",
                         "provincia": "Chaco", "voto": "AFIRMATIVO"}


def test_diputados_acta_fecha_extrae_del_encabezado_real():
    assert politica._diputados_acta_fecha(FIXTURE_ACTA_DIPUTADOS_PDF) == datetime(2026, 6, 24)


def test_diputados_acta_id_maximo_retrocede_si_la_semilla_no_existe(monkeypatch):
    existentes = {10, 20, 30}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    # semilla 45 no existe -- retrocede de a 50 (a -5, ya <=0) sin encontrar nada
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=45) is None


def test_diputados_acta_id_maximo_avanza_hasta_el_primer_hueco(monkeypatch):
    existentes = {5, 6, 7}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=5) == 7


def test_diputados_acta_id_maximo_tolera_huecos_de_numeracion(monkeypatch):
    # La numeración real de actas tiene huecos (verificado: 101 en el caché,
    # el más ancho de 15 ids) -- un acta nueva publicada DESPUÉS de un hueco
    # tiene que descubrirse igual, no quedar invisible tras el primer 404.
    existentes = {5, 6, 9}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=5) == 9


def test_diputados_acta_id_maximo_retrocede_y_encuentra(monkeypatch):
    # Retroceso EXITOSO: la semilla 60 no existe, retrocede de a 50 hasta 10
    # (válido) y desde ahí avanza hasta el máximo real (11).
    existentes = {10, 11}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=60) == 11


def test_diputados_acta_id_maximo_endpoint_patologico_devuelve_none(monkeypatch):
    # Si el endpoint respondiera 200 a cualquier id, el avance no puede ser
    # infinito: corta en el tope y devuelve None (no un máximo inventado).
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, id: b"x")
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=5) is None


def test_diputados_acta_id_maximo_arranca_del_maximo_cacheado(monkeypatch):
    # El punto de partida acompaña el crecimiento real de la numeración: si
    # el caché por acta ya conoce ids más altos que la semilla estática, el
    # probeo arranca del máximo cacheado — con la semilla fija sola, cada
    # corrida re-descargaba todos los ids posteriores y el tope de avance se
    # volvía alcanzable con el paso de las sesiones (None permanente).
    monkeypatch.setattr(politica, "_cargar_cache_cohesion_diputados",
                         lambda: {"100": {"fecha": "2026-06-24", "rice": 90.0}})
    existentes = {100, 101}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    # desde_id=5 no existe: si arrancara de la semilla, el retroceso daría
    # None; que devuelva 101 prueba que arrancó del máximo cacheado (100).
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=5) == 101


def test_diputados_acta_id_maximo_cache_corrupto_cae_a_la_semilla(monkeypatch):
    # Una entrada corrupta/manual del caché con un id inverosímilmente alto
    # NO puede dejar al colector muerto para siempre: cuando el retroceso
    # desde el candidato cacheado agota sus intentos sin tocar el rango real,
    # se reintenta una vez desde la semilla estática.
    monkeypatch.setattr(politica, "_cargar_cache_cohesion_diputados",
                         lambda: {"999999": {"fecha": "2026-06-24", "rice": 90.0}})
    existentes = {10, 11}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id in existentes else None)
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=60) == 11


def test_diputados_acta_id_maximo_fallo_transitorio_devuelve_none(monkeypatch):
    # Si un probeo falla de forma transitoria no se puede saber dónde termina
    # la numeración: un máximo subestimado haría que el walk anual cachee el
    # año sin las actas de arriba (hallazgo de re-revisión). El fallo debe
    # propagarse como None (sin id_maximo esta corrida), no tratarse como 404.
    existentes = {5, 6, 7}
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: politica._ACTA_FALLO if id == 7
                         else (b"x" if id in existentes else None))
    assert politica._diputados_acta_id_maximo(MagicMock(), desde_id=5) is None


def _mock_acta_diputados(monkeypatch, fechas: dict, filas_lla_por_id: dict | None = None):
    """Helper: simula el endpoint PDF para los ids en `fechas`
    ({id: datetime}), con _parsear_acta_diputados_pdf devolviendo
    filas_lla_por_id.get(id, filas por defecto con señal) para que
    indice_rice() no sea None salvo que el test pida lo contrario. Los ids
    que no están en `fechas` responden _ACTA_NO_EXISTE (hueco de id genuino,
    404) -- para simular un fallo transitorio, el test debe mockear
    _diputados_acta_pdf con _ACTA_FALLO explícitamente."""
    filas_lla_por_id = filas_lla_por_id or {}
    filas_default = [{"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
                      {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"}]
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: str(id).encode() if id in fechas else politica._ACTA_NO_EXISTE)
    monkeypatch.setattr(politica, "_diputados_acta_fecha", lambda c: fechas[int(c.decode())])
    monkeypatch.setattr(politica, "_parsear_acta_diputados_pdf",
                         lambda c: filas_lla_por_id.get(int(c.decode()), filas_default))


def test_acta_diputados_cacheada_no_pide_red_si_ya_esta_en_cache(monkeypatch):
    llamadas = []
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, id: llamadas.append(id) or b"x")
    cache = {"5": {"fecha": "2026-06-24", "rice": 87.5}}

    entrada = politica._acta_diputados_cacheada(MagicMock(), 5, cache)

    assert entrada == {"fecha": datetime(2026, 6, 24), "rice": 87.5}
    assert llamadas == []   # cache hit -- nunca llamó a _diputados_acta_pdf


def test_acta_diputados_cacheada_descarga_y_cachea_en_miss(monkeypatch):
    _mock_acta_diputados(monkeypatch, {5: datetime(2026, 6, 24)})
    cache = {}

    entrada = politica._acta_diputados_cacheada(MagicMock(), 5, cache)

    assert entrada == {"fecha": datetime(2026, 6, 24), "rice": politica.indice_rice(1, 1)}
    assert cache["5"] == {"fecha": "2026-06-24", "rice": politica.indice_rice(1, 1)}


def test_acta_diputados_cacheada_sin_senal_igual_se_cachea_con_rice_none(monkeypatch):
    # regresión: la primera versión NO cacheaba las actas sin señal (bloque
    # LLA empatado/ausente), así que un walk repetido las re-descargaba
    # cada vez -- contradice "la próxima corrida solo baja lo no cacheado".
    _mock_acta_diputados(monkeypatch, {5: datetime(2026, 6, 24)},
                          filas_lla_por_id={5: []})
    cache = {}

    entrada = politica._acta_diputados_cacheada(MagicMock(), 5, cache)

    assert entrada == {"fecha": datetime(2026, 6, 24), "rice": None}
    assert cache["5"] == {"fecha": "2026-06-24", "rice": None}


def test_acta_diputados_cacheada_404_no_se_cachea(monkeypatch):
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, id: politica._ACTA_NO_EXISTE)
    cache = {}

    assert politica._acta_diputados_cacheada(MagicMock(), 5, cache) is None
    assert cache == {}   # un hueco de id no es un dato -- no se guarda


def test_acta_diputados_cacheada_fallo_transitorio_devuelve_sentinela(monkeypatch):
    # Un fallo de red NO es un hueco de id: se devuelve _ACTA_FALLO para que
    # el backfill anual sepa que el detalle quedó incompleto, y no se cachea.
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, id: politica._ACTA_FALLO)
    cache = {}

    assert politica._acta_diputados_cacheada(MagicMock(), 5, cache) is politica._ACTA_FALLO
    assert cache == {}


def test_cargar_y_guardar_cache_cohesion_diputados_hacen_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(politica, "DIPUTADOS_COHESION_CACHE_PATH", tmp_path / "cache.json")
    assert politica._cargar_cache_cohesion_diputados() == {}

    politica._guardar_cache_cohesion_diputados({"5": {"fecha": "2026-06-24", "rice": 87.5}})

    assert politica._cargar_cache_cohesion_diputados() == {"5": {"fecha": "2026-06-24", "rice": 87.5}}


def test_fetch_cohesion_bloque_diputados_actas_anio_recorta_por_anio(monkeypatch):
    # ids 10..6 son de 2026, 5..1 son de 2025 -- pidiendo anio=2026 con
    # MARGEN_SALIDA=5, debe cortar apenas ve 5 actas seguidas de un año
    # ANTERIOR (ids 5,4,3,2,1) y no seguir caminando.
    fechas = {i: datetime(2026, 1, i) for i in range(6, 11)}
    fechas.update({i: datetime(2025, 1, i) for i in range(1, 6)})
    _mock_acta_diputados(monkeypatch, fechas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 10)

    detalle = politica.fetch_cohesion_bloque_diputados_actas_anio(2026)

    assert sorted(f["fecha"] for f in detalle) == [f"2026-01-{i:02d}" for i in range(6, 11)]


def test_fetch_cohesion_bloque_diputados_actas_anio_anio_pasado_no_corta_de_mas(monkeypatch):
    # regresión del bug real: id_maximo SIEMPRE ancla a HOY (2026), así que
    # pedir un año pasado (2025) caminando desde ahí solía toparse con 5
    # actas de 2026 seguidas de entrada y cortar ANTES de llegar a 2025. Las
    # actas de un año más nuevo que el pedido no deben contar para el margen
    # de salida -- solo las de un año más viejo (ya pasamos el objetivo).
    fechas = {i: datetime(2026, 1, i) for i in range(6, 11)}     # 5 actas de 2026 (más nuevo que el pedido)
    fechas.update({i: datetime(2025, 6, i) for i in range(1, 4)})  # 3 actas de 2025 (el año pedido)
    _mock_acta_diputados(monkeypatch, fechas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 10)

    detalle = politica.fetch_cohesion_bloque_diputados_actas_anio(2025)

    assert sorted(f["fecha"] for f in detalle) == ["2025-06-01", "2025-06-02", "2025-06-03"]


def test_fetch_cohesion_bloque_diputados_actas_anio_fallo_transitorio_devuelve_none(monkeypatch):
    # ids 6..10 son de 2026, pero el id 8 falla de forma transitoria (red):
    # no se puede saber de qué año era, así que el detalle del año queda
    # incompleto y se devuelve None -- el caller no debe cachearlo. Un hueco
    # de id genuino (404, ausente de `fechas`) NO invalida: eso lo cubren
    # los dos tests de arriba, donde los ids fuera de `fechas` responden
    # _ACTA_NO_EXISTE y el detalle igual se devuelve.
    fechas = {i: datetime(2026, 1, i) for i in range(6, 11)}
    _mock_acta_diputados(monkeypatch, fechas)
    pdf_mock = politica._diputados_acta_pdf
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: politica._ACTA_FALLO if id == 8 else pdf_mock(s, id))
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 10)

    assert politica.fetch_cohesion_bloque_diputados_actas_anio(2026) is None


def test_fetch_cohesion_bloque_diputados_promedia_solo_actas_en_ventana(monkeypatch):
    hoy = datetime.now()
    fechas = {10: hoy - timedelta(days=5), 9: hoy - timedelta(days=200)}
    filas_lla = [{"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
                 {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 10)
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: str(id).encode() if id in fechas else politica._ACTA_NO_EXISTE)
    monkeypatch.setattr(politica, "_diputados_acta_fecha", lambda c: fechas[int(c.decode())])
    monkeypatch.setattr(politica, "_parsear_acta_diputados_pdf", lambda c: filas_lla)

    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)

    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)
    assert resultado["fecha_dato"] == fechas[10].strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_diputados_sin_actas_en_ventana_pero_corrida_exitosa(monkeypatch):
    hoy = datetime.now()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 5)
    monkeypatch.setattr(politica, "_diputados_acta_pdf",
                         lambda s, id: b"x" if id == 5 else politica._ACTA_NO_EXISTE)
    monkeypatch.setattr(politica, "_diputados_acta_fecha", lambda c: hoy - timedelta(days=200))
    monkeypatch.setattr(politica, "_parsear_acta_diputados_pdf", lambda c: [])

    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)

    assert resultado is not None
    assert resultado["valor"] is None
    assert resultado["n_actas"] == 0
    assert resultado["corrida_exitosa_en"] == hoy.strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_diputados_sin_id_maximo_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: None)
    assert politica.fetch_cohesion_bloque() is None


def test_fetch_cohesion_bloque_diputados_incluye_desactualizado_false(monkeypatch):
    # Regresión (hallazgo P2 de revisión externa / Codex, ya vigente antes del
    # cambio a PDF): toda corrida exitosa debe traer "desactualizado": False.
    hoy = datetime.now()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo", lambda s: 1)
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, id: b"x" if id == 1 else None)
    monkeypatch.setattr(politica, "_diputados_acta_fecha", lambda c: hoy - timedelta(days=10))
    monkeypatch.setattr(politica, "_parsear_acta_diputados_pdf", lambda c: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])

    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)

    assert resultado["desactualizado"] is False


def test_cohesion_desactualizada_corrida_exitosa_hoy():
    assert not politica._cohesion_desactualizada(None, {"valor": 90.0, "corrida_exitosa_en": "2026-07-07"})


def test_cohesion_desactualizada_sin_corrida_previa_ni_actual():
    assert politica._cohesion_desactualizada(None, None)


def test_cohesion_desactualizada_corrida_previa_reciente():
    reciente = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert not politica._cohesion_desactualizada({"corrida_exitosa_en": reciente}, None)


def test_cohesion_desactualizada_corrida_previa_vieja():
    vieja = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    assert politica._cohesion_desactualizada({"corrida_exitosa_en": vieja}, None)


def test_cohesion_desactualizada_corrida_exitosa_sin_votos_nuevos():
    hoy = datetime.now().strftime("%Y-%m-%d")
    corrida_receso = {"valor": None, "n_actas": 0, "corrida_exitosa_en": hoy}
    assert not politica._cohesion_desactualizada(None, corrida_receso)


# ── _es_cohesion_legado (hallazgo P1 de revisión externa / Codex) ───────────
# cohesion_bloque fue, hasta ea95da2, un placeholder MANUAL: {"valor": 78,
# "estado": "placeholder", "unidad": "% votos en línea con la posición oficial
# del bloque LLA", ...} (forma real confirmada vía
# `git show 584571b:./data/politica/manuales.json`). Si ese cache sobrevive en
# indicadores_anteriores cuando este código corre por primera vez contra el
# cache de producción (antes de que el scraper nuevo tenga su primera corrida
# exitosa), el código de carry-forward de main() lo arrastraría para siempre
# como si fuera un índice de Rice genuino -- ambas son números 0-100, pero con
# significados completamente distintos. El discriminador es la AUSENCIA de
# "n_actas", clave que SOLO fetch_cohesion_bloque (el scraper nuevo) setea.

LEGADO_MANUAL_COHESION_BLOQUE = {
    "valor": 78,
    "estado": "placeholder",
    "unidad": "% votos en línea con la posición oficial del bloque LLA",
    "fuente": "Votaciones Cámara de Diputados — elaboración CIGOB en base a Hcdn.gob.ar",
    "notas": (
        "Proporción de diputados del bloque LLA que votaron alineados con la "
        "posición oficial en las votaciones nominales de los últimos 3 meses."
    ),
    "fecha_dato": "2026-04-01",
}


def test_es_cohesion_legado_detecta_placeholder_manual():
    assert politica._es_cohesion_legado(LEGADO_MANUAL_COHESION_BLOQUE)


def test_es_cohesion_legado_no_marca_forma_nueva_como_legado():
    # Forma real devuelta por fetch_cohesion_bloque en una corrida exitosa.
    forma_nueva = {
        "valor": 62.5,
        "unidad": "% cohesión (índice de Rice), promedio actas divididas últimos 90 días",
        "fuente": "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
        "fecha_dato": "2026-07-01",
        "n_actas": 4,
        "corrida_exitosa_en": "2026-07-07",
        "desactualizado": False,
    }
    assert not politica._es_cohesion_legado(forma_nueva)


def test_es_cohesion_legado_no_marca_receso_legislativo_como_legado():
    # Corrida exitosa pero sin actas en la ventana (receso) -- "valor" es None
    # pero "n_actas" (0) SÍ está presente: no debe confundirse con el legado.
    forma_nueva_sin_votos = {
        "valor": None,
        "unidad": "% cohesión (índice de Rice), promedio actas divididas últimos 90 días",
        "fuente": "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
        "fecha_dato": None,
        "n_actas": 0,
        "corrida_exitosa_en": "2026-07-07",
        "desactualizado": False,
    }
    assert not politica._es_cohesion_legado(forma_nueva_sin_votos)


# ── Senado (cohesion_bloque_senado) ──────────────────────────────────────────

FIXTURE_LISTADO_SENADO = """
<table>
<tr>
  <td><span style="display:none">20260211</span> 11/02/2026</td>
  <td>Modernización Laboral. Título I.
    <a href="/votaciones/detalleActa/2623">Ver</a>
  </td>
</tr>
</table>
"""


def test_paced_get_reusa_logica_de_pacing(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._paced_get(session, "https://www.senado.gob.ar", "/votaciones/actas")
    assert r.status_code == 200
    session.get.assert_called_with("https://www.senado.gob.ar/votaciones/actas", timeout=politica.HTTP_TIMEOUT)


def test_paced_post_reusa_logica_de_pacing(monkeypatch):
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._paced_post(session, "https://www.senado.gob.ar", "/votaciones/actas",
                              data={"busqueda_actas[anio]": "2024"})
    assert r.status_code == 200
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2024"},
        timeout=politica.HTTP_TIMEOUT,
    )


def test_paced_post_reintenta_ante_403(monkeypatch):
    session = MagicMock()
    resp_403 = MagicMock(status_code=403)
    resp_200 = MagicMock(status_code=200)
    session.post.side_effect = [resp_403, resp_403, resp_200]
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._paced_post(session, "https://www.senado.gob.ar", "/votaciones/actas",
                                      data={"busqueda_actas[anio]": "2023"})
    assert resultado is resp_200
    assert session.post.call_count == 3


def test_hcdn_votaciones_get_sigue_funcionando_via_paced_get(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert r.status_code == 200
    session.get.assert_called_with(f"{politica.HCDN_VOTACIONES_BASE}/votaciones/actas", timeout=politica.HTTP_TIMEOUT)


def test_descubrir_actas_senado_extrae_id_y_fecha():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    actas = politica._descubrir_actas_senado(session, 2026)
    assert actas == [{"id": "2623", "fecha": datetime(2026, 2, 11)}]
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2026"},
        timeout=politica.HTTP_TIMEOUT,
    )


def test_descubrir_actas_senado_pide_el_anio_correcto_no_el_actual():
    # Regresión directa del bug de auditoría 2026-07-08: un año PASADO debe
    # pedirse explícitamente en el form, no depender de que el servidor
    # devuelva el año en curso por default.
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    politica._descubrir_actas_senado(session, 2023)
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2023"},
        timeout=politica.HTTP_TIMEOUT,
    )


def test_fetch_cohesion_bloque_senado_es_complementario(monkeypatch):
    hoy = datetime.now()
    actas = [{"id": "2623", "fecha": hoy - timedelta(days=5)}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, a: actas)
    monkeypatch.setattr(politica, "_paced_get", lambda s, base, path: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque_senado()
    assert resultado["valor"] == 100.0
    assert "Senado" in resultado["fuente"]


def test_fetch_cohesion_bloque_senado_ventana_de_backfill_ancla_al_anio_pedido(monkeypatch):
    # Regresión (hallazgo de revisión, Tarea 2 de este plan): fetch_cohesion_bloque
    # (Diputados) tuvo este mismo bug (Tarea 6, cross-fix) — la ventana de
    # dias_ventana anclada a datetime.now() en vez de al 31-dic de `anio` hace
    # que el backfill de años pasados sea estructuralmente imposible. El brief
    # de esta tarea reintrodujo la versión sin el fix; se corrige acá mirando
    # la implementación ya probada de fetch_cohesion_bloque.
    anio_backfill = datetime.now().year - 2
    acta_de_ese_anio = datetime(anio_backfill, 6, 15)
    actas = [{"id": "1", "fecha": acta_de_ese_anio}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, a: actas)
    monkeypatch.setattr(politica, "_paced_get", lambda s, base, path: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque_senado(anio=anio_backfill, dias_ventana=366)
    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)


def test_fetch_cohesion_bloque_senado_actas_anio_devuelve_detalle_crudo_por_acta(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: [
        {"id": "1", "fecha": datetime(2026, 6, 1)},
        {"id": "2", "fecha": datetime(2026, 6, 10)},
    ])
    filas_por_acta = {
        "1": [{"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
              {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"}],
        "2": [{"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
              {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"}],
    }

    # El "html" que devuelve _paced_get es el id de la acta (path pedido);
    # _parsear_acta lo usa para elegir qué filas devolver -- mismo truco que
    # el resto de los tests de detalle-por-acta de este archivo.
    def fake_paced_get(s, base, path):
        return MagicMock(text=path.rsplit("/", 1)[-1])

    monkeypatch.setattr(politica, "_paced_get", fake_paced_get)
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: filas_por_acta[html])

    detalle = politica.fetch_cohesion_bloque_senado_actas_anio(2026)

    assert detalle == [
        {"fecha": "2026-06-01", "rice": 100.0},
        {"fecha": "2026-06-10", "rice": politica.indice_rice(1, 1)},
    ]


def test_fetch_cohesion_bloque_senado_actas_anio_sin_actas_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: None)
    assert politica.fetch_cohesion_bloque_senado_actas_anio(2026) is None


def test_fetch_cohesion_bloque_senado_actas_anio_detalle_fallido_devuelve_none(monkeypatch):
    # Un timeout puntual en el detalle de UNA acta no puede producir una
    # lista "válida" con esa acta faltante: el caller cachea años cerrados
    # como inmutables y el agujero quedaría congelado para siempre.
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: [
        {"id": "1", "fecha": datetime(2026, 6, 1)},
        {"id": "2", "fecha": datetime(2026, 6, 10)},
    ])
    filas = [{"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
             {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"}]

    def fake_paced_get(s, base, path):
        if path.endswith("/2"):
            return None   # detalle de la acta 2: fallo transitorio
        return MagicMock(text="1")

    monkeypatch.setattr(politica, "_paced_get", fake_paced_get)
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: filas)

    assert politica.fetch_cohesion_bloque_senado_actas_anio(2026) is None


def test_agregar_cohesion_ventana_filtra_por_fecha_y_promedia():
    detalle = [
        {"fecha": "2026-01-01", "rice": 50.0},   # fuera de ventana
        {"fecha": "2026-06-01", "rice": 100.0},
        {"fecha": "2026-06-10", "rice": 80.0},
    ]
    resultado = politica._agregar_cohesion_ventana(detalle, datetime(2026, 6, 15), dias_ventana=90)
    assert resultado == {"valor": 90.0, "fecha_dato": "2026-06-10", "n_actas": 2}


def test_agregar_cohesion_ventana_sin_actas_en_ventana_devuelve_none():
    detalle = [{"fecha": "2025-01-01", "rice": 90.0}]
    assert politica._agregar_cohesion_ventana(detalle, datetime(2026, 6, 15), dias_ventana=90) is None


# ── Alineamiento de senadores por provincia (reemplaza gobernadores_alineamiento) ──

FIXTURE_ACTA_ALINEAMIENTO = """
<table id="myTable">
<tbody>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador uno">SENADOR UNO</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador dos">SENADOR DOS</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador tres">SENADOR TRES</td>
  <td data-order="union civica radical">Union Civica Radical</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador cuatro">SENADOR CUATRO</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador cinco">SENADOR CINCO</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador seis">SENADOR SEIS</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
</tbody>
</table>
"""


def test_alineamiento_de_una_acta_agrupa_por_provincia_excluyendo_full_lla():
    # Posición LLA en esta acta: 2 senadores LLA de CABA, ambos AFIRMATIVO -> posición = AFIRMATIVO.
    # CABA tiene 1 senador no-LLA (UCR, AFIRMATIVO) -> coincide -> CABA: 1/1 = 100%.
    # Córdoba tiene 3 senadores no-LLA (PJ): AFIRMATIVO, NEGATIVO, NEGATIVO -> 1/3 coincide -> 33.3%.
    # (CABA no se excluye del todo -- tiene 1 senador no-LLA real, solo se ignora el voto de los 2 LLA)
    filas = politica._parsear_acta(FIXTURE_ACTA_ALINEAMIENTO)
    resultado = politica._alineamiento_por_provincia(filas)
    assert resultado == {"CABA": (1, 1), "Córdoba": (1, 3)}  # (coincidencias, total) por provincia


def test_alineamiento_por_provincia_provincia_100pct_lla_no_aparece():
    fixture_solo_lla = FIXTURE_ACTA_ALINEAMIENTO.replace(
        'data-order="union civica radical">Union Civica Radical',
        'data-order="la libertad avanza">La Libertad Avanza',
    )
    filas = politica._parsear_acta(fixture_solo_lla)
    resultado = politica._alineamiento_por_provincia(filas)
    assert "CABA" not in resultado  # los 3 senadores de CABA son LLA -- sin señal, se excluye
    assert resultado == {"Córdoba": (1, 3)}


def test_fetch_alineamiento_senadores_prov_promedia_provincias(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: session)
    monkeypatch.setattr(politica, "_descubrir_actas_senado",
                         lambda s, anio: [{"id": "1", "fecha": datetime(2026, 6, 1)}])
    monkeypatch.setattr(politica, "_paced_get",
                         lambda s, base, path: MagicMock(status_code=200, text=FIXTURE_ACTA_ALINEAMIENTO))

    resultado = politica.fetch_alineamiento_senadores_prov(anio=2026, dias_ventana=366)

    # CABA=100%, Córdoba=33.33...% -> promedio = 66.67%
    assert resultado["valor"] == 66.7
    assert resultado["n_provincias"] == 2


# Acta 2: mismo bloque LLA de CABA (2 AFIRMATIVO), pero el senador no-LLA de
# CABA ahora vota NEGATIVO (se desalinea) -- sin filas de Córdoba, para poder
# aislar el cálculo de acumulación de CABA entre 2 actas.
FIXTURE_ACTA2_CABA_DESALINEADO = """
<table id="myTable">
<tbody>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador uno">SENADOR UNO</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador dos">SENADOR DOS</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador tres">SENADOR TRES</td>
  <td data-order="union civica radical">Union Civica Radical</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
</tbody>
</table>
"""

# Acta 3: el bloque LLA de CABA queda empatado (1 AFIRMATIVO, 1 NEGATIVO) --
# _alineamiento_por_provincia debe devolver {} (sin señal), y esta acta NO
# debe mover fecha_max aunque sea la más reciente de las 3.
FIXTURE_ACTA3_LLA_EMPATADO = """
<table id="myTable">
<tbody>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador uno">SENADOR UNO</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador dos">SENADOR DOS</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador tres">SENADOR TRES</td>
  <td data-order="union civica radical">Union Civica Radical</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
</tbody>
</table>
"""


def test_fetch_alineamiento_senadores_prov_acumula_entre_actas_y_fecha_max_solo_avanza_con_senal(monkeypatch):
    # Hallazgo de revisión (2026-07-08): fecha_max se actualizaba si el
    # acumulado GLOBAL era no vacío, no si la acta ACTUAL había aportado señal
    # -- una acta posterior sin señal (empate LLA) hacía avanzar fecha_dato
    # igual, sobreestimando la recencia real del dato.
    session = MagicMock()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: session)
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: [
        {"id": "1", "fecha": datetime(2026, 6, 1)},
        {"id": "2", "fecha": datetime(2026, 6, 10)},
        {"id": "3", "fecha": datetime(2026, 6, 20)},  # LLA empatado -- sin señal
    ])
    fixtures = {
        "1": FIXTURE_ACTA_ALINEAMIENTO,
        "2": FIXTURE_ACTA2_CABA_DESALINEADO,
        "3": FIXTURE_ACTA3_LLA_EMPATADO,
    }

    def fake_paced_get(s, base, path):
        acta_id = path.rsplit("/", 1)[-1]
        return MagicMock(status_code=200, text=fixtures[acta_id])

    monkeypatch.setattr(politica, "_paced_get", fake_paced_get)

    resultado = politica.fetch_alineamiento_senadores_prov(anio=2026, dias_ventana=366)

    # CABA acumulado entre acta 1 y 2: (1+0, 1+1) = (1, 2) -> 50%.
    # Córdoba solo aporta en acta 1: (1, 3) -> 33.3%. Promedio: 41.7%.
    assert resultado["valor"] == 41.7
    assert resultado["n_provincias"] == 2
    # La acta 3 (20-jun) no aporta señal (empate LLA) -- fecha_dato debe
    # quedar en la última acta que SÍ aportó (acta 2, 10-jun), no en 20-jun.
    assert resultado["fecha_dato"] == "2026-06-10"


def test_fetch_alineamiento_senadores_actas_anio_devuelve_detalle_crudo_por_acta(monkeypatch):
    # Mismas 3 actas que el test de acumulación de arriba, pero acá se pide
    # el detalle SIN agregar -- una fila por acta con señal, la 3ª (LLA
    # empatado) se excluye igual que en la agregación.
    session = MagicMock()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: session)
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: [
        {"id": "1", "fecha": datetime(2026, 6, 1)},
        {"id": "2", "fecha": datetime(2026, 6, 10)},
        {"id": "3", "fecha": datetime(2026, 6, 20)},  # LLA empatado -- sin señal
    ])
    fixtures = {
        "1": FIXTURE_ACTA_ALINEAMIENTO,
        "2": FIXTURE_ACTA2_CABA_DESALINEADO,
        "3": FIXTURE_ACTA3_LLA_EMPATADO,
    }

    def fake_paced_get(s, base, path):
        acta_id = path.rsplit("/", 1)[-1]
        return MagicMock(status_code=200, text=fixtures[acta_id])

    monkeypatch.setattr(politica, "_paced_get", fake_paced_get)

    detalle = politica.fetch_alineamiento_senadores_actas_anio(2026)

    assert detalle == [
        {"fecha": "2026-06-01", "provincias": {"CABA": [1, 1], "Córdoba": [1, 3]}},
        {"fecha": "2026-06-10", "provincias": {"CABA": [0, 1]}},
    ]


def test_fetch_alineamiento_senadores_actas_anio_sin_actas_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: None)
    assert politica.fetch_alineamiento_senadores_actas_anio(2026) is None


def test_fetch_alineamiento_senadores_actas_anio_detalle_fallido_devuelve_none(monkeypatch):
    # Mismo contrato que cohesion_bloque_senado_actas_anio: un fallo
    # transitorio en el detalle de una acta invalida el año completo, para
    # que el caché anual inmutable nunca congele un agujero.
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: [
        {"id": "1", "fecha": datetime(2026, 6, 1)},
        {"id": "2", "fecha": datetime(2026, 6, 10)},
    ])

    def fake_paced_get(s, base, path):
        if path.endswith("/2"):
            return None   # detalle de la acta 2: fallo transitorio
        return MagicMock(status_code=200, text=FIXTURE_ACTA_ALINEAMIENTO)

    monkeypatch.setattr(politica, "_paced_get", fake_paced_get)

    assert politica.fetch_alineamiento_senadores_actas_anio(2026) is None


def test_agregar_alineamiento_ventana_filtra_por_fecha_y_promedia():
    detalle = [
        {"fecha": "2026-01-01", "provincias": {"CABA": [1, 1]}},          # fuera de ventana
        {"fecha": "2026-06-01", "provincias": {"CABA": [1, 1], "Córdoba": [1, 3]}},
        {"fecha": "2026-06-10", "provincias": {"CABA": [0, 1]}},
    ]
    resultado = politica._agregar_alineamiento_ventana(detalle, datetime(2026, 6, 15), dias_ventana=90)
    # CABA acumulado entre 01-jun y 10-jun: (1+0, 1+1) = (1, 2) -> 50%.
    # Córdoba solo aporta el 01-jun: (1, 3) -> 33.3%. Promedio: 41.7%.
    assert resultado == {"valor": 41.7, "fecha_dato": "2026-06-10", "n_provincias": 2}


def test_agregar_alineamiento_ventana_sin_actas_en_ventana_devuelve_none():
    detalle = [{"fecha": "2025-01-01", "provincias": {"CABA": [1, 1]}}]
    assert politica._agregar_alineamiento_ventana(detalle, datetime(2026, 6, 15), dias_ventana=90) is None


# ── Adhesión a reformas (RIGI) ────────────────────────────────────────────────

FIXTURE_TABLA_RIGI = """
<table>
<tr><td>CATAMARCA</td><td><a href="/ley_dgr_catamarca">Ley DGR Catamarca 5.863</a></td></tr>
<tr><td>CHUBUT</td><td><a href="/ley_dgr_chubut">Ley DGR Chubut 123</a></td></tr>
</table>
"""


def test_fetch_adhesion_reformas_provincial_cuenta_provincias(monkeypatch):
    monkeypatch.setattr(politica.requests, "get",
        lambda *a, **kw: MagicMock(status_code=200, text=FIXTURE_TABLA_RIGI))
    resultado = politica.fetch_adhesion_reformas_provincial()
    assert resultado["n_provincias"] == 2
    assert resultado["valor"] == round(2 / 24 * 100, 1)


def test_fetch_adhesion_reformas_provincial_request_fallido(monkeypatch):
    monkeypatch.setattr(politica.requests, "get",
        lambda *a, **kw: MagicMock(status_code=500, text=""))
    assert politica.fetch_adhesion_reformas_provincial() is None


def test_fetch_adhesion_reformas_provincial_deduplica_filas_repetidas(monkeypatch):
    # Regresión: el sitio real (MAGyP) tiene un <tr> vacío malformado que con
    # html.parser produce una fila duplicada (confirmado en vivo: SANTA CRUZ
    # aparece 2 veces). `provincias` debe ser un set() -- si se refactoriza a
    # una lista, este test debe fallar (con la fixture de 2 arriba no lo haría).
    fixture_con_duplicado = FIXTURE_TABLA_RIGI.replace(
        "</table>",
        '<tr><td>CATAMARCA</td><td><a href="/x">otra ley</a></td></tr></table>',
    )
    monkeypatch.setattr(politica.requests, "get",
        lambda *a, **kw: MagicMock(status_code=200, text=fixture_con_duplicado))
    resultado = politica.fetch_adhesion_reformas_provincial()
    assert resultado["n_provincias"] == 2  # CATAMARCA + CHUBUT, no 3


# ── eficacia_legislativa: media sanción no es ley ────────────────────────────

def test_es_media_sancion_distingue_etiquetas():
    assert politica._es_media_sancion("TEXTO DE LA MEDIA SANCION")
    assert politica._es_media_sancion("Texto de la media sancion con modificaciones")
    assert not politica._es_media_sancion("CONSIDERACION Y SANCION")
    assert not politica._es_media_sancion("TEXTO SANCION DEFINITIVA")


def test_fetch_eficacia_legislativa_excluye_medias_sanciones(monkeypatch):
    # regresión (auditoría 2026-07-09): q='SANCION' del CKAN también matchea
    # 'TEXTO DE LA MEDIA SANCION' (aprobación de UNA cámara, no ley) y esas
    # filas contaban como proyecto aprobado. Acá: 2 proyectos PE enviados en
    # ventana; uno con sanción real, otro SOLO con media sanción -> 1/2 = 50%,
    # no 100%.
    hoy = datetime.now().strftime("%Y-%m-%d")

    def fake_paginate(rid, q=""):
        if rid == politica.HCDN_PROYECTOS_RID:
            return [
                {"PROYECTO_ID": "HCDN1", "EXP_DIPUTADOS": "0001-PE-2026", "PUBLICACION_FECHA": hoy},
                {"PROYECTO_ID": "HCDN2", "EXP_SENADO": "0002-PE-2026", "PUBLICACION_FECHA": hoy},
            ]
        return [
            {"PROYECTO_ID": "HCDN1", "MOVIMIENTO": "TEXTO DE LA MEDIA SANCION", "FECHA": hoy},
            {"PROYECTO_ID": "HCDN2", "MOVIMIENTO": "CONSIDERACION Y SANCION", "FECHA": hoy},
        ]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    resultado = politica.fetch_eficacia_legislativa()

    assert resultado["enviados_n"] == 2
    assert resultado["aprobados_n"] == 1   # solo la sanción real; la media sanción no cuenta
    assert resultado["valor"] == 50.0


# ── protestas_caba (reutiliza el fetcher ACLED de gestión, ADR-0017) ─────────
# En gestión este indicador es CONTEXTO y no puntúa ("premiaría menos
# marchas"). En política SÍ puntúa: nivel de conflicto social como condición
# objetiva de gobernabilidad (Matus), no un juicio sobre la legitimidad de
# protestar.

def test_politica_reutiliza_fetcher_de_gestion(monkeypatch):
    import gestion
    monkeypatch.setattr(gestion, "fetch_protestas_caba",
                         lambda: {"valor": 12.0, "fecha_dato": "2026-07-07"})
    resultado = politica.fetch_protestas_caba()
    assert resultado["valor"] == 12.0


def test_politica_protestas_caba_devuelve_none_si_gestion_devuelve_none(monkeypatch):
    import gestion
    monkeypatch.setattr(gestion, "fetch_protestas_caba", lambda: None)
    assert politica.fetch_protestas_caba() is None


# ── _valor_itcp (wiring ITCP, Tarea 5) ───────────────────────────────────────
# Cross-fix: protestas_caba puntúa en el ITCP sobre "var_vs_2023" (% variación
# vs. base 2023), NO sobre "valor" (conteo crudo de eventos, que puede estar
# en cientos — itcp.BANDAS_ITCP["protestas_caba"] espera una escala %).

def test_valor_itcp_protestas_caba_usa_var_vs_2023_no_valor():
    entry = {"valor": 347, "var_vs_2023": 15.3}
    assert politica._valor_itcp("protestas_caba", entry) == 15.3


def test_valor_itcp_protestas_caba_none_si_var_vs_2023_ausente():
    # base_2023 == 0 -> gestion.fetch_protestas_caba() deja var_vs_2023 en None
    entry = {"valor": 347, "var_vs_2023": None}
    assert politica._valor_itcp("protestas_caba", entry) is None


def test_valor_itcp_otros_indicadores_usan_valor_directo():
    entry = {"valor": 62.5, "var_vs_2023": 999.0}  # campo ajeno, no debe usarse
    assert politica._valor_itcp("cohesion_bloque", entry) == 62.5


# ── _resultado_utilizable (hallazgo de auditoría 2026-07-08) ────────────────
# protestas_caba puntúa en el ITCP sobre var_vs_2023, no sobre "valor" (conteo
# crudo). El gate de frescura de main() históricamente miraba solo "valor" --
# si algún día base_2023 fuera 0, gestion.fetch_protestas_caba() deja
# var_vs_2023 en None pero "valor" sigue presente, y el indicador se contaría
# como fresco sin aportar realmente al ITCP. Reusa _valor_itcp para que el
# gate de frescura y el cálculo del índice usen SIEMPRE el mismo valor.

def test_resultado_utilizable_protestas_caba_requiere_var_vs_2023():
    entry = {"valor": 347, "var_vs_2023": None}
    assert not politica._resultado_utilizable("protestas_caba", entry)


def test_resultado_utilizable_protestas_caba_con_var_vs_2023():
    entry = {"valor": 347, "var_vs_2023": 15.3}
    assert politica._resultado_utilizable("protestas_caba", entry)


def test_resultado_utilizable_otro_indicador_usa_valor_directo():
    assert politica._resultado_utilizable("cohesion_bloque", {"valor": 62.5})


def test_resultado_utilizable_none_no_es_utilizable():
    assert not politica._resultado_utilizable("cohesion_bloque", None)


# ── _extraer_cifra_cepa / _fecha_informe_cepa (backfill movilizacion_cepa) ──
# Fixtures = fragmentos REALES de 4 informes de centrocepa.com.ar verificados
# en vivo 2026-07-08 (ids 809, 773, 748, 739). 748 y 739 acumulan desde un
# ancla temporal distinta (ene-2024 / dic-2023, no "desde inicios del año en
# curso").
#
# CORRECCIÓN (verificado en vivo por segunda vez, contra la página COMPLETA
# de 748, no solo el fragmento de la cifra acumulada): a diferencia de lo que
# se asumió al escribir el fixture original, _extraer_cifra_cepa NO devuelve
# None para 748 -- el cuerpo del informe también trae una oración con un
# promedio mensual ("promediando 24 casos por mes") que matchea la rama
# m_mes. FRAGMENTO_748 abajo incluye AMBAS oraciones reales (en el mismo
# orden en que aparecen en la página real) para reflejar esto con fidelidad.
# La exclusión de 748 de la serie NO ocurre en _extraer_cifra_cepa: ocurre
# en el filtro de fetch_cepa_movilizacion_serie() (scripts/descargar_series.py),
# que descarta cualquier lectura cuyo campo "rama" no sea "m_tot" -- ver
# test_extraer_cifra_cepa_informe_748_no_es_acumulado más abajo, que
# documenta el discriminador real. 739 sí fue reverificado
# contra su página completa real y sigue devolviendo None (ninguna de las
# 2 frases-gatillo del regex está presente en esa página).

FRAGMENTO_809 = (
    '<meta property="datePublished" content="2026-06-09T15:40:01-03:00">'
    "Desde inicios del 2026 se registraron, al menos, 101 conflictos "
    "laborales de trabajadores estatales en todo el país."
)
FRAGMENTO_773 = (
    '<meta property="datePublished" content="2026-04-09T23:47:31-03:00">'
    "Desde inicios del 2026 se registraron, al menos, 92 conflictos "
    "laborales de trabajadores estatales en todo el país."
)
FRAGMENTO_748 = (
    '<meta property="datePublished" content="2026-02-18T18:29:01-03:00">'
    "Desde enero 2024 hasta el 5 de febrero 2026 se registraron al menos "
    "717 casos de conflictividad laboral en todo el país."
    "Desde la elección del 26 de octubre de 2025 los conflictos no se "
    "detuvieron, sino que se recrudecieron. Desde enero 2024 hasta "
    "septiembre 2025, se registraron 507 casos de conflictividad laboral "
    "(promediando 24 casos por mes). Sin embargo, luego de las elecciones "
    "se contabilizó un promedio de 42 casos por mes (210 desde las "
    "elecciones a febrero)."
)
FRAGMENTO_739 = (
    '<meta property="datePublished" content="2025-12-31T20:40:01-03:00">'
    "Ofrecemos un recuentro gráfico de los 629 conflictos laborales y "
    "cierres de empresas registrados durante el gobierno de Javier Milei."
)


def test_extraer_cifra_cepa_informe_809():
    r = politica._extraer_cifra_cepa(FRAGMENTO_809)
    assert r["cifra_cruda"] == 101.0
    assert r["valor"] == round(min(100.0, 101.0 / 200.0 * 100.0), 1)


def test_extraer_cifra_cepa_informe_773():
    r = politica._extraer_cifra_cepa(FRAGMENTO_773)
    assert r["cifra_cruda"] == 92.0


def test_extraer_cifra_cepa_informe_748_no_es_acumulado():
    # La página real de 748 SÍ matchea -- vía m_mes (tasa mensual, no el
    # "717 casos" acumulado desde ene-2024, que no dispara ninguna rama del
    # regex porque dice "casos" y no "conflictos"). re.search encuentra la
    # PRIMERA ocurrencia de "N casos por mes": "24 casos por mes" (ventana
    # ene24-sep25), no "42 casos por mes" (ventana post-elección) -- ambas
    # aparecen en el cuerpo real del informe.
    r = politica._extraer_cifra_cepa(FRAGMENTO_748)
    assert r == {"valor": 30.0, "cifra_cruda": 24.0, "metrica": "24.0 casos/mes", "rama": "m_mes"}
    # Discriminador real usado por fetch_cepa_movilizacion_serie() para
    # excluir esta lectura de la serie: no es "conflictos acumulados" (m_tot),
    # es una tasa mensual (m_mes) -- escala distinta (0-80 vs. 0-200),
    # no comparable con el resto de la serie (que es 100% m_tot).
    assert r["rama"] == "m_mes"


def test_extraer_cifra_cepa_informe_739_no_matchea_ninguna_rama():
    # "629 conflictos" pero sin ninguna de las 2 frases-gatillo del regex
    # ("al menos" / "se registraron" inmediatamente antes del número), y sin
    # ninguna oración de tasa mensual tampoco -- reverificado contra la
    # página real completa de 739 (2026-07-08), no solo este fragmento.
    assert politica._extraer_cifra_cepa(FRAGMENTO_739) is None


def test_fecha_informe_cepa_extrae_datepublished():
    assert politica._fecha_informe_cepa(FRAGMENTO_809) == "2026-06-09"
    assert politica._fecha_informe_cepa(FRAGMENTO_748) == "2026-02-18"


def test_fecha_informe_cepa_fallback_a_hoy_si_no_hay_meta():
    from datetime import date
    assert politica._fecha_informe_cepa("<html>sin meta tag</html>") == str(date.today())


# ── fetch_cepa_movilizacion: guard de rama en el fetch vigente ──────────────
# Hallazgo de la revisión final (2026-07-08): fetch_cepa_movilizacion_serie()
# ya filtra por rama=="m_tot", pero el fetch del indicador VIGENTE no lo
# hacía -- publicaba lo que sea que matcheara primero. Regresión directa:
# si el informe más reciente listado es rama=="m_mes" (tasa mensual, escala
# 0-80), no debe publicarse contra las bandas calibradas para m_tot
# (conteo acumulado, escala 0-200) -- degrada a None (cache), igual que
# "sin patrón encontrado".

def test_fetch_cepa_movilizacion_rechaza_informe_mas_reciente_si_no_es_m_tot(monkeypatch):
    listado_html = '<a href="/documentos/informes/999-conflictividad-ejemplo">ver</a>'
    informe_html = (
        '<meta property="datePublished" content="2026-07-01T00:00:00-03:00">'
        "Se registró un promedio de 30 casos por mes en el último trimestre."
    )

    def fake_get(url, headers=None, timeout=None):
        if "documentos/informes/999" in url:
            return MagicMock(status_code=200, text=informe_html)
        return MagicMock(status_code=200, text=listado_html)

    monkeypatch.setattr(politica.requests, "get", fake_get)
    assert politica.fetch_cepa_movilizacion() is None


# ── Compuesto bicameral de cohesión (ADR-0048) ───────────────────────────────

def _camara(valor=99.0, fecha="2026-06-24", n_actas=10, corrida="2026-07-10",
            desactualizado=False):
    return {"valor": valor, "fecha_dato": fecha, "n_actas": n_actas,
            "corrida_exitosa_en": corrida, "desactualizado": desactualizado}


def test_componer_cohesion_bloque_pondera_65_35():
    dip = _camara(valor=99.9, fecha="2026-06-24", n_actas=33)
    sen = _camara(valor=99.4, fecha="2026-06-04", n_actas=18)
    card = politica.componer_cohesion_bloque(dip, sen)
    # 0.65*99.9 + 0.35*99.4 = 99.725 -> 99.7 (valores live reales al 10-jul)
    assert card["valor"] == 99.7
    assert card["fecha_dato"] == "2026-06-24"    # la más nueva de las dos
    assert card["n_actas"] == 51
    assert card["desactualizado"] is False
    assert set(card["componentes"]) == {"diputados", "senado"}
    assert card["componentes"]["senado"]["valor"] == 99.4


def test_componer_cohesion_bloque_renormaliza_con_una_camara():
    card = politica.componer_cohesion_bloque(_camara(valor=98.0), None)
    assert card["valor"] == 98.0                 # 100% del peso a la única cámara
    assert set(card["componentes"]) == {"diputados"}


def test_componer_cohesion_bloque_sin_camaras_devuelve_none():
    assert politica.componer_cohesion_bloque(None, None) is None


def test_componer_cohesion_bloque_desactualizado_solo_si_todas_las_camaras():
    dip = _camara(desactualizado=True)
    sen = _camara(desactualizado=False)
    assert politica.componer_cohesion_bloque(dip, sen)["desactualizado"] is False
    sen_stale = _camara(desactualizado=True)
    assert politica.componer_cohesion_bloque(dip, sen_stale)["desactualizado"] is True


def test_anterior_camara_lee_componentes_de_la_card_compuesta():
    anteriores = {"cohesion_bloque": {
        "valor": 99.7, "componentes": {
            "diputados": {"valor": 99.9, "n_actas": 33},
            "senado": {"valor": 99.4, "n_actas": 18},
        },
    }}
    assert politica._anterior_camara(anteriores, "diputados")["valor"] == 99.9
    assert politica._anterior_camara(anteriores, "senado")["valor"] == 99.4


def test_anterior_camara_migra_del_cache_pre_compuesto():
    # Primera corrida post ADR-0048: el cache viejo tiene las DOS cards
    # separadas — diputados sale de cohesion_bloque (forma vieja, sin
    # "componentes") y senado de cohesion_bloque_senado.
    anteriores = {
        "cohesion_bloque": {"valor": 99.9, "n_actas": 33},
        "cohesion_bloque_senado": {"valor": 99.4, "n_actas": 18},
    }
    assert politica._anterior_camara(anteriores, "diputados")["valor"] == 99.9
    assert politica._anterior_camara(anteriores, "senado")["valor"] == 99.4


def test_anterior_camara_sin_cache_devuelve_none():
    assert politica._anterior_camara({}, "diputados") is None
    assert politica._anterior_camara({}, "senado") is None


def test_entrada_camara_fresca():
    resultado = _camara(valor=98.5)
    entrada, ok = politica._entrada_camara(resultado, _camara(valor=97.0))
    assert entrada is resultado
    assert ok is True


def test_entrada_camara_receso_reusa_anterior_sin_marcar_desactualizado():
    # Corrida exitosa (llegó al sitio) pero sin actas divididas en la ventana:
    # se reusa el último valor y se actualiza corrida_exitosa_en — misma
    # semántica que tenían las dos cards separadas.
    receso = {"valor": None, "n_actas": 0, "corrida_exitosa_en": "2026-07-10"}
    anterior = _camara(valor=97.0, corrida="2026-07-01")
    entrada, ok = politica._entrada_camara(receso, anterior)
    assert ok is True
    assert entrada["valor"] == 97.0
    assert entrada["desactualizado"] is False
    assert entrada["corrida_exitosa_en"] == "2026-07-10"


def test_entrada_camara_sin_corrida_cae_al_cache_con_chequeo_de_staleness():
    reciente = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    anterior = _camara(valor=97.0, corrida=reciente)
    entrada, ok = politica._entrada_camara(None, anterior)
    assert ok is False
    assert entrada["valor"] == 97.0
    assert entrada["desactualizado"] is False    # corrida previa reciente

    vieja = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    entrada, _ = politica._entrada_camara(None, _camara(valor=97.0, corrida=vieja))
    assert entrada["desactualizado"] is True


def test_entrada_camara_sin_nada_devuelve_none():
    entrada, ok = politica._entrada_camara(None, None)
    assert entrada is None
    assert ok is False
