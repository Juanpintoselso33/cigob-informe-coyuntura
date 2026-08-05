# Task 5 Report: Sync final de `docs/cinturon_politica.md`

## Status: DONE_WITH_CONCERNS

Deliverable complete and committed. All 125 pytest pass, including the
previously-failing `test_politica_itcp_reconcilia`. One real, pre-existing
concern surfaced during the pipeline run (`gate_calidad.py` G3 gap) —
investigated, confirmed by-design (not a bug), documented in the doc itself,
and correctly left unfixed as out of this task's code-change scope.

## 1. Step 1 — full pipeline run

Ran each command from the brief individually (not chained with `&&`, so I
could inspect each stage's output before continuing):

```
python scripts/descargar_series.py    → OK, all 5 belts regenerated
python scripts/politica.py            → [OK] politica: score=3.2 frescos=11/12
python scripts/validacion_externa.py  → OK (ITCP r=-0.371 vs EPU Argentina, unchanged pair)
python scripts/generar_informe.py     → [OK] informe: score_global=3.2 cinturones=5/5
python scripts/publicar.py            → OK, snapshot written
python scripts/gate_calidad.py        → 4 FAILURES (see concern below)
python -m pytest tests/ -q            → 125 passed
```

### Full test suite result

```
125 passed in 1.68s
```

`test_politica_itcp_reconcilia` explicitly re-verified:

```
python -m pytest tests/test_publicar.py -q -k test_politica_itcp_reconcilia -v
1 passed, 10 deselected
```

Confirmed: before the pipeline run it failed exactly as the brief predicted
(`faltan indicadores que no deberían faltar: {'alineamiento_senadores_prov'}`,
because `output/informe.json` hadn't been regenerated since the test was
updated). After Step 1's `generar_informe.py` + `publicar.py` run, it passes.

### Concern: `gate_calidad.py` G3 failure (not fixed, flagged instead)

`gate_calidad.py` exited 1 with 4 G3 ("serie ↔ card invariante") failures:

```
[FALLA] G3 macro/iai: serie[-1]=0.31 ≠ card=-3.9 (tolerancia 0.11)
[FALLA] G3 politica/alineamiento_senadores_prov: serie[-1]=51.9 ≠ card=68.3 (tolerancia 0.683)
[FALLA] G3 vida_cotidiana/mortalidad_pymes: serie[-1]=0.41 ≠ card=-2.14 (tolerancia 0.11)
[FALLA] G3 vida_cotidiana/despacho_cemento: serie[-1]=154.46 ≠ card=144.1 (tolerancia 1.441)
```

3 of the 4 are macro/vida_cotidiana — exactly the "normal day-to-day data
drift" the brief said to expect and ignore, unrelated to this task.

The 4th (`politica/alineamiento_senadores_prov`) I investigated rather than
ignored, since it's this task's own indicator. Root cause (verified by
reading code, not guessed): `_serie_cohesion_cacheada()` in
`descargar_series.py` backfills each year's point with
`fetch_fn(anio=anio, dias_ventana=366)` — a **full-year** window — while
`politica.py`'s live card uses the function's default `dias_ventana=90` —
a **rolling 90-day** window. This is the exact same "card measures a
different window than serie" pattern `gate_calidad.py`'s own
`G3_EXCEPCIONES` dict already declares for `sentimiento_digital`,
`rigi_inversiones`, and `protestas_caba` — it's simply missing an entry for
`alineamiento_senadores_prov` (and, arguably, `cohesion_bloque_senado`,
which only passes today by coincidence because its values happen to be
stable across both windows: 99.7 vs 99.4).

This is real and pre-existing (confirmed against `progress.md`: Plan5-Task3
already recorded the 51.9%/2026 backfill value, Plan5-Task4 already recorded
the 68.3% live value — both numbers were already known separately; nobody
had run `gate_calidad.py` against the combination until now). It is **not**
a bug in this task's doc work, and fixing it means editing
`scripts/gate_calidad.py` (adding a `G3_EXCEPCIONES` entry) — out of this
task's scope (`Files: Modify: docs/cinturon_politica.md`). I did NOT touch
`gate_calidad.py`. Instead:
- Added an honest "Nota de consistencia" in the new
  `alineamiento_senadores_prov` doc subsection explaining the card-vs-serie
  window difference (good doc content, in scope).
- Added a `Notas de mantenimiento` bullet naming the gate gap explicitly as
  a follow-up item for whoever next touches `gate_calidad.py`.

It does not block anything in this task: all 125 pytest still pass, and the
docs deliverable doesn't depend on `gate_calidad.py` passing.

## 2. Real live values used (from `output/cache/politica.json` and
   `output/informe.json`, live run 2026-07-08)

