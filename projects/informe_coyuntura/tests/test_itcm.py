"""Tests unitarios del módulo ITCM (sin red).

Pinean: las tablas de bandas del doc "Paramétrica Macro" (CIGOB, may-2026),
la convención de bordes (low exclusivo, high inclusivo), la ponderación por
dimensiones, el mecanismo de ajuste manual y la renormalización ante faltantes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm

# Valores del ejemplo del documento (mayo 2026). Con tablas puras (sin los
# ajustes discrecionales del doc): D1=50, D2=82, D3=52.5, D4=100 → ITCM=67.6.
EJEMPLO_DOC = {
    "ipc_total": 2.58,            # banda 2-3 → 65
    "rem_ipc_12m": 24.2,          # banda 20-30 → 35
    "recaudacion": 8.27,          # banda 5-10 → 80
    "saldo_comercial_12m": 17125, # banda >15000 → 85
    "reservas_bcra": 48113,       # banda 40-50k → 70
    "badlar": 20.62,              # banda 15-25 → 35
    "emae_ia": 5.48,              # banda >5 → 100
}


def test_itcm_reproduce_ejemplo_doc():
    r = itcm.calcular_itcm(EJEMPLO_DOC)
    dims = r["dimensiones"]
    assert dims["estabilidad_monetaria"]["puntaje"] == 50.0
    assert dims["viabilidad_fiscal_comercial"]["puntaje"] == 82.0
    assert dims["financiamiento"]["puntaje"] == 52.5
    assert dims["actividad"]["puntaje"] == 100.0
    assert r["valor"] == 67.6
    assert r["banda"] == "moderadamente_aflojado"
    assert itcm.tension_de_itcm(r["valor"]) == 3.2
    assert r["ajustes_aplicados"] == []


def test_pesos_efectivos_reconcilian_con_itcm():
    """sum(puntaje × peso_efectivo) ≈ ITCM y los pesos efectivos suman 1."""
    r = itcm.calcular_itcm(EJEMPLO_DOC)
    pares = [
        (info["puntaje_aplicado"], info["peso_efectivo"])
        for dim in r["dimensiones"].values()
        for info in dim["indicadores"].values()
    ]
    assert abs(sum(p * w for p, w in pares) - r["valor"]) <= 0.1
    assert abs(sum(w for _, w in pares) - 1.0) <= 0.001


def test_bordes_de_banda():
    """Convención: low exclusivo, high inclusivo."""
    b = itcm.BANDAS_ITCM
    assert itcm.puntaje_banda(1.0, b["ipc_total"]) == 100
    assert itcm.puntaje_banda(2.0, b["ipc_total"]) == 85
    assert itcm.puntaje_banda(3.0, b["ipc_total"]) == 65
    assert itcm.puntaje_banda(5.0, b["ipc_total"]) == 40
    assert itcm.puntaje_banda(5.01, b["ipc_total"]) == 10
    assert itcm.puntaje_banda(5.0, b["emae_ia"]) == 80     # >5 estricto para 100
    assert itcm.puntaje_banda(-5.0, b["emae_ia"]) == 5      # high inclusivo: -5 cae abajo
    assert itcm.puntaje_banda(-4.99, b["emae_ia"]) == 20
    assert itcm.puntaje_banda(50000, b["reservas_bcra"]) == 70
    assert itcm.puntaje_banda(50001, b["reservas_bcra"]) == 85
    assert itcm.puntaje_banda(-5000, b["saldo_comercial_12m"]) == 30
    assert itcm.puntaje_banda(0, b["saldo_comercial_12m"]) == 50
    assert itcm.puntaje_banda(25.0, b["badlar"]) == 35
    assert itcm.puntaje_banda(30.0, b["rem_ipc_12m"]) == 35
    assert itcm.puntaje_banda(10.0, b["recaudacion"]) == 80


def test_ajuste_manual_aplicado():
    """Override del analista: reproduce el juicio del doc (saldo 85 → 60)."""
    ajustes = {"saldo_comercial_12m": {
        "puntaje": 60, "justificacion": "Superávit por contracción de importaciones"}}
    r = itcm.calcular_itcm(EJEMPLO_DOC, ajustes)
    assert r["dimensiones"]["viabilidad_fiscal_comercial"]["puntaje"] == 72.0
    assert r["valor"] == 64.6
    assert len(r["ajustes_aplicados"]) == 1
    aj = r["ajustes_aplicados"][0]
    assert aj["indicador"] == "saldo_comercial_12m" and aj["de"] == 85 and aj["a"] == 60
    ind = r["dimensiones"]["viabilidad_fiscal_comercial"]["indicadores"]["saldo_comercial_12m"]
    assert ind["puntaje_banda"] == 85 and ind["puntaje_aplicado"] == 60


def test_ajuste_vencido_no_se_aplica(tmp_path):
    archivo = tmp_path / "ajustes.json"
    archivo.write_text(json.dumps({
        "saldo_comercial_12m": {"puntaje": 60, "justificacion": "x", "vigente_hasta": "2026-04"},
        "badlar":              {"puntaje": 50, "justificacion": "y", "vigente_hasta": "2026-12"},
    }), encoding="utf-8")
    vigentes = itcm.cargar_ajustes(archivo, "2026-06")
    assert "saldo_comercial_12m" not in vigentes   # vencido abril < junio
    assert "badlar" in vigentes
    assert itcm.cargar_ajustes(tmp_path / "no_existe.json", "2026-06") == {}


def test_renormalizacion_indicador_faltante():
    """Sin REM, la dimensión monetaria queda solo con el IPC."""
    valores = dict(EJEMPLO_DOC, rem_ipc_12m=None)
    r = itcm.calcular_itcm(valores)
    assert r["dimensiones"]["estabilidad_monetaria"]["puntaje"] == 65.0
    # ITCM = 0.35×65 + 0.30×82 + 0.20×52.5 + 0.15×100 = 72.85
    assert abs(r["valor"] - 72.85) <= 0.05


def test_renormalizacion_dimension_faltante():
    """Sin EMAE, la dimensión actividad desaparece y los pesos se renormalizan."""
    valores = dict(EJEMPLO_DOC, emae_ia=None)
    r = itcm.calcular_itcm(valores)
    assert "actividad" not in r["dimensiones"]
    esperado = (0.35 * 50 + 0.30 * 82 + 0.20 * 52.5) / 0.85
    assert abs(r["valor"] - esperado) <= 0.1


def test_sin_indicadores_devuelve_none():
    assert itcm.calcular_itcm({}) is None
    assert itcm.calcular_itcm({"tcrm": 79.8}) is None  # contexto no integra el índice


def test_contexto_no_altera_el_indice():
    con_contexto = dict(EJEMPLO_DOC, tcrm=79.8, prestamos_privados=2.1,
                        base_monetaria=0.7, tc_mayorista=-0.3)
    assert itcm.calcular_itcm(con_contexto)["valor"] == itcm.calcular_itcm(EJEMPLO_DOC)["valor"]


def test_ajuste_automatico_saldo_por_contraccion():
    """Superávit con importaciones cayendo más de lo que crecen las expo →
    ajuste a 60 (caso del doc: el superávit 2024/25 'por contracción')."""
    ind = {"valor": 17125, "expo_var_ia": 2.0, "impo_var_ia": -15.0,
           "expo_delta_12m": 1500, "impo_delta_12m": -9000}
    aj = itcm.ajuste_automatico_saldo(ind)
    assert aj is not None and aj["puntaje"] == 60 and aj["origen"] == "automatico"
    assert "contracción de importaciones" in aj["justificacion"]
    r = itcm.calcular_itcm(dict(EJEMPLO_DOC), {"saldo_comercial_12m": aj})
    assert r["dimensiones"]["viabilidad_fiscal_comercial"]["puntaje"] == 72.0
    assert r["ajustes_aplicados"][0]["origen"] == "automatico"


def test_ajuste_automatico_saldo_no_aplica():
    """No opina cuando: las impo crecen (superávit genuino), la caída de impo
    no domina, no hay superávit relevante, o faltan los campos de composición."""
    # impo creciendo (situación jun-2026 real)
    assert itcm.ajuste_automatico_saldo(
        {"valor": 18322, "expo_var_ia": 14.1, "impo_var_ia": 10.6,
         "expo_delta_12m": 11451, "impo_delta_12m": 7125}) is None
    # impo caen pero la mejora viene más de las expo
    assert itcm.ajuste_automatico_saldo(
        {"valor": 16000, "expo_var_ia": 12.0, "impo_var_ia": -1.0,
         "expo_delta_12m": 9000, "impo_delta_12m": -500}) is None
    # déficit / sin superávit relevante
    assert itcm.ajuste_automatico_saldo(
        {"valor": -2000, "expo_var_ia": 0.0, "impo_var_ia": -20.0,
         "expo_delta_12m": 0, "impo_delta_12m": -8000}) is None
    # banda ya ≤ 60: el ajuste no agrega nada
    assert itcm.ajuste_automatico_saldo(
        {"valor": 8000, "expo_var_ia": 0.0, "impo_var_ia": -20.0,
         "expo_delta_12m": 0, "impo_delta_12m": -8000}) is None
    # sin composición (fallback a la serie de saldo directa)
    assert itcm.ajuste_automatico_saldo({"valor": 17125}) is None


def test_interpretacion_bandas():
    assert itcm.banda_interpretacion(15) == "severamente_apretado"
    assert itcm.banda_interpretacion(20) == "severamente_apretado"
    assert itcm.banda_interpretacion(40) == "apretado"
    assert itcm.banda_interpretacion(61.45) == "moderadamente_aflojado"
    assert itcm.banda_interpretacion(95) == "aflojado"
