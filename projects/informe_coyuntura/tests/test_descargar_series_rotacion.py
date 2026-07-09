"""rotacion_gabinete (ADR-0047): cómputo de la ventana móvil de 12 meses
sobre el registro curado, exclusión de laterales/reestructuraciones,
coincidencia card↔serie (G3 sin excepción) y reconciliación del detector
InfoLeg contra el registro."""
import sys
import json
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series
import politica


class _FakeDate(date):
    _hoy = date(2026, 7, 9)

    @classmethod
    def today(cls):
        return cls._hoy


def _registro_fixture() -> dict:
    """Registro mínimo con salidas, un lateral y una reestructuración: solo
    la clave 'salidas' debe contar en la serie."""
    return {
        "_meta": {"nota": "fixture"},
        "salidas": [
            {"n": 1, "persona": "Salida Vieja", "cargo": "Ministra de Prueba",
             "mes": "2025-06", "clasificacion": "salida_politica",
             "decreto_renuncia": "Decreto 100/2025"},
            {"n": 2, "persona": "Salida Politica", "cargo": "Ministro de Prueba",
             "mes": "2025-11", "clasificacion": "salida_politica",
             "decreto_renuncia": "Decreto 200/2025"},
            {"n": 3, "persona": "Salida Electoral", "cargo": "Ministra de Prueba",
             "mes": "2026-06", "clasificacion": "salida_estructural_electoral",
             "decreto_renuncia": "Decreto 300/2026"},
        ],
        "movimientos_laterales_no_contados": [
            {"persona": "Pase Lateral", "de": "Ministro del Interior",
             "a": "Jefe de Gabinete de Ministros", "mes": "2026-06",
             "decreto": "Decreto 300/2026"},
        ],
        "reestructuraciones_ley_ministerios": [
            {"mes": "2026-06", "hecho": "Disolución de una cartera", "cargos_rango_ministerial": 9},
        ],
    }


