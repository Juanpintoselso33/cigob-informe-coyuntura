---
madr: 4
id: '0312'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'politica'
indicadores: [votometro_ventaja_lla]
archivos: ['scripts/itcp.py', 'web/src/lib/fichas.ts']
corrige: ['0121']
ambito: 'ITCP · `votometro_ventaja_lla` · semáforo'
origen: 'Doc «260915 Ajuste de los Indicadores» — umbrales de Luis, en colores de semáforo'
---

# ADR-0312 — El votómetro traduce el semáforo que pidió Luis, no ya los márgenes simétricos

| **Corrige** | ADR-0121 (los cortes ±5/±15 pp de la ventaja LLA−PJ) |

## Contexto y planteo del problema

Luis pidió otros umbrales para la ventaja LLA−PJ, y los pidió en **colores de
semáforo**, no en puntaje:

- más de +8 puntos → verde
- entre +8 y +5 → amarillo
- entre +5 y 0 → naranja
- negativo → rojo

El semáforo de un indicador en este proyecto no se declara: se **deriva** del
puntaje 0-100 vía la tensión equivalente (`parametrica.color_de_puntaje`,
cortes de tensión 4/6/8 → puntaje 60/40/20 — ADR-0181). Traducir los cortes de
Luis exige entonces elegir las anclas de `BANDAS_ITCP["votometro_ventaja_lla"]`
de modo que esos cruces de color caigan exactamente en los pp que pidió, **no**
inventar una escala de colores propia por fuera del motor.

El equipo señaló además que la redacción de la ficha estaba en orden confuso
("entre +5 y +15" en vez de "entre +15 y +5").

## Opciones consideradas

- **Reanclar `BANDAS_ITCP` para que los cruces de color caigan en 8/5/0/negativo**
  — elegida.
- **Declarar el color a mano por fuera del motor paramétrico** — descartada:
  rompería la única fuente de verdad del semáforo (`parametrica.color_de_puntaje`)
  para un solo indicador, y el color dejaría de ser consistente con la lectura
  del resto del ITCP.
- **Dejar las anclas de ADR-0121 y sólo redactar la ficha con los colores** —
  descartada: la ficha mentiría, porque con las anclas viejas el corte real
  verde/amarillo cae en +9 pp (no en +8) y el naranja/rojo en −5 (no en 0) —
  verificado antes de descartar la opción.

## Decisión

Las anclas nuevas: `(14, INF, 100), (8, 14, 80), (2, 8, 40), (-2, 2, 20), (-INF, -2, 0)`.

El motor deriva el puntaje 0-100 por **interpolación lineal entre anclas**
(ADR-0021): para una banda finita el ancla es su punto medio, para una abierta
es su borde finito. Con esta tabla, las anclas quedan en **14, 11 (medio de
8–14), 5 (medio de 2–8), 0 (medio de −2–2) y −2**. Los cruces de color siguen
cayendo exactamente en los pp que pidió Luis (8, 5, 0) — el ancla nueva en 14
no mueve ningún corte de semáforo, sólo estira el tramo verde para que siga
subiendo por encima de +8 en vez de aplanarse ahí.

**Revisión, misma corrida (2026-09-15):** la primera versión de este ADR usaba
sólo cuatro bandas —`(8, INF, 60), (2, 8, 40), (-2, 2, 20), (-INF, -2, 0)`— y
argumentaba que subir el ancla superior a 100 "corta el tramo +5/+8 antes de
tiempo (con ancla en 100, +7 puntúa 70 → verde)". **Eso es un falso dilema**:
sólo vale si se mantienen cuatro anclas. Agregando una quinta banda arriba de
8 (con su propio punto medio en 11 y su ancla superior en 14) se logra el
mismo barrido de colores **sin** bajar el techo del indicador de 100 a 60.

Verificado numéricamente en `tests/test_itcp.py::test_banda_votometro_semaforo_traduce_umbrales_de_luis`
(colores, sin cambios respecto de la versión anterior del ADR) y a mano contra
las anclas nuevas:

| ventaja (pp) | puntaje interpolado | tensión | color |
|---|---|---|---|
| +12 | 86,7 | 1,33 | verde |
| **+8** (exacto) | 60,0 | 4,0 | **verde** |
| +6 | 46,7 | 5,33 | amarillo |
| **+5** (exacto, límite amarillo/naranja) | 40,0 | 6,0 | **amarillo** |
| +2 | 28,0 | 7,2 | naranja |
| **0** (exacto, límite naranja/rojo) | 20,0 | 8,0 | **naranja** |
| −1 | 10,0 | 9,0 | rojo |
| −10 | 0,0 | 10,0 | rojo |

Idéntico color a la tabla original en los 8 casos, techo 100 en vez de 60.

Los dos cortes exactos (+5 y 0) caen del lado que fija la convención del motor
(low exclusivo / high inclusivo en la tensión: `tensión ≤ tope` — ADR-0181), no
de una elección editorial nueva. Ninguno de los dos está exactamente en el pp
nominal por el redondeo a un decimal de `puntaje_desde_anclas` (ADR-0021): el
corte naranja→amarillo real está en **+4,9875** (puntaje crudo 39,95 redondea
a 40,0), no en +5,00 — con +5,00 exacto también da amarillo, así que el pedido
de Luis se cumple igual. Son 3 transiciones de color en total (no 4): rojo→naranja
en 0 (dentro de la resolución del redondeo), naranja→amarillo en +4,9875, y
amarillo→verde en ~+7,99. Ninguna cambió al pasar de cuatro a cinco anclas: el
tramo (−∞, 8] es idéntico en las dos versiones de la tabla.

