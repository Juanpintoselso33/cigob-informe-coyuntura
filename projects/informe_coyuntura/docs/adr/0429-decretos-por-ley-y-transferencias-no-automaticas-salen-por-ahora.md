---
madr: 4
id: '0429'
estado: 'aceptado'
fecha: 2026-11-15
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu, transferencias_no_automaticas, eficacia_legislativa]
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

- **Suspenderlos con el mecanismo de [[0245]]; en legislativo, el peso del decreto pasa
  entero a eficacia (elegida, Juan, 15-nov).**
- Suspenderlos y que los demás absorban en proporción: vetos insistidos y decretos
  derogados, que casi siempre están en 100, subían de 12,5 % a 16,7 % y la cobertura a
  26,7 %, contra lo decidido en [[0422]].
- Borrarlos sin tocar el reparto: lo mismo que la proporcional.

## Decisión

`ratio_dnu` y `transferencias_no_automaticas` pasan a `INDICADORES_SUSPENDIDOS` desde
noviembre de 2026. Se siguen calculando, no puntúan ni se muestran como card.

- **Poder legislativo:** el 25 % de `ratio_dnu` pasa entero a eficacia legislativa, que
  queda como la medida de si se gobierna por ley o por decreto: eficacia 55 %, cobertura
  de cargos de juez 20 %, vetos insistidos 12,5 % y decretos derogados 12,5 %. Es lo más
  alineado con [[0422]]: la cobertura quedó en 20 % a propósito y vetos y derogados
  abajo porque casi siempre están en 100. `ratio_dnu` sale de la tabla de pesos; si
  vuelve, el reparto previo era 30/25/20/12,5/12,5.
- **Alianzas territoriales:** `transferencias_no_automaticas` conserva su peso de diseño
  en la tabla y los otros dos absorben su 40 % en proporción: alineamiento de senadores
  50 % y adhesión provincial a las reformas 50 %.

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
