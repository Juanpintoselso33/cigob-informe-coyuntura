---
madr: 4
id: '0426'
estado: 'aceptado'
fecha: 2026-11-12
cinturon: 'politica'
indicadores: [ratio_dnu, transferencias_no_automaticas]
archivos: ['scripts/itcp.py']
relacionado: ['0245', '0378', '0422']
ambito: 'Cinturón política · índice político · `ratio_dnu` y `transferencias_no_automaticas` pasan a suspendidos'
origen: 'Pedido de la dirección del Monitor, 12-nov-2026'
---

# ADR-0426 — Decretos por ley y transferencias no automáticas salen del índice

## Contexto y planteo del problema

La dirección del Monitor pidió retirar del índice político dos indicadores:
`ratio_dnu` (decretos de necesidad y urgencia por ley publicada, poder
legislativo, 0,25 de la dimensión, 9,7% del índice) y
`transferencias_no_automaticas` (variación real de lo que la Nación gira a
provincias y municipios por decisión, alianzas territoriales, 0,40 de la
dimensión, 8,2% del índice). Al momento del pedido los dos estaban en rojo,
puntuando en el piso (10): 2,643 decretos por ley con el dato del 7-nov y
−82,1% real frente a 2023 con el dato de septiembre.

## Decisión

Los dos pasan a `INDICADORES_SUSPENDIDOS` con el mecanismo de ADR-0245: salen
del cálculo, no de la tabla de pesos. Cada dimensión reparte su peso entre los
indicadores que le quedan, y los dos dejan de publicarse como tarjeta (si no
puntúa, no es card). Se siguen relevando como seguimiento interno, y
reponerlos es borrar su entrada de `INDICADORES_SUSPENDIDOS`.

### Consecuencias

- El índice político sube: salen los dos indicadores que más lo bajaban.
- Poder legislativo queda con eficacia legislativa, cobertura judicial, vetos
  insistidos y decretos derogados (0,30/0,20/0,125/0,125 de diseño, que el
  motor renormaliza).
- Alianzas territoriales queda con alineamiento de senadores y adhesión
  provincial a las reformas, mitad y mitad.
- Los pesos entre dimensiones no cambian.

## Más información

La razón de fondo del retiro y la condición de reingreso quedan a definir por
la dirección; este ADR registra la decisión y su mecanismo.
