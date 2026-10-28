---
madr: 4
id: '0373'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [brecha_salario_cbt, pobreza_nowcast, consumo_supermercados, motorizacion_total, ratio_motos_autos, consumo_carnes_total, consumo_carne_vacuna]
archivos: ['scripts/itvc.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0115', '0225', '0339', '0383', '0386', '0392']
ambito: 'Cinturón de impacto social · ITCIS · dimensiones Ingresos y Consumo'
origen: 'Documento de Luis Babino «Cambios del cinturón impacto social v1» (22-oct-2026, punto 1) y decisión de Juan del 26-oct-2026.'
---

# ADR-0373 — Ingresos y consumo se parten en dos dimensiones

## Contexto y planteo del problema

La dimensión «Ingresos y consumo» juntaba dos preguntas distintas: si el
ingreso alcanza (salario contra canasta, pobreza) y qué se compra
efectivamente (supermercados, motorización, carnes). Con las dos en un solo
número, una caída del consumo quedaba tapada por el salario, que pesaba casi
la mitad, y al revés. Luis pidió separarlas.

## Factores de decisión

- Que cada dimensión responda una sola pregunta.
- No mover el índice por una reorganización: cambiar la agrupación no es
  recalibrar.

## Opciones consideradas

- **Partir la dimensión conservando el peso de cada componente en el índice
  (elegida).**
- Partirla con pesos nuevos para cada mitad.

## Decisión

«Ingresos» (0,2016): `brecha_salario_cbt` 0,6469 y `pobreza_nowcast` 0,3531.
«Consumo» (0,0790): `consumo_supermercados` 0,6926, `motorizacion_total`
0,1098, `ratio_motos_autos` 0,0888, `consumo_carnes_total` 0,0544 y
`consumo_carne_vacuna` 0,0544. El peso de cada dimensión es la suma de lo que
sus componentes ya pesaban adentro de la anterior (0,7185 y 0,2815 de 0,2806),
y los pesos internos son los de antes reescalados.

`ratio_motos_autos` va a Consumo aunque el pedido no lo nombra: descompone la
motorización y no tiene sentido sin ella.

Sobre la duda de Luis (¿la carne es consumo o producción?): el nivel es el
consumo aparente por habitante de la Secretaría de Agricultura, y el
movimiento mensual sale de la faena del INDEC, que es producción. Queda dicho
en la ficha.

### Consecuencias

- Con los datos del 26-oct-2026: índice de impacto social 93,6 → 93,6; la
  dimensión que era 109,0 se lee como Ingresos 114,6 y Consumo 94,6.
- Consumo pesa 7,9 % del índice: es una dimensión chica, que cambia poco el
  total aunque se mueva mucho.

### Confirmación

`tests/test_itvc.py` fija las dos dimensiones y sus pesos.

## Pros y contras de las opciones

- Conservar los pesos: el índice no se mueve y se ve qué pasa con cada mitad;
  Consumo queda con poco peso.
- Pesos nuevos: daría más peso al consumo, pero es una recalibración que nadie
  pidió.
