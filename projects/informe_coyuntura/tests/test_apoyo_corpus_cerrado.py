"""`apoyo_empresario` vuelve al ITCP con el corpus cerrado (ADR-0310).

ADR-0246 lo suspendió porque el saldo −0,429 salía de siete textos codificados
con catorce detectados sin codificar: medía qué se alcanzó a clasificar. La
condición de reingreso pedía corpus cerrado; esto la hace mecánica. La serie
llega sólo hasta el mes anterior al comunicado pendiente más viejo, así que un
pendiente nunca entra al saldo como si no existiera: congela el dato, y el
congelamiento se ve.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica
from cotejo_manual import avisos


class Hoy(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 14)


def _caso(fecha, postura):
    return {"fecha": fecha, "titulo": fecha, "camara": "UIA", "texto": "t",
            "postura": postura, "destinatario": "ejecutivo_nacional", "motivo": "m",
            "concordancia": "acuerdo", "pasada_2": {"postura": postura,
                                                   "destinatario": "ejecutivo_nacional"}}


@pytest.fixture
def registro(tmp_path, monkeypatch):
    cod = tmp_path / "cod.json"
    cod.write_text(json.dumps({"casos": [_caso("2025-06-02", "apoyo"), _caso("2026-03-10", "critica"),
                                         _caso("2026-07-14", "apoyo")]}))
    nov = tmp_path / "nov.json"
    nov.write_text(json.dumps({"pendientes": {}, "revisadas": {}}))
    monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", cod)
    monkeypatch.setattr(politica, "APOYO_NOVEDADES_PATH", nov)
    monkeypatch.setattr(politica, "date", Hoy)
    return nov


def _pendiente(nov, fecha):
    nov.write_text(json.dumps({"pendientes": {f"UIA|x-{fecha}": {
        "camara": "UIA", "id": f"x-{fecha}", "fecha": fecha, "titulo": "x", "url": "u"}},
        "revisadas": {}}))


def test_con_el_inventario_completo_la_serie_llega_al_mes_en_curso(registro):
    serie = politica.apoyo_empresario_serie()
    assert serie[-1][0] == "2026-09-01"


def test_un_pendiente_corta_la_serie_en_el_mes_anterior(registro):
    _pendiente(registro, "2026-08-20")
    serie = politica.apoyo_empresario_serie()
    assert serie[-1][0] == "2026-07-01"          # agosto no se calcula sin ese comunicado
    card = politica.fetch_apoyo_empresario()
    assert [card["fecha_dato"], card["valor"]] == serie[-1]   # G3: la card corta igual
    assert card["pendientes_de_codificar"] == 1


def test_un_pendiente_de_enero_corta_en_diciembre_del_ano_anterior(registro):
    _pendiente(registro, "2026-01-05")
    assert politica.apoyo_empresario_serie()[-1][0] == "2025-12-01"


def test_cada_pendiente_sale_como_cotejo_manual(capsys):
    politica.avisar_apoyo_pendientes({"UIA|a": {"url": "https://uia.org.ar/a"},
                                      "UIA|b": {"url": "https://uia.org.ar/b"}})
    mensajes = avisos(capsys.readouterr().err)
    assert len(mensajes) == 2 and all("apoyo_empresario" in m for m in mensajes)


def test_el_detector_corre_antes_que_la_card():
    # Si corriera después, un comunicado detectado esa noche cortaría la serie
    # (descargar_series lee el inventario ya actualizado) pero no la card, y el
    # gate G3 las encontraría distintas.
    import inspect
    src = inspect.getsource(politica.main)
    assert src.index("detectar_novedades_empresarias()") < src.index("fetch_apoyo_empresario")


def test_ya_no_esta_suspendido():
    import itcp
    assert "apoyo_empresario" not in itcp.INDICADORES_SUSPENDIDOS
    assert itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]["apoyo_empresario"] == 0.5


# ── Lo que agregó la revisión de Codex ───────────────────────────────────────

def test_un_pendiente_con_fecha_invalida_corta_igual(registro):
    for mala in ("", "2026-08", "2026-13-01"):
        registro.write_text(json.dumps({"pendientes": {"UIA|x": {"fecha": mala}}, "revisadas": {}}))
        assert politica.apoyo_empresario_serie()[-1][0] <= "2026-08-01", mala   # nunca el mes en curso ni futuro


def test_sin_comprobar_el_inventario_este_mes_no_avanza(registro):
    registro.write_text(json.dumps({"_meta": {"inventario_verificado": "2026-07-30"},
                                    "pendientes": {}, "revisadas": {}}))
    assert politica.apoyo_empresario_serie()[-1][0] == "2026-07-01"


def test_la_card_cortada_se_declara_desactualizada_y_no_cuenta_lo_posterior(registro, tmp_path, monkeypatch):
    cod = tmp_path / "cod2.json"
    cod.write_text(json.dumps({"casos": [_caso("2026-03-10", "critica"),
                                         _caso("2026-07-14", "apoyo"),
                                         _caso("2026-09-01", "apoyo")]}))
    monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", cod)
    assert politica.fetch_apoyo_empresario()["desactualizado"] is False
    _pendiente(registro, "2026-08-20")
    card = politica.fetch_apoyo_empresario()
    assert card["fecha_dato"] == "2026-07-01" and card["desactualizado"] is True
    assert card["comunicados_ventana"] == 2        # el apoyo de septiembre no descompone el saldo de julio


@pytest.mark.parametrize("cae,verificado", [(None, "2026-09-14"), ("uia", "2026-06-30"), ("aea", "2026-06-30")])
def test_solo_una_corrida_con_las_dos_camaras_comprueba_el_inventario(registro, monkeypatch, cae, verificado):
    registro.write_text(json.dumps({"_meta": {"inventario_verificado": "2026-06-30"},
                                    "pendientes": {}, "revisadas": {}}))
    monkeypatch.setattr(politica, "_apoyo_ya_codificados", lambda: set())
    monkeypatch.setattr(politica, "_apoyo_firmas_codificadas", lambda: set())

    def caida(*a, **k):
        raise ConnectionError("sin respuesta")
    monkeypatch.setattr(politica, "_uia_comunicados", caida if cae == "uia" else (lambda s, o: []))
    monkeypatch.setattr(politica, "_aea_comunicados", caida if cae == "aea" else (lambda s: []))
    store = politica.detectar_novedades_empresarias()
    assert store["_meta"]["inventario_verificado"] == verificado
