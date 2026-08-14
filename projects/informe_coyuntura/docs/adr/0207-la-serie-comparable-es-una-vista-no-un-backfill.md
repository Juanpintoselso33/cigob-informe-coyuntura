---
madr: 4
id: '0207'
estado: 'aceptado'
fecha: 2026-08-14
cinturon: 'transversal'
archivos: ['scripts/bq_vista_comparable.py']
relacionado: ['0180', '0205']
ambito: 'Archivo histórico en BigQuery · lectura del score global a través de un cambio de perímetro'
origen: 'Sacar espíritu de época dejó la columna score_global de `corridas` sin poder leerse de corrido'
---

# ADR-0207 — La serie comparable es una vista, no un backfill

## Contexto y planteo del problema

[[0205-espiritu-de-epoca-sale-del-tablero]] cambió el perímetro del informe de
cinco cinturones a cuatro. El `score_global` publicado saltó de 3,5 a 4,2 ese
día, y ese salto **no es coyuntura**: es que se dejó de promediar el cinturón
más bajo del tablero.

El archivo en BigQuery ([[0180-integracion-con-la-plataforma-google]]) acumula
una fila por corrida en `corridas`. Las de antes del cambio llevan un global de
cinco cinturones y las de después uno de cuatro, así que **la columna no se
puede leer de corrido**: un gráfico de la serie muestra un escalón que nadie
vivió.

Al 2026-08-14 son 13 corridas, todas de agosto de 2026 — el archivo tiene nueve
días y no hay comparación entre meses todavía. El problema es chico hoy y crece
solo.

## Factores de decisión

- El archivo tiene que seguir diciendo qué se publicó cada día: es su trabajo.
- Los pesos no pueden tener un segundo dueño.
- `bigquery_export.py` declara que BigQuery es aguas abajo y de una sola
  dirección, y que el pipeline nunca lee de BQ. Eso existe para que ningún
  camino paralelo esquive los gates G1-G7.

## Opciones consideradas

- **Una vista que recalcula el global sobre el perímetro vigente** — elegida.
- **Backfill: reescribir `score_global` en las filas viejas.** Descartada:
  destruye lo que efectivamente se publicó cada día. Un archivo que se reescribe
  para que la serie quede linda deja de ser archivo.
- **Una columna nueva materializada en `corridas`.** Descartada: obliga a un
  backfill igual y a que el export lea de BQ para saber qué falta rellenar,
  contra la regla de una sola dirección.
- **Documentar el quiebre y no hacer nada.** Descartada: la nota no aparece al
  lado del gráfico que alguien va a mirar.

## Decisión

### 1. `corridas_comparables`, una vista al lado del archivo

`scripts/bq_vista_comparable.py` crea la vista. Para cada corrida archivada
recalcula el global usando **sólo** los cinturones que hoy tienen peso, y
publica las dos lecturas juntas: `score_global_archivado` (lo que se publicó
ese día), `score_global_comparable` y el `delta`.

El recorte lo hace el `JOIN` contra una CTE de pesos: un cinturón que no está
en esa lista queda afuera del promedio. Por eso sacar otro cinturón mañana no
pide tocar el SQL — sólo volver a correr el script.

### 2. Los pesos siguen teniendo un solo dueño

El SQL se **genera** desde `config.PESOS_CINTURONES`. No hay pesos escritos a
mano en la vista, igual que no hay cortes de semáforo escritos en el front. Si
cambian los pesos o el conjunto de cinturones, se vuelve a correr el script y
la vista se redefine.

Es de corrida manual, no del pipeline nocturno: redefinir una vista cada noche
es ruido, y hacerlo desde el export obligaría a que lea de BigQuery.

### 3. El archivo no se toca

`corridas` y `cinturones` quedan exactamente como están.

### Consecuencias

- La serie de agosto de 2026 se lee de corrido: **4,0 → 4,2**, sube apenas y
  sin escalón. El "salto" de 3,5 a 4,2 desaparece en base comparable, que es
  la confirmación de que era perímetro y no coyuntura.
- Cualquier consumidor que grafique la serie tiene que usar la vista; la tabla
  cruda sigue siendo correcta para "qué decía el informe tal día".
- La vista queda desactualizada si cambian los pesos y nadie la regenera. No
  hay test que lo agarre: vive en BigQuery, fuera del alcance de la suite.

### Confirmación

- Corrida del 2026-08-14: 13 filas, delta +0,6/+0,7 en las doce de cinco
  cinturones y 0,0 en la primera de cuatro, que es lo que tiene que dar.

## Pros y contras de las opciones

**Vista generada desde config** (elegida)

- Bueno, porque no destruye el archivo y no duplica los pesos.
- Bueno, porque respeta la regla de una sola dirección hacia BigQuery.
- Malo, porque hay que acordarse de regenerarla si cambian los pesos.

**Backfill de la columna**

- Bueno, porque la serie queda comparable sin que nadie elija una vista.
- Malo, porque reescribe lo que se publicó y rompe la única copia de eso.

## Más información

- La vista lleva su propia `description` en BigQuery, con el puntero a este ADR
  y el aviso de que se genera y no se edita a mano.
