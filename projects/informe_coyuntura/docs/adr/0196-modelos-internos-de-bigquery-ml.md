---
madr: 4
id: '0196'
estado: 'aceptado'
fecha: 2026-08-12
cinturon: 'transversal'
parametros: ['MIN_PUNTOS_MENSUAL', 'MESES_ALERTA', 'SERIES_DIARIAS']
archivos: ['scripts/bq_ml.py', 'scripts/bigquery_export.py', '.gitignore']
relacionado: ['0180', '0198']
ambito: 'Herramientas internas de análisis sobre el archivo de BigQuery — no alimentan el snapshot ni la web'
origen: 'Pregunta del usuario sobre qué se podía hacer con ML predictivo en BigQuery, con el pedido explícito de que fueran herramientas internas y no algo para mostrar'
---

# ADR-0196 — Modelos internos de BigQuery ML: dos que quedan, uno que se descarta medido

## Contexto y planteo del problema

Desde ADR-0180 cada corrida del informe se espeja en BigQuery, así que ya hay un
archivo histórico consultable: 98 series, los índices mensuales reconstruidos y
la foto de cada corrida. La pregunta era qué se puede sacar de ahí con BigQuery
ML **para uso interno** —control de calidad, anticipación operativa— sin que
nada de eso entre al snapshot ni a la web.

La restricción real no es de herramientas sino de datos. El archivo tiene 98
series pero la **mediana es de 33 puntos mensuales**, y la propia validación
cruzada del informe ya documenta que en una muestra de unos treinta meses casi
todas las series argentinas comparten la tendencia del período. Con eso,
cualquier modelo que busque estructura *entre* indicadores va a encontrar
correlación espuria y a reportarla como hallazgo.

### Cómo apareció

Se construyeron tres tareas y se midieron. Dos funcionan. La tercera —un
nowcast del ITCM con los cuatro indicadores diarios del BCRA— falló dos veces
por motivos distintos, y la segunda falla es la que importa:

1. La primera versión daba `r2 = −0.0`. Estaba entrenada contra la tabla
   `cinturones`, que es la **foto de la corrida** (un mes por corrida, 35 filas),
   no la historia. Con un solo valor de label ningún modelo puede dar otra cosa.
   La historia mensual de los índices está en `series_indices` (31 meses de ITCM).
2. Corregida la tabla y medida contra un holdout **secuencial**, empeoró.

## Factores de decisión

- **Un modelo interno igual tiene autoridad.** "Lo dice el modelo" pesa en una
  discusión aunque el modelo no se publique. Un nowcast malo no es inocuo.
- **La evaluación tiene que ser secuencial, no aleatoria.** Con series en
  tendencia, un split al azar entrena con meses posteriores a los que evalúa e
  infla el r² hasta que parece que funciona.
- **Un modelo se compara contra la alternativa tonta**, no contra cero.
- La brecha que hay que cubrir es de **plausibilidad del dato**:
  `gate_calidad.py` mira estructura, frescura y card-contra-serie, pero un PDF
  mal parseado con un dígito de más pasa el gate entero.

## Opciones consideradas

- **A. Las tres tareas** (anomalías, nowcast, forecast).
- **B. Anomalías y forecast; el nowcast se descarta y se documenta la medición.**
- **C. Dejar el nowcast marcado como experimental**, con una advertencia.
- **D. Nada de ML** hasta tener más historia mensual.

## Decisión

**Opción B.** Quedan dos tareas en `scripts/bq_ml.py`:

- **`anomalias`** — un `ARIMA_PLUS` con `time_series_id_col` sobre las series con
  ≥24 puntos mensuales, `clean_spikes_and_dips = FALSE` (queremos ver los picos,
  no suavizarlos) y `ML.DETECT_ANOMALIES` al 0,99. El umbral es exigente a
  propósito: esto tiene que avisar de un dígito mal leído, no opinar sobre si un
  mes fue bueno o malo. La salida se parte en **`recientes`** (últimos 4 meses,
  accionables) e **`historicas`**: sin ese corte, la primera corrida devolvía 118
  anomalías de las cuales 113 eran shocks conocidos —la devaluación de diciembre
  de 2023 aparece en media docena de series— y la alerta quedaba ilegible.
