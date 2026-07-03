"""Tests unitarios del módulo ITCM (sin red).

Pinean: las tablas de bandas de la Paramétrica CIGOB con las revisiones de los
docs "260602 (2)" y "260626 aportes" (REM por equivalente mensual, recaudación
i.a. real, reservas NETAS, Índice de Capacidad Prestable), la convención de
bordes (low exclusivo, high inclusivo — vigente para las etiquetas), el
PUNTAJE POR INTERPOLACIÓN entre anclas (ADR-0021), la ponderación por
dimensiones, el mecanismo de ajuste manual y la renormalización ante
faltantes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm

# Fixture mayo 2026 con la metodología REVISADA. Los valores de rem_ipc_12m,
# reservas_bcra, recaudacion, idc, idm y tcrm son los que el colector alimenta.
# Desde el ADR-0021 el puntaje es INTERPOLADO entre las anclas de las bandas
# (banda de referencia entre paréntesis):
#   * rem_ipc_12m  = equivalente MENSUAL del REM (raíz 12). 1,76% → 79,8 (banda 85).
#   * recaudacion  = variación i.a. REAL (deflactada). 1,82% → 57,3 (banda 60).
#   * reservas_bcra= NETAS (Machado). 1.881M → 25,0 (banda 30).
#   * idc          = Índice de Capacidad Prestable. 1,012 → 70,0 (banda 60).
#   * idm          = Índice de Desequilibrio Monetario. 4,5 pp → 51,7 (banda 60).
#   * tcrm         = ITCRM (base 2015=100). 84,3 → 45,7 (banda 35).
#   * iai          = inversión física (% i.a.). −4,2 → 42,5 (banda 35).
#   * icip         = capitalización digital (% i.a.). 8,2 → 73,1 (banda 80).
#   * saldo/emae quedan planos más allá de la última ancla (85 y 100).
# Dimensiones: estab=64,9 fiscal=68,4 financ=47,5 actividad=100
# competitividad=45,7 inversión=54,7 → ITCM=63,5.
EJEMPLO = {
    "ipc_total": 2.58,             # interpolado 63,7 (banda 65)
    "rem_ipc_12m": 1.76,           # equiv. mensual: 79,8 (banda 85)
    "idm": 4.5,                    # gap i.a. real: 51,7 (banda 60)
    "recaudacion": 1.82,           # i.a. real: 57,3 (banda 60)
    "saldo_comercial_12m": 17125,  # más allá de la última ancla → 85 plano
    "reservas_bcra": 1881,         # netas: 25,0 (banda 30)
    "idc": 1.012,                  # 70,0 (banda 60)
    "emae_ia": 5.48,               # más allá de la última ancla → 100 plano
    "tcrm": 84.3,                  # ITCRM: 45,7 (banda 35)
    "iai": -4.2,                   # inversión física: 42,5 (banda 35)
    "icip": 8.2,                   # capitalización digital: 73,1 (banda 80)
}


def test_itcm_reproduce_ejemplo():
    r = itcm.calcular_itcm(EJEMPLO)
    dims = r["dimensiones"]
    assert dims["estabilidad_monetaria"]["puntaje"] == 64.9
    assert dims["viabilidad_fiscal_comercial"]["puntaje"] == 68.4
    assert dims["financiamiento"]["puntaje"] == 47.5
    assert dims["actividad"]["puntaje"] == 100.0
    assert dims["competitividad_externa"]["puntaje"] == 45.7
    assert dims["inversion"]["puntaje"] == 54.7
    assert r["valor"] == 63.5
    assert r["banda"] == "moderadamente_aflojado"
    assert itcm.tension_de_itcm(r["valor"]) == 3.6
    assert r["ajustes_aplicados"] == []


def test_puntaje_interpolado():
    """ADR-0021: lineal entre anclas (punto medio de bandas finitas, borde de
    las abiertas), plano en los extremos; en cada ancla reproduce el puntaje
    de su banda."""
    import parametrica
    b = itcm.BANDAS_ITCM["ipc_total"]   # ≤1→100 · 1-2→85 · 2-3→65 · 3-5→35 · >5→10
    assert parametrica.puntaje_interpolado(0.5, b) == 100.0   # antes de la 1ª ancla
    assert parametrica.puntaje_interpolado(1.0, b) == 100.0   # ancla (borde abierto)
    assert parametrica.puntaje_interpolado(1.5, b) == 85.0    # ancla (punto medio)
    assert parametrica.puntaje_interpolado(2.0, b) == 75.0    # mitad entre 85 y 65
    assert parametrica.puntaje_interpolado(2.5, b) == 65.0    # ancla
    assert parametrica.puntaje_interpolado(5.0, b) == 10.0    # última ancla
    assert parametrica.puntaje_interpolado(9.0, b) == 10.0    # plano más allá


def test_pesos_efectivos_reconcilian_con_itcm():
    """sum(puntaje × peso_efectivo) ≈ ITCM y los pesos efectivos suman 1."""
    r = itcm.calcular_itcm(EJEMPLO)
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
    assert itcm.puntaje_banda(5.01, b["ipc_total"]) == 10
    assert itcm.puntaje_banda(5.0, b["emae_ia"]) == 80     # >5 estricto para 100
    assert itcm.puntaje_banda(-5.0, b["emae_ia"]) == 5
    assert itcm.puntaje_banda(10.0, b["recaudacion"]) == 80
    # REM: la banda opera sobre el EQUIVALENTE MENSUAL (misma escala que el IPC)
    assert itcm.puntaje_banda(1.76, b["rem_ipc_12m"]) == 85
    assert itcm.puntaje_banda(2.0, b["rem_ipc_12m"]) == 85
    assert itcm.puntaje_banda(2.01, b["rem_ipc_12m"]) == 65
    # Reservas NETAS
    assert itcm.puntaje_banda(20000, b["reservas_bcra"]) == 85   # high inclusivo
    assert itcm.puntaje_banda(20001, b["reservas_bcra"]) == 100
    assert itcm.puntaje_banda(3000, b["reservas_bcra"]) == 30
    assert itcm.puntaje_banda(0, b["reservas_bcra"]) == 10       # 0 → negativas/crisis
    assert itcm.puntaje_banda(0.01, b["reservas_bcra"]) == 30
    # Índice de Capacidad Prestable (semáforo)
    assert itcm.puntaje_banda(1.02, b["idc"]) == 60              # amarillo (high inclusivo)
    assert itcm.puntaje_banda(1.0201, b["idc"]) == 85           # verde
    assert itcm.puntaje_banda(0.98, b["idc"]) == 35             # rojo (high inclusivo)
    assert itcm.puntaje_banda(0.9801, b["idc"]) == 60          # amarillo
    assert itcm.puntaje_banda(1.05, b["idc"]) == 100
    assert itcm.puntaje_banda(0.90, b["idc"]) == 10
    # IDM: gap i.a. real (negativo = remonetización, baja tensión, score alto)
    assert itcm.puntaje_banda(-2.0, b["idm"]) == 100            # high inclusivo
    assert itcm.puntaje_banda(-1.99, b["idm"]) == 85
    assert itcm.puntaje_banda(2.0, b["idm"]) == 85
    assert itcm.puntaje_banda(2.01, b["idm"]) == 60
    assert itcm.puntaje_banda(8.01, b["idm"]) == 10            # excedente fuerte
    # TCRM: apreciación (nivel bajo) = más tensión
    assert itcm.puntaje_banda(110.1, b["tcrm"]) == 100         # competitivo
    assert itcm.puntaje_banda(110.0, b["tcrm"]) == 80          # high inclusivo
    assert itcm.puntaje_banda(85.0, b["tcrm"]) == 35           # apreciación marcada
    assert itcm.puntaje_banda(74.9, b["tcrm"]) == 10           # atraso severo
    # IAI / ICIP: mayor crecimiento de inversión = menos tensión, bandas anchas
    assert itcm.puntaje_banda(10.0, b["iai"]) == 80            # high inclusivo
    assert itcm.puntaje_banda(10.1, b["iai"]) == 100
    assert itcm.puntaje_banda(-2.0, b["iai"]) == 35
    assert itcm.puntaje_banda(-10.1, b["iai"]) == 10
    assert itcm.puntaje_banda(20.0, b["icip"]) == 80
    assert itcm.puntaje_banda(20.1, b["icip"]) == 100
    assert itcm.puntaje_banda(-20.1, b["icip"]) == 10


def test_rem_mensual_equivalente_y_idc():
    """Helpers de la metodología revisada."""
    # raíz 12 de la expectativa anual → equivalente mensual
    assert abs(itcm.rem_mensual_equivalente(23.3) - 1.7607) < 1e-3
    assert itcm.puntaje_banda(itcm.rem_mensual_equivalente(23.3),
                              itcm.BANDAS_ITCM["rem_ipc_12m"]) == 85
    # IdC = 0,30·P + 0,40·V + 0,30·A
    idc = itcm.indice_capacidad_prestable(0.9947, 1.0042, 1.0398)
    assert abs(idc - 1.012) < 1e-3
    assert itcm.puntaje_banda(idc, itcm.BANDAS_ITCM["idc"]) == 60


def test_ajuste_manual_aplicado():
    """Override del analista: saldo 85 → 60."""
    ajustes = {"saldo_comercial_12m": {
        "puntaje": 60, "justificacion": "Superávit por contracción de importaciones"}}
    r = itcm.calcular_itcm(EJEMPLO, ajustes)
    # fiscal = 0,6×57,3 (recaudación interpolada) + 0,4×60 (override) = 58,4
    assert r["dimensiones"]["viabilidad_fiscal_comercial"]["puntaje"] == 58.4
    assert r["valor"] == 61.1
    assert len(r["ajustes_aplicados"]) == 1
    aj = r["ajustes_aplicados"][0]
    assert aj["indicador"] == "saldo_comercial_12m" and aj["de"] == 85.0 and aj["a"] == 60
    ind = r["dimensiones"]["viabilidad_fiscal_comercial"]["indicadores"]["saldo_comercial_12m"]
    assert ind["puntaje_banda"] == 85.0 and ind["puntaje_aplicado"] == 60


def test_ajuste_vencido_no_se_aplica(tmp_path):
    archivo = tmp_path / "ajustes.json"
    archivo.write_text(json.dumps({
        "saldo_comercial_12m": {"puntaje": 60, "justificacion": "x", "vigente_hasta": "2026-04"},
        "idc":                 {"puntaje": 50, "justificacion": "y", "vigente_hasta": "2026-12"},
    }), encoding="utf-8")
    vigentes = itcm.cargar_ajustes(archivo, "2026-06")
    assert "saldo_comercial_12m" not in vigentes   # vencido abril < junio
    assert "idc" in vigentes
    assert itcm.cargar_ajustes(tmp_path / "no_existe.json", "2026-06") == {}


def test_renormalizacion_indicador_faltante():
    """Sin REM, la dimensión monetaria queda con IPC + IDM (renormalizados)."""
    valores = dict(EJEMPLO, rem_ipc_12m=None)
    r = itcm.calcular_itcm(valores)
    # (63,7×0.40 + 51,7×0.30) / 0.70 = 58.56 → 58.6
    assert r["dimensiones"]["estabilidad_monetaria"]["puntaje"] == 58.6
    assert abs(r["valor"] - 61.8) <= 0.05


def test_renormalizacion_dimension_faltante():
    """Sin EMAE, la dimensión actividad desaparece y los pesos se renormalizan."""
    valores = dict(EJEMPLO, emae_ia=None)
    r = itcm.calcular_itcm(valores)
    assert "actividad" not in r["dimensiones"]
    # estab=64.9 fiscal=68.4 financ=47.5 compet=45.7 inversión=54.7, sin actividad (0.11)
    esperado = (0.26 * 64.9 + 0.24 * 68.4 + 0.16 * 47.5 + 0.11 * 45.7 + 0.12 * 54.7) / 0.89
    assert abs(r["valor"] - esperado) <= 0.1


def test_sin_indicadores_devuelve_none():
    assert itcm.calcular_itcm({}) is None
    # base_monetaria es contexto: no integra el índice
    assert itcm.calcular_itcm({"base_monetaria": 0.7}) is None
    # tcrm AHORA integra el índice (competitividad externa): ya no devuelve None
    # (84,3 interpolado entre las anclas 80(35) y 102,5(80) → 45,7)
    assert itcm.calcular_itcm({"tcrm": 84.3})["valor"] == 45.7


def test_contexto_no_altera_el_indice():
    con_contexto = dict(EJEMPLO, badlar=20.62, prestamos_privados=2.1,
                        base_monetaria=0.7, tc_mayorista=-0.3)
    assert itcm.calcular_itcm(con_contexto)["valor"] == itcm.calcular_itcm(EJEMPLO)["valor"]


def test_ajuste_automatico_saldo_por_contraccion():
    """Superávit con importaciones cayendo más de lo que crecen las expo →
    ajuste a 60 (caso del doc: el superávit 2024/25 'por contracción')."""
    ind = {"valor": 17125, "expo_var_ia": 2.0, "impo_var_ia": -15.0,
           "expo_delta_12m": 1500, "impo_delta_12m": -9000}
    aj = itcm.ajuste_automatico_saldo(ind)
    assert aj is not None and aj["puntaje"] == 60 and aj["origen"] == "automatico"
    assert "contracción de importaciones" in aj["justificacion"]
    r = itcm.calcular_itcm(dict(EJEMPLO), {"saldo_comercial_12m": aj})
    # fiscal = 0,6×57,3 (recaudación interpolada) + 0,4×60 (ajuste) = 58,4
    assert r["dimensiones"]["viabilidad_fiscal_comercial"]["puntaje"] == 58.4
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
