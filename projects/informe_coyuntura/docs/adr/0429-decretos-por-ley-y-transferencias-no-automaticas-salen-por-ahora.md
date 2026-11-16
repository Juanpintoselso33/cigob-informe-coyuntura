---
madr: 4
id: '0429'
estado: 'aceptado'
fecha: 2026-11-15
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu, transferencias_no_automaticas]
archivos: ['scripts/itcp.py', 'web/src/lib/fichas.ts']
relacionado: ['0245', '0378', '0422']
ambito: 'ITCP · `ratio_dnu` (poder legislativo) y `transferencias_no_automaticas` (alianzas territoriales)'
origen: 'Reunión de Juan con Luis del 13-nov-2026: «DNU, Luis y Marcos lo sacaron por ahora; transferencias no automáticas, hay que sacarlo por ahora».'
---

# ADR-0429 — Decretos por ley y transferencias no automáticas salen del índice por ahora

## Contexto y planteo del problema

En la reunión del 13-nov-2026 la dirección (Luis y Marcos) decidió sacar por ahora del
índice político dos indicadores: los decretos de necesidad y urgencia por ley
(`ratio_dnu`, 25 % de poder legislativo, 9,7 % del índice desde [[0422]]) y las
transferencias no automáticas a provincias (`transferencias_no_automaticas`, 40 % de
alianzas territoriales desde [[0378]], 8,2 % del índice). Los dos estaban en rojo
(10/100) y bajaban el ITCP de ~80 a 68.

## Factores de decisión

- Es una decisión de la dirección, provisoria: reponerlos tiene que ser trivial.
- No cambiar el peso entre dimensiones.
- La regla del tablero: lo que no puntúa no es card ([[0245]]).

## Opciones consideradas

- **Suspenderlos con el mecanismo de [[0245]] (elegida).**
- Borrarlos de la tabla de pesos: obliga a rehacer los pesos al reponerlos.

## Decisión

`ratio_dnu` y `transferencias_no_automaticas` pasan a `INDICADORES_SUSPENDIDOS` desde
noviembre de 2026. Se siguen calculando, no puntúan ni se muestran como card, y su peso
de diseño queda en la tabla. Los demás indicadores de cada dimensión absorben su peso en
proporción: poder legislativo queda eficacia 40 %, cobertura de cargos de juez 26,7 %,
vetos insistidos 16,7 % y decretos derogados 16,7 %; alianzas territoriales, alineamiento
de senadores 50 % y adhesión provincial a las reformas 50 %.

### Consecuencias

- El ITCP sube porque salen dos rojos; el número exacto lo da la corrida que publica el
  cambio.
- Es método: llega a la edición mensual y al archivo.
- La línea de la card del cinturón sobre los rojos (punto 11 del documento de Luis del
  11-nov) queda sin objeto mientras sigan afuera.

### Confirmación

Los tests de suspensión de `tests/test_itcp.py` verifican que ninguno de los dos puntúe.

## Pros y contras de las opciones

- Elegida: reversible con una línea; el peso de diseño sigue a la vista.
- Borrar: más limpio en la tabla, pero pierde el peso para cuando vuelvan.

## Más información

La decisión está en `docs/pendientes-monitor.md`, punto 11.
