---
madr: 4
id: '0258'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [costo_financiamiento_tesoro]
archivos: ['scripts/macro.py', 'tests/test_macro_costo_financiamiento.py', 'tests/fixtures/colocaciones_2026_07.json', 'tests/fixtures/tireas_corte_oficiales.json']
relacionado: ['0071', '0238']
ambito: 'ITCM · costo del financiamiento del Tesoro · qué tasa mide una colocación fuera de la par'
origen: 'Reauditoría de indicadores, 25-ago-2026, prioridad 0: «en la reapertura S30N6 se anualiza el cupón contractual de 2,30% TEM en vez de usar la TIREA de corte 25,59% determinada por el precio»'
---

# ADR-0258 — Una reapertura rinde lo que dice su precio, no lo que dice su cupón

## Contexto y planteo del problema

`costo_financiamiento_tesoro` ([[0071-costo-financiamiento-tesoro]]) publicó
**5,80% real anual** para julio de 2026, sobre una TIREA nominal de 28,87%.
Julio tuvo dos colocaciones a tasa fija en pesos:

| Instrumento | Licitación | Precio de corte | Valor efectivo | TIREA que publicó Finanzas | TIREA que usó el colector |
|---|---|---|---|---|---|
| S30N6 (`LECAP/$/30-11-2026`, reapertura) | 15-07 | $ 1.194,00 | $ 2.382.801 M | **25,59%** | 31,37% |
| S16O6 (`LECAP/$/16-10-2026`, nueva) | 29-07 | $ 1.000,00 | $ 4.612.305 M | 27,57% | 27,57% |

La segunda estaba bien y la primera no. `_tirea_de_fila` anualizaba el cupón
—`(1 + 2,30%)^12 − 1 = 31,37%`— para **toda** fila con TEM publicada. En una
reapertura el cupón fija el flujo del instrumento, pero el rendimiento lo fija
el precio al que se colocó: quien pagó $1.194 por un papel que ya venía
capitalizando desde diciembre no ganó 31,37% anual, ganó 25,59%. Son 578 puntos
básicos sobre casi un tercio del monto del mes.

**Verificación de primera mano.** La afirmación de la auditoría se comprobó
contra la fuente antes de aceptarla, y hay un matiz que cambia la solución:

- La **gacetilla** del 15-07-2026 publica, textualmente, «S30N6 - reapertura ·
  Precio de corte por cada VNO $ 1.000: $ 1.194,00 · TIREA: 25,59%». La
  auditoría acierta.
- La **planilla de colocaciones**, que es de donde el colector lee, **no publica
  la TIREA**. Sus columnas son instrumento, fecha de emisión, vencimiento,
  cupón, amortización, tipo y moneda, fecha de colocación, valor nominal, valor
  efectivo, precio de emisión, vida promedio y resolución. No hay una columna de
  tasa, ni de corte ni de ninguna otra.

Por eso la primera acción que propone la auditoría —«obtener TIREA/TEM de corte
por licitación»— no se puede hacer desde la planilla, y hacerla desde las
gacetillas obligaría a sumar una fuente HTML sin URL estable, con una página por
licitación. Queda la segunda: **calcular el rendimiento desde el precio y el
flujo**, que es lo que se decide acá.

[[0238-la-tirea-no-se-estima-se-lee]] ya había visto este caso y lo dejó
abierto: «en una reapertura colocada fuera de la par, el indicador informa la
tasa contractual del instrumento, no el rendimiento marginal del precio de
corte. Es una limitación declarada, no un descuido». Lo era. Pero **no es un
caso de borde**: sobre las 177 colocaciones a tasa fija en pesos desde 2023,
**118 se colocaron fuera de la par** y el desvío del cupón contra la tasa de
corte va de **−30,5 pp a +29,2 pp**.

## Factores de decisión

- **El indicador mide el costo de fondearse, no el cupón de un papel.** Lo que
  el Tesoro paga por la plata que se lleva ese día es la tasa de corte.
- **La cuenta tiene que ser reproducible desde la planilla**, que es la única
  fuente con cobertura histórica completa y URL estable.
- **La convención no se elige, se verifica.** ADR-0238 se rompió por suponer una
  convención de días razonable y no contrastarla; suponer otra sería repetirlo.
- **No puede cambiar ningún valor a la par.** Junio de 2026 —el caso que ADR-0238
  arregló— tiene que seguir dando 28,32% y 4,92% real.

## Opciones consideradas

