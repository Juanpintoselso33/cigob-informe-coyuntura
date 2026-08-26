# -*- coding: utf-8 -*-
"""ADR-0261 e ADR-0262: dos constructos macro que dejaron de puntuar.

ADR-0253 y ADR-0254 les cambiaron el NOMBRE y dejaron la estructura intacta, y
cada uno anotó por escrito la deuda que quedaba: la banda de `idm` seguía
calibrada bajo la lectura que el propio ADR daba por muerta, y `icip` seguía
dentro de la dimensión Inversión midiendo consumo intermedio. Esta entrega la
salda, y en los dos casos la respuesta es la misma: **el indicador se sigue
publicando, pero no puntúa**.

Lo que estos tests vigilan no es la ausencia por la ausencia. Es que no vuelva a
pasar lo de la entrega anterior — cambiar el rótulo y dejar el score afirmando lo
que el rótulo ya no dice —, y que la retirada de un indicador no arrastre de
contrabando decisiones de peso que nadie tomó.

Tres invariantes estructurales viajan acá porque no las cuidaba nadie:

  1. **Banda ⟺ dimensión.** Un indicador con banda pero sin dimensión es una
     escala muerta que el próximo lector va a creer viva; uno en una dimensión
     sin banda revienta el motor con un KeyError en producción. Sacar un
     indicador es un movimiento de dos manos y acá se exigen las dos.
  2. **El contexto no tiene banda.** Es la mitad que faltaba: `en_indice` sale
     de `nombre in itcm.BANDAS_ITCM` (macro.py), así que un indicador que se
     declara contexto y conserva su banda sigue diciendo que integra el índice.
  3. **Los pesos que no se discutieron no se movieron.** Ver
     `test_estabilidad_monetaria_conserva_el_ancla_nominal_del_desequilibrio`.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcm        # noqa: E402
import macro       # noqa: E402
import parametrica  # noqa: E402

RETIRADOS = ("idm", "icip")


def _en_dimensiones() -> set:
    return {i for d in itcm.DIMENSIONES_ITCM.values() for i in d["indicadores"]}


# ── lo que se decidió ────────────────────────────────────────────────────────

def test_ni_idm_ni_icip_puntuan():
    """El corazón de las dos decisiones: no integran el ITCM por ninguna vía."""
    for ind in RETIRADOS:
        assert ind not in itcm.BANDAS_ITCM, f"{ind} volvió a tener banda"
        assert ind not in _en_dimensiones(), f"{ind} volvió a una dimensión"
        assert ind not in itcm.ANCLAS_ITCM, f"{ind} volvió por la puerta de las anclas"
        assert ind in itcm.INDICADORES_CONTEXTO, (
            f"{ind} no puntúa y tampoco está declarado como contexto: así queda "
            "publicado como card sin puntaje, que es justo lo que ADR-0153 prohíbe")


def test_icip_no_puede_volver_sin_cambiar_su_insumo():
    """La razón por la que `icip` salió no es DÓNDE estaba sino QUÉ suma.

    Sus dos insumos necesitarían signos opuestos —los pagos al exterior por
    servicios de informática son consumo intermedio (ADR-0253) y, si algo firman,
    firman un débito; la productividad laboral firma positivo— y el compuesto los
    suma con el MISMO signo. Mudarlo de dimensión no arregla eso, así que la
    guarda es condicional: si alguien lo devuelve al índice, `ICIP_PESOS` tiene
    que haber cambiado antes.
    """
    if "icip" in _en_dimensiones():
        assert macro.ICIP_PESOS != {"servicios_tech": 0.57, "productividad": 0.43}, (
            "icip volvió al índice con el mismo compuesto 57/43: sigue sumando "
            "con el mismo signo dos insumos que necesitarían signos opuestos")


def test_la_dimension_inversion_no_cambio_de_peso():
    """Al irse `icip`, el IAI se lleva la dimensión entera y la dimensión sigue
    valiendo 12% del ITCM. Lo que perdió justificación es que unos pagos al
    exterior midan formación de capital, no cuánto vale la inversión física."""
    inv = itcm.DIMENSIONES_ITCM["inversion"]
    assert inv["peso"] == 0.12
    assert inv["indicadores"] == {"iai": 1.0}


def test_estabilidad_monetaria_conserva_el_ancla_nominal_del_desequilibrio():
    """La guarda que atajó una sobrecorrección de esta misma entrega.

    La primera versión repartió el 20% vacante de `idm` EN PROPORCIÓN (50/25/25).
    Se ve inocente y no lo es: ADR-0193 no fijó estos pesos como proporciones
    sino contra un ancla NOMINAL —el desequilibrio monetario tenía que pesar como
    reservas_bcra, 5,2% contra 5,44%— y renormalizar lo subía a 6,5%, o sea que
    la salida de `idm` habría promovido de contrabando a otro indicador. Lo
    delató `test_el_desequilibrio_pesa_como_las_reservas_y_no_como_el_tcrm`, que
    ya existía. El 20% vuelve entero al IPC, que es el núcleo de la dimensión.
    """
    dim = itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]
    assert dim["indicadores"]["rem_ipc_12m"] == 0.20
    assert dim["indicadores"]["desequilibrio_monetario"] == 0.20
    nominal_deseq = dim["peso"] * dim["indicadores"]["desequilibrio_monetario"]
    fin = itcm.DIMENSIONES_ITCM["financiamiento"]
    nominal_reservas = fin["peso"] * fin["indicadores"]["reservas_bcra"]
    assert abs(nominal_deseq - nominal_reservas) < 0.005


# ── invariantes estructurales que no cuidaba nadie ───────────────────────────

def test_banda_y_dimension_son_el_mismo_conjunto():
    en_dim = _en_dimensiones()
    con_banda = set(itcm.BANDAS_ITCM)
    assert con_banda - en_dim == set(), (
        f"bandas de indicadores que no puntúan en ninguna dimensión: "
        f"{sorted(con_banda - en_dim)} — escala muerta que parece viva")
    assert en_dim - con_banda == set(), (
        f"indicadores en una dimensión y sin banda: {sorted(en_dim - con_banda)} "
        "— el motor revienta con KeyError la próxima corrida")


def test_el_contexto_no_conserva_su_banda():
    """macro.py deriva `en_indice` de `nombre in itcm.BANDAS_ITCM`: un indicador
    declarado contexto que conserva la banda sigue diciendo que integra el índice."""
    con_banda = [c for c in itcm.INDICADORES_CONTEXTO if c in itcm.BANDAS_ITCM]
    assert not con_banda, f"contexto con banda viva: {con_banda}"


# ── el efecto medido, con los valores del 25-ago-2026 ────────────────────────

# Snapshot del 25-ago-2026 20:11 (el que auditó la reauditoría, ya con ADR-0257
# aplicado). Congelado a propósito: pinea el EFECTO de las dos decisiones, no el
# dato del día, así que la corrida nocturna no lo mueve.
VALORES_260825 = {
    "ipc_total": 2.11, "rem_ipc_12m": 21.8, "idm": 4.7,
    "desequilibrio_monetario": 38.69, "resultado_primario": 5.55,
    "recaudacion": 88.2, "saldo_comercial_12m": 22481.0,
    "reservas_bcra": 11962.0, "idc": -0.32,
    "costo_financiamiento_tesoro": 5.8, "credito_privado": -1.5,
    "emae_ia": 2.69, "emae_difusion": 80.0, "ipi_manufacturero": -2.0,
    "tcrm": 85.47, "iai": -0.18, "icip": 8.36,
}

INF = float("inf")
# Configuración ANTERIOR, reconstruida acá para poder medir contra ella.
BANDAS_ANTES = dict(itcm.BANDAS_ITCM)
BANDAS_ANTES["idm"] = [(-INF, -2.0, 100), (-2.0, 2.0, 85), (2.0, 5.0, 60),
                       (5.0, 8.0, 35), (8.0, INF, 10)]
BANDAS_ANTES["icip"] = [(20.0, INF, 100), (5.0, 20.0, 80), (-5.0, 5.0, 60),
                        (-20.0, -5.0, 35), (-INF, -20.0, 10)]


def _itcm_antes() -> float:
    dims = {k: dict(v, indicadores=dict(v["indicadores"]))
            for k, v in itcm.DIMENSIONES_ITCM.items()}
    dims["estabilidad_monetaria"]["indicadores"] = {
        "ipc_total": 0.40, "rem_ipc_12m": 0.20, "idm": 0.20,
        "desequilibrio_monetario": 0.20,
    }
    dims["inversion"]["indicadores"] = {"iai": 0.6, "icip": 0.4}
    return parametrica.calcular_indice(
        dict(VALORES_260825), None, BANDAS_ANTES, dims,
        itcm.BANDAS_INTERPRETACION, itcm.INTERPRETACION_LEGIBLE,
        anclas_por_indicador=itcm.ANCLAS_ITCM,
        transformaciones_por_indicador=itcm.TRANSFORMACIONES_ITCM)["valor"]


def test_el_efecto_de_las_dos_decisiones_sobre_el_itcm():
    """Las dos correcciones van en sentidos OPUESTOS y casi se cancelan; se
    declaran por separado a propósito. Sacar `idm` (puntuaba 50,0, por debajo de
    su dimensión) sube el ITCM; sacar `icip` (puntuaba 73,4, por encima de la
    suya) lo baja. Que el neto sea medio punto no es diseño ni es un argumento a
    favor de ninguna de las dos."""
    antes = _itcm_antes()
    despues = itcm.calcular_itcm(dict(VALORES_260825))["valor"]
    assert antes == 64.8
    assert despues == 65.3
    # y la tensión publicada del cinturón no se mueve: 3,5 en los dos
    assert itcm.tension_de_itcm(antes) == itcm.tension_de_itcm(despues) == 3.5


def test_cada_retiro_por_separado():
    """Atribución: cuánto mueve cada uno solo, para que nadie lea el neto de
    medio punto como si las dos decisiones fueran chicas."""
    def con(dims_estab, dims_inv, valores):
        dims = {k: dict(v, indicadores=dict(v["indicadores"]))
                for k, v in itcm.DIMENSIONES_ITCM.items()}
        dims["estabilidad_monetaria"]["indicadores"] = dims_estab
        dims["inversion"]["indicadores"] = dims_inv
        return parametrica.calcular_indice(
            valores, None, BANDAS_ANTES, dims, itcm.BANDAS_INTERPRETACION,
            itcm.INTERPRETACION_LEGIBLE, anclas_por_indicador=itcm.ANCLAS_ITCM,
            transformaciones_por_indicador=itcm.TRANSFORMACIONES_ITCM)["valor"]

    antes_estab = {"ipc_total": 0.40, "rem_ipc_12m": 0.20, "idm": 0.20,
                   "desequilibrio_monetario": 0.20}
    despues_estab = {"ipc_total": 0.60, "rem_ipc_12m": 0.20,
                     "desequilibrio_monetario": 0.20}
    v = dict(VALORES_260825)
    assert con(antes_estab, {"iai": 0.6, "icip": 0.4}, v) == 64.8       # nada
    assert con(despues_estab, {"iai": 0.6, "icip": 0.4}, v) == 66.0     # solo idm  (+1,2)
    assert con(antes_estab, {"iai": 1.0}, v) == 64.1                    # solo icip (−0,7)
    assert con(despues_estab, {"iai": 1.0}, v) == 65.3                  # los dos   (+0,5)
