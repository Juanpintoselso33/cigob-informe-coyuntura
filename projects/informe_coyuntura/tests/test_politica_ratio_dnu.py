"""Regresiones offline para ratio_dnu con ventana móvil de 365 días (ADR-0058)."""
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import politica


class _RespuestaHome:
    text = '<form action="/infolegInternet/buscarNormas.do">'

    def raise_for_status(self):
        return None


class _RespuestaBusqueda:
    def __init__(self, texto):
        self.text = texto

    def raise_for_status(self):
        return None


def test_infoleg_session_count_arma_rango_de_fechas_explicito():
    """El POST usa desde/hasta explícitos (día/mes/año), no un año calendario
    completo — el cambio que habilita la ventana móvil (ADR-0058)."""
    capturado = {}

    class _SesionFake:
        def post(self, url, data, **kwargs):
            capturado["url"] = url
            capturado["data"] = data
            return _RespuestaBusqueda("Encontradas: 17")

    n = politica._infoleg_session_count(
        _SesionFake(), "https://x/buscar", "1",
        date(2025, 7, 16), date(2026, 7, 15),
    )

    assert n == 17
    assert capturado["data"]["tipoNorma"] == "1"
    assert capturado["data"]["diaPubDesde"] == "16"
    assert capturado["data"]["mesPubDesde"] == "07"
    assert capturado["data"]["anioPubDesde"] == "2025"
    assert capturado["data"]["diaPubHasta"] == "15"
    assert capturado["data"]["mesPubHasta"] == "07"
    assert capturado["data"]["anioPubHasta"] == "2026"


def test_infoleg_session_count_pasa_texto_de_dnu():
    class _SesionFake:
        def post(self, url, data, **kwargs):
            assert data["texto"] == "necesidad y urgencia"
            return _RespuestaBusqueda("Encontradas: 27")

    n = politica._infoleg_session_count(
        _SesionFake(), "https://x/buscar", "2",
        date(2025, 7, 16), date(2026, 7, 15), texto="necesidad y urgencia",
    )
    assert n == 27


def test_infoleg_session_count_falla_sin_conteo():
    class _SesionFake:
        def post(self, url, data, **kwargs):
            return _RespuestaBusqueda("sin resultados")

    try:
        politica._infoleg_session_count(
            _SesionFake(), "https://x/buscar", "1", date(2025, 1, 1), date(2026, 1, 1),
        )
        assert False, "debía lanzar ValueError"
    except ValueError as e:
        assert "Conteo no encontrado" in str(e)


