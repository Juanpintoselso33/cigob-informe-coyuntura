---
madr: 4
id: '0281'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [velocidad_resolucion]
archivos: ['web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts']
ambito: 'Interpretación de la tasa de resolución judicial'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0281 — Tasa de resolución no es duración judicial

## Contexto y planteo del problema

El cociente anual de casos resueltos sobre ingresados se llamaba velocidad.
El anuario CSJN distingue estos flujos de la duración de los casos. Un aumento
de ingresos puede reducir la tasa aunque cada expediente tarde lo mismo.

## Decisión

Usar el nombre público «Tasa de resolución de la Corte» y aclarar que no mide
duración ni sentido de las decisiones. Se conserva la clave interna histórica,
el valor, las bandas y el signo. La interpretación de menor fricción para el
Gobierno se declara como hipótesis del monitor, no hecho probado por el cociente.

## Más información

El [anuario oficial 2025](https://www.csjn.gov.ar/novedades/detalle/13002)
confirma 26.524 casos resueltos y 58.424 ingresados: 45,4%. Revisar la validez
del signo requiere otra decisión metodológica, registrada como mejora potencial.
