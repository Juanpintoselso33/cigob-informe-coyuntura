---
madr: 4
id: '0409'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'macro'
indice: 'ITCM'
indicadores: [reservas_bcra, rem_ipc_12m, saldo_comercial_12m, tcrm, terminos_intercambio]
archivos: ['scripts/itcm.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'tests/test_itcm.py', 'tests/test_itcm_dimensiones_externo_fiscal.py', 'tests/test_idm_e_icip_no_puntuan.py', 'tests/test_terminos_intercambio.py', 'tests/test_contrato_publico_dice_lo_que_corre.py']
modifica: ['0387']
relacionado: ['0193', '0261', '0359']
ambito: 'Cinturón macro · ITCM · dimensiones Estabilidad monetaria-inflacionaria y Sector externo'
origen: 'Decisión de Juan del 28-oct-2026 (`docs/pendientes-monitor.md`): las reservas netas van a «Estabilidad monetaria-inflacionaria», conservando su peso en el índice.'
---

# ADR-0409 — Las reservas netas pasan a «Estabilidad monetaria-inflacionaria»

## Contexto y planteo del problema

[[0387]] juntó en «Sector externo» el saldo comercial, las reservas netas y el cruce
del tipo de cambio real con los términos del intercambio. Juan decidió que las
reservas netas se lean con la estabilidad de la moneda: son los dólares propios con que
el Banco Central respalda el peso, y su caída o su acumulación se discuten junto con la
inflación y la presión por salir del peso más que junto con el comercio.

## Factores de decisión

- El índice no se mueve: cada indicador conserva su peso efectivo.
- El ancla de [[0193]] —el desequilibrio monetario pesa como las reservas (0,052 contra
  0,0544 del índice)— se conserva.
- La proporción 60/20/20 de [[0261]] entre inflación, expectativas y desequilibrio se
  conserva.

## Opciones consideradas

- **Mover las reservas con su peso efectivo y reescribir los pesos internos como
  cociente (elegida).**
- Mover las reservas y repartir la dimensión en proporciones redondas: movería el índice
  y rompería el ancla de [[0193]].

## Decisión

| Dimensión | Peso | Indicadores (peso en el índice) |
|---|---|---|
| Estabilidad monetaria-inflacionaria | 0,26 → **0,3144** | inflación 0,156 · expectativas 0,052 · desequilibrio monetario 0,052 · **reservas netas 0,0544** |
| Sector externo | 0,2124 → **0,158** | saldo comercial 0,048 · tipo de cambio real 0,055 · términos del intercambio 0,055 |

Las demás dimensiones no cambian. Los pesos internos se escriben como cociente
(`0.0544 / 0.3144`, `0.048 / 0.158`), igual que en [[0387]], para que
`peso_dimensión × peso_interno` dé exactamente el peso de antes. El cruce del tipo de
cambio real con los términos del intercambio sigue siendo un grupo del sector externo.

### Consecuencias

- Con los datos de octubre de 2026 el índice macroeconómico sigue en 52,2. Estabilidad
  monetaria-inflacionaria pasa de 41,6 a 45,3 (las reservas puntúan por encima de la
  inflación) y el sector externo de 59,1 a 57,8.
- Con el ejemplo del test (`EJEMPLO`) el índice sigue en 60,6 (59,4 y 59,8 con los dos
  ajustes del saldo comercial); estabilidad 39,0 → 36,5 y sector externo 51,4 → 60,5.
- Con datos faltantes la renormalización cambia, porque ahora ocurre dentro de
  dimensiones distintas: sin expectativas, 60,2 → 60,1 con el ejemplo; sin el tipo de
  cambio real o sin los términos del intercambio, el sector externo queda con el saldo
  comercial solo; sin reservas, la estabilidad renormaliza entre los otros tres.
- Las series históricas de las dos dimensiones cambian de valor; los meses ya
  archivados se rehacen con el método vigente ([[0359]]).
- Fichas: la del índice (pesos de dimensión y cambio), la de reservas, y los faltantes
  de expectativas, tipo de cambio real y términos del intercambio; las descripciones de
  las dos dimensiones.

### Confirmación

`tests/test_itcm.py::test_estabilidad_monetaria_usa_pesos_60_20_20` fija los pesos
efectivos y la proporción 60/20/20;
`test_el_desequilibrio_pesa_como_las_reservas_y_no_como_el_tcrm` fija el ancla;
`tests/test_itcm_dimensiones_externo_fiscal.py` fija la composición, que cada indicador
conserva su peso efectivo y que el índice no se mueve.

## Pros y contras de las opciones

- Cociente con pesos efectivos: el índice y el ancla quedan intactos; los pesos internos
  dejan de ser redondos.
- Proporciones redondas: pesos internos legibles, a costa de mover el índice y el ancla.

## Más información

[[0387]] armó el sector externo; [[0193]] fijó el ancla del desequilibrio; [[0261]] el
60/20/20; [[0359]] la lectura del archivo con el método vigente.
