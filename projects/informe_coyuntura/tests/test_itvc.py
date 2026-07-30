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
# vulnerabilidad (ADR-0154) = mora sola = 60,0
# empleo = 0,45×102 + 0,4×80 + 0,15×96 = 92,3
# confianza (ADR-0034) = 0,45×118 + 0,3×104 + 0,1×110 + 0,1×92 + 0,05×130 = 111,0
# ITVC = 0,35×90,5 + 0,25×74 + 0,10×89 + 0,15×92,3 + 0,15×111,0 = 89,6
EJEMPLO = {
    "brecha_salario_cbt": 87.5,
    "informalidad": 96.0,
    "ipc_alimentos": 95.0,
    "peso_tarifas": 60.0,
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
    # ADR-0154: la dimensión queda apoyada en la mora sola, así que su puntaje
    # ES el índice de la mora. Antes promediaba 0,5×118 + 0,5×60 = 89,0 con
    # endeudamiento, que salió del índice.
    assert dims["vulnerabilidad"]["puntaje"] == 60.0
    # 92,3 → 92,2 al entrar empleo_registrado (ADR-0130): el EJEMPLO no lo
    # declara, así que la dimensión renormaliza sobre los proxies con sus pesos
    # nuevos, que no son exactamente proporcionales por redondeo. Sigue dando
    # 92,2 con ADR-0154 (sale el líder, que el EJEMPLO tampoco declaraba): la
    # renormalización reparte entre los mismos tres.
    assert dims["empleo"]["puntaje"] == 92.2
    assert dims["percepcion"]["puntaje"] == 116.5   # ADR-0115: sólo ICC + Trends
    assert dims["seguridad"]["puntaje"] == 104.0    # ADR-0115: victimización sola
    assert r["valor"] == 87.0
    assert r["banda"] == "deterioro_moderado"
    assert r["ajustes_aplicados"] == []


def test_pesos_del_documento():
    """35/25/10/15/15 y los internos del doc, con las enmiendas declaradas:
    ADR-0034 en confianza (entra sentimiento_digital 10%), ADR-0111 en precios
    (entra alquiler_real 20%), ADR-0130 en empleo (entra empleo_registrado 35%),
    ADR-0153 en ingresos (entra pobreza_nowcast 25%) y ADR-0154, que es la
    primera que saca componentes en vez de agregarlos (endeudamiento_familiar e
    indice_lider).

    En las altas los existentes CEDEN proporcionalmente y en las bajas los que
    quedan ABSORBEN proporcionalmente; las dos operaciones conservan el orden
    relativo y ninguna toca los pesos NOMINALES de dimensión, que no se
    modificaron nunca."""
    pesos = {k: d["peso"] for k, d in itvc.DIMENSIONES_ITVC.items()}
    assert pesos == {"ingresos": 0.3725, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "percepcion": 0.0825, "seguridad": 0.045}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9
    d = itvc.DIMENSIONES_ITVC
    # ADR-0153: entra pobreza_nowcast con 25% y los cuatro previos ceden ×0,75
    # conservando su orden relativo.
    assert d["ingresos"]["indicadores"] == {"brecha_salario_cbt": 0.4580, "informalidad": 0.2467,
                                            "pobreza_nowcast": 0.25,
                                            "consumo_carne": 0.0302, "patentamiento_motos": 0.0151}
    assert abs(sum(d["ingresos"]["indicadores"].values()) - 1.0) < 1e-9
    # ADR-0154: sale endeudamiento_familiar (redundante, winsorizado y de signo
    # equívoco) y la mora sostiene sola la dimensión.
    assert d["vulnerabilidad"]["indicadores"] == {"mora_familias": 1.0}
    assert d["precios"]["indicadores"] == {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                                           "alquiler_real": 0.20}
    # ADR-0130: entra empleo_registrado con 0,35 y los cuatro proxies ceden ×0,65
    # ADR-0154: sale indice_lider y los cuatro que quedan absorben ÷0,87
    assert d["empleo"]["indicadores"] == {"empleo_registrado": 0.4023,
                                          "mortalidad_pymes": 0.2644,
                                          "despacho_cemento": 0.2414,
                                          "pluriempleo": 0.0919}
    assert d["percepcion"]["indicadores"] == {"icc_utdt": 0.8182, "sentimiento_digital": 0.1818}
    assert d["seguridad"]["indicadores"] == {"inseguridad": 1.0}
    for dim in d.values():
        assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9


def test_no_hay_cards_de_contexto():
    """La categoría «card visible que no puntúa» está dada de baja (ADR-0153).

    El editor la prohibió expresamente: un indicador entra al índice o va a los
    ocultos del snapshot (patrón `*_OCULTOS`, ADR-0022). Este guard existe
    porque el camino de vuelta es de una línea —agregar un nombre a la lista— y
    porque mientras `pobreza_nowcast` estuvo ahí, `publicar.py` le estampaba la
    nota de contexto sin que nada fallara.
    """
    assert itvc.INDICADORES_CONTEXTO == [], (
        f"{itvc.INDICADORES_CONTEXTO} volvería a publicarse como card de contexto: "
        f"si no puntúa va a los ocultos de publicar.py, no acá"
    )


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
    assert r["valor"] == 89.8


def test_sin_datos_devuelve_none():
    assert itvc.calcular_itvc({}) is None
    assert itvc.calcular_itvc({k: None for k in EJEMPLO}) is None
