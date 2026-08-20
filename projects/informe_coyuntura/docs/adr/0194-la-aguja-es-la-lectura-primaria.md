---
madr: 4
id: '0194'
estado: 'aceptado'
nota_estado: 'La decisión 1 (la aguja de arco como lectura primaria) la reemplazó ADR-0204 por una barra recta. Las otras tres siguen vigentes.'
fecha: 2026-08-12
cinturon: 'transversal'
archivos: ['web/src/components/Aguja.astro', 'web/src/components/Hero.astro', 'web/src/components/CinturonCard.astro', 'web/src/components/TensionPanel.astro', 'web/src/components/Metodologia.astro', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/index.astro', 'web/src/lib/datos.ts', 'web/public/overrides.css']
relacionado: ['0181', '0195', '0199', '0200', '0213']
superado_parcialmente_por: ['0204']
ambito: 'Capa visual y textual del informe · portada, cinturones y metodología'
origen: 'Rediseño pedido por el editor: que el estado se lea por color y posición antes que por número, con menos texto'
---

# ADR-0194 — La aguja es la lectura primaria, y el color deja de tener dos varas

## Contexto y planteo del problema

El informe publica una tensión 0-10 por cinturón y un semáforo de cuatro
colores ([[0181-el-color-es-la-tension-que-ya-se-publica]]), pero la presentación seguía
siendo numérica: para saber si el país está mejor o peor había que leer cifras
y compararlas contra umbrales que no están a la vista. El titular de la portada
eran cuatro números sueltos y seis líneas de prosa institucional.

Al montar la lectura por color apareció algo que la presentación anterior
tapaba: **sobre la misma tensión 0-10 conviven dos particiones distintas y no
coinciden.**

| Cinturón | Tensión | `estado` (3 valores) | Semáforo (4 colores) |
|---|---:|---|---|
| Macroeconomía | 3,9 | en_tension | **verde** |
| Política | 3,5 | en_tension | **verde** |
| Vida cotidiana | 6,9 | tensionado | **naranja** |
| Gestión | 2,3 | estable | verde |

La card decía "EN TENSIÓN" en amarillo mientras el mismo número era verde para
el semáforo, y el hero llegaba a anunciar "1 cinturón en rojo" sin que ninguna
aguja estuviera roja. Los dos veredictos son legítimos por separado —`estado`
alimenta la regla sistémica del informe, el semáforo alimenta el color— pero
puestos juntos en la misma pantalla se leen como un error.

## Factores de decisión

- Una sola vara para el color en todo el sitio.
- No tocar metodología: `estado` y sus umbrales son del pipeline.
- El color no puede ser el único canal (daltonismo, gris, lectores de pantalla).
- Los umbrales no se escriben en el front.

## Opciones consideradas

- **Unificar el CANAL VISUAL y dejar que `estado` hable en su vocabulario** — elegida.
- **Unificar las dos escalas en una.** Descartada: es cambiar metodología desde
  la capa de presentación, y `estado` tiene consecuencias más allá del color.
- **Mostrar los dos veredictos juntos y explicar la diferencia.** Descartada:
  duplica la carga de lectura justo donde el rediseño quiere quitarla.
- **Dejar el color como estaba.** Descartada: es el pedido del rediseño.

## Decisión

### 1. La aguja de temperatura es la lectura primaria

`Aguja.astro` dibuja la tensión 0-10 sobre un arco partido en los tramos que
publica `informe.semaforo_cortes`. No hay ningún umbral escrito en el front: si
cambian los cortes, la aguja se redibuja sola. Va en el hero, en cada card de
cinturón y en la cabecera de cada página de cinturón.

### 2. El color sale de una sola vara; `estado` conserva su palabra

Todo color de cinturón se deriva de los cortes publicados
(`colorPorTension()` en `datos.ts`). El `estado` **no se toca ni se
reinterpreta**: sigue mandando en la regla sistémica, pero se expresa con su
propio valor —"tensionado"— en vez de pedirle prestada la palabra "rojo" a una
escala que no es la suya. Con eso desaparece la contradicción visible sin mover
un solo umbral.

**Queda abierto del lado de la metodología**, y son TRES particiones, no dos.
Sobre la misma tensión 0-10:

```text
semáforo (color)      verde ≤4 · amarillo ≤6 · naranja ≤8 · rojo >8
estado                estable ≤3 · en_tension ≤6 · tensionado >6
alerta multicinturón  cuenta sólo los cinturones con score >= 7
```

Ninguna coincide con las otras, y entre 6 y 7 hay una **zona muerta**: un
cinturón queda clasificado "tensionado" y NO cuenta para la alerta. Con el
snapshot de agosto de 2026 le pasa a vida cotidiana, en 6,9.

Eso se descubrió intentando mostrarlo: una versión de esta página llegó a
publicar un chip que decía "Cuenta para la alerta sistémica: Sí" para vida
cotidiana, que es falso. El chip se retiró. Escribir el 7 en el front para
arreglarlo sería meter un umbral de metodología en la capa de presentación,
que es justo lo que este ADR evita.

Esta decisión sólo deja de exhibir la inconsistencia como si fuera un error de
la página; **no la resuelve**.

### 3. El color nunca es el único canal

Cada aguja lleva un arco base neutro con marcas y números en los extremos (0 y
10), la posición del puntero, una etiqueta con el nombre del tramo y un
`aria-label` que dice tensión, lectura y color en una frase. Hay reglas de
`@media print` —donde los tramos de color se apagan del todo y mandan la
posición y el texto— y de `forced-colors`.

El panel de tensión sistémica da la lectura en texto por cinturón y **nombra**
cuál dispara la regla, en vez de dejar que el lector deduzca cuál es el punto
distinto.

### 4. La metodología sale de la portada

Los cuatro bloques de credibilidad (robustez Monte Carlo, validación externa,
ponderación por fase, regla de lectura) se **mudan** a `/metodologia`: no es
coyuntura y no vivían allá. En la portada queda el recorrido del dato con
números vivos, que es credibilidad de un vistazo y no prosa.

### Consecuencias

- El estado del informe se entiende sin leer cifras.
- `verdictDeCinturon()` deja de pintar: sólo alimenta el conteo de la regla.
- La página de inicio pierde ~330 palabras de prosa metodológica.

### Confirmación

- `tests/test_web_semaforo.py` y `test_web_labels.py` siguen verdes.
- Revisión adversarial con Codex sobre el primer paso: encontró tres problemas
  reales —el panel dependía sólo del color, la falta de cortes se anunciaba
  como "sin dato" mientras se imprimía el número, y los tramos atenuados
  desaparecían en gris—. Los tres están corregidos acá.

## Pros y contras de las opciones

**Unificar el canal visual** (elegida)

- Bueno, porque el sitio pasa a tener una sola vara de color.
- Bueno, porque no toca metodología.
- Malo, porque la inconsistencia de fondo sigue existiendo, ahora sin síntoma
  visible que la recuerde. Por eso queda escrita acá.

**Unificar las dos escalas**

- Bueno, porque elimina el problema de raíz.
- Malo, porque es una decisión de metodología tomada desde el front.

## Más información

- **La decisión 1 ya no está vigente.** La aguja de arco la reemplazó una barra
  recta en [[0204-la-tension-se-lee-en-una-barra-recta]]: el editor pidió sacar
  la metáfora del velocímetro. Las decisiones 2, 3 y 4 de este ADR siguen
  mandando —una sola vara de color, el color nunca como único canal, y la
  metodología fuera de la portada—, y la zona muerta entre 6 y 7 que queda
  reportada arriba sigue abierta del lado de la metodología.
- Los cortes vienen de `parametrica.CORTES_SEMAFORO` vía `publicar._semaforos()`.
- `estado` sale de `_estado()` en `generar_informe.py`, con sus propios umbrales.
