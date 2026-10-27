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
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm

# Fixture mayo 2026 con la metodología REVISADA. Los valores de rem_ipc_12m,
# reservas_bcra, recaudacion e idc son los que el colector alimenta.
# `idm` e `icip` NO están: salieron del índice el 25-ago-2026 (ADR-0261/0262) y
# pasaron a contexto, así que ya no tienen banda ni peso que pinear.
# Desde el ADR-0021 el puntaje es INTERPOLADO entre las anclas de las bandas
# (banda de referencia entre paréntesis):
#   * rem_ipc_12m  = expectativa ANUAL del REM, CRUDA. El motor la convierte a
#     su equivalente mensual (raíz 12) porque así lo declara TRANSFORMACIONES_ITCM
#     (ADR-0082): 23,3% anual → 1,76% mensual → 79,8 (banda 85). El fixture pasa
#     el valor crudo a propósito: si pasara el mensual ya convertido, el motor lo
#     convertiría de nuevo — que es justo el acoplamiento que ADR-0082 eliminó.
#   * recaudacion  = NIVEL de base imponible real desestacionalizada, 100 = 4T-2023
#     (ADR-0152, antes era variación i.a. real). 94,4 → 58,5 (banda 60).
#   * reservas_bcra= NETAS (Machado). 1.881M → 25,0 (banda 30).
#   * idc          = IdC en z-scores (σ vs. historia, ADR-0028). −0,31 → 49,7 (banda 60).
#   * presión dolarización = presión 0-100 sensible al régimen. 45,24 → 64,8.
#   * tcr_terminos_intercambio = puntaje 0-100 de la matriz tipo de cambio
#     real × términos del intercambio (ADR-0360); el valor YA es el puntaje:
#     45,7 → 45,7. Hasta el 20-oct-2026 la dimensión puntuaba el ITCRM solo
#     (84,3 → 45,7), y el fixture conserva ese número para no mover el ITCM.
#   * iai          = inversión física (% i.a.). −4,2 → 41,8 (banda 35; escala
#     corrida +0,17 al crecimiento de la población, ADR-0341). Desde el
#     16-oct-2026 puntúa dentro de «Actividad e inversión» con 30%.
#   * saldo/emae quedan planos más allá de la última ancla (85 y 100).
#   * credito_privado = % i.a. REAL de préstamos privados (ADR-0022). +26% → 80.
# Dimensiones: estab=67,1 fiscal=78,5 financ=54,7
# actividad e inversión=73,9 (EMAE 100 × 0,3696 + IAI 41,8 × 0,30, renormalizado
# porque el fixture no trae difusión, industria ni actividad tributaria)
# competitividad=45,7 → ITCM=67,1. Era 66,1 con la inversión como dimensión
# propia (hasta el 16-oct-2026). ADR-0367 (escala de inflación sobre los cortes de
# color 1/2/3 % mensual): estab 67,1 → 39,0 e ITCM 67,1 → 59,8. ADR-0368 (sale la tributaria, EMAE 0,42):
# actividad 73,9 → 75,8 e ITCM → 60,2.
EJEMPLO = {
    "ipc_total": 2.58,             # interpolado 28,4 (entre 2 % → 40 y 3 % → 20, ADR-0367)
    "rem_ipc_12m": 23.3,           # ANUAL crudo → 1,76% mensual → 44,8 (ADR-0367)
    "desequilibrio_monetario": 35.2,  # tensión 0-100 de la matriz A×B: 64,8
    # ADR-0152: dejó de ser variación i.a. y pasó a NIVEL de base imponible real
    # desestacionalizada (100 = 4T-2023). 94,4 es la mediana de la serie observada.
    "recaudacion": 94.4,
    "resultado_primario": 6.39,    # superávit sobre recaudación 12m: 87,9 (banda 85)
    "saldo_comercial_12m": 17125,  # más allá de la última ancla → 85 plano
    "reservas_bcra": 1881,         # netas: 25,0 (banda 30)
    "idc": -0.31,                  # z compuesto (σ): 49,7 (banda 60)
    "credito_privado": 26.0,       # % i.a. real: 80,0 (banda 85)
    "costo_financiamiento_tesoro": 8.07,  # tasa real: 78,9 (U invertida, tramo 6-12)
    "emae_ia": 5.48,               # más allá de la última ancla → 100 plano
    "tcrm": 85.87,                 # tipo de cambio real: 49,7 (ADR-0375)
    "terminos_intercambio": 145.1401,  # términos del intercambio 2T-2026: 85,0
    # competitividad externa = matriz de los dos (no el promedio): 49,8
    "iai": -4.2,                   # inversión física: 41,8 (banda 35)
}


