"""El aviso a Slack distingue lo esperado de lo que hay que mirar.

Un canal de alertas se muere por exceso, no por defecto: si avisa todas las
noches, en una semana nadie lo lee y el día que importe tampoco. Por eso lo que
se prueba acá es sobre todo lo que NO tiene que avisar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from aviso_slack import analizar

# Log real de la corrida del 25-ago-2026, recortado.
SAIJ = ("[WARN] politica.judicializacion: 403 Client Error: Forbidden for url: "
        "https://www.saij.gob.ar/busqueda. Usando cache.\n"
        "##[notice]politica exit=1\n"
        "  [ERR] judicializacion: 403 Client Error: Forbidden for url: "
        "https://www.saij.gob.ar/busqueda -- se conservan las filas anteriores\n")


def test_el_bloqueo_conocido_de_saij_no_avisa():
    """Pasa casi todas las noches y la política es refrescar a mano.
    Avisarlo convierte el canal en ruido."""
    assert analizar(SAIJ + "##[notice]macro exit=0\n") == []


def test_una_corrida_limpia_no_avisa():
    assert analizar("##[notice]macro exit=0\n##[notice]gestion exit=0\n") == []


def test_exit_1_solo_no_avisa():
    """exit=1 es «alguna fuente cayó a caché», la condición normal."""
    assert analizar("##[notice]politica exit=1\n") == []


def test_una_fuente_caida_entera_si_avisa():
    ms = analizar("##[notice]gestion exit=2\n")
    assert len(ms) == 1 and "gestion" in ms[0] and "caída" in ms[0]


def test_un_error_de_codigo_disfrazado_de_fuente_si_avisa():
    """El caso que costó cuatro días: NameError reportado como fuente caída."""
    log = ("  [ERR] icg_utdt: name 'UTDT_ICG_REFERER' is not defined "
           "-- se conservan las filas anteriores\n")
    ms = analizar(log)
    assert len(ms) == 1
    assert "icg_utdt" in ms[0] and "no es la fuente" in ms[0]


def test_otro_error_de_red_tampoco_avisa():
    for msg in ("HTTPSConnectionPool: Read timed out",
                "502 Server Error: Bad Gateway for url: http://x",
                "Max retries exceeded with url: /a"):
        assert analizar(f"  [ERR] otra_fuente: {msg} -- se conservan\n") == [], msg


def test_agotar_el_presupuesto_avisa():
    ms = analizar("##[warning]series agotó su presupuesto de 25m — se sigue con caché\n")
    assert len(ms) == 1 and "presupuesto" in ms[0]
