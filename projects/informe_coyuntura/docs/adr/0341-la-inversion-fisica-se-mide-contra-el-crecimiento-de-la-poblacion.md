---
madr: 4
id: '0341'
estado: 'aceptado'
fecha: 2026-09-30
cinturon: 'macro'
indice: 'ITCM'
indicadores: [iai]
archivos: ['scripts/itcm.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'tests/test_itcm.py', 'tests/test_idm_e_icip_no_puntuan.py']
relacionado: ['0331']
ambito: 'Cinturón macro · ITCM · dónde arranca el verde de la inversión física'
origen: 'Revisión de Luis del 23-sep-2026: «el tema de inversión física se toma verde cuando está arriba de 0, por lo menos debería estar arriba del crecimiento de la población o ponerlo como relación al PBI». Juan eligió el piso de población el 30-sep, sabiendo que mueve la escala sólo 0,17 puntos.'
---

# ADR-0341 — La inversión física se mide contra el crecimiento de la población

## Contexto y planteo del problema

La card «Inversión física» salía en verde apenas su variación interanual
superaba 0 %: las anclas del índice macroeconómico ponían el puntaje 60 —el
corte del verde— justo en 0. Luis objetó que crecer 0,1 % no es expandir la
inversión si la población crece más que eso: por habitante se estaría
invirtiendo menos.

Antes de fijar el piso se midió el crecimiento de la población, en vez de
suponerlo. La proyección vigente del INDEC, «Estimaciones y proyecciones de
población. Total del país. Años 2022-2040» (base Censo 2022), Cuadro 1, da
46.387.098 habitantes al 1 de julio de 2025 y 46.466.688 en 2026: **+0,17 %**.
El Cuadro 3 da una tasa de crecimiento total de 1,8 por mil para 2025, y el
dosier del INDEC de octubre de 2025 espera un promedio de 0,16 % por año hasta
2040. La cifra que suele venir a la cabeza, de 0,8-1 % anual, es la de la
proyección anterior, con base en el Censo 2010; el Censo 2022 la dejó sin
efecto.

## Factores de decisión

- El pedido es explícito: el verde tiene que estar, al menos, por encima del
  crecimiento de la población.
- El piso tiene que salir de una fuente oficial citada, no de una convención.
- No se recalibra el resto de la escala: sus anchos se decidieron por la
  volatilidad del dato y ese argumento sigue en pie.

## Opciones consideradas

1. **Correr la escala entera al crecimiento de la población** — elegida.
2. Mover sólo el corte del verde y dejar las demás anclas donde estaban.
3. Medir la inversión como proporción del PBI (la otra propuesta de Luis).

## Decisión

Las cinco anclas de `iai` en `BANDAS_ITCM` se corren
`CRECIMIENTO_POBLACION_PCT = 0.17` puntos: el tramo neutro deja de estar
centrado en 0 y pasa a estarlo en «invertir lo mismo por habitante». El verde
arranca en +0,17 %.

La opción 2 dejaba el tramo entre 0 y 0,17 más empinado que el resto sin
motivo. La opción 3 es un indicador distinto —nivel y no variación, trimestral y
con tres meses de rezago— y no una corrección de este; queda para conversar.

### Consecuencias

- **El efecto es chico y se declara así.** Con una población que casi no
  crece, el piso mueve la escala 0,17 puntos. El −5,66 % de julio pasa de 36,4 a
  35,7 puntos y sigue en naranja; ninguno de los 34 meses de la serie publicada
  cambia de color por esto (verificado contra `series.json` el 30-sep).
  La objeción de fondo de Luis —que el verde es fácil de alcanzar— no la
  resuelve este piso. Si se quiere más exigencia, la discusión es la opción 3 o
  subir el corte del verde por criterio propio, y cualquiera de las dos pide su
  propio ADR.
- El piso es una constante: no se actualiza con cada proyección. Si el INDEC
  revisa sus proyecciones, hay que volver a medirlo.
- `test_idm_e_icip_no_puntuan.py` congela las bandas de agosto de `iai` para que
  la atribución de ADR-0261/0262 siga midiendo esa decisión y no esta.

### Confirmación

- `test_itcm.py` fija las anclas nuevas (−9,83 · −5,83 · 0,17 · 6,17 · 10,17) y
  los bordes de banda.
- `test_fichas_bandas.py` exige que la ficha publique los mismos cortes que el
  motor, y `test_la_ficha_no_se_queda_atras` que registre este ADR.

## Pros y contras de las opciones

### Correr la escala entera

- Bien: hace lo que se pidió con una sola constante citada, y la forma de la
  escala no cambia.
- Mal: su efecto es casi simbólico con la demografía actual.

### Mover sólo el corte del verde

- Bien: toca el único corte en discusión.
- Mal: deja un tramo de 0,17 puntos con otra pendiente, sin justificación.

### Inversión como proporción del PBI

- Bien: mide un nivel, así que discriminaría de verdad entre invertir mucho y
  poco.
- Mal: es trimestral, llega con tres meses de rezago y es otro indicador, con su
  ficha, su serie y su validación.

## Más información

- ADR-0331 — por qué no hay indicador de inversión tecnológica (el otro punto de
  la misma revisión).
- INDEC, `proyecciones_nacionales_2022_2040.pdf`, Cuadros 1 y 3.
