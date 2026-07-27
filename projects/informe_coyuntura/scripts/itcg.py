"""ITCG — Índice de Tensión del Cinturón de Gestión.

Implementa la "Fórmula Paramétrica para Evaluación del Estado de Tensión —
Cinturón de la Gestión" (Fundación CIGOB, doc 260702, jul-2026). Escala 0-100:
0 = máxima tensión (el gobierno promete reformas pero no las ejecuta),
100 = mínima tensión (agenda de reformas ejecutándose).

ITCG = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor))

La tensión 0-10 del informe se deriva como (100 − ITCG) / 10 (motor común en
parametrica.py, compartido con el ITCM macro).

Las CINCO DIMENSIONES y sus pesos (35/25/15/15/10) vienen del documento.
Los pesos INTERNOS de cada dimensión son operacionalización propia donde el
doc no los fija (solo D1 trae 40/40/20 explícito) — ver ADR-0013.

Decisiones sobre ambigüedades del documento (ADR-0013):
  * El doc dice "dieciséis indicadores" pero nunca los enumera de forma
    cerrada; se operacionalizan 14 conservando las CLAVES históricas de
    gestion.py (cepo_mulc, reduccion_estado, ...) para no romper las series
    acumuladas en data/historico.
  * El ejemplo de D1 del doc "(0,40×20 + 0,40×95 + 0,20×85) = 63/100" es
    ilustrativo y sus insumos no cierran con el propio texto (la brecha de
    4,91% se describe como "promesa cumplida" pero aparecería puntuando 20 o
    95 según el orden). No se pinea ese resultado: los puntajes salen siempre
    de las bandas sobre datos reales.
  * Apertura comercial: el doc definía un compuesto (brecha inversa, alícuota
    efectiva, canal verde aduanero). El canal verde no tiene fuente pública y
    la brecha ya puntúa como indicador propio (cepo_mulc) — mantenerla dentro
    del compuesto la hacía pesar ~1,6 veces en la dimensión (doble conteo,
    ADR-0021). Desde jul-2026 apertura mide la ALÍCUOTA EFECTIVA sola, con
    bandas ancladas en la lineal del doc (0% → 100 · 15% → 0).
  * Fondo de Cese (D3): el doc lo define compuesto (cobertura CCT 40% +
    patrimonio FCI/CNV 30% + litigiosidad diff-in-diff 30%); se computa en
    gestion.py renormalizando lo disponible y conserva la clave histórica
    fal_modernizacion_laboral.
  * Estado legal del protocolo antipiquetes (anulado 29-dic-2025, en
    apelación): el doc pide tratarlo como dato de primer orden — se expone
    como contexto del indicador y habilita override del analista en
    data/gestion/ajustes_itcg.json, no una banda propia.

El juicio cualitativo del analista se expresa como override en
data/gestion/ajustes_itcg.json, con justificación y vencimiento (mismo
mecanismo que el ITCM).
"""
import parametrica

INF = float("inf")

