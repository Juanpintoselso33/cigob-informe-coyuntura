"""Modelos de BigQuery ML sobre el archivo del informe. Uso INTERNO.

No alimentan el snapshot ni la web: escriben a `output/bq_ml/` y se leen a mano
o desde CI. La razón es deliberada — un pronóstico no es un dato publicado, y
mezclarlo con los indicadores del informe borraría esa diferencia justo donde
más importa.

## Qué hay y por qué

El archivo tiene 98 series pero la MEDIANA es de 33 puntos mensuales, y la
propia validación cruzada del informe ya documenta que "en una muestra de unos
treinta meses casi todas las series argentinas comparten la tendencia del
período". Con eso, cualquier modelo que busque estructura ENTRE indicadores va a
encontrar correlación espuria. Así que acá sólo hay modelos que no dependen de
eso:

  anomalias  Detecta valores que no pegan con la historia de SU PROPIA serie.
             Se construyó como control de calidad de datos, para cubrir el hueco
             que deja `gate_calidad.py` —que mira estructura y frescura, no
             plausibilidad—. **Leer abajo qué resultó ser en la práctica antes
             de confiar en él para eso.**

  forecast   Pronóstico sobre las series DIARIAS (tc_mayorista, badlar y las
             otras dos del BCRA, ~635 puntos cada una). Son las únicas con datos
             suficientes para un ARIMA con estacionalidad e intervalos que
             signifiquen algo.

## El detector de anomalías encuentra eventos, no errores (auditado 2026-08-12)

Se revisaron **las 118 anomalías** que devuelve sobre la historia completa,
clasificándolas por forma: un dígito mal leído es un **PICO** —al mes siguiente
la fuente se lee bien y la serie vuelve—, mientras que un cambio real de política
es un **ESCALÓN**: salta y se queda.

    escalón (salta y se queda)   75
    pico (se va y vuelve)        12
    parcial                      11
    sin serie con qué comparar   19

Y las 12 de forma pico se miraron una por una: `ipc_alimentos` 2023-12 (29,7 —
la devaluación de diciembre), `alquiler_real` 2024-04, `protestas_caba` en tres
meses distintos, `pluriempleo` 2020-04 (la cuarentena), `icg_utdt` 2002-06.
**Todas son eventos reales. Ninguna es un error de dato.**

O sea: en toda la historia del proyecto este detector encontró **cero** de lo que
se construyó para encontrar, y 118 de algo que el informe ya publica por diseño.
En este dataset un valor estadísticamente raro es señal, no ruido — es la
naturaleza de las series argentinas del período, no un defecto del modelo.

Sirve igual, con la expectativa corregida: la salida se parte por forma y
`revisar` trae sólo lo reciente CON forma de error de lectura, que baja el
volumen unas diez veces. Pero el instrumento correcto para calidad de dato es
`verificacion_pdf.py` (ADR-0198), que compara contra el documento de origen en
vez de contra la propia serie. Un error de columna que cae dentro del rango
histórico —el caso peligroso— es invisible acá y evidente allá.

## Lo que NO está, a propósito

Clasificar `alerta_multicinturon` (33 meses, cero casos positivos), importancia
de variables entre indicadores (la colinealidad del período la arruina) y
clustering de meses en regímenes (con 33 puntos es descriptivo, no predictivo).

**Y el nowcast del ITCM, que se construyó y se midió mal** (2026-08-12, ADR-0196).
La idea era estimar el índice del mes con los cuatro indicadores diarios del
BCRA, antes de que llegaran los lentos. Medido contra un holdout SECUENCIAL —los
últimos 8 meses, que es la única pregunta que importa— pierde contra las dos
referencias más tontas que existen:

    variaciones + niveles → ITCM         MAE 12,33   (r2 −18,9)
    sólo variaciones → ITCM              MAE  7,69   (r2  −7,3)
    ingenuo: repetir el mes anterior     MAE  3,75
    ingenuo: predecir la media           MAE  2,65

Sobre un índice que en esa ventana se mueve entre 57 y 66. No es un modelo
flojo: es peor que no hacer nada, y publicarlo como herramienta interna sería
darle autoridad de modelo a algo que degrada la lectura. Con ~30 filas
mensuales y features en tendencia no hay versión de esto que funcione; haría
falta más historia mensual del índice, no otro algoritmo.

Antes de reintentarlo: la primera versión daba `r2 −0.0` porque entrenaba
contra `cinturones`, que es la FOTO de la corrida (un mes por corrida, 35 filas)
y no la historia. La historia mensual de los índices está en `series_indices`.

**Y TimesFM (`AI.FORECAST`), evaluado y no adoptado** (2026-08-12). Está
disponible en `southamerica-east1` y funciona con nuestros datos —su ventana de
contexto mínima es 64, así que acepta series de 31 puntos, y al ser zero-shot no
necesita entrenarlas—. Backtest ocultando los últimos 6 meses de las 87 series
mensuales con ≥24 puntos:

    le gana a repetir el último valor en 48/87 series (55%), mediana de mejora 3%

Se probaron dos criterios para aislar dónde sí sirve, medidos sólo con datos de
entrenamiento, y los dos fallaron: separar por "series que se mueven" da 57% vs
55%, y separar por direccionalidad da 47% en las que están en tendencia contra
62% en las que oscilan — al revés de lo esperado. Hay triunfos grandes sueltos
(credito_privado 20×, ipc_nivel 15×) pero sin regla para anticiparlos, y
reportarlos sin la regla sería elegir los casos que convienen.

En las DIARIAS, contra el ARIMA_PLUS que corre acá abajo (holdout de 30 días):
gana en badlar y base_monetaria, pierde en prestamos_privados, y en
tc_mayorista le gana el baseline ingenuo a los dos. No hay motivo para cambiar.

Uso:
    python scripts/bq_ml.py anomalias
    python scripts/bq_ml.py --todo
    python scripts/bq_ml.py anomalias --dry-run     # imprime el SQL y sale
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "output" / "bq_ml"

PROYECTO_POR_DEFECTO = "cigob-analytics"
DATASET_POR_DEFECTO = "informe_coyuntura"
UBICACION = "southamerica-east1"

# Mínimo de puntos para que un ARIMA mensual signifique algo. Con menos, el
# modelo entrena igual y devuelve intervalos de confianza que son decorativos.
MIN_PUNTOS_MENSUAL = 24
# Las series del BCRA que se publican todos los días.
SERIES_DIARIAS = ("tc_mayorista", "badlar", "prestamos_privados", "base_monetaria")


def sql_anomalias(ds: str) -> list[tuple[str, str]]:
    """Un solo ARIMA_PLUS para las 98 series, con `time_series_id_col`.

    Se entrena sobre la serie entera y se pregunta por los últimos puntos. El
    umbral 0,99 es deliberadamente exigente: esto tiene que avisar de un dígito
    mal leído, no opinar sobre si un mes fue bueno o malo.
    """
    return [
        ("modelo", f"""
