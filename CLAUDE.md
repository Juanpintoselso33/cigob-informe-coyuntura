# Claude Code Context For This Repo

Canonical operating guide for Claude Code in this repo. Codex reads
`AGENTS.md` (same directory) — keep both in sync; this file is
the source of truth, `AGENTS.md` points back here.

## Do not bulk-load `.claude/skills/`

`.claude/skills/` has ~40 SKILL.md files, almost all BMAD (`bmad-*`):
product-planning workflows (PRD, architecture, brainstorming, epics/stories,
UX). **They are not relevant to the day-to-day work in this repo**, which is
data engineering on `projects/informe_coyuntura/` (Python collectors,
scoring, tests) — not product/PRD building. Do not scan or consider them per
turn. Only read a specific `SKILL.md` if the user explicitly invokes BMAD or
a named workflow by name.

`.claude/skills/informe-coyuntura.md` was rewritten 2026-07-09 (5 cinturones,
current paramétrica engines, current file layout) — still, it's a quick-
reference, not the source of truth. It will drift again as the project
evolves; when in doubt prefer `projects/informe_coyuntura/README.md`,
`docs/adr/`, and the tests over anything hand-summarized in a skill file.

## Repo overview

Monorepo for CIGOB/UBA political analysis tools.

- `projects/informe_coyuntura/`: data collectors, scoring (paramétricas
  ITCM/ITCG/ITVC/ITCP), report generation, versioned outputs, Astro web app.
  This is where nearly all active work happens.
- `web/`: legacy static site. **Not the deploy target.**
- `.github/workflows/`: daily data pipeline (`data-pipeline.yml`, 00:00 ART,
  commits as `github-actions[bot]`). The `pages.yml` workflow is DEAD — GitHub
  Pages was retired in July 2026. **The site deploys through Vercel, which
  builds every push to `main`** (production alias:
  `https://cigob-informe-coyuntura.vercel.app/`; the Astro app under
  `projects/informe_coyuntura/web/` is what it builds). Per-deploy
  `…-<hash>.vercel.app` URLs sit behind a login wall, so they are useless for
  showing anything to the user — always check the production alias.

Read the nearest `README.md` before changing a project; project docs have
the operational detail, the root README is just an entry point.

## Local environment: Mac and tower

The command blocks in this file are written for the tower (PowerShell, plain
`python`). On the **Mac** everything works the same once you know these four
things — set up and verified 2026-08-13:

- **Python.** There is no `python` on the PATH (Homebrew ships `python3`, with
  nothing installed in it). The project venv is
  `projects/informe_coyuntura/.venv`, built with uv on **Python 3.12** to match
  the CI. Either `source .venv/bin/activate` — after which every `python …`
  block in this file works verbatim — or call `.venv/bin/python` directly. To
  rebuild it:

  ```bash
  cd projects/informe_coyuntura
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -r requirements.txt
  ```

- **Web.** `node_modules` is installed under `projects/informe_coyuntura/web/`.
  `npm run build` · `npm run preview -- --port 4321`.
- **BigQuery.** `bigquery_export.py` (last step of every data run, ADR-0180)
  authenticates with `GOOGLE_APPLICATION_CREDENTIALS` in CI and with gcloud ADC
  locally. The gcloud SDK is installed (Homebrew cask, on the PATH) and the
  **ADC is set up** (verified 2026-08-14: a manual run exported all tables to
  `cigob-analytics.informe_coyuntura` without warnings). The `gcloud` CLI
  itself has no logged-in account and does not need one — the scripts go
  through the Python SDK. If the export ever starts failing with credential
  errors, re-run `gcloud auth application-default login` against project
  `cigob-analytics`.
- **Permissions.** The tree arrived from the tower with every directory at
  `555` — no write bit even for the owner. Editing existing files works, but
  creating them does not, which breaks `uv venv`, `npm install`,
  `git worktree add` and, worst of all, **`git add`** (`insufficient permission
  for adding an object to repository database .git/objects`, which only shows
  up once the work is already done). Fixed repo-wide; if it ever comes back:

  ```bash
  find . -type d ! -perm -u+w -exec chmod u+w {} +
  ```

### `.env`: seven credentials, and one trap that fails silently

