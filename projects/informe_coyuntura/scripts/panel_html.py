"""Genera el panel de las herramientas internas y lo publica en Cloud Storage.

## Por qué acá y no en Cloud Monitoring

Cloud Monitoring sólo grafica MÉTRICAS. Eso alcanza para el semáforo y para
alertar —y para eso se sigue usando, ver `panel_gcp.py`— pero no puede mostrar
un pronóstico a 30 días con su banda, ni la tabla de parser-vs-modelo, ni la
distribución por forma de las anomalías. Armar el panel ahí terminó dejando
afuera justo lo que había que ver.

Y Looker Studio, que sí sería la herramienta correcta, no tiene API pública para
crear reportes: el Linking API deja la fuente conectada y los gráficos hay que
ponerlos a mano, cada vez.

Así que el panel se genera acá desde las vistas `panel_ml_*` y se sube a un
bucket privado del mismo proyecto. Es una página quieta: se regenera en cada
corrida, no tiene backend y no puede quedar desactualizada sin que se note,
porque estampa la hora de la última corrida de cada herramienta.

Uso:
    python scripts/panel_html.py              # genera y sube
    python scripts/panel_html.py --solo-local # sólo escribe el HTML local
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = Path(__file__).resolve().parent / "plantillas" / "panel.html"
SALIDA = RAIZ / "output" / "panel"

PROYECTO = os.environ.get("GCP_PROJECT", "cigob-analytics")
DATASET = "informe_coyuntura"
BUCKET = os.environ.get("PANEL_BUCKET", f"{PROYECTO}-panel")
UBICACION = "southamerica-east1"

SERIES_DIARIAS = ("tc_mayorista", "badlar", "prestamos_privados", "base_monetaria")
ETIQUETAS = {
    "tc_mayorista": ("Tipo de cambio mayorista", "$/US$"),
    "badlar": ("Badlar bancos privados", "% n.a."),
    "prestamos_privados": ("Préstamos al sector privado", "M$"),
    "base_monetaria": ("Base monetaria", "M$"),
}


def recolectar() -> dict:
    """Todo sale de las vistas, no de los JSON locales: lo que se ve en el panel
    es exactamente lo que hay en BigQuery."""
    from google.cloud import bigquery

    c = bigquery.Client(project=PROYECTO)
    q = lambda sql: [dict(r) for r in c.query(sql).result()]
    D = f"{PROYECTO}.{DATASET}"

    salud = q(f"SELECT * FROM `{D}.panel_ml_salud`")[0]
    alertas = q(f"SELECT * FROM `{D}.panel_ml_alertas`")
    verificacion = q(f"SELECT caso, campo, valor_parser, valor_modelo, coincide "
                     f"FROM `{D}.panel_ml_verificacion` ORDER BY caso, campo")
    anomalias = q(f"SELECT bandeja, forma, indicador, CAST(fecha AS STRING) fecha, "
                  f"valor, previo, siguiente, lower_bound, upper_bound "
                  f"FROM `{D}.panel_ml_anomalias`")
    forecast = q(f"SELECT indicador, CAST(dia AS STRING) dia, pronostico, piso, techo "
                 f"FROM `{D}.panel_ml_forecast` ORDER BY indicador, dia")
    historia = q(f"""
        SELECT indicador, CAST(DATE(fecha) AS STRING) dia, AVG(valor) valor
        FROM `{D}.series`
        WHERE indicador IN ({",".join("'%s'" % s for s in SERIES_DIARIAS)})
          AND DATE(fecha) >= DATE_SUB(CURRENT_DATE(), INTERVAL 75 DAY)
          AND valor IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2""")

    hist, fore = collections.defaultdict(list), collections.defaultdict(list)
    for r in historia:
        hist[r["indicador"]].append([r["dia"], r["valor"]])
    for r in forecast:
        fore[r["indicador"]].append([r["dia"], r["pronostico"], r["piso"], r["techo"]])

    recientes = [a for a in anomalias if a["bandeja"] != "historicas"]
    return {
        "salud": salud,
        "alertas": alertas,
        "verificacion": verificacion,
        "formas": dict(collections.Counter(a["forma"] for a in anomalias)),
        "picos": [{"indicador": a["indicador"], "fecha": a["fecha"][:7],
                   "valor": a["valor"], "previo": a["previo"],
                   "siguiente": a["siguiente"]}
                  for a in anomalias if a["forma"] == "pico"],
        "recientes": [{"indicador": a["indicador"], "fecha": a["fecha"][:7],
                       "forma": a["forma"], "bandeja": a["bandeja"],
                       "valor": a["valor"], "previo": a["previo"],
                       "siguiente": a["siguiente"],
                       "lo": a["lower_bound"], "hi": a["upper_bound"]}
                      for a in recientes],
        "series": {k: {"hist": hist.get(k, []), "fore": fore.get(k, [])} for k in fore},
        "etiquetas": ETIQUETAS,
    }


def render(datos: dict) -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    bloque = "<script>\nconst DATOS = " + json.dumps(
        datos, ensure_ascii=False, default=str) + ";\n</script>"
    return plantilla.replace("<script>/*__DATOS__*/</script>", bloque)


def _gcloud() -> str:
    """En Windows `gcloud` es un .cmd y CreateProcess no lo resuelve solo."""
    import shutil
    return shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud"


def _correr(*args) -> subprocess.CompletedProcess:
    return subprocess.run((_gcloud(),) + args[1:] if args[0] == "gcloud" else args,
                          capture_output=True, text=True, encoding="utf-8")


def subir(archivo: Path) -> str | None:
    """Sube al bucket, creándolo privado si no existe.

    Se usa el CLI y no `google-cloud-storage` por el mismo criterio que el resto:
    no sumarle una dependencia al pipeline nocturno por algo que se toca poco.
    """
    ver = _correr("gcloud", "storage", "buckets", "describe", f"gs://{BUCKET}",
                  f"--project={PROYECTO}", "--format=value(name)")
    if ver.returncode != 0:
        cr = _correr("gcloud", "storage", "buckets", "create", f"gs://{BUCKET}",
                     f"--project={PROYECTO}", f"--location={UBICACION}",
                     "--uniform-bucket-level-access")
        if cr.returncode != 0:
            print(f"  [!] no se pudo crear el bucket: {cr.stderr.strip()[:200]}",
                  file=sys.stderr)
            return None
        print(f"  bucket creado: gs://{BUCKET} (privado, {UBICACION})")

    # `no-store` porque el panel se regenera en cada corrida: una versión
    # cacheada es peor que no tener panel — muestra números viejos con cara
    # de actuales, que es exactamente el problema que este proyecto persigue.
    cp = _correr("gcloud", "storage", "cp", str(archivo), f"gs://{BUCKET}/panel.html",
                 f"--project={PROYECTO}", "--cache-control=no-store",
                 "--content-type=text/html; charset=utf-8")
    if cp.returncode != 0:
        print(f"  [!] no se pudo subir: {cp.stderr.strip()[:200]}", file=sys.stderr)
        return None
    return f"https://storage.cloud.google.com/{BUCKET}/panel.html"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--solo-local", action="store_true", help="no sube a Cloud Storage")
    args = p.parse_args()

    datos = recolectar()
    html = render(datos)
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "panel.html"
    destino.write_text(html, encoding="utf-8")
    print(f"  {len(html) // 1024} KB · {len(datos['series'])} series · "
          f"{len(datos['verificacion'])} campos · {len(datos['alertas'])} alerta(s)")
    print(f"  → {destino.relative_to(RAIZ)}")

    if not args.solo_local:
        url = subir(destino)
        if url:
            print(f"  → {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
