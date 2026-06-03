# web/ — Carpeta de publicación (GitHub Pages)

Esta carpeta es **la raíz del sitio público**. El workflow
`.github/workflows/pages.yml` la sube tal cual a GitHub Pages en cada push a `main`.

- **URL:** https://juanpintoselso33.github.io/biblitotecario-ai/

## Contenido

| Archivo / carpeta | Qué es | Versionado |
|---|---|---|
| `index.html` | Landing — índice de herramientas de análisis (linkea a las tres de abajo) | ✅ sí |
| `bibliotecario.html` | Prototipo del **Bibliotecario IA** (RAG sobre corpus CIGOB) | ✅ sí |
| `votometro.html` | Votómetro publicado | ❌ no — lo copia el CI desde `projects/votometro/web/votometro.html` en cada deploy |
| `informe/` | Build de la app Astro del Informe de Coyuntura | ❌ no — lo regenera el CI (`outDir`) |

> Los artefactos generados (`votometro.html`, `informe/`) están en `.gitignore`: se
> producen en el deploy, no se versionan, para evitar duplicados que se desincronicen.

## ⚠️ Estado del Bibliotecario IA

`bibliotecario.html` es un **prototipo en desarrollo — todavía no está funcional**.
La API key de Anthropic se ingresa en runtime y se guarda en `localStorage` del
navegador (no se versiona ninguna credencial). Ver el estado del proyecto en la nota
de viabilidad técnica antes de retomarlo.

## Cómo se arma el sitio (deploy)

`pages.yml` hace, en orden:

1. `npm ci && npm run build` en `projects/informe_coyuntura/web` → genera `web/informe/`.
2. Copia `projects/votometro/web/votometro.html` → `web/votometro.html`.
3. Sube toda la carpeta `web/` como artefacto de Pages.

Por eso al clonar verás `index.html`, `bibliotecario.html` y este README, pero **no**
`votometro.html` ni `informe/`: aparecen solo en el sitio publicado.
