---
madr: 4
id: '0442'
estado: 'aceptado'
fecha: 2026-11-27
cinturon: 'transversal'
archivos: ['web/src/lib/seo.ts', 'web/src/pages/index.astro', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/[id].astro', 'web/src/pages/metodologia/index.astro', 'web/src/pages/glosario/index.astro', 'web/src/pages/equipo/index.astro', 'web/src/pages/archivo/index.astro', 'web/tools/emitir-artifact.mjs']
relacionado: ['0337', '0439', '0440']
ambito: 'Presentación · título y descripción de cada página para buscadores y vista previa'
origen: 'Juan, 27-nov-2026, sobre la propuesta de títulos de la investigación de SEO: «Dale, sí, hace eso, está bueno».'
---

# ADR-0442 — Títulos y descripciones para buscadores

## Contexto y planteo del problema

Todas las páginas tenían la misma meta description, la de la portada, y los títulos repetían un sufijo de 39
caracteres («· Monitor del Plan de Gobierno · CiGob») detrás del rótulo de la card. El rótulo está escrito para
leerse dentro del tablero («Inflación del mes», «Reservas netas»), no para lo que la gente busca. Google corta
el título cerca de los 60 caracteres, así que el sufijo se comía el espacio y lo buscado no aparecía. Las
fotos de `/archivo/AAAA-MM/` tenían todas el título de la portada.

## Factores de decisión

- Que cada página tenga un título y una descripción propios.
- Que lo que la gente escribe en el buscador vaya primero.
- No tocar los rótulos de las cards ni los encabezados de las páginas.
- La tensión se dice con la palabra del tramo, nunca con número (ADR-0337).

## Opciones consideradas

1. Un archivo (`web/src/lib/seo.ts`) con el término de búsqueda de cada ficha y las descripciones armadas con
   el dato y el mes del snapshot.
2. Sumar el término de búsqueda a cada entrada de `fichas.ts`.
3. Dejar los títulos y escribir sólo las descripciones.

## Decisión

**Opción 1.** Un solo lugar para todo lo que es buscador, separado del contenido editorial de las fichas.

- **Título:** hasta 60 caracteres con « | CiGob» al final (tope duro 65). En las fichas de indicador es el
  término de búsqueda (por ejemplo «Inflación mensual en Argentina (IPC del INDEC)»); sin término propio, el
  rótulo con «en Argentina». En las fichas de índice va la sigla y el nombre largo. La portada y los cuatro
  cinturones tienen el suyo.
- **Descripción:** de 120 a 155 caracteres. En las fichas de indicador abre con el rótulo, el valor y el mes
  del dato; en los cinturones, los índices y la portada, con el mes de la edición y la palabra del tramo. Se
  arma en cada build, así que sigue al dato sin tocar nada.
- **Fotos del archivo:** el título lleva el mes de la edición.
- El build falla si un título pasa de 65 caracteres, si dos páginas comparten título o si queda un término de
  búsqueda sin ficha.

### Consecuencias

- Cada ficha nueva entra con el rótulo como título hasta que se le escriba su término de búsqueda.
- Los encabezados de las páginas no cambian: el término de búsqueda está en el título y no en el encabezado.

### Confirmación

En producción, `https://monitor.cigob.org/metodologia/ipc_total/` trae el título nuevo y una descripción con
el último dato. El efecto se mide en el informe mensual de tráfico (ADR-0440): clics e impresiones de Search
Console por página.

## Pros y contras de las opciones

- **Opción 1.** A favor: todo lo de buscadores en un archivo con sus guardas. En contra: un mapa más que
  mantener junto a `fichas.ts`.
- **Opción 2.** A favor: todo de la ficha en un lugar. En contra: mezcla el buscador con el contenido
  editorial de 4.500 líneas.
- **Opción 3.** En contra: el título sigue sin decir lo que se busca.

## Más información

Investigación de SEO del 26-nov-2026: autocompletado de Google para Argentina, títulos de las páginas que hoy
aparecen primero y consultas de Search Console de informe.cigob.org.
