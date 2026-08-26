---
madr: 4
id: '0259'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'transversal'
archivos: ['scripts/generar_informe.py', 'tests/test_suspendido_es_archivo_no_componente.py', 'tests/test_suspension_libera_el_peso.py']
relacionado: ['0245', '0246', '0247', '0248', '0255', '0189', '0210', '0180']
ambito: 'Transversal · qué dice el artefacto crudo de un indicador que ya no puntúa'
origen: 'Reauditoría de indicadores, 25-ago-2026, discrepancias 7 y 8: «una serie retirada puede preservarse como archivo, pero no debe aparecer como componente vigente ni conservar peso/estado activo en consumidores públicos»'
---

# ADR-0259 — Un indicador suspendido es archivo, no componente

## Contexto y planteo del problema

[[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]] sacó a los
suspendidos del **cálculo**, y `publicar.py` los saca del **snapshot público**.
Entre esas dos capas quedó `output/informe.json`, que se arma copiando el caché
del colector tal cual. Ahí, el 25 de agosto de 2026:

| Indicador | `en_indice` | `peso_efectivo` | `puntaje_itcp` |
|---|---|---|---|
| `judicializacion` (ITCP, [[0255-el-corpus-de-saij-no-identifica-al-ejecutivo]]) | `true` | `0.03` | `54.4` |
| `apoyo_empresario` (ITCP, [[0246-el-saldo-empresario-se-calculaba-sobre-un-corpus-abierto]]) | `true` | — | — |
| `reestructuracion_organismos` (ITCG, [[0247-un-porcentaje-entre-normas-y-una-meta-documental]]) | `false` | — | — |

Los tres estaban igual de fuera del score. El artefacto decía tres cosas
distintas. Y el peso y el puntaje de `judicializacion` no eran de hoy: eran los
de la última corrida en que efectivamente puntuó, congelados por el
carry-forward del caché. Un consumidor que leyera ese archivo reconstruiría un
ITCP de 18 componentes que nadie calculó.

