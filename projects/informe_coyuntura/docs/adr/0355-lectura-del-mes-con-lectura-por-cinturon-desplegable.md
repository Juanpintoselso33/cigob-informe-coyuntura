---
madr: 4
id: '0355'
estado: 'aceptado'
fecha: 2026-10-13
cinturon: 'transversal'
archivos: ['web/src/components/Bluf.astro', 'web/src/contenido/lectura-del-mes/2026-10.md', 'web/src/contenido/lectura-del-mes/2026-09.md', 'web/public/dashboard.css']
relacionado: ['0211']
ambito: 'Web · la lectura del mes en la portada'
origen: 'Editorial «Lectura sistémica, octubre 2026» que mandó Luis el 13-oct-2026, con un «leer más» para la lectura por cinturón'
---

# ADR-0355 — La lectura del mes con la lectura por cinturón desplegable

## Contexto y planteo del problema

Luis mandó el editorial de octubre: un resumen, una lectura de conjunto y una
lectura por cada cinturón. Pidió que la parte de los cinturones no se vea
entera de entrada sino que se despliegue «al hacer clic», con un «leer más».

La lectura del mes ya tenía su lugar (ADR-0211): un archivo `AAAA-MM.md` por
período que reemplaza a la síntesis automática. Faltaban dos cosas: una forma
de esconder una parte del texto y algo que diga con qué datos se escribió,
porque el tablero diario cambia todas las noches y el texto queda fijo.

## Factores de decisión

- Que lo escriba el equipo sin tocar código: el markdown del mes manda.
- Que funcione sin JavaScript y con teclado.
- Que las cifras del texto no se lean contra datos más nuevos sin aviso.

## Opciones consideradas

1. Un `<details>` dentro del markdown del mes.
2. Un componente con botón y JavaScript propio, y el texto partido en dos archivos.

## Decisión

Opción 1. El archivo del mes puede encerrar en un
`<details class="cg-bluf-mas">` lo que va detrás del «Leer más»; el resumen
dice «Leer más: la lectura por cinturón» y, abierto, «Ver menos». El
frontmatter admite `corte`, que se suma a la nota al pie: «Datos del Monitor
al 11 de octubre de 2026». Al desplegarse se manda el evento
`ver_lectura_cinturones` a GA4, una vez por visita a la página.

Se publica `2026-10.md` con el texto de Luis, con retoques de puntuación. Cada
cifra se cotejó contra el snapshot del 11 de octubre: inflación 1,66 %, REM
21,1 %, saldo comercial 24.460 M, reservas 12.661 M, brecha 5,91 %,
recaudación 91,3 (base 4T-2023), eficacia legislativa 21,4 %, DNU por ley
1,06, conflictividad −27,3 %, planta estatal −21,4 %, 17.606 artículos,
privatizaciones 55,6 %, RIGI 26,9 %, pobreza 31,3 %, 3,84 canastas (111,6
contra 4T-2023), mora 14,72 %, supermercados 89,1, informalidad 37,9 % y
confianza 105,8.

### Consecuencias

- Buena: la portada lleva el texto firmado del equipo y la lectura larga no
  empuja el resto del tablero hacia abajo.
- Buena: un mes sin archivo sigue cayendo a la síntesis automática (ADR-0211).
- A tener en cuenta: el mismo texto va como `2026-10.md` (seguimiento
  diario) y como `2026-09.md`, para que salga ya en `informe.cigob.org`, que
  muestra la foto de septiembre (pedido de Juan, 13-oct). Sus cifras son las
  del 11 de octubre y la nota al pie lo dice; pueden diferir un poco de las
  tarjetas de esa foto.

### Confirmación

En la portada del diario, «La lectura del mes» muestra Resumen y Lectura de
conjunto, un «Leer más: la lectura por cinturón» cerrado que al abrirse muestra
los cuatro cinturones, y la nota «Datos del Monitor al 11 de octubre de 2026».

## Pros y contras de las opciones

### Opción 1

- Bueno, porque el equipo lo maneja desde el markdown y anda sin JavaScript.
- Malo, porque el markdown lleva dos etiquetas HTML.

### Opción 2

- Bueno, porque el markdown queda limpio.
- Malo, porque son dos archivos por mes y más código para lo mismo.

## Más información

ADR-0211 (la lectura del mes y su caída a la síntesis automática).
