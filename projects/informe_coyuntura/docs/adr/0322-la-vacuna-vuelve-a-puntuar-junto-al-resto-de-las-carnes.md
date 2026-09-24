---
madr: 4
id: '0322'
estado: 'superado'
nota_estado: 'SUPERSEDIDO por el [ADR-0339](0339-puntua-el-total-de-carnes-y-la-vacuna-aparte.md) el 24-sep-2026: puntúan el total de las tres carnes y la vacuna aparte; aviar + porcina deja de puntuar.'
fecha: 2026-09-15
cinturon: 'vida'
indicadores: [consumo_carne_vacuna, consumo_carnes_otras, consumo_carnes_total]
archivos: ['scripts/itvc.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_carne_compuesto.py']
relacionado: ['0153', '0216', '0217', '0224', '0325', '0326', '0328']
superado_por: ['0339']
ambito: 'ITCIS · componente de proteína animal · qué puntúa la carne'
origen: 'Juan, Slack #monitor-de-proyecto-de-gobierno, 15-sep-2026: "en impacto social, sumar indicador carne vacuna por separado"'
---

# ADR-0322 — La vacuna vuelve a puntuar, junto al resto de las carnes

## Contexto y planteo del problema

ADR-0217 fusionó vacuna, aviar y porcina en un único componente que puntúa
(`consumo_carnes_total`) porque la vacuna sola exageraba el deterioro del
acceso a proteína: caía 10,7% contra el arranque del mandato mientras el
total —con la sustitución hacia pollo y cerdo adentro— caía sólo 5,0%. La
vacuna quedó como diagnóstico dentro de la matriz, sin card propia (regla
ADR-0153/0216: o integra el índice, o no es card).

Juan pide ahora sumarla "por separado". Eso reabre exactamente el problema
que ADR-0217 cerró: si vuelve a puntuar sola, y el total sigue puntuando
también, la faena vacuna —el 52,3% del total al 4T-2023, medido sobre las
tres series de faena del INDEC— entraría dos veces al índice.

**Antes de tocar el cálculo**, se verificó por qué la card de la vacuna
aparecía vacía (motivo del pedido, según el brief). Es falso a la fecha: las
cuatro corridas del pipeline del 15-sep-2026 (`vida_cotidiana_20260915_*.json`)
trajeron el tablero de SAGYP sin error, con el mismo dato (vacuna 46,75 kg/hab,
mes 2026-07) en las cuatro. El colector `consumo_carnes.py` funciona; lo que
no existe es una card de vacuna que puntúe, porque ADR-0217 la sacó a
propósito.

## Factores de decisión

- **No puede duplicar la faena vacuna.** Si vacuna y total puntúan juntos sin
  ajustar pesos, una caída de la vacuna golpea el índice dos veces.
- **El componente tiene que medir lo que su nombre dice** (regla del repo):
  "carne vacuna" tiene que medir vacuna, no un promedio que la diluye.
- **No perder la distinción sustitución/empobrecimiento** que es la razón de
  ser de la ficha de proteína animal: si sólo vuelve a puntuar la vacuna y el
  resto queda fuera del índice, se pierde la capacidad de leer si una caída de
  la vacuna se compensa con pollo/cerdo o no.
- El peso NOMINAL de la dimensión de ingresos y del resto de sus componentes
  no se toca.

## Opciones consideradas

1. Vacuna aparte + el resto de las carnes (aviar+porcina) como segundo
   componente, **reemplazando** al total fusionado.
2. Vacuna aparte + el total fusionado, con los pesos de ambos reducidos para
   "no duplicar".
3. Vacuna como único componente de acceso a proteína animal, con el total
   dentro de su explicación (volver a como estaba antes de ADR-0217).

## Decisión

**Opción 1.** `consumo_carnes_total` deja de puntuar. En su lugar puntúan
`consumo_carne_vacuna` y `consumo_carnes_otras` (aviar+porcina), cada uno
reconstruido desde la faena INDEC de sus propias categorías (antes: una sola
función sumaba las tres; ahora `_fetch_faena_indice(categorias)` en
`descargar_series.py` es compartida por los dos).

El peso nominal que tenía `consumo_carnes_total` (0,0392) se reparte entre
los dos **en la proporción con la que cada carne pesaba en la faena total al
4T-2023**, no 50/50: 52,3% vacuna / 47,7% aviar+porcina (medido sobre las
tres series de faena INDEC, ventanas móviles de 12 meses que terminan en el
4T-2023). Eso da 0,0392 × 0,523 ≈ **0,0205** para la vacuna y
0,0392 × 0,477 ≈ **0,0187** para el resto — los cuatro dígitos exactos, y no
0,0204/0,0188, son los que hacen que la cesión ×0,80 hacia
`consumo_supermercados` (que redondea cada componente a 4 decimales por
separado) siga sumando exactamente 1,0 en la dimensión; con el redondeo
"directo" al 52,0/48,0 la suma quedaba en 0,9999. La suma de los dos pesos
nominales es exactamente el peso anterior — no se resta ni se agrega peso a
ningún otro componente de la dimensión de ingresos y consumo.

Se descartó la Opción 2 porque "ajustar los pesos para no duplicar" sin una
regla de reparto es inventar un número; la Opción 1 tiene una regla medible
(la composición real de lo que se reemplaza) y evita la duplicación por
construcción, no por un factor de corrección. Se descartó la Opción 3 porque
es literalmente deshacer ADR-0217 y volver al falso positivo que esa
decisión existía para corregir — Juan pidió sumar la vacuna, no volver a que
sea la única que puntúa.

