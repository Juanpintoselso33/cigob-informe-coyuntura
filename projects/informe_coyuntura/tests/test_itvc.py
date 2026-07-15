"""Tests unitarios del módulo ITVC-B100 (sin red).

Pinean: los pesos del doc 260702 vida cotidiana (35/25/10/15/15 y los
internos), la agregación por índices rebaseados (sin bandas por componente),
la escala de interpretación, el mapeo lineal a tensión 0-10 (decisión del
usuario: 5 − (ITVC−100)×0,2) y la renormalización ante faltantes.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itvc

# Fixture con índices base-100 realistas (100 = promedio 4T-2023):
# ingresos = 0,65×87,5 + 0,35×96 = 90,5 · precios = 0,4×95 + 0,6×60 = 74,0
# vulnerabilidad (ADR-0067) = 0,5×118 + 0,5×60 = 89,0
# empleo = 0,45×102 + 0,4×80 + 0,15×96 = 92,3
# confianza (ADR-0034) = 0,45×118 + 0,3×104 + 0,1×110 + 0,1×92 + 0,05×130 = 111,0
# ITVC = 0,35×90,5 + 0,25×74 + 0,10×89 + 0,15×92,3 + 0,15×111,0 = 89,6
EJEMPLO = {
    "brecha_salario_cbt": 87.5,
    "informalidad": 96.0,
    "ipc_alimentos": 95.0,
    "peso_tarifas": 60.0,
    "endeudamiento_familiar": 118.0,
    "mora_familias": 60.0,
    "mortalidad_pymes": 102.0,
    "despacho_cemento": 80.0,
    "pluriempleo": 96.0,
    "icc_utdt": 118.0,
    "inseguridad": 104.0,
    "sentimiento_digital": 110.0,
    "consumo_carne": 92.0,
    "patentamiento_motos": 130.0,
}


def test_itvc_reproduce_ejemplo():
    r = itvc.calcular_itvc(EJEMPLO)
    dims = r["dimensiones"]
    assert dims["ingresos"]["puntaje"] == 90.5
    assert dims["precios"]["puntaje"] == 74.0
    assert dims["vulnerabilidad"]["puntaje"] == 89.0
    assert dims["empleo"]["puntaje"] == 92.3
    assert dims["confianza"]["puntaje"] == 111.0
    assert r["valor"] == 89.6
    assert r["banda"] == "deterioro_moderado"
    assert r["ajustes_aplicados"] == []


def test_pesos_del_documento():
    """35/25/10/15/15 y los internos del doc; confianza enmendada por el
    ADR-0034 (entra sentimiento_digital 10%, cede ICC 5 y motos 5)."""
    pesos = {k: d["peso"] for k, d in itvc.DIMENSIONES_ITVC.items()}
    assert pesos == {"ingresos": 0.35, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "confianza": 0.15}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9
    d = itvc.DIMENSIONES_ITVC
    assert d["ingresos"]["indicadores"] == {"brecha_salario_cbt": 0.65, "informalidad": 0.35}
    assert d["vulnerabilidad"]["indicadores"] == {"endeudamiento_familiar": 0.5,
                                                  "mora_familias": 0.5}
    assert d["precios"]["indicadores"] == {"ipc_alimentos": 0.40, "peso_tarifas": 0.60}
    assert d["empleo"]["indicadores"] == {"mortalidad_pymes": 0.45, "despacho_cemento": 0.40,
                                          "pluriempleo": 0.15}
    assert d["confianza"]["indicadores"] == {"icc_utdt": 0.45, "inseguridad": 0.30,
                                             "sentimiento_digital": 0.10,
                                             "consumo_carne": 0.10, "patentamiento_motos": 0.05}
    for dim in d.values():
        assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9


def test_tension_lineal_por_escala_del_doc():
    """tensión = 5 − (ITVC−100)×0,2, acotada: los umbrales del doc calzan."""
    assert itvc.tension_de_itvc(100.0) == 5.0
    assert itvc.tension_de_itvc(110.0) == 3.0
    assert itvc.tension_de_itvc(105.0) == 4.0
    assert itvc.tension_de_itvc(95.0) == 6.0
    assert itvc.tension_de_itvc(85.0) == 8.0
    assert itvc.tension_de_itvc(150.0) == 0.0   # tope inferior de tensión
    assert itvc.tension_de_itvc(40.0) == 10.0   # tope superior


def test_escala_interpretacion():
    """Bordes de la escala del doc (low exclusivo, high inclusivo)."""
    assert itvc.banda_interpretacion(85.0) == "deterioro_sustancial"
    assert itvc.banda_interpretacion(85.1) == "deterioro_moderado"
    assert itvc.banda_interpretacion(95.1) == "sin_cambios"
    assert itvc.banda_interpretacion(105.0) == "sin_cambios"
    assert itvc.banda_interpretacion(105.1) == "mejora_moderada"
    assert itvc.banda_interpretacion(110.0) == "mejora_moderada"
    assert itvc.banda_interpretacion(110.1) == "mejora_sustancial"


def test_renormalizacion_ante_faltantes():
    """Sin carne ni motos (fuentes sin dato), confianza renormaliza entre
    ICC (0,45), inseguridad (0,3) y sentimiento (0,1)."""
    valores = dict(EJEMPLO)
    valores["consumo_carne"] = None
    valores["patentamiento_motos"] = None
    r = itvc.calcular_itvc(valores)
    conf = r["dimensiones"]["confianza"]
    assert set(conf["indicadores"]) == {"icc_utdt", "inseguridad", "sentimiento_digital"}
    # (0,45×118 + 0,3×104 + 0,1×110) / 0,85 = 112,06 → 112,1
    assert conf["puntaje"] == 112.1
    pesos = [i["peso_efectivo"] for d in r["dimensiones"].values()
             for i in d["indicadores"].values()]
    assert abs(sum(pesos) - 1.0) <= 0.001


def test_ajuste_manual_del_analista():
    ajustes = {"peso_tarifas": {"puntaje": 80.0, "justificacion": "revisión tarifaria puntual"}}
    r = itvc.calcular_itvc(EJEMPLO, ajustes)
    assert len(r["ajustes_aplicados"]) == 1
    assert (r["ajustes_aplicados"][0]["de"], r["ajustes_aplicados"][0]["a"]) == (60.0, 80.0)
    # precios = 0,4×95 + 0,6×80 = 86 → ITVC = 89,57 + 0,25×12 = 92,6
    assert r["dimensiones"]["precios"]["puntaje"] == 86.0
    assert r["valor"] == 92.6


def test_sin_datos_devuelve_none():
    assert itvc.calcular_itvc({}) is None
    assert itvc.calcular_itvc({k: None for k in EJEMPLO}) is None
