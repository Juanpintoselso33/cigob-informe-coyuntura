# Codex Context For This Repo

Read `CLAUDE.md` first — it is the canonical operating guide, and it IS
versioned in the repo (since 2026-07-31). This file is not: it stays local to
this machine, so anything that has to survive a fresh clone goes in
`CLAUDE.md`, not here. This file is the Codex-specific bridge
to that same context, kept lightweight: route work, then read the specific
source files needed for the task.

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
  verify it against the current repo docs before relying on details. It appears
  older than `projects/informe_coyuntura/README.md`: the current project has
  five cinturones and `informe.json` schema v1.1.0, while the Claude skill still
  describes four cinturones and schema v1.0.0.

## Repo Overview

This is a monorepo for CIGOB/UBA political analysis tools.

- `projects/informe_coyuntura/`: data collectors, scoring, report generation,
  versioned outputs, and an Astro web app for the Informe de Coyuntura.
- `web/`: public GitHub Pages site.
- `scripts/`: root utilities such as Markdown-to-DOCX export.
- `.github/workflows/`: daily data pipeline and GitHub Pages deployment.

Read the nearest `README.md` before changing a project. The root README is only
the entry point; project README files contain the operational details.

## Informe De Coyuntura

Start in `projects/informe_coyuntura/`.

Current collector commands:

```powershell
python scripts/macro.py
python scripts/politica.py
python scripts/gestion.py
python scripts/vida_cotidiana/main.py
python scripts/espiritu_epoca.py
```

Generate the report:

```powershell
python scripts/generar_informe.py
```

Publish data for the Astro web app:

```powershell
python scripts/publicar.py
```

Preview/build the web app:

```powershell
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