### Efecto medido en el ITCIS

Con la faena INDEC a jul-2026 (último mes con las tres series): índice vacuna
= 89,2 (cae 10,8% contra el 4T-2023), índice aviar+porcina = 100,0 (sin
variación contra su propia base), índice del total fusionado que
reemplazan = 94,4. La vacuna cae mientras el resto se sostiene — exactamente
el patrón de sustitución que la ficha existe para poder leer, ahora visible
en dos componentes en vez de uno solo.

Los pesos efectivos y el aporte al ITCIS de cada componente, y el score
global resultante, se registran en el snapshot publicado por esta misma
corrida (`web/src/data/informe.json`, `generated_at` de esta corrida) — no se
calculan a mano acá para evitar que este documento quede desalineado con el
número real la próxima vez que la faena se revise hacia atrás.

**El resultado más importante de esa medición, dicho explícito: el ITCIS
publicado no se mueve.** `itvc.valor` es 93,1 antes y después del split —
verificado sobre `web/src/data/informe.json` (`peso_efectivo` de
`consumo_carne_vacuna` = 0,0050 y de `consumo_carnes_otras` = 0,0046, exactos
a los cuatro decimales del `consumo_carnes_total` que reemplazan: 0,0050 +
0,0046 = 0,0096). **No es casualidad, es por construcción**: repartir el peso
en la proporción real de la faena (52,3%/47,7%) hace que el promedio
ponderado del score dé lo mismo que el score del total fusionado, porque el
índice del total (94,4) YA ES el promedio ponderado de los índices de sus
partes con esos mismos pesos (0,523×89,2 + 0,477×100,0 = 94,37 ≈ 94,4). Sobre
el peso efectivo (×0,80 de la cesión hacia `consumo_supermercados`, ver
arriba): 0,0314×94,4 = 2,964 puntos de aporte del total fusionado, contra
0,0164×89,2 + 0,0150×100,0 = 2,963 puntos de la suma de las dos partes — la
diferencia de milésimas es redondeo de los cuatro decimales publicados, no
una discrepancia real.

Que el índice no se mueva NO es un defecto de esta implementación: es la
prueba de que separar vacuna de "el resto" no coló un cambio de nivel por la
ventana. El objetivo del split nunca fue mover el ITCIS — fue dejar de tapar,
con un promedio, que la vacuna cae a 89,2 mientras aviar+porcina se sostienen
en 100,0. Antes de esta corrección, la sección de arriba decía sólo "se
registran en el snapshot" sin decir el resultado, que es peor que decirlo: un
lector no puede distinguir "no lo calculé" de "lo calculé y da lo mismo".

### Los tres números del equipo, verificados contra la serie

El equipo corrige un "13% arriba" que no se pudo localizar en ningún texto
generado actual ni histórico de este repo (revisados `_por_que_carne` y su
historial de git): la explicación publicada nunca calculó ese porcentaje. Del
resto:

- **Promedio histórico ~73 kg/hab/año (vacuna):** no verificable contra la
  serie propia del monitor, que arranca en oct-2023 (CICCRA) o ene-1998
  (faena INDEC, pero mide producción, no consumo aparente). Es una referencia
  externa, no recalculada acá, y no contradicha por lo que sí se puede medir.
- **~43 kg/hab/año actual:** la serie da 46,75 kg (SAGYP, jul-2026) y 46,0 kg
  (CICCRA, ago-2026) — más alto que lo que cita el equipo. Se publica el
  número que la fuente oficial trae, no 43.
- **Contracción de casi 10% interanual:** confirmado en orden de magnitud —
  SAGYP publica −8,44% i.a. para la vacuna en jul-2026.

La ficha (`web/src/lib/fichas.ts`, `consumo_carne_vacuna`) documenta estos
tres puntos con sus números verificados, no con los del brief.

### Confirmación

`tests/test_carne_compuesto.py` (reescrito) verifica: que puntúan
`consumo_carne_vacuna` y `consumo_carnes_otras` y no `consumo_carnes_total`;
que las dos siguen siendo card (ninguna cae en la regla ADR-0153/0216); que
sus semáforos comparten la misma matriz explicativa; y que sus series se
reconstruyen desde la faena INDEC de sus categorías correspondientes.

## Pros y contras de las opciones

**1. Vacuna + resto, reemplazando al total.** A favor: no duplica por
construcción, reparto medible, conserva la distinción sustitución/pérdida de
acceso. En contra: dos componentes en vez de uno, más superficie de fuente
caída.

**2. Vacuna + total, pesos reducidos.** A favor: menos cambios de código. En
contra: el "ajuste para no duplicar" no tiene una regla objetiva sin
inventar un descuento arbitrario, y de todos modos la vacuna sigue
sobre-representada dentro del total.

**3. Sólo vacuna.** A favor: cero componentes nuevos. En contra: es
literalmente el problema que ADR-0217 resolvió, sin resolver nada nuevo.

## Más información

- [[0217-puntua-el-acceso-total-a-proteina-no-la-vacuna]] — la decisión que
  este ADR matiza: no la revierte, reemplaza su único componente por dos que
  cubren la misma composición sin fusionarla.
- [[0216-o-integra-el-indice-o-no-es-card]] — regla que exige que las dos
  cards nuevas puntúen.
- [[0224-puntua-la-motorizacion-total-no-cada-vehiculo]] — mismo patrón de
  Componentes A/B en la matriz explicativa, para motorización.
