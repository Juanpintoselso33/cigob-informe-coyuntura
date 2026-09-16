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

# ADR-0323/0324/0325: se conservan por NOMBRE, no por ranking de volumen.
# Antes `tipos_principales` era el top-5 por cantidad de hechos, y eso
# descartaba "Homicidios dolosos" (1.613 hechos en 2025) mientras conservaba
# categorías de bulto como "Robos" (360.946, el #1 nacional) — el dato ya se
# bajaba y se tiraba en la cañería antes de llegar a la ficha. Nombres
# verificados contra el CSV oficial 2025 (no contra este comentario, que
# puede desactualizarse).
#
# ADR-0325: la primera versión de esta lista (sólo homicidios + robos +
# hurtos + abusos) sacó "Amenazas" (217.883 hechos) y "Lesiones dolosas"
# (179.710) sin decirlo — las dos estaban en el top-5 por volumen que este
# cambio reemplaza. Se restituyen: el objetivo del cambio era dejar de
# PERDER categorías relevantes al filtrar por ranking, no reemplazar una
# pérdida por otra. Queda afuera "Otros delitos contra la propiedad"
# (249.754): es un cajón residual sin identidad propia, no un tipo de delito.
TIPOS_RELEVANTES = (
    "Homicidios dolosos",
    "Robos (excluye los agravados por el resultado de lesiones y/o muertes)",
    "Robos agravados por el resultado de lesiones y/o muertes",
    "Hurtos",
    "Abusos sexuales con acceso carnal (violaciones)",
    "Amenazas",
    "Lesiones dolosas",
)


def _num_ar(texto: str) -> float:
    """El CSV del SNIC usa coma decimal dentro de columnas separadas por ';'
    (`tasa_hechos` llega como "7,2270207", no "7.2270207"). `cantidad_hechos`
    no lo necesita —son enteros sin coma— pero `tasa_hechos` sí, y la fuente
    ya la trae calculada: no se recalcula con población propia (ADR-0327)."""
    return float((texto or "0").replace(",", "."))


def _parse_snic_csv(content: bytes) -> dict:
    """
    Parsea el CSV del SNIC nacional.
    Devuelve el total de hechos del ultimo anio disponible, el desglose por
    tipo y, para los tipos de TIPOS_RELEVANTES, la SERIE COMPLETA de
    `tasa_hechos` (cada 100.000 habitantes, ya calculada por la fuente) en
    todos los años que trae el CSV — no sólo el último (ADR-0327: es lo que
    permite anclar `tasa_homicidios`/`tasa_robos` contra la propia historia
    de 26 años, sin inventar una referencia externa).
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
    tasas_por_tipo: dict[str, dict[str, float]] = {}
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
        if tipo in TIPOS_RELEVANTES and row.get("tasa_hechos"):
            tasas_por_tipo.setdefault(tipo, {})[anio] = round(_num_ar(row["tasa_hechos"]), 4)

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

    tipos = por_anio[ultimo_anio]["tipos"]
    # Por NOMBRE (ver TIPOS_RELEVANTES), no por ranking de volumen: un ranking
    # por cantidad de hechos deja afuera a los homicidios, que son el tipo más
    # bajo en volumen y el más citado en cualquier lectura de seguridad.
    principales = {t: tipos[t] for t in TIPOS_RELEVANTES if t in tipos}
    faltantes = [t for t in TIPOS_RELEVANTES if t not in tipos]
    if faltantes:
        # ADR-0325: con lista fija por NOMBRE, el modo de falla más probable
        # es que la fuente renombre una categoría — y eso antes se perdía
        # en silencio (sólo un `logger.warning`, con un test que lo
        # bendecía). Ahora es ruidoso: se levanta acá, lo atrapa el
        # try/except de `fetch_snic()` (que loguea "SNIC FAIL" y sigue con
        # el resto de las fuentes del cinturón sin tumbar la corrida
        # completa) y, un nivel más arriba, `_seguro()` en main.py marca al
        # colector como caído — exactamente el circuito que hoy usan
        # `consumo_carnes.py` y demás colectores del cinturón para
        # degradaciones de formato, y que alimenta el exit code 1/2 y el
        # aviso de #monitor-alertas. No es "que revienta la corrida": es
        # que deja de tirarse en silencio.
        raise ValueError(
            f"SNIC: el CSV {ultimo_anio} no trae estos tipos esperados "
            f"(la fuente pudo renombrar la categoría): {faltantes}")

    return {
        "anio": ultimo_anio,
        "total_hechos": por_anio[ultimo_anio]["total_hechos"],
        "tipos_principales": dict(
            sorted(principales.items(), key=lambda x: -x[1])
        ),
        # ADR-0327: series completas de tasa_hechos (26 años) para los dos
        # tipos que puntúan como indicador propio. Se guardan por nombre y no
        # sólo el último año porque `descargar_series.py` las usa para anclar
        # `tasa_homicidios`/`tasa_robos` contra su propia historia.
        "tasas_por_tipo": tasas_por_tipo,
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
