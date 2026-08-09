"""Tests unitarios del módulo ITCG (sin red).

Pinean: las tablas de bandas de la Paramétrica de Gestión (doc 260702) con la
operacionalización del ADR-0013, la convención de bordes (low exclusivo, high
inclusivo), la ponderación por dimensiones (35/25/15/15/10), el mecanismo de
ajuste manual y la renormalización ante faltantes — mismo motor que el ITCM
(parametrica.py).
"""
import sys
from pathlib import Path
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcg
import gestion

# Fixture jul-2026 con valores realistas de cada indicador. Desde el ADR-0021
# el puntaje es INTERPOLADO entre las anclas de las bandas (banda de
# referencia entre paréntesis):
#   * cepo_mulc 4,91% → 100 (plano bajo la primera ancla).
#   * apertura_comercial = ALÍCUOTA efectiva 4,86% → 67,6 (la lineal del doc:
#     0% → 100 · 15% → 0; la brecha salió del compuesto — ADR-0021).
#   * desregulacion_normativa 16.178 artículos → 71,3 (ADR-0143; antes 846
#     normas → 82,0). ADR-0125 ya había cambiado la unidad (de
#     «% de avance» al conteo oficial de normas acumuladas), así que el insumo
#     del ejemplo se expresa en la unidad nueva CONSERVANDO su puntaje: lo que
#     este test fija es el ITCG que produce la combinación de puntajes del
#     documento, no el valor crudo de cada indicador.
#   * reduccion_estado −10,5% vs dic-2023 → 88,8 (banda 85).
#   * gasto_funcionamiento −18% real → 81,0.
#   * reestructuracion_organismos 40% → 52,5 (borde de banda: promedio 40/65).
#   * fal_modernizacion_laboral 100 → 100 (dos actos fundamentales, ADR-0142)
#     · litigiosidad +3,6% → 57,8 (ADR-0023 lo repartía 0,7/0,3; ADR-0128 lo
#     pasó a 0,5/0,5).
#   * privatizaciones 51,4% → 71,4 (banda 65).
#   * rigi_inversiones 22,1% → 47,7 (banda 40).
#   * concesiones 35% → 52,5 (borde de banda) · asistencia 96% → 100 ·
#     protocolo 52% → 76,6 (banda 85) · libertad_opcion_salud 40% → 65 (ancla).
# Dimensiones: económicas=81,3 estado=77,3 laboral=78,9 privatizaciones=58,1
# social=72,8 → ITCG = 75,6.
EJEMPLO = {
    "cepo_mulc": 4.91,                  # 100 (plano bajo la primera ancla)
    "apertura_comercial": 4.86,         # alícuota efectiva % → 67,6
    "desregulacion_normativa": 16178.0,  # 71,3 — ARTÍCULOS modificados o
    # eliminados, acumulados (ADR-0143). Antes 846 normas → 82,0: cambió la
    # unidad, no la fuente.
    "reduccion_estado": -10.5,          # 88,8 (banda 85)
    "gasto_funcionamiento": -18.0,      # 81,0 (banda 85)
    # masa_salarial YA NO PUNTÚA (ADR-0186, 2026-08-09): sale del cálculo del
    # ITCG a pedido de CIGOB. Se deja el valor acá porque gestion.py lo sigue
    # pasando en `valores` —el colector no deja de medirlo— y calcular_itcg lo
    # ignora al no estar en ninguna DIMENSIONES_ITCG["..."]["indicadores"].
    # Desde ADR-0189 tampoco se publica la card.
    "masa_salarial": -15.0,             # sin efecto: no integra ninguna dimensión
    "reestructuracion_organismos": 40.0,  # 52,5 (borde 40/65)
    "fal_modernizacion_laboral": 100.0,  # 100 — los DOS actos fundamentales
    # cumplidos: Ley 27.802 (mar-2026) + Decreto 408/2026 (jun-2026). ADR-0142.
    # La escala vieja de tres etapas (ADR-0098) daba 40,2 → 30,8; la nueva sólo
    # puede tomar 0, 50 o 100 y ya está en el techo.
    "litigiosidad_laboral": 3.6,        # 57,8 (banda 65) — resultado (30%, ADR-0023)
    "privatizaciones": 51.4,            # 71,4 (banda 65)
    "rigi_inversiones": 22.1,           # 47,7 (banda 40)
    "concesiones_infraestructura": 35.0,  # 52,5 (borde 40/65)
    "asistencia_directa": 96.0,         # 100
    "protocolo_antipiquetes": 52.0,     # 76,6 (banda 85)
    "libertad_opcion_salud": 40.0,      # 65 (ancla exacta)
}


