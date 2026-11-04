---
madr: 4
id: '0423'
estado: 'aceptado'
fecha: 2026-11-04
cinturon: 'politica'
indice: 'ITCP'
indicadores: [votos_sobre_bancas]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
relacionado: ['0376', '0400', '0399']
ambito: 'ITCP · dimensión Cohesión interna · `votos_sobre_bancas`'
origen: 'Revisión de Luis del 3-nov-2026: sólo Diputados, escala 129/119/109, «si no hay votación asume el puntaje de la última votación». Juan, 4-nov: va tal cual la propuesta de Luis.'
---

# ADR-0423 — Votos ajenos pasa a diputados a favor, por mes

## Contexto y planteo del problema

[[0376]] midió los votos ajenos con que se aprueban las leyes del Ejecutivo como % de la
cámara, promedio de 12 meses, Diputados 65 % y Senado 35 %. Si la ley se aprueba, siempre
hace falta un piso de votos ajenos: en el Senado ese piso (22,2 %) ya superaba el corte del
verde, y el promedio de 12 meses tardaba medio año en mostrar un cambio.

## Factores de decisión

- Que el indicador pueda dar mal aunque la ley se apruebe.
- Que lea el mes, no un año.
- La escala la fijó Luis.

## Opciones consideradas

- **Diputados a favor, promedio del mes, escala de Luis (elegida).**
- Mantener el excedente sobre las bancas propias, sólo Diputados: sigue dependiendo del
  tamaño del bloque propio, que pasó de 39 a 94 bancas.

## Decisión

El indicador cuenta, en cada votación del universo de [[0376]] (leyes del Ejecutivo
aprobadas en general, sin tratados, con LLA a favor), cuántos diputados votaron a favor.
El valor es el promedio de las votaciones del último mes que las tuvo: un mes sin
votaciones conserva el último. El Senado sale. Cortes de color: más de 129 verde, de 119 a
129 amarillo, de 109 a menos de 119 naranja, menos de 109 rojo. Para que caigan en los
puntajes de corte (60, 40, 20), las anclas son 99 → 10, 109 → 20, 119 → 40, 129,1 → 60 y
172 (dos tercios) → 100; 129,1 deja la mayoría justa en amarillo, como dice «más de 129».
El rezago declarado pasa de 6 a 0,5 meses ([[0399]]). El peso (50 % de cohesión interna)
no cambia; la clave interna `votos_sobre_bancas` se conserva.

### Consecuencias

- La corrección de bancas del Senado de [[0400]] deja de afectar el valor.
- Un mes con una sola votación toma su valor entero: la serie es más volátil.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_votos_sobre_bancas.py` prueba el promedio del mes, el arrastre, que el Senado
no cuenta y cada borde de color.

## Pros y contras de las opciones

- Elegida: lectura directa contra la mayoría absoluta; muestra chica por mes.
- Excedente en Diputados: comparable con la serie anterior, pero sigue el tamaño del bloque.

## Más información

La revisión de Luis está en `docs/pendientes-monitor.md` (bloque del 3-nov, ítems 5 y 6).