def _con_registro(monkeypatch, tmp_path, registro: dict) -> None:
    path = tmp_path / "gabinete_salidas.json"
    path.write_text(json.dumps(registro, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(politica, "GABINETE_SALIDAS_PATH", path)


def test_ventana_12m_cuenta_solo_salidas_y_respeta_el_borde():
    salidas = _registro_fixture()["salidas"]
    # jun-2025 cuenta en las ventanas que terminan jun-2025..may-2026 y cae
    # en la que termina jun-2026 (12 meses calendario, extremo inclusivo).
    assert len(politica.salidas_gabinete_ventana_12m(salidas, "2025-06")) == 1
    assert len(politica.salidas_gabinete_ventana_12m(salidas, "2026-05")) == 2
    en_jun = politica.salidas_gabinete_ventana_12m(salidas, "2026-06")
    assert [s["persona"] for s in en_jun] == ["Salida Politica", "Salida Electoral"]
    # un mes ilegible en el registro no rompe el cómputo, se ignora
    assert politica.salidas_gabinete_ventana_12m([{"mes": "sin-fecha"}], "2026-06") == []


def test_fetch_rotacion_gabinete_serie_reconstruye_ventana_movil(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    _con_registro(monkeypatch, tmp_path, _registro_fixture())

    serie = descargar_series.fetch_rotacion_gabinete_serie()
    puntos = dict((f, v) for f, v in serie)

    assert serie[0] == ["2023-12-01", 0]          # arranca en la asunción
    assert serie[-1][0] == "2026-07-01"           # incluye el mes corriente
    assert puntos["2025-05-01"] == 0
    assert puntos["2025-06-01"] == 1              # entra Salida Vieja
    assert puntos["2025-11-01"] == 2              # + Salida Politica
    assert puntos["2026-05-01"] == 2              # Salida Vieja todavía en ventana
    assert puntos["2026-06-01"] == 2              # sale Salida Vieja, entra Salida Electoral
    assert puntos["2026-07-01"] == 2
    # los laterales y las reestructuraciones del fixture NO suman: jun-2026
    # tiene 1 salida real, no 3 eventos
    assert puntos["2026-06-01"] - puntos["2026-05-01"] == 0


def test_fetch_rotacion_gabinete_card_coincide_con_serie(tmp_path, monkeypatch):
    # G3 del gate sin excepción: la card (ventana 12m al mes corriente) debe
    # ser exactamente el último punto de la serie.
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(politica, "date", _FakeDate)
    monkeypatch.setattr(politica, "_detectar_salidas_gabinete_infoleg", lambda: None)
    _con_registro(monkeypatch, tmp_path, _registro_fixture())

    card = politica.fetch_rotacion_gabinete()
    serie = descargar_series.fetch_rotacion_gabinete_serie()

    assert card is not None
    assert card["valor"] == serie[-1][1] == 2
    assert card["salidas_politicas"] == 1
    assert card["salidas_estructurales"] == 1
    assert "Salida Politica (2025-11)" in card["detalle_txt"]
    assert card["desactualizado"] is False
    assert "detector_decretos_sin_registrar" not in card   # detector caído ≠ discrepancia


def test_fetch_rotacion_gabinete_sin_registro_devuelve_none(tmp_path, monkeypatch):
    monkeypatch.setattr(politica, "GABINETE_SALIDAS_PATH", tmp_path / "no_existe.json")
    assert politica.fetch_rotacion_gabinete() is None


def test_fetch_rotacion_gabinete_serie_sin_registro_devuelve_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(politica, "GABINETE_SALIDAS_PATH", tmp_path / "no_existe.json")
    assert descargar_series.fetch_rotacion_gabinete_serie() == []


def test_regex_cargo_extrae_multiples_actos_del_mismo_decreto():
    # Resumen REAL del Decreto 548/2026 (InfoLeg id=427132, verificado en
    # vivo): acepta la renuncia de Adorni (JGM) Y la de Santilli (Interior)
    # -- que además viene repetida -- y designa a Santilli JGM. El regex debe
    # extraer los actos de renuncia sin confundir la designación.
    resumen = (
        "ACEPTASE LA RENUNCIA PRESENTADA POR EL SENOR MANUEL ADORNI "
        "(D.N.I. N° 28.052.206) AL CARGO DE JEFE DE GABINETE DE MINISTROS. "
        "ACEPTASE LA RENUNCIA PRESENTADA POR EL CONTADOR PUBLICO DIEGO CESAR SANTILLI "
        "(D.N.I. N° 17.735.449) AL CARGO DE MINISTRO DEL INTERIOR. "
        "ACEPTASE LA RENUNCIA PRESENTADA POR EL CONTADOR PUBLICO DIEGO CESAR SANTILLI "
        "(D.N.I. N° 17.735.449) AL CARGO DE MINISTRO DEL INTERIOR. "
        "DESIGNASE EN EL CARGO DE JEFE DE GABINETE DE MINISTROS AL CONTADOR PUBLICO "
        "DIEGO CESAR SANTILLI (D.N.I. N° 17.735.449)."
    )
    actos = [(m.group(1).strip(), m.group(2).strip())
             for m in politica._RE_GABINETE_CARGO.finditer(resumen)]
    assert ("SENOR MANUEL ADORNI", "JEFE DE GABINETE DE MINISTROS") in actos
    assert sum(1 for _, cargo in actos if cargo == "MINISTRO DEL INTERIOR") == 2  # dedupe aguas arriba
    # un "ministro plenipotenciario" del servicio exterior NO matchea
    diplomatico = ("ACEPTASE LA RENUNCIA PRESENTADA POR EL SENOR JUAN PEREZ "
                   "(D.N.I. N° 11.111.111) AL CARGO DE MINISTRO PLENIPOTENCIARIO DE PRIMERA CLASE")
    assert not politica._RE_GABINETE_CARGO.search(diplomatico)


def test_gabinete_discrepancias_compara_por_decreto():
    registro = _registro_fixture()
    detecciones = [
        # ya citado en el registro (como salida): no es discrepancia
        {"decreto": "Decreto 200/2025", "persona": "Salida Politica",
         "cargo": "MINISTRO DE PRUEBA", "mes_bo": "2025-11"},
        # ya citado en el registro (como lateral): tampoco
        {"decreto": "Decreto 300/2026", "persona": "Pase Lateral",
         "cargo": "MINISTRO DEL INTERIOR", "mes_bo": "2026-06"},
        # decreto nuevo, no citado: ESTA es la alerta
        {"decreto": "Decreto 999/2026", "persona": "Ministro Nuevo",
         "cargo": "MINISTRO DE PRUEBA", "mes_bo": "2026-07"},
    ]
    discrepancias = politica._gabinete_discrepancias(registro, detecciones)
    assert [d["decreto"] for d in discrepancias] == ["Decreto 999/2026"]
