---
madr: 4
id: '0420'
estado: 'aceptado'
fecha: 2026-11-03
cinturon: 'politica'
indice: 'ITCP'
archivos: ['scripts/itcp.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts']
relacionado: ['0088']
ambito: 'ITCP · nombre público de la dimensión `sector_privado`'
origen: 'Juan, 3-nov-2026, en el repaso para la reunión con Luis y Marcos; Luis lo confirmó en su revisión del mismo día.'
---

# ADR-0420 — La dimensión «Sector privado» pasa a llamarse «Sector empresarial»

## Contexto y planteo del problema

La dimensión mide lo que dicen en público las cámaras empresarias (industria, comercio,
campo y construcción). «Sector privado» abarca también a trabajadores y hogares, que no
están adentro.

## Factores de decisión

- Que el nombre diga a quién mide.

## Opciones consideradas

- **«Sector empresarial» (elegida).**
- Dejar «Sector privado».

## Decisión

Cambia sólo el nombre público. La clave interna `sector_privado`, los indicadores, los
pesos y el cálculo quedan igual. Los registros históricos de las fichas conservan el
nombre de su momento.

### Consecuencias

- Ningún número cambia.

### Confirmación

El nombre sale de `itcp.DIMENSIONES_ITCP` hacia el snapshot; se verifica en el sitio.

## Más información

[[0088]] creó la dimensión.
