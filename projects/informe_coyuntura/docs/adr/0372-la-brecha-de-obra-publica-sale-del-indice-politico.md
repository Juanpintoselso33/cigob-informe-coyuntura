---
madr: 4
id: '0372'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'politica'
indice: 'ITCP'
indicadores: [brecha_obra_publica, apoyo_empresario]
archivos: ['scripts/itcp.py', 'scripts/publicar.py', 'scripts/out_of_sample.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0088', '0150', '0310', '0359', '0380', '0399']
ambito: 'Cinturón político · ITCP · dimensión Sector privado'
origen: 'Pedido de Luis Babino (18-oct-2026) y decisión de Juan del 26-oct-2026.'
---

# ADR-0372 — La brecha de obra pública sale del índice político

## Contexto y planteo del problema

[[0088-dimension-sector-privado]] abrió la dimensión de sector privado
con la brecha entre las expectativas de las constructoras que trabajan para el
Estado y las que trabajan para privados. [[0150-apoyo-empresario-entra-al-itcp]] le sumó la
postura pública de la Unión Industrial, 50/50. La propia ficha de la brecha
admitía que mide un solo canal —el gasto en infraestructura— y que son
expectativas de un sector, no la relación del empresariado con el Gobierno.

## Factores de decisión

- Un indicador tiene que medir lo que su dimensión promete.
- Lo que no puntúa no se publica como tarjeta.
- La dimensión se va a ampliar con más cámaras (pendiente de Luis).

## Opciones consideradas

- **Sacar la brecha y dejar la postura de la Unión Industrial sola (elegida).**
- Mantener el 50/50 hasta sumar las otras cámaras.

## Decisión

`brecha_obra_publica` pasa a suspendido: se sigue calculando, no puntúa y no se
publica como tarjeta. Sector privado queda 100 % `apoyo_empresario`. La brecha
deja de figurar en la validación pública del índice político (su contraste con
Construya y su lectura por gobierno validaban un componente que ya no está), y
sigue siendo el control positivo de `out_of_sample.py`, que prueba el método y
no el índice.

Condición para volver: que la dimensión necesite otra vez una medida revelada
además de las posturas declaradas, y una que cubra más de un sector.

### Consecuencias

- Con los datos del 26-oct-2026 (seguimiento diario): la brecha puntuaba 71,2 y
  la postura de la Unión Industrial 40,0. Sector privado 55,6 → 40,0 e índice
  político 73,8 → 71,6.
- La serie de la dimensión hereda los huecos de la postura de la Unión
  Industrial (meses con menos de tres comunicados, ADR-0335).
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_politica_apoyo_empresario.py` fija la composición nueva y
`tests/test_out_of_sample.py` exige que el control siga evaluándose.

## Pros y contras de las opciones

- Sacarla: la dimensión mide la relación con el Gobierno; queda con una sola
  cámara hasta que entren las otras.
- Mantenerla: dos fuentes, pero una que mide expectativas de la construcción.
