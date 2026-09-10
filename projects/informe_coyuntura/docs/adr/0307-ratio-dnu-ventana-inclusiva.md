---
madr: 4
id: '0307'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts']
corrige: ['0058', '0241', '0263']
---

# ADR-0307 — Ratio DNU: 365 fechas incluidas

## Contexto y planteo del problema

InfoLeg incluye los extremos del rango: una consulta de leyes del 21-oct-2025
al mismo 21-oct-2025 devuelve las leyes 27795 y 27796. Restar 365 días a la
fecha final e incluir ambas fechas seleccionaba 366 días aunque la tarjeta
declaraba 365. La historia repetía el error.

## Decisión

La fecha inicial se calcula como final menos 364 días. Tarjeta e historia
usan la misma función. Los períodos y cohortes de otros indicadores se
auditan separadamente; no se cambia de forma indiscriminada su calendario.
Se conserva el fixture original de agosto, aclarando que su intervalo
incluía 366 fechas. No se altera retrospectivamente la descarga de evidencia.

La ficha deja de garantizar un rezago fijo y detección automática de todos
los errores de tipificación. El cotejo sin filtro textual encontró el rótulo
«Decreto DNU 44/2026» en InfoLeg, pero el original del BO lo identifica como
DECTO-2026-44-APN-PTE e invoca el artículo 99 inciso 1 y el Código Aduanero.
No se transforma esa discrepancia de catalogación en un DNU adicional.

## Más información

Las anclas y los pesos se conservan. Las pruebas comprueban la cantidad de
fechas incluidas, los bordes y los años bisiestos. La reconstrucción nominal
por meses y sus resultados se documentan en la auditoría del 8-sep-2026.
El control de inventarios no certifica efectos políticos ni validez jurídica
de cada norma; publicar un DNU no equivale a sostenerlo ni ejecutarlo.
