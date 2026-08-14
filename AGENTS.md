# Codex Context For This Repo

Read `CLAUDE.md` first — it is the canonical operating guide, and it IS
versioned in the repo (since 2026-07-31). This file is versioned too (since
2026-08-05), and it is the Codex-specific bridge to that same context, kept
lightweight: route work, then read the specific source files needed for the
task. `CLAUDE.md` stays the source of truth: anything that has to survive a
fresh clone goes there, not here.

## Reuse Claude Context

- Claude/BMAD skills live under `.claude/skills/`.
- When a user invokes BMAD, a named workflow, or a task that clearly matches a
  skill, read the matching `.claude/skills/<skill>/SKILL.md` before acting.
- If that skill references relative `steps/`, `templates/`, `assets/`, or
  `references/`, resolve them relative to the skill folder and read only the
  files required for the current task.
- Do not bulk-load all of `.claude/skills`; there are many BMAD skills and most
  are irrelevant to a given turn.
- Treat `.claude/skills/informe-coyuntura.md` as useful operational context, but
  verify it against the current repo docs before relying on details. It was
  updated 2026-08-14 (**four** cinturones after ADR-0205, current paramétrica
  engines, current file layout), so it is not stale today — but it is a quick
  reference, not the source of truth, and it will drift again. When in doubt
  prefer `projects/informe_coyuntura/README.md`, `docs/adr/`, and the tests.

## Repo Overview

This is a monorepo for CIGOB/UBA political analysis tools.

- `projects/informe_coyuntura/`: data collectors, scoring, report generation,
  versioned outputs, and an Astro web app for the Informe de Coyuntura.
- `web/`: legacy static site. **Not the deploy target.**
- `scripts/`: root utilities such as Markdown-to-DOCX export.
- `.github/workflows/`: daily data pipeline (`data-pipeline.yml`). GitHub Pages
  was retired in July 2026 and `pages.yml` is gone. **The site deploys through
  Vercel, which builds every push to `main`** from the Astro app under
  `projects/informe_coyuntura/web/` (production alias:
  `https://cigob-informe-coyuntura.vercel.app/`). Per-deploy
  `…-<hash>.vercel.app` URLs sit behind a login wall — always check the
  production alias.

Read the nearest `README.md` before changing a project. The root README is only
the entry point; project README files contain the operational details.

## Informe De Coyuntura

Start in `projects/informe_coyuntura/`.

**Interpreter (Mac).** There is no bare `python` on this machine — Homebrew only
ships `python3`, empty. Use the project venv `.venv/bin/python` (uv, Python 3.12,
matching CI), or `source .venv/bin/activate` first. On the tower these same
commands run under PowerShell with a plain `python`.

**Espíritu de época left the tablero on 2026-08-14 (ADR-0205)**:
`scripts/espiritu_epoca.py` was deleted along with its pipeline step. Four
cinturones remain (macro / política / gestión / vida cotidiana), and `config.py`
weights four, not five.

Current collector commands:

```bash
.venv/bin/python scripts/macro.py
.venv/bin/python scripts/politica.py
.venv/bin/python scripts/gestion.py
.venv/bin/python scripts/vida_cotidiana/main.py
.venv/bin/python scripts/vida_cotidiana.py   # puente legacy, después de main.py
```

Generate the report:

```bash
.venv/bin/python scripts/generar_informe.py
```

Publish data for the Astro web app:

```bash
.venv/bin/python scripts/publicar.py
```

Preview/build the web app:

```bash
cd web
npm install
npm run build
npm run preview
```

Collector exit codes:

- `0`: all expected indicators are fresh.
- `1`: mixed fresh/cache data.
- `2`: all data came from cache after source failures.

Versioned outputs are intentional in this project, especially
`projects/informe_coyuntura/output/` and
`projects/informe_coyuntura/scripts/vida_cotidiana/data/`. Do not remove them as
"generated noise" unless the user explicitly asks.

Useful current docs:

- `projects/informe_coyuntura/README.md`
- `projects/informe_coyuntura/docs/260523_proyecto_pais_estado_extraccion.md`
- `projects/informe_coyuntura/docs/archivo/cinturon_*.md` (diseño original, read-only)
- `projects/informe_coyuntura/docs/arquitectura/README.md`
- `projects/informe_coyuntura/docs/adr/README.md`

## Working Rules

- Use Spanish for user-facing prose and documentation unless the surrounding
  file clearly uses English.
- Prefer current code and docs over stale AI-context files when they conflict.
- Never version secrets (`.env`, keys, credentials, service accounts).
- Do not treat `.claude/`, `_bmad/`, `_bmad-output/`, or this file as product
  source; they are assistant context.
- For live data, source availability, package behavior, or any "latest" claim,
  verify before answering because this repo depends on external data sources
  that can drift.
- Before editing, check `git status --short` and avoid overwriting unrelated
  local changes.
- Validate with the narrowest useful command: targeted Python script, unit test,
  `npm run build`, or workflow-equivalent command depending on the touched area.

