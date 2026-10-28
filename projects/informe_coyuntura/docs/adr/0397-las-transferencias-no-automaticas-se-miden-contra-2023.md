---
madr: 4
id: '0397'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [transferencias_no_automaticas]
parametros: ['BANDAS_ITCP["transferencias_no_automaticas"]']
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'tests/test_politica_transferencias_no_automaticas.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
modifica: ['0378']
relacionado: ['0239', '0359', '0378', '0390', '0399']
ambito: 'ITCP · dimensión Alianzas territoriales · medida y escala de las transferencias no automáticas'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0397 — Las transferencias no automáticas se miden contra 2023

## Contexto y planteo del problema

`transferencias_no_automaticas` ([[0378-transferencias-no-automaticas-reemplazan-a-las-automaticas]])
medía la variación real de los últimos 12 meses contra los 12 anteriores, con cortes
**−50 · −20 · +5 · +30 %** fijados mirando las 22 ventanas de la gestión, y
`procedencia_anclas` los clasificaba como `convencion`.

La variación interanual lee la base, no el nivel. Las transferencias discrecionales se
hundieron en 2024 (−85,3 % real en la ventana a diciembre de 2024) y nunca volvieron:
el nivel de los 12 meses a septiembre de 2026 es un 82,1 % menor que el de 2023. Pero
contra un 2025 igual de bajo, la recuperación parcial daba +31,8 % en diciembre de
2025 y +6,0 % en septiembre de 2026, y el componente puntuaba 75,8: «más recurso
puesto en juego» cuando la Nación gira menos de una quinta parte de lo que giraba.

## Factores de decisión

- Que el número diga cuánto gira la Nación, no cuánto cambió contra un año ya caído.
- La misma lectura que la conflictividad social ([[0390-conflictividad-con-cortes-de-la-historia-previa]]):
  nivel de 12 meses contra el total de 2023.
- Que la escala no salga del período que se evalúa.

## Opciones consideradas

- **Nivel real de 12 meses contra el total real de 2023, cortes en uno y dos desvíos de
  la historia previa (elegida).**
- Mantener la variación interanual y llevar los cortes a ±36/±72 (uno y dos desvíos).
- Nivel contra el promedio de 2018-2023.

## Decisión

El valor pasa a ser el **nivel real de los últimos 12 meses contra el total real de
2023**, cada flujo deflactado por el IPC de su mes ([[0239-el-deflactor-lo-pondera-el-flujo-no-el-calendario]]).
La primera ventana, diciembre de 2023, es la base misma y vale 0. La consulta a
Presupuesto Abierto arranca en 2023.

Los cortes pasan a **−72 · −36 · +36 · +72 %**. La variación interanual real de las 61
ventanas de 12 meses de noviembre de 2018 a noviembre de 2023 (devengado desde noviembre
de 2017, el primer mes con 12 meses de IPC nacional) tiene un desvío de **35,9 puntos**:
±36 es un desvío y ±72 son dos. La banda del medio es «un año normal» según esa
historia. Mayor sigue siendo mejor. El origen pasa a `historia_larga` y el techo de
circularidad del ITCP baja de 0,31 a 0,23 (medido: 22,3 %).

### Consecuencias

- Con el dato de septiembre de 2026 (−82,1 % contra 2023), el componente pasa de **75,8
  a 10**. En el mandato, 23 de los 34 meses quedan en 10 (todos desde noviembre de
  2024); los únicos por encima de 40 van de diciembre de 2023 a agosto de 2024, cuando
  la ventana todavía tenía meses de 2023.
- 2023 no es un año atípico de la historia: su nivel real (8,0 billones a precios de
  septiembre de 2026) está cerca del de 2018 (8,6) y del de 2022 (8,3). La base es fija y
  envejece; va en la ficha, como en la conflictividad.
- La historia previa es corta (cinco años) y está condicionada por el IPC, que empieza
  en diciembre de 2016.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_politica_transferencias_no_automaticas.py` fija la base 2023 (la primera
ventana da 0, la base no corre con la ventana), la deflación mes a mes, los cortes ±36/±72
y los puntajes en el nivel de 2023, el de septiembre de 2026 y los extremos.

## Pros y contras de las opciones

- Nivel contra 2023: mide la magnitud del recurso; la base es la del resto del cinturón.
  Satura abajo durante casi todo el mandato, porque el recorte fue de esa magnitud.
- Interanual con desvíos: externa al mandato (67,2 hoy), pero sigue premiando la
  recuperación contra una base hundida.
- Promedio 2018-2023: base más ancha, mismo resultado (−83,9 %, 10) y otra base que la
  del resto del índice.
