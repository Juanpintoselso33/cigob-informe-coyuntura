---
madr: 4
id: '0282'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [apertura_comercial]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
ambito: 'Vigencia y alcance de la alícuota efectiva'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0282 — Apertura usa el ICA original y explicita estadística

## Contexto y planteo del problema

La API tributaria contiene agosto, pero las series de comercio exterior de la
API terminan en junio. El cuadro original ICA contiene julio. La tarjeta y su
historia quedaban rezagadas pese a existir los insumos necesarios. Además, la
serie tributaria de importación incluye la tasa de estadística.

## Decisión

Usar el mecanismo de descubrimiento y conservación del ICA original establecido
en ADR-0275 y una función compartida para tarjeta e historia. Mantener el último
mes común con derechos y A3500. Si falla el catálogo, conservar el cuadro
validado y declarar su condición de caché. No alterar bandas ni universo
tributario: explicitar la tasa de estadística ya incluida.

La recaudación relativa es un indicador de carga efectiva, no una medida directa
de restricciones legales. Corregir la equivalencia automática entre cero y libre
comercio, o quince por ciento y cierre: las anclas son decisiones del monitor.

## Más información

La consulta real del 8 de septiembre reproduce 7,62% en julio tanto en tarjeta
como en historia, frente a 6,18% en junio. La planilla ARCA permite reconciliar
la serie importadora como derechos más tasa de estadística: julio
466.938,064 + 108.728,933 = 575.666,997 millones de pesos.
