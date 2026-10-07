---
madr: 4
id: '0348'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'transversal'
archivos: ['scripts/archivo.py', 'web/src/pages/archivo/index.astro', 'web/src/components/Nav.astro', 'tests/test_archivo.py']
relacionado: ['0347']
ambito: 'Publicación · archivo navegable de los informes mensuales en /archivo/'
origen: 'Reunión del 6-oct-2026, punto 8: «las fotos anteriores quedan disponibles, cada mes con la suya». Juan, 7-oct: reconstruir los meses anteriores.'
---

# ADR-0348 — Archivo de informes mensuales

## Contexto y planteo del problema

ADR-0347 dejó `informe.cigob.org` como informe del mes, pero un mes publicado
sólo sobrevivía como etiqueta de git. La reunión del 6-oct pidió que cada mes
quede disponible para leerlo, y Juan pidió reconstruir los meses anteriores: hay
corridas nocturnas desde junio de 2026.

## Factores de decisión

- Que un mes viejo se lea **como era**, con su metodología, no los datos viejos
  dentro del código de hoy (la limitación declarada en ADR-0347).
- No multiplicar el build del sitio por cada mes.
- Que publicar un mes sume su archivo sin trabajo manual.

## Opciones consideradas

1. Una foto por mes: el informe entero en un solo archivo, armado con
   `web/tools/emitir-artifact.mjs` sobre el sitio de ese día.
2. Generar todas las páginas de cada mes dentro del sitio (`/archivo/AAAA-MM/…`).
3. Un deploy de Vercel por mes con su propia URL.

## Decisión

**Opción 1.**

- `scripts/archivo.py construir AAAA-MM` toma la última corrida del mes
  (`mensual.elegir`), construye el sitio de ESE commit con `PUBLIC_MURO=0` y lo
  empaqueta con el emisor de ese día o, si todavía no existía, con el de hoy.
  Si el código viejo no se deja empaquetar, cae a «código actual» (código de hoy
  con los datos de ese día) y la tarjeta lo dice.
- La foto va a `web/public/archivo/AAAA-MM/index.html` (sin muro ni GA: es un
  archivo autocontenido) y el resumen a `web/src/contenido/archivo.json`.
- `/archivo/` lista los meses, del más nuevo al más viejo, con la tensión
  general, el riesgo dominante y el estado de cada cinturón; «Archivo» entra al
  menú. GA4: `ver_archivo` y `abrir_mes_archivo` (`mes`).
- `.github/workflows/mensual.yml` arma el archivo del mes al publicarlo.
- Se reconstruyeron junio, julio, agosto y septiembre de 2026.

### Consecuencias

- Cada mes pesa unos 4 MB en el repo y en el deploy.
- La página `/archivo/` queda detrás del muro como el resto del sitio; las fotos
  no tienen muro propio (se puede llegar a ellas con el link directo).

### Confirmación

`tests/test_archivo.py`: toda tarjeta tiene su foto y viceversa, y ninguna foto
quedó con el muro o con GA.

## Pros y contras de las opciones

### Opción 1 — Foto en un archivo

- Bien: es la foto exacta, y reutiliza el emisor.
- Mal: 4 MB por mes.

### Opción 2 — Páginas por mes en el sitio

- Mal: el código lee un único snapshot en todos lados; habría que reescribirlo, y
  los meses viejos igual se leerían con la metodología de hoy.

### Opción 3 — Un deploy por mes

- Mal: una URL distinta por mes y nada que los liste.

## Más información

- ADR-0347: el informe mensual.
