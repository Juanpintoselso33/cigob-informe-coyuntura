"""
Colector CAFAM — Patentamiento de motovehículos
API pública sin autenticación. Verificada 2026-05-10.
Nota: CIAM no existe (DNS falla). La entidad real es CAFAM.
"""
import logging
from datetime import datetime, timedelta

import requests

from config import CAFAM_API, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def fetch_cafam(year: int | None = None, month: int | None = None) -> dict:
    """
    Descarga el patentamiento de motovehículos del mes indicado.

    Por defecto reporta el último mes calendario COMPLETO (el mes anterior al
    actual). El patentamiento es un flujo mensual que se compara contra umbrales
    por mes; tomar el mes en curso devolvería un acumulado parcial (ej. 2.523 el
    2-jun vs ~70.000 de un mes completo), inflando espuriamente la tensión. El
    último dato disponible y comparable es siempre el mes completo más reciente.
    """
    now = datetime.today()
    if year is None and month is None:
        # Mes anterior al actual = último mes calendario completo.
        ref = now.replace(day=1) - timedelta(days=1)
        year, month = ref.year, ref.month
    else:
        year = year or now.year
        month = month or now.month

    params = {
        "month_start": month,
        "month_end": month,
        "year": year,
        "type": "TODOS",
    }

    try:
        r = requests.get(CAFAM_API, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        total = sum(p["count"] for p in data.get("provinces", []))
        provincias = {p["_id"]: p["count"] for p in data.get("provinces", [])}

        result = {
            "patentamiento_motos": {
                "valor": total,
                "fecha": f"{year}-{month:02d}",
                "unidad": "unidades",
                "provincias": provincias,
                "fuente": "CAFAM API",
            }
        }
        logger.info("CAFAM OK: %d motos en %d-%02d", total, year, month)
        return result

    except Exception as e:
        logger.error("CAFAM FAIL: %s", e)
        return {}
