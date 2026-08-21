---
madr: 4
id: '0229'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'gestion'
indicadores: [desregulacion_normativa]
archivos: ['web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
relacionado: ['0096', '0125', '0143', '0226']
ambito: 'ITCG · `desregulacion_normativa` · ficha, descripción y fórmula pública — qué declara el indicador sobre sí mismo. NO cambia el indicador, su peso ni su cálculo'
origen: 'Editor, 21-ago-2026: el indicador publica un acumulado de artículos sin decir que cuenta actos y no efectos, ni que la fuente es el propio ejecutor del programa'
---

# ADR-0229 — La desregulación cuenta actos, no efectos, y la ficha lo dice

`web/src/lib/fichas.ts` · `web/src/lib/descripciones.ts` · `web/src/lib/formulas.ts`

- **Relacionados**: [[0143-la-desregulacion-se-mide-en-articulos]] (fijó la unidad
  y la escala que este ADR anota), [[0125-la-desregulacion-pasa-a-la-fuente-oficial]]
  (puso la fuente oficial que acá se declara como parte interesada),
  [[0096-desregulacion-cuenta-normas-no-menciones]] (el antecedente de corregir
  qué se estaba contando en realidad),
  [[0226-el-itcg-se-queda-sin-validacion-externa-y-lo-declara]] (por qué esta base
  no puede ser el validador externo que al ITCG le falta).

## Contexto y planteo del problema

`desregulacion_normativa` pesa **7% del ITCG** (0,2 dentro de la dimensión de
reformas económicas) y publica un acumulado de **16.771 artículos de normas
modificados o eliminados desde el 10 de diciembre de 2023**, que puntúa **72,5**.

La ficha explicaba bien de dónde sale el número —ADR-0143 eligió los artículos
sobre las normas, ADR-0125 fijó la fuente oficial— pero dejaba dos cosas sin
decir, y las dos condicionan cómo hay que leerlo.

### Cuenta actos, no efectos

El recuento registra que un artículo **fue alcanzado por una norma de
desregulación**. No registra si esa norma llegó a regir. Un artículo derogado que
después la Justicia suspende suma exactamente igual que uno que se aplica, y una
derogación revertida por una norma posterior queda contada las dos veces que se
la dictó.

La ficha tenía una sola línea sobre esto —«es un recuento normativo, no una
auditoría del efecto económico»— sin evidencia detrás y sin decir que la brecha
es medible. Es la clase de afirmación que suena a cautela de rutina y se lee como
si no importara.

### La fuente es el ejecutor del programa

El Ministerio de Desregulación y Transformación del Estado publica el recuento
del programa **que ese mismo ministerio conduce**. No es descalificante: es el
registro primario y la única fuente con detalle mes a mes desde diciembre de
2023, y por eso ADR-0125 la eligió. Pero fija el criterio de qué norma cuenta
como «de desregulación», y por lo tanto qué artículos entran. La ficha decía «no
hay un tercero que lo audite» sin nombrar la asimetría de quién publica.

## Factores de decisión

- **Un indicador tiene que declarar la distancia entre lo que mide y lo que su
  nombre sugiere.** «Desregulación normativa» se lee como desregulación lograda;
  lo que hay es articulado alcanzado por actos firmados.
- **Existe evidencia de un tercero que cuantifica esa distancia**, y mientras no
  esté citada, la limitación queda en el terreno de lo plausible.
- **Anotar no es recalibrar.** El número, la escala y el peso son los que fijó
  ADR-0143. Esto corrige lo que el índice *dice sobre sí mismo*.

### Lo que dice el tercero, verificado contra la planilla original

Chequeado y elDiarioAR clasificaron medidas de desregulación por su impacto real,
con criterio publicado de cuatro niveles, consulta a unos treinta especialistas y
más de veinte pedidos de acceso a la información. Se difundió el **19 de diciembre
de 2025** en el marco del Data Journalism Visualization Bootcamp de FOPEA
(`impactosdesregularizacion.fopea.org`).

**Las cifras se recalcularon sobre la planilla original de la investigación**, no
sobre el resumen periodístico: la visualización es una SPA y la base vive en una
hoja de cálculo pública enlazada desde su bundle, que se descargó y se procesó
entera. Distinguir las dos cosas no fue ceremonia — dos de los números que
circulan no sobrevivieron al recálculo.

| | filas | share |
|---|---|---|
| moderado | 62 | 38,5% |
| alto | 43 | **26,7%** |
| bajo | 36 | 22,4% |
| nulo | 20 | 12,4% |
| **total** | **161** | |

«Nulo» está definido en la propia base como la medida que **no fue implementada,
porque la Justicia suspendió sus efectos o porque otra norma posterior la modificó
o eliminó**. Alrededor de una de cada ocho medidas relevadas no llegó a regir.

**El instrumento predice la supervivencia más que el contenido.** Separando las
filas que citan el DNU 70/2023 de las demás:

| | medidas | nulo |
|---|---|---|
| DNU 70/2023 | 45 | 16 — **35,6%** |
| dictadas después | 116 | 4 — **3,4%** |

Dieciséis de los veinte casos nulos vienen del decreto fundacional. Lo que se
hizo por decreto se frenó ~10 veces más que lo que se hizo norma por norma.

### Tres cosas que NO reprodujeron, y una que la base arrastra

Se verificó todo, incluidos los números que venían dados por buenos:

- **El «28% de impacto alto» que difundieron las notas no sale de la base**: es el
  **residuo** de redondear los otros tres niveles hacia abajo (38 + 22 + 12 = 72).
  Sobre las 161 filas la proporción real es **26,7%**. Los otros tres coinciden.
- **«118 instrumentos normativos» cuenta variantes de tipeo, no instrumentos.**
  Son 118 cadenas distintas en la columna, pero el DNU 70/2023 aparece escrito de
  seis formas (`DNU 70/23.`, `DNU 70/2023`, `Decreto N° 70/2023`…) y una fila no
  tiene norma cargada. Instrumentos realmente distintos: **110**.
- **«Doce veces más» es ~10 veces**: 35,6 / 3,4 = 10,4.
- **Los 16 nulos del DNU 70/2023 no son 16 frenos independientes.** **Doce** de
  ellos son el capítulo laboral del mismo decreto, con idéntico texto de
  justificación repetido fila por fila: un único bloqueo judicial registrado como
  doce medidas. La brecha entre decreto y norma posterior es real, pero su
  magnitud depende de una convención de conteo de la base.

**Las once filas mal fechadas sí existen.** Once filas del DNU 70/2023 están
fechadas en diciembre de **2024** en vez de diciembre de 2023 (diez de ellas al
20/12/2024, la restante al 06/09/2024). Corregirlas mueve diciembre de 2023 de
**36 a 47** medidas y diciembre de 2024 de **27 a 17** — exactamente lo que
anticipaba el análisis previo. Reproducirlo exige parsear tres formatos de fecha
conviviendo en la columna (`datetime`, `dd/mm/aaaa` y `mes-aaaa` en castellano);
con un parseo ingenuo diez filas quedan sin fecha y la cuenta de diciembre de 2024
da 26, no 27. La distribución mensual de la base no se puede leer sin corregir
esto. **El total de 161 y el reparto por impacto no dependen de la corrección.**

Se encontraron además dos fechas fuera de la ventana declarada, evidentes erratas
de tipeo: una fila al `06/08/04` y otra al `08/10/25`. Las 159 restantes caen
dentro de dic-2023 → may-2025.

## Opciones consideradas

- **Anotar la ficha con el contraste, sin tocar el indicador** — elegida.
- **Incorporar el impacto ponderado como componente del índice** — descartada.
- **Usar la base como validación externa del ITCG** — descartada.
- **No hacer nada, porque la limitación ya estaba mencionada** — descartada: la
  mención existía sin evidencia y sin nombrar a la parte interesada.

## Decisión

**Se anota la ficha; el indicador no se toca.** `desregulacion_normativa` mantiene
su fuente, su unidad, su serie, sus bandas, su peso de 0,2 en la dimensión y su
cálculo. Cambian tres archivos de texto público:

- **`fichas.ts`** — `limitaciones` gana: que cuenta actos y no efectos; que quien
  publica es el ejecutor del programa; qué encontró el tercero con sus cifras
  verificadas; qué **no** es esa base; y la advertencia de recálculo (el 28%
  residual y las once filas mal fechadas). Se eliminó la línea genérica que el
  texto nuevo subsume. Entrada nueva en `cambios`.
- **`descripciones.ts`** — «volumen de texto regulatorio **efectivamente
  removido**» pasa a «volumen de articulado que el programa **alcanzó**», más una
  oración sobre la diferencia. El adverbio afirmaba justo lo que el indicador no
  puede sostener.
- **`formulas.ts`** — la leyenda suma las dos declaraciones en una línea.

### Por qué la base es anotación y no componente ni validador

**Es un corte único, no un tracker vivo.** Se publicó una sola vez, cubre hasta
mayo de 2025 y no se actualiza. Un componente del índice necesita una serie que
se refresque; una validación externa recurrente, todavía más. Esta base no puede
dar ninguna de las dos: al mes siguiente de incorporarla quedaría congelada y el
carry-forward estaría publicando un dato muerto como si respirara.

Es exactamente la restricción que ADR-0226 ya había encontrado al buscar un
validador para el ITCG —«tampoco hay tracker argentino independiente con serie
descargable»—, y este ADR la confirma con un caso concreto en vez de dejarla como
ausencia genérica. Su clasificación de impacto es además **cualitativa y de sus
autores**, y no audita el recuento oficial de artículos: mide otra cosa. Una
cuenta medidas y su efecto; la otra, articulado alcanzado.

### Consecuencias

- La ficha declara una limitación que **no tiene gate**: ningún test compara un
  recuento de actos con una medición de efectos. Queda como texto, sostenido por
  `test_texto_publico_no_caduca.py` sólo en cuanto a no envejecer.
- Las cifras del corte quedan **fechadas** en la prosa (19-dic-2025, ventana
  dic-2023 → may-2025), que es lo que impide que envejezcan solas.
- El puntaje publicado no se mueve: 72,5 con 16.771 artículos.

### Confirmación

- `pytest tests -q` — en particular `test_texto_publico_no_caduca.py` (la prosa
  nueva no introduce deixis temporal), `test_adr_format.py` y
  `test_fichas_pesos.py`.
- `npx tsc --noEmit` y `npm run build` en `web/`.
- `scripts/gate_calidad.py` sin cambios de datos: el snapshot no se toca.
- La reproducción de las cifras del tercero es rehacible bajando la hoja pública
  enlazada desde el bundle de `impactosdesregularizacion.fopea.org`.

## Pros y contras de las opciones

### Anotar la ficha, sin tocar el indicador (elegida)

- **A favor**: corrige lo que el índice dice sobre sí mismo, que es donde estaba
  el defecto; no mueve un número por una razón editorial; deja registrada
  evidencia de tercero con sus cifras verificadas.
- **En contra**: el puntaje sigue tratando por igual al artículo que rige y al
  suspendido. La ficha lo advierte pero el índice no lo corrige.

### Incorporar el impacto ponderado como componente (descartada)

- **A favor**: acercaría el indicador a medir desregulación efectiva.
- **En contra**: la base **termina en mayo de 2025** y no se actualiza, así que el
  componente nacería congelado. Además, ponderar el recuento oficial por una
  clasificación cualitativa de un tercero mezcla dos universos que no fueron
  construidos para multiplicarse: 161 medidas contra 16.771 artículos, sin
  correspondencia fila a fila. Y hacerlo sería cambiar el indicador —decisión del
  editor, no de este ADR.

### Usar la base como validación externa del ITCG (descartada)

- **A favor**: el ITCG quedó sin validador único tras ADR-0226.
- **En contra**: un validador necesita **serie**; esto es un punto. Correlacionar
  contra un único corte no es validación.

### No hacer nada (descartada)

- **A favor**: la limitación estaba nombrada.
- **En contra**: estaba nombrada como fórmula de cortesía, sin evidencia y sin
  decir que la fuente es parte interesada. Y `descripciones.ts` afirmaba
  «efectivamente removido», que es directamente lo contrario de lo que el
  recuento puede sostener.

## Más información

- Base de la investigación: `impactosdesregularizacion.fopea.org` (visualización
  FOPEA · Chequeado · elDiarioAR, 19-dic-2025). La hoja de cálculo pública con
  las 161 filas está enlazada desde el bundle del sitio; las cifras de este ADR
  salen de ahí, no de las notas.
- Notas periodísticas asociadas, mismo día: Chequeado, «Desregulaciones del
  gobierno de Javier Milei: 6 de cada 10 tuvieron hasta ahora un impacto moderado
  o bajo y el 12% están frenadas», y su espejo en elDiarioAR. Son la fuente del
  28% que este ADR corrige a 26,7%.
- Fuente oficial del indicador: Ministerio de Desregulación y Transformación del
  Estado, «La desregulación en números»,
  `argentina.gob.ar/desregulacion/desregulacion-en-numeros`.
- **Queda planteado y no resuelto**: si el indicador debería medir supervivencia
  normativa además de volumen. Es un cambio de indicador y la decisión es del
  editor.