CREATE OR REPLACE MODEL `{ds}.ml_anomalias_series`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'fecha',
  time_series_data_col = 'valor',
  time_series_id_col = 'indicador',
  auto_arima = TRUE,
  data_frequency = 'MONTHLY',
  clean_spikes_and_dips = FALSE   -- justamente queremos VER los picos
) AS
SELECT DATE(fecha) AS fecha, indicador, valor
FROM `{ds}.series`
WHERE valor IS NOT NULL
  AND indicador IN (
    SELECT indicador FROM `{ds}.series`
    WHERE valor IS NOT NULL
    GROUP BY indicador
    HAVING COUNT(DISTINCT DATE_TRUNC(DATE(fecha), MONTH)) >= {MIN_PUNTOS_MENSUAL}
  )
"""),
        # Se traen el punto ANTERIOR y el SIGUIENTE de cada anomalía. Sin ellos
        # no se puede distinguir un pico de un escalón, que es la única
        # distinción que separa "dato mal leído" de "pasó algo" (ver el
        # docstring del módulo).
        ("consulta", f"""
WITH detectadas AS (
  SELECT indicador, fecha, valor, lower_bound, upper_bound, anomaly_probability
  FROM ML.DETECT_ANOMALIES(
    MODEL `{ds}.ml_anomalias_series`,
    STRUCT(0.99 AS anomaly_prob_threshold))
  WHERE is_anomaly
),
mensual AS (
  SELECT indicador, DATE_TRUNC(DATE(fecha), MONTH) AS mes, AVG(valor) AS valor
  FROM `{ds}.series` WHERE valor IS NOT NULL GROUP BY 1, 2
),
vecinos AS (
  SELECT indicador, mes, valor,
         LAG(valor)  OVER (PARTITION BY indicador ORDER BY mes) AS previo,
         LEAD(valor) OVER (PARTITION BY indicador ORDER BY mes) AS siguiente
  FROM mensual
)
SELECT d.indicador, d.fecha, d.valor, d.lower_bound, d.upper_bound,
       d.anomaly_probability, v.previo, v.siguiente