def test_itcm_reproduce_ejemplo():
    r = itcm.calcular_itcm(EJEMPLO)
    dims = r["dimensiones"]
    assert dims["estabilidad_monetaria"]["puntaje"] == 39.0
    # ADR-0387: las tres dimensiones de antes (fiscal-comercial 78,5, financiamiento
    # 54,7, competitividad 49,8) se reagrupan sin mover el índice.
    assert dims["cuentas_fiscales"]["puntaje"] == 76.9
    assert dims["sector_externo"]["puntaje"] == 51.4
    assert dims["financiamiento"]["puntaje"] == 69.9
    assert dims["actividad"]["puntaje"] == 75.8   # 73,9 → 75,8 (ADR-0368: EMAE 0,42 sin la tributaria)
    assert "competitividad_externa" not in dims and "viabilidad_fiscal_comercial" not in dims
    cruce = dims["sector_externo"]["indicadores"]
    assert cruce["tcrm"]["puntaje_aplicado"] == pytest.approx(49.7, abs=0.05)   # matriz (ADR-0375)
    assert "inversion" not in dims
    ind = dims["financiamiento"]["indicadores"]["credito_privado"]
    assert ind["puntaje_banda"] == 80.0 and ind["peso"] == pytest.approx(0.032 / 0.1056)
    assert dims["financiamiento"]["indicadores"]["idc"]["puntaje_aplicado"] == 49.7
    assert r["valor"] == 60.6   # 60,2 → 60,6: competitividad 45,7 → 49,8 en el ejemplo (ADR-0375)
    assert r["banda"] == "moderadamente_aflojado"   # 60,2: apenas sobre el corte de 60
    desequilibrio = dims["estabilidad_monetaria"]["indicadores"]["desequilibrio_monetario"]
    assert desequilibrio["puntaje_aplicado"] == 64.8
    assert desequilibrio["peso"] == 0.20
    assert desequilibrio["peso_efectivo"] == 0.052
    assert itcm.tension_de_itcm(r["valor"]) == 3.9
    assert r["ajustes_aplicados"] == []


def test_puntaje_interpolado():
    """ADR-0021: lineal entre anclas (punto medio de bandas finitas, borde de
    las abiertas), plano en los extremos; en cada ancla reproduce el puntaje
    de su banda."""
    import parametrica
    b = itcm.BANDAS_ITCM["ipc_total"]   # ADR-0367: ≤0,5→100 · 0,5-1,5→60 · 1,5-2,5→40 · 2,5-3,5→20 · >3,5→10
    assert parametrica.puntaje_interpolado(0.3, b) == 100.0   # antes de la 1ª ancla
    assert parametrica.puntaje_interpolado(0.5, b) == 100.0   # ancla (borde abierto)
    assert parametrica.puntaje_interpolado(1.0, b) == 60.0    # ancla = corte verde/amarillo
    assert parametrica.puntaje_interpolado(1.5, b) == 50.0    # mitad entre 60 y 40
    assert parametrica.puntaje_interpolado(2.0, b) == 40.0    # ancla = corte amarillo/naranja
    assert parametrica.puntaje_interpolado(3.0, b) == 20.0    # ancla = corte naranja/rojo
    assert parametrica.puntaje_interpolado(3.5, b) == 10.0    # última ancla
    assert parametrica.puntaje_interpolado(9.0, b) == 10.0    # plano más allá

    # Antes acá se pineaban las anclas de `idm`; salió del índice (ADR-0261) y
    # ya no tiene banda. El IAI sirve igual: misma forma de cinco tramos, con la
    # escala corrida al crecimiento de la población (ADR-0341).
    iai = itcm.BANDAS_ITCM["iai"]
    assert parametrica.puntaje_interpolado(-9.83, iai) == 10.0
    assert parametrica.puntaje_interpolado(-5.83, iai) == 35.0
    assert parametrica.puntaje_interpolado(0.17, iai) == 60.0
    assert parametrica.puntaje_interpolado(6.17, iai) == 80.0
    assert parametrica.puntaje_interpolado(10.17, iai) == 100.0