- **A — Dejarlo como está** y documentar mejor la limitación.
- **B — Leer la TIREA de corte de la gacetilla de cada licitación**, sumando un
  scraper HTML como fuente del indicador.
- **C — Reconstruir el rendimiento desde el precio de corte y el flujo**, con la
  convención calibrada contra las tasas que Finanzas sí publica.

## Decisión

**Opción C, con una sola cuenta para todas las filas.**

```
payoff = 1000 · (1 + TEM)^(días de vida / (365/12))     # capitalizable
payoff = 1000                                           # a descuento
TIREA  = (payoff / precio de corte)^(365 / días al vencimiento) − 1
```

Lo que hace que esto sea una simplificación y no una rama más: **a la par la
fórmula devuelve exactamente `(1 + TEM)^12 − 1`**. Con `precio = 1000` y
`colocación = emisión`, los días de vida y los días al vencimiento son los
mismos y los exponentes se cancelan. O sea que la tasa publicada por Finanzas
para una emisión nueva sigue siendo el resultado —no una aproximación de él— y
no hace falta detectar si una fila es reapertura: la misma cuenta cubre los dos
casos. `_tirea_de_fila` pasó de dos ramas a una, y las LEDE a descuento son el
mismo descuento con un payoff de 1.000.

### La convención de días se midió, no se supuso

Un mes son **365/12 días** y un año son **365 días**. No es una elección de
estilo: se determinó ajustando las dos bases contra **catorce TIREA de corte
publicadas** por la Secretaría entre julio de 2025 y agosto de 2026 —precios de
$1.010 a $1.518, plazos remanentes de 15 a 518 días, tasas de 25% a 65%—.

| Convención | Error cuadrático medio | Desvío máximo |
|---|---|---|
| mes 30 · año 360 | 1,08 pp | 2,74 pp |
| mes 30 · año 365 | 1,49 pp | — |
| mes 365/12 · año 360 | 0,58 pp | — |
| **mes 365/12 · año 365** | **0,41 pp** | **1,09 pp** |
| el cupón anualizado (lo que había) | 7,38 pp | 16,47 pp |

Con mes de 30 y año de 360 —la convención que se había supuesto en la
`_tirea_reconstruida` de ADR-0238— el error **crece cuanto más corto es el plazo
remanente**, que es exactamente la firma de una base de días equivocada. Con
365/12 y 365 desaparece. Las catorce observaciones viven en
`tests/fixtures/tireas_corte_oficiales.json`, cada una con la URL de su
gacetilla.

`_tirea_reconstruida` desaparece: era el control de una tasa que se leía, y
ahora la tasa se calcula. Su lugar lo toma **`_tirea_contractual(cup)`**, que
devuelve `(1+TEM)^12 − 1`. El control se dio vuelta con los roles: lo que se
verifica ahora es que a la par las dos coincidan, y se verifica **exactamente**
(tolerancia 1e-12, contra los 5 pb que admitía ADR-0238).

El inventario de colocaciones que viaja con la card lleva ahora las dos tasas,
el precio de corte y una marca de reapertura. Publicar un promedio de 26,8% sin
decir que una de las dos colocaciones cortó casi 6 pp por debajo de su cupón es
la misma opacidad que dejó pasar 32,17% durante meses.

### Consecuencias

- **Julio de 2026 pasa de 5,80% a 4,13% real**; la TIREA nominal, de 28,87% a
  26,83%. El puntaje del indicador sube de **88,3 a 95,3**. El semáforo no
  cambia: los dos valores caen en la zona sana de la U invertida, y lo que se
  corrige es el nivel. La reauditoría estimó 4,18% usando la TIREA oficial
  redondeada de la gacetilla; la reconstrucción da 25,41% donde la gacetilla dice
  25,59%, y esos 18 pb explican la diferencia de 5 pb en el valor final.
- **Junio de 2026 no se mueve**: 28,32% nominal, 4,92% real. Su única colocación
  fue una emisión nueva a la par.
- **La serie histórica se rehace**: cambian **22 de los 40 meses** con
  colocaciones. Los movimientos grandes están donde el precio y el cupón más se
  separaron: septiembre de 2025 sube de 37,88% a 58,81% —el pico de tasas
  posterior a la elección bonaerense, que el cupón no veía porque los papeles
  reabiertos eran viejos y baratos de cupón— y febrero de 2025 baja de 57,05% a
  34,63%. Hay que revisar las bandas contra la serie nueva, no contra la
  anterior.
- Como la serie cambia en casi todos los meses, **la validación externa del ITCM
  hay que recalcularla**: `validacion_externa.py` reconstruye los índices desde
  las series de indicadores.
