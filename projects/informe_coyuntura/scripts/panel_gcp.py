"""Publica el estado de las herramientas internas como dashboard de GCP.

Dos capas, porque ninguna sola alcanza:

  Cloud Monitoring   El semáforo y la serie histórica. Se crea entero por API —
                     métricas + dashboard + política de alerta— así que no hay
                     ningún paso manual. Es lo que contesta "¿hay algo mal hoy?"
                     y lo que puede mandar un mail solo.

  Looker Studio      La exploración: las tablas de anomalías, el pronóstico, la
                     comparación parser-vs-modelo. Looker Studio no tiene API
                     pública para crear reportes, así que lo que se genera acá
                     son URLs del Linking API: abren un reporte con la vista de
                     BigQuery ya conectada, a un clic de "Crear".

Se usa REST y no `google-cloud-monitoring` a propósito: agregar la librería a
requirements.txt la instala en cada corrida del pipeline nocturno por algo que
se toca una vez cada tanto. `requests` y `google-auth` ya están.

Uso:
    python scripts/panel_gcp.py               # publica métricas y arma todo
    python scripts/panel_gcp.py --solo-links  # sólo imprime los links
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

PROYECTO = os.environ.get("GCP_PROJECT", "cigob-analytics")
DATASET = "informe_coyuntura"
PREFIJO = "custom.googleapis.com/informe"
BUCKET = os.environ.get("PANEL_BUCKET", f"{PROYECTO}-panel")
PANEL_URL = f"https://storage.cloud.google.com/{BUCKET}/panel.html"

# Cada métrica con su descripción: son las que arma `panel_ml_salud`.
METRICAS = {
    "alertas_abiertas": "Cosas que piden atención hoy, de las dos herramientas",
    "anomalias_a_revisar": "Anomalías recientes con forma de error de lectura",
    "campos_en_discrepancia": "Campos donde el parser y el modelo no coinciden",
    "campos_verificados": "Campos comparados contra el documento de origen",
}

VISTAS_LOOKER = {
    "panel_ml_alertas": "Bandeja de entrada",
    "panel_ml_anomalias": "Detector de anomalías",
    "panel_ml_forecast": "Pronóstico a 30 días",
    "panel_ml_verificacion": "Parser contra modelo",
}


def _sesion():
    """Sesión HTTP autenticada con el ADC, sin librerías nuevas."""
    import google.auth
    import google.auth.transport.requests
    import requests

    cred, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cred.refresh(google.auth.transport.requests.Request())
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {cred.token}",
                      "Content-Type": "application/json"})
    return s


def leer_salud() -> dict:
    from google.cloud import bigquery
    c = bigquery.Client(project=PROYECTO)
    fila = list(c.query(
        f"SELECT * FROM `{PROYECTO}.{DATASET}.panel_ml_salud`").result())[0]
    return dict(fila)


def publicar_metricas(s, salud: dict) -> int:
    """Una serie temporal por métrica. Cloud Monitoring las acumula, así que la
    evolución de las discrepancias queda graficable sin guardar nada más."""
    ahora = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    series = []
    for clave in METRICAS:
        valor = salud.get(clave)
        if valor is None:
            continue
        series.append({
            "metric": {"type": f"{PREFIJO}/{clave}"},
            "resource": {"type": "global", "labels": {"project_id": PROYECTO}},
            "points": [{"interval": {"endTime": ahora},
                        "value": {"int64Value": int(valor)}}],
        })
    r = s.post(
        f"https://monitoring.googleapis.com/v3/projects/{PROYECTO}/timeSeries",
        data=json.dumps({"timeSeries": series}))
    if r.status_code >= 300:
        print(f"  [!] métricas: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
        return 0
    return len(series)


def _widget(clave, titulo):
    return {
        "title": titulo,
        "xyChart": {
            "dataSets": [{
                "timeSeriesQuery": {
                    "timeSeriesFilter": {
                        "filter": (f'metric.type="{PREFIJO}/{clave}" '
                                   'resource.type="global"'),
                        "aggregation": {"alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_MAX"},
                    }
                },
                "plotType": "LINE",
                "targetAxis": "Y1",
            }],
            "chartOptions": {"mode": "COLOR"},
            "yAxis": {"scale": "LINEAR"},
        },
    }


def _scorecard(clave, titulo, umbral):
    return {
        "title": titulo,
        "scorecard": {
            "timeSeriesQuery": {
                "timeSeriesFilter": {
                    "filter": (f'metric.type="{PREFIJO}/{clave}" '
                               'resource.type="global"'),
                    "aggregation": {"alignmentPeriod": "86400s",
                                    "perSeriesAligner": "ALIGN_MAX"},
                }
            },
            "thresholds": [{"value": umbral, "color": "YELLOW",
                            "direction": "ABOVE"}],
            "sparkChartView": {"sparkChartType": "SPARK_LINE"},
        },
    }


def dashboard() -> dict:
    return {
        "displayName": "Informe de Coyuntura — herramientas internas",
        "mosaicLayout": {
            "columns": 12,
            "tiles": [
                {"width": 12, "height": 2, "xPos": 0, "yPos": 0,
                 "widget": {"title": "", "text": {
                     "content": (
                         "### Sala de máquinas\n"
                         "Este tablero es el **semáforo y la alerta**: Cloud Monitoring "
                         "sólo grafica métricas, así que el pronóstico a 30 días, la "
                         "tabla de parser-vs-modelo y el detalle de las anomalías no "
                         "entran acá.\n\n"
                         f"**Panel completo → [{PANEL_URL}]({PANEL_URL})**  \n"
                         "Datos → BigQuery, vistas `panel_ml_*`. "
                         "Ninguna de las tres herramientas toca el snapshot publicado."),
                     "format": "MARKDOWN"}}},
                {"width": 3, "height": 3, "xPos": 0, "yPos": 2,
                 "widget": _scorecard("alertas_abiertas", "Alertas abiertas", 1)},
                {"width": 3, "height": 3, "xPos": 3, "yPos": 2,
                 "widget": _scorecard("campos_en_discrepancia",
                                      "Campos en discrepancia", 0)},
                {"width": 3, "height": 3, "xPos": 6, "yPos": 2,
                 "widget": _scorecard("anomalias_a_revisar", "A revisar", 1)},
                {"width": 3, "height": 3, "xPos": 9, "yPos": 2,
                 "widget": _scorecard("campos_verificados", "Campos verificados", 999)},
                {"width": 6, "height": 4, "xPos": 0, "yPos": 5,
                 "widget": _widget("alertas_abiertas", "Alertas abiertas en el tiempo")},
                {"width": 6, "height": 4, "xPos": 6, "yPos": 5,
                 "widget": _widget("campos_en_discrepancia",
                                   "Discrepancias parser vs modelo")},
            ],
        },
    }


def crear_dashboard(s) -> str | None:
    base = f"https://monitoring.googleapis.com/v1/projects/{PROYECTO}/dashboards"
    d = dashboard()
    existentes = s.get(base).json().get("dashboards", []) or []
    previo = next((x for x in existentes
                   if x.get("displayName") == d["displayName"]), None)
    if previo:
        # PATCH necesita el etag para no pisar una edición hecha en la consola.
        d["etag"] = previo.get("etag", "")
        r = s.patch(f"https://monitoring.googleapis.com/v1/{previo['name']}",
                    data=json.dumps(d))
        nombre = previo["name"]
    else:
        r = s.post(base, data=json.dumps(d))
        nombre = (r.json() or {}).get("name", "")
    if r.status_code >= 300:
        print(f"  [!] dashboard: HTTP {r.status_code} {r.text[:250]}", file=sys.stderr)
        return None
    return nombre.rsplit("/", 1)[-1] if nombre else None


def politica_alerta(s) -> str | None:
    """Avisa cuando el parser y el modelo dejan de coincidir.

    Es lo único que justifica Cloud Monitoring acá: un panel hay que ir a
    mirarlo, una política te busca. Se dispara sólo con `campos_en_discrepancia`
    —no con las anomalías— porque una discrepancia significa que dos lectores
    independientes del MISMO documento dicen cosas distintas, y eso siempre
    amerita mirar. Las anomalías, medido, son casi siempre eventos reales.
    """
    nombre = "Informe de Coyuntura — el parser y el modelo no coinciden"
    base = f"https://monitoring.googleapis.com/v3/projects/{PROYECTO}/alertPolicies"
    existentes = s.get(base).json().get("alertPolicies", []) or []
    if any(p.get("displayName") == nombre for p in existentes):
        return "ya existía"

    cuerpo = {
        "displayName": nombre,
        "documentation": {
            "content": (f"Un campo leído del PDF difiere entre el parser de regex y "
                        f"el modelo. Revisar el documento de origen antes de confiar "
                        f"en el indicador.\n\nPanel: {PANEL_URL}"),
            "mimeType": "text/markdown",
        },
        "combiner": "OR",
        "conditions": [{
            "displayName": "campos_en_discrepancia > 0",
            "conditionThreshold": {
                "filter": (f'metric.type="{PREFIJO}/campos_en_discrepancia" '
                           'resource.type="global"'),
                "comparison": "COMPARISON_GT",
                "thresholdValue": 0,
                "duration": "0s",
                "aggregations": [{"alignmentPeriod": "3600s",
                                  "perSeriesAligner": "ALIGN_MAX"}],
            },
        }],
        # Sin canal de notificación: crearlo requiere confirmar un mail desde la
        # consola, así que la política queda armada y el canal se engancha a mano.
        "notificationChannels": [],
        "enabled": True,
    }
    r = s.post(base, data=json.dumps(cuerpo))
    if r.status_code >= 300:
        print(f"  [!] política: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
        return None
    return (r.json() or {}).get("name", "").rsplit("/", 1)[-1]


def links_looker() -> dict:
    """URLs del Linking API: abren Looker Studio con la vista ya conectada.

    No hay API pública para crear el reporte con sus gráficos, así que esto deja
    todo listo menos el último clic. Es la diferencia honesta entre "automatizado"
    y "a un clic".
    """
    out = {}
    for vista, titulo in VISTAS_LOOKER.items():
        p = {
            "c.reportName": f"Informe de Coyuntura · {titulo}",
            "ds.connector": "bigQuery",
            "ds.type": "TABLE",
            "ds.projectId": PROYECTO,
            "ds.billingProjectId": PROYECTO,
            "ds.datasetId": DATASET,
            "ds.tableId": vista,
            "ds.datasourceName": vista,
        }
        out[titulo] = ("https://lookerstudio.google.com/reporting/create?"
                       + urllib.parse.urlencode(p))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--solo-links", action="store_true",
                   help="no publica nada, sólo imprime las URLs de Looker Studio")
    args = p.parse_args()

    if not args.solo_links:
        s = _sesion()
        salud = leer_salud()
        n = publicar_metricas(s, salud)
        print(f"  {n} métricas publicadas en Cloud Monitoring")
        did = crear_dashboard(s)
        if did:
            print(f"  dashboard: https://console.cloud.google.com/monitoring/"
                  f"dashboards/builder/{did}?project={PROYECTO}")
        pol = politica_alerta(s)
        if pol:
            print(f"  política de alerta: {pol}")
        print(f"  panel completo: {PANEL_URL}")

    print("\n  Looker Studio (abre con la vista ya conectada, falta un clic en «Crear»):")
    for titulo, url in links_looker().items():
        print(f"\n  · {titulo}\n    {url}")
    print(f"\n  BigQuery: https://console.cloud.google.com/bigquery"
          f"?project={PROYECTO}&d={DATASET}&p={PROYECTO}&page=dataset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
