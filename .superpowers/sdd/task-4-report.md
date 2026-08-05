# Task 4 Report: Wiring en itcp.py y politica.py (Plan 5 — alineamiento_senadores_prov)

> Nota: este archivo sobrescribe una versión anterior de `task-4-report.md`
> que pertenecía a otra tarea (Plan 3 — backfill de `cohesion_bloque_senado`),
> por instrucción explícita del coordinador de esta tarea (mismo esquema de
> numeración reutilizado entre planes en este proyecto).

**Status:** DONE
**Commit:** `89e7ed0` — "feat(politica): reemplaza gobernadores_alineamiento por alineamiento_senadores_prov en el ITCP"

## Summary

Wired `alineamiento_senadores_prov` (built in Plan5 Tasks 1-3) into the ITCP
band tables, dimension weights, `INDICADORES_ESPERADOS`, and `main()`'s live
collector, replacing `gobernadores_alineamiento` (the frozen manual
placeholder, 55%, since 2026-04-01) for scoring purposes — without deleting
the placeholder's code/data (per the plan's own global constraint).

## Pre-implementation investigation (per task instructions: "don't guess")

Before touching `main()`, I read the real code around `INDICADORES_ESPERADOS`
and `main()`'s collector wiring:

- `gobernadores_alineamiento`'s ONLY read site in `politica.py` was the
  `("gobernadores_alineamiento", lambda: fetch_manual("gobernadores_alineamiento"))`
  entry in `main()`'s flat `colectores` list. There is no separate
  "context indicator" exposure mechanism for the ITCP (unlike gestion.py's
  ITCG) — `_anotar_indicadores_itcp`'s own docstring confirms this
  explicitly: "A diferencia del ITCG, el ITCP no tiene indicadores de
  contexto declarados todavía."
- `manuales.json` and the generic `fetch_manual()` helper are untouched —
  they remain as historical reference, matching the plan's explicit
  constraint ("`gobernadores_alineamiento` NO se borra del código/datos").
- `fetch_alineamiento_senadores_prov` (already implemented in Task 2) has a
  **byte-identical return contract** to `fetch_cohesion_bloque_senado`:
  returns `None` only on session failure, and a dict with `"valor": None`
  (not `None` itself) when the corrida reaches senado.gob.ar but finds no
  divided actas in the recency window (normal legislative recess).

**Design decision (confirmed via advisor before implementing):** rather than
adding `alineamiento_senadores_prov` to the flat `colectores` list (which
would incorrectly stamp `"desactualizado": True` during any recess, even
though the source was reachable — the exact anti-pattern `cohesion_bloque`/
`cohesion_bloque_senado` already got dedicated blocks to avoid), I gave it
the same dedicated block treatment as `cohesion_bloque_senado`, reusing the
existing generic `_cohesion_desactualizada()` staleness check. This mirrors
an already-tested sibling; no new `main()`-level test was added (declared
test scope was `test_itcp.py`).

## Deviation from the brief's literal code (flagged, verified, fixed)

The brief's exact band tuples for `alineamiento_senadores_prov` —
`(0,10,10),(10,25,40),(25,45,65),(45,65,85),(65,100,100)` — were **not**
actually equivalent to `gobernadores_alineamiento`'s bands despite the
brief's own comment claiming "mismas anclas". Root cause: `calcular_indice`
scores via `parametrica.puntaje_interpolado` (linear interpolation between
band midpoint anchors, ADR-0021), not discrete `puntaje_banda` lookup. A
**finite** top band `(65,100,100)` places its interpolation anchor at the
midpoint (82.5), so saturation to puntaje=100 only kicks in at valor≥82.5 —
whereas the old `gobernadores_alineamiento` band `(65.0, INF, 100)` anchors
at 65 (open/infinite band → anchor at the finite edge), saturating
immediately above 65.

