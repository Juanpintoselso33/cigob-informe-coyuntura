"""Chequeos estáticos de plantilla.html: no hay navegador en este entorno
(ver README/issue #27, punto 4), así que esto es lo más cerca que se puede
verificar sin uno. Discrimina sobre el texto fuente, no ejecuta el DOM."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = (HERE / "plantilla.html").read_text()


def test_el_corte_por_defecto_no_esta_hardcodeado():
    assert "'2026-09-08'" not in HTML and '"2026-09-08"' not in HTML
    assert "data.fechas[data.fechas.length-1]" in HTML


def test_los_listeners_de_change_no_dejan_escapar_el_error():
    # addEventListener('change',pintar) deja la excepción fuera de cualquier
    # try/catch cuando el evento dispara más tarde (issue #27, punto 4).
    assert "addEventListener('change',pintar)" not in HTML
    assert HTML.count("addEventListener('change'") == 2
    assert HTML.count("catch(e){manejarError(e)}") >= 2


def test_pintar_no_asume_que_el_corte_existe():
    assert "if(!r)throw" in HTML or "if (!r) throw" in HTML
