# ADR-0011 — El RIGI se mide desde la plataforma oficial (inversión aprobada/pipeline), no por conteo de normas

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-30 |
| **Ámbito** | `scripts/gestion.py` · `scripts/publicar.py` · web (`descripciones.ts`) |

## Contexto

El indicador `rigi_inversiones` (cinturón gestión) medía el avance del Régimen de
Incentivo a Grandes Inversiones contando **Resoluciones de InfoLeg** con el texto
"VPU" (Vehículo de Proyecto Único, término exclusivo del RIGI) como **proxy** del
número de proyectos aprobados, y tratando ese conteo como porcentaje de avance
(`avance = min(100, conteo)` ≈ 31%). Era un hack: contar normas no es un porcentaje
de nada, y la calibración (≈28 normas ≈ 16 proyectos ≈ 28%) era frágil.

En **junio de 2026 el Ministerio de Economía lanzó una plataforma oficial** del RIGI
con mapa interactivo, montos de inversión y empleos. Sus datos salen de un **Google
Sheet público** que se puede leer sin autenticación (gviz CSV): pestaña `dataset`
(una fila por proyecto aprobado, con provincia, empresa, sector e inversión) y
pestaña `evaluacion` (agregados de los proyectos en evaluación). El sheet se mantiene
actualizado (al lanzamiento: 16 proyectos / US$ 29.892M; a fin de junio: 17 / US$ 31.192M).

## Decisión

Reemplazar el proxy de InfoLeg por la **plataforma oficial** como fuente primaria.

- **Qué puntúa (avance):** la **inversión aprobada sobre el total del pipeline**
  (aprobada + en evaluación). Hoy: US$ 31.192M / US$ 140.879M = **22,1%**.
  Es un porcentaje *genuino* (no un conteo disfrazado), ponderado por monto —
  coherente con que el indicador se llama "inversiones"— y honesto: los mega-proyectos
  (GNL US$ 15.156M) siguen en evaluación, así que el régimen "aprobó" ~1/5 de los
  dólares comprometidos.
- **Qué se muestra (contexto):** la ficha expone además **proyectos aprobados** (17),
  **inversión aprobada** (US$ 31.192M), **proyectos en evaluación** (24) e **inversión
  en evaluación** (US$ 109.687M). El modal lo arma con un campo `detalle_txt`.
- **Conteo de proyectos por título:** un proyecto multi-provincia ocupa varias filas;
  se deduplica por título (igual que el `Set(titulo)` del propio sitio oficial).
- **Fallback:** si el sheet no responde, cae al conteo "VPU" de InfoLeg, marcado
  `desactualizado=True`.

## Por qué NO el conteo directo de proyectos

Pasar el avance a "17 proyectos = 17%" haría **saltar la tensión de 6,9 a 8,3 por puro
cambio de medición**, no por la realidad (el mismo trap mecánico que se evitó en otros
indicadores). Un ratio real lo evita. Se descartó también `proyectos aprobados /
presentados` (17/41 = 41,5%) por estar dominado por los proyectos chicos; la versión
ponderada por monto es más fiel al fenómeno económico. (Decisión del usuario vía
AskUserQuestion: puntúa la inversión, se muestran los proyectos.)

## Consecuencias

- `rigi_inversiones`: avance 31% → **22,1%**, tensión 6,9 → **7,8**. Gestión 5,8 → 5,9.
- Dato **oficial, estructurado y en vivo** (continuo), en vez de un proxy de conteo de
  normas con calibración manual. La ficha gana cifras concretas (USD y proyectos).
- **Riesgo:** depende del `RIGI_SHEET_ID` del Google Sheet oficial; si Economía rota el
  ID o cambia las columnas (`nombre`, `inv-comprometida`, `cantidad`, `inversion`), el
  colector cae al fallback de InfoLeg. URLs y columnas centralizadas en `gestion.py`.
