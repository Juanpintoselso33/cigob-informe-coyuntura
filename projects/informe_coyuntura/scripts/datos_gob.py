"""Pedidos a la API de series de datos.gob.ar que no se dejan engañar por respuestas a medias.

Desde el 12-oct-2026 la API contesta 200 con la misma serie de tres maneras según
el servidor que atienda: completa, vacía (`"data": []`, `count` 0) o recortada.
Medido el 15-oct con diez pedidos frescos por serie: el EMAE vino 7 veces con 271
filas y 3 con 167; la faena vacuna, 6 veces vacía. Y hay series que ningún servidor
tiene enteras: «otros gastos de funcionamiento» del IMIG vuelve siempre con 28 de
sus 128 filas (2016 a 2018), aunque el CSV oficial llega a agosto de 2026. Los
runners de GitHub se lo comían entero: cada noche fallaban series distintas, la
card y la serie del mismo indicador salían de lecturas distintas y el gate frenaba
la publicación (G3 card ≠ serie, G7 anclas del panel sin el 4T-2023).

Lo que no viene roto es el catálogo: con `metadata=full`, cada serie trae
`time_index_size`, cuántas filas tiene de verdad. Entonces, para un pedido de una
sola serie, `get` acepta la primera lectura con todas las filas que declara el
catálogo; si ninguna de `LECTURAS_MAX` las trae, arma la respuesta desde el CSV de
la distribución (`downloadURL`, columna `title`). Cada lectura lleva un parámetro
propio, porque la misma URL repetida devuelve la misma respuesta, buena o mala.

Un pedido de varias series a la vez se parte en pedidos de una y se vuelve a armar
con la misma forma (las sectoriales del EMAE son quince). Una respuesta sin catálogo
no tiene `time_index_size`: ahí se juntan `LECTURAS_BUENAS` lecturas no vacías y
gana la de más filas, porque un servidor roto puede quitar filas pero no agregarlas.

Si todo falla, la última respuesta, y el que llama decide como hasta ahora (cache o
error). Un error de red se reintenta una sola vez: una API colgada no tiene que
comerse el tope de tiempo de la corrida.
"""
import csv
import io
import logging
import time
from itertools import count

import requests
from requests import RequestException

logger = logging.getLogger(__name__)

LECTURAS_BUENAS = 3
LECTURAS_MAX = 6
ESPERA = 0.5
LIMITE_API = 100            # el `limit` por defecto de la API
_numero = count(1)
_csvs: dict[str, str] = {}


def _cuerpo(r):
    try:
        cuerpo = r.json()
    except ValueError:
        return None
    return cuerpo if isinstance(cuerpo, dict) and "count" in cuerpo else None


def _campo(cuerpo) -> dict:
    for m in cuerpo.get("meta") or []:
        if isinstance(m, dict) and "field" in m:
            return {**m.get("distribution", {}), **m["field"]}
    return {}


def _declaradas(cuerpo) -> int | None:
    try:
        return int(_campo(cuerpo)["time_index_size"])
    except (KeyError, TypeError, ValueError):
        return None


class _DesdeCSV:
    """Respuesta armada desde el CSV oficial, con la forma de la de la API."""

    def __init__(self, cuerpo):
        self._cuerpo = cuerpo
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._cuerpo


def _desde_csv(cuerpo_api, params: dict, timeout):
    campo = _campo(cuerpo_api)
    url, columna = campo.get("downloadURL"), campo.get("title")
    if not url or not columna:
        return None
    if url not in _csvs:
        r = requests.get(url, timeout=timeout or 60)
        r.raise_for_status()
        _csvs[url] = r.content.decode("utf-8-sig")
    # El CSV se actualiza antes que la API: puede traer un mes que el catálogo
    # todavía no declara. Se corta en `time_index_end` para que la lectura desde
    # el CSV sea la misma que una completa de la API; si no, dos series del mismo
    # indicador terminan en meses distintos (16-oct: SIPA con 174 y 175 filas).
    fin = str(campo.get("time_index_end") or "")[:10]
    filas = []
    for fila in csv.DictReader(io.StringIO(_csvs[url])):
        valor = (fila.get(columna) or "").strip()
        fecha = fila["indice_tiempo"][:10]
        if valor and (not fin or fecha <= fin):
            filas.append([fecha, float(valor)])
    filas.sort(key=lambda f: f[0], reverse=params.get("sort") == "desc")
    limite = int(params.get("limit", LIMITE_API))
    return _DesdeCSV({"data": filas[:limite], "count": len(filas),
                      "meta": cuerpo_api.get("meta", [])})


