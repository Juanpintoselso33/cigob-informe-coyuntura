"""ITVC-B100 — Índice de Tensión del Cinturón de Vida Cotidiana (base 100).

Implementa el "ITVC — versión base 100" (Fundación CIGOB, doc 260702 vida
cotidiana, jul-2026): un índice de SEGUIMIENTO DE GESTIÓN. Los componentes se
rebasean a 100 = promedio del 4º trimestre de 2023, con una excepción vigente:
`peso_tarifas` usa umbrales internacionales de 10% para agua+energía y 5% para
transporte, para no tomar como normal el precio subsidiado de 2023 (ADR-0235).
El ITVC es el promedio ponderado directo de esos índices.

    ITVC > 100 = condiciones por encima de la referencia compuesta
    ITVC < 100 = condiciones por debajo de la referencia compuesta

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


def alta_proporcional(previos: dict, nuevo: str, peso: float) -> dict:
    """Alta de un componente con CESIÓN PROPORCIONAL de los que ya estaban.

    Es la regla que el cinturón viene aplicando en cada alta —ADR-0130 (35%),
    ADR-0112 (20%), ADR-0153 (25%), ADR-0219 (10%), ADR-0223 (2%), ADR-0225
    (20%)— y hasta ahora se aplicaba a mano, dejando en el código los decimales
    ya multiplicados. Escrita así, la regla se lee en el código en vez de
    quedar implícita en un comentario al lado de cuatro números.

    Que sea una función y no una constante importa por un motivo concreto: los
    pesos previos de una dimensión cambian cuando entra o se funde otro
    componente, y unos decimales calculados a mano quedan inválidos en silencio
    apenas eso pasa. Acá la cesión se recalcula sobre lo que efectivamente haya.

    Los previos ceden un factor (1 − peso) y **conservan su orden relativo**,
    que es la parte que hace que el alta no sea una recalibración encubierta:
    ninguno de los que estaban cambia lo que aporta EN RELACIÓN a los otros.
    El peso NOMINAL de la dimensión no se toca nunca en una alta.
    """
    if not 0.0 < peso < 1.0:
        raise ValueError(f"peso fuera de rango: {peso}")
    if nuevo in previos:
        raise ValueError(f"{nuevo} ya está en la dimensión")
    factor = 1.0 - peso
    out = {k: round(v * factor, 4) for k, v in previos.items()}
    out[nuevo] = peso
    return out

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
        # ADR-0214: baja de 0,3725 a 0,2806 porque `informalidad` se fue a la
        # dimensión de empleo. NO es una recalibración: el peso que se va es
        # exactamente el peso EFECTIVO que el indicador ya tenía (9,19% del
        # índice), así que ninguno de los que quedan cambia lo que aporta y el
        # ITCIS no se mueve. Los nominales de acá se derivan de esos efectivos.
        "peso": 0.2806,
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
        # ADR-0223: entra `patentamiento_autos` con 2%, exactamente el peso de
        # las motos. Es el espejo del componente que ya estaba y el peso igual
        # es la única asignación que no afirma, sin haberlo medido, cuál de los
        # dos vehículos dice más del bolsillo. Los cuatro previos ceden
        # proporcionalmente (×0,98) y conservan su orden relativo — la regla de
        # ADR-0130/0153. El peso NOMINAL de la dimensión no se toca.
        #
        # Sobre las series SIN recortar correlacionan +0,894 en niveles y
        # +0,368 en primeras diferencias: el nivel alto es la época en común que
        # ADR-0108 ya documentó para todo el cinturón, no señal repetida. Y
        # desde dic-2025 se separan — autos cae de 136,1 a 125,5 mientras motos
        # sube de 138,2 a 170,5—, que es exactamente lo que una sola de las dos
        # series no podía mostrar.
        #
        # OJO al leer la matriz de redundancia publicada, que dice +0,978 y
        # +0,801 para este par: mide los componentes DESPUÉS del techo de 140, y
        # motos está clavada ahí desde ene-2026, así que el techo borra el tramo
        # en que las dos se separan. Es el único par del cinturón por encima de
        # 0,7 al destendenciar y está declarado en el ADR, con el motivo.
        # ADR-0224: los dos componentes de vehículos se funden en
        # `motorizacion_total`, que toma su peso combinado (0,0196 + 0,0200)
        # SIN tocar a los otros tres. Autos y motos siguen relevándose: son los
        # Componentes A y B de la matriz A×B que explica el color, igual que la
        # vacuna dentro del total de carnes.
        #
        # El motivo es el mismo que en ADR-0217. Con las dos series por
        # separado, una suba de motos admite dos lecturas opuestas —el hogar
        # accedió a su primer vehículo, o bajó de categoría— y el índice no
        # tiene con qué distinguirlas. El total sí: si fuera sustitución
        # descendente estaría plano, porque cada moto que entra tendría un auto
        # que sale. Sube 7,5% en la ventana en que las dos series se separan.
        #
        # ADR-0225: entra `consumo_supermercados` con 20%, aplicando la regla
        # de cesión proporcional sobre lo que HAYA en la dimensión — por eso se
        # llama a `alta_proporcional` en vez de dejar acá los decimales ya
        # multiplicados. Los previos ceden ×0,80 y conservan su orden relativo.
        # El peso NOMINAL de la dimensión no se toca.
        #
        # Y esto es exactamente el caso que la función existe para sobrevivir:
        # el alta se escribió cuando la dimensión tenía cinco componentes —los
        # dos vehículos por separado— y ADR-0224 los fundió en el medio. Con los
        # decimales calculados a mano, el merge habría dejado pesos que no suman
        # uno sin que nada avisara; con la regla escrita como regla, la cesión
        # se recalculó sola sobre los cuatro que quedaron.
        #
        # POR QUÉ 20%, fijado antes de mirar el efecto. En esta dimensión
        # `brecha_salario_cbt` mide la CAPACIDAD de comprar y `pobreza_nowcast`
        # cuenta a quién no le alcanza; las dos son estructurales. Los únicos
        # rastros de compra REALIZADA eran la carne y la motorización, que
        # juntos no llegan al 8% de la dimensión y miran una proteína y los
        # vehículos. El supermercado mide la canasta cotidiana entera y con 113
        # meses de historia, así que tiene que pesar bastante más que esos dos
        # y bastante menos que las dos estructurales. 20% es el número redondo
        # de esa banda.
        #
        # ES EL ÚNICO COMPONENTE QUE MIDE VOLUMEN EFECTIVAMENTE COMPRADO. Los
        # otros miden ingreso, precio, empleo, mora, percepción o victimización.
        # Medido antes de incorporarlo: el 43% de su nivel y el 82% de su
        # movimiento mes a mes NO los reproducen las seis dimensiones juntas.
        #
        # Venía de ser el ANCLA de validación externa (ADR-0155) y por eso sale
        # del panel en el mismo movimiento: es la regla que sacó al ICC. Un
        # indicador no puede ser componente y juez del mismo índice.
        #
        # El par que hay que declarar, y no esconder: contra `pobreza_nowcast`
        # da −0,758 en NIVELES (n=20) y −0,093 al destendenciar. Queda por
        # debajo de tres de los cinco pares altos que la pobreza YA tiene, y la
        # matriz del cinturón tiene 42 pares sobre 0,7 sobre 136 — es la época
        # en común de ADR-0108, no señal repetida. En primeras diferencias, que
        # es donde se cuenta dos veces lo que se promedia, su máximo contra
        # cualquier componente es +0,345.
        "indicadores": alta_proporcional(
            {"brecha_salario_cbt": 0.5959,
             "pobreza_nowcast": 0.3253,
             "consumo_carnes_total": 0.0392,
             "motorizacion_total": 0.0396},
            "consumo_supermercados", 0.20),
    },
    "precios": {
        "nombre": "Presión de precios",
        "peso": 0.25,
        # ADR-0235 cambia la VARIABLE y el ancla de `peso_tarifas`, no su lugar
        # en el índice: pasa de IPC Regulados/RIPTE contra 4T-2023 a la canasta
        # efectiva del IIEP contra umbrales internacionales por rubro.
        # Conserva el 45% interno fijado antes de esta corrección.
        "indicadores": {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                        "alquiler_real": 0.20},
    },
    "vulnerabilidad": {
        "nombre": "Vulnerabilidad financiera",
        "peso": 0.10,
        # ADR-0154: SALE `endeudamiento_familiar` y la dimensión queda apoyada
        # en la mora sola. ADR-0067 había dejado el 50/50 declarado como
        # "provisorio, sujeto a revisión editorial"; ésta es esa revisión.
        #
        # Se va por tres motivos, y el tercero es el que decide:
        #
        # 1. Es redundante. Participa en 6 de los 24 pares altos del cinturón y
        #    su tope es r = +0,943 contra `brecha_salario_cbt`, que es el
        #    componente MÁS PESADO del índice (17,06%). También +0,919 con
        #    alimentos y −0,858 con alquiler.
        # 2. Es el único componente clavado en el techo de winsorización: índice
        #    crudo 171,5 recortado a 140.
        # 3. Y el signo es equívoco. El índice NO está invertido: mide el stock
        #    real de crédito de consumo de familias y lee que crezca como
        #    "acceso al crédito" (así lo dice el fetcher). Con la deuda real
        #    +71,5% sobre la base y la mora multiplicada por 5,6 en el mismo
        #    período, esa lectura no se sostiene: no es más acceso, es consumo
        #    financiado con crédito que no se paga. Y el efecto sobre el tablero
        #    era concreto — el componente en 140 promediaba contra la mora en
        #    17,2 y dejaba la dimensión en 78,6, o sea que TAPABA la señal que
        #    la dimensión existe para dar.
        #
        # ADR-0232: entra la carga del servicio de deuda de los hogares. La
        # mora mide incumplimiento ya materializado; la carga CDF/MS mide qué
        # parte de la masa salarial registrada queda comprometida antes del
        # atraso. En niveles comparten la crisis (+0,883), pero en cambios
        # mensuales apenas +0,182: no es la misma señal repetida. Parte con
        # 30% porque el BCRA la actualiza en lotes semestrales; la mora conserva
        # 70% por ser mensual, directa y más fresca. El peso NOMINAL de la
        # dimensión no cambia.
        "indicadores": {"mora_familias": 0.70,
                        "carga_servicio_deuda_hogares": 0.30},
    },
    "empleo": {
        "nombre": "Prospectivas de empleo",
        # ADR-0214: sube de 0,15 a 0,2419 al recibir `informalidad` con su peso
        # efectivo intacto (9,19%). Pasa a ser la segunda dimensión del índice,
        # y eso es la consecuencia buscada: la informalidad es una condición
        # del EMPLEO —de qué tipo de empleo se consigue—, no del ingreso, y
        # medirla acá es lo que ADR-0033 dejó anotado como pendiente cuando
        # observó que "la informalidad vive en Ingresos".
        "peso": 0.2419,
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
        #
        # ADR-0154: SALE `indice_lider`, y por un motivo distinto al de
        # `endeudamiento_familiar` — el líder NO es redundante (participa en 2
        # de los 24 pares altos, y uno de los dos es justamente con
        # endeudamiento, que se va en el mismo cambio). Se va porque mide otra
        # cosa: es un índice de ciclo macroeconómico construido para anticipar
        # puntos de giro de la ACTIVIDAD, no una condición de la vida cotidiana
        # de los hogares. Era el argumento de ADR-0112 para incorporarlo —"el
        # único componente que mira adelante"— y sigue siendo cierto; lo que
        # cambió es que mirar adelante no lo vuelve parte de este cinturón.
        #
        # No se descarta: pasa a VALIDADOR EXTERNO del ITCM, que es donde su
        # naturaleza encaja, y ahí funciona mejor que el validador que macro
        # tenía (ver ADR-0154 y `correlaciones_itcm`).
        #
        # Los cuatro que quedan ABSORBEN proporcionalmente (÷0,87), regla
        # simétrica de la de las altas, conservando el orden relativo.
        # `informalidad` es el componente más pesado, por encima de
        # `empleo_registrado`, que ADR-0130 había puesto como principal. Es
        # aritmética del traslado —trae 9,19% y el registrado tiene 6,04%—, no
        # una decisión de jerarquía: los dos miden empleo desde los dos lados,
        # cuánto hay y de qué calidad es.
        # ADR-0219: entra `trabajo_independiente` con 10% y los cinco previos
        # ceden proporcionalmente (×0,90), conservando su orden relativo. Es la
        # contracara de `mortalidad_pymes`: una PyME que cierra y reaparece como
        # gente facturando por su cuenta no es lo mismo que una que desaparece.
        "indicadores": {"informalidad": 0.3419, "empleo_registrado": 0.2246,
                        "mortalidad_pymes": 0.1476,
                        "despacho_cemento": 0.1347, "pluriempleo": 0.0512,
                        "trabajo_independiente": 0.1000},
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
    "deterioro_sustancial": "Deterioro sustancial frente a las referencias",
    "deterioro_moderado":   "Deterioro moderado frente a las referencias",
    "sin_cambios":          "Sin cambios significativos frente a las referencias",
    "mejora_moderada":      "Mejora moderada frente a las referencias",
    "mejora_sustancial":    "Mejora sustancial frente a las referencias",
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


def indice_asequibilidad_tarifas(carga_salario: float,
                                  transporte_pct_canasta: float) -> float:
    """Canasta IIEP → escala común del ITCIS (ADR-0235).

    Evalúa agua+energía y transporte por separado y conserva la peor señal.
    Centralizar esta cuenta evita que la serie que puntúa y la explicación de
    la card puedan implementar fórmulas distintas sin que nadie lo note.
    """
    carga = float(carga_salario)
    participacion = float(transporte_pct_canasta)
    if carga <= 0:
        raise ValueError(f"carga tarifaria fuera de rango: {carga}")
    if not 0 <= participacion <= 100:
        raise ValueError(f"participación del transporte fuera de rango: {participacion}")
    transporte = carga * participacion / 100.0
    agua_energia = carga - transporte
    t_ae = min(10.0, max(0.0, 2.0 * (agua_energia - 10.0)))
    t_transporte = min(10.0, max(0.0, 2.0 * (transporte - 5.0)))
    return round(125.0 - 5.0 * max(t_ae, t_transporte), 1)


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


# ── Construcción de los índices base-100 desde las series ────────────────────
# Vivía dentro de publicar.py, que era el único que sabía armar el ITVC. Por eso
# generar_informe.py publicaba un score legacy de vida cotidiana y los dos
# artefactos del informe decían números distintos (ADR-0206). Acá es importable
# por los dos, que es lo que cierra la causa (ADR-0208).

BASE_MESES = ("2023-10", "2023-11", "2023-12")
WINSOR_TOPE = 140.0   # techo de componentes B100 (ADR-0033) — SOLO techo:
                           # un boom (motos 166,7) no compra compensación
                           # ilimitada; las crisis NO se recortan — se señalizan
                           # con el flag de dimensión crítica (ADR-0020)

# ── La excepción al techo, ACOTADA a un componente (ADR-0224) ────────────────
#
# El techo de 140 rige para todos los componentes y está declarado en la ficha
# del ITCIS. Esto NO lo levanta: exime a uno solo, con dos motivos medidos.
#
# 1. A su peso, el techo protege contra algo que no puede pasar.
#    `motorizacion_total` pesa 0,89% del índice. Lo máximo que puede comprar
#    por encima del techo son 0,27 puntos de ITCIS, y eso exigiría que el
#    componente llegara a 170. El techo existe para que un boom no compre
#    compensación ILIMITADA en una agregación lineal; acá la compensación ya
#    está acotada por el peso, que es el mecanismo del que el techo es un
#    sustituto grueso.
#
# 2. Contra la base 4T-2023, 140 no marca un outlier: marca un año normal.
#    El 4T-2023 fue el fondo del congelamiento previo a la devaluación, o sea
#    una base DEPRIMIDA. Medido sobre 2011-2019 y rebaseado a esa misma base,
#    el 64% de los meses del total de motorización habrían superado 140 (y el
#    84% de los de autos solos), con máximos de 206,7 para el total y 213,4
#    para autos. El criterio del JRC que ADR-0033 cita recorta un puñado de
#    valores extremos —del orden del percentil 95—, no dos tercios de la
#    distribución. Winsorizar acá no controla outliers: censura el rango
#    normal, y convierte al componente en una constante justo cuando empieza a
#    decir algo.
#
# Lo que esta excepción NO decide: si el techo de 140 sigue siendo el número
# correcto PARA EL RESTO de los componentes, dado que todos comparten la misma
# base deprimida. El problema es más grande que este componente y merece su
# propio ADR; acá no se resuelve. `sentimiento_digital` y todos los demás
# siguen con techo.
WINSOR_EXENTOS = frozenset({"motorizacion_total"})

# Serie transformada (ya rebaseada en descargar_series) → indicador del cinturón
SERIES_REBASEADAS = {
    "itvc_alimentos":     "ipc_alimentos",
    # Índice de asequibilidad por componente: 100 = tensión 5. No se rebasea;
    # agua+energía y transporte llegan contra sus propias anclas (ADR-0235).
    "itvc_tarifas":       "peso_tarifas",
    "itvc_alquiler":      "alquiler_real",
    "itvc_isac":          "despacho_cemento",
    "itvc_pobreza":       "pobreza_nowcast",
    # Reconstruida desde la faena de las tres carnes: ya llega en base 100
    # = 4T-2023, así que no se re-rebasea (ADR-0217).
    "consumo_carnes_total": "consumo_carnes_total",
    # Autos + motos per cápita por acumulado móvil 12m: el colector ya la
    # entrega en base 100 = 4T-2023 (ADR-0224), como la de carnes.
    "motorizacion_total": "motorizacion_total",
}


def rebase_movil12(series, skey):
    """Índice base-100 por ACUMULADO MÓVIL de 12 meses (ADR-0024): promedio de
    los últimos 12 meses de la serie vs el promedio de las ventanas móviles que
    terminan en el 4T-2023. Desestacionaliza flujos con calendario fuerte
    (motos: enero ≈ 2× junio) — misma lógica que la carne (CICCRA ya publica
    su PM-12m). Si la serie no alcanza para las ventanas base, devuelve None
    (cae al fallback de baselines)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie if p.get("valor")}
    yms = sorted(vals)

    def ventana(fin):
        i = yms.index(fin) if fin in yms else -1
        if i < 11:
            return None
        win = yms[i - 11:i + 1]
        # 12 meses CONSECUTIVOS (sin huecos): compara el rango real
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) != 11:
            return None
        return sum(vals[k] for k in win) / 12.0

    bases = [v for v in (ventana(f) for f in BASE_MESES) if v]
    actual = ventana(yms[-1]) if yms else None
    if not bases or not actual:
        return None
    return round(actual / (sum(bases) / len(bases)) * 100.0, 1)


