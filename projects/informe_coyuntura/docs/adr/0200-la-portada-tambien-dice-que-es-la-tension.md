---
madr: 4
id: '0200'
estado: 'aceptado'
fecha: 2026-08-13
cinturon: 'transversal'
archivos: ['web/src/components/MarcoTension.astro', 'web/src/pages/index.astro', 'web/public/overrides.css', 'tests/test_marco_conceptual.py']
relacionado: ['0194', '0199']
ambito: 'Capa textual de la portada — la definición del concepto que el tablero mide'
origen: 'Pedido del editor el mismo día que se repuso el marco en /metodologia: la explicación también tiene que estar en el home'
---

# ADR-0200 — La portada también dice qué es la tensión

## Contexto y planteo del problema

[[0199-el-marco-conceptual-vuelve-en-metodologia]] repuso el encuadre en
`/metodologia` y descartó explícitamente devolverlo a la portada, porque eso es
lo que [[0194-la-aguja-es-la-lectura-primaria]] había decidido sacar. El editor
pidió, el mismo día, que la explicación esté además en el home.

El pedido es correcto y 0199 lo resolvió sólo a medias. La portada muestra una
aguja grande de «Tensión general», cinco agujas de cinturón, una leyenda de
semáforo que dice «el color es la misma tensión 0–10» y un BLUF que habla de
«tensiones que no se procesan». **Todo eso nombra la tensión y nada la define.**
Mandar al lector a otra página para saber qué es lo que está mirando es pedirle
un clic para entender la pantalla en la que ya está.

Lo que 0194 sacó, y sigue sin volver, es otra cosa: un párrafo institucional de
seis líneas *arriba de todo*, antes de que se viera un solo dato. El problema
de aquel bloque era la posición y el tamaño, no que explicara el concepto.

## Factores de decisión

- No reconstruir el paredón: el estado se tiene que seguir entendiendo antes de
  leer, que es el núcleo de 0194.
- No duplicar `/metodologia`: en la portada va la definición, no el encuadre
  completo (Matus, los cinco cinturones, el barbarismo).
- Que caiga donde nace la pregunta, no antes.
- Sin umbrales escritos en el front, como en 0194 y 0199.

## Opciones consideradas

- **A. Un bloque compacto entre el BLUF y las cards.**
- **B. Sumar las frases al `cg-hero-lead`.**
- **C. Expandir el subtítulo de «Los cinturones, hoy».**
- **D. Un tooltip o un desplegable sobre la aguja.**

## Decisión

**Opción A.** `MarcoTension.astro`: dos frases —la definición de tensión y la
dirección de la escala 0-10— más un enlace «El marco completo →» a
`/metodologia/#marco`. Va después del BLUF y antes de las cards, que es el punto
donde el lector pasa de «cómo viene el mes» a cinco números que dicen 0-10.

Se presenta como nota de lectura, no como card de datos: fondo tenue, borde de
acento a la izquierda y sin sombra, el mismo tratamiento que `.cg-tension-rule`.
Así no compite con el BLUF que tiene arriba ni con las cinco cards de abajo.

La primera frase es la del texto institucional original, recortada a su oración
de apertura; el encuadre entero —marco CIGOB-Matus, los cinco cinturones uno por
uno, el barbarismo— sigue viviendo sólo en `/metodologia`.

### Consecuencias

- La portada define el concepto que mide, sin volver a abrir con seis líneas de
  prosa: son 2 párrafos cortos y llegan recién en el tercer bloque de la página.
- Queda una redundancia deliberada entre la portada y `/metodologia`: la
  definición se dice dos veces. Es el precio de que ninguna de las dos páginas
  dependa de la otra para entenderse.
- 0199 no se revierte; su decisión (el encuadre completo vive en /metodologia)
  sigue en pie. Esto agrega, no mueve.

### Confirmación

`tests/test_marco_conceptual.py` cubre ahora las dos superficies: la sección de
`/metodologia` y el bloque de la portada. Si alguna de las dos pierde la
definición, falla.

## Pros y contras de las opciones

- **A. Bloque entre el BLUF y las cards.** A favor: cae donde nace la pregunta,
  no interrumpe la lectura del estado y se puede tratar como nota. En contra:
  un bloque más en una portada que el rediseño quiso aligerar.
- **B. Al `cg-hero-lead`.** A favor: cero elementos nuevos. En contra: es
  literalmente reconstruir lo que 0194 sacó, en el peor lugar posible — arriba
  de todo, empujando la aguja hacia abajo.
- **C. Expandir el subtítulo de «Los cinturones, hoy».** A favor: mínimo. En
  contra: los `cg-h2-sub` son de una línea en todo el sitio, y ahí abajo ya
  está la leyenda del semáforo — dos textos explicativos pegados.
- **D. Tooltip o desplegable.** A favor: no ocupa lugar. En contra: esconde
  detrás de una interacción justo lo que hay que entender sin buscar, y no
  existe en móvil sin inventar un patrón nuevo.

## Más información

- La frase de apertura sale del `cg-hero-lead` previo a `1f6aa0e`, igual que en
  0199, recortada a su primera oración.
- Queda abierto lo mismo que dejó 0199: el Nav apunta «Metodología» a
  `/#metodologia`, no a `/metodologia`. Con este bloque el marco completo queda
  a un clic desde la portada, así que aprieta menos.