def test_itcg_reproduce_ejemplo():
    r = itcg.calcular_itcg(EJEMPLO)
    dims = r["dimensiones"]
    # 83,4 → 81,3 (ADR-0143: la desregulación pasa de normas a artículos y el
    # puntaje del indicador baja de 82,0 a 71,3 — misma trayectoria, otra unidad)
    assert dims["reformas_economicas"]["puntaje"] == 81.3
    # 78,3 → 77,3 (ADR-0186: masa_salarial sale del cálculo; reduccion_estado,
    # gasto_funcionamiento y reestructuracion_organismos renormalizan 35/25/20
    # → 43,75/31,25/25, conservando su proporción relativa 7:5:4).
    assert dims["reforma_estado"]["puntaje"] == 77.3
    # 38,9 → 44,3 (ADR-0128, reparto 50/50) → 78,9 (ADR-0142, el FAL pasa a
    # medir sus dos actos fundamentales y salta de 30,8 a 100). El segundo
    # salto es editorial y no empírico: está declarado en el ADR y en la ficha.
    assert dims["reforma_laboral"]["puntaje"] == 78.9
    assert dims["privatizaciones_inversion"]["puntaje"] == 58.1
    # ADR-0189: vuelve asistencia_directa y la dimension recupera el 40/40/20
    # del documento. 0,4x100 + 0,4x76,6 + 0,2x65 = 83,6 (antes 72,8 con 67/33).
    assert dims["social_orden"]["puntaje"] == 83.6
    assert r["valor"] == 76.7          # 71,4 (0128) → 76,6 (0142) → 75,9 (0143) → 75,6 (0186) → 76,7 (0189)
    assert r["banda"] == "moderadamente_aflojado"
    assert itcg.tension_de_itcg(r["valor"]) == 2.3
    assert r["ajustes_aplicados"] == []


def test_pesos_de_dimension_del_documento():
    """Los pesos 35/25/15/15/10 del doc 260702 suman 1 y no se tocan."""
    pesos = {k: d["peso"] for k, d in itcg.DIMENSIONES_ITCG.items()}
    assert pesos == {
        "reformas_economicas": 0.35,
        "reforma_estado": 0.25,
        "reforma_laboral": 0.15,
        "privatizaciones_inversion": 0.15,
        "social_orden": 0.10,
    }
    assert abs(sum(pesos.values()) - 1.0) < 1e-9
    # D1 trae la ponderación interna explícita del doc: 40/40/20.
    d1 = itcg.DIMENSIONES_ITCG["reformas_economicas"]["indicadores"]
    assert d1 == {"cepo_mulc": 0.40, "apertura_comercial": 0.40,
                  "desregulacion_normativa": 0.20}
    # Los pesos internos de cada dimensión suman 1.
    for d in itcg.DIMENSIONES_ITCG.values():
        assert abs(sum(d["indicadores"].values()) - 1.0) < 1e-9


def test_pesos_efectivos_reconcilian_con_itcg():
    """sum(puntaje × peso_efectivo) ≈ ITCG y los pesos efectivos suman 1."""
    r = itcg.calcular_itcg(EJEMPLO)
    pares = [
        (info["puntaje_aplicado"], info["peso_efectivo"])
        for dim in r["dimensiones"].values()
        for info in dim["indicadores"].values()
    ]
    assert abs(sum(p * w for p, w in pares) - r["valor"]) <= 0.1
    assert abs(sum(w for _, w in pares) - 1.0) <= 0.001


