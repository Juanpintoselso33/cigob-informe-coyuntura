"""
Colector SNIC — Estadisticas Criminales Argentina
Descarga directa de CSV verificada. Last-Modified 2025-05-21.
Frecuencia: anual con ~5 meses de rezago.
Complemento: delitos CABA con menor rezago.
"""
import io
import logging
from datetime import datetime

import requests

from config import SNIC_CSV, CABA_DELITOS_URL, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _parse_snic_csv(content: bytes) -> dict:
    """
    Parsea el CSV del SNIC nacional.
    Devuelve el total de hechos del ultimo anio disponible y desglose por tipo.
    """
    import csv
    text = content.decode("utf-8", errors="replace")
    # El CSV oficial cambió a ';' como separador en 2026 (con headers entre
    # comillas); detectar por la primera línea para soportar ambos formatos.
    sep = ";" if ";" in text.split("\n", 1)[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=sep)
    rows = list(reader)
    if not rows:
        return {}

    # Agrupar por anio
    por_anio: dict[str, dict] = {}
    for row in rows:
        anio = row.get("anio") or row.get("year") or row.get("Anio") or ""
        if not anio:
            continue
        if anio not in por_anio:
            por_anio[anio] = {"total_hechos": 0, "tipos": {}}
        tipo = (row.get("codigo_delito_snic_nombre") or row.get("tipo_delito")
                or row.get("tipo") or "total")
        hechos = int(float(
            row.get("cantidad_hechos") or row.get("hechos") or row.get("cantidad") or 0
        ))
        por_anio[anio]["total_hechos"] += hechos
        por_anio[anio]["tipos"][tipo] = por_anio[anio]["tipos"].get(tipo, 0) + hechos

    ultimo_anio = max(por_anio.keys()) if por_anio else None

    # Si total_hechos==0 para todos los años, las columnas no coinciden
    if not ultimo_anio or por_anio[ultimo_anio]["total_hechos"] == 0:
        cols = list(rows[0].keys())
        logger.debug("SNIC columnas disponibles: %s", cols)
        # Intentar buscar columna numerica que sea el conteo
        import csv as _csv
        candidatas = [c for c in cols if any(
            kw in c.lower() for kw in ["hecho", "cant", "total", "delito", "count"]
        )]
        return {
            "columnas_disponibles": cols,
            "columnas_candidatas": candidatas,
            "nota": "CSV descargado pero columnas de hechos no identificadas. Ver 'columnas_disponibles'.",
        }

    return {
        "anio": ultimo_anio,
        "total_hechos": por_anio[ultimo_anio]["total_hechos"],
        "tipos_principales": dict(
            sorted(por_anio[ultimo_anio]["tipos"].items(), key=lambda x: -x[1])[:5]
        ),
    }


def fetch_snic() -> dict:
    """Descarga estadisticas criminales SNIC nacionales y delitos CABA."""
    results = {}

    # SNIC nacional
    try:
        r = requests.get(SNIC_CSV, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        parsed = _parse_snic_csv(r.content)
        results["inseguridad_snic"] = {
            **parsed,
            "fuente": "SNIC - Ministerio de Seguridad",
            "url": SNIC_CSV,
            "nota": "Datos anuales. Rezago ~5 meses desde cierre de anio.",
        }
        logger.info("SNIC OK: anio %s, %s hechos", parsed.get("anio"), parsed.get("total_hechos"))
    except Exception as e:
        logger.error("SNIC FAIL: %s", e)

    # Delitos CABA (mas recientes — 2025 publicado 2026-05-08)
    for year in [datetime.today().year, datetime.today().year - 1]:
        url = CABA_DELITOS_URL.format(year=year)
        try:
            r = requests.head(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            if r.status_code == 200:
                # Solo bajar si no es muy grande (puede ser 10+ MB)
                size_mb = int(r.headers.get("content-length", 0)) / 1e6
                results["delitos_caba_disponible"] = {
                    "anio": year,
                    "url": url,
                    "size_mb": round(size_mb, 1),
                    "last_modified": r.headers.get("Last-Modified", ""),
                    "nota": "CSV con hechos geolocalizados. Descargar con pd.read_csv(url) para analisis detallado.",
                }
                logger.info("Delitos CABA %d: disponible (%.1f MB)", year, size_mb)
                break
        except Exception as e:
            logger.debug("Delitos CABA %d: %s", year, e)

    return results
