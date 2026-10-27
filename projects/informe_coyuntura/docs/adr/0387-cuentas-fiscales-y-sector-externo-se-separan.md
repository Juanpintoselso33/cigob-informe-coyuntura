---
madr: 4
id: '0387'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'macro'
indice: 'ITCM'
indicadores: [resultado_primario, recaudacion, saldo_comercial_12m, reservas_bcra, tcrm, terminos_intercambio, idc, credito_privado, costo_financiamiento_tesoro]
archivos: ['scripts/itcm.py', 'scripts/parametrica.py', 'scripts/sensibilidad.py', 'scripts/auditoria_coherencia.py', 'scripts/interpolacion_sombra.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
relacionado: ['0375', '0359']
ambito: 'Cinturón macro · ITCM · dimensiones Cuentas fiscales, Sector externo y Capacidad y costo del financiamiento'
origen: 'Revisión macro de Luis Babino del 26-oct-2026 (punto 1.1) y decisión de Juan del 27-oct-2026: hacerlo conservando el peso efectivo de cada indicador.'
---

# ADR-0387 — Las cuentas fiscales y el sector externo se separan

## Contexto y planteo del problema

El sector externo estaba repartido en tres dimensiones: el saldo comercial en
«Viabilidad fiscal-comercial», las reservas netas en «Capacidad y costo del
financiamiento» y el tipo de cambio real cruzado con los términos del intercambio
en «Competitividad externa». Luis señaló (revisión macro, 1.1) que el nombre
«fiscal-comercial» junta dos restricciones distintas —que las cuentas del Estado
cierren y que entren dólares— y propuso reagrupar.

## Factores de decisión

- Cada dimensión tiene que responder una sola pregunta.
- El índice no se mueve: cada indicador conserva su peso efectivo.
- El cruce del tipo de cambio real con los términos del intercambio (ADR-0375) tiene
  que seguir funcionando como cruce, no como promedio.

## Opciones consideradas

- **Dos dimensiones nuevas con los pesos efectivos intactos (elegida).**
- Sumar el sector externo sin tocar las otras: dejaba el saldo comercial y las
  reservas contados en dos lugares o forzaba cambiar pesos.
- Reagrupar y aprovechar para repesar: mezcla una reorganización con una decisión
  de método; no se pidió.

## Decisión

Cinco dimensiones, con el peso de cada indicador en el índice sin cambios:

| Dimensión | Peso | Indicadores (peso efectivo) |
|---|---|---|
| Estabilidad monetaria-inflacionaria | 26,0 % | inflación 15,6 · expectativas 5,2 · desequilibrio monetario 5,2 |
| **Cuentas fiscales** (antes «Viabilidad fiscal-comercial», 24 %) | 19,2 % | resultado primario 12,0 · recaudación 7,2 |
| **Sector externo** (nueva) | 21,2 % | saldo comercial 4,8 · reservas netas 5,44 · tipo de cambio real 5,5 · términos del intercambio 5,5 |
| Capacidad y costo del financiamiento (antes 16 %) | 10,6 % | capacidad prestable 3,36 · costo del Tesoro 4,0 · crédito privado 3,2 |
| Actividad e inversión | 23,0 % | sin cambios |

- Los pesos internos de las tres dimensiones tocadas se reescriben para que
  `peso_dimensión × peso_interno` dé exactamente el peso efectivo de antes (por
  eso aparecen como cocientes, p. ej. `0.048 / 0.2124`).
- `parametrica.calcular_indice` deja de admitir una regla `combinar` para toda la
  dimensión y admite **grupos**: un conjunto de indicadores que se cruza con una
  regla propia y entra a la dimensión con el peso que suman sus miembros
  (`parametrica.puntaje_dimension`). El sector externo declara un grupo,
  `(tcrm, terminos_intercambio)`, con `terminos_intercambio.combinar_dimension`
  (la matriz de ADR-0360/0375). Un grupo incompleto no se calcula: sus miembros
  presentes quedan afuera y el sector externo se arma con el saldo comercial y las
  reservas. La simulación de sensibilidad, la auditoría de coherencia y la
  interpolación en sombra usan la misma función.
- La clave `competitividad_externa` desaparece; el texto de las tarjetas del tipo
  de cambio real y de los términos del intercambio nombra ahora al sector externo.

### Consecuencias

- Con los datos de septiembre de 2026 el índice macroeconómico sigue en 53,9, y con
  el ejemplo del test (`EJEMPLO`) en 60,6, igual que antes, con y sin ajustes del
  analista. Lo único que cambia con datos completos es el redondeo del puntaje de
  cada dimensión (un decimal) al reagrupar.
- Con datos faltantes la renormalización cambia, porque ahora ocurre dentro de
  dimensiones distintas. Ejemplos con el ejemplo del test: sin reservas 63,1 → 62,6;
  sin saldo comercial 60,3 → 58,6; sin tipo de cambio real 62,0 → 61,0 (antes caía
  toda la competitividad; ahora el sector externo sigue con el saldo y las reservas);
  sin expectativas 60,3 → 60,2 (redondeo).
- Las series históricas por dimensión (`output/series`, BigQuery) cambian de claves:
  `viabilidad_fiscal_comercial` y `competitividad_externa` dejan de existir, nacen
  `cuentas_fiscales` y `sector_externo`. Los meses ya archivados se rehacen con el
  método vigente (ADR-0359).
- Las fichas de nueve indicadores y la del índice registran el cambio.

### Confirmación

`tests/test_itcm_dimensiones_externo_fiscal.py` fija la composición, que el peso
efectivo de cada indicador es el de antes y que los pesos suman 1; los tests de
`test_itcm.py` y `test_terminos_intercambio.py` fijan que el índice no se mueve y
que el cruce sigue siendo la matriz.

## Pros y contras de las opciones

- Dimensiones separadas: cada una responde una pregunta y el lector ve el sector
  externo junto. Cuesta un cambio en el motor (grupos) para no perder el cruce.
- Sin tocar las otras: no hace falta cambiar el motor, pero deja el problema que
  señaló Luis.

## Más información

- [[0375-competitividad-el-cruce-pasa-a-la-dimension]], [[0359-el-mensual-se-lee-con-el-metodo-vigente]]
- Revisión macro de Luis, 26-oct-2026, punto 1.1; `docs/pendientes-monitor.md`, ítem 9.
