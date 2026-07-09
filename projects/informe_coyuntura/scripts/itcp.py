"""ITCP — Índice de Tensión del Cinturón Político (capital político según
Matus: capacidad de gobernar, NO popularidad).

ITCP = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor)), escala
0-100 donde 100 = mínima tensión (máximo capital político). Tensión 0-10 del
informe = (100 − ITCP) / 10 (motor común en parametrica.py).

A diferencia de ITCM/ITCG/ITVC, NO hay un documento CIGOB que fije los pesos
de las 5 dimensiones (imagen y voto, poder legislativo, alianzas
territoriales, cohesión interna del oficialismo, conflicto social) — ya
descriptas en docs/cinturon_politica.md pero nunca pesadas. Los pesos acá son
una decisión editorial explícita (ver ADR-0036): "imagen y voto" pesa
deliberadamente MENOS que las demás porque el propio marco del proyecto
distingue capital político de popularidad.

Bandas de cohesion_bloque (Diputados, sigue bloqueado por anti-bot, ADR-0037,
sin datos propios), adhesion_reformas_provincial y protestas_caba son
PROVISIONALES (sin serie histórica propia todavía) — ver ADR-0036, a
recalibrar cuando el backfill esté corriendo.

alineamiento_senadores_prov (2026-07-08) reemplaza a gobernadores_alineamiento
en el peso de la dimensión "alianzas_territoriales" — placeholder manual
congelado desde 2026-04, sin fuente automatizable. Su banda queda en
BANDAS_ITCP como referencia histórica (no se borra), pero ya no pondera en
DIMENSIONES_ITCP. **Sus propias anclas (distinto indicador de
gobernadores_alineamiento) ya NO son provisionales**: recalibradas 2026-07-09
con 29 puntos mensuales reales backfilleados (ver el comentario en
BANDAS_ITCP y ADR-0038) — primera banda del ITCP en salir del estado
PROVISIONAL con datos propios en vez de heredados.
`cohesion_bloque_senado` (mismo día, ADR-0039) siguió el mismo camino: sus
propias anclas (distintas de las de `cohesion_bloque` Diputados, con las que
compartía tabla sin fundamento) ya no son provisionales.

protestas_caba puntúa sobre "var_vs_2023" (% de variación de eventos de
protesta en CABA, ACLED, contra la base 2023), NO sobre "valor" — a diferencia
de todos los demás indicadores de este índice, que puntúan directo sobre su
propio "valor". "valor" en gestion.fetch_protestas_caba() es el conteo CRUDO
de eventos acumulado 12 meses (puede ser un número en cientos): una tabla de
bandas pensada para una escala 0-100 (como la de movilizacion_cepa) lo
interpretaría mal. "var_vs_2023" sí es una variación porcentual, comparable a
otros indicadores %-variación ya en BANDAS_ITCP (ej. iaf_transferencias) —
hallazgo posterior al Task 1 (bug real, no hipotético), corregido en el
wiring de main() (politica.py).
"""
import parametrica

INF = float("inf")

