import { defineConfig } from 'astro/config';

// Un solo target de deploy: informe.cigob.org, servido directo desde este
// mismo repo (Pages con dominio custom) — sin repo de deploy separado.
export default defineConfig({
  site: 'https://informe.cigob.org',
  base: '/',
  outDir: '../../../web-dominio',
  build: { format: 'directory', assets: '_assets' },
});