def test_puntaje_desde_anclas_respeta_los_cinco_puntos_aprobados():
    """Las anclas explícitas no se reinterpretan como puntos medios de bandas."""
    import parametrica
    anclas = ((0.0, 100.0), (25.0, 85.0), (50.0, 60.0),
              (75.0, 35.0), (100.0, 10.0))

    assert parametrica.puntaje_desde_anclas(-5.0, anclas) == 100.0
    assert parametrica.puntaje_desde_anclas(0.0, anclas) == 100.0
    assert parametrica.puntaje_desde_anclas(25.0, anclas) == 85.0
    assert parametrica.puntaje_desde_anclas(37.5, anclas) == 72.5
    assert parametrica.puntaje_desde_anclas(50.0, anclas) == 60.0
    assert parametrica.puntaje_desde_anclas(75.0, anclas) == 35.0
    assert parametrica.puntaje_desde_anclas(100.0, anclas) == 10.0
    assert parametrica.puntaje_desde_anclas(120.0, anclas) == 10.0


def test_itcm_usa_anclas_explicitas_para_desequilibrio_monetario():
    valores = dict(EJEMPLO)

    r = itcm.calcular_itcm(valores)
    indicador = r["dimensiones"]["estabilidad_monetaria"]["indicadores"][
        "desequilibrio_monetario"
    ]

    assert itcm.ANCLAS_ITCM["desequilibrio_monetario"] == (
        (0.0, 100.0), (100.0, 0.0),
    )
    assert indicador["puntaje_banda"] == 64.8
    assert indicador["puntaje_aplicado"] == 64.8
    assert indicador["peso"] == 0.20
    assert indicador["peso_efectivo"] == 0.052


def test_estabilidad_monetaria_usa_pesos_60_20_20():
    """Eran 40/20/20/20 (ADR-0193). Al salir `idm` del índice (ADR-0261) su 20%
    vuelve ENTERO al IPC: el REM y el desequilibrio son pares entre sí y no se
    tocan, y el desequilibrio además tiene un ancla nominal propia (pesar como
    las reservas) que renormalizar en proporción habría roto."""
    assert itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]["indicadores"] == {
        "ipc_total": 0.60,
        "rem_ipc_12m": 0.20,
        "desequilibrio_monetario": 0.20,
    }


def test_el_desequilibrio_pesa_como_las_reservas_y_no_como_el_tcrm():
    """La ficha pide "un peso similar al de los indicadores cambiarios/de
    reservas". El comparable es reservas_bcra; el TCRM llega a 11% por ser el
    único de su dimensión, que es un artefacto de la estructura."""
    D = itcm.DIMENSIONES_ITCM

    def nominal(dim, ind):
        return D[dim]["peso"] * D[dim]["indicadores"][ind]

    desequilibrio = nominal("estabilidad_monetaria", "desequilibrio_monetario")
    reservas = nominal("sector_externo", "reservas_bcra")
    assert abs(desequilibrio - reservas) < 0.005, (
        f"desequilibrio {desequilibrio:.2%} debería estar cerca de "
        f"reservas {reservas:.2%}")