- **`forecast`** — `ARIMA_PLUS` a 30 días sobre las cuatro series diarias del
  BCRA (~635 puntos cada una), con intervalos al 90%. Son las únicas series del
  archivo con historia suficiente para que el intervalo signifique algo.

**El nowcast se descarta**, con la medición registrada en el docstring del
módulo para que no se reconstruya de memoria. Holdout secuencial de los últimos
8 meses, sobre un ITCM que en esa ventana se mueve entre 57 y 66:

| | MAE | r² |
|---|---|---|
| variaciones + niveles → ITCM | 12,33 | −18,9 |
| sólo variaciones → ITCM | 7,69 | −7,3 |
| ingenuo: repetir el mes anterior | **3,75** | |
| ingenuo: predecir la media del holdout | **2,65** | |

Pierde dos a tres veces contra las dos referencias más tontas que existen. No es
un modelo flojo: es peor que no hacer nada. Con ~30 filas mensuales y features
en tendencia no hay versión de esto que funcione — falta historia mensual del
índice, no otro algoritmo.

Las salidas van a `output/bq_ml/` y **ese directorio se ignora en git**. El resto
de `output/` se versiona a propósito porque es el rastro de auditoría de lo que
se publicó; esto no alimenta el snapshot, no sale en la web y no es lo que se
publicó. El archivo de verdad de estas corridas son los modelos en BigQuery.

### Consecuencias

- Aparece un control de plausibilidad que el gate no tenía, con volumen operable
  (5 anomalías recientes en la corrida del 2026-08-12, todas leves).
- Queda un pronóstico a 30 días de tipo de cambio y tasa, para uso interno.
- **No** hay lectura anticipada del ITCM, y queda escrito por qué, con números.
- `bq_ml.py` no corre en el pipeline nocturno: se invoca a mano. Correrlo no
  altera ningún artefacto publicado.

### Confirmación

- `python scripts/bq_ml.py --todo` termina en 0 y escribe `anomalias.json`,
  `forecast.json` y `resumen.json`.
- `--dry-run` imprime el SQL sin tocar BigQuery ni pedir credenciales.
- Ningún archivo de `web/src/data/` ni de `output/` versionado cambia al correrlo.

## Pros y contras de las opciones

- **A. Las tres.** Bueno: cubre el caso de uso más atractivo, leer el mes antes
  de que llegue INDEC. Malo: ese caso de uso está medido y no funciona; el
  número saldría igual, con cara de estimación, en una discusión real.
- **B. Dos y la medición del descarte.** Bueno: sólo queda lo que se verificó, y
  el fracaso queda documentado con los números para que se pueda reintentar
  cuando haya más historia. Malo: no se cubre la necesidad de anticipación.
- **C. Experimental con advertencia.** Bueno: no se pierde el trabajo. Malo: la
  advertencia se lee una vez y el número se copia muchas; es la misma dinámica
  que el documento del ICC, que avisaba que sus cifras eran de relleno y estaba
  redactado como hallazgo.
- **D. Nada.** Bueno: cero riesgo. Malo: deja sin cubrir el hueco de
  plausibilidad, que es real y ya existe.

## Más información

- ADR-0180 — el espejo en BigQuery que hace posible todo esto.
- Un hallazgo lateral: `bigquery_export.py` sólo aceptaba
  `GOOGLE_APPLICATION_CREDENTIALS` e ignoraba el ADC de gcloud, así que en local
  salía por 2 sin subir nada. En Windows el ADC vive en `%APPDATA%\gcloud`, no en
  `~/.config/gcloud`. Ahora acepta las dos vías y, si falla, imprime el error
  como **última línea** para que sobreviva a un `| tail`.
