---
madr: 4
id: '0375'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'macro'
indice: 'ITCM'
indicadores: [tcrm, terminos_intercambio, tcr_terminos_intercambio]
archivos: ['scripts/parametrica.py', 'scripts/terminos_intercambio.py', 'scripts/itcm.py', 'scripts/macro.py', 'scripts/validacion_externa.py', 'scripts/sensibilidad.py', 'scripts/publicar.py', 'config.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
relacionado: ['0153', '0216', '0360']
ambito: 'Cinturón macro · ITCM · dimensión Competitividad externa'
origen: 'Reunión de Juan y Luis Babino del 26-oct-2026 y pedido de Juan del 27-oct («la cuenta que hoy se hace en el indicador se transfiere a la dimensión y quedan los dos indicadores por separado»).'
---

# ADR-0375 — Competitividad: el cruce pasa a la dimensión

## Contexto y planteo del problema

[[0360-competitividad-externa-tipo-de-cambio-real-por-terminos-del-intercambio]]
cruzó el tipo de cambio real con los términos del intercambio en una matriz y publicó
el resultado como un único indicador, `tcr_terminos_intercambio`. El lector veía un
puntaje y no los dos datos. En la reunión del 26-oct se pidió mostrar los dos por
separado y que el color de la competitividad lo siga dando el cruce.

La regla «o integra el índice, o no es card» ([[0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto]],
[[0216-o-integra-el-indice-o-no-es-card]]) impide publicar dos tarjetas que no
puntúan.

## Factores de decisión

- El lector tiene que ver el tipo de cambio real y los términos del intercambio.
- Las dos tarjetas tienen que puntuar.
- El número de la dimensión no debería cambiar: la matriz ya está decidida.

## Opciones consideradas

- **Dos tarjetas que puntúan y la matriz en la dimensión (elegida).**
- Mostrar los dos datos dentro de la tarjeta del compuesto.

## Decisión

- `tcrm` y `terminos_intercambio` son tarjetas con puntaje propio en la escala
  10-100: el tipo de cambio real con sus umbrales de siempre y los términos del
  intercambio con `10 + 90 × posición` entre sus percentiles congelados.
- La dimensión competitividad externa declara una regla `combinar`
  (`terminos_intercambio.combinar_dimension`) que reemplaza al promedio: lleva los
  dos puntajes a sus posiciones y aplica la matriz de ADR-0360. El motor
  (`parametrica.calcular_indice`), la simulación de sensibilidad y la reconstrucción
  histórica usan la misma regla. Sin uno de los dos, la dimensión no se calcula.
- Los pesos 0,5 / 0,5 sólo reparten el peso efectivo que declara cada tarjeta.
- `tcr_terminos_intercambio` pasa a contexto: se sigue calculando y es el mismo
  número que la dimensión.
- La tarjeta de los términos del intercambio muestra el último trimestre publicado y
  lo nombra; la reconstrucción histórica toma, mes a mes, el trimestre vigente con la
  regla de publicación de ADR-0360.

### Consecuencias

- Con los datos de septiembre de 2026: tipo de cambio real 49,7, términos del
  intercambio 85,0, dimensión 49,8 (igual al compuesto) e índice macroeconómico 53,9.
- La serie reconstruida de la dimensión coincide con la del compuesto (diferencias de
  redondeo de hasta 0,1).
- Una tarjeta puede estar verde y la otra amarilla con la dimensión en naranja: la
  tarjeta de cada una explica el cruce y nombra el cuadrante de hoy.

### Confirmación

`tests/test_terminos_intercambio.py` fija que la dimensión reproduce el compuesto y
que con un solo componente no se calcula.

## Pros y contras de las opciones

- Dos tarjetas: se ven los dos datos y cada uno puntúa; el peso efectivo de cada uno
  es una convención, porque la dimensión no es lineal.
- Dentro del compuesto: no toca el motor, pero el lector sigue viendo un solo número.
