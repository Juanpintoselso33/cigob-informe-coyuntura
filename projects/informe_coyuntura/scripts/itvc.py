"""ITVC-B100 — Índice de Tensión del Cinturón de Vida Cotidiana (base 100).

Implementa el "ITVC — versión base 100" (Fundación CIGOB, doc 260702 vida
cotidiana, jul-2026): un índice de SEGUIMIENTO DE GESTIÓN, no de nivel
absoluto. Cada componente se rebasea a 100 = promedio del 4º trimestre de
2023 (oct-nov-dic, para amortiguar la distorsión de la devaluación de fines
de diciembre); el ITVC es el promedio ponderado directo de esos índices.

    ITVC > 100 = mejora acumulada vs el arranque del mandato
    ITVC < 100 = deterioro acumulado

A diferencia del ITCM/ITCG no hay tablas de bandas: los componentes entran
como índices continuos (la banda solo interpreta el resultado agregado).

Los cinco pesos de dimensión (35/25/10/15/15) y los internos vienen TODOS
del documento (no hay operacionalización propia de pesos). Polaridades:
las fórmulas de rebase viven en descargar_series (series itvc por
componente) y en publicar (componentes sin serie histórica); acá solo se
agrega, renormaliza e interpreta.

La tensión 0-10 del informe se deriva LINEAL de la escala del doc (decisión
del usuario, jul-2026): tensión = 5 − (ITVC − 100) × 0,2, con tope [0, 10].
Calza exacto: ITVC 110 → 3 · 105 → 4 · 100 → 5 · 95 → 6 · 85 → 8.

Overrides del analista: data/vida/ajustes_itvc.json ({indicador: {puntaje,
justificacion, vigente_hasta}}, mismo mecanismo que ITCM/ITCG — acá el
"puntaje" pisa el índice base-100 del componente).
"""
import parametrica

INF = float("inf")

