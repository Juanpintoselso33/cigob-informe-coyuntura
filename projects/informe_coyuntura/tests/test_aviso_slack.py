"""El aviso a Slack distingue lo esperado de lo que hay que mirar.

Un canal de alertas se muere por exceso, no por defecto: si avisa todas las
noches, en una semana nadie lo lee y el día que importe tampoco. Por eso lo que
se prueba acá es sobre todo lo que NO tiene que avisar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from aviso_slack import analizar, causas, cola, colectores, resumen_pytest

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


# ── Lo que el aviso tiene que DECIR, no sólo lo que tiene que callar ─────────
#
# Hasta septiembre de 2026 el aviso nombraba el paso ("Tests de reconciliación")
# y nada más: para saber qué había pasado había que abrir el run igual. Peor,
# las tres noches del 1 al 3-sep mandaron el mismo texto y se leían como tres
# problemas cuando era uno solo — un mes escrito a mano adentro de un test.

CORRIDA_CAIDA = (
    "::notice::macro exit=0\n"
    "::notice::politica exit=1\n"
    "  [FALLA] G3 gestion/concesiones_infraestructura: card 28.7 ≠ serie 100.0\n"
    "FAILED tests/test_piso_cobertura.py::test_la_ausencia_de_componentes"
    " - AssertionError: sólo 24 de 32 meses se desvían más de 3 puntos\n"
    "1 failed, 3211 passed, 4 skipped in 216.41s\n"
    "##[error]Process completed with exit code 1.\n"
)


def test_el_aviso_nombra_la_prueba_que_fallo_y_su_motivo():
    """Lo mínimo para no tener que abrir el run."""
    texto = "\n".join(causas(CORRIDA_CAIDA))
    assert "test_la_ausencia_de_componentes" in texto
    assert "24 de 32 meses" in texto, "sin el motivo, el nombre del test no alcanza"


def test_el_aviso_nombra_la_falla_del_gate():
    assert any("G3 gestion/concesiones" in c for c in causas(CORRIDA_CAIDA))


def test_no_repite_el_epitafio_generico_de_github():
    """«Process completed with exit code 1» es «falló porque falló»."""
    assert not any("exit code 1" in c for c in causas(CORRIDA_CAIDA))


def test_cuenta_cuantas_pruebas_fallaron():
    assert resumen_pytest(CORRIDA_CAIDA) == "1 de 3212 pruebas"


def test_un_log_ilegible_no_inventa_una_causa():
    """Prefiere decir que no sabe: el aviso nunca es la única fuente."""
    assert causas("basura sin formato\n") == []


# ── La forma cruda de los comandos de workflow ──────────────────────────────
#
# `::notice::` es lo que el script ESCRIBE y lo que el `tee` guarda en el
# archivo que este parser lee; `##[notice]` es como GitHub lo RENDERIZA en el
# log descargado. Los tests de arriba usaban sólo la segunda forma, así que los
# avisos de "fuente caída entera" y "presupuesto agotado" pasaban en verde
# mientras en producción no matcheaban NUNCA. Se prueban las dos.

def test_la_fuente_caida_entera_grita_en_la_forma_que_escribe_el_script():
    assert analizar("::notice::gestion exit=2\n"), (
        "el archivo que se lee trae `::notice::`, no `##[notice]`: con el parser "
        "mirando sólo la forma renderizada este aviso nunca se disparó")


def test_el_presupuesto_agotado_grita_en_la_forma_que_escribe_el_script():
    assert analizar("::warning::series agotó su presupuesto de 25m\n")


def test_los_colectores_se_leen_en_las_dos_formas():
    assert colectores("::notice::macro exit=0\n##[notice]politica exit=1\n") == [
        ("macro", 0), ("politica", 1)]


# ── Los cinco huecos que encontró la revisión adversarial ───────────────────

COLECCION_ROTA = (
    "ERROR tests/test_vida.py\n"
    "E   ModuleNotFoundError: No module named 'pypdf'\n"
    "1 error in 0.12s\n"
)


def test_un_pytest_que_ni_arranca_tambien_dice_por_que():
    """Un ModuleNotFoundError rompe la COLECCIÓN: no hay `FAILED` ni
    `N failed`. Es la forma exacta en que un crash de import se veía como un
    diagnóstico vacío — y ya pasó, con pypdf, el 26-jul-2026 (ADR-0133)."""
    texto = "\n".join(causas(COLECCION_ROTA))
    assert "test_vida.py" in texto
    assert "pypdf" in texto, "sin el módulo que falta, el aviso no sirve de nada"
    assert "módulo" in resumen_pytest(COLECCION_ROTA)


def test_un_log_sin_formato_conocido_muestra_el_final_en_vez_de_callarse():
    """«No se pudo leer la causa» y nada más es peor que pegar el final del
    log: el traceback casi siempre está ahí aunque no tenga formato."""
    assert cola("linea vieja\nTraceback (most recent call last):\nKeyError: 'x'\n") \
        == ["linea vieja", "Traceback (most recent call last):", "KeyError: 'x'"]


def test_los_delimitadores_no_se_mezclan():
    """`::error]` y `##[error::` no existen; matchearlos es inventar causas."""
    assert causas("::error]falso\n") == []
    assert causas("##[error::falso\n") == []
    assert causas("##[error]verdadero\n") == ["verdadero"]


def test_una_causa_que_aparece_dos_veces_se_lista_una():
    """El aviso lee dos logs (gates y colectores) concatenados. Si la misma
    causa cae en los dos, listarla dos veces la hace parecer dos problemas —
    exactamente lo que este parser vino a evitar."""
    doble = CORRIDA_CAIDA + CORRIDA_CAIDA
    assert causas(doble) == causas(CORRIDA_CAIDA)