FROM detectadas d
LEFT JOIN vecinos v
  ON v.indicador = d.indicador AND v.mes = DATE_TRUNC(DATE(d.fecha), MONTH)
ORDER BY d.anomaly_probability DESC, d.fecha DESC
LIMIT 200
"""),
    ]


def sql_forecast(ds: str) -> list[tuple[str, str]]:
    """ARIMA sobre las diarias del BCRA: son las únicas con historia suficiente."""
    lista = ",".join("'%s'" % s for s in SERIES_DIARIAS)
    return [
        ("modelo", f"""
CREATE OR REPLACE MODEL `{ds}.ml_forecast_diarias`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'fecha',
  time_series_data_col = 'valor',
  time_series_id_col = 'indicador',
  auto_arima = TRUE,
  data_frequency = 'DAILY'
) AS
SELECT DATE(fecha) AS fecha, indicador, AVG(valor) AS valor
FROM `{ds}.series`
WHERE indicador IN ({lista}) AND valor IS NOT NULL
GROUP BY fecha, indicador
"""),
        ("consulta", f"""
SELECT indicador, forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `{ds}.ml_forecast_diarias`,
                 STRUCT(30 AS horizon, 0.9 AS confidence_level))
ORDER BY indicador, forecast_timestamp
"""),
    ]


TAREAS = {"anomalias": sql_anomalias, "forecast": sql_forecast}

# Ventana en la que una anomalía todavía es accionable. Más atrás son shocks
# conocidos (la devaluación de diciembre de 2023 sale en media docena de series)
# y saturan la lectura: en la primera corrida, 112 de 118 eran historia.
MESES_ALERTA = 4


def forma_de(fila: dict) -> str:
    """PICO si el valor se va y VUELVE; ESCALÓN si salta y se QUEDA.

    Es la única distinción que separa las dos causas posibles de un valor raro.
    Un dígito mal leído es un PICO por construcción: al mes siguiente la fuente
    se lee bien y la serie vuelve a su nivel. Un cambio real de política es un
    ESCALÓN: salta y se queda ahí.

    Medido sobre las 118 anomalías de la corrida del 2026-08-12: 75 escalones y
    12 picos. La forma es lo que hace usable la alerta — sin este corte, el 85%
    del volumen es historia conocida.
    """
    prev, act, sig = fila.get("previo"), fila.get("valor"), fila.get("siguiente")
    if prev is None or act is None or sig is None:
        return "sin_vecinos"
    salto = act - prev
    if abs(salto) < 1e-9:
        return "plano"
    # Qué proporción del salto se deshizo al mes siguiente.
    vuelta = (sig - act) / -salto
    if vuelta > 0.6:
        return "pico"
    if vuelta < 0.25:
        return "escalon"
    return "parcial"


def _posproceso_anomalias(salidas: dict) -> dict:
    """Separa lo que hay que mirar hoy de lo que ya se sabe, y por FORMA.

    El modelo detecta anomalías sobre TODA la historia de cada serie, y eso está
    bien —es como se entrena—, pero como alerta operativa no sirve mezclado: lo
    que importa es si un PDF que se parseó esta semana trajo un dígito de más.
    """
    filas = salidas.get("filas") or []
    for f in filas:
        f["forma"] = forma_de(f)
    corte = date.today() - timedelta(days=MESES_ALERTA * 31)
    def _fecha(f):
        # ML.DETECT_ANOMALIES devuelve la columna de tiempo como datetime aunque
        # el modelo se entrene sobre un DATE, y `datetime` hereda de `date`, así
        # que hay que preguntar por el hijo primero o la comparación explota.
        v = f.get("fecha")
        if isinstance(v, datetime):
            return v.date()
        return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])
    recientes = [f for f in filas if _fecha(f) >= corte]
    # `revisar` es la bandeja de entrada de verdad: reciente Y con forma de
    # error de lectura. El resto queda accesible pero no compite por atención.
    salidas["revisar"] = [f for f in recientes if f["forma"] in ("pico", "sin_vecinos")]
    salidas["recientes_otras_formas"] = [f for f in recientes
                                         if f["forma"] not in ("pico", "sin_vecinos")]
    salidas["historicas"] = [f for f in filas if _fecha(f) < corte]
    del salidas["filas"]
    return salidas


POSPROCESO = {"anomalias": _posproceso_anomalias}


def _hay_credenciales() -> bool:
    """GOOGLE_APPLICATION_CREDENTIALS (CI) o el ADC de gcloud (local)."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    for base in (os.environ.get("CLOUDSDK_CONFIG"),
                 os.path.join(os.path.expanduser("~"), ".config", "gcloud"),
                 os.path.join(os.environ.get("APPDATA", ""), "gcloud")):
        if base and os.path.exists(os.path.join(base, "application_default_credentials.json")):
            return True
    return False


