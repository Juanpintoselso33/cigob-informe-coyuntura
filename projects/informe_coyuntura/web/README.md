# Monitor del Plan de Gobierno — Web (Astro)

App [Astro](https://astro.build/) que renderiza el observatorio público del Informe de
Coyuntura. Replica el estilo del observatorio de klipea (CSS propio de CIGOB) y se
alimenta de un snapshot de datos en JSON.

- **URL pública vigente:** ver el [README del proyecto](../README.md#web-pública)
- **Stack:** Astro 4.16, sin framework de UI (componentes `.astro` puros)
- **Node:** 20 (el que usa el CI)

## Configuración relevante (`astro.config.mjs`)

| Opción | Valor | Por qué |
|---|---|---|
| `site` | `https://informe.cigob.org` | URL canónica configurada en los metadatos y el sitemap |
| `base` | `/` | El sitio se sirve desde la raíz del dominio custom |
| `outDir` | `dist/` (default) | Vercel publica ese directorio según `vercel.json` en la raíz del repo |

## Desarrollo local

```bash
cd projects/informe_coyuntura/web
npm install
npm run dev        # servidor de desarrollo con HMR
npm run build      # build de producción → dist/
npm run preview    # previsualizar el build
```

> El CI usa `npm ci` (requiere `package-lock.json` versionado).

## Datos

La web NO ejecuta los colectores: consume un snapshot precalculado en `src/data/`:

| Archivo | Origen |
|---|---|
| `src/data/informe.json` | Informe completo (cinturones, indicadores, scores) |
| `src/data/series.json` | Series históricas agrupadas para los sparklines |

Ambos los regenera `.venv/bin/python scripts/publicar.py` (en la raíz del
proyecto) a partir de los outputs de los colectores. Ciclo completo de
actualización en el [`README` del proyecto](../README.md#web-pública).

## Estructura

```
web/
├── astro.config.mjs
├── src/
│   ├── pages/
│   │   ├── index.astro          # dashboard principal
│   │   └── [slug].astro         # página por cinturón
│   ├── components/              # Hero, CinturonCard, IndicadorTile, MiniChart, etc.
│   ├── layouts/Layout.astro
│   ├── lib/                     # datos.ts, descripciones.ts, sparkline.ts
│   └── data/                    # snapshot JSON (informe.json, series.json)
└── public/                      # CSS de CIGOB + logo
```

## Deploy

Automático vía la integración de GitHub de Vercel en cada push a `main`.
`vercel.json` instala y construye esta app desde la raíz del monorepo y publica
`projects/informe_coyuntura/web/dist`. GitHub Pages y `pages.yml` se retiraron;
no hay un workflow de deploy en este repo.