def rebase_de_serie(series, skey, invertido=False, base_meses=None):
    """Índice base-100 del ÚLTIMO punto de una serie vs su promedio 4T-2023.
    En series trimestrales el 4T-2023 es un único punto (2023-10), que coincide
    naturalmente con la base del doc; en mensuales, el promedio oct-nov-dic.
    `base_meses` permite una base DECLARADA distinta cuando la fuente no midió
    el 4T-2023 (ej. IVI: encuesta suspendida 2020-2023, reanudada ene-2024)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie}
    base_vals = [vals[m] for m in (base_meses or BASE_MESES) if vals.get(m) is not None]
    if not serie or not base_vals:
        return None
    base = sum(base_vals) / len(base_vals)
    ult = serie[-1]["valor"]
    if not ult or not base:
        return None
    return round((base / ult if invertido else ult / base) * 100.0, 1)


def indices_desde_series(vida_ind, series, baselines=None):
    """Índices base-100 por componente del ITVC (None = componente sin dato).

    `series` es {indicador: [{fecha, valor}, ...]} y `vida_ind` los indicadores
    del cinturón, que sólo se usan para los tres fallbacks de baselines.
    `baselines` es el contenido ya leído de `data/vida/itvc_baselines.json`:
    se recibe como dict y no como ruta a propósito, para que este módulo siga
    sin conocer el layout del repo y lo puedan importar tanto publicar.py como
    generar_informe.py (ADR-0208)."""
    idx = {}
    for skey, ikey in SERIES_REBASEADAS.items():
        serie = series.get(skey) or []
        idx[ikey] = serie[-1]["valor"] if serie else None
    # Rebase directo desde las series oficiales existentes
    idx["brecha_salario_cbt"] = rebase_de_serie(series, "brecha_salario_cbt")
    # Mora del crédito familiar (ADR-0067): % de cartera irregular, invertido
    # (más mora = peor).
    idx["mora_familias"] = rebase_de_serie(series, "mora_familias", invertido=True)
    # Carga del servicio de deuda sobre la masa salarial registrada (ADR-0232):
    # más ingreso comprometido en cuotas e intereses = peor capacidad de pago.
    idx["carga_servicio_deuda_hogares"] = rebase_de_serie(
        series, "carga_servicio_deuda_hogares", invertido=True)
    idx["icc_utdt"] = rebase_de_serie(series, "icc_utdt")
    idx["pluriempleo"] = rebase_de_serie(series, "pluriempleo", invertido=True)
    # Empleo registrado privado (ADR-0130): NO invertido — más empleo es mejor.
    # Es el único componente de la dimensión que mide empleo de verdad; los
    # otros tres son proxies (producción, construcción, pluriempleo) — el
    # líder salió del cinturón en ADR-0154.
    idx["empleo_registrado"] = rebase_de_serie(series, "empleo_registrado")
    # ADR-0218: cierre neto de PyMEs — empleadores de hasta 50 trabajadores
    # con cobertura de ART (SRT). NO invertido: menos empleadores es peor.
    # Reemplaza al IPI industrial, que llevaba el nombre `mortalidad_pymes`
    # sin medir mortalidad ni PyMEs.
    idx["mortalidad_pymes"] = rebase_de_serie(series, "mortalidad_pymes")
    # ADR-0219: participación del trabajo independiente en el empleo
    # registrado, INVERTIDA. Un empleo que se corre del salario al trabajo
    # por cuenta propia pierde aportes patronales, indemnización y
    # estabilidad, aunque siga siendo registrado.
    idx["trabajo_independiente"] = rebase_de_serie(series, "trabajo_independiente",
                                                  invertido=True)
    # Informalidad TRIMESTRAL (52.2_ASDJ, barrido vida 2/13): la 303.1 murió en
    # 2020 pero la 52.2 sigue viva — base = 4T-2023 exacto (punto 2023-10),
    # invertida (menos informalidad = mejora). Reemplaza la excepción anual.
    idx["informalidad"] = rebase_de_serie(series, "informalidad", invertido=True)
    # ADR-0217: el que puntúa es el consumo TOTAL de carnes, no la vacuna
    # sola. La vacuna sigue relevándose —es el Componente A de la ficha y la
    # mitad de la matriz A×B que explica el color— pero ya no arma índice: una
    # caída suya puede ser sustitución hacia pollo y cerdo, y leerla como
    # pérdida de acceso a proteína es el falso positivo que la ficha vino a
    # desarmar.
    #
    # ADR-0224: motos y autos YA NO arman índice. El que puntúa es
    # `motorizacion_total`, que entra por SERIES_REBASEADAS más arriba porque
    # el colector ya lo entrega en base 100 = 4T-2023 —incluida la ventana
    # móvil de 12 meses de ADR-0024, que ahí se aplica a la suma de los dos
    # vehículos y no a cada uno—. Las dos series se siguen bajando: son los
    # Componentes A y B de la matriz A×B que explica el color.
    #
    # ADR-0225: ventas en supermercados a precios constantes. NO invertido —
    # más volumen comprado es mejor. Rebase directo y sin móvil 12m: la serie
    # que publica el INDEC YA viene desestacionalizada, así que la ventana
    # móvil sólo agregaría un rezago de medio año sobre algo que no tiene
    # calendario que sacar. Es la misma regla que dejó ADR-0155 — usar la
    # desestacionalizada de la fuente antes que suavizarla acá.
    idx["consumo_supermercados"] = rebase_de_serie(series, "consumo_supermercados")
    #
    # Inseguridad (SNIC anual: su serie emite el total del año en YYYY-12, así
    # el 4T-2023 resuelve al año 2023 — la excepción declarada del doc).
    # IVI (ADR-0032): base = ene-2024, la primera medición tras la reanudación
    # de la encuesta (suspendida 2020-2023; su ventana de 12 meses captura
    # mayormente el año PRE-mandato, así que aproxima bien el arranque).
    idx["inseguridad"] = rebase_de_serie(series, "inseguridad", invertido=True,
                                               base_meses=("2024-01",))
    # Sentimiento digital (ADR-0034): canasta mensual Trends de ventana fija —
    # el cociente intra-consulta es inmune a la renormalización. Invertido:
    # más búsquedas de inflación/precios = más urgencia percibida.
    idx["sentimiento_digital"] = rebase_de_serie(series, "sentimiento_digital",
                                                       invertido=True)
    # Fallback: constante 4T-2023 documentada en itvc_baselines.json (con
    # fuente) × valor actual del indicador, si la serie no está disponible.
    bas = baselines or {}
    # ADR-0224: `patentamiento_motos` salió de este bucle junto con su condición
    # de componente. El fallback a baseline existía porque CAFAM se consulta mes
    # a mes y podía no contestar; la motorización total viene de un CSV que la
    # DNRPA publica entero en cada corrida, así que o está completa o no está —
    # el mismo criterio deliberado que ya tenía autos.
    for ikey, invertido in (("inseguridad", True),):
        if idx[ikey] is not None:
            continue
        b = (bas.get(ikey) or {}).get("valor")
        v = (vida_ind.get(ikey) or {}).get("valor")
        idx[ikey] = (round((b / v if invertido else v / b) * 100.0, 1)
                     if b and isinstance(v, (int, float)) and v else None)
    # WINSORIZACIÓN ASIMÉTRICA (ADR-0033, tratamiento de outliers JRC): los
    # componentes B100 se acotan al TECHO de 140 — un boom puntual no debe
    # comprar compensación ilimitada en la agregación lineal. SIN piso
    # deliberadamente: las crisis (endeudamiento 31,7) no se recortan, se
    # señalizan (flag crítica, ADR-0020). El crudo queda en _winsor para la
    # nota del modal. Los de WINSOR_EXENTOS se saltean: ver el bloque de
    # arriba, donde está escrito por qué y por qué no es un permiso general.
    idx["_winsor"] = {}
    for ikey, v in list(idx.items()):
        if ikey.startswith("_") or v is None or ikey in WINSOR_EXENTOS:
            continue
        if v > WINSOR_TOPE:
            idx["_winsor"][ikey] = v
            idx[ikey] = WINSOR_TOPE
    return idx
