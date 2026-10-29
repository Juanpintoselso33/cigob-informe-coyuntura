---
madr: 4
id: '0414'
estado: 'aceptado'
fecha: 2026-10-29
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [gasto_funcionamiento]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_gasto_funcionamiento.py']
relacionado: ['0186', '0361']
ambito: 'Cinturón de gestión · ITCG · dimensión reforma del Estado · gasto de funcionamiento'
origen: 'Decisión de Juan del 29-oct-2026, a partir de la revisión de gestión de Luis (puntos 1.5 y 2.4): comparar el promedio de 12 meses contra todo 2023, de modo que el aguinaldo se cancele.'
---

# ADR-0414 — El gasto de funcionamiento se compara con todo 2023

## Contexto y planteo del problema

`gasto_funcionamiento` comparaba el último mes con el mismo mes de 2023. Luis
pidió en su revisión de gestión (1.5 y 2.4) una lectura menos sujeta al mes
elegido. El gasto es un flujo con medio aguinaldo en junio y otro en diciembre:
un mes suelto, o tres meses salteados, saltan según caiga o no un aguinaldo, y
contra octubre–diciembre de 2023 la base trae uno solo en tres meses (1/6)
mientras que doce meses traen dos en doce (1/12), lo que exagera la caída de 4 a
7 puntos.

## Factores de decisión

- Que el aguinaldo se cancele de verdad, no que se atenúe.
- Estabilidad del valor de un mes al siguiente.
- Actualizarse todos los meses.
- No tocar bandas ni peso: el puntaje sigue siendo 100.

## Opciones consideradas

Resultados con los datos de agosto de 2026 (variación real, %):

- Último mes contra el mismo mes de 2023: −35,9 (el método anterior).
- Último mes contra octubre–diciembre de 2023: −39,4. Inflado: la base trae el
  aguinaldo de diciembre y el último mes no.
- Últimos tres meses contra octubre–diciembre de 2023: −30,0. Salta entre −26 y
  −38 según caiga o no un aguinaldo en la ventana.
- Últimos doce meses contra octubre–diciembre de 2023: −31,9. Exagera la caída
  por el aguinaldo de la base; se eligió primero y se descartó después, en la
  misma conversación.
- Octubre–diciembre de 2025 contra octubre–diciembre de 2023: −27,4. El
  aguinaldo se cancela, pero se actualiza una vez por año y llega tarde.
- **Últimos doce meses contra todo 2023: −28,0 (elegida).**

## Decisión

Variación real del promedio mensual de los últimos 12 meses contra el promedio
mensual de los 12 meses de 2023 (enero a diciembre), ambos deflactados por el
índice de precios al consumidor del INDEC (`gestion._var_real_12m_vs_2023`).
Los dos lados traen los dos medios aguinaldos, así que el efecto se cancela. La
base es todo 2023, el año anterior al mandato, y no el último trimestre como el
resto del Monitor: ese es el motivo de la diferencia. Se exigen los 24 meses
(ventana y base); si falta alguno falla en voz alta, no se rellena.

La serie histórica (`descargar_series._serie_var_real_12m_vs_2023`) usa la
misma función y arranca en enero de 2024, la primera ventana que termina después
de la base. Bandas y peso no cambian. `masa_salarial` no se toca: no puntúa.

### Consecuencias

- La tarjeta pasa de −35,9 a −28,0 con los datos de agosto de 2026; sigue en la
  banda de 100.
- Reacciona más lento que un mes suelto a un cambio reciente.
- Los meses del archivo se releen con el método vigente (ADR-0359).

### Confirmación

`tests/test_gasto_funcionamiento.py` prueba la cuenta, que con una serie real
plana y medio aguinaldo en junio y diciembre el resultado sea exactamente cero,
el error por mes faltante y que serie y tarjeta coincidan;
`tests/test_la_ficha_no_se_queda_atras.py` exige la ficha.

## Pros y contras de las opciones

- Elegida: el aguinaldo se cancela, valor estable y mensual; más lenta, y la base
  difiere de la del resto del Monitor.
- Mismo mes de 2023: sin aguinaldo distorsionado, pero depende del mes.
- Último mes o tres meses contra oct–dic: dependen del aguinaldo.
- Doce meses contra oct–dic: exagera la caída 4 a 7 puntos.
- Trimestre contra trimestre: cancela, pero llega una vez por año.

## Más información

Ver ADR-0186 (la masa salarial sale del índice) y ADR-0361 (auditoría del
cinturón de gestión).