BANDAS_ITCP = {
    "votometro_ventaja_lla": [           # pp gap LLA-PJ, mayor = mejor
        (15.0, INF, 100), (5.0, 15.0, 85), (-5.0, 5.0, 65), (-15.0, -5.0, 40), (-INF, -15.0, 10),
    ],
    "ratio_dnu": [                        # DNUs / leyes, menor = mejor
        (-INF, 0.3, 100), (0.3, 0.7, 85), (0.7, 1.2, 65), (1.2, 2.0, 40), (2.0, INF, 10),
    ],
    "eficacia_legislativa": [             # % proyectos PE aprobados, mayor = mejor
        (55.0, INF, 100), (35.0, 55.0, 85), (15.0, 35.0, 65), (5.0, 15.0, 40), (-INF, 5.0, 10),
    ],
    "veto_quorum": [                      # % sesiones fracasadas, menor = mejor
        (-INF, 5.0, 100), (5.0, 10.0, 85), (10.0, 20.0, 65), (20.0, 30.0, 40), (30.0, INF, 10),
    ],
    "comisiones_caidas": [                # % varados (20-30% es "normal" según el doc), menor = mejor
        (-INF, 30.0, 100), (30.0, 50.0, 85), (50.0, 70.0, 65), (70.0, 85.0, 40), (85.0, INF, 10),
    ],
    "iaf_transferencias": [               # % var real YoY transferencias federales, mayor = mejor
        (10.0, INF, 100), (0.0, 10.0, 85), (-10.0, 0.0, 65), (-20.0, -10.0, 40), (-INF, -20.0, 10),
    ],
    "gobernadores_alineamiento": [        # % gobernadores alineados, mayor = mejor (manual)
        # Placeholder manual congelado desde 2026-04 (55%), retirado del peso
        # del ITCP (ver DIMENSIONES_ITCP) en favor de alineamiento_senadores_prov
        # (2026-07-08). Banda NO se borra — queda como referencia histórica,
        # mismo criterio que dejar cohesion_bloque en el código aunque el
        # scraping de Diputados esté bloqueado (ADR-0037).
        (65.0, INF, 100), (45.0, 65.0, 85), (25.0, 45.0, 65), (10.0, 25.0, 40), (-INF, 10.0, 10),
    ],
    "alineamiento_senadores_prov": [
        # RECALIBRADO 2026-07-09 con backfill real (ADR-0038): las anclas
        # 65/45/25/10 de abajo eran heredadas de gobernadores_alineamiento
        # (nunca validadas contra este indicador). Con 29 puntos mensuales
        # reales reconstruidos (feb-2024→jun-2026, ventana rolling 90d —
        # descargar_series.fetch_alineamiento_senadores_prov_mensual), el
        # rango observado es 19,4–100,0 (media 56,9, mediana 57,7): el techo
        # de 65 saturaba en 8/29 meses (28%, no un caso de borde) y el piso
        # de 10 casi no se tocaba (0/29). Anclas nuevas en 40/50/60/70
        # (números redondos, chequeados contra los 29 puntos: 6/6/6/7/4 por
        # banda, casi equidistribuido). Tramos extremos siguen ABIERTOS
        # (INF) — un tramo superior finito (70,100,100) desplazaría la
        # saturación al punto medio del motor interpolado (85 en vez de 70),
        # mismo gotcha ya documentado antes de este cambio.
        (70.0, INF, 100),
        (60.0, 70.0, 85),
        (50.0, 60.0, 65),
        (40.0, 50.0, 40),
        (-INF, 40.0, 10),
    ],
    "adhesion_reformas_provincial": [     # % provincias adheridas RIGI, mayor = mejor — PROVISIONAL
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "cohesion_bloque": [                  # índice de Rice %, mayor = mejor — PROVISIONAL
        (90.0, INF, 100), (75.0, 90.0, 85), (60.0, 75.0, 65), (40.0, 60.0, 40), (-INF, 40.0, 10),
    ],
    "cohesion_bloque_senado": [
        # RECALIBRADO 2026-07-09 con backfill real (mismo criterio que
        # alineamiento_senadores_prov, ADR-0038/0039): las anclas 90/75/60/40
        # eran una copia de cohesion_bloque (Diputados, sin datos — sigue
        # bloqueado por anti-bot, ADR-0037), nunca validadas contra la
        # cohesión real del Senado. Con 29 puntos mensuales reales
        # (feb-2024→jun-2026, ventana rolling 90d), el rango observado es
        # 77,8–100,0 (media 94,4, mediana 93,1): el techo de 90 saturaba en
        # 25/29 meses (86% — esta dimensión pesa el 20% ENTERO del ITCP
        # mientras cohesion_bloque Diputados siga sin datos, así que la
        # saturación afectaba directo a un quinto del índice). Piso de 40
        # nunca se tocó ni de cerca (mínimo real 77,8). Anclas nuevas en
        # 95/90/85/80 (chequeadas contra los 29 puntos: 12/13/3/0/1 por
        # banda — el hueco en 80-85 es real, no hay datos ahí, se deja como
        # margen hasta que aparezcan). cohesion_bloque (Diputados) NO se
        # toca: sigue con las anclas viejas hasta tener datos propios.
        (95.0, INF, 100),
        (90.0, 95.0, 85),
        (85.0, 90.0, 65),
        (80.0, 85.0, 40),
        (-INF, 80.0, 10),
    ],
    "movilizacion_cepa": [                # índice 0-100, menor = mejor
        (-INF, 20.0, 100), (20.0, 40.0, 85), (40.0, 60.0, 65), (60.0, 80.0, 40), (80.0, INF, 10),
    ],
    "protestas_caba": [                   # % var. eventos vs. base 2023 (ACLED) — PROVISIONAL
        (-INF, -30.0, 100), (-30.0, -10.0, 85), (-10.0, 10.0, 65), (10.0, 30.0, 40), (30.0, INF, 10),
    ],
}

DIMENSIONES_ITCP = {
    "poder_legislativo": {
        "nombre": "Poder legislativo",
        "peso": 0.30,
        "indicadores": {"ratio_dnu": 0.25, "eficacia_legislativa": 0.30,
                        "veto_quorum": 0.20, "comisiones_caidas": 0.25},
    },
    "alianzas_territoriales": {
        "nombre": "Alianzas territoriales",
        "peso": 0.25,
        "indicadores": {"iaf_transferencias": 0.40, "alineamiento_senadores_prov": 0.30,
                        "adhesion_reformas_provincial": 0.30},
    },
    "cohesion_interna": {
        "nombre": "Cohesión interna del oficialismo",
        "peso": 0.20,
        "indicadores": {"cohesion_bloque": 0.65, "cohesion_bloque_senado": 0.35},
    },
    "conflicto_social": {
        "nombre": "Conflicto social",
        "peso": 0.15,
        "indicadores": {"movilizacion_cepa": 0.60, "protestas_caba": 0.40},
    },
    "imagen_voto": {
        "nombre": "Imagen y voto",
        "peso": 0.10,
        "indicadores": {"votometro_ventaja_lla": 1.0},
    },
}

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


def puntaje_banda(valor: float, bandas: list) -> int:
    return parametrica.puntaje_banda(valor, bandas)


def banda_interpretacion(itcp: float) -> str:
    return parametrica.banda_interpretacion(itcp, BANDAS_INTERPRETACION)


def tension_de_itcp(itcp: float) -> float:
    return parametrica.tension_de_indice(itcp)


def texto_bandas(indicador: str) -> str:
    return parametrica.texto_bandas(BANDAS_ITCP[indicador])


def cargar_ajustes(path, periodo: str) -> dict:
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itcp(valores: dict, ajustes: dict | None = None) -> dict | None:
    """Calcula el ITCP a partir de {indicador: valor} (None se ignora)."""
    return parametrica.calcular_indice(
        valores, ajustes, BANDAS_ITCP, DIMENSIONES_ITCP,
        BANDAS_INTERPRETACION, INTERPRETACION_LEGIBLE)
