---
madr: 4
id: '0209'
estado: 'aceptado'
fecha: 2026-08-18
cinturon: 'transversal'
archivos: ['scripts/bigquery_backfill.py', 'scripts/bigquery_export.py']
relacionado: ['0180', '0205', '0207', '0221', '0231']
ambito: 'Archivo histórico en BigQuery · corridas anteriores al 6-ago-2026 · columnas `origen` y `valor_txt`'
origen: 'El espejo en BigQuery arrancó el 6-ago-2026, pero el informe publica desde el 23-may'
---

# ADR-0209 — El archivo se rellena desde git, y cada corrida dice de dónde vino

## Contexto y planteo del problema

El espejo en BigQuery ([[0180-integracion-con-la-plataforma-google]]) empezó a
correr el 6-ago-2026. El informe publica desde el 23-may-2026. Entre esas dos
fechas hay **206 corridas que el archivo histórico no tiene**, y que no se
perdieron: cada una quedó commiteada en `web/src/data/informe.json` junto con
sus artefactos de análisis.

Las tablas de snapshot se acumulan por `generated_at` y no se pueden
reconstruir después — lo que no se subió el día que corrió, se pierde. Salvo
que esté en git, que es exactamente el caso.

Medido antes de decidir nada, sobre los 297 commits que tocaron el snapshot:

- **225 corridas distintas**, del 23-may al 18-ago. Hoy en BigQuery: 19.
- El exportador de hoy parsea **297/297** snapshots viejos sin una sola falla.
- **225/225 tienen los cuatro cinturones vigentes**, así que la vista
  `corridas_comparables` de [[0207-la-serie-comparable-es-una-vista-no-un-backfill]]
  las cubre enteras sin tocar una línea de su SQL.
- De las 225, sólo **71 son del cron**. Las otras 154 son republicaciones a
  mano y regeneraciones de desarrollo; julio solo tiene 24 del cron contra 116
  manuales.

## Factores de decisión

- El archivo tiene que decir qué se publicó cada día. No es un modelo de la
  realidad: es el registro de lo que salió al aire.
- Una corrida de desarrollo y una del nocturno no son el mismo hecho, aunque
  las dos hayan estado en producción.
- El backfill no puede degradar lo que ya está bien en BigQuery.
- BigQuery sigue siendo aguas abajo: nada de esto puede convertirse en una vía
  para que el pipeline lea de BQ.

## Opciones consideradas

1. **No rellenar.** El archivo arranca en agosto y se acepta.
2. **Rellenar sólo las 71 corridas del cron.** Serie diaria limpia.
3. **Rellenar las 225 sin distinguir.** Fiel, pero julio parece un mes de
   saltos violentos del dato que en realidad son iteraciones de código.
4. **Rellenar las 225 con una columna `origen`.**
5. **Recalcular la historia con el motor de scoring de hoy.** El "backfill
   corregido" en su versión fuerte.

## Decisión

### 1. Entran las 225, con `origen`

`scripts/bigquery_backfill.py` reconstruye cada corrida desde git y escribe
`origen` en `corridas`: `'cron'` si el commit es de `github-actions[bot]`,
`'manual'` si no. El exportador nocturno también la escribe, deducida de la
variable `GITHUB_ACTIONS`.

Es la opción 4. La 3 hace que el archivo mienta por omisión —no distingue un
día de dato de una tarde de desarrollo— y la 2 tira publicaciones que
estuvieron en producción de verdad. Con la columna, el archivo queda completo y
quien consulta filtra.

### 2. Se rellena el archivo, NO se recalcula la historia

La opción 5 queda descartada, y es la parte que más importa dejar escrita.

La vista comparable corrige el **perímetro** —qué cinturones se promedian—, no
la **metodología**. Entre mayo y agosto hubo recalibraciones de bandas, cuatro
indicadores de gestión pasaron de cualitativos a numéricos (2-jul), entró
`desequilibrio_monetario` al ITCM (11-ago), pobreza al ITVC (30-jul) y se
corrigió el numerador del ITCG (9-ago).

**Un score de junio backfilleado es "lo que publicamos en junio", no "junio
medido con la vara de hoy".** Lo segundo exigiría re-correr el motor actual
sobre los datos crudos de cada fecha, y varios colectores no versionan crudo
por fecha: no hay con qué. Esta decisión continúa la de
[[0207-la-serie-comparable-es-una-vista-no-un-backfill]] en vez de
contradecirla — aquel ADR rechazó backfillear *scores recalculados*; este
rellena *corridas archivadas*, que es otra cosa.

