---
madr: 4
id: '0288'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [costo_financiamiento_tesoro]
archivos: ['scripts/macro.py', 'scripts/descargar_series.py', 'scripts/colocaciones_complementarias.py', 'web/src/lib/fichas.ts']
complementa: ['0258']
ambito: 'Vigencia del costo de financiamiento'
---

# ADR-0288 — Financiamiento completa meses con gacetillas

## Contexto y planteo del problema

La planilla anual llega a julio, pero agosto ya tiene resultados oficiales.
El colector no los incorporaba. La caché de planillas tampoco distinguía una
consulta de dos años de una posterior de cuatro, recortando el backfill.

## Decisión

Completar meses cerrados posteriores a la planilla con gacetillas oficiales.
El registro de fuentes exige cobertura mensual revisada, fechas confirmadas
en los llamados y número de instrumentos esperado. No contiene tasas ni montos
cargados a mano: se extraen de la tabla fija en pesos de cada resultado.
Una falla aborta el complemento entero. No se publica una muestra como mes completo.

Ponderar TIREA publicada por valor efectivo y deflactar con REM del mismo mes.
No incluir CER, dólar linked ni dólares. La planilla anual mantiene prioridad
cuando incorpora ese mes: puede revisar tasas reconstruidas, montos y cobertura;
no se agregan ambos universos. El inventario conserva URL y método de la tasa.
La caché se separa por ventana de años solicitada.

## Más información

Agosto comprende cuatro colocaciones fijas liquidadas los días 14 y 31.
La conversión del 18 de agosto recibió instrumentos dólar linked, fuera del
universo. El registro requiere mantenimiento cuando se verifica otro mes;
no afirma descubrir automáticamente todas las futuras licitaciones.

La cobertura y las fuentes están en
`docs/auditorias/2026-09-08/financiamiento-agosto-pendiente.md`.
