# Task 13 — Fix 3 Codex code review findings (feature/itcp-cohesion-bloque-politica)

## Status: DONE

Commit: `13cc9a9` — `fix(politica): corrige 3 hallazgos de code review externo (Codex) — guard de legado en cohesion_bloque, desactualizado faltante y ficha ITCP 404`

Files changed (staged explicitly, no `-A`): `scripts/politica.py`, `tests/test_politica_cohesion.py`, `web/src/lib/fichas.ts` (3 files, 167 insertions, 1 deletion). All other pre-existing dirty files (data/output cache regen, `scripts/gestion.py`, `scripts/descargar_series.py`, `tests/test_itcg.py`, the itcp plan doc, the untracked `motos_serie.json`) were left untouched and unstaged.

---

## Finding 1 [P1] — legacy manual cohesion cache leaking into ITCP scoring

**Verification before fixing:** confirmed via `git show 584571b:./data/politica/manuales.json` that `cohesion_bloque`'s legacy manual shape is exactly `{"valor": 78, "estado": "placeholder", "unidad": "% votos en línea con la posición oficial del bloque LLA", "fuente": ..., "notas": ..., "fecha_dato": "2026-04-01"}` — no `n_actas`, no `corrida_exitosa_en`. Confirmed `fetch_cohesion_bloque()`'s real return dict always sets `n_actas` (even 0 when there are no votes in the window) and `corrida_exitosa_en` on every successful run. **This is a safe, unambiguous discriminator.**

Also verified (per instruction) whether `cohesion_bloque_senado` and `adhesion_reformas_provincial` ever had a manual precedent: `git log -p -- data/politica/manuales.json` shows neither ever appeared in that file — `cohesion_bloque_senado` is entirely new, and `adhesion_reformas_provincial` is explicitly documented (commit `ea95da2`) as a "indicador NUEVO y DISTINTO" from the start. **Neither needs the guard.**

**Important discovery, not hypothetical:** `output/cache/politica.json`'s current `cohesion_bloque` entry IS the legacy shape (`valor: 78, estado: "placeholder"`, no `n_actas`) and it IS currently being scored in the ITCP (`puntaje_itcp: 79.0`, `peso_efectivo: 0.13`). This is the live production cache today — `docs/cinturon_politica.md` confirms the Rice scraper is currently blocked by anti-bot detection (ADR-0037), so this bug is actively corrupting the published ITCP right now, not just a future-merge risk.

**Fix:** added `_es_cohesion_legado(anterior: dict) -> bool` (returns `True` iff `"n_actas" not in anterior`) in `scripts/politica.py`, applied right after `anterior_cohesion = indicadores_anteriores.get("cohesion_bloque")` in `main()`: if legacy, `anterior_cohesion` is set to `None` before the 3-branch chain, so all three branches correctly treat it as "no fresh Rice data yet."

