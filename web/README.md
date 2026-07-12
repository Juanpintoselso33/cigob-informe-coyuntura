# web/ — carpeta de trabajo del deploy (GitHub Pages)

El sitio público es el Informe de Coyuntura, servido en **https://informe.cigob.org**.
El workflow `.github/workflows/pages.yml` compila la app Astro
(`projects/informe_coyuntura/web/`) en `web-dominio/` (raíz del repo, ver
`astro.config.mjs`) y sube esa carpeta como artefacto de Pages en cada push
a `main`.

`web-dominio/` está en `.gitignore` — es un artefacto generado por el CI, no
se versiona. Esta carpeta (`web/`) quedó vacía de contenido publicado desde
que se consolidó a un único repo y un único target de deploy (antes había
una landing page acá + un repo separado para el dominio custom).
