# ADR-0077 — El IPC general se lee junto al núcleo

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · `ipc_total` · serie acompañante `ipc_nucleo` |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0022 / feedback de tablero (ningún cinturón publica cards de contexto) · patrón de series comparadas del TCRM |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · observación 10 |

## Contexto

La auditoría señaló que **un mes de corrección tarifaria y uno de núcleo alta
puntúan igual y significan lo opuesto**: el IPC general mezcla precios
regulados, estacionales y núcleo, y el índice puntúa el general sin dar al
lector forma de distinguirlos.

La recomendación literal era "núcleo del IPC como serie de contexto". Tomada al
pie de la letra chocaría con una regla ya establecida del tablero: **ningún
cinturón publica cards de contexto** — un indicador que no integra su índice se
oculta, se sigue recolectando pero no se muestra. Agregar una card de núcleo
habría sido la excepción a una regla que costó trabajo emparejar.

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

## Consecuencias

- El modal del IPC pasa de una curva a dos. Sin cambios en el índice ni en
  ninguna ficha de puntuación.
- La regla de "sin cards de contexto" queda intacta.

## Limitaciones declaradas

- El núcleo del INDEC excluye regulados y estacionales, pero la frontera entre
  categorías es una decisión metodológica del organismo, no una propiedad
  natural de los precios.
- Mostrar las dos curvas ayuda a interpretar, pero **no corrige** el hecho de
  que el índice puntúa el IPC general: si el editor concluyera que el núcleo es
  la variable relevante para puntuar estabilidad monetaria, eso sería un cambio
  de metodología con su propio ADR, no esta decisión.
