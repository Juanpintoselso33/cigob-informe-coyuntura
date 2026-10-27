---
madr: 4
id: '0376'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [votos_sobre_bancas, cohesion_bloque]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'data/politica/votos_sobre_bancas_actas.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'tests/test_votos_sobre_bancas.py']
relacionado: ['0040', '0041', '0048', '0284', '0359']
ambito: 'Cinturón político · ITCP · dimensión Cohesión interna del oficialismo'
origen: 'Pedido de Luis Babino (bajar el peso de la cohesión) y decisión de Juan del 27-oct-2026.'
---

# ADR-0376 — Los votos ajenos al aprobar leyes entran a la cohesión interna

## Contexto y planteo del problema

La dimensión de cohesión interna del oficialismo tenía un solo indicador,
`cohesion_bloque` (qué tan parejo vota el bloque de La Libertad Avanza, LLA), y
pesaba 16,1 % del índice político. Luis pidió que la cohesión pesara menos y que
la dimensión midiera también algo que la cohesión no ve: un bloque puede votar
unido y aun así necesitar muchos votos de otros bloques para aprobar una ley.

## Factores de decisión

- Que la dimensión siga siendo del oficialismo y de su capacidad de sumar votos.
- No tocar el peso de la dimensión entre las seis (ADR-0344).
- Usar actas que ya se leen (las dos cámaras) y no pedir una fuente nueva.
- Que el indicador se deje reproducir a mano acta por acta.

## Opciones consideradas

- **Indicador nuevo `votos_sobre_bancas`, 50/50 con la cohesión (elegida).**
- Dejar la cohesión sola y bajar el peso de la dimensión: no agrega ninguna
  lectura y mueve las demás dimensiones.
- Medir la mayoría con la que se aprobó cada ley, sin restar las bancas propias:
  mezcla el tamaño del bloque con la negociación.

## Decisión

Nace `votos_sobre_bancas`: **votos a favor con que se aprueba cada ley menos las
bancas propias de LLA, como % de las bancas de la cámara.**

- Universo: votaciones nominales EN GENERAL de proyectos de ley con resultado
  afirmativo y con el bloque LLA votando mayoritariamente a favor (más
  afirmativos que negativos dentro del bloque). Diputados y Senado por separado.
- Por votación: `(afirmativos totales − bancas del bloque LLA en esa acta) /
  bancas de la cámara × 100`. Las bancas del bloque son todos los legisladores
  del bloque que figuran en el acta, hayan votado o no. Bancas de la cámara: 257
  en Diputados (el acta lista 256 filas, sin quien preside) y 72 en el Senado
  (lista las 72).
- Por cámara: promedio simple de las votaciones de los últimos 12 meses
  calendario, sin cruzar la instalación del Congreso (10-dic-2023).
- Indicador: 65 % Diputados + 35 % Senado, el reparto de `cohesion_bloque`; si
  falta una cámara en la ventana, la otra sola y el detalle lo dice.
- Entra a `cohesion_interna` **50/50** con `cohesion_bloque`: la cohesión baja de
  16,1 % a ~8,1 % del índice. El peso de la dimensión no cambia.
- Familia `capacidad`, rezago 6 meses (centroide de la ventana; las actas salen
  en días).
- Anclas por **convención declarada**, más alto = mejor: 40 % o más → 100 · 30 → 85
  · 20 → 65 · 10 → 40 · 5 % o menos → 10. Se codifican con bandas (5,15) (15,25)
  (25,35) (35,45) y una abierta que repite el 100, porque el motor interpola en
  el punto medio de cada banda y así las anclas caen exactamente donde se
  declararon.
- Serie mensual desde dic-2023 con el mismo cálculo que la tarjeta (la tarjeta es
  el último punto), sobre un caché permanente por acta
  (`data/politica/votos_sobre_bancas_actas.json`) que se escribe de a una acta.

Cómo se decide el universo en cada cámara:

- **Senado**: el acta trae la etapa («en general», «en general y en particular»,
  «en particular»…) y la clave del expediente. Cuenta si la etapa es general (o no
  declara, cuando se vota en bloque) y algún expediente termina en `-PL`.
  Pliegos (`-AC`), resoluciones (`-PR`) y declaraciones (`-PD`) no cuentan. Sin
  expediente, cuenta un Orden del Día que no sea designación, moción ni
  reconocimiento.
