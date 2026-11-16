"""Actas de Diputados desde ArgentinaDatos cuando la Cámara da 403 (ADR-0434).

Sin red: el acta es el JSON real del acta 5737 (insistencia de la ley 27.791,
20-ago-2025) recortado a tres votos; el padrón, dos entradas con la forma de
`api.argentinadatos.com/v1/diputados/diputados`.
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import argentinadatos_diputados as ad  # noqa: E402
import politica  # noqa: E402

ACTA_5737 = {
    "id": "5737", "titulo": "INSISTENCIA PROYECTO DE LEY 27.791.", "resultado": "negativo",
    "fecha": "2025-08-21T02:15:00.000Z", "votosAfirmativos": 160, "votosNegativos": 83,
    "abstenciones": 6, "ausentes": 8, "presentes": 249, "miembros": None,
    "tipoMayoria": "Dos tercios", "baseMayoria": "Votos Emitidos",
    "votos": [{"diputado": "Menem, Martin", "tipoVoto": "presidente"},
              {"diputado": 'Ali, Ernesto "Pipi"', "tipoVoto": "afirmativo"},
              {"diputado": "Matzkin, Martin", "tipoVoto": "negativo"}],
}
PADRON = [
    {"apellido": "Ali", "nombre": "Ernesto", "bloque": "Unión por la Patria", "provincia": "San Luis",
     "periodoBloque": {"inicio": "2023-12-10T00:00:00-03:00", "fin": "2027-12-09T00:00:00-03:00"}},
    {"apellido": "Matzkin", "nombre": "Martín Alberto", "bloque": "La Libertad Avanza",
     "provincia": "Río Negro",
     "periodoBloque": {"inicio": "2023-12-10T00:00:00-03:00", "fin": "2027-12-09T00:00:00-03:00"}},
]


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    monkeypatch.setattr(ad, "_PADRON", PADRON)
    monkeypatch.setattr(ad, "_ACTAS", {2026: {6026: {"id": "6026"}}, 2025: {5737: ACTA_5737}})
    monkeypatch.setattr(ad, "_anio_actual", lambda: 2026)


def test_la_fecha_es_la_de_la_sesion_en_hora_argentina():
    """02:15 UTC del 21 es 23:15 del 20 en Buenos Aires: el día del acta."""
    assert ad.fecha_local(ACTA_5737).date().isoformat() == "2025-08-20"


def test_filas_sin_el_presidente_y_con_bloque_del_padron():
    filas = ad.filas(ACTA_5737)
    assert [f["nombre"] for f in filas] == ['Ali, Ernesto "Pipi"', "Matzkin, Martin"]
    assert filas[0]["bloque"] == "Unión por la Patria"          # el apodo no estorba
    assert filas[1]["bloque"] == "La Libertad Avanza"           # primer nombre del padrón
    assert [f["voto"] for f in filas] == ["AFIRMATIVO", "NEGATIVO"]


def test_los_lectores_de_pdf_leen_el_acta_de_argentinadatos():
    acta = ad.ActaAD(ACTA_5737)
    assert isinstance(acta, bytes)       # los walkers de ids la cuentan como existente
    enc = politica._parsear_encabezado_acta_diputados(acta)
    assert enc["fecha"] == "2025-08-20" and enc["resultado"] == "NEGATIVO"
    assert enc["votos_txt"] == "160 afirmativos - 83 negativos - 6 abst."
    assert "tercios" in enc["mayoria"].lower()
    cab = politica._cabecera_acta_diputados_pdf(acta)
    assert cab["bancas_camara"] == 257 and cab["afirmativos_encabezado"] == 160
    assert politica._diputados_acta_fecha(acta) == datetime(2025, 8, 20)
    assert len(politica._parsear_acta_diputados_pdf(acta)) == 2


def test_existe_hueco_o_sin_respuesta():
    assert isinstance(politica._acta_diputados_argentinadatos(5737), ad.ActaAD)
    assert politica._acta_diputados_argentinadatos(6000) is politica._ACTA_NO_EXISTE


def test_si_argentinadatos_tampoco_responde_es_un_fallo(monkeypatch):
    def caido(*a, **k):
        raise requests.ConnectionError("caído")
    monkeypatch.setattr(ad, "buscar_acta", caido)
    assert politica._acta_diputados_argentinadatos(5737) is None


def test_si_la_camara_no_da_el_pdf_se_usa_argentinadatos(monkeypatch):
    monkeypatch.setattr(politica, "_paced_get", lambda *a, **k: None)
    assert isinstance(politica._diputados_acta_pdf(None, 5737), ad.ActaAD)
