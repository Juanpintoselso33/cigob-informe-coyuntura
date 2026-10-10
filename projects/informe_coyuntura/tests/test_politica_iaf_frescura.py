"""`iaf_transferencias` no puede declarar la fecha de la CORRIDA como fecha del dato.

Hasta el 29-jul-2026 la card ponía `fecha_dato = date.today()`, así que se
mostraba fresca todos los días mientras describía un año cerrado, y G2 —que mide
el rezago con ese campo— no podía avisar nada. Desde ADR-0353 la ventana son 12
meses móviles y la fecha es el último día del último mes con IPC publicado.

Lo que no es legítimo es esconder el rezago: la fecha tiene que ser la del dato.
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gate_calidad
import politica

FUENTE = (ROOT / "scripts" / "politica.py").read_text(encoding="utf-8")


def test_la_card_no_declara_la_fecha_de_la_corrida():
    """Lectura estática: que nadie vuelva a poner date.today() ahí."""
    i = FUENTE.index("def fetch_iaf_transferencias")
    cuerpo = FUENTE[i:FUENTE.index("\ndef ", i + 10)]
    assert 'str(date.today())' not in cuerpo and "date.today()" not in cuerpo, (
        "iaf_transferencias volvió a declarar la fecha de la corrida como fecha del dato")
    assert re.search(r'"fecha_dato":\s*ultimo_dia\.isoformat\(\)', cuerpo), (
        "la fecha del dato tiene que ser el cierre del último mes de la ventana")


def test_la_fecha_es_el_cierre_del_mes_que_informa():
    """Coherencia entre lo que dice `periodo` y lo que dice `fecha_dato`."""
    card = politica.fetch_iaf_transferencias()
    if card is None:
        import pytest
        pytest.skip("la fuente RON no respondió; el test estático ya cubre la regresión")
    f = date.fromisoformat(card["fecha_dato"])
    assert (f + timedelta(days=1)).day == 1, "la fecha del dato no es fin de mes"
    fin_txt = card["periodo"].split(" vs ")[0].split("–")[1]       # «ago 2026»
    assert fin_txt == politica._etiqueta_mes(card["fecha_dato"][:7])
    assert f < date.today(), "el último mes no puede ser el corriente"


def test_el_rezago_de_hoy_cabe_en_el_tope_del_gate():
    """Ya no tiene tope propio (ADR-0353): una mensual con IPC entra en el default.
    Si alguien le vuelve a poner 560 el indicador deja de avisar cuando se congela."""
    assert "iaf_transferencias" not in gate_calidad.MAX_DIAS
    card = politica.fetch_iaf_transferencias()
    if card is None:
        import pytest
        pytest.skip("la fuente RON no respondió")
    rezago = (date.today() - date.fromisoformat(card["fecha_dato"])).days
    assert rezago <= gate_calidad.MAX_DIAS_DEFAULT, (
        f"rezago {rezago}d supera el default: la fuente se atrasó de verdad")
