"""
Colector BCRA via API pública v4.0
Verificado: HTTP 200, JSON, sin autenticación.
IMPORTANTE: v1/v2/v3 están deprecadas (devuelven 400). Usar solo v4.0.
"""
import logging
import requests
from datetime import datetime, timedelta

from config import BCRA_BASE, BCRA_VARIABLES, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _get_variable(id_variable: int, desde: str | None = None, limit: int = 30) -> list[dict]:
    """
    Trae observaciones de una variable BCRA.
    `desde` formato: 'YYYY-MM-DD'. Por defecto últimos 30 días.
    Retorna lista de {fecha, valor}.
    """
    if desde is None:
        desde = (datetime.today() - timedelta(days=45)).strftime("%Y-%m-%d")

    url = f"{BCRA_BASE}/{id_variable}"
    params = {"desde": desde, "limit": limit}
    r = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    return r.json()["results"][0]["detalle"]


def _ultimo(id_variable: int) -> dict:
    """Devuelve la última observación disponible de una variable."""
    detalle = _get_variable(id_variable, limit=5)
    detalle_sorted = sorted(detalle, key=lambda x: x["fecha"], reverse=True)
    return {"valor": detalle_sorted[0]["valor"], "fecha": detalle_sorted[0]["fecha"]}


def _variacion_mensual(id_variable: int) -> dict:
    """Variación % del promedio semanal más reciente vs. mes anterior."""
    detalle = _get_variable(id_variable, limit=60)
    detalle_sorted = sorted(detalle, key=lambda x: x["fecha"], reverse=True)
    ultimo = detalle_sorted[0]["valor"]
    # Promedio de hace ~30 días como referencia mensual
    anterior = next(
        (d["valor"] for d in detalle_sorted if d["fecha"] < detalle_sorted[0]["fecha"][:8] + "01"),
        None,
    )
    var = (ultimo / anterior - 1) * 100 if anterior else None
    return {
        "valor": ultimo,
        "fecha": detalle_sorted[0]["fecha"],
        "variacion_mensual_pct": var,
    }


def _serie_mensual(id_variable: int, meses: int = 15) -> list[dict]:
    """Última observación de cada mes para los últimos `meses` meses.
    Permite computar la variación interanual real del crédito aguas abajo."""
    desde = (datetime.today() - timedelta(days=meses * 31)).strftime("%Y-%m-%d")
    detalle = _get_variable(id_variable, desde=desde, limit=500)
    por_mes: dict = {}
    for d in sorted(detalle, key=lambda x: x["fecha"]):
        por_mes[d["fecha"][:7]] = d          # la última del mes pisa a las previas
    return [{"fecha": v["fecha"], "valor": v["valor"]} for _, v in sorted(por_mes.items())]


def fetch_bcra() -> dict:
    """
    Recolecta indicadores de crédito y endeudamiento del BCRA.
    Clave: indicador #3 del cinturón (Endeudamiento Familiar) =
           créditos tarjeta + personales como proxy de deuda de consumo.
    """
    results = {}

    # Préstamos totales al sector privado
    try:
        results["prestamos_privado_total"] = _ultimo(BCRA_VARIABLES["prestamos_privado_total"])
        logger.info("BCRA préstamos privado OK: %s", results["prestamos_privado_total"])
    except Exception as e:
        logger.error("BCRA préstamos privado FAIL: %s", e)

    # Créditos de consumo (proxy endeudamiento familiar)
    for nombre, var_id in [
        ("prestamos_tarjeta", BCRA_VARIABLES["prestamos_tarjeta"]),
        ("prestamos_personales", BCRA_VARIABLES["prestamos_personales"]),
        ("prestamos_hipotecarios", BCRA_VARIABLES["prestamos_hipotecarios"]),
    ]:
        try:
            results[nombre] = _ultimo(var_id)
            logger.info("BCRA %s OK", nombre)
        except Exception as e:
            logger.error("BCRA %s FAIL: %s", nombre, e)

    # Índice de endeudamiento de consumo (tarjeta + personales)
    if "prestamos_tarjeta" in results and "prestamos_personales" in results:
        consumo = results["prestamos_tarjeta"]["valor"] + results["prestamos_personales"]["valor"]
        fecha = results["prestamos_tarjeta"]["fecha"]
        results["credito_consumo_total"] = {
            "valor": consumo,
            "fecha": fecha,
            "unidad": "Millones de pesos",
            "nota": "Tarjeta + personales. Proxy de endeudamiento familiar de consumo.",
        }
        # Serie mensual (tarjeta + personales) para la variación interanual real.
        try:
            per = _serie_mensual(BCRA_VARIABLES["prestamos_personales"])
            tar = _serie_mensual(BCRA_VARIABLES["prestamos_tarjeta"])
            tmap = {p["fecha"][:7]: p["valor"] for p in tar}
            serie = [{"fecha": p["fecha"], "valor": p["valor"] + tmap[p["fecha"][:7]]}
                     for p in per if p["fecha"][:7] in tmap]
            if serie:
                results["credito_consumo_serie"] = serie
                logger.info("BCRA credito_consumo_serie OK: %d meses", len(serie))
        except Exception as e:
            logger.error("BCRA credito_consumo_serie FAIL: %s", e)

    # Tasa BADLAR (costo de financiamiento — contexto)
    try:
        results["badlar"] = _ultimo(BCRA_VARIABLES["badlar"])
    except Exception as e:
        logger.error("BCRA BADLAR FAIL: %s", e)

    return results
