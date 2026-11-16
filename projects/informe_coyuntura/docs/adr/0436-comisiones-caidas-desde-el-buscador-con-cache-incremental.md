---
madr: 4
id: '0436'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [comisiones_caidas]
archivos: ['scripts/hcdn_buscador.py', 'scripts/politica.py', 'scripts/descargar_series.py', 'data/politica/hcdn_dictamenes_cache.json', 'tests/test_hcdn_buscador.py']
relacionado: ['0431', '0432']
ambito: 'Seguimiento interno de `comisiones_caidas` (fuera del índice y del tablero)'
origen: 'Juan, 16-nov-2026: «¿por qué de a uno todos? ¿No puede ser incremental?».'
---

# ADR-0436 — Comisiones caídas sale del buscador de Diputados, con una caché incremental

## Contexto y planteo del problema

`comisiones_caidas` es el porcentaje de proyectos con dictamen de Diputados (Orden del Día)
en los últimos 12 meses que no se sancionaron. Está fuera del índice y del tablero. Leía los
datasets de dictámenes y movimientos de `datos.hcdn.gob.ar`, caído desde el 4-nov-2026
([[0431]]). El buscador de proyectos de la Cámara ([[0432]]) trae los dictámenes y los
movimientos de cada proyecto, pero sólo en el detalle, de a un proyecto por pedido.

## Factores de decisión

- No sumar a cada corrida nocturna unos 15 minutos de pedidos.
- La misma regla que el indicador.

## Opciones consideradas

- **Caché incremental en el repo (elegida, Juan, 16-nov).**
- Pedir cada noche el detalle de todos los proyectos: unos 2.150 pedidos.
- Dejarlo congelado hasta que vuelva el portal.

## Decisión

`hcdn_buscador.dictamenes_diputados` lista, con el filtro `con_dictamen_diputados`, los
proyectos de las Órdenes del Día del año anterior y del actual: unas 100 páginas. Pide el
detalle sólo de los proyectos nuevos, porque el dictamen no cambia una vez publicado, y de
los proyectos de ley todavía sin sanción, una vez por día. Guarda en
`data/politica/hcdn_dictamenes_cache.json`, de cada proyecto, sus dictámenes de Diputados
(número, año y fecha de la Orden del Día) y las fechas de sus movimientos de sanción.

- La card se calcula con la misma ventana de 365 días.
- La serie conserva los meses anteriores a enero de 2026, que el CKAN ya publicó, y
  recalcula desde enero de 2026, cuando la ventana cae entera dentro de los dos años de la
  caché (`COMISIONES_BUSCADOR_DESDE`).

La carga inicial (1.045 proyectos, nueve minutos) se hizo el 16-nov desde la Mac y quedó
versionada. Cada noche son unos 110 pedidos, alrededor de un minuto.

### Consecuencias

- No coincide exacto con el CKAN. Al 4-nov da 95,5 % (624 proyectos con dictamen y 28
  sancionados) contra 96,5 % (549 y 19).
  - Los movimientos del buscador también registran las sanciones del Senado, y no dicen de
    qué cámara son.
  - El buscador trae algunas Órdenes del Día más.
- En la serie se nota como un escalón de uno a dos puntos desde enero de 2026. Se acepta
  porque el indicador es interno y no se publica.

### Confirmación

`tests/test_hcdn_buscador.py::test_la_cache_es_incremental` y
`::test_comisiones_caidas_cuenta_la_ventana`.

## Pros y contras de las opciones

- Elegida: un minuto por noche; a cambio, un punto de diferencia con el CKAN.
- Todo cada noche: el mismo dato y 15 minutos más.
- Congelado: deja de medir.

## Más información

`www.hcdn.gob.ar/proyectos/buscador/api/v1/proyectos?con_dictamen_diputados=1&od_anio=2026`
