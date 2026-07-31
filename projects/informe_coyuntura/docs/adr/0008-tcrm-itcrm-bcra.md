---
madr: 4
id: '0008'
estado: 'aceptado'
fecha: 2026-06-27
cinturon: 'macro'
archivos: ['scripts/macro.py', 'scripts/descargar_series.py', 'requirements.txt', 'datos.ts']
ambito: '`scripts/macro.py` · `scripts/descargar_series.py` · `requirements.txt` · `datos.ts`'
---

# ADR-0008 — El TCRM usa el ITCRM oficial del BCRA, no la serie discontinuada de INDEC

## Contexto y planteo del problema

El tipo de cambio real multilateral (`tcrm`) es un indicador de **contexto** del
cinturón macro (no puntúa en el ITCM). Se tomaba de la serie de INDEC en
datos.gob.ar `116.3_TCRMA_0_M_36` (base 2010=100).

Al auditar la frescura de los datos se detectó que esa serie **está discontinuada:
su último punto es diciembre de 2024** (verificado contra la API: dic-24 = 79,8;
no hay puntos posteriores). El indicador mostraba un valor de 18 meses de
antigüedad marcado, además, como actualizado — contradiciendo la regla de datos
frescos ([[0001-datos-calculados-no-hardcodeados]]).

## Opciones consideradas

- **Mantener la serie de INDEC.** Rechazada: discontinuada, dato congelado en
  dic-2024.
- **Buscar otra serie en datos.gob.ar.** Rechazada: la búsqueda no devolvió una
  serie de TCRM vigente; INDEC dejó de publicarla.
- **ITCRM del BCRA vía API de Monetarias v4.0.** No disponible: la API solo expone
  tipos de cambio nominales (minorista, mayorista, valuación contable), no el ITCRM.
- **Planilla `ITCRMSerie.xlsx` del BCRA.** Elegida: es la fuente oficial y vigente
  del ITCRM, accesible y automatizable.

## Decisión

Usar el **ITCRM oficial del BCRA** (Índice de Tipo de Cambio Real Multilateral),
que el BCRA mantiene vigente y publica a diario, **de ahora en adelante**.

- Fuente: planilla `ITCRMSerie.xlsx` del BCRA, hoja *"ITCRM y bilaterales prom.
  mens."* (promedios mensuales), columna ITCRM. Base **17-dic-2015=100**.
- `macro.fetch_itcrm_serie()` parsea la planilla (con `openpyxl`) y devuelve la
  serie mensual; `fetch_tcrm()` toma el último mes para el indicador y
  `descargar_series.fetch_tcrm_serie()` arma la serie del gráfico (últimos 18m).
- La serie INDEC discontinuada queda como **fallback** explícito en `fetch_tcrm`,
  marcado `desactualizado=True` (nunca debería usarse salvo caída del BCRA).
- Cambia la base del índice (2010=100 → dic-2015=100). Es **cosmético**: el TCRM
  es contexto, no tiene bandas ni puntúa, así que el cambio de base no afecta
  ningún score. La unidad mostrada se actualizó a "Índice (base dic-2015=100)".

### Consecuencias

- `tcrm` vuelve a ser fresco (mismo vintage mensual que IPC/reservas/REM).
- Nueva dependencia `openpyxl` (lectura de `.xlsx`) en `requirements.txt`; el CI la
  instala. La planilla pesa ~3,5 MB: se descarga una vez por corrida en
  `macro.py` y otra en `descargar_series.py`.
- Si el BCRA cambia la URL o el nombre de la hoja, `fetch_tcrm` cae al fallback
  INDEC (marcado desactualizado) en vez de romper el pipeline.
