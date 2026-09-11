---
madr: 4
id: '0292'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [desregulacion_normativa]
archivos: ['scripts/gestion.py', 'web/src/lib/fichas.ts']
ambito: 'Revisiones de la serie oficial de desregulación'
---
# ADR-0292 — Desregulación incorpora las revisiones mensuales

Fecha: 2026-09-08. Estado: aceptada.

El informe de julio de 2026 publica 16.771 artículos acumulados. El de agosto
publica 17.115 y revisa julio a 16.848 en el gráfico de los últimos tres meses.
Restar los titulares de dos ediciones producía +344, mientras la versión
vigente informa +267. El nivel de agosto era correcto; la variación no.

El colector extrae las tres etiquetas impresas cuando puede verificar los
meses consecutivos, el orden y la igualdad del último valor con la portada.
La edición más reciente prevalece sobre los titulares anteriores. Se vuelve
a consultar la última edición disponible y se conserva URL y SHA-256.
Las ediciones previas conservan sus titulares originales como procedencia.
La tarjeta y el historial usan la misma serie revisada.

La reconstrucción geométrica anterior a mayo de 2026 se conserva como tal.
Este cambio no convierte el autorreporte del Ministerio en una medición de
impacto económico ni de implementación efectiva. La evidencia original se
conserva en `../auditorias/2026-09-08/cotejo-desregulacion-original.json`.

Validación: pruebas con la secuencia publicada, rechazo de períodos/totales
incompatibles y regresión del incremento mensual con julio revisado.
