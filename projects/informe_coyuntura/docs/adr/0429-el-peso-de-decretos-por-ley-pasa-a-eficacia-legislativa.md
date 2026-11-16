---
madr: 4
id: '0429'
estado: 'aceptado'
fecha: 2026-11-15
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu, eficacia_legislativa]
archivos: ['scripts/itcp.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'tests/test_itcp.py']
modifica: ['0426']
relacionado: ['0245', '0378', '0422']
ambito: 'ITCP · poder legislativo: el 25 % de `ratio_dnu` (suspendido) pasa a `eficacia_legislativa`'
origen: 'Revisión de Juan del 15-nov-2026 de los pendientes de la reunión con Luis del 13-nov.'
---

# ADR-0429 — El peso de decretos por ley pasa entero a eficacia legislativa

## Contexto y planteo del problema

[[0426]] (12-nov-2026, pedido de la dirección) suspendió `ratio_dnu` y
`transferencias_no_automaticas` con el mecanismo de [[0245]]: salen del cálculo y la
dimensión renormaliza en proporción. En poder legislativo eso deja eficacia 40 %,
cobertura de cargos de juez 26,7 % y vetos insistidos y decretos derogados 16,7 % cada
uno. Ese reparto contradice el de [[0422]] (4-nov): la cobertura quedó en 20 % a
propósito, porque es un solo dato que depende tanto del Ejecutivo como del Senado, y
vetos y derogados abajo porque casi siempre están en 100.

## Factores de decisión

- Respetar lo que [[0422]] decidió para cada indicador que sigue en la dimensión.
- Que el índice siga leyendo si se gobierna por ley o por decreto.

## Opciones consideradas

- **El 25 % del decreto pasa entero a eficacia (elegida, Juan, 15-nov).**
- Renormalización proporcional de [[0426]]: sube la cobertura y los dos indicadores que
  casi siempre están en 100.
- Repartirlo entre eficacia y cobertura: la cobertura pasaría del 20 % que se le fijó.

## Decisión

Poder legislativo: eficacia legislativa 55 %, cobertura de cargos de juez 20 %, vetos
insistidos 12,5 % y decretos derogados 12,5 %. `ratio_dnu` sale de la tabla de pesos
(sigue en `INDICADORES_SUSPENDIDOS` por [[0426]]); su rezago, familia y procedencia de
anclas quedan comentados para reponerlos. Si vuelve, el reparto previo era
30/25/20/12,5/12,5. Alianzas territoriales no cambia: alineamiento de senadores y
adhesión provincial a las reformas, mitad y mitad.

### Consecuencias

- Con los puntajes del 15-nov-2026 (eficacia 70,5, cobertura 61,5, vetos y derogados
  100) poder legislativo pasa de 77,9 a 76,1 y el ITCP baja algo menos de una décima por
  punto de la dimensión; el número exacto lo da la corrida.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_itcp.py::test_pesos_internos_poder_legislativo_sin_bloqueo`.

## Pros y contras de las opciones

- Elegida: conserva los pesos que [[0422]] fijó; eficacia pesa más de la mitad de la
  dimensión.
- Proporcional: no exige decidir nada, pero infla dos indicadores casi constantes.
- Eficacia y cobertura: más repartido, pero contra el tope de la cobertura.

## Más información

`docs/pendientes-monitor.md`, punto 11.
