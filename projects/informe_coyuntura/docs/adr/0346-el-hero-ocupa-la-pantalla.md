---
madr: 4
id: '0346'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'transversal'
archivos: ['web/public/overrides.css']
relacionado: ['0343']
ambito: 'Portada — el hero ocupa el alto de la ventana en escritorio'
origen: 'Pedido de Juan del 7-oct-2026: «que ocupe todo el alto el hero bien centrado» (pantalla 1920×1080).'
---

# ADR-0346 — El hero ocupa la pantalla

## Contexto y planteo del problema

El hero de la portada mide 630 px en cualquier pantalla y el menú 75 px. En una
pantalla de 1920×1080 la ventana útil del navegador ronda los 950 px, así que
abajo asomaban unos 250 px de la sección siguiente, cortados, y el veredicto no
quedaba como lo único de la primera pantalla.

## Factores de decisión

- Que la portada abra con el veredicto solo, centrado.
- No perjudicar celulares ni ventanas bajas.

## Opciones consideradas

1. Alto mínimo de la ventana menos el menú, con el contenido centrado, sólo en
   pantallas anchas y altas.
2. Lo mismo en todas las pantallas.
3. Agrandar tipografías y márgenes para llenar el espacio.

## Decisión

**Opción 1.** Con `min-width: 900px` y `min-height: 640px`, `.cg-hero` toma
`min-height: calc(100svh - 75px)` y centra su contenido en vertical. En celular y
en ventanas bajas queda como estaba.

### Consecuencias

- En 1920×1080 y en 1440×900, menú más hero ocupan exactamente la ventana, con
  el contenido centrado (medido: 187 px arriba y 180 abajo en 1920).
- El muro de acceso de la portada, que salta al salir del hero (ADR-0342), ahora
  aparece después de bajar una pantalla entera.
- Si el menú cambia de alto, hay que ajustar los 75 px.

### Confirmación

Medido con el navegador sobre el build en 1920×950, 1440×800 y 390×844.

## Pros y contras de las opciones

### Opción 1 — Sólo escritorio

- Bien: resuelve lo pedido sin tocar celulares.
- Mal: un número fijo para el alto del menú.

### Opción 2 — Todas las pantallas

- Mal: en celular empuja la lectura del mes fuera de vista.

### Opción 3 — Agrandar el contenido

- Mal: cambia la jerarquía tipográfica para llenar un hueco.

## Más información

- ADR-0343: el resto de los cambios de la portada del mismo día.
