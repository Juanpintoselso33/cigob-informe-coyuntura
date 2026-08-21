"""Tests unitarios del módulo ITVC-B100 (sin red).

Pinean: los pesos vigentes del cinturón —el doc 260702 arrancó en
35/25/10/15/15 y las enmiendas posteriores están declaradas una por una en los
comentarios de cada assert— y los internos, la agregación por índices rebaseados (sin bandas por componente),
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
    "consumo_carnes_total": 92.0,   # ADR-0217: puntúa el total, no la vacuna
    # ADR-0224: era `patentamiento_motos`. Se conserva el MISMO valor del doc
    # para que la aritmética del ejemplo siga siendo comparable: lo que cambió
    # es qué componente lo lleva, no el número.
    "motorizacion_total": 130.0,
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
    # ADR-0214: 91,3 → 89,0. `informalidad` (96,0, el mejor de la dimensión
    # después de motos) se fue a empleo, así que lo que queda promedia más
    # bajo. El EJEMPLO tampoco declara `pobreza_nowcast`, así que la
    # dimensión renormaliza sobre los tres que quedan.
    # ADR-0224: 89,0 → 90,3. Motos y autos se fundieron en un componente que
    # pesa la suma de los dos, así que el 130,0 del ejemplo entra con 0,0396 en
    # vez de con 0,0196 y tira la dimensión para arriba.
    assert dims["ingresos"]["puntaje"] == 90.3
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
    # ADR-0214: 92,2 → 94,1 al recibir `informalidad` (96,0), que está por
    # encima del promedio de los proxies.
    assert dims["empleo"]["puntaje"] == 94.1
    assert dims["percepcion"]["puntaje"] == 116.5   # ADR-0115: sólo ICC + Trends
    assert dims["seguridad"]["puntaje"] == 104.0    # ADR-0115: victimización sola
    # ADR-0214: 87,0 → 86,9. El traslado es NEUTRO sobre el índice cuando
    # están todos los componentes —conserva el peso efectivo de cada uno—,
    # pero el EJEMPLO no declara tres de ellos (pobreza, alquiler, empleo
    # registrado) y la renormalización opera DENTRO de cada dimensión: con
    # huecos, el agrupamiento sí cambia el resultado. La corrida real, con
    # los dieciséis presentes, dio 90,7 antes y 90,7 después.
    # ADR-0224: 86,9 → 87,2, por lo mismo. El ejemplo declara el componente de
    # vehículos con 130,0 y ahora pesa el doble, así que sobre una dimensión a
    # la que le faltan componentes el efecto se amplifica. La corrida real dio
    # 90,7 antes y 90,8 después.
    assert r["valor"] == 87.2
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
    assert pesos == {"ingresos": 0.2806, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.2419, "percepcion": 0.0825, "seguridad": 0.045}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9
    d = itvc.DIMENSIONES_ITVC
    # ADR-0153: entra pobreza_nowcast con 25% y los cuatro previos ceden ×0,75
    # conservando su orden relativo.
    # ADR-0214: sale `informalidad` a la dimensión de empleo. Los internos que
    # quedan NO se recalibran: se derivan de los pesos efectivos intactos sobre
    # el nominal nuevo (0,2806), así que cada uno sigue aportando lo mismo al
    # índice — 17,06%, 9,31%, 1,12% y 0,56%.
    # ADR-0223: entra `patentamiento_autos` con 2%, el mismo peso que motos, y
    # los cuatro previos ceden ×0,98 conservando su orden relativo.
    # ADR-0224: motos y autos se funden en `motorizacion_total`, que toma la
    # SUMA de los dos (0,0196 + 0,0200). Los otros tres no se tocan.
    # ADR-0225: entra `consumo_supermercados` con 20% y los CUATRO previos
    # ceden ×0,80. Es el único componente que mide volumen efectivamente
    # comprado. Los decimales de acá salen de `alta_proporcional` aplicada
    # sobre la dimensión tal como la dejó ADR-0224, no de una cuenta a mano.
    assert d["ingresos"]["indicadores"] == {"brecha_salario_cbt": 0.4767,
                                            "pobreza_nowcast": 0.2602,
                                            "consumo_carnes_total": 0.0314,
                                            "motorizacion_total": 0.0317,
                                            "consumo_supermercados": 0.2000}
    assert abs(sum(d["ingresos"]["indicadores"].values()) - 1.0) < 1e-9
    # ADR-0154: sale endeudamiento_familiar (redundante, winsorizado y de signo
    # equívoco) y la mora sostiene sola la dimensión.
    assert d["vulnerabilidad"]["indicadores"] == {"mora_familias": 1.0}
    assert d["precios"]["indicadores"] == {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                                           "alquiler_real": 0.20}
    # ADR-0130: entra empleo_registrado con 0,35 y los cuatro proxies ceden ×0,65
    # ADR-0154: sale indice_lider y los cuatro que quedan absorben ÷0,87
    # ADR-0214: entra `informalidad` con su peso efectivo intacto (9,19%) y
    # queda primera. Los otros cuatro tampoco se recalibran: sus internos bajan
    # sólo porque el nominal de la dimensión subió a 0,2419.
    # ADR-0219: entra trabajo_independiente con 10% y los cinco ceden ×0,90,
    # conservando su orden relativo.
    assert d["empleo"]["indicadores"] == {"informalidad": 0.3419,
                                          "empleo_registrado": 0.2246,
                                          "mortalidad_pymes": 0.1476,
                                          "despacho_cemento": 0.1347,
                                          "pluriempleo": 0.0512,
                                          "trabajo_independiente": 0.1000}
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
    """Sin carnes ni vehículos (fuentes sin dato), la dimensión que renormaliza es
    INGRESOS: ADR-0115 los movió ahí desde la vieja dimensión de confianza.

    Desde ADR-0214 queda apoyada en brecha y pobreza —`informalidad` se fue a
    empleo—, y como el EJEMPLO tampoco declara pobreza, el único que sobrevive
    es la brecha: la dimensión ES su índice (87,5). Que no invente peso sigue
    siendo lo que este test comprueba, y lo verifica la suma de efectivos."""
    valores = dict(EJEMPLO)
    valores["consumo_carnes_total"] = None
    valores["motorizacion_total"] = None
    r = itvc.calcular_itvc(valores)
    ing = r["dimensiones"]["ingresos"]
    assert set(ing["indicadores"]) == {"brecha_salario_cbt"}
    assert ing["puntaje"] == 87.5
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
    assert r["valor"] == 90.0


def test_sin_datos_devuelve_none():
    assert itvc.calcular_itvc({}) is None
    assert itvc.calcular_itvc({k: None for k in EJEMPLO}) is None


# ── La regla de alta, probada como REGLA y no como cinco decimales ───────────
# `alta_proporcional` existe (ADR-0225) para que la cesión no quede escrita a
# mano en el código: los pesos previos de una dimensión cambian cada vez que
# entra o se funde un componente, y unos decimales ya multiplicados quedan
# inválidos en silencio apenas eso pasa.

def test_la_cesion_es_proporcional_y_conserva_el_orden():
    previos = {"a": 0.60, "b": 0.30, "c": 0.10}
    out = itvc.alta_proporcional(previos, "nuevo", 0.20)
    assert out["nuevo"] == 0.20
    assert abs(sum(out.values()) - 1.0) < 1e-9
    # cada previo cedió exactamente ×0,80
    for k, v in previos.items():
        assert abs(out[k] - v * 0.80) < 1e-9
    # y el orden relativo entre ellos no se movió
    assert [k for k in sorted(previos, key=previos.get, reverse=True)] == \
           [k for k in sorted(('a', 'b', 'c'), key=lambda k: out[k], reverse=True)]


def test_la_cesion_se_recalcula_sobre_lo_que_haya():
    """El motivo por el que es función: si otra alta cambió la dimensión, la
    regla sigue valiendo sobre los pesos nuevos sin tocar esta línea."""
    out = itvc.alta_proporcional({"a": 0.5, "b": 0.5}, "nuevo", 0.20)
    assert out == {"a": 0.4, "b": 0.4, "nuevo": 0.20}


def test_un_alta_no_puede_pisar_un_componente_existente():
    import pytest
    with pytest.raises(ValueError):
        itvc.alta_proporcional({"a": 1.0}, "a", 0.20)


def test_un_peso_fuera_de_rango_no_se_acepta():
    import pytest
    for malo in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            itvc.alta_proporcional({"a": 1.0}, "nuevo", malo)


def test_el_supermercado_puntua_y_no_es_card_de_contexto():
    """ADR-0216/0153: o integra el índice, o no es card. El supermercado dejó
    de ser ancla de validación justamente para no quedar en ese limbo."""
    comp = {i for dd in itvc.DIMENSIONES_ITVC.values() for i in dd["indicadores"]}
    assert "consumo_supermercados" in comp
