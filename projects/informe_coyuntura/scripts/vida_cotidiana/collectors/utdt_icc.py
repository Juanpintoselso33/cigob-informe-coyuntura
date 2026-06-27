"""
Colector UTDT — Índice de Confianza del Consumidor (ICC)
Método: scraping del listado para obtener el fname del XLS más reciente,
        luego descarga y parseo del Excel.
Verificado: HTTP 200, descarga exitosa (184 KB), formato BIFF/OLE2.
"""
import io
import logging
import re

import requests
import xlrd  # pip install xlrd==1.2.0  (necesario para archivos .xls OLE2)

from config import UTDT_ICC_LISTADO, UTDT_ICC_DOWNLOAD_BASE, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _get_latest_xls_fname() -> str:
    """Scrapea el listado UTDT y extrae el fname del XLS más reciente."""
    r = requests.get(UTDT_ICC_LISTADO, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    # Busca patrones como: download.php?fname=_177694842963231300.xls
    matches = re.findall(r"download\.php\?fname=([^\"'\s>]+\.xls)", r.text, re.IGNORECASE)
    if not matches:
        raise ValueError("No se encontró ningún link de descarga .xls en el listado UTDT")
    return matches[0]


def _parse_icc_xls(content: bytes) -> dict:
    """
    Parsea el Excel del ICC UTDT.
    La serie histórica tiene formato: columna fecha, columna ICC.
    Busca la última fila con datos válidos.
    """
    wb = xlrd.open_workbook(file_contents=content)
    ws = wb.sheets()[0]

    ultimo_fecha = None
    ultimo_valor = None

    for row_idx in range(ws.nrows - 1, -1, -1):
        fecha_cell = ws.cell(row_idx, 0)
        valor_cell = ws.cell(row_idx, 1)

        # Fechas en xlrd tienen ctype=3 (XL_CELL_DATE); valores numéricos ctype=2
        if fecha_cell.ctype == xlrd.XL_CELL_DATE and valor_cell.ctype == xlrd.XL_CELL_NUMBER:
            try:
                fecha_tuple = xlrd.xldate_as_tuple(fecha_cell.value, wb.datemode)
                ultimo_fecha = f"{fecha_tuple[0]}-{fecha_tuple[1]:02d}-{fecha_tuple[2]:02d}"
                ultimo_valor = valor_cell.value
                break
            except Exception:
                continue

    if ultimo_valor is None:
        raise ValueError("No se pudo parsear ninguna fila válida del Excel ICC")

    return {"valor": ultimo_valor, "fecha": ultimo_fecha, "unidad": "Índice"}


def fetch_icc() -> dict:
    """
    Descarga y parsea el ICC UTDT.
    Retorna {'icc_utdt': {'valor': float, 'fecha': str, 'unidad': 'índice'}}.
    """
    results = {}
    try:
        fname = _get_latest_xls_fname()
        url = UTDT_ICC_DOWNLOAD_BASE + fname
        logger.info("Descargando ICC UTDT desde: %s", url)
        r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
        r.raise_for_status()
        icc = _parse_icc_xls(r.content)
        results["icc_utdt"] = icc
        logger.info("ICC UTDT OK: %s = %s", icc["fecha"], icc["valor"])
    except Exception as e:
        logger.error("ICC UTDT FAIL: %s", e)
    return results
