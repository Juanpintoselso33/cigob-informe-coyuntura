"""
ITCM — Índice de Tensión del Cinturón Macroeconómico.

Implementa la "Fórmula Paramétrica para Evaluación del Estado de Tensión —
Cinturón de la Macroeconomía" (Fundación CIGOB, mayo 2026). Escala 0-100:
0 = máxima tensión (cinturón apretado), 100 = mínima tensión (aflojado).

ITCM = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor))

La tensión 0-10 del informe se deriva como (100 − ITCM) / 10, así el resto
del pipeline (umbrales, estados, score global) conserva su convención.

Convención de bordes de banda (uniforme, pineada por tests/test_itcm.py):
cada banda es (low, high, puntaje) con low EXCLUSIVO y high INCLUSIVO.
El documento fuente es ambiguo en los límites exactos (ej. "50-60.000" y
"40-50.000" comparten el 50.000); esta convención lo resuelve de forma única.

Los puntajes salen siempre de las tablas. El juicio cualitativo del analista
(ej. "saldo comercial positivo pero por contracción") se expresa como override
en data/macro/ajustes_itcm.json, con justificación y vencimiento.

Revisiones sobre el doc original (observaciones del analista, docs
"260602 Parametrica Macro (2)" y "260626 aportes para el cinturon macro"):
  * REM: se puntúa por el EQUIVALENTE MENSUAL de la expectativa anual
    (raíz 12: (1+REM/100)^(1/12)−1), bandeado con la misma escala mensual del
    IPC. Pone las expectativas y la inflación realizada en la misma vara.
    El equivalente mensual se deriva en macro.py y alimenta la banda "rem_ipc_12m".
  * Recaudación: variación INTERANUAL REAL (deflactada por el IPC del mismo
    período), no la variación mensual nominal.
  * Reservas: NETAS "a secas" (el número del mercado), 100% datos oficiales y sin
    constantes: netas = SDDS estricto (Activos de reserva − drenajes Sección II de la
    Planilla SDDS) + depósitos del Tesoro en USD (balance BCRA) + Bopreal 12m (bucket
    de vencimiento 3m-1año de la Sección II.1 del SDDS). El mercado suma de vuelta
    Tesoro y Bopreal porque no son pasivos del BCRA para defender el TC. Escala propia
    (ver BANDAS_ITCM). BADLAR pasa a contexto.
  * Financiamiento: la tasa se reemplaza por el ÍNDICE DE CAPACIDAD PRESTABLE
    (IdC): Precio (BADLAR real, 30%), Volumen (depósitos privados reales, 40%)
    y Asignación (holgura préstamos/depósitos, 30%). Índice ~1,0 (>1,02 verde /
    0,98-1,02 amarillo / <0,98 rojo). Nota: el doc define A=1−R (un nivel ~0,14
    que rompe el semáforo); se implementa A como el RATIO mensual de holgura
    (1−R_t)/(1−R_{t-1}), que sí deja el índice centrado en 1,0 y reproduce el
    "amarillo" de mayo 2026 del doc. El IdC se computa en macro.py.

Incorporaciones de la 3ª tanda (propuesta "Índice de Desequilibrio Monetario"
+ tipo de cambio multilateral, jun-2026):
  * Estabilidad monetaria suma el IDM (brecha de crecimiento real M3–M2; se
    llamaba «Índice de Desequilibrio Monetario» hasta ADR-0254): la brecha entre
    el crecimiento del M3 privado y el del M2 privado transaccional. Los dos son
    AGREGADOS: la brecha no es oferta menos demanda estimada. La propuesta original lo define como
    ΔM3 nominal − ΔM2 real mensual; esa fórmula está sesgada por la inflación
    (resta una tasa real de una nominal → da rojo permanente) y por la
    estacionalidad del aguinaldo. Se implementa la versión REAL-REAL INTERANUAL
    (ΔM3 priv. real i.a. − ΔM2 priv. real i.a.), que respeta la intención
    (comparar los dos agregados en términos reales) sin esos defectos. Se computa en
    macro.py a partir de circulante (var. 17) + depósitos privados (var. 100) y
    M2 privado transaccional (var. 197) del BCRA, deflactados por el IPC.
  * Composición de la liquidez y presión compradora (ficha de Diego, ago-2026;
    ADR-0192, renombrado por ADR-0252): indicador separado del IDM que cruza DOS
    componentes en una matriz — cuánta de la liquidez privada total sigue en
    pesos transaccionales (stock) contra cuántos dólares netos compra el sector
    privado no financiero (flujo). El componente B se llamaba «fuga fuera del
    sistema» y no identifica eso: el BCRA estimó que cerca del 80% de esas
    compras quedó depositado localmente. Comprar divisas y sacarlas del sistema
    financiero son dos actos distintos y acá sólo se observa el primero.
    Reemplaza a `presion_dolarizacion` (ADR-0055), que medía la misma presión
    cambiaria desde la misma fuente del BCRA y quedaba contándola dos veces
    dentro de la dimensión. El módulo resuelve la matriz y publica una tensión
    0-100; mayor tensión reduce el ITCM.
  * Nueva dimensión COMPETITIVIDAD EXTERNA (12%): el TCRM (ITCRM oficial del BCRA,
    base 2015=100) deja de ser contexto y puntúa. Apreciación real = atraso
    cambiario = más tensión. Las 4 dimensiones originales se recortan en
    proporción para hacer lugar (ver DIMENSIONES_ITCM).

Capítulo INVERSIÓN (docs "260629 INDICADOR DE INVERSION" + "260630 INVERSIÓN E IA",
jun-2026): nueva 6ª dimensión (12%) con dos indicadores compuestos calculados en
macro.py como promedios ponderados de variaciones interanuales:
  * IAI — Índice Anticipador de Inversión (físico): ISAC construcción + bienes de
    capital importados (+ patentamientos comerciales cuando haya histórico). Mide
    la inversión tradicional/tangible.
  * ICIP — Pagos de servicios digitales y productividad: pagos al exterior de
    servicios de informática (software/cloud/IA) + productividad laboral
    (IPI/empleo). NO es inversión digital: esos pagos son consumo intermedio en
    cuentas nacionales (ADR-0253). La lectura conjunta IAI vs ICIP sigue
    contrastando inversión física contra gasto en digitalización.
  El umbral ±2% de los docs no sobrevive al dato argentino (las series i.a. se
  mueven ±30-180% por la base 2024-2025): se usan BANDAS ANCHAS calibradas a la
  realidad, conservando la lógica contracción/neutro/expansión.
"""
from pathlib import Path

