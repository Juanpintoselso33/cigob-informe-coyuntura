"""Pedidos a la API de series de datos.gob.ar que no se dejan engañar por respuestas a medias.

Desde el 12-oct-2026 la API contesta 200 con la misma serie de tres maneras según
el servidor que atienda: completa, vacía (`"data": []`, `count` 0) o recortada.
Medido el 15-oct con diez pedidos frescos por serie: el EMAE vino 7 veces con 271
filas y 3 con 167; la faena vacuna, 6 veces vacía; el IPC regulados, 4. Los runners
de GitHub se lo comían entero: cada noche fallaban series distintas, la card y la
serie del mismo indicador salían de lecturas distintas y el gate frenaba la
publicación (G3 card ≠ serie, G7 anclas del panel sin el 4T-2023).

Dos lecturas iguales no prueban nada: la misma URL repetida devuelve la misma
respuesta, buena o mala. Por eso cada lectura lleva un parámetro propio que la
manda a un servidor al azar, y `get` junta `LECTURAS_BUENAS` lecturas no vacías
(hasta `LECTURAS_MAX` pedidos) y devuelve la de más filas: un servidor roto puede
quitar filas, nunca agregarlas. Si todas vinieron vacías devuelve la última, y el
que llama decide como hasta ahora (cache o error). Un error de red se reintenta una
sola vez: una API colgada no tiene que comerse el tope de tiempo de la corrida.
"""
import logging
import time
from itertools import count

import requests
from requests import RequestException

logger = logging.getLogger(__name__)

LECTURAS_BUENAS = 3
LECTURAS_MAX = 8
ESPERA = 0.5
_numero = count(1)


def _filas(r) -> int | None:
    """`count` de una respuesta de la API, o None si no lo trae."""
    try:
        cuerpo = r.json()
    except ValueError:
        return None
    if not isinstance(cuerpo, dict) or "count" not in cuerpo:
        return None
    return cuerpo["count"]


def get(url: str, params: dict | None = None, **kwargs):
    """Como `requests.get`, pero devuelve la lectura más completa de varias."""
    ids = (params or {}).get("ids")
    mejor, mejor_filas = None, -1
    buenas = errores = 0
    ultima = None
    vistas = []
    for lectura in range(LECTURAS_MAX):
        if lectura:
            time.sleep(ESPERA)
        try:
            r = requests.get(url, params={**(params or {}), "_lectura": next(_numero)},
                             **kwargs)
            r.raise_for_status()
        except RequestException:
            errores += 1
            if errores < 2:
                continue
            if mejor is not None:
                return mejor
            raise
        ultima = r
        filas = _filas(r)
        if filas is None:
            # Sin `count` no hay con qué comparar (o no es esta API): como antes.
            return r
        vistas.append(filas)
        if filas == 0:
            continue
        buenas += 1
        if filas > mejor_filas:
            mejor, mejor_filas = r, filas
        if buenas >= LECTURAS_BUENAS:
            break
    if len(set(vistas)) > 1:
        logger.warning("datos.gob.ar devolvió %s desparejo %s; se usa la de %d filas",
                       ids, vistas, mejor_filas)
    if mejor is not None:
        return mejor
    if ultima is None:
        raise RequestException(f"datos.gob.ar no contestó {ids}")
    return ultima
