---
madr: 4
id: '0419'
estado: 'aceptado'
fecha: 2026-11-03
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [rigi_inversiones]
archivos: ['scripts/gestion.py', 'scripts/archivo.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_gestion.py', 'tests/test_archivo.py']
supersede: ['0102']
relacionado: ['0011', '0406', '0086']
ambito: 'ITCG · dimensión Privatizaciones e inversión · qué mide `rigi_inversiones`'
origen: 'Marcos, 3-nov-2026: «tomamos como promesa 100MM, contra eso juego lo aprobado al 31/10». Juan: «vamos encarando eso».'
---

# ADR-0419 — El RIGI se mide contra la promesa de US$ 100.000 millones

## Contexto y planteo del problema

`rigi_inversiones` medía la inversión aprobada sobre la cartera del régimen
(aprobada + en evaluación, [[0011]]). Ese denominador crece cada vez que se presenta un
proyecto, así que el porcentaje podía bajar sin que nada empeorara ([[0102]] lo explicaba
con una nota). Y como casi todo lo presentado termina aprobado, medía sobre todo la demora
en aprobar ([[0406]]). En la revisión del 3-nov-2026 Juan anotó que los cortes «no cierran»
y propuso un objetivo absoluto de monto. Marcos lo definió ese mismo día: la vara es la
promesa de US$ 100.000 millones de inversión, contra la que se juega lo aprobado.

## Factores de decisión

- Una vara que no se mueva con lo que se presenta.
- Que el número diga cuánto de lo prometido ya está aprobado.
- Que el mes publicado lea lo aprobado al último día del mes.

## Opciones consideradas

- **Aprobado sobre la promesa de US$ 100.000 millones (elegida).**
- Aprobado sobre la cartera (lo de antes).

## Decisión

El valor es `100 × inversión aprobada / 100.000` (millones de dólares). Lo que está en
evaluación sigue en la card como dato, pero no puntúa. La escala no cambia: la de medidor de
avance de [[0406]] (anclas 15 → 10 · 25 → 40 · 45 → 65 · 65 → 85 · 75 → 100), ahora sobre
el porcentaje de la promesa. Desaparece la nota de [[0102]]: con un denominador fijo el
porcentaje sólo baja si baja lo aprobado.

En el mes rehecho (`archivo.py`), la card sale del último punto de la serie hasta el fin de
mes —lo aprobado acumulado, fechado por la norma de aprobación— dividido por la promesa. La
foto del mes no sirve: guarda el porcentaje sobre la cartera.

### Consecuencias

- Con los US$ 76.173 millones aprobados al 3-nov-2026 el valor pasa de 34,9 % (sobre la
  cartera) a 76,2 % de la promesa, y el puntaje de 52,4 a 100.
- Es método: llega a la edición mensual y al archivo. Octubre se lee con lo aprobado al
  31-oct.
- La serie sigue en millones de dólares (es el gráfico) y sigue fuera de la reconstrucción
  histórica por la misma razón de [[0086]].

### Confirmación

`tests/test_gestion.py::test_rigi_mide_lo_aprobado_contra_la_promesa` fija la cuenta y que lo
que está en evaluación no la mueve; `tests/test_archivo.py` exige que el mes rehecho la tome
de la serie.

## Pros y contras de las opciones

- Promesa: vara fija y legible («cuánto de lo prometido»), pero es una convención: el
  número de la promesa lo eligió el equipo.
- Cartera: sale toda de la fuente, pero el denominador se mueve y mide la demora.

## Más información

La promesa de US$ 100.000 millones es la definición del equipo (Marcos, 3-nov-2026).
