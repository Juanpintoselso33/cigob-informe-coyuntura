import { defineConfig } from 'astro/config';

// Deploy: Vercel (proyecto con Root Directory = projects/informe_coyuntura/web),
// dominio custom informe.cigob.org. outDir default (dist/) — Vercel lo detecta solo.
export default defineConfig({
  site: 'https://informe.cigob.org',
  base: '/',
  build: { format: 'directory', assets: '_assets' },
  redirects: {
    '/metodologia/dolarizacion_depositos/': '/metodologia/presion_dolarizacion/',
  },
});
