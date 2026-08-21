---
madr: 4
id: '0223'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [patentamiento_autos, patentamiento_motos]
archivos: ['scripts/vida_cotidiana/collectors/dnrpa_autos.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'tests/test_patentamiento_autos.py']
complementa: ['0024']
relacionado: ['0018', '0108', '0130', '0153', '0216']
ambito: 'ITCIS · dimensión de ingresos y consumo · patentamiento de automotores'
origen: 'Pedido del editor: incorporar el patentamiento de autos como espejo del de motos'
---

# ADR-0223 — El espejo de las motos: el patentamiento de autos

## Contexto y planteo del problema

El cinturón mide consumo durable con **una sola** serie de vehículos:
`patentamiento_motos`, que entró en [[0018-itvc-parametrica-vida-cotidiana]] y
puntúa por acumulado móvil de 12 meses desde
[[0024-motos-movil-12m-estacionalidad]].

Con motos solas, el componente sólo admite una lectura: si sube, mejoró el poder
de compra. **Y la moto no es únicamente un bien de consumo.** Es medio de trabajo
—reparto, mensajería— y es el sustituto barato del auto. Un hogar que no puede
sostener el auto y compra una moto empuja el indicador hacia arriba mientras su
situación empeora. El índice no tiene con qué distinguir esos dos mundos, y el
número que publica es el mismo en los dos.

La pregunta que el editor pide contestar es exactamente ésa: **¿el patentamiento
sube porque los hogares compran más, o porque bajan de categoría?** Se contesta
con dos series, no con una.

## Factores de decisión

- **La fuente tiene que ser primaria, mensual, viva y llegar al 4T-2023**, que es
  la base de todos los componentes.
- **El rezago se mide contra la fuente**, no se copia de lo que la fuente
  declare: de ahí sale el tope del gate, y un tope mal puesto marca demoras
  falsas o deja pasar un indicador congelado.
- **Autos y motos no son el mismo fenómeno**, así que hay que medir cuánto se
  parecen antes de ponerlos juntos: si repitieran la misma señal, sumar el
  segundo sólo diluiría al resto del índice.
- **O integra el índice, o no es card** ([[0216-o-integra-el-indice-o-no-es-card]]).
  No hay tercera opción: o puntúa, o vive dentro de la explicación de otra card.

## Opciones consideradas

1. **DNRPA — inscripciones iniciales de automotores**, como componente propio con
   el mismo peso y la misma transformación que motos.
2. **ACARA** — patentamientos mensuales publicados por la cámara de
   concesionarios.
3. **ADEFA** — estadística mensual de la cámara de fábricas terminales.
4. **No crear un indicador** y usar el dato sólo como explicación del color de
   `patentamiento_motos`, como hace la matriz A×B de proteína animal.
5. **No incorporarlo.**

## Decisión

**Opción 1.** Entra `patentamiento_autos`: **cuántos autos 0 kilómetro se
inscriben por mes en los Registros Seccionales de la Propiedad del Automotor**,
total país. Fuente: DNRPA, dataset «Estadística de trámites de automotores» del
portal de datos abiertos del Ministerio de Justicia.

Va a la dimensión de **ingresos y consumo**, con **2% de la dimensión** —
exactamente el peso que tiene motos— y los cuatro componentes previos ceden
proporcionalmente (×0,98) conservando su orden relativo, la regla de
[[0130-la-dimension-empleo-pasa-a-medir-empleo]] y ADR-0153. El peso nominal de
la dimensión no se toca.

El peso igual **no es comodidad**: es el único reparto que no afirma cuál de los
dos vehículos dice más del bolsillo sin haberlo medido. Los dos juntos suman
3,96% de la dimensión, del orden del 3,92% de proteína animal —el otro proxy de
consumo revelado— y muy lejos de las dos medidas directas de ingreso, salario
contra canasta (59,59%) y pobreza (32,53%). Ése es el orden que la dimensión
tenía y el que conserva: primero lo que se mide en el ingreso, después lo que se
infiere de lo que el hogar compra.

**Misma transformación que motos** —acumulado móvil de 12 meses rebaseado a
100 = promedio del 4T-2023—, y por el mismo motivo, medido sobre esta serie y no
heredado: la estacionalidad del flujo crudo de autos es incluso más marcada que
la de motos. Sobre 2015-2026, **enero pesa 1,36 veces el mes promedio y diciembre
0,57**. Contra una base fija, el flujo crudo mediría calendario.

### La correlación con motos, y qué significa el signo que dio

La hipótesis de sustitución diría correlación **negativa**. No es lo que dan los
datos sobre el mandato:

| Medición | r | n |
|---|---|---|
| Flujo mensual crudo, en niveles | **+0,565** | 45 |
| Variación interanual del flujo crudo | **+0,575** | 33 |
| Componente base-100 (móvil 12m), en niveles | **+0,894** | 32 |
| Componente base-100, primeras diferencias | **+0,368** | 31 |

**Los dos se mueven juntos, no en contra.** Es lo esperable: comparten el ciclo
de crédito y el arrastre de la caída de 2024 con la recuperación posterior. El
+0,894 en niveles no es señal repetida sino la «época en común» que
[[0108-redundancia-interna-del-itvc]] ya documentó para todo el cinturón (r medio
0,413 en niveles contra 0,199 al destendenciar); al destendenciar, este par cae a
+0,368, por debajo del umbral de 0,7 con que el cinturón marca redundancia.

**Y ahí está lo que justifica el alta.** La información nueva no aparece en el
promedio de tres años: aparece en el punto donde las dos series se separan.

| Índice base 100 = 4T-2023 | dic-2025 | jul-2026 | |
|---|---|---|---|
| Autos | 136,1 | **125,5** | −10,6 |
| Motos (crudo, antes del techo) | 138,2 | **170,5** | +32,3 |

Los autos hicieron pico en diciembre de 2025 y llevan siete meses cayendo,
mientras las motos siguen subiendo sin freno. Ése es exactamente el patrón que
la hipótesis de sustitución describe, y el índice no podía verlo: con motos
solas, la lectura publicada era «el consumo durable acumula +70% contra el
arranque del mandato» y nada más.

### La matriz publicada dice +0,978, y la diferencia con el +0,894 es el hallazgo

Los números de la tabla de arriba son del **fenómeno**: las dos series tal como
las publican sus fuentes. La matriz de redundancia que el informe publica mide
otra cosa —los componentes **como el índice los ve**, o sea después del techo de
winsorización de 140 ([[0033-itvc-doble-conteo-y-winsorizacion]])— y ahí el par
da **+0,978 en niveles y +0,801 en primeras diferencias**.

Es una brecha grande y tiene una sola causa: **motos está clavada en 140 desde
enero de 2026** (su valor crudo es 170,5). El techo borra justamente el tramo en
que las dos series se separan, así que el par que se compara ya no es
«autos que cae contra motos que sube» sino «autos que cae contra una recta».

Hay que declararlo porque cambia lo que el informe publica sobre sí mismo: hasta
ahora **ningún** par del cinturón superaba el umbral de 0,7 al destendenciar, y
desde esta alta **hay uno de 153**, éste. El dato no se puede presentar como si
la matriz siguiera limpia.

**Y sin embargo el alta es la respuesta correcta a ese número, no su víctima.**
Que el par se vea redundante *dentro del índice* es un síntoma de que
`patentamiento_motos` está saturado: hace siete meses que su componente no se
mueve pase lo que pase con las motos, porque el techo lo aplana. El componente
que queda aportando variación en el bloque de vehículos es autos, que entra en
125,5 y está dentro del rango. Sacar autos para que la matriz vuelva a dar
limpio dejaría al bloque con un único componente, y ese componente es una
constante.

### Por qué la DNRPA y no ACARA ni ADEFA

Los tres publican mensual y siguen vivos; la diferencia es qué miden y de dónde
sale el número.

- **ACARA** publica los patentamientos que **la propia DNRPA registra**: es
  reelaboración, no una segunda medición. Sumar un intermediario agrega un modo
  de falla y no agrega un dato.
- **ADEFA** mide otra cosa: producción, exportación y **ventas de fábrica a
  concesionario**. Ocurren antes del patentamiento y pueden quedar en stock, así
  que describen la oferta, no la compra del hogar. Un indicador que se llama
  patentamiento de autos y mide despachos a concesionarios sería exactamente el
  error que [[0218-el-cierre-de-pymes-se-mide-con-la-srt]] tardó trece meses en
  corregir.
- **DNRPA** es el registro mismo. El patentamiento **es** un acto registral: el
  auto 0km existe cuando se inscribe. Publica CSV abierto sin credenciales, con
  apertura por mes y jurisdicción, **desde enero de 2000** — cubre el 4T-2023 con
  veintitrés años de sobra.

### El rezago, medido

Se midió sobre el historial de actualizaciones del catálogo, no sobre lo que la
fuente declare: **el mes M aparece publicado entre el día 1 y el 4 de M+1**, en
las doce actualizaciones de septiembre de 2025 a agosto de 2026, con una sola
excepción más tardía (13 de marzo de 2026). Es dato registral, no una encuesta:
no hay relevamiento que consolidar.

Con esa cadencia la card nunca supera los ~72 días de antigüedad. **El tope del
gate queda en 90 días**, que es el punto en que una publicación se corrió más
allá del mes siguiente entero — o sea, un mes salteado, que es justo lo que el
tope tiene que agarrar. El default de 110 no habría avisado nunca.

### Consecuencias

- **El componente entra en 125,5** con 0,56% del índice. El ITCIS pasa de
  **90,59 a 90,65** y la tensión queda en 6,9: el alta es visible en la dimensión
  —ingresos y consumo 117,1 → **117,3**— y se diluye en el agregado, que es lo
  esperable para un componente del tamaño más chico del índice.
- Los pesos efectivos de la dimensión quedan: salario/canasta 17,06% → **16,72%**,
  pobreza 9,31% → **9,13%**, proteína animal 1,12% → **1,10%**, motos 0,56% →
  **0,55%**, y autos **0,56%**.
- **El cinturón queda con dieciocho componentes y los dieciocho puntúan.** No hay
  card de contexto: el dato entra al índice o no se publica.
- **La matriz de redundancia del cinturón cambia de veredicto y hay que leerlo
  con la explicación de arriba**: el par autos↔motos pasa a ser el más alto del
  cinturón en niveles (+0,978) y el único de los 153 que supera 0,7 al
  destendenciar (+0,801). Medido sobre las series sin recortar, el mismo par da
  +0,894 y +0,368. La diferencia es el techo de winsorización aplanando a motos.
- La reconstrucción histórica del ITCIS en `validacion_externa.py` aplica el
  mismo móvil de 12 meses que el índice vivo. La lista de componentes con esa
  transformación pasó a ser una constante compartida por nombre, en vez de un
  `if` con un literal adentro: eran dos lugares donde escribir «motos» y ahora
  hay dos donde escribir «motos y autos».

### Confirmación

`tests/test_patentamiento_autos.py` cuida lo que puede volver a romperse: que la
fuente siga siendo el registro y no una cámara, que el colector reviente en vez
de publicar una serie recortada cuando la fuente cambia de forma, que card y
serie sean el mismo número, que la serie llegue al 4T-2023 con las ventanas
móviles completas, y que autos y motos no se hayan vuelto la misma serie.

## Pros y contras de las opciones

**1. DNRPA, componente propio con el peso de motos.** A favor: fuente primaria,
mensual, con veintiséis años de historia y sin credenciales; contesta la pregunta
que motos solas no pueden contestar; el peso igual no introduce ninguna
afirmación no medida. En contra: agrega el par más
correlacionado del cinturón —y el único que sobrevive al destendenciado, por el
efecto del techo sobre motos—, y dos series de vehículos sobre dieciocho
componentes puede leerse como sobre-representación del consumo durable; por eso
las dos juntas pesan 3,96% de la dimensión y no más.

**2. ACARA.** A favor: es la cifra que citan los medios, así que el número
publicado coincidiría con el que el lector ve en otro lado. En contra: republica
el dato de la DNRPA. Se agrega un intermediario que puede cambiar de formato o de
criterio sin avisar, a cambio de nada.

**3. ADEFA.** A favor: la serie es larga y la cámara es estable. En contra: mide
ventas de fábrica a concesionario, que no es el patentamiento — el indicador
diría una cosa y mediría otra, que es la falla que este repositorio ya tiene
documentada dos veces.

**4. Sólo como explicación del color de motos.** A favor: evita la discusión de
peso y no toca la paramétrica. En contra: el mecanismo de explicación del
cinturón ya está ocupado por la matriz A×B de la carne, y sobre todo deja el
puntaje intacto: `patentamiento_motos` seguiría siendo el único que puntúa y
seguiría leyendo una sustitución como una mejora. El problema es del puntaje, no
del texto.

**5. No incorporarlo.** A favor: ninguno. En contra: deja publicado un componente
de consumo durable que no puede distinguir más consumo de bajar de categoría, con
el agravante de que está clavado en el techo de winsorización.

## Más información

- Recurso usado: «Estadística de inscripciones iniciales de automotores» del
  dataset `estadistica-de-tramites-de-automotores`
  (`datos.jus.gob.ar`), CSV con una fila por mes y jurisdicción.
- **La URL de descarga lleva el período adentro y cambia todos los meses**, así
  que el colector la descubre por catálogo en cada corrida. Fijarla a mano
  habría congelado el indicador en un archivo viejo sin que nada avisara.
- El anclaje del colector es de **texto**, no de magnitud: el nombre del recurso
  declara el período que contiene («… - 200001 - 202607») y se compara contra lo
  que el archivo efectivamente trae. Un umbral del tipo «el último mes no puede
  ser menos del X% del promedio» quedó descartado con datos: **abril de 2020 fue
  el 12% de la mediana de los doce meses previos**, y era real. Cualquier umbral
  que atrape una carga parcial también atrapa una cuarentena.
- La serie se recorta a noviembre de 2022 en adelante por el mismo motivo que la
  de motos: once meses antes de la base, para que las ventanas móviles que
  terminan en octubre, noviembre y diciembre de 2023 estén completas.
- **Lo que queda abierto, y es lo primero a revisar:** el techo de winsorización
  de motos. Mientras siga clavado en 140, el componente de motos es una constante
  y la matriz de redundancia va a seguir marcando el par. La discusión de fondo
  —si un componente saturado durante siete meses seguidos debe seguir puntuando
  con su peso completo— excede este ADR y no se resuelve acá: éste incorpora
  autos, no recalibra motos.
- **Lo que también queda abierto:** el indicador no distingue gama ni precio, así que un
  mes de autos de entrada y uno de vehículos caros se registran igual. La lectura
  de sustitución que este ADR habilita se apoya en el conteo de unidades; separar
  gamas exigiría una fuente de precios que la DNRPA no publica.