- **Diputados**: el PDF no dice qué clase de proyecto es. Se decide por el título:
  cuenta «VOT. EN GRAL.» y la votación única de un Orden del Día; no cuentan
  mociones, habilitaciones, apartamientos, pedidos de informes, comisiones
  investigadoras, DNU, insistencias ni los títulos con capítulo, título o
  artículo (votaciones en particular).

### Consecuencias

- Con las actas leídas el 27-oct-2026 (103 votaciones del universo: 54 de Diputados
  desde feb-2025 y 49 del Senado desde mar-2024, de las cuales 72 caen en la ventana
  de 12 meses): el indicador vale 40,8 % (Diputados 39,7 con 46 votaciones, Senado
  42,9 con 26) y puntúa 100, el techo de la escala. La serie arranca en 71,9 (mar-2024,
  sólo Senado), llega a 60,1 en oct-2025 y baja a 40,8 hoy.
- Ese valor está empujado por las leyes de consenso: en 2026 los tratados, las capitales
  nacionales y los reconocimientos se aprueban con 40-65 % de la cámara de votos ajenos,
  mientras que las leyes de la agenda oficial (presupuesto, reforma laboral, inocencia
  fiscal, propiedad privada) quedan entre 12 % y 35 %. La definición pedida promedia
  votaciones, no leyes de peso político; si hace falta separar, es una decisión de
  Luis y de Juan, no de este ADR.
- El excedente depende del tamaño del bloque propio. El bloque LLA de Diputados
  pasó de 36-39 a 94 bancas (y el del Senado de 9 a 21) con la renovación de diciembre de 2025: con el
  mismo respaldo total el excedente baja. Se declara como limitación en la ficha.
- Las leyes de consenso (tratados, capitales nacionales) suben el promedio porque
  se aprueban con casi toda la cámara. Se cuentan por votación y no por ley.
- **El portal de Diputados dejó de publicar las actas anteriores al 6-feb-2025**
  (id 5567) y cambió la ruta del PDF a `/pdf/acta/{id}.pdf`, unos días antes de
  esta decisión. Con la ruta vieja el recorrido de actas de Diputados daba «sin
  actas»; se corrige en `_DIPUTADOS_ACTA_PDF_PATH`. Entre dic-2023 y ene-2025 el
  indicador es sólo el Senado, y la ventana de Diputados recién se completa en
  feb-2026. La cohesión de Diputados anterior sigue en su caché permanente.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]); el dato nuevo, no, hasta que
  se publique el mes siguiente.

### Confirmación

`tests/test_votos_sobre_bancas.py` fija el cálculo del excedente, el universo
(no cuenta lo que no es ley en general, lo rechazado ni lo que LLA votó en contra),
la ventana de 12 meses, el 65/35, el caché por acta y la composición 50/50 en el
ITCP. `tests/test_fichas_bandas.py` y `tests/test_la_ficha_no_se_queda_atras.py`
cruzan la ficha contra el motor y este ADR.

## Pros y contras de las opciones

- Indicador nuevo 50/50: mide capacidad de sumar votos y deja la cohesión en la
  mitad de la dimensión; cuesta un criterio de universo que en Diputados sale del
  título.
- Bajar el peso de la dimensión: simple, pero no agrega información.
- Mayoría de aprobación sin restar bancas propias: no distingue un bloque grande
  de una negociación exitosa.

## Más información

Precedentes de la cohesión: [[0040-cohesion-bloque-diputados-desbloqueo-pdf]],
[[0041-cohesion-bloque-diputados-cache-permanente-y-serie-mensual]],
[[0048-revision-editorial-cinturon-politica]] (compuesto bicameral 65/35) y
[[0284-cohesion-publica-fechas-y-cache-por-camara]].

Si se prefiere la lectura por cortes (≥ 40 · 30-40 · 20-30 · 10-20 · ≤ 10) en vez
de anclas, se cambia la tabla de `BANDAS_ITCP["votos_sobre_bancas"]` y la ficha;
un valor de 20 % pasa de puntuar 65 a ~52.