`projects/informe_coyuntura/.env` holds seven credentials (BA Transporte ×2,
Presupuesto Abierto, ACLED ×2, ACLED-UBA ×2). It is gitignored, copied to each
machine by hand, never versioned. Nothing loads it for you — there is no
python-dotenv in `requirements.txt`, the scripts read `os.environ` directly, and
the CI injects the same names from GitHub secrets. Locally you export it
yourself:

```bash
set -a; source ./.env; set +a
```

**The trap** (hit 2026-08-14, cost one aborted pipeline run): the file arrived
from the tower with **CRLF** line endings, so `source` leaves a trailing `\r` on
*every* value. The tokens go out malformed, the source rejects the auth, and the
collector **falls back to cache without saying anything** — the run completes,
the gate passes, and you publish yesterday's data believing it is fresh. The
only hint is `command not found: ^M` scrolling past at the top.

Converted to LF and locked down to `600` on the Mac. Before trusting any file
that a shell has to `source`, check it:

```bash
file .env                    # must NOT say "with CRLF line terminators"
```

And when running the pipeline by hand, verify the credentials landed before
burning 20 minutes on a run that will quietly use cache:

```zsh
# zsh (the Mac's shell): ${(P)v} is its indirect expansion; in bash it is ${!v}
set -a; source ./.env; set +a
for v in BA_TRANSPORTE_CLIENT_ID PRESUPUESTO_ABIERTO_TOKEN ACLED_USERNAME; do
  [ -n "${(P)v}" ] || echo "FALTA $v"
done
```

The same warning applies to anything else copied over from the tower — check
first, don't assume.

## Working rules

- Spanish for user-facing prose/docs unless the surrounding file is English.
- Never version secrets.
- `.claude/`, `AGENTS.md`, `_bmad/`, `.superpowers/sdd/`, `docs/superpowers/`
  are assistant context, not product source — but they **are versioned**
  since 2026-08-05, so a fresh clone arrives with the working setup instead
  of an empty `.claude/`. Treat them as setup, not as deliverables: they
  don't need ADRs, tests, or pipeline runs. What stays ignored is anything
  per-machine (`.claude/settings.local.json`) or regenerable
  (`.superpowers/sdd/*.diff` — reproducible with `git diff <sha1>..<sha2>`).
  Secrets never go in any of them; `projects/informe_coyuntura/.env` stays
  ignored and must be copied to each machine by hand.
- Versioned outputs (`output/`, `scripts/vida_cotidiana/data/`) are
  intentional (audit trail) — don't delete tracked ones as "generated
  noise." Reverting *uncommitted, stale/inconsistent* local regenerations
  (e.g. a snapshot that mixes new code with an unrefreshed cache) is fine —
  the nightly pipeline regenerates them correctly. See git history around
  2026-07-09 for a worked example of the difference.
