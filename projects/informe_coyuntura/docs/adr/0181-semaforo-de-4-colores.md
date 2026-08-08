---
madr: 4
id: '0181'
estado: 'aceptado'
fecha: 2026-08-08
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/parametrica.py', 'tests/test_semaforo.py']
relacionado: ['0182']
ambito: 'Semáforo de 4 colores: capa de lectura que visualiza la tensión 0-10 del informe'
origen: 'La tensión 0-10 ya se publica en el informe; se necesitaba una capa visual de 4 colores para mejorar la legibilidad'
---

# ADR-0181 — Semáforo de 4 colores

## Contexto y planteo del problema

El informe publica una tensión 0-10 para cada índice, que es el marco metodológico
de interpretación. Se necesitaba una capa de lectura simple que traduza esa tensión
a colores visuales (verde, amarillo, naranja, rojo) para mejorar la accesibilidad
de los datos sin modificar la escala metodológica.

## Factores de decisión

- El color NO es una escala nueva, es la tensión 0-10 que ya existe, partida en tramos.
- Para los índices 0-100 (ITCM, ITCG, ITCP), los cortes coinciden con los bordes
  de las bandas de interpretación (60, 40, 20).
- Para el ITVC base-100, surge de despejar su fórmula propia de tensión.
- El cálculo debe hacerse sobre la tensión SIN redondear, para respetar los bordes exactos.

## Opciones consideradas

- Usar la tensión redondeada: rompe el borde en 59.9 (tensión 4.01 → verde incorrecto).
- Definir cortes separados por índice: innecesario complejidad, contradiría el método.

## Decisión

Los cortes están fijos en tensión 4.0, 6.0, 8.0 e infinito, aplicados siempre
a la tensión sin redondear. Cada índice tiene su propia función de conversión.

## Más información

Ver ADR-0182 para los umbrales en unidades propias de cada índice.
