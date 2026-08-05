# Task 11 (follow-up) — Report

Branch: `feature/itcp-cohesion-bloque-politica`
Commit: `2484acf` — `fix(web): regenera datos de la web con los indicadores nuevos de política + sincroniza descripciones.ts`

## Status: DONE_WITH_CONCERNS

Both assigned findings are closed and build-verified. A third, pre-existing issue
was uncovered as a direct consequence of properly closing Finding 1 — it does not
block this task's scope but **does block CI / merge** and is documented below in
detail so it's a turnkey follow-up.

---

## Finding 1 — Build-reproducibility risk: CLOSED (real data, no guard needed)

### What was true before
- `output/cache/politica.json` (working tree, uncommitted) already had real,
  live-fetched data for `cohesion_bloque_senado` (99.5, Senado Rice cohesion) and
  `adhesion_reformas_provincial` (66.7%, RIGI adhesion), generated earlier today
  by a prior real run of `scripts/politica.py` — this was **not** entangled with
  any other in-progress work (`politica.py` only imports `gestion` for its ACLED
  fetcher, never the unrelated SSS code path).
- `output/series/politica.csv` already had the correct real backfilled rows,
  committed in `da94098`.
- `output/informe.json` / `web/src/data/informe.json` (the file the Astro build
  actually reads, via `web/src/lib/datos.ts`) had **never** been regenerated to
  include these 2 indicators — confirmed by diffing HEAD's `informe.json`
  against the committed `politica.csv`/cache.

### What I did
1. Did **not** re-run `descargar_series.py` or `politica.py` — data was already
   fresh and correct; re-running would only add ACLED/HCDN/Senado/MAGyP network
   risk for zero correctness gain.
2. Ran the real downstream pipeline: `python scripts/generar_informe.py` then
   `python scripts/publicar.py`.
3. **Working-tree complication handled:** this repo's working tree already had
   substantial *unrelated* uncommitted work when I started — a motos-serie
   backfill in `scripts/descargar_series.py` (+ untracked
   `data/vida/motos_serie.json`) and an RNEMP/SSS parsing fix in
   `scripts/gestion.py` (+ a new test in `tests/test_itcg.py`) — plus ordinary
   daily-refresh drift in `data/gestion/*.json`, `data/historico/indicadores.json`,
   `data/vida/*.json`, and the `macro`/`gestion`/`vida_cotidiana`/`espiritu_epoca`
   caches/series (all pre-dating this session). To guarantee the regenerated
   `informe.json` reflects **only** committed code (nothing from the unreviewed
   WIP), I temporarily reset those 4 non-politica caches + 3 series CSVs to HEAD,
   regenerated, verified the diff was isolated to `politica` (see below), then
   restored the originals byte-for-byte from a scratchpad backup before staging.
4. Verified with a scripted diff (HEAD vs regenerated) across all 4 non-politica
   cinturones: the **only** cross-cinturón change is
   `espiritu_epoca.sentimiento_digital` (6.2 → 5.5), which is not a leak — it's
   `informe.json` catching up to `output/cache/espiritu_epoca.json`'s value that
   was **already committed at HEAD** (HEAD's `informe.json` pre-dates HEAD's own
   cache by about a day — a pre-existing staleness, now fixed as a side effect).
   `apertura_comercial` (SSS-affected indicator) and `patentamiento_motos`
   (motos-affected indicator) are byte-identical before/after — confirming zero
   WIP leakage.
5. Ran the project's own `python scripts/gate_calidad.py` (read-only, exit 0,
   one advisory: 2/12 politica indicators in carry-forward, expected/documented).
6. Ran `cd web && npm run build` for real: **64 pages built successfully**,
   including `/metodologia/cohesion_bloque_senado/index.html` and
   `/metodologia/adhesion_reformas_provincial/index.html`. Spot-checked the
   rendered HTML: no `undefined`/`NaN` artifacts, real values present
   (`cohesion_bloque_senado` = 99.5%, `adhesion_reformas_provincial` = 66.7%).

**No defensive null-guard was needed** — real data was obtainable and used, per
the task's stated preference. `[id].astro` remains as-is.

### Result
`output/informe.json`, `web/src/data/informe.json` (+ `web/src/data/series.json`,
+13 series points for the 2 new indicators, cleanly isolated the same way),
`output/informe.md`, and `output/cache/politica.json` were staged and committed.

---

## Finding 2 — `descripciones.ts` staleness: CLOSED

Read `web/src/lib/descripciones.ts` in full (interface `Descripcion { que, aporta,
frecuencia, tipo }`, keyed by indicator id, rendered in the "Qué mide y por qué
importa" section — directly above fichas.ts's "Cómo se calcula" section).

- **`cohesion_bloque`**: replaced "Qué porcentaje de los diputados de LLA vota
  alineado con la posición oficial del bloque" / "Indica la disciplina de la
  tropa propia..." with wording matching fichas.ts's corrected mechanism (favor
  minus contra, absolute value, over total votes, per contested roll-call,
  90-day average) and toned down the informal "disciplina de la tropa propia"
  phrase per the task's optional-polish note.