### Por qué NO bajar el techo a 60 (motivo real para preferir 5 anclas)

La versión de 4 anclas hacía que la **tensión mínima** del indicador fuera
exactamente 4,0 — el borde inclusivo del verde en `CORTES_SEMAFORO`
(`parametrica.py`). Eso significa que con techo 60 el indicador **sólo** es
verde cuando está saturado en su máximo (+8,00 pp exactos → 60,0 → verde) y
**+7,99 pp → 59,9 → amarillo**: la banda "sin tensión" del semáforo era
inalcanzable salvo en el borde exacto de saturación, y una ventaja de +40 pp
puntuaba lo mismo que una de +8 — el indicador dejaba de poder distinguir un
empate apenas favorable de una victoria arrasadora. Es además, con ese techo,
el **único** de los 26 indicadores del ITCP con rango 0–60 (los otros 25 van
de 10 a 100); ningún gate lo detecta porque ningún test compara el rango de un
indicador contra el resto del índice.

### Impacto medido en el histórico reconstruido

`scripts/validacion_externa.py` reconstruye el ITCP mes a mes desde las series
de componentes con las bandas vigentes en cada corrida (32 meses con cobertura
suficiente, ene-2024→ago-2026). Comparando contra las anclas originales de
ADR-0121 (`(15,∞,100)(5,15,85)(-5,5,65)(-15,-5,40)(-∞,-15,10)`):

- **Con la tabla de 4 anclas (techo 60, descartada):** el ITCP reconstruido
  baja en los 32 meses, entre −3,20 y −1,50, media **−2,11**. El techo solo
  (aislado del resto de la recalibración) muerde en 12 de esos 32 meses —
  todos con ventaja > 8 pp— y resta por sí mismo hasta 2,40 puntos de ITCP en
  un mes puntual.
- **Con la tabla de 5 anclas (techo 100, esta revisión):** el ITCP baja entre
  −2,70 y **+0,20** (dic-2023/ene-2026/mar-2026 mejoran levemente por el
  desplazamiento del corte naranja/rojo hacia 0 en vez de −15), media
  **−1,43**. El movimiento restante es enteramente el efecto de trasladar los
  cortes de +15/+5/−5/−15 (ADR-0121) a +8/+5/0 (Luis) en el tramo ≤ 8 pp — no
  queda ningún componente de "techo bajado".

El mes publicado más reciente (ago-2026, ventaja +4,3 pp) cae en el tramo
[0, 5] que **no cambió** entre la tabla de 4 y la de 5 anclas (ambas comparten
el segmento por debajo de 8 pp) — el ITCP publicado y la dimensión
`imagen_voto` del snapshot actual quedan exactamente iguales a los que ya
publicó la corrida anterior de este PR (70,3 y 37,2 respectivamente); el
techo 100 sólo se manifiesta en meses con ventaja > 8 pp.

Esto cambia otra vez los dos tests que ya se habían tocado por el tope 60
(`test_calcular_itcp_pondera_dimensiones`, `test_calcular_itcp_renormaliza_ante_faltantes`):
con `votometro_ventaja_lla` en su valor más alto observado (+15 pp, > 14, ancla
superior), el indicador vuelve a puntuar el máximo (100), así que "todo en el
máximo" vuelve a dar ITCP = 100,0 en vez de 96,1.

### Ficha

Reescrita en orden descendente, con los cortes de **color** (no los bordes de
banda) y sin la contradicción de la versión anterior (que mezclaba +2 con
naranja y luego decía "−2 o menos → rojo", dejando +2 y −1 sin encajar en
ningún tramo declarado):

> "El puntaje del índice se asigna por bandas de la ventaja, interpolado entre
> anclas: más de +8 puntos → verde, el más alto; entre +8 y +5 → amarillo;
> entre +5 y 0 → naranja; 0 o menos → rojo, el más bajo."

El encabezado de la ficha ("van de 0 a 100, donde 100 es la mejor situación")
vuelve a ser cierto con el techo restaurado.

### Validación externa

`scripts/validacion_externa.py` reconstruye la serie histórica del ITCP contra
las bandas vigentes; se corrió de nuevo después de esta revisión (ver la
secuencia del PR) porque la reconstrucción usa las anclas nuevas para todo el
histórico. Los r contra los benchmarks externos (EPU, primeras diferencias,
adelantado, sin sector privado) se movieron dentro de lo esperable de una
recalibración de bandas — valores actualizados en el PR.

## Más información

Sigue sin resolverse (no es alcance de este ADR) la objeción del equipo sobre
la relevancia relativa de "Sesiones caídas por falta de quórum" frente a
"Producción legislativa" y "Eficacia parlamentaria" — ver ADR-0313, que la
documenta para la dimensión de poder legislativo, no para ésta.
