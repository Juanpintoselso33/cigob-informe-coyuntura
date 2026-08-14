---
madr: 4
id: '0202'
estado: 'aceptado'
fecha: 2026-08-13
cinturon: 'transversal'
archivos: ['web/src/pages/metodologia/index.astro', 'web/src/pages/metodologia/[id].astro', 'web/src/components/Metodologia.astro']
relacionado: ['0199', '0201']
ambito: 'Nombre público de /metodologia y los enlaces que la nombran'
origen: 'Última deuda declarada en ADR-0199 y 0201; el editor pidió cerrarla'
---

# ADR-0202 — La página se llama Metodología, no «Diccionario de indicadores»

## Contexto y planteo del problema

`/metodologia` se llamaba **«Diccionario de indicadores»** desde que nació
(2026-07-06), y era exacto: era el índice de las fichas, una por indicador.

Dejó de serlo hoy. [[0199-el-marco-conceptual-vuelve-en-metodologia]] le puso
adelante el marco conceptual del informe, y antes el refactor de la portada le
había mudado los controles de credibilidad (robustez, validación externa,
ponderación por fase, regla de lectura). El diccionario pasó a ser la mitad de
abajo de la página, no la página.

[[0201-el-nav-manda-a-la-pagina-de-metodologia]] hizo que el Nav mandara acá con
el rótulo «Metodología», así que el desajuste quedó a la vista: hacés clic en
«Metodología» y aterrizás en un h1 que dice otra cosa.

## Factores de decisión

- El rótulo del Nav y el título de la página tienen que coincidir: si no, cada
  llegada empieza con una duda sobre si el clic hizo lo que parecía.
- El nombre tiene que describir lo que la página es hoy, no lo que fue.
- No perder el dato de que adentro hay un diccionario: eso ahora lo dice el
  lead, no el título.
- La URL no se toca: `/metodologia` ya era correcta y está citada desde la
  portada, el footer y cada ficha.

## Opciones consideradas

- **A. «Metodología».**
- **B. «Metodología y diccionario de indicadores».**
- **C. Dejar el h1 y cambiar el rótulo del Nav a «Diccionario».**
- **D. Partir la página en dos**, marco y diccionario.

## Decisión

**Opción A.** El h1 pasa a «Metodología», y con él el `<title>` del navegador.
Arrastra tres renombres más, porque el nombre viejo se citaba desde otras
pantallas:

| Dónde | Antes | Ahora |
|---|---|---|
| `metodologia/index.astro` · h1 y `<title>` | Diccionario de indicadores | **Metodología** |
| `metodologia/index.astro` · eyebrow | ← Resumen · Metodología | ← Resumen |
| `metodologia/[id].astro` · eyebrow | ← Diccionario | ← Metodología |
| `metodologia/[id].astro` · pie de ficha | ← Diccionario de indicadores | ← Todas las fichas y el marco |
| `Metodologia.astro` · CTA de la portada | Abrir el diccionario → | Abrir la metodología → |

El eyebrow del índice pierde el « · Metodología» porque con el h1 nuevo repetía
la palabra dos veces en dos líneas seguidas.

El pie de ficha no pasa a «← Metodología» a secas: ahí el lector viene de leer
UNA ficha y lo que quiere saber es qué hay del otro lado. «Todas las fichas y el
marco» lo dice; «Metodología» lo esconde detrás de una categoría.

### Consecuencias

- Nav, footer, portada y fichas nombran la página igual.
- Se pierde la palabra «diccionario» como nombre, que era buena y descriptiva.
  Sobrevive donde sigue siendo cierta: el lead de la página («una ficha
  metodológica por indicador…») y el CTA de la portada, que cuenta fichas.
- Cierra la última deuda declarada del hilo 0199-0200-0201.

### Confirmación

Ninguna. Es un renombre de rótulos: `npm run build` y la lectura de las tres
pantallas (índice, ficha, portada). No se le agrega test — el archivo
`test_marco_conceptual.py` protege que el marco esté publicado y que se pueda
llegar, que es lo que puede romperse en silencio; un h1 que cambia se ve.

## Pros y contras de las opciones

- **A. «Metodología».** A favor: coincide con el Nav, describe la página
  entera, una sola palabra. En contra: pierde el nombre que anunciaba las 73
  fichas.
- **B. «Metodología y diccionario de indicadores».** A favor: no pierde nada.
  En contra: es un título que explica en vez de nombrar, y ningún otro h1 del
  sitio hace eso.
- **C. Cambiar el Nav a «Diccionario».** A favor: cero cambios en la página.
  En contra: manda a leer «diccionario» a quien va a buscar el marco, que es lo
  primero que se ve al llegar. Arregla el desajuste por el lado equivocado.
- **D. Partir en dos páginas.** A favor: cada una con su nombre exacto. En
  contra: un ítem más de navegación y dos páginas que se leen juntas — es lo
  que 0200 ya descartó para la portada, por lo mismo.

## Más información

- La URL `/metodologia` no cambia, así que no hay enlaces rotos ni redirects
  que escribir.
- Con esto no queda ninguna deuda abierta del hilo que empezó con el borrado
  del marco en `1f6aa0e`.