**Test outcome:** No precedent exists anywhere in the test suite for testing `main()` directly (it calls ~12 live fetchers + load/save_cache) — confirmed via `advisor` consultation that testing the guard function directly, mirroring the existing `_cohesion_desactualizada` precedent, is the correct scope (duplicating main()'s branch logic in a test would give false confidence — a copy that could drift from the real code silently). Added 3 tests to `tests/test_politica_cohesion.py`:
- `test_es_cohesion_legado_detecta_placeholder_manual` — exact legacy dict → `True`
- `test_es_cohesion_legado_no_marca_forma_nueva_como_legado` — exact new-shape dict → `False`
- `test_es_cohesion_legado_no_marca_receso_legislativo_como_legado` — new shape with `valor: None` but `n_actas: 0` (receso legislativo) → `False` (guards against a false positive on the "successful run, no votes in window" case)

**Honesty note on test coverage:** the tests prove the discriminator function is correct in isolation. The one-line wiring (`anterior_cohesion = None`) inside `main()` is verified by direct code inspection, not by an executed test of `main()` itself — there was no reasonable way to test that without either duplicating production branch logic (rejected, per above) or mocking ~12 unrelated fetchers (rejected as disproportionate and fragile, per advisor).

**Behavioral consequence to flag:** on the next real pipeline run (while the scraper is still blocked), `cohesion_bloque` will now be **absent** from `frescos`/the published index — not silently frozen at 78 — until the scraper has one genuine successful run. The `cohesion_interna` dimension will renormalize to `cohesion_bloque_senado` alone (~100), which will nudge the published ITCP up slightly and tension down slightly. This is the intended fix, not a regression, but it is a real, visible change to the next published number.

---

## Finding 2 [P2] — missing `desactualizado` on fresh `cohesion_bloque` scrape

Confirmed via reading `fetch_cohesion_bloque_senado` and `fetch_adhesion_reformas_provincial` that both already set `"desactualizado": False` on success; `fetch_cohesion_bloque` was the only one missing it. Added `"desactualizado": False` to its return dict (`scripts/politica.py`, end of the function).

**Test:** `test_fetch_cohesion_bloque_incluye_desactualizado_false` — asserts a successful `fetch_cohesion_bloque()` call returns `desactualizado: False`. Confirmed.

---

## Finding 3 [P2] — broken `/metodologia/itcp/` link

Confirmed `web/src/lib/datos.ts::indiceDe()` already returns the ITCP block (sigla, nombre, descripcion) and `informe.json`/`web/src/data/informe.json` already publish `cinturones.politica.itcp` with `valor`, `banda_legible`, `dimensiones`, `ajustes_aplicados`. Confirmed `web/src/pages/metodologia/[id].astro` builds its static paths from `Object.keys(FICHAS)`, and `FICHAS` had no `itcp` key — hence no `/metodologia/itcp/` route was ever generated, and the homepage card 404'd.

**Fix:**
- Added `"politica"` to the `FichaIndice.cinturon` union type (it was missing — only `FichaIndicador.cinturon` included it).
- Added a new top-level `itcp: FichaIndice` entry to `web/src/lib/fichas.ts`, mirroring `itcg`'s structure (bands/interpolation-based, not base-100), placed after `itvc` (matching the file's convention of appending newly-added index fichas at the end). Content: 5 dimensions with exact weights from `scripts/itcp.py::DIMENSIONES_ITCP` (poder_legislativo 30%, alianzas_territoriales 25%, cohesion_interna 20%, conflicto_social 15%, imagen_voto 10%), plain-language explanation (political capital / governability per Matus, explicitly not popularity), the 0–100 reading scale, and tension = (100−ITCP)/10. Institutional register throughout, no ADR numbers (content was cross-checked against `docs/adr/0036-itcp-parametrica-politica.md` and `docs/cinturon_politica.md` for factual accuracy, then rewritten in public-facing prose with no ADR references, per project convention).
- **Correction made during self-review:** my first draft of the `robustez`/`validacion` sections wrongly claimed Monte Carlo sensitivity analysis was "pending" for ITCP. Checked `scripts/publicar.py::_scoring_indice` and found it generically calls `sensibilidad.robustez_compacta()` for ANY bloque with `dimensiones` — including `itcp` — so Monte Carlo (p05/p95, leave-one-out dominant component) **is** already computed and published for ITCP (confirmed live in `web/src/data/informe.json`: `p05: 62.5, p95: 67.6, dominante: veto_quorum`). Corrected the ficha to describe this correctly. Only `validacion` (external anchor / cross-validation matrix) is genuinely absent for ITCP — confirmed no `_validacion_itcp()` function exists in `publicar.py` and ITCP is excluded from `_validacion_cruzada()`'s pares (`ITCM`/`ITCG`/`ITVC` only). The ficha's `validacion` section and corresponding `limitaciones` bullet correctly state this is pending.

**Build outcome:** `cd web && npm run build` succeeded (65 pages built, no errors). Confirmed by inspecting the generated file directly (output resolves to `../../../web/informe` per `astro.config.mjs`'s non-`dominio` branch → `C:\Users\trico\OneDrive\UBA\Analisis CIGOB\web\informe\metodologia\itcp\index.html`):
- File exists, 17KB+, renders real runtime data: "ITCP", "64,7/100", "Moderadamente aflojado", "Poder legislativo", "Cohesión interna del oficialismo".
- Monte Carlo callout renders with real numbers: "90% de escenarios 62,5–67,6 (tensión 3,2–3,8). Componente dominante: Sesiones caídas por quórum — sin él, el índice sería 59,9."
- Homepage (`web/informe/index.html`) link to `metodologia/itcp/` confirmed present; diccionario index page (`web/informe/metodologia/index.html`) confirmed lists the `itcp` card.

---

## Out-of-scope issue discovered (flagged, not fixed)

While reading `web/src/lib/fichas.ts`'s política section, found that 8 of the original 9 indicator fichas (`votometro_ventaja_lla`, `ratio_dnu`, `movilizacion_cepa`, `iaf_transferencias`, `eficacia_legislativa`, `gobernadores_alineamiento`, `veto_quorum`, `comisiones_caidas`) still contain stale `incidenciaTexto` claiming *"El cinturón político no usa un índice compuesto: su score es el promedio simple de las tensiones de los indicadores disponibles"* — this was true before ITCP shipped but is no longer accurate (the 3 newer indicator fichas — `cohesion_bloque`, `cohesion_bloque_senado`, `adhesion_reformas_provincial` — were already correctly updated to describe their place in the ITCP). This is real staleness but was not one of the 3 assigned findings and touches 8 additional indicator fichas beyond the strict scope/file list given for this task, so it was **not** fixed here — flagging for a follow-up task.

---

## Test suite

`python -m pytest tests/ -v` → **97 passed**, 0 failed, 0 regressions (includes the 4 new tests: 3 for `_es_cohesion_legado`, 1 for the `desactualizado` key).

## Concerns

- None blocking. The Finding-1 fix changes real published output on the next pipeline run (see "Behavioral consequence" above) — this is intended and correct, but worth the team's awareness before the next scheduled run merges to `main`.
- The stale "promedio simple" ficha text (8 files) is a good candidate for a quick follow-up, not urgent.
