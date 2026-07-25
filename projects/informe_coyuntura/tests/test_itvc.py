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
    """El ejemplo del documento, con la salvedad de ADR-0111.

    EJEMPLO es el juego de valores del doc de diseño y NO trae `alquiler_real`,
    que entró a la dimensión de precios después. El motor renormaliza los dos
    componentes restantes (45/35 → 56,25/43,75), así que precios da 75,3 y no
    los 74,0 del doc: la diferencia es la renormalización funcionando, no una
    deriva del cálculo. El resto de las dimensiones queda intacto, que es lo que
    este test cuida.
    """
    r = itvc.calcular_itvc(EJEMPLO)
    dims = r["dimensiones"]
    assert dims["ingresos"]["puntaje"] == 91.3   # ADR-0115: entran carne y motos
    assert dims["precios"]["puntaje"] == 75.3
    assert dims["vulnerabilidad"]["puntaje"] == 89.0
    # 92,3 → 92,2 al entrar empleo_registrado (ADR-0130): el EJEMPLO no lo
    # declara, así que la dimensión renormaliza sobre los cuatro proxies con
    # sus pesos nuevos, que no son exactamente proporcionales por redondeo.
    assert dims["empleo"]["puntaje"] == 92.2
    assert dims["percepcion"]["puntaje"] == 116.5   # ADR-0115: sólo ICC + Trends
    assert dims["seguridad"]["puntaje"] == 104.0    # ADR-0115: victimización sola
    assert r["valor"] == 89.9
    assert r["banda"] == "deterioro_moderado"
    assert r["ajustes_aplicados"] == []


def test_pesos_del_documento():
    """35/25/10/15/15 y los internos del doc, con las enmiendas declaradas:
    ADR-0034 en confianza (entra sentimiento_digital 10%, ceden ICC y motos) y
    ADR-0111 en precios (entra alquiler_real 20%) y ADR-0112 en empleo (entra
    indice_lider 20%). En los dos casos los existentes ceden proporcionalmente
    y los pesos NOMINALES de dimensión no se tocaron nunca."""
    pesos = {k: d["peso"] for k, d in itvc.DIMENSIONES_ITVC.items()}
    assert pesos == {"ingresos": 0.3725, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "percepcion": 0.0825, "seguridad": 0.045}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9
    d = itvc.DIMENSIONES_ITVC
    assert d["ingresos"]["indicadores"] == {"brecha_salario_cbt": 0.6107, "informalidad": 0.3289,
                                            "consumo_carne": 0.0403, "patentamiento_motos": 0.0201}
    assert d["vulnerabilidad"]["indicadores"] == {"endeudamiento_familiar": 0.5,
                                                  "mora_familias": 0.5}
    assert d["precios"]["indicadores"] == {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                                           "alquiler_real": 0.20}
    # ADR-0130: entra empleo_registrado con 0,35 y los cuatro proxies ceden ×0,65
    assert d["empleo"]["indicadores"] == {"empleo_registrado": 0.35,
                                          "mortalidad_pymes": 0.23, "despacho_cemento": 0.21,
                                          "indice_lider": 0.13, "pluriempleo": 0.08}
    assert d["percepcion"]["indicadores"] == {"icc_utdt": 0.8182, "sentimiento_digital": 0.1818}
    assert d["seguridad"]["indicadores"] == {"inseguridad": 1.0}
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
    """Sin carne ni motos (fuentes sin dato), la dimensión que renormaliza es
    INGRESOS: ADR-0115 los movió ahí desde la vieja dimensión de confianza.

    Quedan brecha (0,6107) e informalidad (0,3289) y el motor reparte entre las
    dos, de modo que la dimensión vuelve al valor que tenía antes de recibirlos
    (90,5) — que es la comprobación de que la renormalización no inventa peso."""
    valores = dict(EJEMPLO)
    valores["consumo_carne"] = None
    valores["patentamiento_motos"] = None
    r = itvc.calcular_itvc(valores)
    ing = r["dimensiones"]["ingresos"]
    assert set(ing["indicadores"]) == {"brecha_salario_cbt", "informalidad"}
    assert ing["puntaje"] == 90.5
    pesos = [i["peso_efectivo"] for d in r["dimensiones"].values()
             for i in d["indicadores"].values()]
    assert abs(sum(pesos) - 1.0) <= 0.001


def test_ajuste_manual_del_analista():
    ajustes = {"peso_tarifas": {"puntaje": 80.0, "justificacion": "revisión tarifaria puntual"}}
    r = itvc.calcular_itvc(EJEMPLO, ajustes)
    assert len(r["ajustes_aplicados"]) == 1
    assert (r["ajustes_aplicados"][0]["de"], r["ajustes_aplicados"][0]["a"]) == (60.0, 80.0)
    # EJEMPLO no trae alquiler_real (ADR-0111), así que precios renormaliza
    # sobre los dos componentes del doc: 0,4375×95 + 0,5625×80 = 86,6
    assert r["dimensiones"]["precios"]["puntaje"] == 86.6
    assert r["valor"] == 92.7


def test_sin_datos_devuelve_none():
    assert itvc.calcular_itvc({}) is None
    assert itvc.calcular_itvc({k: None for k in EJEMPLO}) is None
