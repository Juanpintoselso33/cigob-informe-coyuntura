# Informe de Coyuntura — Web (Astro)

App [Astro](https://astro.build/) que renderiza el observatorio público del Informe de
Coyuntura. Replica el estilo del observatorio de klipea (CSS propio de CIGOB) y se
alimenta de un snapshot de datos en JSON.

- **Publicado en:** https://juanpintoselso33.github.io/biblitotecario-ai/informe/
- **Stack:** Astro 4.16, sin framework de UI (componentes `.astro` puros)
- **Node:** 20 (el que usa el CI)

## Configuración relevante (`astro.config.mjs`)

| Opción | Valor | Por qué |
|---|---|---|
| `base` | `/biblitotecario-ai/informe` | Sub-path bajo el dominio de GitHub Pages |
| `outDir` | `../../../web/informe` | El build sale a la carpeta de deploy (`web/` en la raíz del repo) |

## Desarrollo local

```bash
cd projects/informe_coyuntura/web
npm install
npm run dev        # servidor de desarrollo con HMR
npm run build      # build de producción → ../../../web/informe
npm run preview    # previsualizar el build
```

> El CI usa `npm ci` (requiere `package-lock.json` versionado).

## Datos

La web NO ejecuta los colectores: consume un snapshot precalculado en `src/data/`:

| Archivo | Origen |
|---|---|
| `src/data/informe.json` | Informe completo (cinturones, indicadores, scores) |
| `src/data/series.json` | Series históricas agrupadas para los sparklines |

Ambos los regenera `python scripts/publicar.py` (en la raíz del proyecto) a partir de
los outputs de los colectores. Ciclo completo de actualización en el
[`README` del proyecto](../README.md#web-pública).

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

Automático vía `.github/workflows/pages.yml` en cada push a `main`: corre
`npm ci && npm run build` y publica toda la carpeta `web/` (raíz) en GitHub Pages.
