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

Ninguna banda de este índice sigue PROVISIONAL desde 2026-07-09 (ver
ADR-0036 para el estado original). `adhesion_reformas_provincial` fue la
última: no había fecha de adhesión por provincia en la fuente (MAGyP), y la
alternativa con esa fecha (trivia.consejo.org.ar) devuelve "Request
Rejected" (WAF) ante fetch directo — pero investigando A MANO, provincia por
provincia, la fecha real de sanción/publicación de cada ley de adhesión
(24 puntos mensuales reales, jul-2024→jun-2026, ADR-0044), se pudo construir
la serie igual. Sus anclas (80/60/40/20) se CHEQUEARON contra esa serie y no
se tocaron -- a diferencia de las otras 4 recalibraciones de hoy, discriminan
bien en todo el rango observado (ver comentario en BANDAS_ITCP: la adhesión
es un evento irreversible, no una tasa que oscila, así que el rango de hoy es
un punto de partida en curso, no el rango final contra el que calibrar).

`protestas_caba` (2026-07-09, sin ADR propio -- recalibración menor, ver
comentario en BANDAS_ITCP) también salió de PROVISIONAL: a diferencia de
los demás, no necesitó backfill nuevo -- la serie ACLED ya tenía 102 meses
en disco. cohesion_bloque (Diputados) YA NO está bloqueado (ADR-0037 quedó
superado por ADR-0040, 2026-07-09: el endpoint PDF directo de
votaciones.hcdn.gob.ar no tiene el anti-bot de la SPA) y sus anclas tampoco
son provisionales desde el mismo día (ADR-0041/0042): recalibradas con 31
puntos mensuales reales backfilleados gracias a la caché permanente por
acta (ver el comentario en BANDAS_ITCP).

alineamiento_senadores_prov (2026-07-08) reemplaza a gobernadores_alineamiento
en el peso de la dimensión "alianzas_territoriales" — placeholder manual
congelado desde 2026-04, sin fuente automatizable. Su banda queda en
BANDAS_ITCP como referencia histórica (no se borra), pero ya no pondera en
DIMENSIONES_ITCP. **Sus propias anclas (distinto indicador de
gobernadores_alineamiento) ya NO son provisionales**: recalibradas 2026-07-09
con 29 puntos mensuales reales backfilleados (ver el comentario en
BANDAS_ITCP y ADR-0038) — primera banda del ITCP en salir del estado
PROVISIONAL con datos propios en vez de heredados.
`cohesion_bloque_senado` (mismo día, ADR-0039) y `cohesion_bloque` Diputados
(mismo día, ADR-0042) siguieron el mismo camino: sus propias anclas
(distintas entre sí, ya no comparten tabla sin fundamento) tampoco son
provisionales.

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