- **ITCP = 68,4** (banda: `moderadamente_aflojado` / "Moderadamente
  aflojado"), tensión derivada = **(100−68,4)/10 = 3,2/10** — matches
  `politica.py`'s own printed `score=3.2` and `informe.json`'s
  `cinturones.politica.score`.
- **`alineamiento_senadores_prov`**: valor = **68,3%**, `fecha_dato` =
  2026-06-04, `n_provincias` = 24 (max possible), `puntaje_banda` = 100,0
  (band saturates above 65%), `peso_efectivo` = 0,075, `en_indice` = true.
- Real backfill series (`output/series/politica.csv`, annual anchors,
  `dias_ventana=366`): 2023 = 71,9% · 2024 = 57,7% · 2025 = 45,3% ·
  2026 = 51,9%.
- `gobernadores_alineamiento`: **fully absent** from
  `output/cache/politica.json["indicadores"]` and
  `output/informe.json["cinturones"]["politica"]["indicadores"]` — not even
  as an inert entry. Confirmed via direct code read: it's not in
  `INDICADORES_ESPERADOS`, not in the `colectores` list in `main()`, and
  `load_manuales()`/`fetch_manual()` are defined but never called anywhere
  — `data/politica/manuales.json` (still on disk, still holding the old 55%
  placeholder, `fecha_dato: "2026-04-01"`) is now dead weight, read by
  nothing.
- 11 of 12 indicators fresh (`cohesion_bloque` still absent — blocked,
  ADR-0037, unchanged from before this task).
- **Drift found and corrected while cross-checking every number against
  live cache** (not part of the brief's ask, but the doc would have been
  internally inconsistent otherwise — flagged by the advisor before
  writing): `ratio_dnu` moved from 1,471 (25 DNUs/17 leyes, puntaje 45,0) to
  **1,529 (26 DNUs/17 leyes, puntaje 42,7)** between the last doc sync and
  this run — one more DNU counted. `adhesion_reformas_provincial`'s
  `fecha_dato` moved from "7 de julio" to "8 de julio" (same run-today
  semantics, no value change: still 66,7%/16 of 24). All other detailed
  indicator values (`eficacia_legislativa`, `veto_quorum`,
  `comisiones_caidas`, `iaf_transferencias`, `cohesion_bloque_senado`,
  `movilizacion_cepa`, `protestas_caba`, `votometro_ventaja_lla`) were
  verified byte-exact against the live cache and needed no changes.

## 3. What changed in the doc (Step 2 + Step 3)

- Header table: "Datos de carga manual" row updated — no manual indicator
  is active anymore; `manuales.json` is a historical record only.
- New "Nota metodológica (8 de julio de 2026)" paragraph in Encuadre:
  documents the swap, the honest caveat (senator voting behavior ≠
  governor's executive stance), and that `gobernadores_alineamiento`'s
  band definition is kept inert in `itcp.py::BANDAS_ITCP` (same pattern as
  `cohesion_bloque`) but no longer weighted or read.
- ITCP formula, dimension table, bandas table, "Indicadores activos" table:
  `gobernadores_alineamiento` → `alineamiento_senadores_prov`, marked
  **provisional** in the bandas table per the brief's Step 3 instruction.
- "Score actual del cinturón" and "Nota de continuidad": updated to
  ITCP=68,4 / tensión 3,2/10, with an added sentence attributing part of
  the ITCP's small rise (67,2→68,4, both same-day corridas) to the
  indicator swap (85,0→100,0 banda points) plus normal live-source drift.
- New full `### alineamiento_senadores_prov` detail subsection (replacing
  the old `### gobernadores_alineamiento` one), written in the same style
  as `cohesion_bloque_senado`/`adhesion_reformas_provincial`: qué mide,
  fuente, cálculo, reemplaza-a (preserving the 4-proxy investigation
  history from `manuales.json._meta.pendiente_automatizacion` as
  historical context, not deleted), caveat honesto, bandas provisionales,
  último valor, backfill real, and the card-vs-serie window caveat.
- `ratio_dnu` detail line and `adhesion_reformas_provincial` detail line
  updated to current live values/dates.
- "Notas de mantenimiento": added a bullet for `alineamiento_senadores_prov`
  (shared Senado session risk with `cohesion_bloque_senado`), rewrote the
  "Datos de carga manual" bullet (nothing active today), added
  `alineamiento_senadores_prov` to the provisional-bandas list, and added
  the `gate_calidad.py` G3 gap as a named follow-up item.

## 4. Staging and commit (Step 4)

`git diff --cached --stat` immediately before committing:

```
 .../informe_coyuntura/docs/cinturon_politica.md    | 47 +++++++++++++---------
 1 file changed, 27 insertions(+), 20 deletions(-)
```

Exactly one file staged. Confirmed `scripts/descargar_series.py`'s diff was
identical before and after running the full pipeline (63 insertions / 1
deletion both times) — the pre-existing "motos" WIP was never touched,
never staged, never committed.

Commit:

```
a84aad7 docs(politica): sincroniza cinturon_politica.md con alineamiento_senadores_prov (reemplazo de gobernadores_alineamiento)
 1 file changed, 27 insertions(+), 20 deletions(-)
```

`git status --short` after the commit shows only the expected leftover
pipeline-regenerated files (macro/gestion/vida_cotidiana/espiritu_epoca
caches+series, `informe.json`/`informe.md`, `web/src/data/*.json`,
`data/historico/indicadores.json`, `data/vida/sentimiento_serie.json`,
`data/vida/snic_serie.json`) plus the pre-existing unrelated dirty files
(`scripts/descargar_series.py` motos WIP, `scripts/gestion.py`,
`tests/test_itcg.py`) and 2 untracked files
(`data/vida/motos_serie.json`, `scripts/vida_cotidiana/data/vida_cotidiana_20260708_1646.json`)
— none of it staged or committed by this task.

## 5. Self-review checklist

- [x] Every real number cited in the doc verified byte-against
      `output/cache/politica.json` / `output/informe.json` (not invented).
- [x] `gobernadores_alineamiento` handled in all 7 places it appeared in
      the doc (header table, methodology note, formula, dimension table,
      bandas table, indicadores activos table, detail section,
      maintenance notes) — not just the one détaille section named in the
      brief's Step 2.
- [x] `alineamiento_senadores_prov` marked provisional in the bandas table
      per Step 3.
- [x] `ratio_dnu` drift (1,471→1,529) caught and corrected — would have
      been an internal contradiction against the updated ITCP=68,4 headline
      otherwise.
- [x] `gate_calidad.py` G3 gap investigated to root cause, confirmed
      by-design not a bug, documented in the doc, left unfixed (out of
      scope) — not silently ignored.
- [x] Full test suite: 125/125, `test_politica_itcp_reconcilia` explicitly
      re-verified passing.
- [x] Staging scope verified clean via `git diff --cached --stat`
      immediately before commit: exactly `docs/cinturon_politica.md`.
- [x] `scripts/descargar_series.py` never staged, diff unchanged
      before/after the pipeline run.
