import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica
from unittest.mock import MagicMock
from datetime import datetime


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
