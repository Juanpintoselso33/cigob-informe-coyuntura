"""IPC nivel general nacional desde la planilla original del INDEC.

La API de series de datos.gob.ar replica el IPC con días de atraso: el 20-oct-2026
el INDEC llevaba una semana publicado septiembre (1,9%) y la API seguía en agosto.
El IPC es el deflactor de medio Monitor —recaudación, crédito real, capacidad
prestable, actividad tributaria—, así que ese atraso dejaba cinco cards de macro,
y las de los otros cinturones que deflactan, un mes detrás del organismo.

`datos_gob.get` usa esta planilla para COMPLETAR la serie de la API con los meses
que la API todavía no tiene, nunca para reemplazarla: el mes en común tiene que
coincidir, o no se agrega nada.
"""
import logging

import requests
import xlrd

logger = logging.getLogger(__name__)

SERIE_ID = "148.3_INIVELNAL_DICI_M_26"          # IPC nivel general nacional, base dic-2016
URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_divisiones.xls"
HOJA = "Índices IPC Cobertura Nacional"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}

_memo: list = []


def parsear(contenido: bytes) -> list:
    """[[YYYY-MM-01, nivel], ...] ascendente, del bloque «Total nacional».

    La hoja trae un bloque por región; el primero es el total nacional. Su fila
    de fechas (serial de Excel) es la que dice «Total nacional» en la primera
    columna, y el índice es la primera fila «Nivel general» que le sigue.
    """
    libro = xlrd.open_workbook(file_contents=contenido)
    hoja = libro.sheet_by_name(HOJA)
    fila_fechas = None
    for r in range(hoja.nrows):
        etiqueta = str(hoja.cell_value(r, 0)).strip()
        if fila_fechas is None and etiqueta == "Total nacional":
            fila_fechas = r
        elif fila_fechas is not None and etiqueta == "Nivel general":
            fechas, niveles = hoja.row_values(fila_fechas), hoja.row_values(r)
            serie = []
            for f, v in zip(fechas[1:], niveles[1:]):
                if isinstance(f, float) and isinstance(v, float) and v > 0:
                    d = xlrd.xldate_as_datetime(f, libro.datemode)
                    serie.append([f"{d.year:04d}-{d.month:02d}-01", v])
            if not serie:
                break
            return serie
    raise ValueError("planilla del IPC: no encontré el nivel general nacional")


def serie() -> list:
    if not _memo:
        r = requests.get(URL, headers=HTTP_HEADERS, timeout=60)
        r.raise_for_status()
        _memo.extend(parsear(r.content))
    return _memo


def completar(filas_api: list, original: list, tolerancia: float = 0.01) -> list:
    """Filas de la API más los meses posteriores que sólo trae el original.

    `filas_api` = [[fecha, valor], ...] en cualquier orden. Devuelve [] si no hay
    nada que agregar o si el último mes de la API no coincide con el original
    (dos series distintas no se empalman).
    """
    api = {str(f)[:10]: v for f, v in filas_api if v is not None}
    if not api:
        return []
    ultimo = max(api)
    orig = {f: v for f, v in original}
    if ultimo not in orig or abs(orig[ultimo] - api[ultimo]) > tolerancia:
        logger.warning("IPC: la planilla del INDEC no coincide con la API en %s "
                       "(%s contra %s); no se completa", ultimo, orig.get(ultimo), api[ultimo])
        return []
    return [[f, v] for f, v in original if f > ultimo]