def test_bordes_de_banda():
    """Convención: low exclusivo, high inclusivo."""
    b = itcg.BANDAS_ITCG
    # Brecha: 5% incluido en la banda óptima; >25% = cepo de hecho.
    assert itcg.puntaje_banda(5.0, b["cepo_mulc"]) == 100
    assert itcg.puntaje_banda(5.01, b["cepo_mulc"]) == 85
    assert itcg.puntaje_banda(-1.0, b["cepo_mulc"]) == 100   # CCL bajo el mayorista
    assert itcg.puntaje_banda(25.01, b["cepo_mulc"]) == 10
    # Apertura = alícuota efectiva % (ADR-0021): menor alícuota, mejor puntaje.
    assert itcg.puntaje_banda(1.0, b["apertura_comercial"]) == 100
    assert itcg.puntaje_banda(1.01, b["apertura_comercial"]) == 85
    assert itcg.puntaje_banda(7.0, b["apertura_comercial"]) == 65
    assert itcg.puntaje_banda(7.01, b["apertura_comercial"]) == 40
    assert itcg.puntaje_banda(11.01, b["apertura_comercial"]) == 10
    # y la interpolación reproduce la lineal del doc (0% → 100 · 15% → 0)
    import parametrica
    assert parametrica.puntaje_interpolado(4.86, b["apertura_comercial"]) == 67.6
    # Litigiosidad SRT (ADR-0023): caída fuerte = 100; expansión 2021-23 = 10.
    assert itcg.puntaje_banda(-15.0, b["litigiosidad_laboral"]) == 100
    assert itcg.puntaje_banda(-14.99, b["litigiosidad_laboral"]) == 85
    assert itcg.puntaje_banda(20.01, b["litigiosidad_laboral"]) == 10
    assert parametrica.puntaje_interpolado(3.6, b["litigiosidad_laboral"]) == 57.8
    # Desregulación = artículos acumulados (ADR-0143), no normas (ADR-0125).
    assert itcg.puntaje_banda(16178.0, b["desregulacion_normativa"]) == 85
    assert itcg.puntaje_banda(15000.0, b["desregulacion_normativa"]) == 60
    assert itcg.puntaje_banda(30000.01, b["desregulacion_normativa"]) == 100
    assert itcg.puntaje_banda(2499.0, b["desregulacion_normativa"]) == 10
    # Dotación APN: reducción fuerte = menos tensión; dotación creciendo = 10.
    assert itcg.puntaje_banda(-12.0, b["reduccion_estado"]) == 100
    assert itcg.puntaje_banda(-11.99, b["reduccion_estado"]) == 85
    assert itcg.puntaje_banda(0.0, b["reduccion_estado"]) == 40
    assert itcg.puntaje_banda(0.01, b["reduccion_estado"]) == 10
    # RIGI: 22,1% del pipeline aprobado (jun-2026) → 40.
    assert itcg.puntaje_banda(22.1, b["rigi_inversiones"]) == 40
    assert itcg.puntaje_banda(10.0, b["rigi_inversiones"]) == 10
    assert itcg.puntaje_banda(60.01, b["rigi_inversiones"]) == 100
    # Privatizaciones: la cartera del doc (etapa promedio 2,06/4 = 51,5%) → 65.
    assert itcg.puntaje_banda(51.5, b["privatizaciones"]) == 65
    assert itcg.puntaje_banda(35.0, b["privatizaciones"]) == 40
    # TDPS: ≈100% = desintermediación completa.
    assert itcg.puntaje_banda(100.0, b["asistencia_directa"]) == 100
    assert itcg.puntaje_banda(95.0, b["asistencia_directa"]) == 85
    # Piquetes: sin reducción (o suba) de cortes vs 2023 → 10.
    assert itcg.puntaje_banda(0.0, b["protocolo_antipiquetes"]) == 10
    assert itcg.puntaje_banda(0.01, b["protocolo_antipiquetes"]) == 40
    assert itcg.puntaje_banda(75.01, b["protocolo_antipiquetes"]) == 100


def test_renormalizacion_ante_faltantes():
    """Sin gasto_funcionamiento (fuente caída), la Reforma del Estado
    renormaliza entre dotación (0,4375) y organismos (0,25) — los dos únicos
    indicadores que quedan, ya que masa_salarial no es más miembro de la
    dimensión (ADR-0186: salió del cálculo, no de "faltó el dato")."""
    valores = dict(EJEMPLO)
    valores["gasto_funcionamiento"] = None
    r = itcg.calcular_itcg(valores)
    d2 = r["dimensiones"]["reforma_estado"]
    assert set(d2["indicadores"]) == {"reduccion_estado", "reestructuracion_organismos"}
    # (0,4375×88,8 + 0,25×52,5) / 0,6875 = 75,6 (puntajes interpolados; mismo
    # resultado que antes de ADR-0186 porque la proporción 7:4 entre estos dos
    # se conservó al renormalizar sin masa_salarial)
    assert d2["puntaje"] == 75.6
    pesos = [i["peso_efectivo"] for d in r["dimensiones"].values()
             for i in d["indicadores"].values()]
    assert abs(sum(pesos) - 1.0) <= 0.001