REVISIÓN EDITORIAL CIGOB 2026-07-10 (ADR-0048): el cinturón se acota a
capacidad de gobernar y avanzar la agenda legislativa. Tres cambios:
(1) `rotacion_gabinete` y `protestas_caba` SALEN del índice — siguen
publicándose como cards de contexto (INDICADORES_CONTEXTO, mismo patrón que
badlar en ITCM); sus bandas quedan abajo como referencia histórica.
(2) `cohesion_bloque` pasa a ser el COMPUESTO bicameral (Rice de Diputados
65% + Senado 35%, el ratio interno que ya tenían como indicadores separados)
y es el único indicador de la dimensión cohesion_interna; la banda del
compuesto se calibró contra su propia serie reconstruida (ver comentario).
(3) `cohesion_bloque_senado` deja de ser un indicador propio (absorbido por
el compuesto); su banda queda como referencia histórica, igual que
gobernadores_alineamiento.
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
    "comisiones_caidas": [
        # RECALIBRADO 2026-07-09 (auditoría adversarial del cinturón,
        # ADR-0045) con los 32 puntos mensuales reales ya existentes en
        # output/series/politica.csv (dic-2023→jul-2026): las anclas
        # anteriores (30/50/70/85, "20-30% es normal" según el doc de
        # diseño) describen un congreso de manual, no la métrica real de
        # este indicador -- con ventana móvil de 12 meses, un dictamen
        # reciente casi nunca alcanza a sancionarse dentro de SU MISMA
        # ventana, así que el piso estructural observado es 94,7 y el
        # rango real 94,7-99,8 (media 98,2). Resultado: los 32 meses
        # caían en la banda (85,inf)->10 -- tensión máxima clavada, cero
        # discriminación, exactamente la misma patología (en espejo) que
        # cohesion_bloque saturando su techo (ADR-0042). Anclas nuevas en
        # 96/97/98/99 (números redondos, chequeadas contra los 32 puntos:
        # 5/3/5/10/9 por banda, todas con datos reales). menor = mejor,
        # tramos extremos abiertos como siempre (ADR-0021).
        (-INF, 96.0, 100), (96.0, 97.0, 85), (97.0, 98.0, 65), (98.0, 99.0, 40), (99.0, INF, 10),
    ],
    "derrotas_legislativas": [
        # NUEVO 2026-07-09 (ADR-0046): derrotas legislativas consumadas del
        # Ejecutivo en ventana móvil de 12 meses — vetos insistidos por ambas
        # cámaras (art. 83 CN) + decretos DNU/delegados rechazados por al
        # menos una cámara bajo la ley 26.122. Conteo absoluto por NORMA
        # (cada derrota cuenta una vez, fechada en el mes en que se consuma);
        # menor = mejor, misma polaridad que veto_quorum/comisiones_caidas.
        # Anclas calibradas contra la serie mensual reconstruida real
        # (32 meses, dic-2023→jul-2026, eventos verificados contra InfoLeg,
        # actas del Senado y actas PDF de Diputados): valores observados
        # {0×3, 1×10, 2×7, 5×1, 6×1, 8×10} → 13/7/12/0/0 por banda. Las dos
        # bandas inferiores quedan vacías A PROPÓSITO: son el margen para
        # escenarios de confrontación aún más intensos que el pico real de
        # ago-oct 2025 (mismo criterio que el hueco documentado en
        # cohesion_bloque_senado, ADR-0039). El indicador nace SIN estado
        # provisional. Tramos extremos abiertos (ADR-0021).
        (-INF, 1.0, 100), (1.0, 3.0, 85), (3.0, 8.0, 65), (8.0, 14.0, 40), (14.0, INF, 10),
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
    "adhesion_reformas_provincial": [
        # CHEQUEADO 2026-07-09 contra 24 puntos mensuales reales (jul-2024 a
        # jun-2026, reconstruidos investigando a mano la fecha de adhesión
        # de cada provincia, ADR-0044) -- a diferencia de los otros 4
        # indicadores recalibrados hoy, acá NO se tocaron las anclas: la
        # adhesión al RIGI es un evento IRREVERSIBLE por provincia (un
        # trinquete, no una tasa que oscila), así que el rango observado
        # (4,2%–66,7%) es el arranque de un proceso todavía en curso, no una
        # muestra representativa de su rango final -- recalibrar ahora
        # anclaría las bandas a un punto de partida que se va a quedar
        # obsoleto apenas sigan adhiriendo provincias. El puntaje interpolado
        # ya discrimina de verdad en todo el rango observado (10 en jul-2024,
        # 82 en jun-2026, sin aplanarse en ningún tramo) -- las anclas
        # heredadas resultaron razonables, no hace falta cambiarlas. Vuelve
        # a evaluarse si el rango observado se estanca de forma sostenida.
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "cohesion_bloque": [
        # COMPUESTO BICAMERAL desde 2026-07-10 (ADR-0048, revisión editorial
        # CIGOB): Rice de Diputados 65% + Rice del Senado 35% (el ratio
        # interno 65/35 ≈ 45/25 que las dos cámaras ya tenían como
        # indicadores separados desde ADR-0036), renormalizado si una cámara
        # no tiene dato. Anclas calibradas contra la serie compuesta
        # reconstruida desde las dos series mensuales por cámara ya en
        # output/series/politica.csv (31 puntos, dic-2023→jun-2026, rango
        # 90,3–100,0, media 97,6): las anclas del indicador anterior
        # (99,9/99,0/98,0/97,0, calibradas para Diputados sola, ADR-0042) no
        # sirven para el compuesto — el Senado (bloque chico, un disidente
        # mueve mucho el promedio) le mete al compuesto un rango 3 veces más
        # ancho que el de Diputados sola. Anclas nuevas 99,9/99,0/97,0/95,0
        # (chequeadas contra los 31 puntos: 8/4/9/7/3 por banda, las cinco
        # con datos reales — los 8 meses en 100,0 exacto son cohesión
        # perfecta simultánea en ambas cámaras, indistinguibles entre sí por
        # diseño, mismo caveat que ADR-0042).
        (99.9, INF, 100),
        (99.0, 99.9, 85),
        (97.0, 99.0, 65),
        (95.0, 97.0, 40),
        (-INF, 95.0, 10),
    ],
    "cohesion_bloque_senado": [
        # RETIRADO como indicador propio 2026-07-10 (ADR-0048): absorbido por
        # el compuesto bicameral de cohesion_bloque (35% interno). La banda
        # queda como referencia histórica (mismo criterio que
        # gobernadores_alineamiento) — ya no pondera en DIMENSIONES_ITCP.
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
        # margen hasta que aparezcan). cohesion_bloque (Diputados) en ese
        # momento NO se tocó, seguía con las anclas viejas -- recalibrada
        # unas horas después, mismo día, ver comentario propio más arriba
        # (ADR-0041/0042).
        (95.0, INF, 100),
        (90.0, 95.0, 85),
        (85.0, 90.0, 65),
        (80.0, 85.0, 40),
        (-INF, 80.0, 10),
    ],
    "rotacion_gabinete": [
        # FUERA DEL ÍNDICE desde 2026-07-10 (ADR-0048, revisión editorial
        # CIGOB: "no sería pertinente en este cinturón") — sigue publicándose
        # como card de contexto (INDICADORES_CONTEXTO); banda de referencia.
        # Salidas de rango ministerial (JGM + ministros) acumuladas en
        # ventana móvil de 12 meses, desde el registro curado
        # data/politica/gabinete_salidas.json (ADR-0047) — menor = mejor.
        # Pata EJECUTIVA de la dimensión cohesion_interna, que hasta
        # 2026-07-09 era 100% legislativa (Diputados+Senado). Anclas
        # calibradas contra la serie real reconstruida completa (32 puntos,
        # dic-2023→jul-2026, rango 0-7): distribución por banda 7/8/9/6/2,
        # las CINCO bandas pobladas con datos reales (criterio ADR-0042 —
        # nace discriminando, a diferencia de cohesion_bloque que nació
        # saturado y hubo que recalibrar). Cuenta salidas políticas Y
        # estructurales-electorales sin distinguir (la composición se
        # publica; el caso extremo se administra por override en
        # ajustes_itcp.json). Tramos extremos abiertos (ADR-0021): >7
        # salidas satura en 10 sin romperse.
        (-INF, 1.0, 100),   # 0-1: recambio fisiológico
        (1.0, 2.0, 85),     # 2: recambio bajo
        (2.0, 4.0, 65),     # 3-4: rotación sostenida
        (4.0, 6.0, 40),     # 5-6: crisis de gabinete
        (6.0, INF, 10),     # 7+: crisis abierta
    ],
    "movilizacion_cepa": [                # índice 0-100, menor = mejor
        (-INF, 20.0, 100), (20.0, 40.0, 85), (40.0, 60.0, 65), (60.0, 80.0, 40), (80.0, INF, 10),
    ],
    "protestas_caba": [
        # FUERA DEL ÍNDICE desde 2026-07-10 (ADR-0048, revisión editorial
        # CIGOB: "no sería pertinente en este cinturón") — sigue publicándose
        # como card de contexto (INDICADORES_CONTEXTO); banda de referencia.
        # RECALIBRADO 2026-07-09 con la serie ACLED ya existente (102 meses
        # en output/series/gestion.csv desde 2017, sin backfill nuevo --
        # solo hubo que reconstruir var_vs_2023 mes a mes con la misma
        # fórmula de gestion.fetch_protestas_caba(): rolling 12m / total
        # 2023 − 1). Las anclas -30/-10/10/30 (simétricas, nunca validadas)
        # eran demasiado anchas para el rango real observado: con 30 puntos
        # mensuales válidos (dic-2023→may-2026, primer mes en que la
        # ventana de 12m ya no se solapa con el propio 2023 parcial), el
        # rango es -10,0 a +25,4 -- 22 de 30 meses (73%) caían todos en la
        # misma banda "moderado" (65), aplanando el puntaje justo donde más
        # variación real hay. Anclas nuevas en -6,0/-3,0/0,0/10,0
        # (chequeadas contra los 30 puntos: 5/5/7/6/7 por banda, todas con
        # datos reales, sin huecos).
        (-INF, -6.0, 100), (-6.0, -3.0, 85), (-3.0, 0.0, 65), (0.0, 10.0, 40), (10.0, INF, 10),
    ],
}

DIMENSIONES_ITCP = {
    "poder_legislativo": {
        "nombre": "Poder legislativo",
        "peso": 0.30,
        # Pesos internos redistribuidos 2026-07-09 al entrar
        # derrotas_legislativas (antes 25/30/20/25, ADR-0046): eficacia sigue
        # primera (la medida más abarcativa de capacidad legislativa); las
        # derrotas entran al nivel de ratio_dnu/comisiones porque son la
        # expresión más directa del balance de poder Ejecutivo-Congreso (con
        # ratio_dnu forman el par "gobernar por decreto / sostener la norma
        # propia"); veto_quorum cede más por ser la medida más estrecha (solo
        # sesiones fracasadas de una cámara).
        "indicadores": {"ratio_dnu": 0.20, "eficacia_legislativa": 0.25,
                        "veto_quorum": 0.15, "comisiones_caidas": 0.20,
                        "derrotas_legislativas": 0.20},
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
        # 2026-07-10 (ADR-0048): la dimensión queda en un solo indicador — el
        # compuesto bicameral (Diputados 65% + Senado 35% adentro de la
        # fórmula). rotacion_gabinete (que había entrado el 09-jul por
        # ADR-0047) sale del índice por la revisión editorial; los pesos
        # ENTRE dimensiones (ADR-0036) no se tocan.
        "indicadores": {"cohesion_bloque": 1.0},
    },
    "conflicto_social": {
        "nombre": "Conflicto social",
        "peso": 0.15,
        # 2026-07-10 (ADR-0048): protestas_caba sale del índice por la
        # revisión editorial — movilizacion_cepa queda sola en la dimensión.
        "indicadores": {"movilizacion_cepa": 1.0},
    },
    "imagen_voto": {
        "nombre": "Imagen y voto",
        "peso": 0.10,
        "indicadores": {"votometro_ventaja_lla": 1.0},
    },
}

# Indicadores de política que se publican pero NO integran el índice
# (ADR-0048, revisión editorial CIGOB 2026-07-10) — mismo patrón que
# itcm.INDICADORES_CONTEXTO (badlar y los monetarios nominales) y que
# protestas_caba en gestión: la card sigue, el puntaje no.
INDICADORES_CONTEXTO = ["rotacion_gabinete", "protestas_caba"]

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