def test_fetch_ratio_dnu_usa_ventana_movil_365_dias(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(politica, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(politica.requests, "Session", lambda: _SesionFake())

    llamadas = []

    def fake_count(session, action_url, tipo, desde, hasta, texto=""):
        llamadas.append((tipo, desde, hasta, texto))
        return {"1": 17, "2": 27}[tipo]

    monkeypatch.setattr(politica, "_infoleg_session_count", fake_count)

    def fake_dnus(session, action_url, desde, hasta):
        llamadas.append(("2", desde, hasta, "necesidad y urgencia"))
        return 27, [{"norma": f"Decreto DNU {i} / 2026", "fecha_pub": "2026-01-01"}
                    for i in range(27)]

    monkeypatch.setattr(politica, "_infoleg_contar_dnus", fake_dnus)

    ind = politica.fetch_ratio_dnu()

    assert ind["valor"] == round(27 / 17, 3)
    assert ind["dnu_count"] == 27
    assert ind["leyes_count"] == 17
    assert ind["ventana_dias"] == 365
    assert "periodo" not in ind
    assert len(ind["inventario_dnu"]) == 27
    assert len(llamadas) == 2
    for tipo, desde, hasta, texto in llamadas:
        assert hasta == date(2026, 7, 15)
        assert desde == date(2025, 7, 15)  # 365 días antes, sin resetear en enero
        if tipo == "2":
            assert texto == "necesidad y urgencia"


def test_fetch_ratio_dnu_none_si_cero_leyes(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2026, 7, 15)

    monkeypatch.setattr(politica, "date", FechaFija)

    class _SesionFake:
        def get(self, url, **kwargs):
            return _RespuestaHome()

    monkeypatch.setattr(politica.requests, "Session", lambda: _SesionFake())
    monkeypatch.setattr(politica, "_infoleg_session_count", lambda *a, **k: 0)
    monkeypatch.setattr(politica, "_infoleg_contar_dnus", lambda *a, **k: (0, []))

    assert politica.fetch_ratio_dnu() is None


# ── El DNU es un tipo jurídico, no una frase (ADR-0241) ──────────────────────
# El numerador salía de una búsqueda de TEXTO COMPLETO: todos los decretos que
# dicen «necesidad y urgencia». La frase la dicen también los decretos que
# prorrogan una intervención dispuesta por un DNU, los reglamentarios de una ley
# sancionada por DNU y los vetos que la citan. En la ventana auditada eso contó
# 48 donde había 37, y el ratio publicado fue 1,92 en vez de 1,48.

import json as _json

FIXTURE_DNU = Path(__file__).parent / "fixtures" / "infoleg_dnu_ventana_365.json"


@pytest.fixture(scope="module")
def grilla():
    return _json.loads(FIXTURE_DNU.read_text(encoding="utf-8"))


def test_el_fixture_conserva_las_dos_mitades(grilla):
    """48 filas devueltas, 37 tipificadas: si el fixture pierde las 11 que
    sobran, el test dejaría de probar lo que vino a probar."""
    assert len(grilla["filas"]) == grilla["esperado"]["filas_totales"] == 48
    tipificados = [f for f in grilla["filas"]
                   if politica._RE_INFOLEG_DNU.match(f["norma"])]
    assert len(tipificados) == 37


def test_el_filtro_por_tipo_da_el_ratio_verificado(grilla):
    """37 / 25 = 1,48, que es lo que informó la auditoría."""
    dnus = sum(1 for f in grilla["filas"] if politica._RE_INFOLEG_DNU.match(f["norma"]))
    ratio = round(dnus / grilla["leyes_publicadas"], 3)
    assert abs(ratio - grilla["esperado"]["ratio"]) < 0.005


def test_el_ratio_erroneo_no_puede_volver(grilla):
    """1,92 era contar las 48 coincidencias de texto. El test comprueba las dos
    mitades: que el método viejo daba ese número —o sea que el diagnóstico era
    correcto— y que el nuevo no puede darlo."""
    viejo = round(len(grilla["filas"]) / grilla["leyes_publicadas"], 3)
    assert abs(viejo - grilla["esperado"]["ratio_erroneo"]) < 0.005
    dnus = sum(1 for f in grilla["filas"] if politica._RE_INFOLEG_DNU.match(f["norma"]))
    assert abs(round(dnus / grilla["leyes_publicadas"], 3) - viejo) > 0.3


@pytest.mark.parametrize("norma,es_dnu", [
    ("Decreto DNU 771 / 2026 PODER EJECUTIVO NACIONAL (P.E.N.)", True),
    ("Decreto DNU 2 / 2026 PODER EJECUTIVO NACIONAL", True),
    ("Decreto 710 / 2026 PODER EJECUTIVO NACIONAL (P.E.N.)", False),
    ("Decreto Reglamentario 58 / 2026 PODER EJECUTIVO NACIONAL", False),
    ("Decreto/Ley 1285 / 1958", False),
    ("Ley 27.796", False),
])
def test_el_rotulo_de_la_grilla_decide(norma, es_dnu):
    """Los falsos positivos que la auditoría pidió probar, con sus rótulos
    reales. `Decreto Reglamentario` es el más traicionero: empieza igual."""
    assert bool(politica._RE_INFOLEG_DNU.match(norma)) is es_dnu


def test_los_falsos_positivos_de_la_ventana_estan_identificados(grilla):
    """No alcanza con que el conteo dé bien: hay que poder nombrar cuáles se
    excluyeron. Un filtro que descarta 11 normas sin poder decir cuáles es tan
    poco auditable como el conteo que reemplaza."""
    fuera = [f for f in grilla["filas"] if not politica._RE_INFOLEG_DNU.match(f["norma"])]
    assert len(fuera) == 11
    assert all(f["norma"].lower().startswith("decreto") for f in fuera)
    assert any("VETO" in f["sumario"].upper() for f in fuera), (
        "el veto 651/2025 era uno de los falsos positivos; si no está, el "
        "fixture ya no reproduce el caso auditado")


def test_ambos_lados_usan_publicacion_en_el_boletin(grilla):
    """La convención tiene que ser la misma arriba y abajo de la división.

    Hubo 25 leyes publicadas y 22 sancionadas en la misma ventana: elegir mal
    un lado mueve el ratio de 1,48 a 1,68 sin que nada falle."""
    assert grilla["_ventana"]["dias"] == 365
    dnus = sum(1 for f in grilla["filas"] if politica._RE_INFOLEG_DNU.match(f["norma"]))
    assert abs(round(dnus / 25, 2) - 1.48) < 0.005
    assert abs(round(dnus / 22, 2) - 1.48) > 0.1, (
        "22 son las leyes SANCIONADAS; el ratio no puede mezclar convenciones")


def test_todas_las_filas_caen_dentro_de_la_ventana(grilla):
    d, h = grilla["_ventana"]["desde"], grilla["_ventana"]["hasta"]
    for f in grilla["filas"]:
        assert d <= f["fecha_pub"] <= h, f'{f["norma"]} fuera de la ventana'


def test_un_listado_truncado_hace_fallar(monkeypatch):
    """La grilla devuelve 50 por página y la ventana de 365 días trae 48.

    O sea: el techo estaba a dos normas de distancia y quedarse con la primera
    página no habría fallado, habría contado 50. Ahora pagina, y si el total no
    cierra, revienta."""
    from datetime import date

    class _Resp:
        status_code = 200
        text = "Cantidad de Normas Encontradas: 111 en 3 páginas."

        def raise_for_status(self):
            pass

    monkeypatch.setattr(politica, "_parsear_listado_infoleg", lambda html: [])

    class _Ses:
        def post(self, *a, **k):
            return _Resp()

    with pytest.raises(ValueError, match="truncado"):
        politica._infoleg_listado_completo(_Ses(), "http://x", "2",
                                           date(2025, 1, 1), date(2026, 1, 1))
