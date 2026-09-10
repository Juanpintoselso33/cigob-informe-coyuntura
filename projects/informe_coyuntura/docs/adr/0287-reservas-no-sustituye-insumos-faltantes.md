---
madr: 4
id: '0287'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [reservas_bcra]
archivos: ['scripts/macro.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts']
corrige: ['0005']
continua: ['0286']
ambito: 'Estimaciones completas de reservas y conservación de caché'
---

# ADR-0287 — Reservas no sustituye insumos faltantes

## Contexto y planteo del problema

El respaldo mezclaba brutas de la API con drenajes de un config y omitía el
tramo de vencimientos que incluye la fórmula principal. Lo publicaba fresco
si coincidía el mes. La historia sustituía depósitos del Tesoro faltantes
por cero, y el parser SDDS hacía lo mismo si no encontraba la columna del tramo.

## Decisión

Retirar esa ruta alternativa. Si falla SDDS o Tesoro del mes, devolver ausencia
al colector: este conserva el último resultado completo como desactualizado.
No cambiar los sumandos según qué fuente responda. El parser exige la columna
de vencimientos, y la historia solo publica meses con Tesoro observado.
Un cero explícito sigue siendo un dato válido.

Conservar la fórmula principal y sus bandas. Las claves heredadas continúan
por compatibilidad; sus comentarios ya no afirman identidad de instrumento.

## Más información

Las regresiones reproducen el respaldo con config del mismo mes, el Tesoro
ausente frente a cero y la columna SDDS ausente frente a cero. La elección
del tramo excluido sigue siendo un asunto metodológico pendiente de conciliación,
según ADR-0286. Esta corrección no lo da por validado.