def test_pesos_efectivos_reconcilian_con_itcm():
    """sum(puntaje × peso_efectivo) ≈ ITCM y los pesos efectivos suman 1.

    La dimensión con regla propia (competitividad, ADR-0375) no es lineal en
    sus componentes: ahí la cuenta se hace con el puntaje de la dimensión. Sus
    pesos efectivos por tarjeta igual suman el de la dimensión."""
    r = itcm.calcular_itcm(EJEMPLO)
    total = 0.0
    pesos = []
    for dkey, dim in r["dimensiones"].items():
        if itcm.DIMENSIONES_ITCM[dkey].get("grupos"):
            total += dim["puntaje"] * dim["peso_efectivo"]
        else:
            total += sum(i["puntaje_aplicado"] * i["peso_efectivo"]
                         for i in dim["indicadores"].values())
        pesos += [i["peso_efectivo"] for i in dim["indicadores"].values()]
    assert abs(total - r["valor"]) <= 0.1
    assert abs(sum(pesos) - 1.0) <= 0.001


def test_bordes_de_banda():
    """Convención: low exclusivo, high inclusivo."""
    b = itcm.BANDAS_ITCM
    assert itcm.puntaje_banda(0.5, b["ipc_total"]) == 100
    assert itcm.puntaje_banda(1.5, b["ipc_total"]) == 60
    assert itcm.puntaje_banda(2.5, b["ipc_total"]) == 40
    assert itcm.puntaje_banda(3.5, b["ipc_total"]) == 20
    assert itcm.puntaje_banda(3.51, b["ipc_total"]) == 10
    assert itcm.puntaje_banda(5.0, b["emae_ia"]) == 80     # >5 estricto para 100
    assert itcm.puntaje_banda(-5.0, b["emae_ia"]) == 5
    # ADR-0152: la recaudación es un NIVEL base-100, no una variación. El borde
    # relevante es el 100 —igualar la base imponible real de la transición—, y un
    # valor que antes era una variación buena (+10%) hoy cae en la banda más baja.
    assert itcm.puntaje_banda(100.0, b["recaudacion"]) == 60
    assert itcm.puntaje_banda(100.01, b["recaudacion"]) == 85
    assert itcm.puntaje_banda(10.0, b["recaudacion"]) == 10
    # REM: la banda opera sobre el EQUIVALENTE MENSUAL (misma escala que el IPC)
    assert itcm.puntaje_banda(1.76, b["rem_ipc_12m"]) == 40
    assert itcm.puntaje_banda(1.5, b["rem_ipc_12m"]) == 60
    assert itcm.puntaje_banda(2.51, b["rem_ipc_12m"]) == 20
    # Reservas NETAS
    assert itcm.puntaje_banda(20000, b["reservas_bcra"]) == 85   # high inclusivo
    assert itcm.puntaje_banda(20001, b["reservas_bcra"]) == 100
    assert itcm.puntaje_banda(3000, b["reservas_bcra"]) == 30
    assert itcm.puntaje_banda(0, b["reservas_bcra"]) == 10       # 0 → negativas/crisis
    assert itcm.puntaje_banda(0.01, b["reservas_bcra"]) == 30
    # IdC en z-scores (σ, ADR-0028)
    assert itcm.puntaje_banda(0.5, b["idc"]) == 60               # neutro (high inclusivo)
    assert itcm.puntaje_banda(0.51, b["idc"]) == 85             # expansión
    assert itcm.puntaje_banda(-0.5, b["idc"]) == 35             # contracción (high inclusivo)
    assert itcm.puntaje_banda(-0.49, b["idc"]) == 60            # neutro
    assert itcm.puntaje_banda(1.05, b["idc"]) == 100
    assert itcm.puntaje_banda(-1.2, b["idc"]) == 10
    # Desequilibrio monetario: los cortes son los cuatro colores de la matriz,
    # sobre la escala de TENSIÓN (mayor tensión = menor puntaje ITCM).
    assert itcm.puntaje_banda(20.0, b["desequilibrio_monetario"]) == 100
    assert itcm.puntaje_banda(20.01, b["desequilibrio_monetario"]) == 60
    assert itcm.puntaje_banda(50.0, b["desequilibrio_monetario"]) == 60
    assert itcm.puntaje_banda(50.01, b["desequilibrio_monetario"]) == 35
    assert itcm.puntaje_banda(80.0, b["desequilibrio_monetario"]) == 35
    assert itcm.puntaje_banda(80.01, b["desequilibrio_monetario"]) == 10
    # Competitividad externa (ADR-0375): las dos tarjetas con sus tramos.
    assert itcm.puntaje_banda(110.1, b["tcrm"]) == 100
    assert itcm.puntaje_banda(110.0, b["tcrm"]) == 80    # high inclusivo
    assert itcm.puntaje_banda(75.0, b["tcrm"]) == 10
    assert itcm.puntaje_banda(148.2, b["terminos_intercambio"]) == 100
    assert itcm.puntaje_banda(140.4, b["terminos_intercambio"]) == 32
    assert itcm.puntaje_banda(138.1, b["terminos_intercambio"]) == 10
    # IAI: mayor crecimiento de inversión física = menos tensión, bandas anchas
    # corridas +0,17 al crecimiento de la población (ADR-0341)
    assert itcm.puntaje_banda(10.17, b["iai"]) == 80           # high inclusivo
    assert itcm.puntaje_banda(10.2, b["iai"]) == 100
    assert itcm.puntaje_banda(-1.83, b["iai"]) == 35
    assert itcm.puntaje_banda(-9.9, b["iai"]) == 10


