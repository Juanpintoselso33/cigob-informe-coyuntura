"""
Colector CICCRA — Consumo de carne vacuna per capita
Metodo: scraping homepage para encontrar ultimo informe + pdfplumber.
Informe 300 = enero-2026. Numeracion correlativa mensual.
Requiere: pip install pdfplumber
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import requests

from config import CICCRA_HOME, CICCRA_INF_BASE, CICCRA_INF_START_NUM, \
    CICCRA_INF_START_YEAR, CICCRA_INF_START_MONTH, HTTP_HEADERS, HTTP_TIMEOUT, MESES_ES

logger = logging.getLogger(__name__)

# Caché mensual de la serie (lo llena descargar_series.fetch_carne_serie, un
# PDF por mes una sola vez). Acá es la red de seguridad del titular.
CARNE_SERIE_STORE = Path(__file__).resolve().parents[3] / "data" / "vida" / "carne_serie.json"


def _serie_ultimo() -> tuple[str, float] | None:
    """(YYYY-MM, valor) del último mes con dato en el caché de la serie.
    Si el fetch en vivo consigue un mes MÁS VIEJO que el caché (404
    transitorio de un PDF, como el 06-jul-2026 desde los runners de CI),
    el titular no debe retroceder respecto de la serie publicada — el
    invariante G3 del gate exige card == último punto de la serie."""
    try:
        store = json.loads(CARNE_SERIE_STORE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    meses = sorted(ym for ym, v in store.items() if isinstance(v, (int, float)))
    if not meses:
        return None
    return meses[-1], float(store[meses[-1]])


def _numero_para_fecha(year: int, month: int) -> int:
    """Calcula el numero de informe CICCRA para un mes dado."""
    meses_desde_inicio = (year - CICCRA_INF_START_YEAR) * 12 + (month - CICCRA_INF_START_MONTH)
    return CICCRA_INF_START_NUM + meses_desde_inicio


def _url_pdf(year: int, month: int) -> str:
    """Construye la URL del PDF de CICCRA para un mes."""
    num = _numero_para_fecha(year, month)
    mes_str = MESES_ES[month - 1]
    # Publicado el mes siguiente al dato (con 1 mes de delay)
    pub_month = month + 1 if month < 12 else 1
    pub_year  = year if month < 12 else year + 1
    return (
        f"{CICCRA_INF_BASE}{pub_year}/{pub_month:02d}/"
        f"Inf-No-{num}-{year}-{mes_str}.pdf"
    )


def _extraer_per_capita(pdf_bytes: bytes) -> float | None:
    """Extrae el consumo per capita del PDF usando pdfplumber."""
    try:
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        # Patron verificado en PDFs 2025-2026
        # El informe usa "46,2 kilos/año" (no "kg/año") a partir de 2026
        patterns = [
            r'(\d{2,3}[,\.]\d)\s*kilos?/a[nñ]o',
            r'(\d{2}[,\.]\d)\s*kg/a[nñ]o',
            # 2023-2024: "se habría ubicado en 53,2 kg/hab/año" (a veces con
            # salto de línea antes de la unidad); \d{2,3} evita capturar
            # variaciones chicas tipo "+1,9 kg/hab/año"
            r'(\d{2,3}[,\.]\d)\s*kg/hab',
            r'consumo\s+per\s+c[aá]pita[^\n]{0,60}?(\d{1,3}[,\.]\d{1})\s*(?:kilos?|kg)',
            r'(\d{1,3}[,\.]\d{1})\s*(?:kilos?|kg)[^\n]{0,60}?per\s+c[aá]pita',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return float(m.group(1).replace(",", "."))
    except ImportError:
        logger.error("pdfplumber no instalado. Instalar: pip install pdfplumber")
    except Exception as e:
        logger.debug("Error parseando PDF CICCRA: %s", e)
    return None


def fetch_ciccra() -> dict:
    """
    Descarga el informe mas reciente de CICCRA y extrae consumo per capita.
    Fallback: si falla el ultimo mes, intenta el anterior. El titular NUNCA
    retrocede respecto del cache de la serie: si el fetch en vivo devuelve un
    mes anterior al ultimo graficado (un PDF con 404 transitorio hace saltar
    al informe previo), se publica el ultimo mes del cache — asi card y serie
    no divergen (gate G3, falla del 06-jul-2026: card abril 46,2 vs serie
    mayo 47,5 porque el PDF de mayo fallo solo desde CI).
    """
    now = datetime.today()
    vivo = None   # (YYYY-MM, valor, url) del informe mas reciente parseable
    # CICCRA publica con ~1 mes de delay
    for offset in range(0, 3):
        month = now.month - 1 - offset
        year  = now.year
        while month <= 0:
            month += 12
            year  -= 1

        url = _url_pdf(year, month)
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
            if r.status_code != 200:
                logger.debug("CICCRA PDF %d-%02d: HTTP %d", year, month, r.status_code)
                continue

            logger.info("CICCRA PDF encontrado: %s", url)
            per_capita = _extraer_per_capita(r.content)
            if per_capita is not None:
                vivo = (f"{year}-{month:02d}", per_capita, url)
                break
            logger.debug("CICCRA %d-%02d: PDF sin valor extraible", year, month)
        except Exception as e:
            logger.debug("CICCRA %d-%02d FAIL: %s", year, month, e)

    cacheado = _serie_ultimo()
    if vivo is None and cacheado is None:
        logger.error("CICCRA: no se pudo obtener dato en los ultimos 3 meses (sin cache)")
        return {}

    if vivo is None or (cacheado is not None and cacheado[0] > vivo[0]):
        fecha, valor = cacheado
        url, nota = CICCRA_HOME, ("Ultimo informe cacheado por la serie mensual "
                                  "(el fetch en vivo fallo o devolvio un mes anterior)")
        logger.info("CICCRA: titular desde cache de la serie (%s: %.1f)", fecha, valor)
    else:
        fecha, valor, url = vivo
        nota = "Consumo aparente per capita anualizado"

    return {
        "consumo_carne_per_capita": {
            "valor": valor,
            "fecha": fecha,
            "unidad": "kg por habitante/año",
            "fuente": "CICCRA",
            "url": url,
            "nota": nota,
        }
    }
