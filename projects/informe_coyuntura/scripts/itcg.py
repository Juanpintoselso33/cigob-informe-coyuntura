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
  * ILCE (apertura comercial): el doc define tres componentes (brecha inversa,
    alícuota efectiva, canal verde aduanero). El canal verde no tiene fuente
    pública estructurada → el ILCE se computa en gestion.py con los
    componentes disponibles, renormalizando (mismo criterio que el resto del
    informe ante faltantes).
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
    "apertura_comercial": [             # ILCE 0-100 (compuesto, calculado en gestion.py)
        # Matriz de lectura del doc: >90 economía integrada · 70-90 apertura
        # condicionada ("zona típica de transición") · <70 economía reprimida.
        (90.0, INF, 100), (80.0, 90.0, 85), (70.0, 80.0, 65), (50.0, 70.0, 40), (-INF, 50.0, 10),
    ],
    "desregulacion_normativa": [        # % de avance desregulatorio (0-100)
        # Doc: 57% de normas derogadas → 85 ("desregulación en marcha").
        (70.0, INF, 100), (50.0, 70.0, 85), (30.0, 50.0, 65), (10.0, 30.0, 40), (-INF, 10.0, 10),
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
        (-INF, -20.0, 100), (-20.0, -12.0, 85), (-12.0, -5.0, 65), (-5.0, 0.0, 40), (0.0, INF, 10),
    ],
    "reestructuracion_organismos": [    # % de avance (actos de disolución/fusión vs plan)
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "fal_modernizacion_laboral": [      # Índice de Avance del Fondo de Cese 0-100 (compuesto)
        # Reforma opt-in por CCT: 40-60 ya sería adopción masiva; <5 = solo
        # marco normativo sin adopción (la foto de la reglamentación pendiente).
        (60.0, INF, 100), (40.0, 60.0, 85), (20.0, 40.0, 65), (5.0, 20.0, 40), (-INF, 5.0, 10),
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
        (70.0, INF, 100), (50.0, 70.0, 85), (30.0, 50.0, 65), (10.0, 30.0, 40), (-INF, 10.0, 10),
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
        "indicadores": {"fal_modernizacion_laboral": 1.0},
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
        "indicadores": {"asistencia_directa": 0.40, "protocolo_antipiquetes": 0.40,
                        "libertad_opcion_salud": 0.20},
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
# litigiosidad_laboral: proxy SRT (juicios de riesgos del trabajo) — informa la
# lectura de la reforma laboral pero no es el canal indemnizatorio que el Fondo
# de Cese reemplaza, así que no puntúa.
# alertas_manifestacion: serie GTFS-RT en construcción (acumula desde jul-2026,
# sin baseline 2023) — candidata a automatizar protocolo_antipiquetes cuando
# tenga historia (ADR-0014).
INDICADORES_CONTEXTO = ["litigiosidad_laboral", "alertas_manifestacion"]


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
