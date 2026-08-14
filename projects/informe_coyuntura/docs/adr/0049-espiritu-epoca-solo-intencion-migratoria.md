---
madr: 4
id: '0049'
estado: 'superado'
nota_estado: 'Superado por ADR-0205'
fecha: 2026-07-11
cinturon: 'espiritu'
archivos: ['scripts/espiritu_epoca.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/components/Evolucion.astro', 'tests/*']
superado_por: ['0205']
ambito: '`scripts/espiritu_epoca.py` · `scripts/publicar.py` · `web/src/lib/fichas.ts` · `web/src/components/Evolucion.astro` · `tests/*`'
---

# ADR-0049 — Espíritu de época: la intención migratoria queda como único indicador del cinturón

| **Precedente directo** | ADR-0035 (`indice_intencion_migratoria` + Componente B), ADR-0022 (`MACRO_OCULTOS`), ADR-0048 (`POLITICA_OCULTOS`, regla "el tablero solo muestra lo que integra el índice") |

## Contexto y planteo del problema

El cinturón espíritu de época nació (jun-2026) como v1 provisional con tres
proxies que no eran mediciones propias sino **segundas lecturas de cards que
ya viven en otros cinturones**:

- `icc_utdt` y `sentimiento_digital` — cards de vida cotidiana (componentes
  del ITVC).
- `clima_electoral` — el mismo `votometro_ventaja_lla` que puntúa en política
  (dimensión imagen y voto del ITCP).

ADR-0035 (10-jul) agregó el primer indicador con identidad conceptual propia:
`indice_intencion_migratoria` (salida en el sentido de Hirschman — voz vs.
salida), con su contraste de migración real (Componente B, `contexto_duro`,
nunca puntúa). Eso dejó al cinturón en una situación editorial rara: un
indicador que mide el constructo del cinturón + tres duplicaciones declaradas
"hasta que exista una paramétrica propia".

El 2026-07-11 el usuario definió el alcance: **el único indicador del
cinturón, por ahora, es la tendencia migratoria**.

## Opciones consideradas

- **Eliminar los 3 proxies del colector**: descartado — el costo de seguir
  cacheándolos es cero (son lecturas de outputs que el pipeline ya extrae,
  sin fetch propio) y conservan valor como seguimiento interno del humor
  social; además el patrón oculto ya está establecido y probado dos veces.
- **Dejarlos como cards de contexto visibles sin puntuar** (estilo
  `alertas_manifestacion` en gestión): descartado — la regla editorial
  confirmada el 10-jul (ADR-0048) es que el tablero solo muestra lo que
  integra el índice, y acá ni siquiera son mediciones propias del cinturón
  sino duplicados exactos de cards visibles en otros dos tableros.
- **Esperar la paramétrica formal del cinturón para tocar su composición**:
  descartado — con lanzamiento en agosto de 2026, publicar tres duplicaciones
  que inflan/diluyen el score del quinto cinturón es peor que un cinturón
  chico y honesto de un indicador declaradamente provisional.

## Decisión

### 1. El score del cinturón es la tensión de la intención migratoria, sola

`espiritu_epoca.calcular_score()` deja el promedio simple de 4 y devuelve
directamente `clamp10(indice_intencion_migratoria / 10)`; sin dato, 5,0
neutral (mismo default que antes). Las fórmulas de tensión de los otros 3
quedan documentadas en `publicar.SCORING` como referencia, pero ya no llegan
al loop de scoring.

### 2. Los 3 proxies pasan a OCULTOS del snapshot, no de la pipeline

`publicar.ESPIRITU_OCULTOS = {icc_utdt, sentimiento_digital, clima_electoral}`
— mismo criterio que ADR-0022/0048: **el tablero solo muestra lo que integra
el score**. El colector los sigue fetcheando y cacheando en
`output/cache/espiritu_epoca.json` como seguimiento interno
(`INDICADORES_ESPERADOS` sigue en 4; los exit codes de frescura no cambian).
**No se pierde ninguna lectura pública**: `icc_utdt` y `sentimiento_digital`
siguen como cards de vida cotidiana, y la ventaja del Votómetro sigue como
card de política — lo que desaparece es la segunda lectura, no el dato.

### 3. Capa web

- La ficha metodológica de `clima_electoral` se retira de /metodologia (los
  ocultos no tienen ficha — precedente `badlar`/`rotacion_gabinete`). Las de
  `icc_utdt`/`sentimiento_digital` permanecen (son cards de vida) con el
  `dobleUso` reescrito en pasado.
- La ficha de `indice_intencion_migratoria` deja de describir el promedio de
  cuatro y declara el cinturón de indicador único, con entrada fechada en su
  registro de cambios.
- El destacado de espíritu en la sección Evolución de la home pasa de
  `sentimiento_digital` (que como card pertenece a vida) a
  `indice_intencion_migratoria`.
- Labels/unidades/descripciones de los ocultos quedan en `datos.ts`/
  `descripciones.ts`/`formulas.ts` (precedente `rotacion_gabinete`: entradas
  inertes, no renderizan sin card).

### Consecuencias

- **El score del cinturón baja**: con los valores del 11-jul, de 2,5
  (promedio de icc 5,8 · sentimiento 0,6 · clima 3,2 · migración 0,6) a
  **0,6** (migración sola, interés 5,6/100). Es el efecto esperado de la
  decisión editorial — la intención migratoria hoy casi no registra tensión —
  y mueve el score global según el peso del cinturón en la fase temprana.
  Misma clase de salto documentado que ADR-0013/0036/0048.
- El cinturón queda más volátil: un indicador mensual único, sin
  compensación entre proxies. Aceptado como provisional; la salida de fondo
  sigue siendo una paramétrica propia con indicadores adicionales (la apatía
  electoral pendiente de ADR-0035, u otros que defina el marco conceptual).
- `tests/test_publicar.py::test_espiritu_epoca_presente_y_coherente` pinea la
  composición nueva (solo la intención migratoria en el snapshot, con
  `contexto_duro` presente); `tests/test_espiritu_epoca.py` pinea que los
  ocultos no puntúan aunque estén tensos y que sin migración el score es 5,0.
- `data/historico/indicadores.json` deja de acumular meses nuevos para los 3
  ocultos (acumula sobre el snapshot ya filtrado, igual que con los ocultos
  de macro/política); su historia queda en las series de sus cinturones de
  origen.
- Sin cachés nuevos ni cambios de series: nada que agregar al `git add` de
  `data-pipeline.yml`; `validacion_externa.py` no se ve afectada (espíritu no
  tiene paramétrica ni entra en esa validación).