def _subir_resultados(cliente, ds: str, tarea: str, salidas: dict, corrida: str) -> str | None:
    """Deja el resultado en una tabla, no sólo en el JSON local.

    Los modelos vivían en BigQuery y sus resultados en `output/bq_ml/*.json`, que
    está gitignoreado: en la consola no había NADA que mirar. Una herramienta
    interna que nadie puede abrir no se usa. Se acumula por `generated_at`, igual
    que las tablas de snapshot (ADR-0180), así que la bandeja de hoy se puede
    comparar contra la de la semana pasada.
    """
    from google.cloud import bigquery

    filas = []
    for bandeja, items in salidas.items():
        for f in items:
            filas.append({**{k: (v.isoformat() if hasattr(v, "isoformat") else v)
                             for k, v in f.items()},
                          "bandeja": bandeja, "generated_at": corrida})
    if not filas:
        return None
    tabla = f"{ds}.ml_{tarea}_resultado"
    cliente.load_table_from_json(filas, tabla, job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        autodetect=True)).result()
    return tabla


def correr(nombre: str, ds: str, cliente, dry_run: bool) -> dict:
    pasos = TAREAS[nombre](ds)
    if dry_run:
        for etiqueta, sql in pasos:
            print(f"\n----- {nombre} · {etiqueta} -----{sql}")
        return {"tarea": nombre, "dry_run": True}

    salidas: dict = {}
    for etiqueta, sql in pasos:
        print(f"  [{nombre}] {etiqueta}…", flush=True)
        resultado = cliente.query(sql).result()
        if etiqueta.startswith("consulta"):
            # "consulta:evaluacion" → salidas["evaluacion"]; "consulta" → "filas".
            clave = etiqueta.split(":", 1)[1] if ":" in etiqueta else "filas"
            salidas[clave] = [dict(r) for r in resultado]
    salidas = POSPROCESO.get(nombre, lambda s: s)(salidas)
    conteo = {k: len(v) for k, v in salidas.items()}
    print(f"  [{nombre}] " + ", ".join(f"{v} {k}" for k, v in conteo.items()))
    return {"tarea": nombre, "n": conteo, **salidas}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("tareas", nargs="*", choices=list(TAREAS))
    p.add_argument("--todo", action="store_true", help="corre las tres")
    p.add_argument("--dry-run", action="store_true", help="imprime el SQL y sale")
    p.add_argument("--proyecto", default=os.environ.get("GCP_PROJECT", PROYECTO_POR_DEFECTO))
    p.add_argument("--dataset", default=DATASET_POR_DEFECTO)
    args = p.parse_args()

    tareas = list(TAREAS) if args.todo else (args.tareas or ["anomalias"])
    ds = f"{args.proyecto}.{args.dataset}"

    cliente = None
    if not args.dry_run:
        # Mismo criterio que bigquery_export: en Windows el ADC de gcloud vive
        # en %APPDATA%\gcloud, no en ~/.config/gcloud.
        if not _hay_credenciales():
            print("ERROR: sin credenciales de Google Cloud. Correr "
                  "`gcloud auth application-default login` o exportar "
                  "GOOGLE_APPLICATION_CREDENTIALS.", file=sys.stderr)
            return 2
        from google.cloud import bigquery
        cliente = bigquery.Client(project=args.proyecto)

    SALIDA.mkdir(parents=True, exist_ok=True)
    resumen = {"generado": datetime.now().isoformat(timespec="seconds"), "dataset": ds}
    for t in tareas:
        r = correr(t, ds, cliente, args.dry_run)
        # El resumen lleva los conteos, no las filas: es lo que se mira primero.
        resumen[t] = {k: v for k, v in r.items() if not isinstance(v, list)}
        if not args.dry_run:
            destino = SALIDA / f"{t}.json"
            destino.write_text(
                json.dumps(r, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8")
            print(f"  → {destino.relative_to(RAIZ)}")
            listas = {k: v for k, v in r.items() if isinstance(v, list)}
            tabla = _subir_resultados(cliente, ds, t, listas, resumen["generado"])
            if tabla:
                print(f"  → {tabla}")

    if not args.dry_run:
        (SALIDA / "resumen.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