import parametrica

INF = float("inf")

# Tablas de bandas de la sección IV del documento. (low, high, puntaje).
BANDAS_ITCM = {
    "ipc_total": [                      # % mensual
        # Bandas NORMATIVAS, no calibradas contra la historia (ADR-0120). Los
        # cortes son metas de estabilidad de precios: 1% m/m ≈ 12,7% anual = zona
        # de éxito; 5% m/m ≈ 80% anual = fracaso. NO se anclan a los percentiles
        # de la serie propia a propósito: la inflación de 2021-2023 promedió 6,1%
        # m/m, de modo que anclarla a esa historia pondría un mes mediano
        # pre-mandato en el peor tramo y haría parecer perfecto cualquier mes de
        # hoy sólo porque el punto de partida era catastrófico — el blanqueo de
        # señal que ADR-0045 prohíbe. El umbral es la referencia externa correcta.
        (-INF, 1.0, 100), (1.0, 2.0, 85), (2.0, 3.0, 65), (3.0, 5.0, 40), (5.0, INF, 10),
    ],
    "rem_ipc_12m": [                    # EQUIVALENTE MENSUAL del REM (% mensual), raíz 12.
        # Valor DERIVADO en macro.py. Misma escala mensual que el IPC: pone la
        # expectativa anual en términos mensuales comparables a la inflación realizada.
        # Comparte deliberadamente las bandas NORMATIVAS del ipc_total (ADR-0120):
        # el REM es la inflación esperada y se juzga con la misma vara que la
        # realizada, de modo que un mismo puntaje signifique lo mismo en los dos.
        # No tiene historia propia previa a dic-2023 —es la serie derivada— pero
        # hereda su criterio del IPC, no del período medido.
        (-INF, 1.0, 100), (1.0, 2.0, 85), (2.0, 3.0, 65), (3.0, 5.0, 40), (5.0, INF, 10),
    ],
    "idm": [                            # Brecha de crecimiento real M3–M2 (pp, i.a.)
        # gap = crecimiento i.a. REAL del M3 privado − del M2 privado transaccional.
        # Negativo = el agregado transaccional crece más rápido que el amplio;
        # positivo = el amplio corre por encima del transaccional. NO es un
        # excedente sobre la demanda de dinero: M2 es un agregado (ADR-0254).
        # que presiona la brecha cambiaria. Calibrado con la historia 2024-2026 (oct-24 a
        # may-26 va de −11 pp en la remonetización post-estabilización a +7 pp en el pico).
        (-INF, -2.0, 100), (-2.0, 2.0, 85), (2.0, 5.0, 60), (5.0, 8.0, 35), (8.0, INF, 10),
    ],
    "desequilibrio_monetario": [        # tensión 0-100 de la matriz A × B (ADR-0192)
        # El valor crudo YA VIENE en unidades de tensión: desequilibrio_monetario.py
        # resuelve la matriz por interpolación bilineal y publica 0 (nada
        # degradado) a 100 (deterioro total). Estos cuatro tramos son una escala
        # de SEVERIDAD del compuesto y nada más.
        #
        # Hasta ADR-0257 pretendían además una esquina de la matriz por tramo, y
        # eso confundía severidad con diagnóstico. Ya no puede sostenerse: las
        # dos esquinas cruzadas valen 45 y caen en el mismo tramo, porque
        # degradar A sola y degradar B sola son igual de graves por
        # construcción. Cuál de los dos se degradó lo dice el cuadrante
        # (`celda`), que es otra cosa y viaja aparte en el snapshot.
        # El puntaje continuo sale de ANCLAS_ITCM, la inversión exacta
        # puntaje = 100 − tensión.
        # La divergencia banda/ancla es deliberada y del mismo tipo que la que
        # documenta ADR-0082: el motor siempre usa las anclas.
        (-INF, 20.0, 100), (20.0, 50.0, 60), (50.0, 80.0, 35), (80.0, INF, 10),
    ],
    "recaudacion": [                    # índice de base imponible real (100 = 4T-2023)
        # ANCLAS NUEVAS (ADR-0152). La métrica dejó de ser variación interanual y
        # pasó a ser NIVEL real desestacionalizado con base 100 = 4T-2023, así que
        # las bandas viejas no se traducen: estaban ancladas al cero de una
        # variación, y el punto con significado de un nivel base-100 es el 100 —
        # la misma base imponible real que en la transición.
        #
        # Los cortes son pasos de 10 PUNTOS de esa base, unidad redonda y
        # conceptual: 10% de la base imponible real de la transición. Se fijaron
        # sobre esa grilla y no sobre la distribución observada; declarado acá
        # porque ADR-0045 sólo autoriza calibrar contra lo observado cuando el
        # extremo es inalcanzable, y no es el caso (la serie llegó a 114,9 en
        # may-2024 y a 88,2 en jun-2026, o sea que toca dos tramos por arriba y
        # uno por abajo del 100 sin forzar nada).
        #
        # Dónde cae la serie con estas anclas (31 meses desde dic-2023): puntajes
        # de 43 a 100, mediana del índice 94,4. El puntaje INTERPOLA entre anclas
        # (ADR-0021), así que la concentración de meses en el tramo 90-100 no
        # aplana la señal — dentro de ese tramo el puntaje se mueve entre 60 y 85.
        (110.0, INF, 100), (100.0, 110.0, 85), (90.0, 100.0, 60),
        (80.0, 90.0, 35), (-INF, 80.0, 10),
    ],
    "saldo_comercial_12m": [            # millones USD acumulado 12m
        # Bandas en torno al EQUILIBRIO comercial (ADR-0120): el cero —comercio
        # balanceado— es el punto con significado, y los cortes marcan superávit/
        # déficit crecientes en miles de millones redondos. Techo institucional
        # de 85, no 100: un superávit puede ser por contracción de importaciones
        # (recesión), así que no se premia como óptimo pleno (regla de ADR-0056).
        # Sobre la historia 2022-2023 los cortes centrales caen cerca de la
        # mediana (5000→p53), de modo que la banda discrimina también fuera del
        # período que mide — no está calibrada a él.
        (15000.0, INF, 85), (10000.0, 15000.0, 75), (5000.0, 10000.0, 60),
        (-5000.0, 5000.0, 50), (-15000.0, -5000.0, 30), (-INF, -15000.0, 10),
    ],
    "reservas_bcra": [                  # millones USD — RESERVAS NETAS (no brutas)
        # Bandas en torno al CERO de reservas netas (ADR-0120): el cero —el BCRA
        # ni acumula ni quema reservas propias— es el umbral con significado, y
        # los cortes son colchones de USD en miles de millones redondos (>20 mil =
        # holgado, negativo = posición vendida). No se ancla a la historia porque
        # la serie propia arranca en jun-2024 (límite de la fuente de netas, no
        # hay dato pre-mandato comparable): el criterio es el nivel de cobertura,
        # no la distribución observada. Sería más robusto en MESES DE
        # IMPORTACIONES —revisión pendiente, ADR-0084 rechazó una primera versión.
        (20000.0, INF, 100), (15000.0, 20000.0, 85), (10000.0, 15000.0, 70),
        (5000.0, 10000.0, 50), (0.0, 5000.0, 30), (-INF, 0.0, 10),
    ],
    "idc": [                            # IdC en z-scores (σ vs. su historia, ADR-0028).
        # Anclas en desvíos estándar = percentiles conocidos de la muestra:
        # +1σ ≈ p84 · +0,5σ ≈ p69 · −0,5σ ≈ p31 · −1σ ≈ p16.
        (1.0, INF, 100), (0.5, 1.0, 85), (-0.5, 0.5, 60), (-1.0, -0.5, 35), (-INF, -1.0, 10),
    ],
    "emae_ia": [                        # % variación interanual
        # Bandas de crecimiento en torno al CERO (ADR-0120): el cero —actividad
        # estancada i.a.— es el punto con significado, y los cortes son tasas de
        # expansión/recesión en puntos redondos (crece >5% = fuerte, cae >5% =
        # recesión profunda). Sobre la historia 2021-2023 el corte de crecimiento
        # nulo cae en p26 y el de +3% en p42: la banda separa expansión de
        # recesión también en la era anterior, no está ajustada a este período.
        (5.0, INF, 100), (3.0, 5.0, 80), (0.0, 3.0, 60),
        (-2.0, 0.0, 40), (-5.0, -2.0, 20), (-INF, -5.0, 5),
    ],
    "emae_difusion": [                  # % de los 15 sectores del EMAE que crecen i.a.
        # Cortes por CANTIDAD DE SECTORES, no por porcentaje redondo: con 15
        # sectores el indicador sólo puede tomar 16 valores (múltiplos de 6,67),
        # así que los límites se ponen en el hueco entre dos valores alcanzables
        # (30 = entre 4 y 5 sectores, 50 = entre 7 y 8, 70 = entre 10 y 11,
        # 90 = entre 13 y 14). Cada banda es una lectura entera:
        #   14-15 → crecimiento generalizado · 11-13 → mayoría amplia
        #   8-10  → mayoría ajustada         · 5-7   → minoría creciendo
        #   0-4   → contracción generalizada
        #
        # NO se ancla en el 50% "de manual" (la línea de los índices de difusión
        # tipo ISM): sobre 257 meses de historia argentina la MEDIANA es 73,3 y
        # la mitad de los meses tiene 12 o más sectores creciendo. Un corte en 50
        # habría dado puntaje alto a la mitad inferior de la distribución. Los
        # cortes elegidos reparten 21/33/23/16/6% sobre la historia completa y
        # 23/34/22/14/7% pre-mandato: las CINCO bandas pobladas con datos reales
        # (criterio ADR-0042 — nace discriminando, no hay que recalibrarlo
        # después). En el mandato actual reparte 3/30/33/33/0%.
        (90.0, INF, 100), (70.0, 90.0, 80), (50.0, 70.0, 60),
        (30.0, 50.0, 35), (-INF, 30.0, 10),
    ],
    "ipi_manufacturero": [              # % i.a. suavizado 3m — MISMAS bandas que el EMAE
        # ADR-0076 + ADR-0079: se usan las bandas del EMAE a propósito, PERO no
        # porque los rangos sean parecidos (no lo son: sobre la misma ventana el
        # IPI oscila 1,6× más). Se usan porque la brecha que producen es real y
        # hay que dejarla ver: con estas bandas un mes MEDIANO del IPI puntúa
        # 39,4 y uno del EMAE 70,9, porque la industria argentina rindió peor
        # que la actividad agregada durante todo el período. Recalibrar para
        # cerrar esa brecha blanquearía desempeño real (criterio de ADR-0045).
        # El arrastre estructural se compensa con el PESO (20%), no con las
        # anclas.
        (5.0, INF, 100), (3.0, 5.0, 80), (0.0, 3.0, 60),
        (-2.0, 0.0, 40), (-5.0, -2.0, 20), (-INF, -5.0, 5),
    ],
    "tcrm": [                           # ITCRM oficial del BCRA (base 17-dic-2015=100)
        # Apreciación real = pérdida de competitividad y atraso cambiario = más tensión.
        # Bandas calibradas con la historia 1997-2026 (p10≈75, p25≈87, mediana≈106):
        # >110 competitivo · 95-110 cómodo (~nivel 2015) · 85-95 apreciación moderada ·
        # 75-85 apreciación marcada · ≤75 atraso severo.
        (110.0, INF, 100), (95.0, 110.0, 80), (85.0, 95.0, 60), (75.0, 85.0, 35), (-INF, 75.0, 10),
    ],
    "resultado_primario": [             # % de la recaudación (acum. 12 meses)
        # ADR-0072. Superávit primario del SPN sobre recaudación, ventana de 12
        # meses. Monótona: más superávit = más sostenible. Referencias: dic-2023
        # dio −12,0% (déficit) y el programa se estabilizó en torno a +6/+8%.
        (8.0, INF, 100), (4.0, 8.0, 85), (0.0, 4.0, 60),
        (-5.0, 0.0, 30), (-INF, -5.0, 10),
    ],
    "costo_financiamiento_tesoro": [    # % real anual (TIREA vs. inflación esperada REM)
        # ADR-0071. ÚNICA banda de U INVERTIDA del ITCM: los dos extremos son
        # malos. Tasa real muy negativa = represión financiera (el Tesoro coloca
        # licuando al ahorrista: dic-2023 dio −12,2%, y la prensa de esos días lo
        # llamaba "licuación"); tasa real muy alta = bola de nieve, la deuda
        # crece más rápido que la economía (ago-2025 dio +33,5%, con rollover del
        # 61% y tasas que "duplicaban la inflación"). El óptimo es positivo y
        # moderado, cerca del crecimiento potencial.
        (20.0, INF, 15), (12.0, 20.0, 45), (6.0, 12.0, 75),
        (0.0, 6.0, 100), (-5.0, 0.0, 55), (-INF, -5.0, 20),
    ],
    "iai": [                            # IAI — Índice Anticipador de Inversión (% i.a. ponderado)
        # Inversión física (ISAC + bienes de capital importados). Más = expansión.
        # El umbral ±2% del doc no sobrevive al dato (las series i.a. de inversión
        # argentina se mueven ±30-180% por la base 2024); bandas ANCHAS calibradas a
        # la realidad 2024-2026 conservando la lógica contracción/neutro/expansión.
        (10.0, INF, 100), (2.0, 10.0, 80), (-2.0, 2.0, 60), (-10.0, -2.0, 35), (-INF, -10.0, 10),
    ],
    "icip": [                           # ICIP — pagos de servicios digitales (% i.a. ponderado)
        # ADR-0253: se llamaba «Capitalización Inteligente». Los pagos al exterior
        # por informática y nube son, en cuentas nacionales, consumo intermedio —
        # no formación bruta de capital: pagar la nube todos los meses no
        # capitaliza a nadie. Mide pagos de servicios digitales combinados con
        # productividad laboral, y así se llama ahora.
        # Más rápido y volátil que la inversión física (los pagos de servicios
        # informáticos i.a. oscilan más), de ahí la banda más ancha.
        (20.0, INF, 100), (5.0, 20.0, 80), (-5.0, 5.0, 60), (-20.0, -5.0, 35), (-INF, -20.0, 10),
    ],
    "credito_privado": [                # Crédito al sector privado, % i.a. REAL (ADR-0022)
        # Crédito REALIZADO (complementa la capacidad del IdC). Bandas anchas
        # calibradas a la remonetización 2024-2026: el crédito real llegó a
        # crecer +90% i.a. desde base ínfima y se normaliza hacia +20/30%;
        # contracción real = crunch de financiamiento.
        (40.0, INF, 100), (20.0, 40.0, 85), (8.0, 20.0, 65), (0.0, 8.0, 45), (-10.0, 0.0, 25), (-INF, -10.0, 10),
    ],
}