- Before editing, run `git status --short`; don't clobber unrelated local
  changes — this repo regularly has more than one thing in flight
  (`git add -p` / precise hunk-splitting when a file has your change mixed
  with someone else's WIP).
- `git pull --rebase` before pushing — the nightly bot commits to main and a
  plain push will be rejected as non-fast-forward.
- **Never `git add -A` / `git add .` in this repo — stage files explicitly.**
  **On the tower** the checkout lives inside OneDrive, and OneDrive restores
  stale copies of the generated snapshots (`web/src/data/informe.json`,
  `data/historico/indicadores.json`) over the good ones: they show up as
  modified with a *today* mtime but *yesterday's* `generated_at` inside, and
  no script wrote them. A blanket `add` then commits that stale snapshot over
  the cron's fresh one and it deploys. Verified twice on 2026-07-27, once by
  falling into it (fixed in `c6c0b6c`). The Mac checkout
  (`~/dev/trabajo/CIGOB/`) is **not** under OneDrive, so that specific hazard
  doesn't apply there — the rule still does, because the repo regularly has
  more than one thing in flight.
  - Tell-tale: `git status` dirty on generated files nobody regenerated.
  - If it happens, the cron's version is the good one — recover it with
    `git checkout <commit-with-bot-snapshot> -- <file>` and check that
    `generated_at` matches the nightly run, not your manual one.
- Validate with the narrowest useful command: `python -m pytest tests/ -k
  ...`, `npx tsc --noEmit`, `npm run build` — not a full pipeline re-run
  unless the task actually needs fresh live data.
- Design/methodology decisions go in `docs/adr/` (ADRs) — they're
  maintained, unlike `docs/archivo/cinturon_*.md`/`.docx`, which are
  read-only design specs from before implementation (moved into
  `docs/archivo/` 2026-07-12; see AGENTS.md history if that distinction
  matters for the task).

## ADRs: formato MADR v4, e ids que NO se renumeran

`docs/adr/` sigue **MADR v4** en castellano desde 2026-07-31.
Frontmatter YAML + esqueleto `Contexto y planteo · Factores de decisión ·
Opciones consideradas · Decisión (+ Consecuencias, Confirmación) · Pros y
contras · Más información`. `docs/adr/README.md` documenta el formato.

- **Los números de ADR son identificadores estables**: se citan >1.300 veces
  desde `scripts/`, `tests/`, `web/` y artefactos generados como
  `output/procedencia_anclas.json`. No se renumeran ni se fusionan archivos.
- **Los ids van entre comillas** (`id: '0012'`, `relacionado: ['0036']`). Sin
  comillas YAML 1.1 los lee como octal: `0012`→10, `0036`→30, y la referencia
  apunta a otro ADR sin que falle nada. Costó 38 filas del índice en silencio.
- El índice del README y las relaciones inversas **se generan**:
  `python scripts/adr_coherencia.py`. No editar la tabla a mano.
- `tests/test_adr_format.py` (993 tests) es el gate: frontmatter, vocabulario
  cerrado de `estado`, bidireccionalidad, índice sincronizado y que todo ADR
  citado desde código exista. Ese último chequeo encontró un ADR-0165 citado
  por `publicar.py` que nunca se había escrito.
- Si se reescribe el CUERPO de ADR existentes, verificar que no se perdió
  ninguna cifra ni identificador — ningún otro test mira el contenido:

  ```powershell
  python scripts/adr_migracion.py huella --git 5390885 > base.json
  python scripts/adr_migracion.py verificar base.json
  ```

  `5390885` es el último commit anterior a la migración.

## Publishing data "now" instead of waiting for the nightly cron

**First question, every time: does this change touch one cinturón or more
than one?** Answer that before running anything — it decides which of the
two paths below to use. Getting this wrong in either direction has actually
happened and cost real time (see both verified incidents below): guessing
"full pipeline" for a one-cinturón change burns ~20 min doing nothing
useful; guessing "just this collector" when multiple cinturones are
genuinely stale produces false G3 gate failures that look like real bugs.

**Before any of the sequences below**: the collectors need the seven
credentials exported (`set -a; source ./.env; set +a` — see the `.env` section
above). Without them the fetches fail auth and every collector falls back to
cache *silently*: the run finishes, the gate passes, and you publish stale data.
On the Mac, also activate the venv — there is no bare `python` on the PATH.

**One cinturón touched (the common case — a single collector/indicator
fix)**: scope it, don't touch the others at all.

```powershell
python scripts/<colector_del_cinturon>.py         # macro.py | politica.py | gestion.py | vida_cotidiana/main.py
python scripts/descargar_series.py --indicador <nombre>   # only if series/backfill also changed
python scripts/validacion_externa.py              # only if the change touched BANDAS_* or added/changed an indicator SERIES of a parametric index
python scripts/generar_informe.py
python scripts/publicar.py
python scripts/gate_calidad.py
python -m pytest tests -q
python scripts/bigquery_export.py                 # espeja la corrida en BigQuery (ADR-0180)
```

`validacion_externa.py` reconstructs each index's historical series from the
indicator series + current bands to correlate against external benchmarks
(EPU, Merval, riesgo país, ICC) — publicar.py embeds those r values in the
public snapshot. Band recalibrations and new monthly series change that
reconstruction, but the scoped path above didn't include the script until
2026-07-09, verified failure: after 3 ITCP band recalibrations + 2 new
monthly series in one day, the published ITCP↔EPU r was still the morning's
stale value (found by adversarial audit, not by any gate — no gate checks
validation freshness).

`descargar_series.py --cinturon <nombre>` / `--indicador <nombre>` (added
2026-07-09) touch only that scope — the other cinturones'/indicators'
series are left completely untouched, not just unchanged-by-coincidence, so
they can't drift out of sync with their own already-fresh cards.
`--indicador` merges into the existing CSV (preserves every other
indicator's rows). Skip `descargar_series.py` entirely if the change didn't
touch series/backfill data at all (e.g., just unblocking a collector's live
fetch). The individual collector scripts are already naturally scoped by
cinturón (separate scripts); none takes a per-indicator flag yet.

Verified failure mode 2026-07-09: unblocked one Diputados indicator
(`politica.py`-only change) but ran the full 11-step sequence below anyway
out of habit, costing ~20 min for a change that needed ~2. The full-pipeline
rule below is for *actual* multi-cinturón staleness, not a default to apply
unconditionally — check the "one vs. many" question above before reaching
for it.

**More than one cinturón genuinely stale, or unsure**: run the **full
pipeline in one continuous sequence**, same order as
`.github/workflows/data-pipeline.yml`:

```powershell
python scripts/macro.py
python scripts/politica.py
python scripts/gestion.py
python scripts/vida_cotidiana/main.py
python scripts/vida_cotidiana.py
python scripts/espiritu_epoca.py
python scripts/descargar_series.py
python scripts/validacion_externa.py
python scripts/generar_informe.py
python scripts/publicar.py
python scripts/gate_calidad.py
python -m pytest tests -q
python scripts/bigquery_export.py                 # espeja la corrida en BigQuery (ADR-0180)
```

Do not run collectors piecemeal in a way that leaves *some* cinturones
freshly re-fetched and others not — cards and series get fetched at
different moments from live sources that can shift in between, which fails
`gate_calidad.py`'s G3 check (card ≠ last series point) on indicators that
have nothing to do with the actual change. This looks like a real bug and
isn't — verified 2026-07-09 (rem_ipc_12m/iai/desregulacion_normativa all
"failed" from staleness alone, passed clean once run atomically). Don't
rabbit-hole into "why don't these match" for indicators outside the task's
scope; run the full sequence again instead. Set the expectation up front
(~15-20 min).

**After ANY manual pipeline run (full or scoped), before pushing**: run
`python -m pytest tests -q` in addition to `gate_calidad.py` — the real CI
runs both as separate sequential gates (G1-G3/G6 via gate_calidad.py, G4-G5
via pytest). `gate_calidad.py` passing does NOT mean the pytest
reconciliation tests pass. Verified 2026-07-09: skipped the pytest step
after a manual run, pushed a snapshot where `sentimiento_digital` had
silently vanished from `vida_cotidiana` (Google Trends rate-limited after
repeated same-day runs; `build_vida()` skipped adding the indicator
entirely instead of adding it with `valor=None`, so `_carry_forward` never
saw it to restore the last good value — fixed in `publicar.py`).
`gate_calidad.py` had nothing to catch that with (it checks
structure/freshness/card-vs-series, not indicator-count invariants) — only
`test_publicar.py` did. Same principle burned a second time the same day in
a different shape: `gate_calidad.py`/pytest also didn't check that every
indicator has a display label in `web/src/lib/datos.ts` — that gap now has
its own dedicated test (`tests/test_web_labels.py`, added 2026-07-09)
instead of being fixed only as a one-off symptom.

Commit + push the resulting `output/`/`web/src/data/` changes **to `main`**,
staging files explicitly (see the working rules above). Pushing to `main` is
what makes Vercel rebuild; it is not a duplicate of the nightly cron.

Then finish the job per **Definition of done** below. A pipeline run that ends
in a commit has changed nothing the user can see.

## Definition of done: the live site, not the commit

**This project exists to show data on a web page. A number that is in a commit
and not on the page is not delivered.** Before telling the user something is
ready, the whole chain has to hold:

    code → snapshot (`web/src/data/informe.json`) → `npm run build`
         → **merged/pushed to `main`** → Vercel deploy → **production URL opened
           and the number actually read there**
         → `bigquery_export.py` → la corrida queda en el archivo histórico

Verifying a link in the middle does not authorise saying "done".

**Toda corrida de datos termina en BigQuery, no en el commit.** El nocturno lo
hace solo (último paso de `data-pipeline.yml`); **una corrida manual no**, y esa
corrida se pierde para siempre del archivo histórico — las tablas de snapshot se
acumulan por `generated_at`, así que lo que no se sube ese día no se puede
reconstruir después. Si publicaste a mano, corré `bigquery_export.py`. Es
idempotente: re-correr la misma corrida no duplica. Ver ADR-0180.

- **A feature branch is invisible.** Work on a PR branch never reaches the site.
  If the user is waiting to see a change, the branch has to be merged to `main`.
  If there is a real reason to hold it, say so **up front and explicitly**
  ("this stays in the PR and will NOT show on the web until we merge") — never
  report "pushed" and let them find out by looking at an unchanged page.
- **Check production, not the intermediate artefact.** Fetch
  `https://cigob-informe-coyuntura.vercel.app/` (add `?cb=<n>` to dodge cache)
  and grep for the new value. The Vercel MCP (`list_deployments`) confirms
  READY/ERROR and the commit SHA of the deploy that is actually live.
- Verifying that a value landed in `output/validacion_externa.json`, or in the
  snapshot, or that the build passed, are all *necessary and insufficient*. The
  same mistake in miniature: a value can be computed and published to the
  intermediate JSON while `publicar.py` never surfaces it to the page.
- **Long PRs get expensive**: the cron commits generated snapshots to `main`
  nightly, so an unmerged branch accumulates conflicts in
  `output/cache/*.json`, `output/series/*.csv`, `web/src/data/*.json`. Resolve
  them by taking the cron's fresh data and **re-running the pipeline** (see the
  section above), not by hand-picking a side.

