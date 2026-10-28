# -*- coding: utf-8 -*-
"""Revisión del cinturón de gestión del 28-oct-2026 (ADR-0405, 0406 y 0407).

- ADR-0405: los piquetes pasan de la Ciudad al total nacional de Diagnóstico
  Político. ADR-0408 deja eso sin efecto: vuelven a la Ciudad, y los totales
  nacionales verificados quedan en el registro como contexto.
- ADR-0406: el RIGI toma la escala de concesiones/privatizaciones.
- ADR-0407: Corredores Viales sale de la cartera de privatizaciones porque la
  red vial ya la mide concesiones_infraestructura.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import descargar_series as ds  # noqa: E402
import gestion  # noqa: E402
import itcg  # noqa: E402
import procedencia_anclas  # noqa: E402

DP = json.loads((RAIZ / "data/gestion/dp_piquetes.json").read_text(encoding="utf-8-sig"))

# Verificados uno por uno contra su fuente el 28-oct-2026 (ADR-0405).
NACIONAL = {"2014": 6805, "2016": 6491, "2017": 5221, "2018": 5857, "2019": 5430,
            "2021": 6658, "2022": 9778, "2023": 8239, "2024": 5996, "2025": 3893}


# ── ADR-0405 ────────────────────────────────────────────────────────────────

def test_los_totales_nacionales_son_los_verificados_y_tienen_fuente():
    assert DP["nacional"] == NACIONAL
    for anio in NACIONAL:
        f = DP["fuentes_nacional"][anio]
        assert f["url"].startswith("https://"), anio
        assert f"{NACIONAL[anio]:,}".replace(",", ".") in f["cita"] or str(NACIONAL[anio]) in f["cita"], anio


def test_la_clave_caba_es_la_que_puntua():
    assert DP["caba"] == {"2023": 931, "2024": 440, "2025": 240}
    assert DP["_meta"]["puntua"].startswith("caba") and "0408" in DP["_meta"]["puntua"]


def test_la_tarjeta_puntua_la_ciudad_y_no_el_pais(monkeypatch):
    """ADR-0408: vuelve a la Ciudad (ADR-0405 lo había pasado al país)."""
    monkeypatch.setattr(gestion.requests, "get", lambda *a, **k: SimpleNamespace(
        text="", raise_for_status=lambda: None))
    card = gestion.fetch_protocolo_antipiquetes()
    assert card["valor"] == round((1 - 240 / 931) * 100, 1) == 74.2
    assert card["componentes"] == {"caba_2023": 931, "caba_2025": 240}
    assert "Ciudad de Buenos Aires" in card["unidad"] and "país" not in card["unidad"]
    assert "consultora privada" in card["fuente"]


def test_la_serie_reproduce_la_tarjeta(monkeypatch):
    monkeypatch.setattr(gestion.requests, "get", lambda *a, **k: SimpleNamespace(
        text="", raise_for_status=lambda: None))
    assert ds.fetch_protocolo_serie()[-1][1] == gestion.fetch_protocolo_antipiquetes()["valor"]


def test_el_respaldo_manual_esta_en_el_mismo_universo():
    m = json.loads((RAIZ / "data/gestion/manuales.json").read_text(encoding="utf-8-sig"))
    fb = m["protocolo_antipiquetes"]
    assert fb["valor"] == 74.2 and "Ciudad de Buenos Aires" in fb["unidad"]
    assert "ADR-" not in fb["notas"]   # las notas del respaldo se publican (gate G6)


def test_las_bandas_de_piquetes_no_se_movieron_y_se_declaran_convencion():
    assert itcg.BANDAS_ITCG["protocolo_antipiquetes"] == [
        (75.0, itcg.INF, 100), (50.0, 75.0, 85), (25.0, 50.0, 65),
        (0.0, 25.0, 40), (-itcg.INF, 0.0, 10)]
    cat, glosa = procedencia_anclas.PROCEDENCIA["protocolo_antipiquetes"]
    assert cat == "convencion" and "0408" in glosa


def test_la_web_dice_ciudad_y_no_pais():
    lib = RAIZ / "web/src/lib"
    datos = (lib / "datos.ts").read_text(encoding="utf-8")
    assert 'protocolo_antipiquetes: "Reducción de cortes de calle en la Ciudad"' in datos
    for nombre in ("datos.ts", "descripciones.ts", "formulas.ts"):
        texto = (lib / nombre).read_text(encoding="utf-8")
        i = texto.find("protocolo_antipiquetes:")
        tramo = texto[i:i + 600]
        assert "en todo el país" not in tramo and "en el pa" not in tramo, nombre


def test_la_ficha_declara_fuente_privada_y_estado_judicial_vigente():
    fichas = (RAIZ / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
    i = fichas.find("  protocolo_antipiquetes: {")
    tramo = fichas[i:fichas.find("\n  },", i)]
    assert "consultora privada" in tramo
    assert "31 de marzo de 2026" in tramo and "Corte Suprema" in tramo
    assert 'adr: "0408"' in tramo


# ── ADR-0406 ────────────────────────────────────────────────────────────────

def test_el_rigi_usa_exactamente_la_escala_de_concesiones():
    b = itcg.BANDAS_ITCG
    assert b["rigi_inversiones"] == b["concesiones_infraestructura"]
    cat, glosa = procedencia_anclas.PROCEDENCIA["rigi_inversiones"]
    assert cat == "convencion" and "0406" in glosa and "sin calibrar" in glosa


def test_la_ficha_del_rigi_dice_que_mide_la_demora():
    fichas = (RAIZ / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
    i = fichas.find("  rigi_inversiones: {")
    tramo = fichas[i:fichas.find("\n  },", i)]
    assert "demora en aprobar" in tramo
    assert "[[15, 10], [25, 40], [45, 65], [65, 85], [75, 100]]" in tramo


# ── ADR-0407 ────────────────────────────────────────────────────────────────

def test_corredores_viales_fuera_de_la_cartera():
    vivo = json.loads(gestion.PRIVATIZACIONES_PATH.read_text(encoding="utf-8-sig"))
    fechas = json.loads(gestion.PRIVATIZACIONES_FECHAS_PATH.read_text(encoding="utf-8-sig"))
    assert "Corredores Viales" not in vivo["empresas"]
    assert "Corredores Viales" not in fechas["empresas"]
    assert "Corredores Viales" not in gestion.PRIVATIZACIONES_TERMINOS
    assert vivo["fuera_de_cartera"]["Corredores Viales"]["adr"] == "0407"
    assert len(vivo["empresas"]) == 8


def test_la_serie_reproduce_la_tarjeta_sin_corredores(monkeypatch):
    monkeypatch.setattr(gestion, "detectar_novedades_privatizaciones",
                        lambda: {"pendientes": {}, "_meta": {}})
    card = gestion.fetch_privatizaciones()
    assert "Corredores Viales" not in card["componentes"]
    assert ds.fetch_privatizaciones_serie()[-1][1] == card["valor"]


def test_las_fichas_ya_no_declaran_doble_conteo():
    fichas = (RAIZ / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
    for clave in ("privatizaciones", "concesiones_infraestructura"):
        i = fichas.find(f"  {clave}: {{")
        tramo = fichas[i:fichas.find("\n  },", i)]
        linea = next(l for l in tramo.split("\n") if l.strip().startswith("dobleUso:"))
        assert "No comparte hechos" in linea, clave