### 3. `series` queda afuera del backfill

`series` se escribe con `WRITE_TRUNCATE` porque el CSV es la verdad y acumular
versiones duplicaría. Replayar corridas viejas la **pisaría** con las series de
junio. La tabla de hoy ya está bien y el backfill no la toca.

### 4. El valor textual va a `valor_txt`

Hasta el 2-jul-2026, `privatizaciones`, `concesiones_infraestructura`,
`fal_modernizacion_laboral` y `rigi_inversiones` eran cualitativos: su `valor`
era una frase (`'Parcial — corredores viales en licitación'`). La columna
`valor` es FLOAT, así que esas **175 filas** rompen el load. En vez de
tirarlas, el texto va a `valor_txt` y `valor` queda NULL: el indicador sigue en
el archivo, con su valor legible, y las consultas numéricas no lo ven.

### 5. Los auxiliares se leen por commit, no del working tree

`bigquery_export.py` lee `output/*.json` desde `RAIZ`. Si el backfill sólo
restaurara el snapshot, las correlaciones de **hoy** quedarían estampadas con
un `generated_at` de junio: no falla nada, no lo agarra ningún gate, y el
archivo queda mintiendo. Por eso `construir_filas` y `construir_filas_analisis`
aceptan `raiz`, y el backfill materializa de cada commit los seis archivos que
el exportador abre.

Se materializan seis blobs en vez de hacer `git worktree` por commit: la
fidelidad es la misma —son exactamente los inputs— y evita 225 checkouts
completos del árbol.

### Consecuencias

- El archivo pasa de 19 a 225 corridas, del 23-may al 18-ago: **212.956 filas**
  en 19 tablas.
- `corridas.origen` y `indicadores.valor_txt` son columnas nuevas. Se agregan
  con `ALLOW_FIELD_ADDITION`; las filas viejas quedan en NULL hasta que el
  backfill las reescribe, cosa que hace porque también están en git.
- Toda consulta de serie temporal sobre `corridas` **debería filtrar por
  `origen = 'cron'`** si lo que busca es la evolución del dato y no el registro
  de publicaciones.
- Los auxiliares tienen menos historia que el núcleo, y es dato faltante real,
  no una falla: `validacion_externa` existe desde el 3-jul, `revision_bandas`
  desde el 18-jul, `out_of_sample` y `procedencia_anclas` desde el 20-jul.
- El backfill es idempotente: borra las corridas que va a escribir antes de
  escribirlas. Re-correrlo no duplica.
- Quedan **226** corridas, no 225: la del `2026-08-15T16:40:04Z` estaba en
  BigQuery y **no está en git**. Fue una corrida local que se exportó y que diez
  minutos después quedó superada por la que sí se commiteó (`cae525b`). No se
  puede reconstruir, así que el backfill no la toca; se le puso
  `origen = 'manual'` con un UPDATE puntual. La evidencia es concluyente: el
  cron sólo dispara a las ~03:xx UTC y el bot siempre commitea lo que exporta.
  Si vuelve a aparecer una corrida archivada sin contraparte en git, es la misma
  situación —exportar a mano y después re-correr antes de commitear— y se
  resuelve igual.

### Confirmación

`tests/test_bigquery_backfill.py` cubre el reparto valor/`valor_txt`, que
`origen` sale de la variable de entorno, que `series` queda excluida y que
`raiz` redirige de verdad la lectura de los auxiliares. La corrida real se
verifica contra `corridas_comparables`, que tiene que devolver las 225 filas
sin ninguna con menos de cuatro cinturones.

## Pros y contras de las opciones

- **No rellenar**: gratis; tira 206 corridas que existen.
- **Sólo el cron**: serie limpia; pierde publicaciones que estuvieron al aire.
- **225 sin distinguir**: fiel al byte; ilegible como serie.
- **225 con `origen`** (elegida): completo y filtrable; cuesta una columna.
- **Recalcular la historia**: sería lo ideal; no hay datos crudos versionados
  por fecha para hacerlo, y borraría el registro de lo que se publicó.

## Más información

- [[0180-integracion-con-la-plataforma-google]] — el espejo en BigQuery.
- [[0205-espiritu-de-epoca-sale-del-tablero]] — el cambio de perímetro.
- [[0207-la-serie-comparable-es-una-vista-no-un-backfill]] — la vista que hace
  legible la serie a través de ese cambio.