# Tablas de bandas. (low, high, puntaje) — low EXCLUSIVO, high INCLUSIVO,
# convención pineada por tests/test_itcg.py. Mayor puntaje = reforma
# ejecutándose = menos tensión gerencial.
BANDAS_ITCG = {
    "cepo_mulc": [                      # % de brecha CCL/mayorista (cepo corporativo)
        # Doc: brecha sostenida <10-15% = condiciones óptimas de unificación;
        # 4,91% (may-2026) se lee "promesa central cumplida".
        (-INF, 5.0, 100), (5.0, 10.0, 85), (10.0, 15.0, 65), (15.0, 25.0, 40), (25.0, INF, 10),
    ],
    "apertura_comercial": [             # alícuota efectiva % del comercio exterior
        # ADR-0021: la brecha cambiaria salió del compuesto (puntúa una sola
        # vez, en cepo_mulc) y apertura mide la alícuota efectiva sola
        # (recaudación DEX+DIM / intercambio ICA). Anclas sobre la lineal del
        # doc (0% → 100 · 15% → 0): los puntos medios 2,25 / 5,25 / 9 caen
        # exactos en esa recta, así el puntaje interpolado la reproduce.
        (-INF, 1.0, 100), (1.0, 3.5, 85), (3.5, 7.0, 65), (7.0, 11.0, 40), (11.0, INF, 10),
    ],
    "desregulacion_normativa": [        # normas de desregulación acumuladas desde dic-2023
        # ADR-0125: la fuente pasa a ser el informe mensual del Ministerio de
        # Desregulación y la unidad deja de ser un % de avance sobre una escala
        # propia (100 normas = plan completo) para ser el CONTEO OFICIAL.
        #
        # La escala sigue siendo CONVENCIÓN NUESTRA y conviene no disimularlo:
        # el ministerio publica el conteo pero NO publica ninguna meta, así que
        # el "plan completo" lo seguimos poniendo nosotros. Es la misma
        # limitación que ADR-0096 dejó declarada; cambió la procedencia del
        # número, no la de la vara.
        #
        # Los cortes son múltiplos redondos que cubren la trayectoria real del
        # programa (4 normas en dic-2023 → 689 en jun-2026) sin saturar hoy:
        # con 689 el puntaje es 73,3, casi el mismo 72,0 que daba la métrica
        # anterior — la fuente cambió, el resultado no, que es lo que ADR-0045
        # pide para no mover un número recalibrando.
        #
        # Reparto sobre los 31 puntos reales de la serie: 10/7/12/2/0. El tramo
        # superior está vacío A PROPÓSITO (el programa está a mitad de camino).
        # REVISAR cuando el acumulado pase de 1.000: al ritmo de 2026 (+50/mes)
        # eso ocurre alrededor de mediados de 2027 y el indicador empieza a
        # aplanarse contra el techo.
        (1200.0, INF, 100), (600.0, 1200.0, 85), (300.0, 600.0, 60),
        (100.0, 300.0, 35), (-INF, 100.0, 10),
    ],
    "reduccion_estado": [               # % variación dotación APN vs dic-2023 (− = reducción)
        # Calibrado con el dato real: la APN civil recortó ~10-12% desde
        # dic-2023 (~50 mil salidas) → banda 85. Una dotación creciendo = 10.
        (-INF, -12.0, 100), (-12.0, -8.0, 85), (-8.0, -4.0, 65), (-4.0, 0.0, 40), (0.0, INF, 10),
    ],
    "gasto_funcionamiento": [           # % variación REAL del gasto de funcionamiento vs 2023
        # Bandas anchas: el ajuste 2024 fue histórico (−25/−30% real del gasto
        # primario); funcionamiento acompaña con menos amplitud.
        (-INF, -25.0, 100), (-25.0, -15.0, 85), (-15.0, -5.0, 65), (-5.0, 0.0, 40), (0.0, INF, 10),
    ],
    "masa_salarial": [                  # % variación REAL de la masa salarial APN vs dic-2023
        # CONVENCIÓN calibrada al período (ADR-0121): gemela de gasto_funcionamiento
        # —misma medida de variación real del gasto en personal del SPN— y con el
        # mismo origen: los cortes (−5/−12/−20) son grados de recorte fijados
        # contra la magnitud del ajuste 2024, no un umbral externo. El cero es
        # neutro (masa mantenida en términos reales), pero las bandas describen
        # este ajuste. No es reducible: no hay serie comparable previa a dic-2023.
        (-INF, -20.0, 100), (-20.0, -12.0, 85), (-12.0, -5.0, 65), (-5.0, 0.0, 40), (0.0, INF, 10),
    ],
    "reestructuracion_organismos": [    # % de avance (actos de disolución/fusión vs plan)
        # CONCEPTUAL (ADR-0121): medidor de avance 0-100 hacia el plan, mismo
        # patrón que privatizaciones y fal. El 100 —plan de disoluciones/fusiones
        # completo— es el ancla con significado, no el rango observado; los cortes
        # son cuartos de avance en números redondos.
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "fal_modernizacion_laboral": [      # Actos fundamentales del FAL (ADR-0142)
        # RECALIBRADO 2026-07-26 porque cambió lo que mide la escala. El
        # indicador dejó de ser el compuesto de ADR-0098 (construcción 40 +
        # vigencia 20 + adopción 40, escala continua 0-100) y pasa a medir los
        # DOS ACTOS FUNDAMENTALES que ponen en pie al Fondo, 50 cada uno. La
        # escala nueva sólo puede tomar TRES valores y las bandas describen
        # exactamente esos tres, con los cortes en los huecos:
        #     0  ningún acto: el Fondo no existe             ->  10
        #    50  sancionado pero sin reglamentar             ->  50
        #   100  ley + reglamentación: bases completas       -> 100
        #
        # HONESTIDAD SOBRE EL EFECTO: con los dos actos cumplidos el puntaje
        # pasa de 30,8 a 100 y el ITCG sube 5,2 puntos. El cambio MEJORA el
        # número y la justificación es editorial (la revisión externa sostiene
        # que sancionar y reglamentar agota la promesa hasta la vigencia), no
        # empírica. ADR-0098 sostenía lo contrario. Queda escrito para que se
        # pueda discutir.
        #
        # Y EL INDICADOR YA NO DISCRIMINA: los dos actos ocurrieron y no se
        # deshacen, así que queda fijo en 100 para siempre. Va contra ADR-0042
        # y se publica igual por decisión del editor. Ver ADR-0142.
        (75.0, INF, 100), (25.0, 75.0, 50), (-INF, 25.0, 10),
    ],
    "privatizaciones": [                # % de avance por etapas (promedio etapa/4 de la cartera)
        # Etapas 0-4 del doc: 0 sin definir · 1 preparatoria · 2 pliegos ·
        # 3 licitación/adjudicación · 4 cerrada. Cartera jun-2026 ≈ 2,06/4 = 51%.
        (75.0, INF, 100), (55.0, 75.0, 85), (35.0, 55.0, 65), (15.0, 35.0, 40), (-INF, 15.0, 10),
    ],
    "rigi_inversiones": [               # % de inversión aprobada sobre el pipeline (ADR-0011)
        # 22,1% (jun-2026): pipeline dominado por mega-proyectos en evaluación.
        (60.0, INF, 100), (40.0, 60.0, 85), (25.0, 40.0, 65), (10.0, 25.0, 40), (-INF, 10.0, 10),
    ],
    "concesiones_infraestructura": [    # % corredores adjudicados / plan (tasa de adjudicación)
        # CONCEPTUAL (ADR-0121): tasa de adjudicación 0-100 (km adjudicados sobre
        # los km del plan de la Red Federal). El 100 —plan adjudicado por
        # completo— es el ancla; los cortes son grados de avance redondos, no el
        # rango observado.
        (75.0, INF, 100), (55.0, 75.0, 85), (35.0, 55.0, 65), (15.0, 35.0, 40), (-INF, 15.0, 10),
    ],
    "asistencia_directa": [             # TDPS: % del gasto social SIN intermediación (0-100)
        # Doc: la desintermediación fue un cambio normativo puntual (Dto.
        # 198/2024); TDPS ≈ 100% = promesa cumplida en el plano financiero.
        (95.0, INF, 100), (85.0, 95.0, 85), (60.0, 85.0, 65), (30.0, 60.0, 40), (-INF, 30.0, 10),
    ],
    "protocolo_antipiquetes": [         # % de reducción de cortes vs promedio 2023 (IRPC×100)
        # CABA: caída >50% en 2024 y 240 cortes en 2025 (vs ~11% share 2023).
        (75.0, INF, 100), (50.0, 75.0, 85), (25.0, 50.0, 65), (0.0, 25.0, 40), (-INF, 0.0, 10),
    ],
    "libertad_opcion_salud": [          # % de avance de la desregulación de obras sociales
        # CONCEPTUAL (ADR-0121): % de usuarios de prepagas que ya pueden derivar
        # su aporte directo (desregulación del Dto. 170/2024). El 100 —libre
        # opción plena— es el ancla; los cortes son grados de avance redondos,
        # no calibrados al valor observado.
        (70.0, INF, 100), (50.0, 70.0, 85), (30.0, 50.0, 65), (10.0, 30.0, 40), (-INF, 10.0, 10),
    ],
    "litigiosidad_laboral": [           # juicios SRT, % 12m vs 12m previos (ADR-0023)
        # El RESULTADO que la reforma persigue (enfriar la industria del
        # juicio), complementa la adopción del instrumento (Fondo de Cese).
        # Historia: +40/67% (2021-22), +33/37% (2023), +3/7% (2024-26) —
        # bandas calibradas a ese rango; caída sostenida = canal judicial
        # desactivándose.
        (-INF, -15.0, 100), (-15.0, -5.0, 85), (-5.0, 5.0, 65), (5.0, 20.0, 40), (20.0, INF, 10),
    ],
}

# Dimensiones del índice (doc 260702: pesos 35/25/15/15/10). Los pesos internos
# de D2-D5 son operacionalización propia (ADR-0013); D1 trae 40/40/20 del doc.
DIMENSIONES_ITCG = {
    "reformas_economicas": {
        "nombre": "Reformas económicas fundamentales",
        "peso": 0.35,
        "indicadores": {"cepo_mulc": 0.40, "apertura_comercial": 0.40,
                        "desregulacion_normativa": 0.20},
    },
    "reforma_estado": {
        "nombre": "Reforma del Estado",
        "peso": 0.25,
        # Doc: dotación mide personas, estructura mide organigrama, gasto mide
        # magnitud fiscal, masa salarial filtra inflación — "las tres son
        # necesarias pero ninguna sola alcanza" + organismos como 4ª pata.
        "indicadores": {"reduccion_estado": 0.35, "gasto_funcionamiento": 0.25,
                        "masa_salarial": 0.20, "reestructuracion_organismos": 0.20},
    },
    "reforma_laboral": {
        "nombre": "Reforma laboral",
        "peso": 0.15,
        # ADR-0023: instrumento (Fondo de Cese, adopción) + resultado
        # (litigiosidad SRT enfriándose) — antes la dimensión descansaba en
        # un único indicador.
        #
        # ADR-0128 (2026-07-25): pasa de 70/30 a 50/50 a propuesta de la
        # revisión externa del cinturón. El argumento es conceptual y no un
        # ajuste de resultado: el par que la dimensión mide es instrumento y
        # resultado, y no hay razón para que el instrumento pese 2,3 veces al
        # resultado. Al contrario — un fondo bien construido que nadie use no
        # es una reforma laboral, y la litigiosidad es lo único que dice si
        # algo cambió en los hechos.
        #
        # HONESTIDAD SOBRE EL EFECTO: el cambio MEJORA el puntaje. La
        # litigiosidad puntúa 59,4 y el FAL 30,8, así que subirle el peso al
        # primero sube la dimensión de 39,4 a 45,1 y el ITCG de 71,7 a 72,5.
        # No se puede invocar "el efecto es neutro" como defensa. La
        # justificación es únicamente conceptual —instrumento y resultado
        # pesan igual— y viene de una revisión externa, no de mirar el número.
        # Queda escrito acá y en la ficha para que se pueda discutir.
        "indicadores": {"fal_modernizacion_laboral": 0.50,
                        "litigiosidad_laboral": 0.50},
    },
    "privatizaciones_inversion": {
        "nombre": "Privatizaciones e inversión",
        "peso": 0.15,
        "indicadores": {"privatizaciones": 0.40, "rigi_inversiones": 0.40,
                        "concesiones_infraestructura": 0.20},
    },
    "social_orden": {
        "nombre": "Reforma social y orden",
        "peso": 0.10,
        # Doc: "mide desintermediación, liberalización salud y orden público".
        # 2026-07-20 (ADR-0100): sale asistencia_directa, clavada en 100,0 desde
        # abr-2024. Los dos que quedan conservan su proporción relativa
        # (40:20 = 2:1), así que la dimensión no cambia de carácter, sólo deja
        # de arrastrar un componente sin recorrido. Antes 40/40/20.
        "indicadores": {"protocolo_antipiquetes": 0.67,
                        "libertad_opcion_salud": 0.33},
    },
}

# Interpretación (misma escala y etiquetas que el ITCM para leer los dos
# índices con la misma vara). (low, high, etiqueta).
BANDAS_INTERPRETACION = [
    (-INF, 20.0, "severamente_apretado"),
    (20.0, 40.0, "apretado"),
    (40.0, 60.0, "moderadamente_apretado"),
    (60.0, 80.0, "moderadamente_aflojado"),
    (80.0, INF, "aflojado"),
]

INTERPRETACION_LEGIBLE = {
    "severamente_apretado":   "Severamente apretado",
    "apretado":               "Apretado",
    "moderadamente_apretado": "Moderadamente apretado",
    "moderadamente_aflojado": "Moderadamente aflojado",
    "aflojado":               "Aflojado",
}

# Indicadores del cinturón que se publican pero no integran el índice.
# litigiosidad_laboral SALIÓ de contexto (ADR-0023): puntúa como resultado de
# la reforma laboral (proxy SRT — no es el canal indemnizatorio que el Fondo
# de Cese reemplaza, pero es la única serie nacional mensual y su tendencia
# ES la "industria del juicio" que el doc menciona).
# alertas_manifestacion: serie GTFS-RT en construcción (acumula desde jul-2026,
# sin baseline 2023) — candidata a automatizar protocolo_antipiquetes cuando
# tenga historia (ADR-0014).
# protestas_caba: eventos de protesta ACLED (marchas/concentraciones, no cortes)
# — el contraste con protocolo_antipiquetes es la lectura, no puntúa (ADR-0017):
# puntuar el volumen de protesta premiaría "menos marchas", que no es un
# resultado de gestión sino un derecho ejercido.
INDICADORES_CONTEXTO = ["alertas_manifestacion", "protestas_caba"]

# ── Promesas cumplidas: no puntúan, pero se muestran (ADR-0100) ─────────────
# Estado distinto de INDICADORES_CONTEXTO. ADR-0051 sacó del tablero los
# indicadores que NO miden la dimensión de su índice; éstos sí la miden, y el
# hecho de que la promesa esté cumplida es parte de lo que el informe cuenta.
# Lo que se retira es el puntaje, no la card: un indicador clavado en su máximo
# no aporta información al promedio mensual y sí infla la dimensión.
#
# `desde` es el mes en que alcanzó el máximo y dejó de moverse; se publica en
# la card para que el lector sepa por qué no cambia.
INDICADORES_CUMPLIDOS = {
    "asistencia_directa": {
        # La card se sigue mostrando DENTRO de su dimensión, no en un bloque
        # aparte: pertenece ahí y lo que cambió es que dejó de puntuar.
        "dimension": "social_orden",
        "desde": "2024-04",
        "desde_txt": "abril de 2024",
        "por_que": "La desintermediación de los planes sociales llegó al 100% del "
                   "devengado pagado directo a personas en abril de 2024 y se mantiene "
                   "desde entonces, sin variación en 27 meses. La línea de base de 2023 "
                   "ya era 98,3%: el margen para seguir informando algo nuevo estaba "
                   "agotado desde el arranque.",
    },
}


def puntaje_banda(valor: float, bandas: list) -> int:
    """Puntaje de la banda donde cae `valor` (low exclusivo, high inclusivo)."""
    return parametrica.puntaje_banda(valor, bandas)


def banda_interpretacion(itcg: float) -> str:
    return parametrica.banda_interpretacion(itcg, BANDAS_INTERPRETACION)


def tension_de_itcg(itcg: float) -> float:
    """Tensión 0-10 del cinturón (convención del informe) derivada del ITCG."""
    return parametrica.tension_de_indice(itcg)


def texto_bandas(indicador: str) -> str:
    """Texto legible de la tabla de bandas, para transparencia en el frontend."""
    return parametrica.texto_bandas(BANDAS_ITCG[indicador])


def cargar_ajustes(path, periodo: str) -> dict:
    """Overrides del analista vigentes para `periodo` (ver parametrica.cargar_ajustes)."""
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itcg(valores: dict, ajustes: dict | None = None) -> dict | None:
    """Calcula el ITCG a partir de {indicador: valor} (valores None se ignoran).

    Algoritmo común en parametrica.calcular_indice (renormalización ante
    faltantes, overrides con vencimiento); acá solo se enchufan las tablas
    del cinturón de gestión.
    """
    return parametrica.calcular_indice(
        valores, ajustes, BANDAS_ITCG, DIMENSIONES_ITCG,
        BANDAS_INTERPRETACION, INTERPRETACION_LEGIBLE)
