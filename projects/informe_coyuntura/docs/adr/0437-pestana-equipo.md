---
madr: 4
id: '0437'
estado: 'aceptado'
fecha: 2026-11-25
archivos: ['web/src/pages/equipo/index.astro', 'web/src/components/Nav.astro', 'web/public/overrides.css']
ambito: 'Página «Equipo» del Monitor y su pestaña en el menú'
origen: 'Luis Babino, 13 al 16-nov-2026 (WhatsApp): la lista y los cargos del equipo.'
---

# ADR-0437 — Pestaña «Equipo»

## Contexto y planteo del problema

El Monitor no decía quién lo hace. Luis pidió una pestaña con el equipo y el 16-nov-2026 mandó la lista con
los cargos.

## Opciones consideradas

1. Nombres y cargos, sin foto ni bio.
2. Con foto y bio corta.

## Decisión

**Opción 1.** Al 13-nov se le preguntó si llevaban foto o bio, y la lista del 16 trae sólo nombres y cargos. La
página va en `/equipo/` y su pestaña, última del menú, al lado del Glosario. Con nueve pestañas el menú de escritorio ya no entraba en un renglón, así que el espacio entre pestañas pasa de 22 a 18 px:

- Coordinador: Luis Babino.
- Desarrollador: Juan Ignacio Pintos.
- Colaboradores: Diego Dequino, Marcos Jasin, Juan Ignacio Babino y Pablo Dalesandro.

Heber Farfán figuraba en la lista del 14-nov y no en la del 16; vale la del 16.

### Consecuencias

Es una página estática sin nada que se toque: no lleva evento propio de GA, la visita la cuenta la vista de
página. Si más adelante llegan fotos o bios, se suman a `GRUPOS` en la misma página.

### Confirmación

`npm run build` genera `/equipo/` y la pestaña aparece en el menú de todas las páginas.
