---
madr: 4
id: '0430'
estado: 'aceptado'
fecha: 2026-11-15
cinturon: 'vida'
indice: 'ITVC'
indicadores: [ipc_alimentos]
archivos: ['scripts/vida_cotidiana/collectors/indec_series.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_alimentos_sobre_ipc.py']
relacionado: ['0033', '0411', '0418']
ambito: 'Card de `ipc_alimentos` (impacto social)'
origen: 'Documento de Luis del 11-nov-2026, punto 9 («mismo IPC, distinto color»); decisión en la reunión del 14-nov: «porcentaje por encima del IPC».'
---

# ADR-0430 — La card de alimentos muestra cuánto subió la comida por encima del IPC

## Contexto y planteo del problema

La card de `ipc_alimentos` mostraba la inflación de alimentos del mes (≈ 2 %), pero el
color sale de otra cuenta: el nivel de alimentos contra el IPC general, base 4T-2023
([[0033]]). Con 2 % mensual la card de macro pintaba amarillo y la de alimentos verde, y
la tarjeta no mostraba el número que la pintaba (punto 9 del documento de Luis del
11-nov-2026).

## Factores de decisión

- La card muestra el dato que define su color.
- Card y serie salen de la misma función, para que el control card = serie (G3) cierre,
  como con el alquiler real ([[0411]]).
- El puntaje no cambia.

## Opciones consideradas

- **Porcentaje por encima del IPC general desde fines de 2023 (elegida, Luis, 14-nov).**
- El índice base 100 que puntúa: es la misma información, pero «107,8» no se lee solo.
- Dejar la inflación del mes y explicar al lado: la card seguiría pintando una cuenta y
  mostrando otra.

## Decisión

La card muestra `100 × (alimentos / alimentos₄ᵀ₂₃) / (general / general₄ᵀ₂₃) − 100`,
con un decimal: 0 = subieron lo mismo, positivo = la comida está más cara en relación
con el resto de los precios. Es `itvc_alimentos` expresado al revés y en %. La inflación
de alimentos del mes va en el detalle. La calcula
`indec_series.alimentos_sobre_ipc` y la usan el colector (card) y `descargar_series`
(serie). El rótulo pasa a «Alimentos frente al IPC general».

### Consecuencias

- Con octubre de 2026 (índice 107,8) la card pasa de 1,97 % mensual a −7,2 %.
- La serie de `ipc_alimentos` cambia de unidad en toda su historia.

### Confirmación

`tests/test_alimentos_sobre_ipc.py`: la cuenta, su relación con `itvc_alimentos` y que la
card sale del campo nuevo.

## Pros y contras de las opciones

- Elegida: la card dice lo que pinta; cambia la unidad de una serie publicada.
- Índice base 100: no cambia nada del cálculo, pero no se entiende sin explicación.
- Dejarla: no resuelve el punto 9.

## Más información

`docs/pendientes-monitor.md`, punto 9.
