# Monitor del Plan de Gobierno — Web (Astro)

App [Astro](https://astro.build/) que renderiza el observatorio público del Informe de
Coyuntura. Replica el estilo del observatorio de klipea (CSS propio de CIGOB) y se
alimenta de un snapshot de datos en JSON.

- **Publicado en:** https://informe.cigob.org
- **Stack:** Astro 4.16, sin framework de UI (componentes `.astro` puros)
- **Node:** 20 (el que usa el CI)

## Configuración relevante (`astro.config.mjs`)

| Opción | Valor | Por qué |
|---|---|---|
| `site` | `https://informe.cigob.org` | URL canónica del único sitio publicado |
| `base` | `/` | El sitio se sirve desde la raíz del dominio custom |
| `outDir` | `../../../web-dominio` | El build sale a la carpeta que el workflow sube como artefacto de Pages |

## Desarrollo local

```bash
cd projects/informe_coyuntura/web
npm install
npm run dev        # servidor de desarrollo con HMR
npm run build      # build de producción → ../../../web-dominio
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

Automático vía `.github/workflows/pages.yml` en cada push a `main`: corre un
solo `npm ci && npm run build`, sube `web-dominio/` con
`actions/upload-pages-artifact` y publica directamente desde este repo con
`actions/deploy-pages`. No usa `DEPLOY_TARGET` ni un repo externo de deploy.