- **Added** `cohesion_bloque_senado` and `adhesion_reformas_provincial` entries,
  matching fichas.ts's content/register.
- **`protestas_caba`**: confirmed **no change needed**. `FICHAS` has a single
  global entry for this id anchored to `cinturon: "gestion"` (per commit
  `b8bfc09`'s own message — deliberately not duplicated as a 3rd new ficha); the
  política reading only appears via fichas.ts's `dobleUso` prose inside the
  "Cómo entra al índice" section, which `descripciones.ts` doesn't have a field
  for. Since there is no separate política ficha route for this id,
  `descripciones.ts` doesn't need a dual entry — it's keyed purely by id, same
  as FICHAS.
- Verified in the built HTML: `posición oficial`/`vota alineado` no longer
  appear as a live (uncorrected) claim on any of the 3 pages; the only
  remaining mentions of "posición oficial" are the corrected negation
  ("no si acompaña una «posición oficial»...") and the changelog note
  describing the old vs. new definition.
- `npm run build` (same run as Finding 1) confirms no TS/build errors from the
  interface-shaped additions. `npx astro check` was not run (would have
  required installing `@astrojs/check`+`typescript` as new dependencies —
  declined to avoid touching `package.json`/lock); `astro build`'s own
  TS-aware compilation already succeeded, which is sufficient.

---

## Concern (does not block this task, but blocks merge): stale `test_publicar.py` reconciliation for ITCP

Running `python -m pytest tests -q` against the properly-regenerated snapshot
(not required by the task, but done as due diligence, matching CI's own gate
order) surfaces **2 pre-existing failures**, both rooted in the same gap: ITCP
(commits `3849688`/`c965d39`, this branch) was wired into the collector but
never propagated downstream:

1. `tests/test_publicar.py::test_aporte_score_reconcilia_con_score_publicado`
   — asserts política's score is still a simple average of `aporte_score`
   (a comment in the test literally says "solo política queda como promedio
   simple" — pre-ITCP assumption). Since ITCP is a weighted 5-dimension
   parametrica, the assertion now fails (promedio 4.6 vs. score publicado 3.5).
2. `tests/test_publicar.py::test_publicar_genera_snapshot` — asserts every
   indicator record has `unidad`/`fecha_dato`/`desactualizado`.
   `cohesion_bloque_senado` and `adhesion_reformas_provincial`'s cache records
   are missing `desactualizado` (and have `aporte_score: None`).

Also found (does not crash, but is a real content gap, live on production
today for **all** política fichas, not just the 2 new ones):
`scripts/generar_informe.py`'s `for indice in ("itcm", "itcg")` loop never
forwards `cache["itcp"]` into `informe.json`, and `web/src/lib/datos.ts`'s
`indiceDe()` has no `itcp` branch — so every política ficha page silently
drops its "Pesa X% del ITCP" / "Puntaje en el ITCP" chips and dimension
breakdown (they render fine, just incomplete).

I did **not** fix these: per the task's own "NEEDS_CONTEXT when unclear/unsafe"
clause, this is genuinely outside the 2 disclosed findings — fixing #1 requires
building real ITCP-semantics reconciliation logic (like the existing
`test_macro_itcm_reconcilia`) I haven't established confidence in; fixing #2
would mean re-running the flaky live network collector
(`politica.py` → ACLED/HCDN/Senado/MAGyP) or hand-patching a generated cache,
both explicitly things I was told to avoid/avoided. CI's `pytest tests` step
has no `set +e`, so **this branch currently fails its own G4-G5 gate** the
moment `informe.json` is properly regenerated (which is what Finding 1 required)
— this was invisible before only because `informe.json` was stale.

Nothing here is undone or reverted; the pytest run's `publicar.py` subprocess
call did temporarily re-clobber my isolated web snapshot with entangled data —
I caught it, re-isolated, rebuilt (npm build only, no further pytest), and
restored the unrelated dirty files before staging/committing.

---

## Self-review checklist

- Fresh-checkout `npm run build` simulation: **passes**, 64 pages, both new
  ficha routes render with real data.
- `descripciones.ts` ("Qué mide") vs `fichas.ts` ("Cómo se calcula") for
  `cohesion_bloque`: **now agree** — both describe the favor-minus-contra
  mechanism; neither claims "official position" alignment as current fact.
- 2 new ficha pages have real data (not a guard): **confirmed** in built HTML.
- Unrelated in-progress work (motos backfill, SSS parsing fix) in the working
  tree: **untouched** — identical diff stat before/after my session,
  `git status` confirms it's still dirty/uncommitted exactly as found.
- Staged/committed exactly 6 files, no `git add -A` used.
