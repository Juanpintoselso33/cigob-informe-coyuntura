---
madr: 4
id: '0295'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [jornadas_individuales_no_trabajadas_12m]
archivos: ['scripts/politica.py', 'web/src/lib/fichas.ts']
ambito: 'Integridad del acumulado anual de jornadas'
---

# ADR-0295 — Jornadas exige doce meses calendario

El colector sumaba doce filas ordenadas, sin verificar huecos ni duplicados.
Eso permitiría etiquetar un período distinto de un año como doce meses.

Se exige una secuencia mensual única y continua, con jornadas finitas no
negativas, antes de calcular cualquier acumulado. Se conservan eventuales
fracciones en vez de truncarlas. Un error conserva el comportamiento de
fallo del colector y no produce un nuevo dato aparente.

La planilla original vigente al 8 de septiembre termina en mayo de 2026.
La suma independiente de junio de 2025 a mayo de 2026 es 4.760.195; la
corrección no cambia el snapshot. El cuadro C1 y las filas utilizadas se
conservan en `../auditorias/2026-09-08/cotejo-jornadas-original.json`.

Pruebas: cruce de año, fracciones, hueco, duplicado, negativo, no finito y
booleano, además de las pruebas de selección del cuadro y columna originales.