ANCLAS_ITCM = {
    # Las cuatro esquinas de la matriz del desequilibrio monetario (0 · 45 ·
    # 45 · 90 de tensión → 100 · 55 · 55 · 10 de puntaje) caen TODAS sobre
    # esta recta, así que dos anclas la reproducen exactamente y no hay una
    # segunda escala que se pueda desincronizar de la del módulo. Las dos
    # cruzadas valen lo mismo desde ADR-0257: la recta no se entera, porque
    # traduce tensión a puntaje y no depende de cuántos valores distintos haya.
    "desequilibrio_monetario": ((0.0, 100.0), (100.0, 0.0)),
}

# Dimensiones del índice con su peso y la ponderación interna de indicadores.
# Pesos de dimensión: operacionalización propia. La Paramétrica CIGOB define las 4
# originales (35/30/20/15); las dimensiones 5ª (competitividad externa) y 6ª (inversión)
# y el recorte proporcional de las demás para hacerles lugar son extensión propia.
# Pisables vía data/macro/ajustes_itcm.json.
DIMENSIONES_ITCM = {
    "estabilidad_monetaria": {
        "nombre": "Estabilidad monetaria-inflacionaria",
        "peso": 0.26,
        "indicadores": {
            # 40/20/20/20 (ADR-0193). El desequilibrio monetario no hereda el
            # 10% de presion_dolarizacion: la ficha pide "un peso similar al de
            # los indicadores cambiarios/de reservas ya existentes" y ese 10%
            # daba 2,6% nominal, menos de la mitad del comparable.
            #
            # El comparable es reservas_bcra (5,44% nominal), no el TCRM: el
            # TCRM llega a 11% porque es el único indicador de su dimensión, no
            # porque se lo haya juzgado el doble de importante que las reservas.
            # Anclar ahí sería leer un artefacto de la estructura.
            #
            # El 20% deja al indicador en 5,2% nominal, al lado de reservas. Lo
            # que cede son rem e idm, no el IPC: los tres son lecturas distintas
            # de la misma tensión monetaria y ninguna es más autoritativa que
            # otra, mientras que la inflación realizada sigue siendo el núcleo
            # de la dimensión y conserva su 40%.
            "ipc_total": 0.40,
            "rem_ipc_12m": 0.20,
            "idm": 0.20,
            "desequilibrio_monetario": 0.20,
        },
    },
    "viabilidad_fiscal_comercial": {
        "nombre": "Viabilidad fiscal-comercial",
        "peso": 0.24,
        # ADR-0072: entra el RESULTADO primario y pasa a liderar la dimensión.
        # La recaudación baja de 60% a 30% y se reinterpreta como lo que es —un
        # indicador de actividad y formalidad de la base imponible—, no como la
        # medida de la viabilidad fiscal. Composición tomada de la auditoría de
        # consistencia (50/30/20); verificado que 45/30/25 y 40/30/30 mueven la
        # dimensión menos de 0,3 puntos con los datos vigentes.
        "indicadores": {
            "resultado_primario": 0.5,
            "recaudacion": 0.3,
            "saldo_comercial_12m": 0.2,
        },
    },
    "financiamiento": {
        "nombre": "Capacidad y costo del financiamiento",
        "peso": 0.16,
        # ADR-0022: crédito privado REAL i.a. (realizado) complementa al IdC
        # (capacidad) y a las reservas — la única señal no redundante de los
        # viejos indicadores de contexto.
        # ADR-0071: entra el COSTO del financiamiento soberano (25%). Los otros
        # tres se recortaron proporcionalmente (45/40/15 × 0,75).
        # ADR-0074: idc ≈ credito_privado. Capacidad de fondeo y crédito
        # efectivamente otorgado miden el mismo fenómeno —uno como condición,
        # el otro como resultado— y la validación del propio IdC muestra que no
        # anticipa al crédito. No había razón para que la condición pesara 2,7×
        # al resultado, así que se reparte el 41% conjunto casi en partes iguales.
        "indicadores": {
            "reservas_bcra": 0.34,
            "idc": 0.21,
            "costo_financiamiento_tesoro": 0.25,
            "credito_privado": 0.20,
        },
    },
    "actividad": {
        "nombre": "Actividad económica",
        "peso": 0.11,
        # ADR-0076 + ADR-0079: la dimensión dejó de colgar de un único dato, pero
        # el IPI entra como RESPALDO, no como medida principal. El EMAE ya
        # contiene a la industria (~17% del agregado), así que subirle el peso
        # al IPI sobre-expone la dimensión a un solo sector: al 20% la
        # exposición total a manufactura queda en 34%, el doble de su peso
        # natural, que es lo máximo defendible para un componente de respaldo.
        #
        # ADR-0124 (2026-07-25): entra emae_difusion con 0,20, tomado ENTERO del
        # peso del EMAE agregado (0,80 → 0,60). La composición por FUENTE de la
        # dimensión no cambia —el EMAE sigue aportando el 80% y el IPI el 20%—,
        # lo que cambia es que ese 80% pasa a leerse en dos registros: cuánto
        # crece la actividad (nivel) y en cuántos sectores crece (amplitud). El
        # IPI no se toca: sigue siendo el único respaldo de fuente distinta.
        "indicadores": {"emae_ia": 0.60, "emae_difusion": 0.20,
                        "ipi_manufacturero": 0.20},
    },
    "competitividad_externa": {
        "nombre": "Competitividad externa",
        "peso": 0.11,
        "indicadores": {"tcrm": 1.0},
    },
    "inversion": {
        "nombre": "Inversión",
        "peso": 0.12,
        "indicadores": {"iai": 0.6, "icip": 0.4},
    },
}

