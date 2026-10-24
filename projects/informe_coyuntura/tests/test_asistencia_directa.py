"""Planes sin intermediarios (ADR-0362): el indicador mide el cese de las
unidades de gestión del Potenciar Trabajo (Res. 84/2024, BO 10-abr-2024), no la
clasificación del gasto, que ya era 98,3% en 2023 y puntuaba 100 por algo hecho
antes del mandato."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import gestion  # noqa: E402


def test_vale_cero_antes_del_cese_y_cien_desde_el_boletin_oficial():
    assert gestion.asistencia_directa_valor("2024-04-09") == 0.0
    assert gestion.asistencia_directa_valor("2024-04-10") == 100.0
    assert gestion.asistencia_directa_valor("2023-12-31") == 0.0


def test_la_serie_arranca_en_cero_y_abril_de_2024_ya_cuenta():
    serie = dict(gestion.serie_asistencia_directa(date(2024, 6, 15)))
    assert list(serie)[0] == "2023-12-01"
    assert [serie[f"2024-{m:02d}-01"] for m in (1, 2, 3, 4, 5, 6)] == [0, 0, 0, 100, 100, 100]
    assert serie["2023-12-01"] == 0


def test_la_card_no_depende_de_la_api_de_presupuesto(monkeypatch):
    """Sin token de Presupuesto Abierto falta sólo el contexto, no el valor."""
    monkeypatch.setattr(gestion, "_pa_token", lambda: None)
    card = gestion.fetch_asistencia_directa()
    assert card["valor"] == 100.0
    assert "Res" in card["fuente"] and "84/2024" in card["detalle_txt"]
    assert card["valor"] == gestion.serie_asistencia_directa()[-1][1], "card = último punto de la serie (G3)"