def test_masa_salarial_no_integra_ninguna_dimension():
    """ADR-0186: masa_salarial sale del cálculo del ITCG a pedido de CIGOB.
    Sigue en BANDAS_ITCG (la ficha publica su banda) pero ninguna dimensión
    la pesa — a diferencia de asistencia_directa (ADR-0100), no es una
    promesa cumplida: es un retiro por decisión editorial."""
    assert "masa_salarial" in itcg.BANDAS_ITCG
    for dim in itcg.DIMENSIONES_ITCG.values():
        assert "masa_salarial" not in dim["indicadores"]
    assert "masa_salarial" in itcg.INDICADORES_SUSPENDIDOS
    assert itcg.INDICADORES_SUSPENDIDOS["masa_salarial"]["dimension"] == "reforma_estado"
    # con o sin su valor, el ITCG no cambia: no hay dimensión que lo pese
    con_valor = dict(EJEMPLO)
    sin_valor = dict(EJEMPLO)
    sin_valor["masa_salarial"] = None
    assert itcg.calcular_itcg(con_valor)["valor"] == itcg.calcular_itcg(sin_valor)["valor"]


def test_ajuste_manual_del_analista():
    """Override del analista (ej. protocolo antipiquetes anulado judicialmente
    dic-2025: la caída de cortes ya no es atribuible al instrumento)."""
    ajustes = {"protocolo_antipiquetes": {
        "puntaje": 40,
        "justificacion": "Protocolo anulado judicialmente (29-dic-2025, en apelación)",
    }}
    r = itcg.calcular_itcg(EJEMPLO, ajustes)
    assert len(r["ajustes_aplicados"]) == 1
    aj = r["ajustes_aplicados"][0]
    assert aj["indicador"] == "protocolo_antipiquetes"
    assert (aj["de"], aj["a"]) == (76.6, 40)
    # D5 = 0,4×100 + 0,4×40 + 0,2×65 = 69,0 — ADR-0189 devuelve
    # asistencia_directa al cálculo y restituye los pesos del documento;
    # con el reparto 67/33 de ADR-0100 esto daba 48,2.
    assert r["dimensiones"]["social_orden"]["puntaje"] == 69.0
    # lo que se protege es que el override BAJE el índice, no un número fijo:
    # atado a un valor absoluto se rompía con cada recalibración ajena (pasó
    # con ADR-0142, que subió la línea de base de 71,4 a 76,6).
    assert r["valor"] < itcg.calcular_itcg(EJEMPLO)["valor"]


def test_sin_datos_devuelve_none():
    assert itcg.calcular_itcg({}) is None
    assert itcg.calcular_itcg({k: None for k in EJEMPLO}) is None


def test_sss_tabla_parsea_rnemp_2024_con_encabezados_agrupados():
    wb = Workbook()
    ws = wb.active
    ws.append(["EVOLUCION ANUAL DE USUARIOS POR ENTIDADES DE MEDICINA PREPAGA"])
    ws.append(["RNEMP", "Entidad de Medicina Prepaga", "Meses"])
    ws.append([None, None, "1er. Cuatrimestre *", "mayo", "junio", "julio",
               "agosto y septiembre **", "octubre ", "noviembre", "diciembre"])
    ws.append([110022, "GERMED S.A.", 6723, 6720, 6716, 6626, 6723, 6793, 6854, 6847])

    cols, entidades = gestion._sss_tabla(ws)

    assert cols == {2: "04", 3: "05", 4: "06", 5: "07", 6: "09",
                    7: "10", 8: "11", 9: "12"}
    assert len(entidades) == 1
    assert entidades[0][0] == 110022


def test_texto_bandas_legible():
    txt = itcg.texto_bandas("cepo_mulc")
    assert "≤5" in txt and "→ 100" in txt and ">25" in txt
