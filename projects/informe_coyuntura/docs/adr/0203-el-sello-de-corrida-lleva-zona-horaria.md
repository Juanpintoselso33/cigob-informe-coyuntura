---
madr: 4
id: '0203'
estado: 'aceptado'
fecha: 2026-08-14
cinturon: 'transversal'
archivos: ['scripts/generar_informe.py', 'scripts/validacion_externa.py', 'scripts/verificacion_pdf.py', 'scripts/bq_ml.py', 'tests/test_sellos_de_corrida.py']
relacionado: ['0180']
ambito: 'Sello de corrida del archivo histórico en BigQuery'
origen: 'Al correr bigquery_export.py a mano desde la Mac, la fila quedó archivada 3 horas adelantada'
---

# ADR-0203 — El sello de corrida lleva zona horaria

## Contexto y planteo del problema

`generated_at` es la clave de corrida del archivo histórico ([[0180-integracion-con-la-plataforma-google]]).
Se escribía así:

```python
now = datetime.now()          # naive: hora de pared, sin zona
...
"generated_at": now.isoformat()   # '2026-08-14T09:19:37.870713'
```

**BigQuery lee un timestamp sin offset como UTC.** En la CI eso salía bien por
casualidad —el runner de GitHub corre en UTC, así que `datetime.now()` *es*
UTC— pero cualquier corrida hecha desde una máquina en ART queda **3 horas
adelantada** en el archivo, y nada falla: la fila entra, mal fechada.

Medido el 2026-08-14 sobre el dataset:

| Tabla | Corridas | Estado |
|---|---:|---|
| `corridas` | 11 | 8 de CI correctas · **3 manuales desplazadas +3h** |
| `verificacion_pdf`, `panel_ml_*` | todas manuales | **todas desplazadas** |

No es cosmético. Tiene dos consecuencias reales:

1. **`panel_ml.py` elige la corrida vigente con `MAX(generated_at)`.** Con
   sellos mezclados, una corrida local puede ganarle a una de CI posterior, y
   el panel muestra resultados viejos como si fueran los últimos.
2. **El orden se invierte en una ventana concreta.** Una corrida manual entre
   00:00 y 03:00 ART se archiva como 00-03 UTC del mismo día, cuando en verdad
   ocurrió 03-06 UTC: *después* de la nocturna de ese día, no antes. Ese horario
   no es hipotético — la corrida de la noche del 13-08 fue a las 23:17.

## Factores de decisión

- El reloj de pared que ve una persona no puede cambiar: `generated_at` se
  muestra en la web y en las fichas.
- No hardcodear la zona: el mismo código corre en la CI (UTC) y en máquinas en
  ART.
- Sin dependencias nuevas.
- Los sellos que se comparan entre sí tienen que migrar juntos.

## Opciones consideradas

- **A. `datetime.now().astimezone()`** en los sellos que llegan a BigQuery.
- **B. `datetime.now(timezone.utc)`**: pasar todo a UTC.
- **C. Convertir en `bigquery_export.py`**, interpretando el sello naive como
  ART.
- **D. Dejarlo** y documentar que el archivo está en «hora de la máquina».

## Decisión

**Opción A.** Los cuatro sitios que producen un sello que termina siendo clave
de corrida en BigQuery pasan a `datetime.now().astimezone()`:

| Archivo | Qué sella |
|---|---|
| `generar_informe.py` | `generated_at` del snapshot — la clave de corrida |
| `validacion_externa.py` | `_meta.generated_at`, que el test de frescura resta contra el anterior |
| `verificacion_pdf.py` | la corrida de `verificacion_pdf` |
| `bq_ml.py` | `resumen["generado"]`, la corrida de las tablas `panel_ml_*` |

`.astimezone()` sella con el offset **de la máquina que corre**: `-03:00` acá,
`+00:00` en el runner. Los dos correctos, sin zona hardcodeada.

**El reloj de pared no cambia**, que es lo que vuelve barato el cambio: el
offset se agrega al final, así que los primeros 19 caracteres son idénticos a
los de antes. De eso dependen todos los consumidores, y se revisaron los nueve:
`[:10]` en `fichas/generar.py`, `[:19]` en `generar_informe.py`, y
`.slice(0, 10)` / `slice(8, 10)` en Hero, Footer, frontada y la ficha web.

```
antes: 2026-08-14T12:46:17.665898
ahora: 2026-08-14T12:46:17.665902-03:00
       └────── idéntico hasta acá ──────┘
```

Verificado contra BigQuery antes de tocar nada:
`TIMESTAMP("2026-08-14T09:19:37.870713-03:00")` → `12:19:37 UTC`, exactamente
las 3 horas que faltaban.

### Lo que NO se toca

Los sellos de cache de los colectores (`obtenido_en`, y el `generated_at` de
`output/cache/*.json`) siguen naive. No llegan a BigQuery, y el único que los
lee es `gate_calidad.py`, que hace `fromisoformat(sello).date()` — que funciona
igual con o sin zona. Cambiarlos agregaría superficie de riesgo al nocturno sin
arreglar nada.

### Consecuencias

- **Las 3 corridas ya archivadas quedan desplazadas.** Corregirlas es un UPDATE
  sobre ~20 tablas y reescribe filas históricas; se decidió no hacerlo. El corte
  es este ADR: las corridas anteriores al 2026-08-14 llevan hora de la máquina
  etiquetada como UTC, las posteriores llevan el instante real.
- La migración se completa recién con la próxima corrida del pipeline, que es
  la que regenera los dos sellos que se comparan entre sí. Hasta entonces los
  dos siguen naive, que es consistente y no rompe nada.
- `panel_ml.py` deja de poder elegir una corrida vieja como vigente.

### Confirmación

`tests/test_sellos_de_corrida.py`, con tres cosas:

1. Que los cuatro sitios sigan usando `.astimezone()`.
2. Que el prefijo de 19 caracteres siga siendo `YYYY-MM-DDTHH:MM:SS` — es el
   contrato con todos los consumidores que cortan el string.
3. Que el sello del snapshot y el de `validacion_externa` **no se separen**. Es
   el filo del cambio: el test de frescura los resta, y aware menos naive es
   `TypeError`. Una migración a medias no falla en el sello, falla en otro test
   con un mensaje que no menciona zonas horarias.

## Pros y contras de las opciones

- **A. `.astimezone()`.** A favor: correcto en las dos máquinas sin
  configuración, no cambia el reloj de pared y por eso no toca ningún
  consumidor. En contra: el sello ahora tiene dos formas posibles según dónde
  corra, y hay que leerlo como instante y no como texto.
- **B. Todo en UTC.** A favor: una sola forma, sin ambigüedad. En contra:
  cambia la fecha que ve el lector para toda corrida entre 21:00 y 24:00 ART
  —la web mostraría el día siguiente— y eso es un cambio de producto disfrazado
  de arreglo técnico.
- **C. Convertir en el export.** A favor: un solo archivo. En contra: el export
  no sabe en qué máquina se generó el snapshot, así que tendría que adivinar; y
  en la CI la conversión sería incorrecta.
- **D. Dejarlo.** A favor: cero riesgo. En contra: el archivo histórico existe
  justamente para tener el orden de las corridas, y el `MAX()` del panel ML ya
  puede equivocarse hoy.

## Más información

- El bug apareció al correr `bigquery_export.py` a mano por primera vez desde la
  Mac. Con el pipeline corriendo sólo en la CI era invisible.
- La ventana de inversión de orden (00:00–03:00 ART) es angosta pero es
  exactamente el horario en que se hacen las corridas manuales tarde.