# Dimensiones y pesos del doc 260702 (sección III). Las claves de indicador
# son las HISTÓRICAS del cinturón vida (mapeo componente→clave en el ADR-0018):
# I_SRC→brecha_salario_cbt · I_IFL→informalidad · I_IA→ipc_alimentos ·
# I_PT→peso_tarifas · I_EC→endeudamiento_familiar · I_IPI→mortalidad_pymes ·
# I_ISC→despacho_cemento · I_SD→pluriempleo · I_ICC→icc_utdt ·
# I_HD→inseguridad · I_CC→consumo_carne · I_PM→patentamiento_motos.
DIMENSIONES_ITVC = {
    "ingresos": {
        # ADR-0115: recibe consumo_carne y patentamiento_motos, que estaban en
        # la dimensión de percepción sin medir percepción. Sus propias fichas
        # los definen como proxies de poder de compra, y la matriz de
        # redundancia lo confirmó (ADR-0108): motos correlaciona −0,974 con la
        # mora y +0,770 con el salario, y sólo +0,442 con el ICC.
        "nombre": "Ingresos y consumo",
        "peso": 0.3725,
        # ADR-0153: entra `pobreza_nowcast` con 25%. Hasta el 30-jul-2026 era una
        # card VISIBLE que no puntuaba, o sea el patrón de "contexto" que el
        # editor dio de baja: no había tercera opción entre entrar al índice e ir
        # a los ocultos.
        #
        # Entra acá y no en macro porque las seis dimensiones del ITCM son
        # condiciones de la economía (estabilidad monetaria, viabilidad fiscal,
        # financiamiento, actividad, competitividad, inversión) y la pobreza no
        # es ninguna: es el resultado social que este cinturón ya mide.
        #
        # EL PESO, fijado antes de mirar el efecto: la pobreza cubre lo que el
        # indicador de salario NO puede ver. `brecha_salario_cbt` compara salario
        # REGISTRADO contra canasta, así que sólo alcanza al empleo formal;
        # pobreza cuenta personas, incluidos los hogares informales y los que no
        # viven de un salario. Esa población es del orden de la que mide
        # `informalidad` (32,9% de la dimensión), así que el peso va en esa banda
        # y por debajo del ancla salarial. 25% es el número redondo de la banda.
        # Los cuatro previos ceden proporcionalmente (×0,75) y conservan su orden.
        #
        # NO es redundante con la brecha salarial, y está medido: r = +0,150 en
        # la matriz publicada (n = 19). Era el solapamiento que había que
        # descartar —los dos comparan ingreso contra canasta— y no aparece.
        #
        # Pero la matriz señala otra cosa que este razonamiento no anticipaba, y
        # queda anotada acá y no sólo en el ADR: en NIVELES la pobreza pasa el
        # umbral de 0,7 con cuatro componentes de otras dimensiones —mora
        # (−0,897), motos (+0,892), empleo registrado (−0,821) e índice líder
        # (−0,748)—. No es una anomalía suya: el cinturón entero muestra 24 pares
        # altos en niveles y ninguno al destendenciar (r medio 0,413 → 0,199), y
        # eso ya está documentado como época en común (ADR-0108). Lo que sí es
        # propio de la pobreza es que sus pares se miden sobre 19 meses y no 32,
        # así que son los menos asentados de la matriz.
        #
        # Por eso entra a ESTA dimensión, donde el solapamiento queda explícito y
        # los pesos lo absorben, y no como dimensión aparte fingiendo
        # independencia.
        "indicadores": {"brecha_salario_cbt": 0.4580, "informalidad": 0.2467,
                        "pobreza_nowcast": 0.25,
                        "consumo_carne": 0.0302, "patentamiento_motos": 0.0151},
    },
    "precios": {
        "nombre": "Presión de precios",
        "peso": 0.25,
        # ADR-0111: entra alquiler_real con 20%. Los tres son precios de la
        # canasta cotidiana, pero el alquiler golpea a los hogares INQUILINOS
        # —alrededor de un tercio de los urbanos— mientras tarifas y alimentos
        # pegan en todos; por eso entra por debajo de los otros dos. Le ceden
        # proporcionalmente, conservando el orden relativo previo (tarifas
        # arriba de alimentos). El peso NOMINAL de la dimensión no se toca.
        "indicadores": {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                        "alquiler_real": 0.20},
    },
    "vulnerabilidad": {
        "nombre": "Vulnerabilidad financiera",
        "peso": 0.10,
        # ADR-0067: la mora sale del compuesto multiplicativo I_EC y puntúa
        # como indicador propio — endeudamiento queda como stock REAL puro
        # (acceso al crédito) y la mora como señal de estrés de pago. 50/50
        # provisorio, sujeto a revisión editorial (misma nota que ADR-0064).
        "indicadores": {"endeudamiento_familiar": 0.5, "mora_familias": 0.5},
    },
    "empleo": {
        "nombre": "Prospectivas de empleo",
        "peso": 0.15,
        # ADR-0112: entra indice_lider con 20%. La dimensión se llama
        # prospectiva pero sus tres componentes describen lo que YA pasó (IPI e
        # ISAC son contemporáneos, la subocupación llega con dos trimestres de
        # rezago). El Índice Líder de la UTDT está construido para anticipar
        # puntos de giro, y es el único componente del cinturón que mira
        # adelante. Los tres existentes ceden proporcionalmente (×0,8),
        # conservando su orden relativo. El peso NOMINAL de la dimensión no se
        # toca.
        #
        # ADR-0130 (2026-07-25): entra `empleo_registrado` con 35% y pasa a ser
        # el componente principal. La dimensión se llamaba "empleo" y NINGUNO de
        # sus cuatro componentes medía empleo: mortalidad_pymes es un proxy de
        # producción (IPI), despacho_cemento uno de construcción (ISAC),
        # pluriempleo mide cuántos tienen más de un trabajo y el líder anticipa
        # giros. El dato directo —asalariados registrados del sector privado,
        # SIPA, mensual— existía y no se estaba usando.
        #
        # Los cuatro existentes ceden proporcionalmente (×0,65) y conservan su
        # orden relativo, mismo procedimiento que ADR-0112. El peso NOMINAL de
        # la dimensión no se toca.
        "indicadores": {"empleo_registrado": 0.35, "mortalidad_pymes": 0.23,
                        "despacho_cemento": 0.21, "indice_lider": 0.13,
                        "pluriempleo": 0.08},
    },
    "percepcion": {
        # ADR-0115. Antes se llamaba "confianza" y mezclaba tres cosas: ADR-0110
        # arregló el rótulo, esto arregla la estructura. Quedan sólo las dos
        # medidas de ánimo: una encuestada (ICC) y una revelada por conducta de
        # búsqueda (Trends). Consumo se fue a `ingresos` y seguridad a su propia
        # dimensión.
        "nombre": "Confianza y percepción",
        "peso": 0.0825,
        "indicadores": {"icc_utdt": 0.8182, "sentimiento_digital": 0.1818},
    },
    "seguridad": {
        # ADR-0115. Dimensión propia porque la victimización no es percepción ni
        # consumo: es un hecho.
        #
        # LIMITACIÓN CONOCIDA: queda con UNA sola pata, que es el defecto que
        # ADR-0076 corrigió en la dimensión de actividad ("el 11% del índice
        # cuelga de un solo dato"). Acá pesa 4,5% en vez de 11%, así que la
        # exposición es menor, pero el riesgo de fuente única es el mismo y
        # queda declarado. Sumarle una segunda medida —percepción de
        # inseguridad, o delito por tipo— es trabajo pendiente.
        "nombre": "Seguridad",
        "peso": 0.045,
        "indicadores": {"inseguridad": 1.0},
    },
}

# Escala de interpretación del doc (sección III). (low, high, etiqueta).
BANDAS_INTERPRETACION = [
    (-INF, 85.0, "deterioro_sustancial"),
    (85.0, 95.0, "deterioro_moderado"),
    (95.0, 105.0, "sin_cambios"),
    (105.0, 110.0, "mejora_moderada"),
    (110.0, INF, "mejora_sustancial"),
]