Verified failure, 2026-07-30: an entire session's work (pobreza into the ITVC,
two components leaving it, 10 broken ficha URLs, the ITCM validation anchor
swap) was reported commit by commit as "pushed" — all on a PR branch. `main`
had none of it and the site was byte-identical. The user had to point it out
twice. There was already a memory saying "verify production" and it pointed at
the retired GitHub Pages target, which is why it did not bite.

## When a GitHub Actions run fails

**Don't reflexively call it "transient, just `gh run rerun`."** Check first:

1. `gh run view <run-id>` for the failed job/annotation.
2. If the annotation is generic infra-sounding (e.g. "job was not acquired by
   Runner...", empty step list, failed before checkout even ran) — that's a
   platform issue, not a workflow bug. Confirm, don't assume: fetch
   `https://www.githubstatus.com/api/v2/incidents.json` and check for an
   active Actions/runner incident overlapping the run's timestamps.
3. If the failure has real step output (build error, test failure, missing
   secret) — that's ours to fix, retrying won't help.

Only retry (`gh run rerun <run-id>`) after confirming it's actually
infra-side. Verified 2026-07-09: a deploy failed with "job was not acquired
by Runner of type hosted"; githubstatus.com confirmed an active
"Delays starting Actions runs" incident (~96% of hosted-runner jobs failing
to start at peak) covering that exact window — rerun succeeded once the
incident cleared. Confirming this took two `gh api` calls and one fetch, a
lot cheaper than either (a) guessing wrong and missing a real bug, or
(b) leaving the user without an actual answer for "why did it fail."

## Informe de Coyuntura quick reference

Start in `projects/informe_coyuntura/`.

```powershell
python scripts/macro.py
python scripts/politica.py
python scripts/gestion.py
python scripts/vida_cotidiana/main.py
python scripts/espiritu_epoca.py
python scripts/generar_informe.py
python scripts/publicar.py       # writes web/src/data/{informe,series}.json
python scripts/bigquery_export.py  # espeja la corrida en BigQuery (ADR-0180)
```

Collector exit codes: `0` all fresh · `1` mixed fresh/cache · `2` all cache
(source failures).

Useful docs: `projects/informe_coyuntura/README.md`,
`docs/260523_proyecto_pais_estado_extraccion.md`, `docs/archivo/cinturon_*.md`
(diseño original, read-only), `docs/adr/README.md`.