def _juntar(url: str, params: dict, **kwargs):
    """Un pedido de varias series, hecho serie por serie y rearmado igual que la API:
    `data` = [fecha, v1, v2, …] en el orden de `ids`, `meta` = [índice, campo1, …]."""
    ids = str(params["ids"]).split(",")
    columnas, metas = [], []
    for sid in ids:
        cuerpo = get(url, params={**params, "ids": sid}, **kwargs).json()
        columnas.append({f[0]: f[1] for f in cuerpo.get("data") or []})
        meta = cuerpo.get("meta") or []
        metas.append(meta[1] if len(meta) > 1 else {"field": {"id": sid}})
    fechas = sorted(set().union(*columnas), reverse=params.get("sort") == "desc")
    filas = [[f] + [c.get(f) for c in columnas] for f in fechas]
    limite = int(params.get("limit", LIMITE_API))
    return _DesdeCSV({"data": filas[:limite], "count": len(filas),
                      "meta": [{"frequency": None}] + metas})


def get(url: str, params: dict | None = None, **kwargs):
    """Como `requests.get`, pero devuelve una lectura completa de la serie."""
    params = dict(params or {})
    ids = str(params.get("ids", ""))
    if "," in ids:
        return _juntar(url, params, **kwargs)
    una_serie = bool(ids)
    if una_serie:
        params.setdefault("metadata", "full")
    mejor, mejor_filas, mejor_cuerpo = None, -1, None
    buenas = errores = 0
    ultima = None
    vistas = []
    for lectura in range(LECTURAS_MAX):
        if lectura:
            time.sleep(ESPERA)
        try:
            r = requests.get(url, params={**params, "_lectura": next(_numero)}, **kwargs)
            r.raise_for_status()
        except RequestException:
            errores += 1
            if errores < 2:
                continue
            if mejor is not None:
                return mejor
            raise
        ultima = r
        cuerpo = _cuerpo(r)
        if cuerpo is None:
            # Sin `count` no hay con qué comparar (o no es esta API): como antes.
            return r
        filas = cuerpo["count"]
        vistas.append(filas)
        declaradas = _declaradas(cuerpo) if una_serie else None
        if declaradas is not None and filas >= declaradas > 0:
            if lectura:
                logger.warning("datos.gob.ar: %s completa recién en la lectura %d %s",
                               ids, lectura + 1, vistas)
            return r
        if filas > mejor_filas and filas > 0:
            mejor, mejor_filas, mejor_cuerpo = r, filas, cuerpo
        if filas > 0:
            buenas += 1
        if declaradas is None and buenas >= LECTURAS_BUENAS:
            break
    declaradas = _declaradas(mejor_cuerpo or _cuerpo(ultima) or {}) if una_serie and ultima else None
    if declaradas and mejor_filas < declaradas:
        try:
            r = _desde_csv(mejor_cuerpo or _cuerpo(ultima), params, kwargs.get("timeout"))
            if r is not None:
                logger.warning("datos.gob.ar: %s nunca vino completa %s de %d filas; "
                               "se usa el CSV oficial (%d filas)",
                               ids, vistas, declaradas, r.json()["count"])
                return r
        except Exception as e:                                # noqa: BLE001
            logger.warning("datos.gob.ar: %s incompleta y el CSV no se pudo leer (%s)", ids, e)
    if len(set(vistas)) > 1:
        logger.warning("datos.gob.ar devolvió %s desparejo %s; se usa la de %d filas",
                       ids, vistas, mejor_filas)
    if mejor is not None:
        return mejor
    if ultima is None:
        raise RequestException(f"datos.gob.ar no contestó {ids}")
    return ultima
