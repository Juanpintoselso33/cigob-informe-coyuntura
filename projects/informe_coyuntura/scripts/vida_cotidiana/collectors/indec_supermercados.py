"""Ventas en supermercados a precios constantes — INDEC, serie desestacionalizada.

Componente del ITCIS desde ADR-0225. **Antes era el ancla de validación
externa** del cinturón (ADR-0155), y el movimiento es exactamente el que sacó
al ICC en su momento: una serie que mide condiciones materiales del hogar es
un componente del índice, no un juez del índice.

## Qué mide, y por qué es distinto de todo lo demás que hay adentro

Es el único componente que mide **volumen efectivamente comprado**. Los otros
diecisiete miden ingreso (cuánto entra), precio (cuánto cuesta), empleo (de
dónde viene el ingreso), mora (qué no se paga), percepción (qué se opina) o
victimización. Ninguno mira lo que el hogar se llevó de la góndola.

Medido antes de incorporarlo: el 43% de su nivel y el **82% de su movimiento
mes a mes** no los puede reproducir el ITCIS con sus seis dimensiones juntas.

## La serie

`455.1_VENTAS_PREADA_0_M_44_44` de la API de datos.gob.ar: ventas a precios
constantes, **serie desestacionalizada publicada por el INDEC**. Se toma la
desestacionalizada de la fuente y no se suaviza acá — la regla que dejó ADR-0155
después de fabricarse una divergencia con una media móvil propia, que atrasa la
serie medio año y da vuelta el signo.

Lo que NO cubre, y va declarado en la ficha: comercio registrado de cadenas de
supermercados. No ve el comercio informal ni el almacén de barrio.

## El rezago, medido y no copiado

El mes M lo publica el INDEC unos 52 días después de terminado (el informe de
junio-2026 salió el 21-ago-2026), y la API tarda unos 13 días más en
espejarlo: mayo-2026 apareció en el catálogo el 5-ago-2026. Encadenado, el
último punto disponible tiene entre ~95 y ~126 días de antigüedad según en qué
parte del ciclo caiga la corrida. Por eso el tope del gate es 140 y no el
default de 110, que marcaría atraso todos los meses (ver `gate_calidad.MAX_DIAS`).
"""
import logging
import re

import requests

logger = logging.getLogger(__name__)

# Constantes propias y no importadas de `config`, por el mismo motivo que en
# `dnrpa_autos` y `trabajo_independiente`: este módulo se carga POR RUTA desde
# los tests y desde `descargar_series.py`, y ahí `import config` resuelve al
# `config.py` de la raíz del proyecto, que es otro archivo.
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"),
}
HTTP_TIMEOUT = 30

SERIES_API = "https://apis.datos.gob.ar/series/api/series/"
SERIE_ID = "455.1_VENTAS_PREADA_0_M_44_44"

# Los tres meses de la base del cinturón. Si la serie no los trae, el rebase a
# 4T-2023 no se puede hacer y el componente quedaría anclado contra otra cosa
# sin que nada avise: es la falla que este colector tiene que hacer ruidosa.
BASE_MESES = ("2023-10", "2023-11", "2023-12")

# La base del índice se LEE de la fuente, no se escribe acá. La card la
# rotulaba «2004 = 100» y la Encuesta de Supermercados vigente usa **base
# 2017=100**: la serie ni siquiera empieza antes de enero de 2017 (ADR-0243).
# `units` es el campo donde la API declara la base; si dejara de traerlo, el
# colector falla en vez de inventar un rótulo.
_RE_BASE = re.compile(r"base\s*(?:a[ñn]o\s*)?(\d{4})\s*=\s*100", re.IGNORECASE)


def base_declarada(meta: list) -> tuple[int, str]:
    """(año base, unidad textual) leídos de los metadatos de la serie.

    Falla si la API no declara una base reconocible. Es a propósito: el rótulo
    anterior —«2004 = 100»— no vino de ningún lado verificable y sobrevivió
    porque nadie tenía contra qué compararlo."""
    for bloque in meta or []:
        units = ((bloque.get("field") or {}).get("units") or "").strip()
        m = _RE_BASE.search(units)
        if m:
            return int(m.group(1)), units
    raise ValueError(
        f"{SERIE_ID}: la API no declara la base del índice en «units»; "
        "sin eso el rótulo de la card sería una suposición")


def fetch_consumo_supermercados() -> dict:
    """{'consumo_supermercados': {'valor', 'fecha', 'unidad'}, 'serie': {...}}.

    La card es el último punto de la MISMA serie que alimenta el índice: no hay
    dos caminos que puedan divergir. `descargar_series.py` reusa esta función.

    La unidad también sale de acá (ADR-0243), leída de los metadatos de la
    fuente: card, serie y web dejan de tener cada una su copia del rótulo.
    """
    r = requests.get(SERIES_API,
                     params={"ids": SERIE_ID, "format": "json", "limit": 5000,
                             "metadata": "full"},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    cuerpo = r.json()
    anio_base, _ = base_declarada(cuerpo.get("meta"))
    filas = cuerpo.get("data") or []
    serie = {f[0][:7]: float(f[1]) for f in filas if f[1] is not None}
    if not serie:
        raise ValueError(f"{SERIE_ID}: la API no devolvió ningún punto")

    faltan = [m for m in BASE_MESES if m not in serie]
    if faltan:
        raise ValueError(
            f"{SERIE_ID}: faltan meses de la base 4T-2023 ({', '.join(faltan)}); "
            "sin ellos el rebase del componente mediría contra otra base")

    primero = min(serie)
    if int(primero[:4]) < anio_base:
        raise ValueError(
            f"{SERIE_ID}: la serie arranca en {primero} pero la base declarada "
            f"es {anio_base}=100; una de las dos cosas cambió")

    ult = max(serie)
    unidad = f"índice ({anio_base} = 100, desestacionalizado)"
    logger.info("consumo_supermercados OK: %s = %.1f (%d meses, %s)",
                ult, serie[ult], len(serie), unidad)
    return {
        "consumo_supermercados": {"valor": round(serie[ult], 1), "fecha": ult,
                                  "unidad": unidad, "anio_base": anio_base},
        "serie": serie,
    }
