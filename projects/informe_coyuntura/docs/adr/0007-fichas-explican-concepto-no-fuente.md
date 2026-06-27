# ADR-0007 — Las fichas de indicador explican QUÉ MIDE, no de dónde sale el dato

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-27 |
| **Ámbito** | Web · `web/src/lib/descripciones.ts` · modal `IndicadorModal.astro` |
| **Commit** | `6c1a7fb` (pasada completa; gatillado por `69c1c31`) |

## Contexto

El modal de cada indicador muestra varios campos: el **"qué es"** y **"qué aporta"**
(de `descripciones.ts`), más **Fuente**, **Frecuencia**, **Tipo de dato** y, cuando
corresponde, **"Cómo se calcula / Valor usado"** (que arma `publicar.py`).

Algunas fichas usaban el "qué es" para explicar **de dónde sale el dato** (la
fuente, el scraping) o **cómo se computa** (la mecánica), en vez de qué mide. El
caso más flagrante era reservas netas: *"neto estricto de la planilla SDDS +
depósitos del Tesoro + Bopreal a 12m, todo de datos oficiales (planilla SDDS y
balance del BCRA)"* — eso es plumbing, no concepto. El usuario lo marcó: *"explica
el cálculo, no el scraping"*.

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

## Opciones consideradas

- **Dejar la fuente/mecánica en el "qué es"** (statu quo). Rechazada: duplica el
  campo Fuente y "Cómo se calcula", y enturbia el concepto con plumbing.
- **Quitar también las aclaraciones de proxy.** Rechazada: el proxy es información
  conceptual (no es lo mismo medir algo directo que aproximarlo); ocultarlo
  engañaría al lector.
- **"Qué es" = solo concepto; el resto en sus campos.** Elegida.

## Consecuencias

- Pasada completa sobre las 32 fichas (commit `6c1a7fb`): se sacaron los tags de
  fuente del "qué es" (INDEC, CEPA, CICCRA, CAFAM, UTDT, InfoLeg, RIPTE/CBT, etc.)
  y la mecánica de scoring (raíz-12 del REM, deflactación de recaudación).
- Toda ficha nueva debe seguir este criterio.
- La transparencia técnica no se pierde: vive en **Fuente** y en
  **"Cómo se calcula / Valor usado"** (`publicar.py::_macro_input_txt` y los
  `aporte_formula`/`aporte_input_txt`).
