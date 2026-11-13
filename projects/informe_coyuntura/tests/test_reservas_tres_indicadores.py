"""ADR-0428: el cinturón macro mide las reservas con tres indicadores.

1. `reservas_brutas`: reservas internacionales del BCRA (API, variable 1), con
   cortes en la historia previa al mandato (dic-2017 a nov-2023, ADR-0404).
2. `reservas_bcra` («Reservas netas»): la medición estricta de la planilla SDDS
   (I.A + II.1 + II.2 + II.3), la que publican las consultoras. Ya no suma los
   depósitos del Tesoro ni el tramo de II.1 de la fórmula CIGOB (ADR-0286).
3. `meta_reservas_fmi`: avance de la acumulación de netas estrictas contra la
   meta del programa con el FMI, prorrateada al mes.

Las tres se reparten en partes iguales el 5,44 % que pesaban las netas.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series  # noqa: E402
import itcm  # noqa: E402
import macro  # noqa: E402
import meta_reservas_fmi as mrf  # noqa: E402
import parametrica  # noqa: E402

P_VERDE, P_AMARILLO, P_NARANJA = parametrica.PUNTAJES_DE_CORTE
RESERVAS = ("reservas_brutas", "reservas_bcra", "meta_reservas_fmi")

# Netas estrictas de la planilla SDDS, cierre de mes (millones de USD).
NETAS = {"2024-12": -11006.0, "2025-12": -2712.0, "2026-01": -4313.0,
         "2026-09": 7465.0}


# ── Tabla de metas ──────────────────────────────────────────────────────────

def _por_fecha():
    return {m["fecha_meta"]: m for m in mrf.cargar_metas()}


def test_la_tabla_declara_la_meta_de_dic_2026_y_la_indicativa_de_jun_2027():
    metas = _por_fecha()
    dic26 = metas["2026-12-31"]
    assert dic26["base"] == "2025-12-31"
    assert dic26["acumulacion_meta"] == 8000
    assert dic26["tipo"] == "criterio de desempeño"
    jun27 = metas["2027-06-30"]
    assert jun27["base"] == "2026-12-31"
    assert jun27["acumulacion_meta"] == 4500
    assert jun27["tipo"] == "indicativa"
    for m in metas.values():
        assert m["fuente"] and m["revision"]
        assert "oficial" in m      # el campo existe aunque todavía no haya dato


def _escribir(tmp_path, metas):
    p = tmp_path / "metas.json"
    p.write_text(json.dumps({"metas": metas}), encoding="utf-8")
    return p


META_OK = {"base": "2025-12-31", "fecha_meta": "2026-12-31", "acumulacion_meta": 8000,
           "tipo": "criterio de desempeño", "fuente": "FMI", "revision": "2ª", "oficial": None}


def test_la_tabla_rechaza_una_meta_sin_fuente(tmp_path):
    with pytest.raises(ValueError, match="fuente"):
        mrf.cargar_metas(_escribir(tmp_path, [{**META_OK, "fuente": ""}]))


def test_la_tabla_rechaza_ventanas_superpuestas(tmp_path):
    otra = {**META_OK, "base": "2026-06-30", "fecha_meta": "2027-06-30"}
    with pytest.raises(ValueError, match="superpone"):
        mrf.cargar_metas(_escribir(tmp_path, [META_OK, otra]))


def test_la_tabla_rechaza_un_oficial_sin_acumulacion(tmp_path):
    with pytest.raises(ValueError, match="oficial"):
        mrf.cargar_metas(_escribir(tmp_path, [{**META_OK, "oficial": {"fuente": "FMI"}}]))


@pytest.mark.parametrize("ym,fecha_meta", [
    ("2025-12", None), ("2026-01", "2026-12-31"), ("2026-12", "2026-12-31"),
    ("2027-01", "2027-06-30"), ("2027-06", "2027-06-30"), ("2027-07", None),
])
def test_cada_mes_se_mide_contra_la_meta_de_su_ventana(ym, fecha_meta):
    m = mrf.meta_vigente(mrf.cargar_metas(), ym)
    assert (m and m["fecha_meta"]) == fecha_meta


# ── Prorrateo ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("fecha_meta,ym,esperado", [
    ("2026-12-31", "2026-01", 8000 / 12),
    ("2026-12-31", "2026-09", 6000.0),
    ("2026-12-31", "2026-12", 8000.0),
    ("2027-06-30", "2027-03", 2250.0),
])
def test_la_meta_se_prorratea_por_meses_transcurridos(fecha_meta, ym, esperado):
    meta = _por_fecha()[fecha_meta]
    assert mrf.meta_prorrateada(meta, ym) == pytest.approx(esperado)


def test_septiembre_2026_avanza_170_por_ciento_de_la_meta_prorrateada():
    r = mrf.avance(mrf.cargar_metas(), "2026-09", NETAS)
    assert r["acumulado"] == 10177.0                     # 7.465 − (−2.712)
    assert r["meta_prorrateada"] == pytest.approx(6000.0)  # 8.000 × 9/12
    assert r["valor"] == 169.6
    assert r["origen"] == "estimacion"
    assert r["fecha_meta"] == "2026-12-31"


def test_enero_no_sale_rojo_por_construccion():
    """Con la meta entera de denominador, un enero que acumula al ritmo exacto
    del año daría 8 %: rojo sólo por estar en enero."""
    netas = {"2025-12": -2712.0, "2026-01": -2712.0 + 700.0}
    r = mrf.avance(mrf.cargar_metas(), "2026-01", netas)
    assert r["valor"] == 105.0
    p = parametrica.puntaje_desde_anclas(r["valor"], itcm.ANCLAS_ITCM["meta_reservas_fmi"])
    assert parametrica.color_de_puntaje(p) == "verde"


def test_sin_el_dato_de_la_base_no_hay_avance():
    assert mrf.avance(mrf.cargar_metas(), "2026-09", {"2026-09": 7465.0}) is None


def test_el_dato_oficial_gana_sobre_la_estimacion_en_la_fecha_de_prueba(tmp_path):
    oficial = {"acumulacion": 9000, "fuente": "FMI, 3ª revisión"}
    metas = mrf.cargar_metas(_escribir(tmp_path, [{**META_OK, "oficial": oficial}]))
    netas = {"2025-12": -2712.0, "2026-11": 4000.0, "2026-12": 3000.0}
    dic = mrf.avance(metas, "2026-12", netas)
    assert dic["origen"] == "oficial" and dic["acumulado"] == 9000
    assert dic["valor"] == 112.5
    nov = mrf.avance(metas, "2026-11", netas)          # antes de la fecha de prueba
    assert nov["origen"] == "estimacion" and nov["acumulado"] == 6712.0


def test_la_serie_arranca_en_el_primer_mes_con_meta():
    serie = mrf.serie(mrf.cargar_metas(), NETAS)
    assert [ym for ym, _ in serie] == ["2026-01", "2026-09"]
    assert serie[-1][1]["valor"] == 169.6


# ── Cortes de color de la meta ──────────────────────────────────────────────

@pytest.mark.parametrize("pct,color", [
    (170.0, "verde"), (100.0, "verde"),
    (99.5, "amarillo"), (75.0, "amarillo"),
    (74.5, "naranja"), (50.0, "naranja"),
    (49.5, "rojo"), (0.0, "rojo"), (-40.0, "rojo"),
])
def test_cortes_de_color_de_la_meta_en_sus_bordes(pct, color):
    p = parametrica.puntaje_desde_anclas(pct, itcm.ANCLAS_ITCM["meta_reservas_fmi"])
    assert parametrica.color_de_puntaje(p) == color


def test_los_cortes_de_la_meta_caen_en_los_bordes_del_semaforo():
    anclas = dict(itcm.ANCLAS_ITCM["meta_reservas_fmi"])
    assert anclas[100.0] == P_VERDE
    assert anclas[75.0] == P_AMARILLO
    assert anclas[50.0] == P_NARANJA
    tramos = parametrica.umbrales_en_unidad("meta_reservas_fmi", itcm.ESCALA_ITCM)
    assert [(t["color"], t["desde"], t["hasta"]) for t in tramos] == [
        ("rojo", None, 50.0), ("naranja", 50.0, 75.0),
        ("amarillo", 75.0, 100.0), ("verde", 100.0, None)]


# ── Reservas brutas ─────────────────────────────────────────────────────────

def test_brutas_cortan_en_desvios_de_la_historia_previa():
    m, s = itcm.MEDIA_RESERVAS_BRUTAS, itcm.DESVIO_RESERVAS_BRUTAS
    assert (m, s) == (45373.1, 11374.9)      # dic-2017 a nov-2023, 72 cierres de mes
    cortes = sorted({lo for lo, _, _ in itcm.BANDAS_ITCM["reservas_brutas"]} - {-itcm.INF})
    assert cortes == [round(m + k * s) for k in (-2, -1, 0, 1, 2)]
    # más reservas, menos tensión
    f = lambda v: itcm.ESCALA_ITCM.puntaje(v, "reservas_brutas")
    valores = [f(v) for v in range(15000, 80001, 1000)]
    assert valores == sorted(valores)
    assert f(15000) == 10 and f(80000) == 100


def test_brutas_card_es_el_ultimo_dato_diario(monkeypatch):
    monkeypatch.setattr(macro, "_bcra_ultimo", lambda v: {"valor": 49586.0, "fecha": "2026-11-11"}
                        if v == macro.BCRA_RESERVAS_ID else pytest.fail("otra variable"))
    r = macro.fetch_reservas_brutas()
    assert r["valor"] == 49586.0 and r["fecha_dato"] == "2026-11-11"


def test_brutas_serie_es_el_ultimo_dato_de_cada_mes(monkeypatch):
    monkeypatch.setattr(macro, "_bcra_fin_de_mes", lambda v, meses: {
        "2026-09": 46092.0, "2026-10": 48565.0, "2026-11": 49586.0})
    serie = descargar_series.fetch_reservas_brutas_serie(meses=2)
    assert serie == [["2026-10-01", 48565.0], ["2026-11-01", 49586.0]]


# ── Reservas netas: la medición estricta ────────────────────────────────────

SDDS = {"netas": -1000.0, "brutas": 10000.0, "prestamos_dep": -4000.0,
        "swaps": -3000.0, "repos": -4000.0, "bopreal_12m": -200.0, "fecha": "31/05/26"}


def test_la_card_de_netas_publica_la_medicion_estricta(monkeypatch):
    monkeypatch.setattr(macro, "_reservas_netas_sdds", lambda: dict(SDDS))
    monkeypatch.setattr(macro, "_bcra_ultimo", lambda _v: {"valor": 10000.0, "fecha": "2026-05-31"})
    monkeypatch.setattr(macro, "_tesoro_deposits_usd", lambda mes=None: 300.0)
    r = macro.fetch_reservas_netas()
    assert r["valor"] == -1000.0
    assert r["metodo"] == "sdds_estricto"
    # los componentes siguen en el snapshot
    assert r["netas_sdds_estricto"] == -1000.0
    assert (r["drenaje_prestamos_dep"], r["drenaje_swaps"], r["drenaje_repos"]) == (-4000, -3000, -4000)
    assert r["depositos_tesoro"] == 300.0 and r["bopreal_12m"] == 200.0
    assert r["estimacion_cigob"] == -500.0


def test_la_card_de_netas_no_depende_del_tesoro(monkeypatch):
    monkeypatch.setattr(macro, "_reservas_netas_sdds", lambda: dict(SDDS))
    monkeypatch.setattr(macro, "_bcra_ultimo", lambda _v: {"valor": 10000.0, "fecha": "2026-05-31"})
    monkeypatch.setattr(macro, "_tesoro_deposits_usd",
                        lambda mes=None: (_ for _ in ()).throw(ValueError("sin balance")))
    r = macro.fetch_reservas_netas()
    assert r["valor"] == -1000.0
    assert r["depositos_tesoro"] is None and r["estimacion_cigob"] is None


def test_la_serie_de_netas_es_la_estricta(monkeypatch):
    descargar_series._sdds_por_mes.cache_clear()
    monkeypatch.setattr(descargar_series.requests, "get", lambda *a, **kw:
                        SimpleNamespace(status_code=200, content=b"x" * 50001))
    monkeypatch.setattr(macro, "_parse_sdds_content", lambda _c: {
        "fecha": "31/07/26", "netas": 1000.0, "bopreal_12m": -200.0})
    try:
        assert descargar_series.fetch_reservas_netas_serie(meses=1) == [["2026-07-01", 1000.0]]
    finally:
        descargar_series._sdds_por_mes.cache_clear()


# ── Meta: el colector ───────────────────────────────────────────────────────

def test_el_colector_mide_la_meta_con_las_netas_estrictas_del_mes_y_de_la_base(monkeypatch):
    monkeypatch.setattr(macro, "_reservas_netas_sdds", lambda: {**SDDS, "netas": 7465.0,
                                                                "fecha": "30/09/26"})
    monkeypatch.setattr(macro, "_netas_estrictas_del_mes",
                        lambda ym: {"2025-12": -2712.0}[ym])
    r = macro.fetch_meta_reservas_fmi()
    assert r["valor"] == 169.6
    assert r["fecha_dato"] == "2026-09-30"
    assert r["acumulado"] == 10177.0 and r["meta_prorrateada"] == 6000.0
    assert r["base"] == "2025-12-31" and r["fecha_meta"] == "2026-12-31"


# ── Pesos ───────────────────────────────────────────────────────────────────

def test_las_tres_reservas_se_reparten_el_peso_de_las_netas():
    dim = itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]
    assert dim["peso"] == pytest.approx(0.3144)            # la dimensión no se mueve
    for k in RESERVAS:
        assert dim["peso"] * dim["indicadores"][k] == pytest.approx(0.0544 / 3)
    assert sum(dim["indicadores"].values()) == pytest.approx(1.0)
    for k in ("ipc_total", "rem_ipc_12m", "desequilibrio_monetario"):   # el resto, igual
        assert dim["peso"] * dim["indicadores"][k] == pytest.approx(
            {"ipc_total": 0.156, "rem_ipc_12m": 0.052, "desequilibrio_monetario": 0.052}[k])
