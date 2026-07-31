---
madr: 4
id: '0077'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [ipc_total, ipc_nucleo]
relacionado: ['0022', '0080']
ambito: 'Cinturón macro · `ipc_total` · serie acompañante `ipc_nucleo`'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · observación 10'
---

# ADR-0077 — El IPC general se lee junto al núcleo

| **Ampliado** | 18-jul-2026, tras revisión adversarial externa: se evalúa la pregunta de medición que la versión original no había evaluado |

## Contexto y planteo del problema

La auditoría señaló que **un mes de corrección tarifaria y uno de núcleo alta
puntúan igual y significan lo opuesto**: el IPC general mezcla precios
regulados, estacionales y núcleo, y el índice puntúa el general sin dar al
lector forma de distinguirlos.

La recomendación literal era "núcleo del IPC como serie de contexto". Tomada al
pie de la letra chocaría con una regla ya establecida del tablero: **ningún
cinturón publica cards de contexto** — un indicador que no integra su índice se
oculta, se sigue recolectando pero no se muestra. Agregar una card de núcleo
habría sido la excepción a una regla que costó trabajo emparejar.

### La pregunta de medición, evaluada (ampliación 18-jul-2026)

La revisión adversarial externa hizo una objeción de proceso que **es correcta y
se acepta**: la versión original de este ADR razonó "la auditoría pide una serie
de contexto → las cards de contexto están prohibidas → entonces va como curva en
el modal → punto cerrado", y en ningún tramo evaluó la pregunta sustantiva.
Peor: la regla invocada **no bloqueaba** las alternativas que sí resolvían el
problema de medición —reemplazar el general por el núcleo, o puntuar los dos con
pesos dentro del componente de inflación—, ninguna de las cuales crea una card
de contexto. Una convención de presentación terminó decidiendo una cuestión de
medición sin que nadie la discutiera.

Evaluada ahora, con los datos.

### La afirmación de sesgo sistemático no se sostiene

El argumento adversarial era que el programa 2024-2026 ejecutó una recomposición
tarifaria grande y deliberada, de modo que el índice estaría puntuando **la
corrección de precios relativos del propio programa como inestabilidad
monetaria**, con signo conocido. Medido sobre los 31 meses de serie común:

| | brecha media (general − núcleo) | efecto medio en el puntaje |
|---|---|---|
| 2024 | +0,53 pp | +2,1 |
| 2025 | **−0,10 pp** | −1,8 |
| 2026 (6 meses) | +0,19 pp | +3,5 |
| **período completo** | **+0,11 pp** | **+0,8** |

El general supera al núcleo en **18 de 31 meses**: casi mitad y mitad. Y la
brecha **cambia de signo** entre años. No existe el sesgo sistemático de signo
conocido que motivaba la objeción.

### La elección es inmaterial en este período

Reconstruyendo el ITCM completo con cada composición:

| composición | r vs riesgo país | ITCM último |
|---|---|---|
| general puro (vigente) | **−0,767** | 52,4 |
| 60 general / 40 núcleo | −0,766 | 52,8 |
| 40 general / 60 núcleo | −0,767 | 52,9 |
| núcleo puro | −0,767 | 53,3 |

La correlación externa es **indistinguible** entre las cuatro. La diferencia
entre general puro y núcleo puro en el ITCM reconstruido es de **0,61 puntos en
promedio** (mediana 0,50; máximo 2,80, en jun-2024).

### Decisión: se conserva el IPC general, ahora por una razón

Sin presión empírica, la decisión se toma por coherencia interna, y hay un
argumento que la versión original no había identificado:

**El otro componente de la dimensión es el REM, que releva expectativas del IPC
NIVEL GENERAL** (BCRA, variable 29), no del núcleo. La dimensión está construida
para leer la misma magnitud en dos momentos —inflación realizada e inflación
esperada—. Puntuar núcleo realizado contra expectativas de general rompería esa
correspondencia: los dos componentes dejarían de medir el mismo objeto.

Agregar el núcleo con un peso propio tampoco se justifica: movería el índice
medio punto y sumaría un componente más a una dimensión cuyos dos indicadores
principales ya correlacionan 0,935 entre sí (ADR-0075).

**La observación 10 queda RESUELTA, no ilustrada**: se evaluó la pregunta de
medición, se midió, y la respuesta es conservar el general con la serie de
núcleo visible al lado para que el lector pueda distinguir un mes de corrección
tarifaria de uno de núcleo alta.

## Opciones consideradas

- **Conservar el IPC general como serie puntuada, con el núcleo visible al lado** — elegida: la observación queda resuelta, no ilustrada. Se evaluó la pregunta de medición, se midió, y la respuesta fue conservar el general para que el lector pueda distinguir un mes de corrección puntual.
- **Puntuar el núcleo en lugar del general** — evaluada y descartada.

## Decisión

El núcleo entra como **serie acompañante dentro del modal del IPC**, no como
card propia: al abrir el indicador de inflación, el gráfico muestra **dos
curvas, general y núcleo**, sobre el mismo eje.

Es el patrón que el tablero ya usa para el TCRM, donde el multilateral se
grafica junto a los bilaterales de Brasil y Estados Unidos tal como lo presenta
el propio BCRA. Resuelve la observación —el lector puede ver si un mes de
inflación alta fue tarifas o núcleo— sin crear una card de contexto ni tocar la
puntuación.

- Fuente: INDEC, IPC Núcleo Nacional (base dic-2016), serie
  `148.3_INUCLEONAL_DICI_M_19`.
- Transformación: variación mensual derivada del nivel, la misma construcción
  que ya se usa para `ipc_total`, de modo que las dos curvas sean comparables
  punto a punto.
- Serie de **31 puntos desde dic-2023**.

**El núcleo no puntúa.** No entra al ITCM, no tiene bandas y no altera ningún
peso. Es material de lectura para interpretar el indicador que sí puntúa.

### Consecuencias

- El modal del IPC pasa de una curva a dos. Sin cambios en el índice ni en
  ninguna ficha de puntuación.
- La regla de "sin cards de contexto" queda intacta.

## Más información

### Precedentes directos

ADR-0022 / feedback de tablero (ningún cinturón publica cards de contexto) · patrón de series comparadas del TCRM

### Limitaciones

- El núcleo del INDEC excluye regulados y estacionales, pero la frontera entre
  categorías es una decisión metodológica del organismo, no una propiedad
  natural de los precios.
- **La inmaterialidad medida es de este período.** Si en el futuro se ejecutara
  una recomposición de precios relativos concentrada y grande, la brecha entre
  general y núcleo podría abrirse de forma sostenida y esta decisión habría que
  revisarla. La medición de arriba es el punto de partida para esa revisión.
- El argumento de coherencia con el REM **ata la decisión a la fuente de
  expectativas**: si el REM pasara a relevar núcleo, o si se cambiara el
  componente de expectativas, el razonamiento habría que rehacerlo.
