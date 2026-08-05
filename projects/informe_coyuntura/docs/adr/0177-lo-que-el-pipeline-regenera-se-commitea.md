---
madr: 4
id: '0177'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['.github/workflows/data-pipeline.yml', 'scripts/validacion_externa.py']
continua: ['0176']
relacionado: ['0159']
continuado_por: ['0178']
ambito: 'Pipeline nocturno · salidas versionadas'
origen: 'G7 pasó en CI pero el panel_anclas nunca apareció en el archivo commiteado'
---

# ADR-0177 — Lo que el pipeline regenera, se commitea

## Contexto y planteo del problema

La corrida que estrenó G7 (ADR-0176) pasó el gate sin una sola falla, y sin
embargo el `output/validacion_externa.json` de `main` **no tenía el campo
`panel_anclas`** que G7 verifica. Las dos cosas sólo podían ser ciertas a la vez
de una manera: el runner generó el archivo bien, el gate lo leyó bien, y el paso
de commit no lo subió.

`output/validacion_externa.json` está **trackeado** pero no figuraba en la lista
de `git add` del workflow. Su último commit era del **31-jul-2026, hecho a
mano**, mientras `output/sensibilidad.json` —que sí está en la lista— lo venía
commiteando el bot todos los días.

O sea: el pipeline lo recalculaba cada noche, `publicar.py` le sacaba las
correlaciones para embeberlas en el snapshot, y después se descartaba. Lo mismo
con `output/informe.json`, que escribe `generar_informe.py` en cada corrida.

**La consecuencia estuvo a la vista todo el día y se leyó mal.**
`tests/test_redundancia_itvc.py` fallaba con:

> `itcp: la matriz publicada mide 103 pares y la reconstrucción da 104: falta
> correr validacion_externa.py`

y se descartó una y otra vez como "staleness que resuelve la próxima corrida del
pipeline". No la resolvía nunca: la corrida recalculaba la matriz y tiraba el
resultado. El test decía la verdad —faltaba correr validacion_externa— y lo que
faltaba en realidad era **guardar** lo que ya se corría.

## Factores de decisión

- Un archivo versionado que el pipeline regenera y no commitea es peor que uno
  no versionado: aparenta ser el estado actual y es una foto vieja.
- El síntoma tardó cinco días en interpretarse bien porque el test culpaba a la
  causa equivocada, y la explicación cómoda ("ya se va a arreglar solo") era
  compatible con lo observado.
- No todas las salidas de `output/` son nocturnas. `out_of_sample.json`,
  `revision_bandas.json`, `interpolacion_sombra.json` y `procedencia_anclas.json`
  son análisis manuales y su antigüedad es legítima: meterlas en el `git add`
  del cron sería ruido.

## Opciones consideradas

- **Sumar las dos salidas nocturnas al `git add` y ponerles un test que lo
  vigile** — elegida.
- **`git add output/*.json` completo** — descartada: barre también las salidas
  manuales, cuya antigüedad es correcta, y las haría aparecer como cambiadas por
  el bot sin que nadie las hubiera regenerado.
- **Dejar de versionar `validacion_externa.json`** — descartada: es el insumo de
  la matriz de redundancia y de G7, y hay tests que lo leen del repo.

## Decisión

### 1. Las dos salidas nocturnas entran al `git add` del workflow

`output/informe.json` y `output/validacion_externa.json`, junto a
`sensibilidad.json` que ya estaba.

### 2. `validacion_externa.json` lleva sello de tiempo

`_meta.generated_at`. Sin sello no había forma de notar desde afuera que dejó de
commitearse — `output/informe.json` sí lo tenía, y por eso su atraso se pudo
medir de una.

### 3. Dos tests, uno sobre la intención y otro sobre la evidencia

`tests/test_salidas_versionadas_frescas.py`:

- que cada salida regenerada esté en el `git add` del workflow (mira el YAML);
- que la copia versionada no quede más de 3 días atrás del snapshot publicado
  (mira los sellos de tiempo). El segundo es el que importa: sigue valiendo
  aunque alguien reorganice el workflow, porque no le cree a la lista sino al
  archivo.

### Consecuencias

- La matriz de redundancia deja de estar cinco días atrás y
  `test_redundancia_itvc` deja de fallar por una causa que no era la que decía.
- `panel_anclas` llega efectivamente a `main`, que es lo que hace verificable a
  G7 fuera del runner.

### Confirmación

Después de la primera corrida con este cambio, `output/informe.json` y
`output/validacion_externa.json` tienen que aparecer en el commit del bot, y
`test_salidas_versionadas_frescas.py` en verde.

## Más información

### Limitaciones

- **`REGENERADAS` es una lista a mano.** Una salida nocturna nueva que nadie
  agregue ahí repite el problema exacto de este ADR. No hay forma automática de
  saber qué escribe cada script sin ejecutarlo: mencionar el archivo no
  distingue leerlo de escribirlo, y varios scripts hacen ambas cosas.
- La tolerancia de 3 días es una convención para aguantar un fin de semana con
  el cron caído. Un archivo que se dejara de commitear un lunes tarda hasta el
  jueves en delatarse.
- Los cuatro archivos de análisis manual siguen sin nadie que mire si envejecen
  más de lo razonable. Es deliberado —no tienen cadencia— pero significa que un
  análisis abandonado se ve igual que uno vigente.