INTERPRETACION_LEGIBLE = {
    "deterioro_sustancial": "Deterioro sustancial vs 4T-2023",
    "deterioro_moderado":   "Deterioro moderado vs 4T-2023",
    "sin_cambios":          "Sin cambios significativos vs 4T-2023",
    "mejora_moderada":      "Mejora moderada vs 4T-2023",
    "mejora_sustancial":    "Mejora sustancial vs 4T-2023",
}

# VACÍA, y tiene que quedar vacía (ADR-0153).
#
# Era la lista de indicadores que el cinturón publicaba como card VISIBLE sin
# puntuar. Esa categoría —"card de contexto"— está DADA DE BAJA por decisión
# del editor: un indicador o entra al índice, o va a los ocultos del snapshot
# (el patrón de ADR-0022 / `*_OCULTOS` en publicar.py). No hay tercera opción,
# y por eso esto no se vuelve a poblar.
#
# Historia de los dos que estuvieron acá: sentimiento_digital salió al
# incorporarse al índice (ADR-0034) y pobreza_nowcast al entrar a la dimensión
# de ingresos (ADR-0153, que descarta ADR-0113 — el motivo de entonces era que
# el nowcast arranca en 2025 y no llega a la base 4T-2023; se resolvió tomando
# la base de la serie oficial del INDEC y declarando el desvío del empalme).
INDICADORES_CONTEXTO: list[str] = []


def banda_interpretacion(itvc: float) -> str:
    return parametrica.banda_interpretacion(itvc, BANDAS_INTERPRETACION)


def tension_de_itvc(itvc: float) -> float:
    """Tensión 0-10 del cinturón, lineal sobre la escala del doc:
    5 − (ITVC − 100) × 0,2, acotada a [0, 10]."""
    return round(min(10.0, max(0.0, 5.0 - (itvc - 100.0) * 0.2)), 1)


def cargar_ajustes(path, periodo: str) -> dict:
    """Overrides del analista vigentes para `periodo` (ver parametrica)."""
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itvc(indices: dict, ajustes: dict | None = None) -> dict | None:
    """Agrega los índices base-100 por componente ({clave: índice} — None se
    ignora) en el ITVC-B100, renormalizando pesos ante faltantes (dentro de
    cada dimensión y entre dimensiones), con overrides del analista.

    Devuelve la misma forma que calcular_itcm/itcg ({valor, banda,
    banda_legible, dimensiones, ajustes_aplicados}; `puntaje_banda` guarda el
    índice sin override y `puntaje_aplicado` el vigente) para que el resto
    del pipeline y la web lo consuman genérico. None sin ningún componente.
    """
    ajustes = ajustes or {}
    resultado_dims = {}
    ajustes_aplicados = []

    for dkey, dim in DIMENSIONES_ITVC.items():
        presentes = {}
        for ikey, peso in dim["indicadores"].items():
            valor = indices.get(ikey)
            if valor is None:
                continue
            indice = round(float(valor), 1)
            aplicado = indice
            if ikey in ajustes:
                aplicado = ajustes[ikey]["puntaje"]
                ajustes_aplicados.append({
                    "indicador": ikey,
                    "de": indice,
                    "a": aplicado,
                    "justificacion": ajustes[ikey].get("justificacion", ""),
                    "origen": ajustes[ikey].get("origen", "manual"),
                })
            presentes[ikey] = {"peso": peso, "puntaje_banda": indice,
                               "puntaje_aplicado": aplicado}
        if not presentes:
            continue
        suma_pesos = sum(i["peso"] for i in presentes.values())
        for info in presentes.values():
            info["peso_renorm"] = info["peso"] / suma_pesos
        puntaje_dim = sum(i["puntaje_aplicado"] * i["peso_renorm"] for i in presentes.values())
        resultado_dims[dkey] = {
            "nombre": dim["nombre"],
            "peso": dim["peso"],
            "puntaje": round(puntaje_dim, 1),
            "indicadores": presentes,
        }

    if not resultado_dims:
        return None

    suma_dim = sum(d["peso"] for d in resultado_dims.values())
    itvc = 0.0
    for d in resultado_dims.values():
        d["peso_efectivo"] = round(d["peso"] / suma_dim, 4)
        itvc += d["puntaje"] * d["peso"] / suma_dim
        for info in d["indicadores"].values():
            info["peso_efectivo"] = round(info["peso_renorm"] * d["peso"] / suma_dim, 4)
            del info["peso_renorm"]
    itvc = round(itvc, 1)

    etiqueta = banda_interpretacion(itvc)
    return {
        "valor": itvc,
        "banda": etiqueta,
        "banda_legible": INTERPRETACION_LEGIBLE[etiqueta],
        "dimensiones": resultado_dims,
        "ajustes_aplicados": ajustes_aplicados,
    }