def test_rem_mensual_equivalente_y_idc():
    """Helpers de la metodología revisada."""
    # raíz 12 de la expectativa anual → equivalente mensual
    assert abs(itcm.rem_mensual_equivalente(23.3) - 1.7607) < 1e-3
    assert itcm.puntaje_banda(itcm.rem_mensual_equivalente(23.3),
                              itcm.BANDAS_ITCM["rem_ipc_12m"]) == 40
    # IdC = 0,30·z_precio + 0,40·z_volumen + 0,30·z_asignación (ADR-0028)
    idc = itcm.indice_capacidad_prestable(0.33, -0.13, -1.18)
    assert abs(idc - (-0.307)) < 1e-3
    assert itcm.puntaje_banda(idc, itcm.BANDAS_ITCM["idc"]) == 60


def test_ajuste_manual_aplicado():
    """Override del analista: saldo 85 → 60."""
    ajustes = {"saldo_comercial_12m": {
        "puntaje": 60, "justificacion": "Superávit por contracción de importaciones"}}
    r = itcm.calcular_itcm(EJEMPLO, ajustes)
    # sector externo = saldo 60 (override) con reservas 25,0 y el cruce 49,8 → 45,8;
    # el índice es el mismo que con la dimensión fiscal-comercial de antes (59,4)
    assert r["dimensiones"]["sector_externo"]["puntaje"] == 45.8
    assert r["valor"] == 59.4
    assert len(r["ajustes_aplicados"]) == 1
    aj = r["ajustes_aplicados"][0]
    assert aj["indicador"] == "saldo_comercial_12m" and aj["de"] == 85.0 and aj["a"] == 60
    ind = r["dimensiones"]["sector_externo"]["indicadores"]["saldo_comercial_12m"]
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
    """Sin REM, la dimensión renormaliza IPC y desequilibrio monetario."""
    valores = dict(EJEMPLO, rem_ipc_12m=None)
    r = itcm.calcular_itcm(valores)
    # (28,4×0.60 + 64,8×0.20) / 0.80 = 37,5 (ADR-0367)
    assert r["dimensiones"]["estabilidad_monetaria"]["puntaje"] == 37.5
    assert abs(r["valor"] - 60.2) <= 0.05   # era 60,3: el puntaje de dimensión se redondea distinto (ADR-0387)


