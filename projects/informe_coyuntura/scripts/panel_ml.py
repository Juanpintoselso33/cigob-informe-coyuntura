"""Crea las vistas del panel de herramientas internas en BigQuery.

Los modelos vivían en BigQuery y sus resultados en JSON gitignoreado: en la
consola no había nada que abrir. Estas vistas son la entrada única — siempre
muestran la ÚLTIMA corrida, así que sirven tanto para mirar a ojo como para
apuntarles un Looker Studio sin escribir SQL.

    panel_ml_alertas       lo que pide atención HOY, de las dos herramientas
    panel_ml_anomalias     la última corrida del detector, con forma y bandeja
    panel_ml_forecast      el pronóstico vigente de las diarias del BCRA
    panel_ml_verificacion  parser vs modelo, campo por campo
    panel_ml_salud         una fila: el estado general, para el semáforo

Uso:
    python scripts/panel_ml.py
"""

from __future__ import annotations

import os
import sys

PROYECTO = os.environ.get("GCP_PROJECT", "cigob-analytics")
DS = f"{PROYECTO}.informe_coyuntura"

VISTAS = {
    # ── Lo único que hay que mirar todos los días ───────────────────────────
    "panel_ml_alertas": f"""
SELECT 'anomalía' AS origen, indicador AS sujeto,
       CAST(fecha AS STRING) AS periodo,
       CONCAT('valor ', FORMAT('%.2f', valor), ' fuera de [',
              FORMAT('%.2f', lower_bound), ' , ', FORMAT('%.2f', upper_bound), ']') AS detalle,
       forma AS nota, generated_at
FROM `{DS}.ml_anomalias_resultado`
WHERE bandeja = 'revisar'
  AND generated_at = (SELECT MAX(generated_at) FROM `{DS}.ml_anomalias_resultado`)
UNION ALL
SELECT 'lectura PDF', CONCAT(caso, '.', campo), NULL,
       CONCAT('parser ', FORMAT('%.2f', valor_parser),
              ' vs modelo ', FORMAT('%.2f', valor_modelo)), tipo, generated_at
FROM `{DS}.verificacion_pdf`
WHERE NOT coincide
  AND generated_at = (SELECT MAX(generated_at) FROM `{DS}.verificacion_pdf`)
""",

    # ── El detector, última corrida ─────────────────────────────────────────
    "panel_ml_anomalias": f"""
SELECT bandeja, forma, indicador, fecha, valor, previo, siguiente,
       lower_bound, upper_bound, anomaly_probability, generated_at
FROM `{DS}.ml_anomalias_resultado`
WHERE generated_at = (SELECT MAX(generated_at) FROM `{DS}.ml_anomalias_resultado`)
""",

    # ── El pronóstico vigente ───────────────────────────────────────────────
    "panel_ml_forecast": f"""
SELECT indicador, DATE(forecast_timestamp) AS dia,
       forecast_value AS pronostico,
       prediction_interval_lower_bound AS piso,
       prediction_interval_upper_bound AS techo,
       generated_at
FROM `{DS}.ml_forecast_resultado`
WHERE generated_at = (SELECT MAX(generated_at) FROM `{DS}.ml_forecast_resultado`)
""",

    # ── Parser vs modelo ────────────────────────────────────────────────────
    "panel_ml_verificacion": f"""
SELECT caso, campo, valor_parser, valor_modelo, coincide, tipo, modelo,
       reusado, generated_at
FROM `{DS}.verificacion_pdf`
WHERE generated_at = (SELECT MAX(generated_at) FROM `{DS}.verificacion_pdf`)
""",

    # ── Una fila, para el semáforo de arriba de todo ────────────────────────
    "panel_ml_salud": f"""
SELECT
  (SELECT COUNT(*) FROM `{DS}.panel_ml_alertas`) AS alertas_abiertas,
  (SELECT COUNT(*) FROM `{DS}.panel_ml_anomalias` WHERE bandeja = 'revisar')
    AS anomalias_a_revisar,
  (SELECT COUNT(*) FROM `{DS}.panel_ml_verificacion` WHERE NOT coincide)
    AS campos_en_discrepancia,
  (SELECT COUNT(*) FROM `{DS}.panel_ml_verificacion`) AS campos_verificados,
  (SELECT MAX(generated_at) FROM `{DS}.ml_anomalias_resultado`) AS ultima_corrida_ml,
  (SELECT MAX(generated_at) FROM `{DS}.verificacion_pdf`) AS ultima_corrida_pdf
""",
}


def main() -> int:
    from google.cloud import bigquery

    cliente = bigquery.Client(project=PROYECTO)
    # `panel_ml_salud` lee de las otras: se crean en orden y por eso el dict es
    # ordenado a propósito (Python conserva el orden de inserción).
    for nombre, sql in VISTAS.items():
        cliente.query(f"CREATE OR REPLACE VIEW `{DS}.{nombre}` AS {sql}").result()
        print(f"  vista {nombre}")
    print(f"\n  consola: https://console.cloud.google.com/bigquery"
          f"?project={PROYECTO}&d=informe_coyuntura&p={PROYECTO}&page=dataset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
