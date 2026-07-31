---
madr: 4
id: '0007'
estado: 'aceptado'
fecha: 2026-06-27
parametros: ['UNIDADES_LARGAS']
archivos: ['descripciones.ts', 'datos.ts', 'IndicadorModal.astro', 'IndicadorTile.astro', 'overrides.css']
relacionado: ['0053']
ambito: 'Web · `descripciones.ts` · `datos.ts` (`UNIDADES_LARGAS`) · `IndicadorModal.astro` · `IndicadorTile.astro` · `overrides.css` · colectores'
commit: '`6c1a7fb` (fichas); ampliación unidades/fuente/tile el mismo día'
---

# ADR-0007 — Las fichas de indicador explican QUÉ MIDE, no de dónde sale el dato

## Contexto y planteo del problema

El modal de cada indicador muestra varios campos: el **"qué es"** y **"qué aporta"**
(de `descripciones.ts`), más **Fuente**, **Frecuencia**, **Tipo de dato** y, cuando
corresponde, **"Cómo se calcula / Valor usado"** (que arma `publicar.py`).

Algunas fichas usaban el "qué es" para explicar **de dónde sale el dato** (la
fuente, el scraping) o **cómo se computa** (la mecánica), en vez de qué mide. El
caso más flagrante era reservas netas: *"neto estricto de la planilla SDDS +
depósitos del Tesoro + Bopreal a 12m, todo de datos oficiales (planilla SDDS y
balance del BCRA)"* — eso es plumbing, no concepto. El usuario lo marcó: *"explica
el cálculo, no el scraping"*.

## Opciones consideradas

- **Dejar la fuente/mecánica en el "qué es"** (statu quo). Rechazada: duplica el
  campo Fuente y "Cómo se calcula", y enturbia el concepto con plumbing.
- **Quitar también las aclaraciones de proxy.** Rechazada: el proxy es información
  conceptual (no es lo mismo medir algo directo que aproximarlo); ocultarlo
  engañaría al lector.
- **"Qué es" = solo concepto; el resto en sus campos.** Elegida.

## Decisión

En las fichas (`descripciones.ts`):

- El **"qué es"** describe el **concepto**: qué mide el indicador, en lenguaje
  llano ("cuánto…", "qué porcentaje…", "si el peso está caro o barato…").
- El **"qué aporta"** explica **por qué importa** para el cinturón (qué tensión
  capta), no cómo se puntúa.
- **NO** va en la ficha: la fuente/organismo (está en el campo **Fuente**), ni la
  mecánica de cálculo o de scoring (está en **Cómo se calcula / Valor usado**).
- **Sí** se mantienen las aclaraciones de **proxy** ("aproximada por… (proxy)"),
  porque son honestidad conceptual: avisan que no es una medición directa.

Regla operativa: si una ficha menciona un organismo, una planilla, una API o una
fórmula, va movida al campo que corresponde; el "qué es" queda solo con el
significado.

### Ampliación a los campos "Unidad", "Fuente" y al texto del tile

El mismo principio (sin plumbing en lo visible) se aplica a los demás campos del modal y al tile:

- **Unidad** — describe SOLO la unidad de medida, normalizada y consistente
  ("Millones de USD", "% mensual", "Índice (0–100)", "% de avance"). NO lleva
  detalle de scraping ni metodología. Se eliminaron casos como
  `"mill USD (netas a secas, consenso)"`, `"índice"` (minúscula),
  `"millones_pesos"` (snake_case), `"Resoluciones tipo=3 texto='VPU' desde
  jul-2024 (InfoLeg)"`, `"% empresas privatizadas efectivamente / listado DL 70/23"`.
  La unidad mostrada se centraliza en `datos.ts → UNIDADES_LARGAS` (capa de
  display, como `LABELS`/`UNIDADES_CORTAS`), **independiente del estado del cache**
  de cada colector; el modal usa `UNIDADES_LARGAS[key] ?? ind.unidad`.
- **Fuente** — nombre limpio del organismo/origen, nunca el archivo interno ni el
  path de scraping. Se eliminaron `"... (temp0526.pdf) ..."` y `str(VOTOMETRO_HTML)`
  (un path de archivo) → `"BCRA — Planilla SDDS y Balance Consolidado"`,
  `"Votómetro CIGOB"`.
- **Texto del tile** — el tile (`IndicadorTile.astro`) muestra el `que` acotado a
  **2 líneas** (`-webkit-line-clamp` en `.cg-tile-desc`); el texto completo queda
  en el modal. Así una ficha conceptual no estira la card. Las descripciones se
  mantienen concisas (1–2 líneas).

### Consecuencias

- Pasada completa sobre las 32 fichas (commit `6c1a7fb`): se sacaron los tags de
  fuente del "qué es" (INDEC, CEPA, CICCRA, CAFAM, UTDT, InfoLeg, RIPTE/CBT, etc.)
  y la mecánica de scoring (raíz-12 del REM, deflactación de recaudación).
- Toda ficha nueva debe seguir este criterio.
- La transparencia técnica no se pierde: vive en **Fuente** y en
  **"Cómo se calcula / Valor usado"** (`publicar.py::_macro_input_txt` y los
  `aporte_formula`/`aporte_input_txt`).