def test_sin_desequilibrio_monetario_renormaliza_los_componentes_disponibles():
    valores = dict(EJEMPLO, desequilibrio_monetario=None)
    r = itcm.calcular_itcm(valores)
    estabilidad = r["dimensiones"]["estabilidad_monetaria"]
    # (28,4×0.60 + 44,8×0.20) / 0.80 = 32,5 (ADR-0367)
    assert estabilidad["puntaje"] == 32.5
    assert "desequilibrio_monetario" not in estabilidad["indicadores"]


def test_renormalizacion_dimension_faltante():
    """Sin el tipo de cambio real el cruce con los términos del intercambio no se
    calcula (la matriz necesita los dos) y el sector externo se arma con el saldo
    comercial y las reservas, renormalizados. Los términos del intercambio solos
    no entran. (Antes se probaba sin EMAE, pero desde el 16-oct-2026 la
    actividad no se queda vacía sin él: le queda la inversión física.)"""
    valores = dict(EJEMPLO, tcrm=None)
    r = itcm.calcular_itcm(valores)
    ext = r["dimensiones"]["sector_externo"]
    assert set(ext["indicadores"]) == {"saldo_comercial_12m", "reservas_bcra"}
    # (0,048 × 85,0 + 0,0544 × 25,0) / 0,1024 = 53,1
    assert ext["puntaje"] == 53.1
    assert abs(sum(i["peso_efectivo"] for d in r["dimensiones"].values()
                   for i in d["indicadores"].values()) - 1.0) <= 0.001
    # sin ninguno de los tres, la dimensión desaparece y el resto renormaliza
    sin = itcm.calcular_itcm(dict(EJEMPLO, tcrm=None, saldo_comercial_12m=None,
                                  reservas_bcra=None))
    assert "sector_externo" not in sin["dimensiones"]


def test_sin_emae_la_actividad_queda_con_la_inversion():
    """Desde el 16-oct-2026 la inversión física vive en la dimensión de
    actividad: si falta el EMAE, la dimensión no desaparece, puntúa lo que
    queda (el fixture no trae los otros tres de actividad)."""
    r = itcm.calcular_itcm(dict(EJEMPLO, emae_ia=None))
    assert r["dimensiones"]["actividad"]["puntaje"] == 41.8


def test_sin_indicadores_devuelve_none():
    assert itcm.calcular_itcm({}) is None
    # base_monetaria es contexto: no integra el índice
    assert itcm.calcular_itcm({"base_monetaria": 0.7}) is None
    # el tipo de cambio real solo no arma la dimensión: la matriz necesita los
    # dos (ADR-0375)
    assert itcm.calcular_itcm({"tcrm": 84.3}) is None
    # el compuesto pasó a contexto
    assert itcm.calcular_itcm({"tcr_terminos_intercambio": 45.7}) is None
    assert itcm.calcular_itcm({"tcrm": 85.87, "terminos_intercambio": 145.1401})["valor"] == 49.8


def test_contexto_no_altera_el_indice():
    con_contexto = dict(EJEMPLO, badlar=20.62, prestamos_privados=2.1,
                        base_monetaria=0.7, tc_mayorista=-0.3)
    assert itcm.calcular_itcm(con_contexto)["valor"] == itcm.calcular_itcm(EJEMPLO)["valor"]


def test_ajuste_automatico_saldo_por_contraccion():
    """Superávit con importaciones cayendo más de lo que crecen las expo →
    ajuste interpolado hacia 60 (caso del doc: el superávit 2024/25 'por
    contracción'; share_impo=9000/10500=85,7% → puntaje 85 − 0,714×25 = 67,1;
    ADR-0056 suaviza el force-a-60 original de este mismo caso)."""
    ind = {"valor": 17125, "expo_var_ia": 2.0, "impo_var_ia": -15.0,
           "expo_delta_12m": 1500, "impo_delta_12m": -9000}
    aj = itcm.ajuste_automatico_saldo(ind)
    assert aj is not None and aj["puntaje"] == 67.1 and aj["origen"] == "automatico"
    assert "contracción de importaciones" in aj["justificacion"]
    r = itcm.calcular_itcm(dict(EJEMPLO), {"saldo_comercial_12m": aj})
    # sector externo = saldo 67,1 (ajuste) con reservas 25,0 y el cruce 49,8 → 47,4;
    # el índice sigue en 59,8, como con la dimensión fiscal-comercial de antes
    assert r["dimensiones"]["sector_externo"]["puntaje"] == 47.4
    assert r["valor"] == 59.8
    assert r["ajustes_aplicados"][0]["origen"] == "automatico"


