import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica
from unittest.mock import MagicMock
from datetime import datetime, timedelta


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
        {"nombre": "JUEZ, LUIS ALFREDO", "bloque": "La Libertad Avanza", "voto": "AFIRMATIVO"},
        {"nombre": "KUEIDER, EDGARDO", "bloque": "Union Por La Patria", "voto": "NEGATIVO"},
        {"nombre": "ALGUIEN, AUSENTE", "bloque": "Pro", "voto": "AUSENTE"},
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


def test_fetch_cohesion_bloque_promedia_solo_actas_en_ventana(monkeypatch):
    hoy = datetime.now()
    actas = [
        {"id": "1", "slug": "a", "fecha": hoy - timedelta(days=10)},
        {"id": "2", "slug": "b", "fecha": hoy - timedelta(days=200)},  # fuera de ventana
    ]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_get", lambda s, p: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)
    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)
    assert resultado["fecha_dato"] == (hoy - timedelta(days=10)).strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_sin_actas_en_ventana_pero_corrida_exitosa(monkeypatch):
    hoy = datetime.now()
    actas = [{"id": "1", "slug": "a", "fecha": hoy - timedelta(days=200)}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)
    assert resultado is not None
    assert resultado["valor"] is None
    assert resultado["n_actas"] == 0
    assert resultado["corrida_exitosa_en"] == hoy.strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_falla_de_red_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: None)
    assert politica.fetch_cohesion_bloque() is None


def test_fetch_cohesion_bloque_incluye_desactualizado_false(monkeypatch):
    # Regresión (hallazgo P2 de revisión externa / Codex): toda corrida exitosa
    # debe traer "desactualizado": False, igual que fetch_cohesion_bloque_senado
    # y fetch_adhesion_reformas_provincial -- sin esta clave, main() la asigna
    # directo a frescos["cohesion_bloque"] sin agregarla en ningún lado, y
    # tests/test_publicar.py::test_publicar_genera_snapshot exige que todo
    # indicador publicado tenga "desactualizado".
    hoy = datetime.now()
    actas = [{"id": "1", "slug": "a", "fecha": hoy - timedelta(days=10)}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_get", lambda s, p: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)
    assert resultado["desactualizado"] is False


def test_fetch_cohesion_bloque_ventana_de_backfill_ancla_al_anio_pedido(monkeypatch):
    anio_backfill = datetime.now().year - 2   # un año claramente pasado, no el actual
    acta_de_ese_anio = datetime(anio_backfill, 6, 15)   # bien adentro del año pedido
    actas = [{"id": "1", "slug": "a", "fecha": acta_de_ese_anio}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_get", lambda s, p: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque(anio=anio_backfill, dias_ventana=366)
    # Con el bug (limite anclado a HOY), esta acta habría quedado SIEMPRE fuera de ventana
    # (un año pasado nunca puede estar a <366 días de "hoy" salvo el año en curso/anterior parcial).
    # Con el fix (limite anclado al 31-dic de anio_backfill), esta acta SÍ debe entrar.
    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)


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
# que descarta cualquier lectura cuya "metrica" no sea "conflictos
# acumulados" -- ver test_extraer_cifra_cepa_informe_748_no_es_acumulado
# más abajo, que documenta el discriminador real. 739 sí fue reverificado
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
