# Análisis CIGOB

Monorepo de herramientas de análisis político para Fundación CIGOB (contexto UBA).
Reúne colectores de datos, generadores de informe y tableros web estáticos.

## Proyectos

| Proyecto | Descripción | Path |
|---|---|---|
| **Informe de Coyuntura** | Colectores de datos + generador de informe periódico sobre cuatro cinturones (marco Matusiano) y web pública en Astro | [`projects/informe_coyuntura/`](projects/informe_coyuntura/) |
| **Votómetro Argentina 2027** | Proyector electoral (Monte Carlo + fundamentals) en HTML estático | [`projects/votometro/`](projects/votometro/) |

Cada proyecto tiene su propio `README.md` con instalación, ejecución y detalle técnico.

## Web pública (GitHub Pages)

El sitio se publica en **https://juanpintoselso33.github.io/biblitotecario-ai/** y se
arma desde `web/`:

| Archivo | Descripción |
|---|---|
| `web/index.html` | Landing — índice de herramientas de análisis |
| `web/bibliotecario.html` | Prototipo del Bibliotecario IA (RAG sobre corpus CIGOB) — **en desarrollo, aún no funcional**; la API key se ingresa en runtime, no se versiona |
| `web/votometro.html` | Espejo del Votómetro (fuente en `projects/votometro/`) |
| `web/informe/` | Build del informe (lo regenera CI desde la app Astro; gitignored) |

El deploy es automático vía GitHub Actions (`.github/workflows/pages.yml`) en cada push a `main`.

## Scripts de utilidad (raíz)

| Script | Uso |
|---|---|
| `scripts/actualizar_encuestas.py` | Agrega una encuesta al Votómetro (dual-write a `projects/votometro/web/encuestas.json` y al HTML) |
| `scripts/md_to_docx.py` | Convierte Markdown → Word con identidad visual CIGOB |

## Automatización

| Workflow | Qué hace |
|---|---|
| `.github/workflows/data-pipeline.yml` | Pipeline diario: corre los colectores, regenera el snapshot y dispara el deploy (00:00 ART) |
| `.github/workflows/pages.yml` | Build de la app Astro + publicación en GitHub Pages |

## Estructura del repo

```
.
├── README.md                  # este archivo
├── .github/workflows/         # CI: data-pipeline + pages
├── web/                       # sitio estático publicado en GitHub Pages
├── scripts/                   # utilidades de raíz (encuestas, md→docx)
├── projects/
│   ├── informe_coyuntura/     # colectores + informe + web Astro
│   └── votometro/             # proyector electoral HTML
└── docs/                      # documentos base de análisis (no todos versionados)
```

## Onboarding para colaboradores

1. Clonar el repo:
   ```bash
   git clone https://github.com/Juanpintoselso33/biblitotecario-ai.git
   cd biblitotecario-ai
   ```
2. Para trabajar sobre el **Informe de Coyuntura**, seguir su [`README`](projects/informe_coyuntura/) (Python + Astro).
3. Para el **Votómetro**, seguir su [`README`](projects/votometro/) (HTML estático, sin build).

> **Nota:** las configuraciones de asistentes de IA (`.claude/`, `CLAUDE.md`, `_bmad/`,
> `docs/superpowers/`) están en `.gitignore` y no forman parte del repo compartido.
> Las credenciales y API keys nunca se versionan: se cargan por variable de entorno
> o se ingresan en runtime.
