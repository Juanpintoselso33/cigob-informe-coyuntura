import { defineConfig } from 'astro/config';

// Dos targets de deploy del mismo sitio:
//  - default: GitHub Pages del monorepo (juanpintoselso33.github.io/biblitotecario-ai/informe/)
//  - DEPLOY_TARGET=dominio: informe.cigob.org (raíz del repo dedicado cigob-informe,
//    publicado por el paso "Publicar al repo del dominio" de los workflows)
const dominio = process.env.DEPLOY_TARGET === 'dominio';

export default defineConfig({
  site: dominio ? 'https://informe.cigob.org' : 'https://juanpintoselso33.github.io',
  base: dominio ? '/' : '/biblitotecario-ai/informe',
  outDir: dominio ? '../../../web-dominio' : '../../../web/informe',
  build: { format: 'directory', assets: '_assets' },
});
