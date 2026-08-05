# Task 8 report — ADR-0036: paramétrica ITCP del cinturón política

## Status: DONE

Note: this file previously held a report for an earlier "Task 8" (main() wiring) from
a prior version of the plan's task numbering. That work is already committed
(`7bcfe4c`) and superseded by this task. This report replaces it per the current
brief's instruction to write to this exact path.

## What was done

Created `docs/adr/0036-itcp-parametrica-politica.md` documenting the ITCP paramétrica
for the cinturón política, mirroring the established ADR format (table
Estado/Fecha/Ámbito/Precedente directo, then Contexto/Decisión/Opciones
descartadas/Consecuencias — same structure as ADR-0013 and ADR-0037).

Sources used:
- `docs/superpowers/specs/2026-07-07-itcp-cinturon-politica-design.md` (approved design
  spec, primary content source).
- `docs/adr/0013-itcg-parametrica-gestion.md` (format convention).
- `docs/adr/0037-cohesion-bloque-scraping-bloqueado-antibot.md` (tone/register
  calibration, same-day sibling ADR).
- `docs/adr/0017-protestas-acled.md` (context on `protestas_caba`'s origin in gestión).
- Real committed code for accuracy rather than inventing numbers:
  `scripts/itcp.py` (real band thresholds, `DIMENSIONES_ITCP`, docstring explaining the
  `protestas_caba` cross-fix), `tests/test_itcp.py`, `scripts/politica.py` (wiring),
  `data/politica/manuales.json` (`_meta.pendiente_automatizacion.gobernadores_alineamiento`
  with the 4 discarded proxies), `output/cache/politica.json` (live ITCP run: valor
  64.7, banda "moderadamente_aflojado", tensión 3.5, per-dimension puntajes), and
  `git log --oneline` to confirm Tasks 1-7 were already committed (commits `c965d39`
  through `11bd7d6`).

## Content coverage (per brief)

- Contexto: promedio simple → 5 dimensiones de Matus ya descriptas en
  `docs/cinturon_politica.md`, nunca pesadas.
- Decisión: pesos 30/25/20/15/10, sin doc CIGOB de respaldo — decisión editorial
  explícita ("capacidad de gobernar, NO popularidad").
- `cohesion_bloque` redefinido de "% alineado con posición oficial" (no calculable) a
  índice de Rice.
- 3 indicadores nuevos con su alcance honesto: `cohesion_bloque_senado`
  (complementario), `adhesion_reformas_provincial` (adhesión fiscal puntual al RIGI, no
  proxy de `gobernadores_alineamiento`), `protestas_caba` (reutilizado de gestión —
  ADR-0017 — con lectura distinta: en política SÍ puntúa, condición de gobernabilidad
  no juicio de legitimidad).
- Bandas provisionales: las 4 nuevas/recalibradas, marcadas explícitamente a recalibrar.
- Opciones descartadas: (a) compactar `poder_legislativo` en compuesto — sin doc que lo
  exija, se mantiene plano; (b) Senado/Presupuesto Abierto como proxy directo de
  `gobernadores_alineamiento` — construct-invalid, ya descartado en
  `manuales.json._meta.pendiente_automatizacion`.
- Bonus (per task instructions): cita cifras reales de la corrida en vivo (ITCP 64,7,
  tensión 3,5, ruptura por dimensión — poder legislativo 36,8 como cuello de botella
  real) y el hallazgo real de un bug corregido durante la integración (banda de
  `protestas_caba` copiada erróneamente de `movilizacion_cepa` asumiendo escala 0-100,
  corregida para puntuar sobre `var_vs_2023`).

## Self-review

Called the `advisor` tool before committing. It confirmed full content coverage against
the brief and correct format/tone, and flagged two small issues, both fixed before
commit:
1. A stray trailing `|` in the Rice index formula (formatting typo).
2. A date inconsistency ("06-jul" vs. "07-jul" for the same live run citing 301 ACLED
   events) — corrected to 07-jul, consistent with the commit date and
   `output/cache/politica.json`'s `generated_at`.

The advisor also confirmed the 4.6/10 → 64.7 "salto" framing (sourced from the design
spec, since the actual pre-ITCP score wasn't recoverable from git history at the
relevant commits — `git show <old-commit>:output/cache/politica.json` returned empty,
the file didn't exist at that path yet) reads correctly as old-score → new-index, not a
tension-value comparison, and is consistent with how ADR-0013 frames its own analogous
jump — left as-is.

## Commit

`4d518b7` — `docs(adr): ADR-0036 — paramétrica ITCP del cinturón política`
1 file changed, 170 insertions(+): `docs/adr/0036-itcp-parametrica-politica.md` only.
Staged explicitly by path (`git add docs/adr/0036-itcp-parametrica-politica.md`), never
`-A` or `.` — verified via `git status --short` before committing that no other
modified/untracked files (pre-existing, unrelated to this task, some likely from
concurrent parallel-task agents on the same branch) were staged alongside it.

Branch: `feature/itcp-cohesion-bloque-politica`.
