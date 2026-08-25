---
madr: 4
id: '0204'
estado: 'aceptado'
fecha: 2026-08-14
cinturon: 'transversal'
archivos: ['web/src/components/NivelTension.astro', 'web/src/components/Hero.astro', 'web/src/components/CinturonCard.astro', 'web/src/components/IndicadorModal.astro', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/index.astro', 'web/public/overrides.css', 'tests/test_web_semaforo.py']
supersede_parcialmente: ['0194']
relacionado: ['0181', '0237']
ambito: 'Capa visual del informe · portada, cinturones, dimensiones y modal'
origen: 'Luis Babino: el concepto de velocímetro no le gusta y hay que sacarlo de todos lados'
---

# ADR-0204 — La tensión se lee en una barra recta, no en un velocímetro

## Contexto y planteo del problema

[[0194-la-aguja-es-la-lectura-primaria]] montó la lectura del informe sobre una
**aguja de arco**: un semicírculo partido en los cuatro tramos del semáforo con
un puntero en el valor. Resolvió lo que tenía que resolver —el estado se
entiende antes de leer cifras— y quedó en cuatro superficies: el hero de la
portada, las cinco cards de cinturón, la cabecera de cada página de cinturón y
la card de cada dimensión, más un clon en JS dentro del modal.

El problema no es de implementación: es que la forma **significa algo que el
informe no quiere decir**. Un semicírculo con aguja es el tablero de un auto, y
arrastra con él la idea de velocidad, de aceleración y de una lectura
instantánea que se mira de reojo. Lo que el informe publica es otra cosa: una
posición sobre una escala 0-10 definida y documentada, que se compara contra sí
misma mes a mes. Luis Babino lo señaló directamente y pidió sacar la metáfora.

Al ir a sacarla apareció el alcance real: la aguja no estaba en un lugar sino en
seis, dibujada por dos implementaciones distintas de la misma geometría —el
componente Astro y su gemelo en JavaScript para el modal, que se escribió
duplicado a propósito para no tener que decidir el umbral dos veces—.

## Factores de decisión

- Sacar la metáfora del tablero, no sólo cambiar el dibujo.
- No perder ninguna de las tres garantías de accesibilidad que ADR-0194 dejó
  peleadas: pista de referencia neutra, color nunca como único canal, y
  comportamiento explícito en impresión y `forced-colors`.
- Los umbrales siguen sin escribirse en el front.
- La barra tiene que servir a seis contextos con anchos muy distintos (una card
  de 260 px y una banda de 720) sin engordar en el más ancho.

## Opciones consideradas

- **Una barra recta con los cuatro tramos y un marcador** — elegida.
- **Sólo el número y un chip de color.** Descartada: sin pista se pierde la
  escala —3,5 no dice dónde cae sin ir a buscar la leyenda— y el color queda
  como único canal no textual, que es exactamente lo que ADR-0194 prohíbe.
- **Bloques discretos 0-10, del estilo del genoma de dimensiones.** Descartada:
  compite con el genoma, que ya vive en la misma card y significa otra cosa.
- **Número grande con una barra fina de progreso debajo.** Descartada: la barra
  de un solo color deja de mostrar los cuatro tramos, y con eso se va la
  referencia de en qué zona cae el valor.

## Decisión

### 1. `NivelTension.astro` reemplaza a `Aguja.astro`

Misma información y mismo contrato de props (`tension`, `titulo`, `tamano`,
`pie`, `ocultarTitulo`); cambia la geometría. La pista es recta, los cuatro
tramos del semáforo se dibujan atenuados, el que contiene el valor va saturado
**y más grueso**, y un marcador vertical oscuro cruza la banda en el valor.
`Aguja.astro` se borra: no queda una variante "por si acaso" que se pueda
reintroducir sin querer.

Lo que **no** cambia, porque es lo que hacía legible a la aguja: los tramos
salen de `tramosSemaforo()`, que lee `informe.semaforo_cortes`. Sigue sin haber
un solo umbral escrito en el front.

### 2. La barra ocupa el ancho que le den sin engordar

Es el problema que la geometría de arco no tenía. Si el viewBox escalara
parejo, la misma pista mediría 56 px de alto en una card y 144 en el hero.
Entonces el SVG se estira **sólo en X** (`preserveAspectRatio="none"`), cada
trazo lleva `vector-effect="non-scaling-stroke"` para que los grosores se
resuelvan en píxeles de pantalla, el viewBox mide en unidades lo mismo que el
CSS le da en píxeles —así la escala vertical es exactamente 1 y las `y` del
trazado son píxeles reales— y los rótulos 0/10 salen del SVG a HTML, porque
adentro el estirado horizontal los dejaría anchos y chatos.

Las cuatro cosas son un solo mecanismo: tocar una sin las otras deforma el
dibujo.

### 3. El hero y la cabecera de cinturón pasan a una columna

La aguja era alta y angosta y pedía una columna propia al lado del texto. La
barra es ancha y baja: en esa columna quedaba apretada. Las dos cabeceras pasan
a una sola columna con la barra de banda debajo del texto, con techo de 720 px
para que la lectura y el número no queden a un palmo uno del otro.

### 4. En la card conviven dos barras horizontales, y se distinguen

La card de cinturón tiene ahora la barra de **nivel** (pista continua 0-10 con
marcador) y el **genoma** (bloques separados, uno por dimensión, ancho = peso).
Se separan por textura —continua contra bloques con huecos—, por alto y por
rótulo propio. Está anotado en el componente: si alguna vez se las hace
parecidas, la card deja de leerse.

### 5. De paso: el bloque `@media print` nunca se había aplicado

Al reescribir el CSS y mirar el render en gris apareció que la regla de
impresión de ADR-0194 era **letra muerta desde el día uno**. Decía:

```css
@media print { .cg-aguja-tramo { stroke: none; } }
```

Una clase de especificidad, contra `.cg-aguja-tramo.sem-verde.is-activo`, que
tiene tres y gana **aunque esté antes en el archivo** —la especificidad manda
sobre el orden—. Los tramos salían impresos con su color igual, y el
comportamiento en papel que el ADR anterior declaraba no existía. No falló
nada porque ningún test mira el render, sólo que los tokens estén definidos.

Se reemplaza por una rampa de grises explícita, con los selectores completos
repetidos en vez de apoyarse en el orden: tramos inactivos en `#D8D8D8`, el
activo en `#5A5A5A` y además más grueso, separadores en blanco y marcador en
negro. El bloque `forced-colors` tenía el mismo defecto y se corrige igual.

### 6. Los anillos radiales del modal se quedan

`gaugeChart()` (ApexCharts, `radialBar`) sigue dibujando `avance`, `nivel 0-100`
y `aporte de tensión` en el modal de indicadores. Es un gráfico de progreso, no
un velocímetro con aguja, y el pedido era sobre la aguja. Queda anotado como
revisable si la objeción se extiende.

### Consecuencias

- La lectura primaria deja de tener forma de tablero de auto.
- Hay una segunda superficie que replica la geometría a mano —`nivelHTML()` en
  el modal— y sigue siendo un riesgo de deriva: si se cambian los números en
  `NivelTension.astro` y no allá, el modal dibuja otra barra. La alternativa
  (importar el componente en el cliente) traería `datos.ts` entero al bundle.
- La aguja desaparece de la prosa del sitio: `/metodologia` y los comentarios
  que la nombraban dicen "barra de tensión".

### Confirmación

- `tests/test_web_semaforo.py` incorpora que `NivelTension.astro` lea
  `tramosSemaforo()` y no escriba ningún corte a mano — el invariante que hasta
  ahora sólo cubría `web/src/lib/*.ts` y `SemaforoLeyenda.astro`.
- `npx tsc --noEmit`, `npm run build` y `python -m pytest tests -q` en verde
  (2175 tests).
- Verificado **mirando el render**, no sólo el código: portada y página de
  cinturón en el preview local, y la barra del modal —que no se puede abrir por
  URL— extrayendo `nivelHTML()` del bundle publicado y ejecutándola con los
  cortes reales del snapshot, un caso por tramo. Ese último paso es el que
  encontró el defecto de impresión del punto 5.
- Pendiente honesto: sigue sin haber ningún test que mire el render. El defecto
  de `@media print` vivió tres días sin que nada fallara, y el bloque nuevo
  tampoco tiene quién lo vigile.

## Pros y contras de las opciones

**Barra recta con los cuatro tramos** (elegida)

- Bueno, porque saca la metáfora sin perder ninguno de los canales redundantes.
- Bueno, porque una escala recta es lo que el informe realmente publica.
- Malo, porque obliga a un mecanismo de escalado no evidente (punto 2) para no
  engordar en los contenedores anchos.

**Sólo número y chip**

- Bueno, porque es lo más simple de mantener.
- Malo, porque deja el color como único canal no textual y borra la escala.

## Más información

- Los cortes vienen de `parametrica.CORTES_SEMAFORO` vía `publicar._semaforos()`.
- De las cuatro decisiones de [[0194-la-aguja-es-la-lectura-primaria]], este ADR
  sólo reemplaza la primera. Siguen vigentes: una sola vara de color, el color
  nunca como único canal, y la metodología fuera de la portada. La zona muerta
  entre 6 y 7 que aquel ADR dejó reportada tampoco se toca: sigue siendo una
  cuestión de metodología, no de presentación.
