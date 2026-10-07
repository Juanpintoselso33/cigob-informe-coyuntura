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

- Que los meses se lean **con la misma vara**: el Monitor de hoy (metodología y
  diseño) sobre los datos de cada mes, para poder compararlos (Juan, 7-oct).
- No multiplicar el build del sitio por cada mes.
- Que publicar un mes sume su archivo sin trabajo manual.

## Opciones consideradas

1. Una foto por mes: el informe entero en un solo archivo, armado con
   `web/tools/emitir-artifact.mjs` sobre el sitio de ese día.
2. Generar todas las páginas de cada mes dentro del sitio (`/archivo/AAAA-MM/…`).
3. Un deploy de Vercel por mes con su propia URL.

## Decisión

**Opción 1, reconstruyendo cada mes con el Monitor de hoy.** Una primera
versión archivó el sitio tal como era cada mes; Juan la corrigió el mismo día:
el archivo tiene que mostrar los meses como los muestra hoy el Monitor.

- `scripts/archivo.py construir AAAA-MM` toma la última corrida del mes
  (`mensual.elegir`), copia el código de HOY, le pone sólo los datos crudos de
  esa corrida (`output/`, `scripts/vida_cotidiana/data/`, `data/historico/`) y
  corre `generar_informe.py` y `publicar.py` de hoy con el reloj de Python fijado
  en el instante de la corrida (el mes, la fecha y la antigüedad de cada dato
  salen de `datetime.now()`). Después construye el sitio sin muro y lo empaqueta
  con `web/tools/emitir-artifact.mjs`.
- La foto va a `web/public/archivo/AAAA-MM/index.html` (sin muro ni GA) y el
  resumen a `web/src/contenido/archivo.json`.
- `/archivo/` lista los meses, del más nuevo al más viejo, con la tensión
  general, el riesgo dominante y el estado de cada cinturón; «Archivo» entra al
  menú. GA4: `ver_archivo` y `abrir_mes_archivo` (`mes`).
- `.github/workflows/mensual.yml` arma el archivo del mes al publicarlo.
- Se reconstruyeron junio, julio, agosto y septiembre de 2026.

Control: septiembre reconstruido da política 2,7 e impacto social 6,3; con el
método de entonces había dado 3,0 y 6,5. Es el mismo corrimiento que ADR-0344 y
ADR-0345 produjeron sobre los datos de octubre (2,9 → 2,7 y 6,5 → 6,3).

### Consecuencias

- Cada mes pesa unos 4 MB en el repo y en el deploy.
- Un mes viejo puede no tener datos de indicadores que entraron después: se
  muestran sin dato, como en cualquier corrida con una fuente faltante.
- Los números de un mes archivado pueden diferir de los que se publicaron ese
  mes: el archivo aplica la metodología vigente.
- La página `/archivo/` queda detrás del muro como el resto del sitio; las fotos
  no tienen muro propio (se puede llegar a ellas con el link directo).

### Confirmación

`tests/test_archivo.py`: toda tarjeta tiene su foto y viceversa, y ninguna foto
quedó con el muro o con GA.

## Pros y contras de las opciones

### Opción 1 — Foto en un archivo

- Bien: todos los meses con la misma vara, y reutiliza el emisor.
- Mal: 4 MB por mes.

### Opción 2 — Páginas por mes en el sitio

- Mal: el código lee un único snapshot en todos lados; habría que reescribirlo.

### Opción 3 — Un deploy por mes

- Mal: una URL distinta por mes y nada que los liste.

## Más información

- ADR-0347: el informe mensual.