- La ficha pública tiene que decir «TIREA de corte», no «TIREA», y explicar la
  diferencia en una reapertura.

### Confirmación

`tests/test_macro_costo_financiamiento.py` (24 tests), contra dos fixtures
nuevos: `colocaciones_2026_07.json` —las 15 filas reales de julio, sin
filtrar— y `tireas_corte_oficiales.json` —las catorce tasas de corte
publicadas—.

Las guardas se probaron rompiéndolas, que es la única forma de saber si guardan:

| Mutación | Resultado |
|---|---|
| `_MES_DIAS` vuelve a 30 | 11 tests fallan |
| la anualización vuelve a 360 días | 10 tests fallan |
| la reapertura vuelve a rendir su cupón | 12 tests fallan |
| se saca la guarda de `dias_vida <= 0` | 1 test falla |
| el inventario deja de marcar la reapertura | 1 test falla |
| el inventario copia la tasa de corte en la contractual | 1 test falla |

La cuarta es la que enseñó algo. La primera versión de su test usaba una fila
con vencimiento anterior a la emisión, y **la mutación pasaba**: el resultado
salía negativo y lo atajaba el recorte de rango, no la guarda. La fila corrupta
que de verdad hace daño es `emisión = vencimiento`, porque ahí el payoff queda
en 1.000 y un precio bajo la par devuelve una tasa de aspecto normal —35,9%—
que entraría al promedio del mes sin que nada avise.

## Pros y contras de las opciones

### A — Dejarlo como está

- Malo: publica un número que la fuente contradice, en 118 de 177 colocaciones.
- Malo: el error no tiene signo fijo, así que ni siquiera se puede leer como una
  cota.

### B — Leer la TIREA de la gacetilla

- Bueno: es el dato oficial, sin convención propia.
- Malo: una página HTML por licitación, sin URL estable ni índice navegable; los
  slugs son del tipo `resultado-de-la-licitacion-...-10`.
- Malo: no cubre la serie histórica sin reconstruir dos años y medio de páginas.
- Malo: agrega una fuente frágil a un colector que hoy depende de un solo `.xlsx`.

### C — Reconstruir desde el precio (elegida)

- Bueno: se calcula desde la planilla, que ya se baja y tiene la serie completa.
- Bueno: a la par coincide idénticamente con la tasa publicada, así que no
  introduce una segunda definición.
- Bueno: reproduce las catorce tasas de corte publicadas con 0,41 pp de error.
- Malo: no es el dato oficial sino su reconstrucción, y queda un residuo.
- Malo: el residuo se amplifica en plazos remanentes muy cortos, donde un día de
  diferencia vale mucho anualizado.

## Más información

### Tres límites que quedan declarados

- **El feriado de agosto de 2025.** La S15G5 del 29-07-2025 es la única de las
  catorce observaciones que la convención no reproduce: da 83,35% contra 65,33%
  oficial. La propia gacetilla explica por qué: «por el feriado dispuesto luego
  de la emisión se realizó el cálculo a la fecha de pago 18/8/2025». Descontando
  hasta esa fecha en vez del vencimiento, la fórmula vuelve a dar la tasa
  oficial dentro de 0,5 pp. El colector no puede saberlo —la planilla sólo trae
  el vencimiento—, así que el caso queda fuera de la tolerancia estricta y con
  un test propio que lo demuestra en vez de esconderlo.
- **Una fila mal cargada en la planilla.** La reapertura de la S30O6 del
  26-11-2025 figura con valor efectivo igual al nominal y precio $1.000, cuando
  la gacetilla informa $1.030,90 y $847.897 M. Es un error de la fuente, no del
  colector; afecta a una fila de 177 y sobreestima esa colocación.
- **Los plazos muy cortos amplifican.** El error de reconstrucción escala con el
  inverso del plazo remanente: a 500 días es de centésimas de punto, a 30 días
  puede ser un punto entero. Ninguna colocación del último año cae en la zona
  peligrosa, pero conviene mirarlo antes de leer un mes dominado por una letra
  a punto de vencer.

### Lo que este ADR no hace

No toca `web/src/lib/fichas.ts` ni `formulas.ts`: la ficha de
`costo_financiamiento_tesoro` sigue describiendo «TIREA» a secas y hay que
agregarle la entrada de cambio y la distinción entre tasa de corte y tasa
contractual. Tampoco recalibra las bandas, que hay que revisar contra la serie
nueva. Por eso queda **propuesto** y no aceptado.