This is the same class of brief-authoring bug repeatedly caught elsewhere in
this project (see `progress.md`, e.g. Plan2-Task 1's band-boundary bug).
Concretely, it was caught because `test_calcular_itcp_pondera_dimensiones`
failed with `99.5 != 100.0` after wiring the literal brief bands (a value of
70.0, documented as "puntaje 100", actually interpolated to 93.2 under the
finite band).

**Fix applied:** kept the *open* (±INF) tail structure, exactly matching
`gobernadores_alineamiento`'s original bands and the file-wide convention
(every other band table in `itcp.py`, including other 0-100%-bounded
indicators like `cohesion_bloque`/`cohesion_bloque_senado`/
`movilizacion_cepa`, uses ±INF tails — the brief's finite-bounded table was
the only outlier):

```python
"alineamiento_senadores_prov": [
    (65.0, INF, 100),
    (45.0, 65.0, 85),
    (25.0, 45.0, 65),
    (10.0, 25.0, 40),
    (-INF, 10.0, 10),
],
```

Verified: `puntaje_interpolado(68.3, ...) == 100.0` and
`puntaje_interpolado(70.0, ...) == 100.0` (68.3 is the real live value from
Plan5-Task 2's verification). `test_calcular_itcp_pondera_dimensiones` was
left asserting `valor == 100.0` (its original, correct expectation) — not
weakened to accept the buggy 99.5.

The brief's dead-band comment for `gobernadores_alineamiento` and the module
docstring were also updated for consistency (documentation only, same file).

## Step 1-4: itcp.py changes

- `BANDAS_ITCP["gobernadores_alineamiento"]` **kept** (not deleted — dead
  reference, per plan's explicit "no se borra" constraint; confirmed via
  grep that nothing enumerates `BANDAS_ITCP.keys()` as a whole set, so the
  orphan entry is harmless — `sensibilidad.py` only walks the *published*
  `dimensiones` structure, never `BANDAS_ITCP` directly).
- `BANDAS_ITCP["alineamiento_senadores_prov"]` added (open-tail bands, see
  above — deviates from brief's literal finite tuples).
- `DIMENSIONES_ITCP["alianzas_territoriales"]["indicadores"]`:
  `"gobernadores_alineamiento": 0.30` → `"alineamiento_senadores_prov": 0.30`.

## Step 5: politica.py changes

- `INDICADORES_ESPERADOS`: `"gobernadores_alineamiento"` →
  `"alineamiento_senadores_prov"` (count unchanged, still 12).
- `main()`: removed the `gobernadores_alineamiento` lambda entry from the
  flat `colectores` list. Added a dedicated block (mirroring
  `cohesion_bloque_senado`'s block structure exactly) calling
  `fetch_alineamiento_senadores_prov()`, with the same 3-way branch (fresh /
  corrida-exitosa-but-no-new-votes reuse / genuinely stale via
  `_cohesion_desactualizada`).
- Module docstring header + "Nota" paragraph updated to describe
  `alineamiento_senadores_prov` instead of `gobernadores_alineamiento`
  (documentation only).
- `manuales.json` and `fetch_manual()` left untouched (unused for ITCP
  scoring now, but not deleted).

## Step 1 test (test_itcp.py) + fix to existing test

Added exactly the brief's Step 1 test:

```python
def test_bandas_itcp_tiene_alineamiento_senadores_prov_no_gobernadores_alineamiento():
    assert "alineamiento_senadores_prov" in itcp.BANDAS_ITCP
    dim = itcp.DIMENSIONES_ITCP["alianzas_territoriales"]
    assert "alineamiento_senadores_prov" in dim["indicadores"]
    assert "gobernadores_alineamiento" not in dim["indicadores"]
```

Also renamed the key in the existing `test_calcular_itcp_pondera_dimensiones`
fixture (`"gobernadores_alineamiento": 70.0` → `"alineamiento_senadores_prov":
70.0`) — this test's file (`tests/test_itcp.py`) was explicitly in the
brief's declared scope, and leaving a stale key referencing a name no longer
in `DIMENSIONES_ITCP` would have made the assertion pass for the wrong
reason (dead key silently ignored) rather than actually exercising the new
indicator.

## Step 6: Full test suite + live ITCP verification

Ran as **separate commands** (not the brief's `&&` chain), per advisor's
recommendation, since a non-zero exit from `politica.py` (expected: 11/12,
`cohesion_bloque` Diputados still blocked per ADR-0037) would have skipped
verification if chained, and pytest's own exit code shouldn't gate it either.

### Full test suite

```
============================= 125 passed in 3.02s =============================
```
125/125, run both before and after the commit (identical result). No
regressions. `tests/test_publicar.py::test_politica_itcp_reconcilia` — which
hardcodes `"gobernadores_alineamiento"` in a set and reads
`web/src/data/informe.json` — still passes unchanged, because that file is
static/untouched by Task 4 (only `publicar.py`/`generar_informe.py`
regenerate it, which is explicitly Task 5's job per the plan's own Step 1
pipeline run). This is expected sequencing, not a gap I introduced. Flagging
for whoever runs Task 5: that test's hardcoded `faltantes` set will need
`"gobernadores_alineamiento"` swapped for `"alineamiento_senadores_prov"`
once `informe.json` is regenerated with the new indicator name — Task 5's
declared file scope (`docs/cinturon_politica.md` only) doesn't cover this,
so it may need a follow-up.

### Live ITCP verification (`python scripts/politica.py`)

```
[OK] politica: score=3.2 frescos=11/12
```
Exit code 1 is expected/normal here (11/12, not 12/12 — `cohesion_bloque`
Diputados remains structurally blocked per ADR-0037, pre-existing and
unrelated to this task).

Inspected `output/cache/politica.json` directly:

```json
"alineamiento_senadores_prov": {
  "valor": 68.3,
  "unidad": "% votos de senadores no-LLA alineados con LLA, por provincia",
  "fuente": "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
  "fecha_dato": "2026-06-04",
  "n_provincias": 24,
  "corrida_exitosa_en": "2026-07-08",
  "desactualizado": false,
  "en_indice": true,
  "dimension": "alianzas_territoriales",
  "puntaje_itcp": 100.0,
  "puntaje_banda": 100.0,
  "peso_efectivo": 0.075
}
```

- `itcp.valor`: **68.4** (banda: `moderadamente_aflojado`) — up from the
  previously-documented ~67.2/67.4 (matches advisor's sanity anchor: real
  alineamiento (68.3→puntaje 100) beats frozen gobernadores (55→puntaje 85),
  so a small upward tick was expected).
- `score`: 3.2 (tension = (100−68.4)/10).
- `alianzas_territoriales` dimension indicators: `iaf_transferencias`,
  `alineamiento_senadores_prov`, `adhesion_reformas_provincial` — confirmed
  `gobernadores_alineamiento` is fully absent from `indicadores`.
- 24/24 provinces contributed (maximum possible), fecha_dato 2026-06-04.

## Staging discipline

`scripts/descargar_series.py` was **not touched** by this task (confirmed —
I never opened it for editing). Staged only the 3 intended files with a
plain `git add` (no `-p` needed, per the task's own instruction that these
files are clean):

```
git diff --cached --stat  (captured right before commit)
 projects/informe_coyuntura/scripts/itcp.py     | 37 +++++++++++++++++++++++---
 projects/informe_coyuntura/scripts/politica.py | 36 ++++++++++++++++++++++---
 projects/informe_coyuntura/tests/test_itcp.py  |  9 ++++++-
 3 files changed, 73 insertions(+), 9 deletions(-)
```

Post-commit `git status --short` confirms only pre-existing unrelated
modified/untracked files remain (`scripts/descargar_series.py` motos WIP,
`scripts/gestion.py`, `tests/test_itcg.py`, various `output/`/`web/src/data/`
regeneration artifacts from the live run and prior sessions) — none staged
or committed by this task.

## Concerns for follow-up (not blocking, disclosed)

1. `tests/test_publicar.py::test_politica_itcp_reconcilia` will need its
   hardcoded `"gobernadores_alineamiento"` string updated to
   `"alineamiento_senadores_prov"` once `output/informe.json` is regenerated
   (Task 5's pipeline run) — Task 5's declared file scope doesn't list this
   test file, so it may fall through unless caught.
2. The band-table deviation from the brief's literal tuples (open ±INF tails
   instead of the brief's finite `(65,100,100)`) should be verified by the
   reviewer against this report's reasoning, not against a naive diff of the
   brief's code block.
