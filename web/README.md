# web/ — Carpeta de publicación (GitHub Pages)

Esta carpeta es **la raíz del sitio público**. El workflow
`.github/workflows/pages.yml` la sube tal cual a GitHub Pages en cada push a `main`.

- **URL:** https://juanpintoselso33.github.io/biblitotecario-ai/

## Contenido

| Archivo / carpeta | Qué es | Versionado |
|---|---|---|
| `index.html` | Landing — índice de herramientas de análisis | ✅ sí |
| `informe/` | Build de la app Astro del Informe de Coyuntura | ❌ no — lo regenera el CI (`outDir`) |

> El artefacto generado (`informe/`) está en `.gitignore`: se produce en el
> deploy, no se versiona, para evitar duplicados que se desincronicen.

## Cómo se arma el sitio (deploy)

`pages.yml` hace, en orden:

1. `npm ci && npm run build` en `projects/informe_coyuntura/web` → genera `web/informe/`.
2. Sube toda la carpeta `web/` como artefacto de Pages.

Por eso al clonar verás `index.html` y este README, pero **no** `informe/`:
aparece solo en el sitio publicado.
