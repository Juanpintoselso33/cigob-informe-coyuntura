---
madr: 4
id: '0433'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [movilizacion_cepa]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'tests/test_cepa_promedio_mensual.py']
relacionado: ['0052']
ambito: 'Seguimiento interno de `movilizacion_cepa` (fuera del índice y del tablero)'
origen: 'Juan, 16-nov-2026, ante el informe 893 de CEPA: «1 ¿no? Es hasta mejor».'
---

# ADR-0433 — Movilización (CEPA) pasa a medir el promedio mensual de casos

## Contexto y planteo del problema

`movilizacion_cepa` medía los conflictos laborales acumulados desde el inicio del año, sobre
un máximo de referencia de 200. Está fuera del índice y del tablero desde [[0052]], entre
otras razones porque ese acumulado crece con el calendario y se reinicia en enero. El informe
893 del Centro de Economía Política Argentina (12-nov-2026) dejó de publicarlo. Ahora trae
953 casos acumulados desde enero de 2024 y promedios mensuales por tramo: «Entre enero de 2024
y octubre de 2025 hubo en promedio 25 casos por mes. Entre noviembre de 2025 y octubre de
2026, el promedio subió a 33 casos mensuales». Desde el 9-nov el indicador quedaba en caché.

## Factores de decisión

- Seguir midiendo con lo que la fuente publica.
- Una cifra que se pueda comparar entre informes, cosa que el acumulado del año no permitía.

## Opciones consideradas

- **Promedio mensual de casos del tramo más reciente (elegida, Juan, 16-nov).**
- Dejarlo congelado con el último acumulado (101 conflictos, 9-jun-2026).

## Decisión

El indicador es el promedio de casos por mes del tramo más reciente que cita el informe
(«Entre <mes> de <año> y <mes> de <año> … N casos por mes / mensuales»), normalizado 0-100
sobre `CEPA_MAX_CASOS_MES` = 80. Un informe sin promedio por tramo no da dato. La serie se
arma con los informes que traen ese promedio; los que sólo traen el acumulado del año no son
comparables y quedan afuera, así que arranca con el informe 893: 33 casos por mes
(noviembre de 2025 a octubre de 2026), índice 41,2.

### Consecuencias

- No cambia ningún número publicado: el indicador sigue fuera del índice y del tablero.
- La serie pierde los tres puntos del acumulado (abril, junio y agosto de 2026).

### Confirmación

`tests/test_cepa_promedio_mensual.py`.

## Pros y contras de las opciones

- Elegida: comparable entre informes y es lo que publica la fuente; arranca con un solo
  punto.
- Congelado: conserva tres puntos viejos, pero deja de medir.

## Más información

https://centrocepa.com.ar/documentos/informes/893-conflictividad-laboral-en-el-gobierno-de-milei-datos-de-enero-2024-a-noviembre-2026
