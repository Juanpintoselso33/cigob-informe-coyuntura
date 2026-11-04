---
madr: 4
id: '0422'
estado: 'aceptado'
fecha: 2026-11-04
cinturon: 'politica'
indice: 'ITCP'
indicadores: [cobertura_judicial, produccion_legislativa, ratio_dnu, eficacia_legislativa, insistencias_vetos, rechazos_decretos]
archivos: ['scripts/itcp.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0126', '0168', '0374', '0377', '0344', '0245']
ambito: 'ITCP · dimensiones Poder legislativo y Poder judicial · `cobertura_judicial`, `produccion_legislativa`'
origen: 'Revisión de Luis del 3-nov-2026: «DNU y cobertura judicial → legislativo, con el 16 % completo» y «sacar producción legislativa». Juan fijó el reparto interno el 4-nov-2026.'
---

# ADR-0422 — El Poder judicial se disuelve en poder legislativo

## Contexto y planteo del problema

Desde [[0374]] la dimensión Poder judicial (16,13 % del ITCP) tenía un solo indicador vivo,
la cobertura de cargos de juez, que depende de los pliegos del Ejecutivo y del acuerdo del
Senado ([[0126]]). En su revisión del 3-nov-2026 Luis pidió pasarla a poder legislativo con
el 16 % completo y sacar la producción legislativa ([[0168]]), que cuenta la actividad de
las cámaras y usa leyes sancionadas mientras decretos por ley usa leyes publicadas.

## Factores de decisión

- El peso entre dimensiones lo fijó Luis: legislativo suma el 16,13 % (22,58 → 38,71 %).
- Que la cobertura, un solo dato, no domine la dimensión.
- Que los indicadores que casi siempre están en 100 (vetos insistidos y decretos
  derogados, [[0377]]) no inflen el índice.

## Opciones consideradas

- **30 / 25 / 20 / 12,5 / 12,5 (eficacia / decretos por ley / cobertura / vetos /
  derogados) (elegida).**
- Proporcional: cada indicador conserva su peso en el índice y la cobertura queda en
  41,7 % de la dimensión. Juan la descartó: la cobertura pasaría a ser lo más pesado del
  legislativo.
- Parejos (20 % cada uno): legislativo daría 68,4 en vez de 61,0, empujado por vetos y
  derogados, que pasan casi todos los meses en 100.

## Decisión

La dimensión Poder judicial se disuelve. Poder legislativo pesa 38,71 % y se reparte:
eficacia legislativa 30 % (11,6 % del índice), decretos por ley 25 % (9,7 %), cobertura
de cargos de juez 20 % (7,7 %), vetos insistidos 12,5 % (4,8 %) y decretos derogados
12,5 % (4,8 %). `produccion_legislativa` pasa a `INDICADORES_SUSPENDIDOS` ([[0245]]): se
sigue calculando, no puntúa ni es card, y vuelve si aparece una medida alternativa.

Los tres judiciales ya suspendidos (judicialización, velocidad de resolución, parálisis
de denuncias) conservan `"dimension": "poder_judicial"` como archivo de dónde pesaban; su
peso de diseño se borra con la dimensión, como los reemplazados de [[0377]].

### Consecuencias

- Con los datos del 4-nov-2026 poder legislativo pasa de 61,2 a 61,0 y el ITCP de 67,7 a
  67,6.
- El índice queda con cinco dimensiones, como antes de [[0126]] más sector empresarial.
- Es método: llega a la edición mensual y al archivo ([[0344]] fijó los pesos previos).

### Confirmación

`tests/test_itcp.py` y `tests/test_politica_judicial.py` exigen la composición nueva; los
tests de suspensión verifican que la producción legislativa no puntúe.

## Pros y contras de las opciones

- Elegida: prioriza lo que dice si se gobierna por ley o por decreto; es una convención.
- Proporcional: no mueve pesos en el índice, pero deja a la cobertura como eje del
  legislativo.
- Parejos: simple, pero mide menos y sube el índice por dos indicadores casi constantes.

## Más información

La revisión de Luis está en `docs/pendientes-monitor.md` (bloque del 3-nov).
