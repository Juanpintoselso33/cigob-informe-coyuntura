---
madr: 4
id: '0283'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [recaudacion]
archivos: ['scripts/comarb.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts']
ambito: 'Actualización de la base imponible compuesta'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0283 — Recaudación actualiza las gacetillas COMARB

## Contexto y planteo del problema

La tarjeta y la serie utilizaban el store COMARB sin ejecutar su actualización.
La API nacional tenía agosto y el portal provincial enlazaba julio y agosto,
pero la combinación quedaba en junio. La descarga de ambas gacetillas mostró
sumas conciliadas entre los seis sistemas y el total.

## Decisión

Actualizar COMARB antes del cálculo de tarjeta e historia. Descargar únicamente
las gacetillas ausentes; conservar el mismo cálculo de estacionalidad y la misma
ventana. Rechazar errores HTTP, catálogos sin períodos reconocibles y nuevos
PDFs cuyo total no concilie dentro del 0,01% con los componentes. Una gacetilla
publicada sin validar impide presentar la corrida como una actualización válida.

## Más información

La ausencia de IPC agosto limita el mes común a julio, aunque ambas fuentes
tributarias ya publiquen agosto. Los factores estacionales se reestiman, por lo
que también cambian puntos históricos; no se cambia la metodología.