def test_ajuste_automatico_saldo_interpolado():
    """La penalización escala con share_impo (mejora_impo/mejora_total), sin
    acantilado: mismo p_banda=85 (valor=17125, flat más allá de la última
    ancla), variando cuánto de la mejora es atribuible a la caída de M."""
    base = {"valor": 17125, "expo_var_ia": 0.0, "impo_var_ia": 0.0}
    # share_impo = 60% → 85 − 0,2×25 = 80,0
    aj60 = itcm.ajuste_automatico_saldo(
        dict(base, expo_delta_12m=4000, impo_delta_12m=-6000))
    assert aj60["puntaje"] == 80.0
    # share_impo = 80% → 85 − 0,6×25 = 70,0
    aj80 = itcm.ajuste_automatico_saldo(
        dict(base, expo_delta_12m=2000, impo_delta_12m=-8000))
    assert aj80["puntaje"] == 70.0
    # share_impo = 100% (expo sin mejora) → piso de 60, incluso con p_banda
    # apenas por encima de 60 (valor=8000 → interpolado 61,5): el caso límite
    # que antes quedaba fuera del gate por usar el escalonado (puntaje_banda
    # daba exactamente 60 y el rule se abstenía) ahora sí se evalúa.
    aj_full = itcm.ajuste_automatico_saldo(
        {"valor": 8000, "expo_var_ia": 0.0, "impo_var_ia": -20.0,
         "expo_delta_12m": 0, "impo_delta_12m": -8000})
    assert aj_full["puntaje"] == 60.0
    # monotonía: a mayor share_impo, menor puntaje
    assert aj60["puntaje"] > aj80["puntaje"] > aj_full["puntaje"]


def test_ajuste_automatico_saldo_no_aplica():
    """No opina cuando: las impo crecen (superávit genuino), la caída de impo
    no domina (share_impo ≤ 50%), no hay superávit relevante, o faltan los
    campos de composición."""
    # impo creciendo (situación jun-2026 real)
    assert itcm.ajuste_automatico_saldo(
        {"valor": 18322, "expo_var_ia": 14.1, "impo_var_ia": 10.6,
         "expo_delta_12m": 11451, "impo_delta_12m": 7125}) is None
    # impo caen pero la mejora viene más de las expo (share_impo = 5,3%)
    assert itcm.ajuste_automatico_saldo(
        {"valor": 16000, "expo_var_ia": 12.0, "impo_var_ia": -1.0,
         "expo_delta_12m": 9000, "impo_delta_12m": -500}) is None
    # déficit / sin superávit relevante
    assert itcm.ajuste_automatico_saldo(
        {"valor": -2000, "expo_var_ia": 0.0, "impo_var_ia": -20.0,
         "expo_delta_12m": 0, "impo_delta_12m": -8000}) is None
    # banda interpolada ya ≤ 60 (valor=5001 → 56,7): el ajuste no agrega nada
    assert itcm.ajuste_automatico_saldo(
        {"valor": 5001, "expo_var_ia": 0.0, "impo_var_ia": -20.0,
         "expo_delta_12m": 0, "impo_delta_12m": -3000}) is None
    # sin composición (fallback a la serie de saldo directa)
    assert itcm.ajuste_automatico_saldo({"valor": 17125}) is None


def test_interpretacion_bandas():
    assert itcm.banda_interpretacion(15) == "severamente_apretado"
    assert itcm.banda_interpretacion(20) == "severamente_apretado"
    assert itcm.banda_interpretacion(40) == "apretado"
    assert itcm.banda_interpretacion(61.45) == "moderadamente_aflojado"
    assert itcm.banda_interpretacion(95) == "aflojado"
