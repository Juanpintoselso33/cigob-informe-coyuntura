---
madr: 4
id: '0090'
estado: 'aceptado'
fecha: 2026-07-19
cinturon: 'politica'
indicadores: [ratio_dnu]
ambito: 'ITCP · `ratio_dnu` · ficha pública'
origen: 'Auditoría externa del cinturón político, prioridad 4'
---

# ADR-0090 — Qué pregunta responde el ratio DNU (y por qué no se agrega "éxito por decreto")

| **Confirma** | ADR-0058 / ADR-0059 (ventana móvil y anclas, sin cambios) |

## Contexto y planteo del problema

La auditoría observó que el indicador sólo admite una lectura:

> "Un gobierno que gobierna por decreto con éxito está, en un sentido literal,
> avanzando su plan pese a la falta de acompañamiento legislativo — no
> necesariamente fallando en hacerlo. Hoy el indicador sólo puede leerse en una
> dirección (más DNU = peor puntaje), lo cual es razonable si lo que se quiere
> medir es salud institucional o dependencia del Congreso, pero es
> contraintuitivo si lo que se quiere medir es si el gobierno logra ejecutar su
> agenda."

La objeción es pertinente porque el ITCP declara medir **capacidad de gobernar**
—capital político en el sentido de Matus—, no salud institucional. Si el
indicador estuviera respondiendo la segunda pregunta mientras el índice pregunta
la primera, estaría restando puntaje por el motivo equivocado. Hoy `ratio_dnu`
vale 1,92 y puntúa **16 sobre 100**: no es un detalle de matiz.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

**Se mantiene la dirección del indicador y sus anclas.** Lo que cambia es el
texto público, que ahora dice explícitamente qué pregunta responde.

El razonamiento, que hasta ahora era implícito: el ratio mide **dependencia del
decreto**, no éxito de la ejecución. Se elige esa lectura porque el cinturón
mide capacidad *sostenible* de gobernar, y una norma dictada por decreto es
reversible por el Congreso y por los tribunales de un modo en que la ley no lo
es. La dependencia es una **vulnerabilidad latente**: permanece dormida mientras
el Congreso no active el procedimiento de la ley 26.122, y se cobra de golpe
cuando lo activa. El 7 de agosto de 2025 cayeron cinco decretos en un día.

Los datos sostienen las dos mitades de esa frase a la vez, y por eso se publican
ambas: gobernar por decreto **funciona** (95% nunca se vota) **y** es **frágil**
cuando se lo pone a prueba (6 de 8 caen). Presentar sólo una de las dos sería
sesgar.

## Más información

### Los datos

Se midieron las dos cosas que la discusión requería y que nadie había medido:

| | |
|---|---|
| DNU dictados desde el 10-dic-2023 | **162** |
| leyes sancionadas en el mismo período | 74 |
| decretos que llegaron a votarse en el recinto | **8** |
| **% de DNU que nunca se votó** | **95,1%** |

Y qué pasó con los ocho que sí se votaron:

| decreto | resultado |
|---|---|
| DNU 70/2023 | en pie |
| DNU 179/2025 | en pie |
| DNU 656/2024 | cayó |
| DNU 340/2025 | cayó |
| Decretos delegados 345, 351, 461 y 462 de 2025 | cayeron los cuatro, el mismo día |

**6 de 8 cayeron.**

### Lo que se rechaza, con evidencia

La auditoría sugería además "considerar si el cinturón necesita una variable
separada de *éxito de ejecución por decreto* (cuántos DNU sobreviven y se
implementan)".

**Se descarta.** Como el 95,1% de los DNU nunca se vota, un indicador de
supervivencia quedaría permanentemente entre 95 y 100: sin varianza, no
distinguiría ningún estado del mundo de ningún otro. La causa es la propia ley
26.122 — un DNU sigue vigente salvo que lo rechacen **las dos** cámaras, de modo
que la inacción del Congreso equivale a la ratificación.

La consulta queda registrada acá para que el negativo sea auditable y alguien
pueda refutarlo con una medición mejor: conteo de InfoLeg `tipoNorma=2` con el
texto "necesidad y urgencia" sobre 10-dic-2023 → hoy, contra el registro de
eventos versionado (`data/politica/derrotas_legislativas_eventos.json`), que
tiene ocho decretos desafiados en total.

Vale notar que la parte de la pregunta que **sí** tiene poder discriminante ya
está medida: `bloqueo_sostenido` es exactamente "de las normas que el Congreso
puso a prueba, cuántas siguen en pie".

### Coherencia con la jornada

En ADR-0089, unas horas antes, `ratio_dnu` había subido de 0,20 a 0,23 dentro de
la dimensión. Subirle peso a un indicador cuya interpretación estaba bajo
revisión fue apresurado. Se evaluó revertirlo y **se decidió mantener el 0,23**,
ahora sí con fundamento: revisada la objeción, el indicador responde la pregunta
que el índice necesita.

### Limitación que queda en pie

El indicador no distingue un DNU central de uno administrativo: los 162 pesan
igual. Un gobierno podría bajar el ratio dictando menos decretos irrelevantes
sin cambiar nada de su relación con el Congreso. No hay hoy una fuente que
clasifique los DNU por materia o por relevancia de forma automatizable.
