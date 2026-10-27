---
madr: 4
id: '0374'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [velocidad_resolucion, paralisis_denuncias, cobertura_judicial]
archivos: ['scripts/itcp.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0126', '0168', '0255', '0281', '0359']
ambito: 'Cinturón político · ITCP · dimensión Poder judicial'
origen: 'Reunión de Juan y Luis Babino del 26-oct-2026 (acuerdos enviados por Luis ese día) y pedido de Juan del 27-oct.'
---

# ADR-0374 — La tasa de la Corte y las comisiones del Consejo salen del índice político

## Contexto y planteo del problema

[[0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp]] sumó a la cobertura de
cargos de juez tres indicadores de comportamiento del Poder Judicial. Uno ya había
salido ([[0255-el-corpus-de-saij-no-identifica-al-ejecutivo]]). De los otros dos, la
tasa de resolución de la Corte mide la eficiencia de la Justicia
([[0281-tasa-de-resolucion-no-es-duracion-judicial]] ya admitía que su signo era una
hipótesis) y las sesiones de las comisiones de Acusación y Disciplina miden el control
del Consejo sobre los jueces. Ninguno depende del Poder Ejecutivo, que es lo que mide
el índice político.

## Factores de decisión

- Un indicador tiene que medir lo que su índice promete: la capacidad de gobernar del
  Ejecutivo.
- Lo que no puntúa no se publica como tarjeta.

## Opciones consideradas

- **Sacar los dos y dejar la dimensión con la cobertura de cargos (elegida).**
- Mantenerlos con el nombre corregido (lo que se hizo en ADR-0366).

## Decisión

`velocidad_resolucion` y `paralisis_denuncias` pasan a suspendidos: se siguen
calculando, no puntúan y no son tarjeta. La dimensión del Poder Judicial queda con
`cobertura_judicial` al 100 % (los pesos de diseño quedan escritos, ADR-0245): el Ejecutivo eleva los pliegos al Senado (lo confirmó
Marcos en la reunión). La dimensión conserva su peso (16,13 %).

Condición para volver: que la dimensión mida además el desempeño de la Justicia, o
una medida de la presión del Ejecutivo sobre los jueces.

### Consecuencias

- Con los datos del 27-oct-2026: Poder judicial 57,1 → 62,0; índice político
  71,6 → 72,4. La tasa de la Corte puntuaba 94,6 y las comisiones, 10.
- La dimensión depende de un solo indicador, de actualización irregular.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

Los tests de composición del índice político y de suspendidos corren con la
dimensión nueva.

## Pros y contras de las opciones

- Sacarlos: la dimensión mide al Ejecutivo; queda con un único indicador.
- Mantenerlos: más información, pero sobre otro poder.
