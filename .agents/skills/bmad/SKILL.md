---
name: bmad
description: Use when the user invokes BMAD, names a bmad-* workflow or agent, or asks for BMAD planning, PRD, architecture, stories, implementation, review, research, UX, sprint, or documentation workflows in this repository.
---

# BMAD Router

Codex usa una sola entrada de descubrimiento y carga el workflow BMAD solicitado
desde su fuente versionada. No copies ni cargues las 44 skills a la vez.

## Selección

1. Normaliza el workflow a un nombre seguro `bmad-<slug>` compuesto sólo por
   minúsculas, números y guiones.
2. Resuelve `.claude/skills/<workflow>/SKILL.md` desde la raíz del repositorio.
3. Si el usuario dijo “BMAD” sin workflow claro, lista nombres de carpetas bajo
   `.claude/skills/bmad-*` y elige por descripción; pregunta sólo si dos rutas
   producirían entregables materialmente distintos.
4. Lee el `SKILL.md` elegido completo antes de actuar.

## Recursos

Cuando el workflow enlace `steps/`, `templates/`, `assets/` o `references/`,
resuélvelos contra la carpeta del workflow y lee únicamente los que indique el
paso actual. Los paths bajo `_bmad/` y `_bmad-output/` se resuelven desde la raíz
del repositorio.

## Adaptación Codex

- `AGENTS.md` es el punto de entrada; abre `CLAUDE.md` sólo cuando el workflow
  necesite detalle que no está en el bridge o en la documentación del proyecto.
- Conserva idioma, ubicación de outputs y gates definidos por `_bmad/bmm/config.yaml`.
- No inventes agentes, herramientas o comandos de otro harness. Ejecuta el paso
  inline o usa capacidades Codex equivalentes dentro de las reglas de delegación.
- Los workflows deprecados redirigen al workflow vigente indicado por su propia
  fuente; no los clones como skills nuevas.

Para contexto rápido del Informe de Coyuntura puede leerse
`.claude/skills/informe-coyuntura.md`, pero código, README, ADR y tests actuales
tienen precedencia.
