---
madr: 4
id: '0291'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'vida'
indicadores: [alquiler_real]
archivos: ['scripts/vida_cotidiana/collectors/ipc_alquiler.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts']
ambito: 'Fuente de alquiler GBA'
---

# ADR-0291 — Alquiler usa la planilla original

## Contexto y planteo del problema

La API utilizada para alquiler GBA discrepa de la serie original del INDEC:
julio de 2026 arroja 1,475% mensual frente a 3,9242%. Ambas tienen base 100
en diciembre de 2016 y el cociente histórico no es constante. El nivel
general GBA coincide. No se puede resolver cambiando una base o un solo mes.

## Decisión

Usar la hoja de niveles de aperturas del libro original para alquiler y nivel
general de GBA. Compartir el lector entre tarjeta e historia, identificar
región y concepto exactos, exigir meses consecutivos y niveles positivos
finitos. Interpretar las fechas Excel por mes calendario: algunas cabeceras
incluyen otro día del mes. Un fallo no autoriza volver a la API discrepante.

Reconstruir la variación mensual y el componente relativo desde toda la serie
original, manteniendo el promedio de 4T-2023 y los pesos vigentes. El cambio
revisa el ITCIS histórico y sus contrastes; no es una mejora económica del mes.

## Más información

La ficha corrige que sólo existe alquiler GBA: el original contiene otras
regiones. Cambiar la cobertura geográfica requeriría una decisión metodológica
separada. Evidencia: `docs/auditorias/2026-09-08/cotejo-alquiler-discrepancia.json`.
