import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Deploy: Vercel (proyecto con Root Directory = projects/informe_coyuntura/web),
// dominio custom informe.cigob.org. outDir default (dist/) — Vercel lo detecta solo.
export default defineConfig({
  site: 'https://informe.cigob.org',
  base: '/',
  build: { format: 'directory', assets: '_assets' },
  redirects: {
    // Apuntan DIRECTO a la ficha vigente y no en cadena: cada salto extra es un
    // redirect que Search Console cuenta aparte.
    '/metodologia/dolarizacion_depositos/': '/metodologia/desequilibrio_monetario/',
    '/metodologia/presion_dolarizacion/': '/metodologia/desequilibrio_monetario/',
  },
  integrations: [
    // public/robots.txt apunta a /sitemap-index.xml. Se excluyen las URLs viejas
    // de dolarizacion_depositos y presion_dolarizacion: son redirects, y un
    // sitemap no debe listar URLs que redirigen — Search Console las reporta
    // como error de indexación.
    //
    // @astrojs/sitemap esta CLAVADA en 3.2.1 (sin ^) a proposito: de la 3.4 en
    // adelante lee la API de rutas de Astro 5 y con Astro 4.16 el build muere
    // con "Cannot read properties of undefined (reading 'reduce')". Al subir
    // Astro a 5 se puede volver a un rango normal.
    sitemap({
      filter: (page) => ![
        '/metodologia/dolarizacion_depositos/',
        '/metodologia/presion_dolarizacion/',
      ].some((vieja) => page.includes(vieja)),
    }),
  ],
});
