---
madr: 4
id: '0320'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'transversal'
archivos: ['web/src/pages/index.astro', 'web/src/components/Metodologia.astro']
relacionado: ['0202', '0311']
ambito: 'Portada (`index.astro`) — qué secciones se muestran, no qué se calcula'
origen: 'Apuntes de Juan del 15-sep-2026 (#monitor-de-proyecto-de-gobierno): «ver el tema de acotar lo que se muestra en el home». Elegida la opción «Cómo se construye» entre tres candidatas relevadas.'
---

# ADR-0320 — La portada no explica el método: lo enlaza

## Contexto y planteo del problema

La portada venía creciendo por acumulación: cada sección se agregó cuando hacía
falta y ninguna se sacó nunca. Al 15-sep-2026 el lector recorría, en orden,
titular, bluf, marco de la tensión, los cuatro cinturones, evolución, tensión
sistémica con recomendaciones, y **"Cómo se construye"** — una sección larga
con el recorrido del dato, los cuatro índices paramétricos con su valor vivo, y
un acceso al total de fichas.

Juan pidió acotar la portada sin decir qué recortar. Se relevaron las tres
secciones candidatas y se comparó qué pierde el lector con cada una.

El problema de fondo no es el largo: es que **"Cómo se construye" duplicaba
`/metodologia`**. La página de metodología ya cuenta el marco conceptual, el
método de los cinturones y el diccionario completo de fichas, y está enlazada
desde el Nav (ítem propio, siempre visible) y desde el Footer (dos veces: el
marco y las fichas). La sección de portada era una antesala de algo que estaba
a un clic desde cualquier punto del sitio.

## Factores de decisión

- Qué información **sólo** existe en esa sección de la portada.
- Si el lector conserva un camino evidente hacia lo que se saca.
- Cuánto aporta la sección a la credibilidad en el primer scroll, que es el
  argumento que la puso ahí.

## Opciones consideradas

- **"Cómo va la película"** (`Evolucion.astro`): es el único lugar del sitio
  donde los cuatro cinturones se comparan en un mismo eje temporal. Sacarla
  pierde información que no está en ninguna otra parte.
- **"Qué vigilar este mes"** (`Recomendaciones.astro`): es el único puntero
  automático a qué dimensiones mirar primero. Sacarla deja el veredicto
  sistémico sin bajada operativa.
- **"Cómo se construye"** (`Metodologia.astro`): todo su contenido —el
  recorrido del dato, los índices, las fichas— vive también en `/metodologia`,
  con más detalle.

## Decisión

Se retira **"Cómo se construye"** de la portada y se borra el componente, que
no tenía otro consumidor.

Es la única de las tres cuyo contenido no se pierde: se llega a él por el Nav y
por el Footer, y con más profundidad de la que la sección daba. Las otras dos
son fuentes únicas de su información y se conservan.

### Consecuencias

- La portada termina en la tensión sistémica. El recorrido del dato deja de
  aparecer antes del footer.
- Se pierde la señal de credibilidad en el primer scroll —el argumento original
  de la sección—. Se acepta: el Nav nombra "Metodología" desde la primera
  pantalla, y el marco de la tensión sigue en la portada explicando qué mide el
  número.
- Desaparece de la portada el último `<small>/10</small>` sobre el score
  global, que ADR-0311 había sacado del titular y que esta sección seguía
  mostrando. Los dos cambios quedan coherentes sin trabajo adicional.
- El CSS `.cg-met-*` de `web/public/overrides.css` (~687-765, más su media
  query) queda **sin ningún consumidor**: era exclusivo de esta sección. No se
  poda acá porque está intercalado con `.cg-method` / `.cg-method-grid`, que
  son otro prefijo y **siguen vivos** en `pages/metodologia/index.astro:82,128,142`;
  separarlos a mano bajo el mismo cambio arriesga llevarse una regla viva sin
  que nada lo note. Queda como poda pendiente, con el alcance ya delimitado.

### Confirmación

`npm run build` sin la sección y la portada servida sin referencias a
`cg-met-`; `/metodologia` sigue construyéndose y enlazada desde Nav y Footer.
Ninguna ancla viva apuntaba a `#metodologia` —la única mención era un
comentario en `Nav.astro` sobre una decisión anterior (ADR-0202)—, así que el
borrado no deja enlaces rotos.

## Pros y contras de las opciones

**Retirar "Cómo se construye"** · Bueno, porque no pierde información: es la
única de las tres que se duplica. Bueno, porque acorta la portada donde más
pesaba. Malo, porque el lector que no toca el Nav ya no tropieza con el método.

**Retirar "Cómo va la película"** · Bueno, porque es una sección visualmente
cara. Malo, porque la comparación de los cuatro cinturones en un eje común no
existe en ningún otro lado.

**Retirar "Qué vigilar este mes"** · Bueno, porque el veredicto sistémico
sobrevive solo. Malo, porque es el único puntero a qué dimensiones mirar
primero, y es la sección más accionable de la portada.

## Más información

ADR-0202 movió el marco conceptual a `/metodologia` y renombró la página;
ADR-0311 sacó la escala de 10 del titular en el mismo hilo de apuntes.
