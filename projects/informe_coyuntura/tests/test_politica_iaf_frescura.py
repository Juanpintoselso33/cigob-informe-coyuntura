"""`iaf_transferencias` no puede declarar la fecha de la CORRIDA como fecha del dato.

La serie RON de Hacienda es por año calendario ejecutado, y el indicador compara
el último año completo contra el anterior: en julio de 2026 informa 2025 contra
2024. Hasta el 29-jul-2026 la card ponía `fecha_dato = date.today()`, así que se
mostraba fresca todos los días mientras describía un año cerrado, y G2 —que mide
el rezago justamente con ese campo— no podía avisar nada.

El rezago de una fuente anual es legítimo; lo que no es legítimo es esconderlo.
La tolerancia va declarada en gate_calidad.MAX_DIAS, que es donde vive el criterio
por indicador.
"""
import re
import sys
from datetime import date
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
    assert 'str(date.today())' not in cuerpo, (
        "iaf_transferencias volvió a declarar la fecha de la corrida como fecha del dato")
    assert re.search(r'"fecha_dato":\s*f"\{year_ref\}-12-31"', cuerpo), (
        "la fecha del dato tiene que ser el cierre del año de referencia")


def test_la_fecha_es_el_cierre_del_anio_que_informa():
    """Coherencia entre lo que dice `periodo` y lo que dice `fecha_dato`."""
    card = politica.fetch_iaf_transferencias()
    if card is None:
        import pytest
        pytest.skip("la fuente RON no respondió; el test estático ya cubre la regresión")
    anio_ref = int(card["periodo"].split(" vs ")[0])
    assert card["fecha_dato"] == f"{anio_ref}-12-31"
    assert anio_ref <= date.today().year - 1, "el año de referencia no puede ser el corriente"


def test_el_gate_tiene_una_tolerancia_declarada_para_esta_fuente():
    """Con la fecha real, el rezago de una anual supera el default de G2. Si la
    tolerancia no está declarada, el gate corta el pipeline por una demora que es
    estructural — y si está declarada de más, deja de avisar cuando la fuente
    muere. 560 días cubren el ciclo anual completo de publicación."""
    tope = gate_calidad.MAX_DIAS.get("iaf_transferencias")
    assert tope is not None, "iaf_transferencias necesita tope propio en MAX_DIAS"
    assert 400 <= tope <= 800, f"tope {tope} fuera del rango razonable para una anual"
    assert tope > gate_calidad.MAX_DIAS_DEFAULT


def test_el_rezago_de_hoy_entra_en_la_tolerancia():
    """Control de que el tope no quedó corto contra el dato que está publicado."""
    card = politica.fetch_iaf_transferencias()
    if card is None:
        import pytest
        pytest.skip("la fuente RON no respondió")
    f = date.fromisoformat(card["fecha_dato"])
    rezago = (date.today() - f).days
    assert rezago <= gate_calidad.MAX_DIAS["iaf_transferencias"], (
        f"rezago {rezago}d supera el tope declarado: o la fuente se atrasó de verdad, "
        f"o hay que revisar si Hacienda publicó el año siguiente")