# Interpretación del ITCM (sección VI del documento). (low, high, etiqueta).
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

# Indicadores macro que se publican pero no integran el índice.
# badlar: ya no integra el índice (la dimensión de financiamiento usa el IdC);
# se sigue publicando como contexto e insumo del IdC (tasa pasiva de referencia).
# tcrm SALIÓ de contexto: ahora puntúa en la dimensión competitividad_externa.
INDICADORES_CONTEXTO = ["badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"]


def puntaje_banda(valor: float, bandas: list) -> int:
    """Puntaje de la banda donde cae `valor` (low exclusivo, high inclusivo)."""
    return parametrica.puntaje_banda(valor, bandas)


def banda_interpretacion(itcm: float) -> str:
    return parametrica.banda_interpretacion(itcm, BANDAS_INTERPRETACION)


def tension_de_itcm(itcm: float) -> float:
    """Tensión 0-10 del cinturón (convención del informe) derivada del ITCM."""
    return parametrica.tension_de_indice(itcm)


def anualizar_mensual(var_m_pct: float) -> float:
    """Tasa anual equivalente (capitalización) de una variación mensual %."""
    return ((1.0 + var_m_pct / 100.0) ** 12 - 1.0) * 100.0


def rem_mensual_equivalente(rem_anual_pct: float) -> float:
    """Equivalente mensual (raíz 12) de la expectativa de inflación anual del
    REM: (1+REM/100)^(1/12)−1, en %. Permite bandear el REM con la misma escala
    mensual del IPC. Ej.: REM 23,3% → 1,76% mensual."""
    return ((1.0 + rem_anual_pct / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0


# Transformaciones que se aplican al valor ANTES de puntuarlo (ADR-0082).
#
# Van declaradas acá, al lado de BANDAS_ITCM y ANCLAS_ITCM, y las aplica el
# motor. Antes cada llamador las aplicaba por su cuenta antes de invocar al
# índice, y quien no se acordaba puntuaba el valor crudo contra la banda
# equivocada — pasó tres veces: la reconstrucción histórica, la matriz de
# redundancia y el diagnóstico de bandas. Con la transformación declarada junto
# a la escala, no hay forma de puntuar sin ella.
def rem_anual_desde_mensual(mensual_pct: float) -> float:
    """Inversa de rem_mensual_equivalente: 1,76% mensual → 23,3% anual."""
    return ((1.0 + mensual_pct / 100.0) ** 12 - 1.0) * 100.0


# Cada entrada es (directa, INVERSA). La inversa no es decorativa: la
# simulación de sensibilidad perturba el valor CRUDO, y para saber cuánto es
# "±5% del ancho entre anclas" necesita ese ancho expresado en las unidades del
# valor crudo, no en las de la banda. Sin ella, el ruido del REM se calculaba
# sobre un ancho mensual y se aplicaba a un valor anual.
TRANSFORMACIONES_ITCM = {
    # La serie guarda la expectativa ANUAL; la banda es MENSUAL, la misma
    # escala del IPC.
    "rem_ipc_12m": (rem_mensual_equivalente, rem_anual_desde_mensual),
}


# Ponderación interna del IdC — los pesos conceptuales del doc "260626
# aportes" se conservan; los componentes son z-scores desde el ADR-0028.
IDC_PESOS = {"precio": 0.30, "volumen": 0.40, "asignacion": 0.30}


def indice_capacidad_prestable(precio: float, volumen: float, asignacion: float) -> float:
    """IdC = 0,30·z_precio + 0,40·z_volumen + 0,30·z_asignación (ADR-0028).
    Cada componente llega como z-score del NIVEL contra su propia historia
    (precio = tasa real BADLAR; volumen = depósitos privados i.a. real;
    asignación = holgura 1−préstamos/depósitos). Devuelve σ: 0 = mes típico,
    positivo = capacidad de fondeo mayor a la habitual."""
    return (IDC_PESOS["precio"] * precio
            + IDC_PESOS["volumen"] * volumen
            + IDC_PESOS["asignacion"] * asignacion)


# La escala del ITCM, armada una sola vez: bandas + anclas + transformaciones.
# Todo lo que reproduzca puntajes del índice usa ESTO y no las tablas sueltas
# (ADR-0082).
ESCALA_ITCM = parametrica.Escala(BANDAS_ITCM, ANCLAS_ITCM, TRANSFORMACIONES_ITCM)


def texto_bandas(indicador: str) -> str:
    """Texto legible de la tabla de bandas, para transparencia en el frontend."""
    return parametrica.texto_bandas(BANDAS_ITCM[indicador])


def ajuste_automatico_saldo(ind_saldo: dict) -> dict | None:
    """Regla automática del "Subcomponente D" de la Paramétrica: un superávit
    comercial que refleja caída de demanda interna (menos importaciones) más
    que aumento de exportaciones es sintomático de apretamiento y se penaliza
    (ADR-0056: suavizado por interpolación, sin el acantilado del "todo o
    nada" original — el piso de 60 puntos del documento fuente se conserva
    como el caso límite de dominación total de las importaciones).

    Definiciones (sobre acumulados 12m vs los 12m previos):
      mejora_expo = max(0, Δexpo_12m)   — aporte positivo de las exportaciones
      mejora_impo = max(0, −Δimpo_12m)  — aporte positivo de la caída de importaciones
      share_impo  = mejora_impo / (mejora_expo + mejora_impo)

    share_impo ≤ 0,5 (la mejora exportadora domina o empata): no opina. Por
    encima de 0,5 se interpola linealmente el puntaje de banda hacia el piso
    de 60 a medida que share_impo va de 0,5 a 1,0:
      frac = (share_impo − 0,5) / 0,5
      puntaje = puntaje_banda − frac × (puntaje_banda − 60)

    El puntaje de banda usado es el INTERPOLADO (parametrica.puntaje_interpolado),
    el mismo que consume calcular_indice — no el escalonado histórico, que
    generaba su propio acantilado en el gate de activación.

    Requiere superávit relevante (banda interpolada > 60) y la composición
    expo/impo que produce fetch_saldo_comercial_12m; sin esos campos (ej.
    fallback a la serie de saldo directa) o sin mejora positiva de ningún
    lado, no opina y devuelve None.
    """
    valor = ind_saldo.get("valor")
    d_expo = ind_saldo.get("expo_delta_12m")
    d_impo = ind_saldo.get("impo_delta_12m")
    if valor is None or d_expo is None or d_impo is None:
        return None
    if valor <= 5000:                # sin superávit relevante: la banda ya lo castiga
        return None
    p_banda = ESCALA_ITCM.puntaje(valor, "saldo_comercial_12m")
    if p_banda <= 60:
        return None
    mejora_expo = max(0.0, d_expo)
    mejora_impo = max(0.0, -d_impo)
    total = mejora_expo + mejora_impo
    if total <= 0:                   # ni expo ni impo mejoraron: nada que atribuir
        return None
    share_impo = mejora_impo / total
    if share_impo <= 0.5:            # la mejora exportadora domina o empata: no opina
        return None
    frac = (share_impo - 0.5) / 0.5
    puntaje = round(p_banda - frac * (p_banda - 60), 1)
    expo_var = ind_saldo.get("expo_var_ia")
    impo_var = ind_saldo.get("impo_var_ia")
    return {
        "puntaje": puntaje,
        "justificacion": (
            f"Regla automática: {share_impo:.0%} de la mejora del saldo se explica por "
            f"contracción de importaciones ({impo_var:+.1f}% i.a.) más que por "
            f"exportaciones ({expo_var:+.1f}% i.a.) — ajuste interpolado hacia el piso "
            f"de 60 puntos (Paramétrica CIGOB, may-2026; suavizado ADR-0056)."
        ),
        "origen": "automatico",
    }


def cargar_ajustes(path: Path, periodo: str) -> dict:
    """Overrides del analista vigentes para `periodo` (ver parametrica.cargar_ajustes)."""
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itcm(valores: dict, ajustes: dict | None = None) -> dict | None:
    """Calcula el ITCM a partir de {indicador: valor} (valores None se ignoran).

    Algoritmo común en parametrica.calcular_indice (renormalización ante
    faltantes, overrides con vencimiento); acá solo se enchufan las tablas
    del cinturón macro.
    """
    return parametrica.calcular_indice(
        valores, ajustes, BANDAS_ITCM, DIMENSIONES_ITCM,
        BANDAS_INTERPRETACION, INTERPRETACION_LEGIBLE,
        anclas_por_indicador=ANCLAS_ITCM,
        transformaciones_por_indicador=TRANSFORMACIONES_ITCM)
