"""Tests unitarios del módulo ITCG (sin red).

Pinean: las tablas de bandas de la Paramétrica de Gestión (doc 260702) con la
operacionalización del ADR-0013, la convención de bordes (low exclusivo, high
inclusivo), la ponderación por dimensiones (35/25/15/15/10), el mecanismo de
ajuste manual y la renormalización ante faltantes — mismo motor que el ITCM
(parametrica.py).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcg

# Fixture jul-2026 con valores realistas de cada indicador:
#   * cepo_mulc 4,91% (doc: "promesa central cumplida") → banda ≤5 → 100.
#   * apertura_comercial = ILCE 78 → "apertura condicionada" (70-80) → 65.
#   * desregulacion_normativa 57% → 85 (el ejemplo explícito del doc).
#   * reduccion_estado −10,5% vs dic-2023 → banda −12/−8 → 85.
#   * gasto_funcionamiento −18% real → 85 · masa_salarial −15% real → 85.
#   * reestructuracion_organismos 40% → banda 20-40 (high inclusivo) → 40.
#   * fal_modernizacion_laboral (Fondo de Cese) 25 → banda 20-40 → 65.
#   * privatizaciones 51,4% (cartera del doc: promedio etapa 2,06/4) → 65.
#   * rigi_inversiones 22,1% (ADR-0011) → banda 10-25 → 40.
#   * concesiones 35% → banda 15-35 (high inclusivo) → 40.
#   * asistencia_directa TDPS 96% → 100 · protocolo 52% reducción → 85 ·
#     libertad_opcion_salud 40% → 65.
# Dimensiones: económicas=83 estado=76 laboral=65 privatizaciones=50 social=87
# → ITCG = 0,35×83 + 0,25×76 + 0,15×65 + 0,15×50 + 0,10×87 = 74,0.
EJEMPLO = {
    "cepo_mulc": 4.91,                  # banda ≤5 → 100
    "apertura_comercial": 78.0,         # banda 70-80 → 65
    "desregulacion_normativa": 57.0,    # banda 50-70 → 85
    "reduccion_estado": -10.5,          # banda −12/−8 → 85
    "gasto_funcionamiento": -18.0,      # banda −25/−15 → 85
    "masa_salarial": -15.0,             # banda −20/−12 → 85
    "reestructuracion_organismos": 40.0,  # banda 20-40 → 40
    "fal_modernizacion_laboral": 25.0,  # banda 20-40 → 65
    "privatizaciones": 51.4,            # banda 35-55 → 65
    "rigi_inversiones": 22.1,           # banda 10-25 → 40
    "concesiones_infraestructura": 35.0,  # banda 15-35 → 40
    "asistencia_directa": 96.0,         # banda >95 → 100
    "protocolo_antipiquetes": 52.0,     # banda 50-75 → 85
    "libertad_opcion_salud": 40.0,      # banda 30-50 → 65
}


def test_itcg_reproduce_ejemplo():
    r = itcg.calcular_itcg(EJEMPLO)
    dims = r["dimensiones"]
    assert dims["reformas_economicas"]["puntaje"] == 83.0
    assert dims["reforma_estado"]["puntaje"] == 76.0
    assert dims["reforma_laboral"]["puntaje"] == 65.0
    assert dims["privatizaciones_inversion"]["puntaje"] == 50.0
    assert dims["social_orden"]["puntaje"] == 87.0
    assert r["valor"] == 74.0
    assert r["banda"] == "moderadamente_aflojado"
    assert itcg.tension_de_itcg(r["valor"]) == 2.6
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
    # ILCE: matriz de lectura del doc (>90 integrada, 70-90 condicionada, <70 reprimida).
    assert itcg.puntaje_banda(90.0, b["apertura_comercial"]) == 85
    assert itcg.puntaje_banda(90.01, b["apertura_comercial"]) == 100
    assert itcg.puntaje_banda(70.0, b["apertura_comercial"]) == 40
    assert itcg.puntaje_banda(70.01, b["apertura_comercial"]) == 65
    # Desregulación: 57% → 85 (ejemplo explícito del doc).
    assert itcg.puntaje_banda(57.0, b["desregulacion_normativa"]) == 85
    assert itcg.puntaje_banda(50.0, b["desregulacion_normativa"]) == 65
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
    """Sin gasto_funcionamiento ni masa_salarial (fuentes caídas), la Reforma
    del Estado renormaliza entre dotación (0,35) y organismos (0,20)."""
    valores = dict(EJEMPLO)
    valores["gasto_funcionamiento"] = None
    valores["masa_salarial"] = None
    r = itcg.calcular_itcg(valores)
    d2 = r["dimensiones"]["reforma_estado"]
    assert set(d2["indicadores"]) == {"reduccion_estado", "reestructuracion_organismos"}
    # (0,35×85 + 0,20×40) / 0,55 = 68,6
    assert d2["puntaje"] == 68.6
    pesos = [i["peso_efectivo"] for d in r["dimensiones"].values()
             for i in d["indicadores"].values()]
    assert abs(sum(pesos) - 1.0) <= 0.001


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
    assert (aj["de"], aj["a"]) == (85, 40)
    # D5 = 0,4×100 + 0,4×40 + 0,2×65 = 69
    assert r["dimensiones"]["social_orden"]["puntaje"] == 69.0
    assert r["valor"] < 74.0


def test_sin_datos_devuelve_none():
    assert itcg.calcular_itcg({}) is None
    assert itcg.calcular_itcg({k: None for k in EJEMPLO}) is None


def test_texto_bandas_legible():
    txt = itcg.texto_bandas("cepo_mulc")
    assert "≤5" in txt and "→ 100" in txt and ">25" in txt
