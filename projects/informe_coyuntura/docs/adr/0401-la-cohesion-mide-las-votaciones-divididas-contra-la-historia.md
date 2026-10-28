---
madr: 4
id: '0401'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [cohesion_bloque]
parametros: ['UMBRAL_MINORIA_DIVIDIDA', 'ANCLAS_ITCP["cohesion_bloque"]', 'BANDAS_ITCP["cohesion_bloque"]']
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'scripts/sensibilidad.py', 'data/politica/cohesion_bloque_diputados_minoria.json', 'tests/test_politica_cohesion.py', 'tests/test_descargar_series_cohesion.py', 'tests/test_itcp.py', 'tests/test_senado_lectura_completa.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts']
modifica: ['0048']
relacionado: ['0042', '0048', '0400', '0402']
ambito: 'ITCP · dimensión Cohesión interna · universo de votaciones y anclas de la cohesión del bloque'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0401 — La cohesión mide las votaciones divididas, contra la historia

## Contexto y planteo del problema

La cohesión del bloque promediaba el índice de Rice de TODAS las votaciones nominales en
que votó el bloque, incluidas las casi unánimes: una votación 70 a 2 no pone a prueba la
disciplina de nadie y empuja el promedio contra 100. La ficha lo declaraba como
limitación y como «decisión metodológica pendiente». Y las anclas de [[0048]]
(99,9/99/97/95) se calibraron contra la serie del propio mandato: la vara la ponía el
gobierno medido.

## Factores de decisión

- Medir la disciplina donde se pone a prueba.
- Un umbral simple, igual para las dos cámaras, que no dependa del bloque medido.
- Anclas que salgan de un período anterior al medido, medido igual.

## Opciones consideradas

- **Votaciones divididas por la minoría de la cámara (al menos 10 % de los votos) y
  anclas del bloque PRO de Macri 2016-2018 (elegida).**
- Umbral de 20 %.
- Votaciones «partidarias» (la mayoría del bloque contra la mayoría del resto).
- Agrupar por proyecto en lugar de por acta.
- Sin filtro, con las anclas de [[0048]].

## Decisión

Una votación es **dividida** cuando el lado que perdió en toda la cámara —el menor entre
afirmativos y negativos— reunió al menos el 10 % de los votos emitidos
(`UMBRAL_MINORIA_DIVIDIDA`). Por cámara, la cohesión es el promedio del Rice del bloque
sólo en esas votaciones; el compuesto 65/35 y la ventana de 90 días no cambian. En el
Senado el bloque es el del día ([[0400]]).

Las **anclas** salen del bloque PRO de Macri, dic-2015 a dic-2018, medido igual
(Diputados de los datos abiertos de la Cámara, Senado del portal, 65/35, 90 días, sólo
divididas): 34 meses, media 96,95, desvío 3,55. En `ANCLAS_ITCP["cohesion_bloque"]`:
media − 2 desvíos **89,8 → 10** · media − 1 desvío **93,4 → 40** · media **97,0 → 65** ·
media + 1 desvío, con tope en **99,9 → 100**. `BANDAS_ITCP` repite los cortes con el
puntaje de su ancla inferior (color y ficha); el motor del ITCP pasa a leer
`ANCLAS_ITCP`.

Para saber si una votación de Diputados fue dividida hace falta el resultado de toda la
cámara, que la caché por acta no guardaba (sólo el Rice). Las actas nuevas lo guardan;
para las 478 ya cacheadas, `data/politica/cohesion_bloque_diputados_minoria.json` trae la
minoría leída de cada PDF: las publicadas desde el 6-feb-2025, del portal; las
anteriores, que el portal ya no sirve, de su copia en el Internet Archive. El Rice
recalculado desde esos PDF coincide con la caché en las 478.

### Consecuencias

- Hoy el valor no cambia (100) y el puntaje tampoco (100).
- La serie recalculada en memoria, dic-2023 a oct-2026 (35 puntos), sube: el mínimo pasa
  de 90,3 (ago-2025) a 97,4 (ago-2024), y ago-2025 queda en 98,0 (Diputados 96,9, Senado 100). En
  Diputados las disidencias del bloque se concentraban en votaciones casi unánimes; en el
  Senado, en Juez y Paoltroni mientras no eran del bloque ([[0400]]). Puntajes: antes 19
  meses verdes, 9 amarillos, 3 naranjas y 4 rojos; ahora los 35 verdes (el más bajo,
  69,8 en ago-2024, con 97,4). El bloque de este mandato vota, en sus votaciones divididas, más
  unido que la media del PRO 2016-2018.
- La serie de `descargar_series.py` se regenera en la próxima corrida: los años cerrados
  cacheados sin minoría se vuelven a pedir (`VERSION_DETALLE_ACTAS`).
- La procedencia pasa a historia larga y el techo de circularidad del ITCP baja a 0,09
  (con [[0402]]).
- Con menos votaciones por ventana, un voto disidente pesa más, y una ventana sin
  divididas deja a la cámara sin dato (el peso pasa a la otra). Va en la ficha.

### Confirmación

`tests/test_politica_cohesion.py` prueba la minoría, el umbral inclusivo y que la
tarjeta del Senado y la agregación mensual descarten las casi unánimes;
`tests/test_itcp.py`, las anclas y que el motor las use;
`tests/test_descargar_series_cohesion.py`, que un año cerrado sin minoría se vuelve a
pedir.

## Pros y contras de las opciones

- 10 %: deja afuera las casi unánimes y conserva casi dos tercios de las votaciones del
  PRO 2016-2018 (280 de 450 en Diputados).
- 20 %: más exigente, con ventanas a menudo vacías en el Senado.
- Partidarias: depende de la posición del resto, que cambia con las alianzas.
- Por proyecto: corrige el peso de las votaciones en particular, pero cambia la unidad y
  agrega una regla de agrupamiento frágil.
- Sin filtro: seguía midiendo sobre todo votaciones sin disputa.

## Más información

Análisis del 28-oct-2026 con las actas de las dos cámaras de 2016 a 2026.
