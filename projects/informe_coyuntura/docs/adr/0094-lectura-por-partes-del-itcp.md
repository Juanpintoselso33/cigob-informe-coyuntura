---
madr: 4
id: '0094'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
archivos: ['publicar._familias']
ambito: 'ITCP · card pública "Lectura por partes" · `publicar._familias`'
origen: 'Auditoría externa del cinturón político, prioridad 2'
---

# ADR-0094 — El ITCP se puede leer por partes: tensión, capacidad y recursos

## Contexto y planteo del problema

> "Separar explícitamente, **en la narrativa del informe (no necesariamente en
> el cálculo)**, qué indicadores miden tensión externa (oposición, gobernadores,
> calle), cuáles miden capacidad interna de gobierno (cohesión propia, uso de
> DNU) y cuáles miden recursos de negociación (imagen y voto). Hoy los tres
> tipos conviven sin distinción dentro de 'Cinturón Política', lo que dificulta
> responder con precisión la pregunta de si el gobierno puede ejecutar pese a la
> tensión."

Es la observación que mejor resume el pedido editorial de esta revisión: el
índice debía servir a la vez a su propósito declarado —capital político, en el
sentido de capacidad de gobernar— y al encuadre de la auditoría —la tensión que
legisladores, gobernadores y empresarios ejercen—. Un promedio único de las tres
cosas no responde ninguna con precisión.

## Opciones consideradas

- **Publicar una card de «Lectura por partes»** con las tres familias, sus puntajes y sus componentes ordenados de peor a mejor — elegida. La separación es **de lectura, no de cálculo**, tal como pedía la auditoría.
- **Partir el cálculo del índice en tres** — descartada.

## Decisión

Se publica una card, **"Lectura por partes"**, tercera de la familia de
robustez junto a "Consistencia interna" (ADR-0085) y "Rezago del índice"
(ADR-0092). Muestra las tres familias con su puntaje, su peso y sus componentes
ordenados de peor a mejor —el que primero conviene mirar va arriba—, más la
conclusión en prosa.

**La separación es de lectura, no de cálculo**, tal como la auditoría lo
planteó: el ITCP se computa igual, los pesos no cambian y ninguna banda se
toca. Se agrega poder leerlo abierto.

El cálculo vive en el pipeline: las tres familias son promedios ponderados por
**peso efectivo**, de modo que reconstruyen el índice general y siguen siendo
ciertas cuando los pesos cambien.

La conclusión publicada cierra con lo que importa:

> Las tres cosas no se compensan entre sí: un Gobierno puede tener con qué
> negociar y aun así no lograr que sus normas prosperen, y esas dos situaciones
> exigen respuestas distintas.

### Confirmación

`test_todo_indicador_del_indice_declara_su_familia` exige que `FAMILIAS_ITCP`
cubra exactamente a los indicadores del índice, en los dos sentidos, y que las
tres familias existan. Sin eso, un indicador nuevo se caería de la
descomposición y las familias dejarían de sumar el total sin que nada avise.
Es la tercera guardia de esta forma —tras ADR-0092 y la de ADR-0089— y responde
al mismo modo de falla: un diccionario paralelo al índice que se desactualiza en
silencio.

## Más información

### Limitaciones

- **La clasificación es interpretativa.** Ningún indicador trae escrito a qué
  familia pertenece; las asignaciones dudosas están justificadas arriba, pero
  otro criterio razonable podría mover `veto_quorum` o `adhesion_reformas_provincial`.
  Por eso la card publica los componentes de cada familia: el lector puede
  reagrupar mentalmente si no comparte el corte.
- **Sólo el ITCP.** El mecanismo es genérico, pero la tríada tensión/capacidad/
  recursos es propia de un cinturón que mide capital político. Los otros índices
  necesitarían su propia partición, si es que la tienen.
- La auditoría dejó abierta una pregunta que este ADR **no** resuelve: si
  `conflictividad_nacional` —que mide a la sociedad civil, un actor distinto de
  los tres del objetivo declarado— corresponde a este cinturón o a otro. Queda
  como decisión editorial pendiente.

### La clasificación

Los doce indicadores del índice se reparten en tres familias, declaradas en
`itcp.FAMILIAS_ITCP` con el motivo de cada asignación:

**Tensión externa** — conducta de terceros: `desafios_legislativos` (el Congreso
decide dar la pelea), `veto_quorum` (la cámara no se reúne),
`conflictividad_nacional` (la calle), `brecha_obra_publica` (los empresarios que
dependen del Estado), `alineamiento_senadores_prov` y
`adhesion_reformas_provincial` (qué deciden las provincias).

**Capacidad propia** — resultado de la acción del gobierno:
`eficacia_legislativa` (cuánto de lo que manda se sanciona), `bloqueo_sostenido`
(cuánto aguanta de lo desafiado), `ratio_dnu` (cuánto depende del decreto),
`cohesion_bloque` (cuán unido vota su propio bloque).

**Recursos de negociación** — activos, no conducta de nadie:
`votometro_ventaja_lla` (capital electoral) e `iaf_transferencias` (el giro
fiscal como instrumento).

Dos asignaciones merecen justificarse porque no son obvias:

- **`iaf_transferencias` va a recursos, no a tensión.** Un giro de transferencias
  lo decide el Gobierno nacional: describe con qué instrumento cuenta para
  negociar con las provincias, no cómo responden ellas. Es la misma corrección
  de encuadre que ADR-0093 aplicó a su texto público.
- **`veto_quorum` va a tensión, no a capacidad.** Que la cámara no se reúna es,
  en los términos de la propia auditoría, "capacidad opositora de bloqueo puro".
  Con la salvedad ya declarada de que el indicador no distingue el quórum
  frustrado por la oposición del que falla por inasistencia propia.

### Lo que muestra

| familia | puntaje | peso en el índice |
|---|---|---|
| Recursos de negociación | **74,0** | 17% |
| Tensión externa | 71,3 | 48% |
| **Capacidad propia** | **63,2** | 36% |

Con el ITCP global en 69,0, la lectura por partes dice algo que el número único
esconde: **el Gobierno tiene más con qué negociar que con qué ejecutar.** Lo que
lo limita no es tanto la presión externa (71,3) como su propia maquinaria
(63,2).

Y adentro de capacidad propia el contraste es más filoso todavía: cohesión de
bloque **96,7** contra ratio DNU **16,0** y bloqueo sostenido **10,0**. Un
oficialismo internamente unido y a la vez institucionalmente débil — dos hechos
que el promedio de la dimensión mezcla en un solo número.