**Por qué salió distinto en cada cinturón.** `gestion.anotar_indicadores()`
recorre `itcg.INDICADORES_SUSPENDIDOS` y marca; `politica._anotar_indicadores_itcp()`
no tiene ese bloque, y su fallback es `en_indice = nombre in itcp.BANDAS_ITCP`
—que sigue dando `True`, porque la banda no se borra: [[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]
decidió justamente no tocar las tablas de diseño—. O sea: el colector que se
acordó, marcó; el que no, no. Es el modo de falla de toda regla que hay que
repetir en cada colector, y ya tiene antecedentes en este repo
([[0082-un-solo-camino-al-puntaje]] agrupó tres casos de lo mismo).

Este ADR no discute si los indicadores tienen que salir del score: eso ya está
decidido en 0246, 0247, 0248 y 0255. Discute **qué queda de ellos en el
artefacto** y **quién se encarga de que quede así**.

## Factores de decisión

- **No borrar la historia.** El valor, su fuente y su fecha son el registro de
  por qué se suspendió; borrarlos hace irreproducible la propia decisión.
- **Un solo estado, no tres.** Los cuatro suspendidos tienen que verse igual,
  vengan del cinturón que vengan.
- **La próxima suspensión no puede requerir acordarse de nada.** Si el contrato
  se cumple indicador por indicador, se rompe en el quinto.
- **Nada de peso ni de puntaje.** Son los campos que un consumidor suma,
  promedia y grafica; mientras existan, el indicador participa aunque el texto
  diga que no.
- **Compatibilidad hacia abajo.** `publicar.py` y `bigquery_export.py` leen
  este artefacto; el contrato no puede obligar a reescribirlos.

## Opciones consideradas

- **A — Borrar el indicador del artefacto.** Retirada estricta.
- **B — Marcarlo: `en_indice: false`, sin campos de scoring, con un bloque
  `suspendido` que dice desde cuándo, por qué y con qué condición vuelve.**
- **C — Moverlo a una sección aparte del JSON** (`indicadores_suspendidos`),
  hermana de `indicadores`.
- **D — Dejarlo como componente con `peso_efectivo: 0`.**

## Decisión

**Opción B**, aplicada en `generar_informe.py`, en el último paso antes de
escribir el artefacto, recorriendo `INDICADORES_SUSPENDIDOS` de cada índice.

El contrato, en una frase: **un indicador suspendido se conserva como archivo y
nunca como componente vigente.** En concreto:

- conserva `valor`, `unidad`, `fuente`, `fecha_dato`, `detalle_txt`, su detalle
  propio y la `dimension` donde pesaba —dónde pesaba es parte del archivo, no
  una afirmación de vigencia—;
- pierde `en_indice: true`, `peso_efectivo`, `peso`, `aporte_score` y todo
  `puntaje_*`;
- gana `suspendido: {dimension, desde, desde_txt, adr, por_que,
  condicion_reingreso}`, que es la entrada de `INDICADORES_SUSPENDIDOS` tal
  cual.

Tres detalles que no son obvios:

**Los campos se borran, no se ponen en cero.** La ausencia ya es la forma que el
artefacto usa para todo lo que no puntúa: `rotacion_gabinete` y el resto del
contexto nunca tuvieron esas claves. Un `peso_efectivo: 0` sería una segunda
convención para el mismo hecho —y además un número, que se suma, se promedia y
se grafica—. Es la única diferencia con lo que recomendaba la reauditoría, y va
en su misma dirección.

**`puntaje_*` se borra por prefijo.** Enumerar `puntaje_itcm`, `puntaje_itcp`,
`puntaje_itcg`, `puntaje_banda` es exactamente lo que se olvida el día que
aparece una sigla nueva.

**Se hace acá y no en cada colector.** Es lo que convierte la decisión en algo
que no hay que recordar: la próxima suspensión es una entrada en
`INDICADORES_SUSPENDIDOS` y nada más. `gestion.py` puede seguir marcando lo
suyo —lo hace bien y el resultado es idempotente—, pero ya no es lo que
sostiene el contrato.

`informe.md` sale del mismo paso y recibe el mismo trato: los suspendidos dejan
la tabla de indicadores del cinturón y pasan a una tabla propia, rotulada
*«Suspendidos — archivo histórico, NO integran el índice ni el score de
arriba»*, con desde cuándo, el ADR y el motivo. Compartir tabla con los
vigentes es afirmar que son el mismo tipo de cosa, y el `.md` es artefacto de
ingesta: lo lee quien no tiene el resto del contexto a mano.

### Consecuencias

- **`output/informe.json` deja de contradecir al snapshot público.** Los cuatro
  suspendidos quedan `en_indice: false`, sin peso ni puntaje, con su motivo.
- **Ningún número publicado cambia.** Los suspendidos ya no entraban al
  cálculo, y `publicar.py` los oculta del snapshot vía `POLITICA_OCULTOS` /
  `GESTION_OCULTOS` / `VIDA_OCULTOS`. Lo que cambia es lo que el artefacto
  *dice* de ellos.
- **Un suspendido deja de disparar el flag diario de desactualizado.** Su
  frescura no tiene consecuencia: no alimenta ningún puntaje ni ninguna card.
  `judicializacion` es el caso vivo — SAIJ bloquea a los runners casi todas las
  noches ([[0175-el-ancla-icg-vuelve-a-actualizarse]] documenta la clase de error, y la
  política acordada es refrescar a mano). Es la misma lógica con que
  [[0210-un-cache-esperable-no-es-carry-forward]] sacó del flag a los que andan
  por caché a propósito.
- **Aparece una guarda que hoy no puede fallar, y es a propósito.**
  `verificar_que_ninguno_puntua()` corta la corrida si un suspendido aparece
  *dentro* del bloque del índice, con peso y puntaje propios. Hoy no puede
  pasar, porque `calcular_itc*()` filtra con `parametrica.sin_suspendidos()`.
  El día que un índice nuevo se olvide de llamarlo, el artefacto saldría con el
  suspendido puntuando y nada lo diría.
- **BigQuery no necesita cambios, y conviene saber por qué.**
  `bigquery_export.py` lee `web/src/data/informe.json`, no el artefacto crudo
  ([[0180-integracion-con-la-plataforma-google]]), y ahí los suspendidos ya no existen:
  el archivo histórico tiene sus filas hasta julio de 2026 con `en_indice=true`
  —que es correcto, entonces puntuaban— y ninguna después. La consecuencia real
  es que **desde BigQuery una suspensión es indistinguible de una serie que se
  cortó**, porque no hay fila que lo diga. Queda anotado como deuda: se
  arreglaría o publicando los suspendidos en el snapshot con su bloque
  `suspendido`, o agregando una columna al export. Las dos tocan archivos que
  no son de este ADR.

### Confirmación

`tests/test_suspendido_es_archivo_no_componente.py` (17 guardas), sobre el
artefacto real construido desde los cachés que hoy dejan los colectores —uno de
los cuales no marca nada—:

- ningún suspendido sale con `en_indice` distinto de `false`, con campos de
  componente vigente, ni sin bloque `suspendido`;
- el archivo sobrevive: valor, unidad, fuente, fecha y dimensión intactos;
- **una suspensión inventada, agregada a la tabla del índice sin tocar
  `generar_informe.py`, queda archivada igual** — es la guarda de que el
  contrato no es una lista de nombres;
- un suspendido que no está en el caché no se inventa como fila fantasma;
- la guarda del índice grita si uno se cuela puntuando;
- el flag diario ignora al suspendido y **no** al vigente de al lado, con el
  caché forzado a estar vencido (con los datos reales el filtro es inerte, así
  que mirarlos no probaría nada);
- en el `.md`, cada fila cae de su lado del rótulo, y el motivo sobrevive a
  saltos de línea y a un `|` adentro.

`tests/test_suspension_libera_el_peso.py` suma `judicializacion` a sus casos
—era el único de los cuatro que no estaba— y ancla el puente entre las dos
mitades del tema.

Probado rompiéndolo, nueve mutaciones, todas cazadas: no llamar al marcado, no
borrar los campos, no poner `en_indice: false`, cambiar la tabla del índice por
una lista fija de nombres, desactivar el `raise` de la guarda, devolver el
suspendido a la tabla de vigentes del `.md`, no normalizar los saltos de línea
del motivo, no escapar el `|`, y sacar el filtro del flag diario.

Una décima mutación **no** fue cazada en el primer intento y por eso está
anotada: la normalización del motivo del `.md` era inatacable contra los datos
reales, porque ningún `por_que` de hoy tiene saltos de línea ni `|`. El test
pasaba con y sin el arreglo. Se reescribió inyectando un motivo que sí los
tiene. Una guarda que no se probó rompiéndola no se sabe si guarda.

## Pros y contras de las opciones

### A — Borrar el indicador del artefacto

- Bueno, porque no hay forma de leerlo como vigente.
- Malo, porque borra el registro de la propia suspensión: sin el último valor
  no se reproduce por qué se decidió.
- Malo, porque desde afuera es indistinguible de una fuente que dejó de
  publicar.

### B — Marcarlo como archivo

- Bueno, porque conserva la historia y elimina la ambigüedad al mismo tiempo.
- Bueno, porque no cambia la forma del artefacto: `suspendido` ya existía
  —`gestion.py` lo emitía— y `en_indice: false` ya era el estado de todo lo que
  no puntúa. Ningún consumidor se rompe.
- Malo, porque el indicador sigue en el mismo diccionario que los vigentes: hay
  que mirar un campo para distinguirlos. Lo compensa que ese campo es el mismo
  que ya distinguía al contexto.

### C — Sección aparte del JSON

- Bueno, porque la separación es estructural y no se puede pasar por alto.
- Malo, porque rompe a todo consumidor que recorra `cinturones[*].indicadores`
  —`publicar.py`, `bigquery_export.py`, `verificacion_remediacion.py`,
  `manifiesto_remediacion.py` y varios tests— para no decir nada que
  `en_indice: false` más `suspendido` no digan ya.
- Malo, porque obliga a versionar el schema para un cambio de acomodo.

### D — Componente con `peso_efectivo: 0`

- Bueno, porque es explícito: aporta cero.
- Malo, porque deja al indicador *adentro* del índice, que es la afirmación que
  hay que retirar.
- Malo, porque un cero es un número: entra a sumas, promedios y gráficos, y
  cuenta como componente en cualquier `len()`.

## Más información

- Reauditoría de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_reauditoria_post_cambios_completa.md`,
  discrepancias 7 y 8, y el expediente de Política, sección 4.

### Lo que este ADR no arregla

La reauditoría marca, en la misma sección, dos residuos que viven en
`web/src/lib/`: la descripción de **Sector privado** todavía promete dos vías
cuando queda una activa, y la de **Poder judicial** enumera cuatro cuando hoy
son tres. Son contratos descriptivos del frontend y se corrigen ahí, junto con
las entradas de `cambios` en las fichas de los dos indicadores. Quedan fuera
del alcance de este ADR, que es sobre el artefacto crudo.

Y una que conviene mirar cuando se toque `publicar.py`: hoy un `en_indice:
false` cae en la rama que le pone la nota genérica de contexto
(`_scoring_indice`), que para un suspendido es la explicación equivocada —tiene
la suya en el bloque `suspendido`—. No se ve, porque los suspendidos se ocultan
del snapshot ([[0189-si-no-puntua-no-se-muestra]]); se vería el día que alguien
decida mostrarlos.
