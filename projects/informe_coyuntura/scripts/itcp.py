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

Bandas de cohesion_bloque, cohesion_bloque_senado, adhesion_reformas_provincial
y protestas_caba son PROVISIONALES (sin serie histórica propia todavía) — ver
ADR-0036, a recalibrar cuando el backfill esté corriendo.

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
        (65.0, INF, 100), (45.0, 65.0, 85), (25.0, 45.0, 65), (10.0, 25.0, 40), (-INF, 10.0, 10),
    ],
    "adhesion_reformas_provincial": [     # % provincias adheridas RIGI, mayor = mejor — PROVISIONAL
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "cohesion_bloque": [                  # índice de Rice %, mayor = mejor — PROVISIONAL
        (90.0, INF, 100), (75.0, 90.0, 85), (60.0, 75.0, 65), (40.0, 60.0, 40), (-INF, 40.0, 10),
    ],
    "cohesion_bloque_senado": [           # mismo constructo que cohesion_bloque — PROVISIONAL
        (90.0, INF, 100), (75.0, 90.0, 85), (60.0, 75.0, 65), (40.0, 60.0, 40), (-INF, 40.0, 10),
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
        "indicadores": {"iaf_transferencias": 0.40, "gobernadores_alineamiento": 0.30,
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
