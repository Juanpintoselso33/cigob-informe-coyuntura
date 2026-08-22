"""ITCP — Índice de Tensión del Cinturón Político (capital político según
Matus: capacidad de gobernar, NO popularidad).

ITCP = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor)), escala
0-100 donde 100 = mínima tensión (máximo capital político). Tensión 0-10 del
informe = (100 − ITCP) / 10 (motor común en parametrica.py).

A diferencia de ITCM/ITCG/ITVC, NO hay un documento CIGOB que fije los pesos.
Las cinco dimensiones originales —imagen y voto, poder legislativo, alianzas
territoriales, cohesión interna del oficialismo y conflicto social— estaban
descriptas en docs/archivo/cinturon_politica.md pero nunca pesadas. ADR-0036
fijó esa primera paramétrica; ADR-0088 y ADR-0126 incorporaron sector privado
y poder judicial. La composición vigente de siete dimensiones vive en
DIMENSIONES_ITCP.

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
(1) `rotacion_gabinete` y `protestas_caba` SALEN del índice Y del tablero —
se siguen relevando y cacheando (INDICADORES_CONTEXTO), pero publicar.py
los oculta del snapshot, mismo patrón que badlar en ITCM (ADR-0022); sus
bandas quedan abajo como referencia histórica.
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
        # CONCEPTUAL (ADR-0121): la ventaja electoral se ancla en el CERO —empate
        # técnico entre el oficialismo y el PJ, el valor con significado propio— y
        # los cortes son márgenes simétricos redondos (±5, ±15 pp), no el rango
        # observado del período.
        (15.0, INF, 100), (5.0, 15.0, 85), (-5.0, 5.0, 65), (-15.0, -5.0, 40), (-INF, -15.0, 10),
    ],
    "cobertura_judicial": [              # % de cargos de juez con juez designado
        # CONCEPTUAL (ADR-0126): los cortes son niveles redondos de cobertura de
        # un cuerpo, con lectura propia y sin referencia al rango observado —
        # >90 banca completa · 80-90 buena · 70-80 aceptable · 60-70 deficitaria
        # · ≤60 crítica. NO se calibraron contra el período: hacerlo habría
        # anclado la escala a un tramo (64-73%) que es desempeño real y bajo,
        # y eso es exactamente lo que ADR-0045 prohíbe.
        #
        # Consecuencia asumida: en los 32 meses reconstruidos sólo se pueblan
        # dos bandas (60-70 y 70-80). No es un defecto de calibración sino el
        # hallazgo — la cobertura de la justicia argentina no estuvo cerca de
        # 80% en todo el período. El puntaje interpolado igual discrimina en
        # todo el recorrido (34,5 en el piso de may-2026 a 59,4 en dic-2023).
        (90.0, INF, 100), (80.0, 90.0, 85), (70.0, 80.0, 65),
        (60.0, 70.0, 40), (-INF, 60.0, 10),
    ],
    "produccion_legislativa": [      # leyes sancionadas en 12m, MAYOR = mejor
        # EXTERNA (ADR-0168, criterio de ADR-0105): el techo es el **promedio
        # histórico de 74,4 leyes por año** de los 18 años completos que trae el
        # dataset de HCDN (2008-2025, 1.340 leyes, cuatro presidencias). No es
        # el rango observado bajo esta administración —15 a 47— sino una
        # referencia ajena al período medido, que es lo que ADR-0045 exige.
        #
        # Mide el DENOMINADOR de la agenda común, no el cociente. ADR-0137
        # midió que el cociente se mueve por abajo: el numerador —leyes de
        # origen Ejecutivo— es estable entre 5 y 10 en todo el período, y lo
        # que se derrumbó fue la producción propia del Congreso. Puntuar el
        # cociente publicaría "el Ejecutivo domina la agenda" exactamente
        # cuando lo que pasó es que el Congreso dejó de sancionar. El cociente
        # sobrevive en el modal como lectura de composición.
        (74.0, INF, 100), (50.0, 74.0, 85), (35.0, 50.0, 65),
        (20.0, 35.0, 40), (-INF, 20.0, 10),
    ],
    "judicializacion": [             # densidad cautelar %, MENOR = mejor
        # HISTORIA LARGA (ADR-0168): el techo es el **0,78% promedio de
        # 2016-2019**, dos gobiernos anteriores al medido, contra 1,66% del
        # promedio 2020-2026. El quiebre estructural está en la serie y las
        # anclas se apoyan en el tramo previo, no en el actual.
        #
        # Serie anual: sumarios con "medida cautelar" sobre el total, ambos
        # restringidos a jurisdicción Federal + Nacional (ADR-0135). La
        # normalización es lo que la vuelve usable — el conteo crudo va de 69 a
        # 350 y eso es volumen editorial de SAIJ, no cautelares.
        (-INF, 0.8, 100), (0.8, 1.2, 85), (1.2, 1.6, 65),
        (1.6, 2.0, 40), (2.0, INF, 10),
    ],
    "velocidad_resolucion": [        # tasa resueltos/ingresos %, MENOR = mejor
        # VALOR CON SIGNIFICADO PROPIO (ADR-0168, segundo escalón de ADR-0105):
        # el 100% es el punto donde la Corte resuelve exactamente lo que le
        # entra — no acumula atraso ni lo descarga. Los cortes son márgenes
        # redondos alrededor de ese valor, no el rango observado (26 a 142).
        #
        # OJO CON EL SIGNO, y está asumido: una Corte más lenta le da MÁS
        # puntaje al Gobierno, porque el ITCP mide capacidad de gobernar sin
        # fricción (ADR-0048), no salud institucional. Es la misma incomodidad
        # que ADR-0090 resolvió para ratio_dnu y por la misma vía: el signo
        # sale de la pregunta declarada, no de si el resultado agrada.
        (-INF, 40.0, 100), (40.0, 70.0, 85), (70.0, 100.0, 65),
        (100.0, 130.0, 40), (130.0, INF, 10),
    ],
    "paralisis_denuncias": [         # sesiones de las 2 comisiones en 12m, MENOR = mejor
        # CONCEPTUAL (ADR-0168): cortes redondos sobre sesiones por año de dos
        # comisiones —una por semestre cada una, una por trimestre, una por
        # bimestre— no calibrados contra el rango observado (2 a 7).
        #
        # Mide sesiones de AMBAS comisiones, no de Disciplina sola: ADR-0166
        # había derivado lo segundo, y los datos crudos lo desmienten —
        # Disciplina tiene 8 sesiones en cuatro años, o sea un indicador de
        # evento, que es justamente la clase que ADR-0147 dejó suspendida.
        (-INF, 2.0, 100), (2.0, 4.0, 85), (4.0, 6.0, 65),
        (6.0, 9.0, 40), (9.0, INF, 10),
    ],
    "desafios_legislativos": [
        # normas propias desafiadas en el recinto (12m), MENOR = mejor. ADR-0089.
        #
        # Reemplaza el puntaje de derrotas_legislativas, que correlacionaba
        # −0,984 con el bloqueo: desde mar-2025 los dos son mes a mes el mismo
        # número (16 lecturas seguidas). No por construcción —difieren en 2024,
        # cuando el rechazo de una sola cámara al DNU 70/2023 era derrota
        # política sin matar la norma— sino de hecho, en el régimen actual.
        #
        # Anclas sobre el conteo observado (4 a 13 desafíos en 22 meses) leído
        # contra el sentido institucional del acto: desafiar una norma del
        # Ejecutivo en el recinto es excepcional —requiere insistencia de veto
        # con dos tercios o el procedimiento de la ley 26.122—, así que un
        # puñado al año ya es conflicto abierto. Hasta 2 en doce meses es el
        # funcionamiento normal de un Congreso que no confronta; más de 12 es
        # la ola de sep-oct 2025, el máximo del período.
        (-INF, 2.0, 100), (2.0, 5.0, 85), (5.0, 9.0, 65), (9.0, 12.0, 40), (12.0, INF, 10),
    ],
    "brecha_obra_publica": [
        # pp de brecha (saldo obra pública − saldo obra privada, 12m móviles),
        # mayor = mejor. ADR-0088.
        #
        # Anclas en números redondos alrededor del CERO, que es el punto con
        # significado propio: brecha nula = las empresas que dependen del Estado
        # esperan lo mismo que sus pares privadas, o sea que el gobierno no es
        # una fuente diferencial de incertidumbre para ellas. No se calibra
        # contra el rango observado — el criterio de ADR-0045 sólo autoriza eso
        # cuando el extremo es matemáticamente inalcanzable, y acá no lo es: la
        # brecha ya tocó +44,8 y −39,9 en lecturas mensuales.
        #
        # Contra la serie de diez años (100 puntos, nov-2017→ago-2026) las
        # bandas discriminan bien: 2024 (−29,8, el piso de toda la serie, año
        # del corte de obra pública) cae en el tramo de 10; 2019 (−13,2, plena
        # recesión pero sin conflicto Estado-contratistas) cae en 40; y
        # 2021-2023, con obra pública activa, quedan entre 65 y 85.
        (10.0, INF, 100), (0.0, 10.0, 85), (-10.0, 0.0, 65), (-20.0, -10.0, 40), (-INF, -20.0, 10),
    ],
    "apoyo_empresario": [
        # Saldo de postura de AEA y UIA hacia el Ejecutivo nacional, 12m
        # móviles: (apoyos − críticas) / (apoyos + críticas). Mayor = mejor.
        # ADR-0150.
        #
        # Las anclas parten el rango TEÓRICO del indicador (−1 a +1) en cinco
        # tramos iguales de 0,4, centrados en el CERO, que es el punto con
        # significado propio: saldo nulo = las cámaras apoyan tanto como
        # critican, o sea que el Gobierno no tiene ni respaldo ni
        # enfrentamiento netos del empresariado organizado.
        #
        # No se calibran contra el rango observado. ADR-0045 sólo autoriza eso
        # cuando el extremo es matemáticamente inalcanzable, y acá no lo es:
        # ±1 es «los pronunciamientos de doce meses todos en el mismo sentido»,
        # que con n≈6 por ventana ocurre sin nada extraordinario. Que la serie
        # de 32 meses se mueva entre −0,667 y +0,333 sin tocar los extremos es
        # desempeño real, no un techo de construcción.
        (0.6, INF, 100), (0.2, 0.6, 85), (-0.2, 0.2, 65), (-0.6, -0.2, 40), (-INF, -0.6, 10),
    ],
    "ratio_dnu": [
        # ADR-0058 cambió la ventana (año calendario → móvil de 365 días) SIN
        # tocar estas anclas (ADR-0059 revirtió una recalibración de un día:
        # ver ese ADR — a diferencia de comisiones_caidas/ADR-0045, acá el
        # rango elevado observado bajo este gobierno es señal real, no un
        # artefacto estructural de la ventana, y las anclas 0.3/0.7/1.2/2.0
        # están ancladas a un benchmark histórico externo real, no a un doc
        # sin fundamento: ACIJ (2011-2024, CFK+Macri+AF+primer año Milei)
        # midió 344 DNU / 1.058 leyes ≈ 0,33 — "cada 3 leyes, 1 DNU" — casi
        # exactamente el corte de 0,3 para el puntaje máximo).
        (-INF, 0.3, 100), (0.3, 0.7, 85), (0.7, 1.2, 65), (1.2, 2.0, 40), (2.0, INF, 10),
    ],
    "eficacia_legislativa": [
        # ADR-0061 (2026-07-15) reemplaza la métrica Y las anclas de ADR-0050:
        # el numerador pasó de "sancionado dentro de la MISMA ventana de 365
        # días que la publicación" (sesgo estructural real, pero ADR-0050 lo
        # sobreestimó sin verificarlo contra ningún caso externo) a "cohorte
        # MADURA (publicada hace 365-730 días) sancionada alguna vez" — saca
        # el sesgo de raíz en vez de compensarlo con anclas más generosas.
        # Con la métrica nueva, el rango real observado (32 meses,
        # dic-2023→jul-2026) es 0-14,8% (mediana 6,5%) — YA SIN el sesgo de
        # ventana compartida, y sigue muy por debajo de cualquier antecedente
        # histórico: Directorio Legislativo mide 40-50% para Macri (gobierno
        # en minoría, sin mayoría propia), 63-67% para Alberto Fernández y
        # 75-82% para los mandatos de CFK con mayoría. Las anclas usan esos
        # tramos históricos como referencia externa (no el rango de esta
        # gestión): >50 (rango CFK/AF) → 100; 30-50 (rango Macri, gobierno
        # funcional en minoría) → 85; 15-30 → 65; 5-15 (la mitad de los 32
        # puntos reales cae acá) → 40; ≤5 (la otra mitad) → 10. Que el 100%
        # de la serie real quede en las dos bandas del piso es intencional:
        # refleja que esta gestión está muy por debajo de cualquier gobierno
        # argentino post-1983 medido con esta vara, no un error de escala.
        # mayor = mejor, tramos extremos abiertos (ADR-0021).
        (50.0, INF, 100), (30.0, 50.0, 85), (15.0, 30.0, 65), (5.0, 15.0, 40), (-INF, 5.0, 10),
    ],
    "veto_quorum": [                      # % sesiones fracasadas, menor = mejor
        # CONCEPTUAL (ADR-0121): el ancla es el CERO —ninguna sesión caída por
        # falta de quórum, el Congreso funcionando— y los cortes son tasas de
        # fracaso redondas (5/10/20/30%). No se calibra contra el rango observado:
        # 0% es el ideal institucional con significado propio, no el mínimo visto.
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
        # CONCEPTUAL (ADR-0121): variación real interanual anclada en el CERO
        # —transferencias a provincias mantenidas en términos reales— con cortes
        # simétricos redondos de a 10 pp, mismo criterio que recaudacion/emae en
        # el ITCM (ADR-0120). La serie propia es anual desde 2018 (cinco puntos
        # previos, ADR-0065/0066): insuficiente para anclar a la historia, pero
        # el cero no lo necesita — es un umbral con significado, no un percentil.
        (10.0, INF, 100), (0.0, 10.0, 85), (-10.0, 0.0, 65), (-20.0, -10.0, 40), (-INF, -20.0, 10),
    ],
    "bloqueo_sostenido": [
        # NUEVO 2026-07-16 (ADR-0069): % de normas propias DESAFIADAS en el
        # recinto (insistencias de veto votadas + validez de decretos votada
        # bajo la ley 26.122) que el Ejecutivo mantuvo en pie, ventana móvil
        # de 12 meses. Es el espejo de derrotas_legislativas: aquél cuenta
        # las derrotas consumadas en términos absolutos y nunca acredita los
        # bloqueos GANADOS — un gobierno que sostiene 6 vetos desafiados
        # puntúa igual que uno al que nadie desafió. Éste mide la TASA de
        # supervivencia sobre el total de desafíos (capacidad de bloqueo:
        # el recurso de poder central de un Ejecutivo sin mayoría, que
        # gobierna sosteniendo el tercio del art. 83 CN y la vigencia de
        # sus decretos). Anclas con referencia externa, no el rango propio:
        # entre 2003 y 2025 NINGÚN veto presidencial fue insistido por el
        # Congreso (tasa histórica de sostenimiento ~100%, incluso en los
        # gobiernos en minoría de Macri), así que ≥90 = dominio normal del
        # bloqueo; 75-90 = bloqueo firme con derrotas puntuales (el H2-2024
        # real de esta gestión: 75%); 50-75 = bloqueo disputado (ago-sep
        # 2025: 54,5/53,8%); 25-50 = minoría en jaque (oct-2025: 33%); <25 =
        # bloqueo perdido (jul-2026: 20%, la resaca de la ventana).
        # mayor = mejor, tramos extremos abiertos (ADR-0021).
        # Limitación declarada (ficha): la ventana de 12m retiene las caídas
        # durante un año — la recuperación del bloqueo tras una crisis
        # aparece con rezago, y un período sin desafíos votados no genera
        # dato (el motor renormaliza, igual que veto_quorum entre períodos).
        (90.0, INF, 100), (75.0, 90.0, 85), (50.0, 75.0, 60), (25.0, 50.0, 35), (-INF, 25.0, 10),
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
        # FUERA DEL ÍNDICE Y DEL TABLERO desde 2026-07-10 (ADR-0048,
        # revisión editorial CIGOB: "no sería pertinente en este cinturón")
        # — se sigue relevando (INDICADORES_CONTEXTO, oculto del snapshot
        # por publicar.py); banda de referencia.
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
    "movilizacion_cepa": [
        # FUERA DEL ÍNDICE Y DEL TABLERO desde 2026-07-11 (ADR-0052) — se
        # sigue relevando (INDICADORES_CONTEXTO, oculto del snapshot por
        # publicar.py) como contraste del indicador que lo reemplaza
        # (conflictividad_nacional); banda de referencia. Dos razones,
        # verificadas en vivo 2026-07-11: (1) SIN BACKFILL POSIBLE — CEPA
        # publica informes de conflictividad recién desde fines de 2025 (40
        # páginas escaneadas: ~4 informes, 2 usables) y era el único
        # indicador puntuante sin serie desde dic-2023; (2) FÓRMULA NO
        # COMPARABLE MES A MES — "conflictos acumulados desde inicios del
        # año" crece mecánicamente con el calendario y se resetea en enero,
        # sobre un máximo de referencia arbitrario (200), extraído por
        # regex de la prosa del informe. índice 0-100, menor = mejor.
        (-INF, 20.0, 100), (20.0, 40.0, 85), (40.0, 60.0, 65), (60.0, 80.0, 40), (80.0, INF, 10),
    ],
    "conflictividad_nacional": [
        # NUEVO 2026-07-11 (ADR-0052): % de variación de eventos de
        # protesta y disturbios (Protests+Riots, ACLED) en TODO el país —
        # acumulado 12 meses completos contra el total 2023 (2.605
        # eventos; CABA, lo que medía protestas_caba, es ~9% del país).
        # Reemplaza a movilizacion_cepa como única pata de la dimensión
        # conflicto_social. menor = mejor (menos conflicto que en 2023 =
        # menos tensión), misma polaridad que tenía protestas_caba.
        # Anclas calibradas contra la serie reconstruida real (30 puntos,
        # dic-2023→may-2026, excluido el mes parcial del archivo; rango
        # −34,2 a +2,7, mediana −27,8): −32/−29/−26/−15, chequeadas contra
        # los 30 puntos: 5/7/8/4/6 por banda, las cinco pobladas y cada
        # corte en un hueco real de los datos. La historia que cuenta la
        # serie se verificó contra prensa (ADR-0052): caída 2024 (−27,7%
        # en dic-24 ≈ el −27% del balance oficial de bloqueos), meseta
        # 2025, reaceleración feb-may 2026 (4° paro general 19-feb, paro
        # docente 2-mar, marchas 30-abr, pico may-2026). Cobertura ACLED
        # pre-2020 NO confiable (expansión de cobertura): no se usa ni
        # para calibrar ni para el gráfico. Tramos extremos abiertos
        # (ADR-0021).
        (-INF, -32.0, 100),
        (-32.0, -29.0, 85),
        (-29.0, -26.0, 65),
        (-26.0, -15.0, 40),
        (-15.0, INF, 10),
    ],
    "jornadas_individuales_no_trabajadas_12m": [
        # ADR-0233: intensidad laboral oficial, huelguistas × duración del
        # paro, acumulada en doce meses. Menor = mejor. Anclas externas al
        # mandato, fijadas sobre los 17 años completos 2006-2022: 5,0 / 6,5 /
        # 8,0 / 10,0 millones dejan 4/2/4/3/4 años en las cinco bandas. No se
        # calibran contra 2024-2026 ni se normalizan por el resultado actual.
        (-INF, 5_000_000.0, 100),
        (5_000_000.0, 6_500_000.0, 85),
        (6_500_000.0, 8_000_000.0, 65),
        (8_000_000.0, 10_000_000.0, 40),
        (10_000_000.0, INF, 10),
    ],
    "protestas_caba": [
        # FUERA DEL ÍNDICE Y DEL TABLERO de política desde 2026-07-10
        # (ADR-0048: "no sería pertinente en este cinturón") — se sigue
        # relevando (INDICADORES_CONTEXTO, oculto del snapshot por
        # publicar.py; en gestión también dejó de ser card visible por
        # ADR-0051 — seguimiento interno en ambos cinturones; su sucesor
        # puntuante en política es conflictividad_nacional, ADR-0052);
        # banda de referencia.
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
        # 0.30 → 0.25 (2026-07-19, ADR-0088): entra la dimensión sector_privado
        # con 0.15 y las cinco existentes ceden proporcionalmente. Es el primer
        # cambio de pesos ENTRE dimensiones desde ADR-0036: la auditoría externa
        # del cinturón encontró que de los tres actores del objetivo declarado
        # —legisladores, gobernadores, empresarios— el tercero no tenía ningún
        # indicador, y llamó a eso "la recomendación de mayor prioridad de todo
        # el documento". El orden relativo de las cinco se conserva intacto.
        "peso": 0.21,   # 0.25 → 0.21 (ADR-0126)
        # Pesos internos redistribuidos 2026-07-16 al entrar bloqueo_sostenido
        # (ADR-0069): cada indicador cede 0.05 y el nuevo toma 0.20 — la
        # dimensión gana la cara ganada del bloqueo (derrotas solo cuenta la
        # perdida) sin tocar los pesos ENTRE dimensiones (ADR-0036). El orden
        # relativo previo se conserva: eficacia sigue primera (la medida más
        # abarcativa, ADR-0061/0062/0063), ratio_dnu/derrotas/bloqueo quedan
        # parejos ("gobernar por decreto / perder la norma / sostener la
        # norma"), veto_quorum sigue último por ser la medida más estrecha.
        # Antes 25/30/20/25 (2026-07-15, salida de comisiones_caidas por
        # ADR-0064; antes de eso 20/25/15/20/20, ADR-0046).
        # 2026-07-19 (ADR-0089): derrotas_legislativas sale del índice y entra
        # desafios_legislativos en su lugar. El par (derrotas, bloqueo)
        # correlacionaba −0,984 y se llevaba el 40% de la dimensión para medir
        # una sola cosa. El par nuevo
        # baja a 30% combinado y el peso liberado va a las dos medidas más
        # abarcativas; veto_quorum NO sube, porque su 0% actual dice más sobre
        # cuántas sesiones se convocaron que sobre ausencia de conflicto.
        # Antes 20/25/15/20/20.
        # 2026-07-31 (ADR-0168): entra `produccion_legislativa` con 0.15 y los
        # cinco existentes ceden proporcionalmente (×0.85), de modo que el orden
        # relativo entre ellos no se toca — mismo procedimiento que usó ADR-0069
        # al entrar bloqueo_sostenido. Mide el DENOMINADOR de la agenda común:
        # cuántas leyes sanciona el Congreso, que es el número que efectivamente
        # se mueve (15 a 47), no el cociente, que sube cuando el Congreso
        # produce menos y admite dos lecturas opuestas (ADR-0137).
        "indicadores": {"ratio_dnu": 0.20, "eficacia_legislativa": 0.27,
                        "veto_quorum": 0.13, "desafios_legislativos": 0.13,
                        "bloqueo_sostenido": 0.12,
                        "produccion_legislativa": 0.15},
    },
    "alianzas_territoriales": {
        "nombre": "Alianzas territoriales",
        "peso": 0.19,   # 0.25 → 0.22 (ADR-0088) → 0.19 (ADR-0126)
        "indicadores": {"iaf_transferencias": 0.40, "alineamiento_senadores_prov": 0.30,
                        "adhesion_reformas_provincial": 0.30},
    },
    "cohesion_interna": {
        "nombre": "Cohesión interna del oficialismo",
        "peso": 0.15,   # 0.20 → 0.18 (ADR-0088) → 0.15 (ADR-0126)
        # 2026-07-10 (ADR-0048): la dimensión queda en un solo indicador — el
        # compuesto bicameral (Diputados 65% + Senado 35% adentro de la
        # fórmula). rotacion_gabinete (que había entrado el 09-jul por
        # ADR-0047) sale del índice por la revisión editorial; los pesos
        # ENTRE dimensiones (ADR-0036) no se tocan.
        "indicadores": {"cohesion_bloque": 1.0},
    },
    "conflicto_social": {
        "nombre": "Conflicto social",
        "peso": 0.10,   # 0.15 → 0.12 (ADR-0088) → 0.10 (ADR-0126)
        # 2026-07-11 (ADR-0052): conflictividad_nacional (ACLED país
        # entero, 30 puntos reales) reemplaza a movilizacion_cepa (2
        # puntos, acumulado YTD no comparable, sin backfill posible), que
        # pasa a seguimiento interno. Antes: 2026-07-10 (ADR-0048)
        # protestas_caba había salido por la revisión editorial y CEPA
        # había quedado solo. ADR-0233 agrega la intensidad laboral oficial:
        # ACLED conserva 60% por cubrir protesta y disturbios en toda la calle;
        # las jornadas individuales no trabajadas reciben 40% por agregar
        # tamaño × duración con una serie oficial desde 2006. Los pesos ENTRE
        # dimensiones no se tocan.
        "indicadores": {"conflictividad_nacional": 0.60,
                        "jornadas_individuales_no_trabajadas_12m": 0.40},
    },
    "imagen_voto": {
        "nombre": "Imagen y voto",
        "peso": 0.07,   # 0.10 → 0.08 (ADR-0088) → 0.07 (ADR-0126)
        "indicadores": {"votometro_ventaja_lla": 1.0},
    },
    "poder_judicial": {
        "nombre": "Poder judicial",
        "peso": 0.15,
        # Dimensión nueva 2026-07-25 (ADR-0126), a partir del aporte externo
        # sobre el cinturón político. Cierra el mismo tipo de hueco que ADR-0088
        # cerró con el sector privado: el índice medía en detalle al Congreso y
        # a los gobernadores y no medía en absoluto al Poder Judicial, que es un
        # actor de veto de primer orden sobre la agenda del Gobierno.
        #
        # Entra con 0,15 —igual que sector_privado— y las seis dimensiones
        # existentes ceden PROPORCIONALMENTE (×0,85), de modo que el orden
        # relativo entre ellas no se toca. Es el segundo cambio de pesos entre
        # dimensiones desde ADR-0036 y sigue el precedente de ADR-0088.
        #
        # Arranca con un solo indicador y eso es una limitación real, no un
        # diseño terminado: la cobertura de cargos mide la CAPACIDAD de integrar
        # el Poder Judicial, no su comportamiento (cautelares contra el Estado,
        # velocidad de resolución, criterio jurisprudencial). El aporte externo
        # propone cinco indicadores más para este bloque; todos dependen de un
        # protocolo de codificación de contenido que todavía no existe.
        # 2026-07-31 (ADR-0168): la dimensión deja de tener un solo indicador.
        # ADR-0126 había dejado escrito que uno solo "es una limitación real, no
        # un diseño terminado": la cobertura mide la CAPACIDAD de integrar el
        # Poder Judicial, no su COMPORTAMIENTO. Entran los tres que ADR-0135 y
        # ADR-0139 dejaron construibles y ADR-0166 desbloqueó al fijar la
        # orientación.
        #
        # cobertura_judicial conserva el peso mayor (0.40) por ser el único
        # mensual y el de menor rezago (1 mes contra 6-18 de los otros tres);
        # los tres nuevos entran parejos en 0.20, sin razón para ordenarlos
        # entre sí — mismo criterio que ADR-0074 usó al repartir la dimensión
        # de financiamiento.
        "indicadores": {"cobertura_judicial": 0.40,
                        "judicializacion": 0.20,
                        "velocidad_resolucion": 0.20,
                        "paralisis_denuncias": 0.20},
    },
    "sector_privado": {
        "nombre": "Sector privado",
        "peso": 0.13,   # 0.15 → 0.13 (ADR-0126)
        # Dimensión nueva 2026-07-19 (ADR-0088). Cierra el hueco que la
        # auditoría externa marcó como prioridad 1: el cinturón medía en
        # detalle al Congreso, de forma indirecta a los gobernadores y no
        # medía en absoluto a los empresarios, que son el tercer actor del
        # objetivo declarado.
        #
        # 2026-07-27 (ADR-0150): entra `apoyo_empresario` y la dimensión deja
        # de tener un solo indicador. ADR-0088 había dejado escrito que uno
        # solo "es una limitación real, no un diseño terminado": la brecha de
        # obra pública mide UN canal de conflicto —el gasto en
        # infraestructura— y es ciega a una pelea con el agro, la energía o
        # los bancos.
        #
        # 50/50 porque miden cosas distintas y ninguna domina a la otra:
        #   brecha_obra_publica  es una medida REVELADA (lo que las empresas
        #     esperan, dato duro del INDEC validado contra Construya r=+0,79),
        #     pero de un solo sector;
        #   apoyo_empresario     es una medida DECLARADA (lo que las cámaras
        #     dicen por escrito y con firma), directa sobre la relación con el
        #     Ejecutivo y sobre cualquier tema, pero de sólo dos cámaras y con
        #     codificación humana en el medio.
        # Revelada vs. declarada, angosta vs. ancha: el empate es el reparto
        # honesto. El peso se fijó antes de mirar su efecto sobre el ITCP,
        # como exige ADR-0045.
        "indicadores": {"brecha_obra_publica": 0.5, "apoyo_empresario": 0.5},
    },
}

# Indicadores de política que NO integran el índice (rotación y protestas:
# ADR-0048, revisión editorial CIGOB 2026-07-10; movilizacion_cepa:
# ADR-0052, 2026-07-11) — mismo patrón que itcm.INDICADORES_CONTEXTO
# (badlar y los monetarios nominales, ADR-0022): se siguen relevando y
# cacheando como seguimiento interno, pero publicar.py los OCULTA del
# snapshot (POLITICA_OCULTOS) — el tablero solo muestra lo que integra
# las dimensiones.
INDICADORES_CONTEXTO = ["rotacion_gabinete", "protestas_caba", "movilizacion_cepa",
                        # ADR-0089: su puntaje era redundante con el del
                        # bloqueo sostenido (identidad algebraica). Se sigue
                        # relevando y queda a la vista como dato dentro de la
                        # card de bloqueo (caidas_12m).
                        "derrotas_legislativas",
                        # ADR-0064: fuente ciega a sanciones del Senado (ver ADR-0062);
                        # su banda queda arriba como referencia histórica
                        "comisiones_caidas"]

# ── Qué tipo de cosa mide cada indicador (ADR-0094) ──────────────────────────
# Prioridad 2 de la auditoría del cinturón: el índice mezclaba bajo una misma
# etiqueta tres preguntas distintas, y eso "dificulta responder con precisión la
# pregunta de si el gobierno puede ejecutar pese a la tensión".
#
# La separación es de LECTURA, no de cálculo: el ITCP se sigue computando igual
# y los pesos no cambian. Lo que se agrega es poder leerlo descompuesto.
#
#   tension    — lo que OTROS actores le hacen al gobierno
#   capacidad  — lo que el gobierno logra, o cuánto se sostiene
#   recursos   — con qué cuenta para negociar
FAMILIAS_ITCP = {
    # Tensión externa: conducta de terceros.
    "desafios_legislativos": "tension",        # el Congreso decide dar la pelea
    "veto_quorum": "tension",                  # la cámara no se reúne
    "conflictividad_nacional": "tension",      # la calle
    "jornadas_individuales_no_trabajadas_12m": "tension",  # intensidad laboral
    "brecha_obra_publica": "tension",          # los empresarios que dependen del Estado
    "apoyo_empresario": "tension",             # lo que las cámaras dicen del Gobierno
    "alineamiento_senadores_prov": "tension",  # cómo votan los senadores provinciales
    "adhesion_reformas_provincial": "tension", # qué deciden las legislaturas provinciales
    # ADR-0168: los cuatro entran por la regla de ADR-0166 — responden "cuánto
    # lo confrontan las otras instituciones", no "cuánta actividad despliega el
    # Gobierno", y de ahí sale el signo.
    "produccion_legislativa": "tension",       # cuánto sanciona el Congreso por su cuenta
    "judicializacion": "tension",              # cuánto se le frena la agenda por vía judicial
    "velocidad_resolucion": "tension",         # cuán rápido resuelve el sistema judicial
    "paralisis_denuncias": "tension",          # si el control disciplinario está activo

    # Capacidad propia: resultado de la acción del gobierno.
    "eficacia_legislativa": "capacidad",       # cuánto de lo que manda se sanciona
    "bloqueo_sostenido": "capacidad",          # cuánto aguanta de lo desafiado
    "ratio_dnu": "capacidad",                  # cuánto depende del decreto
    "cohesion_bloque": "capacidad",            # cuán unido vota su propio bloque
    # Cubrir cargos de juez EXIGE acuerdo del Senado: no es conducta de un
    # tercero sino resultado de lo que el Gobierno consigue negociar (ADR-0126).
    "cobertura_judicial": "capacidad",

    # Recursos de negociación: no son conducta de nadie, son activos.
    "votometro_ventaja_lla": "recursos",       # capital electoral
    "iaf_transferencias": "recursos",          # el giro fiscal como instrumento
}

FAMILIAS_ITCP_META = {
    "tension":   {"nombre": "Tensión externa",
                  "glosa": "lo que otros actores le hacen al Gobierno"},
    "capacidad": {"nombre": "Capacidad propia",
                  "glosa": "lo que el Gobierno consigue, o cuánto sostiene"},
    "recursos":  {"nombre": "Recursos de negociación",
                  "glosa": "con qué cuenta para negociar"},
}


# ── Rezago: dónde cae, en promedio, el dato que alimenta cada indicador ──────
# (ADR-0092, prioridad 5 de la auditoría del cinturón)
#
# No es el retraso de publicación de la fuente —eso ya está en la ficha de cada
# indicador— sino el CENTROIDE DE SU VENTANA: un indicador que promedia los
# últimos 12 meses describe, en promedio, la situación de hace 6, aunque su
# último dato sea de ayer. Es la distinción que la auditoría pide hacer visible:
# "dato de julio de 2026" no es lo mismo que "situación de julio de 2026".
#
# Los valores se derivan del diseño de cada ventana, no se estiman:
#   ventana móvil de N meses  -> N/2
#   cohorte de 12 a 24 meses  -> 18
#   stock acumulado           -> 0 (describe el estado de hoy)
REZAGO_MESES_ITCP = {
    # ADR-0168. Los dos judiciales anuales son, por lejos, los más rezagados
    # del índice: la Corte publica su anuario con el año cerrado y SAIJ indexa
    # con demora. Se declara alto a propósito — la card de rezago (ADR-0092)
    # tiene que mostrar que este bloque describe otro año, no el pulso de hoy.
    "velocidad_resolucion": 12.0,
    "judicializacion": 9.0,
    # Ventana móvil de 12 meses sobre sesiones ya publicadas en el archivo del
    # Consejo: el rezago es el de la publicación de la nota, no el de la ventana.
    "paralisis_denuncias": 2.0,
    # Ventana móvil de 12 meses sobre el dataset de leyes sancionadas de HCDN,
    # que se actualiza con la sanción: el rezago es el de la carga en el CKAN.
    "produccion_legislativa": 1.5,
    # Cohorte MADURA: sólo entran los proyectos publicados hace 12-24 meses,
    # porque antes no hubo tiempo material de sancionarlos (ADR-0061). Es el
    # más rezagado del índice por construcción, y no hay forma de acelerarlo
    # sin volver a introducir el sesgo que ese ADR sacó.
    "eficacia_legislativa": 18.0,
    # Comparación anual dic-dic: hasta 12 meses de rezago por diseño.
    "iaf_transferencias": 12.0,
    # Promedio móvil de 12 meses (6) más el rezago de publicación del INDEC.
    "brecha_obra_publica": 7.5,
    # Ventana móvil de 12 meses sobre comunicados fechados: el rezago de
    # publicación es cero (salen el día que la cámara los emite), así que queda
    # sólo el centroide de la ventana.
    "apoyo_empresario": 6.0,
    # El padrón se publica con ~1-2 meses de rezago, pero la serie se corrige
    # con los registros de designaciones y renuncias, que están al día: el
    # rezago efectivo del último punto es el de esos registros (ADR-0126).
    "cobertura_judicial": 1.0,
    # Ventanas móviles de 12 meses / 365 días.
    "ratio_dnu": 6.0,
    "veto_quorum": 6.0,
    "desafios_legislativos": 6.0,
    "bloqueo_sostenido": 6.0,
    "conflictividad_nacional": 6.0,
    "jornadas_individuales_no_trabajadas_12m": 6.0,
    # Ventanas de 90 días.
    "alineamiento_senadores_prov": 1.5,
    "cohesion_bloque": 1.5,
    # Encuestas ponderadas por recencia: el peso se concentra en las últimas
    # semanas, así que el centroide efectivo es de alrededor de un mes.
    "votometro_ventaja_lla": 1.0,
    # Stock acumulado de adhesiones: describe el estado vigente, no un promedio.
    "adhesion_reformas_provincial": 0.0,
}

# Umbrales de lectura de la card (meses).
REZAGO_PULSO = 2.0          # hasta acá, "pulso inmediato"
REZAGO_ESTRUCTURAL = 12.0   # desde acá, describe otro año


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
