import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Deploy: Vercel (proyecto con Root Directory = projects/informe_coyuntura/web),
// dominio custom informe.cigob.org. outDir default (dist/) — Vercel lo detecta solo.
export default defineConfig({
  site: 'https://informe.cigob.org',
  base: '/',
  build: { format: 'directory', assets: '_assets' },
  redirects: {
    '/metodologia/dolarizacion_depositos/': '/metodologia/presion_dolarizacion/',
  },
  integrations: [
    // public/robots.txt apunta a /sitemap-index.xml. Se excluye la URL vieja de
    // dolarizacion_depositos: es un redirect, y un sitemap no debe listar URLs
    // que redirigen — Search Console las reporta como error de indexación.
    //
    // @astrojs/sitemap esta CLAVADA en 3.2.1 (sin ^) a proposito: de la 3.4 en
    // adelante lee la API de rutas de Astro 5 y con Astro 4.16 el build muere
    // con "Cannot read properties of undefined (reading 'reduce')". Al subir
    // Astro a 5 se puede volver a un rango normal.
    sitemap({
      filter: (page) => !page.includes('/metodologia/dolarizacion_depositos/'),
    }),
  ],
});
