---
madr: 4
id: '0352'
estado: 'aceptado'
fecha: 2026-10-10
cinturon: 'transversal'
archivos: ['web/src/pages/[slug].astro', 'web/public/overrides.css']
relacionado: ['0094', '0106', '0351']
ambito: 'Web · cómo se explica el índice en la página de cada cinturón'
origen: 'Juan, 10-oct-2026: corrección del informe mensual, «esto es para el lector común»'
---

# ADR-0352 — Cómo se calcula el índice, en llano y debajo de sus dimensiones

## Contexto y planteo del problema

La explicación de cada índice era una «Nota metodológica» al final de la
página: un párrafo técnico (anclas, interpolación, escalones de banda,
alícuotas, universos de las fuentes) que el lector común no entendía, y que
política ni siquiera tenía. Además, macro mostraba la sección «Punto de
partida» (ADR-0106) y política la «Lectura por partes» (ADR-0094), que
siguen la misma lógica de examinar el índice en vez de mostrar la coyuntura
que ADR-0351 ya sacó de la página.

## Factores de decisión

- El lector del informe mensual no es especialista: tiene que poder leer qué
  significa el número sin saber qué es una banda o una interpolación.
- La explicación tiene que estar donde aparece el número, no al final.
- Lo técnico no se pierde: está en cada ficha y en la metodología.

## Opciones consideradas

1. Una explicación nueva, en llano, debajo de las tarjetas de dimensiones, y
   sacar la nota del final.
2. Dejar la nota técnica y sumarle un resumen arriba.

## Decisión

Opción 1. Debajo de las tarjetas de dimensiones de cada cinturón va
«Cómo se calcula este número», en cuatro partes:

- qué mide el índice, qué quiere decir 0 y 100 (o 100 en impacto social, el
  promedio del 4º trimestre de 2023) y cuánto marca hoy;
- los tres pasos del cálculo (puntaje de cada indicador, promedio por
  dimensión, promedio ponderado de las dimensiones), con las dimensiones y sus
  pesos leídos del snapshot;
- lo particular de cada cinturón que el lector necesita para no malinterpretar
  el número (las reservas estimadas en macro, que política mide capacidad de
  gobernar y no popularidad, las etapas verificables en gestión, las
  referencias que no son 2023 en impacto social);
- de dónde sale el color y que los cortes son los mismos para los cuatro.

Salen la nota metodológica del final (macro, impacto social, gestión), el
«Punto de partida» de macro y la «Lectura por partes» de política. Los
cálculos de esas dos secciones siguen en el snapshot.

### Consecuencias

- Buena: el número se entiende donde se lee, y los cuatro cinturones explican
  su índice de la misma manera.
- Mala: se pierden de la página detalles técnicos de la nota vieja (la
  composición de la vulnerabilidad financiera, la base de la victimización, el
  universo del registro oficial de delitos). Siguen en las fichas.

### Confirmación

En `/macro/`, `/politica/`, `/vida/` y `/gestion/` aparece «Cómo se calcula
este número» debajo de las tarjetas de dimensiones, con los pesos del día, y
no aparecen «Nota metodológica», «Punto de partida» ni «Lectura por partes».

## Pros y contras de las opciones

### Opción 1

- Bueno, porque la explicación es para el lector del informe.
- Malo, porque el especialista tiene que ir a la ficha para el detalle.

### Opción 2

- Bueno, porque no se pierde nada de la página.
- Malo, porque deja al final un párrafo que el lector común no lee y que
  repite lo que el resumen ya dice.

## Más información

ADR-0094 (lectura por partes del índice político), ADR-0106 (línea de base de
diciembre de 2023) y ADR-0351 (las secciones de validación que ya salieron).
