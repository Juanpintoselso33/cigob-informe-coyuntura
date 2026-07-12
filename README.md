# Análisis CIGOB

Monorepo de herramientas de análisis político para Fundación CIGOB (contexto UBA).
Reúne colectores de datos, generadores de informe y tableros web estáticos.

## Proyectos

| Proyecto | Descripción | Path |
|---|---|---|
| **Informe de Coyuntura** | Colectores de datos + generador de informe periódico sobre cuatro cinturones (marco Matusiano) y web pública en Astro | [`projects/informe_coyuntura/`](projects/informe_coyuntura/) |

Cada proyecto tiene su propio `README.md` con instalación, ejecución y detalle técnico.

## Web pública (GitHub Pages)

El sitio se publica en **https://informe.cigob.org** (dominio custom, único
target de deploy — un solo repo, un solo sitio). El workflow
`.github/workflows/pages.yml` compila la app Astro y sube `web-dominio/`
(build generado por CI, gitignored) como artefacto de Pages en cada push a
`main`. Ver `web/README.md` para el detalle.

## Scripts de utilidad (raíz)

| Script | Uso |
|---|---|
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
├── web/                       # carpeta de trabajo del deploy (ver web/README.md)
├── scripts/                   # utilidades de raíz (md→docx)
└── projects/
    └── informe_coyuntura/     # colectores + informe + web Astro (docs propios en projects/informe_coyuntura/docs/)
```

## Onboarding para colaboradores

1. Clonar el repo:
   ```bash
   git clone https://github.com/Fundacion-CIGOB/cigob-informe-coyuntura.git
   cd cigob-informe-coyuntura
   ```
2. Para trabajar sobre el **Informe de Coyuntura**, seguir su [`README`](projects/informe_coyuntura/) (Python + Astro).

### Colaboradores no técnicos

Si no vas a programar y solo querés poder preguntarle a una IA cómo funciona
el proyecto, no hace falta clonar nada — seguí la
[guía de onboarding no técnico](docs/onboarding_colaboradores.md).

## Qué se versiona y qué no

El repo versiona **todo el contenido real** (código, docs, datos y outputs generados),
para que un colaborador clone y trabaje sin depender de correr los colectores. El
`.gitignore` solo excluye tres cosas:

| No se versiona | Qué incluye | Por qué |
|---|---|---|
| 🔒 **Secretos** | `.env`, `*.key`, `*.pem`, `credentials*` | Seguridad — nunca |
| ♻️ **Regenerable** | `node_modules/`, `__pycache__/`, `web-dominio/` | Se reconstruyen desde el código/source versionado (`npm install`, `pip install`, build de CI) |
| 🤖 **Contexto de IA** | `.claude/`, `CLAUDE.md`, `_bmad/`, `docs/superpowers/`, etc. | Configuración de asistentes, no es del proyecto |

> Los datos y outputs del informe (`output/`, `scripts/vida_cotidiana/data/`) **sí** se
> versionan. Las API keys nunca: se cargan por variable de entorno o se ingresan en runtime.
