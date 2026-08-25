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


# Rótulos de las columnas regionales y de las de variación. El cuadro trae
# Capital, Interior, GBA y Nacional, cada uno con su variación mensual al lado.
_REGIONALES = ("capital", "interior", "gba", "conurbano")
_RE_BANNER = re.compile(r"desagreg|series", re.IGNORECASE)


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def columna_icc_nacional(ws) -> int:
    """Índice de la columna «ICC Nacional», ubicada por su encabezado.

    Hasta ago-2026 el colector leía la **columna 1 por posición**, que es
    `ICC Capital`: publicaba el ICC de CABA rotulado como total nacional. En el
    corte auditado eso daba 39,87 donde el nacional era 40,23 (ADR-0242).

    El encabezado está partido en varias filas y hay una **trampa**: la fila 0
    trae el banner `ICC Nacional - Desagregación por regiones` **encima de la
    columna de Capital**. Un `"nacional" in encabezado` que incluyera esa fila
    volvería a elegir Capital, ahora con aire de estar bien ubicada. Por eso el
    banner se descarta y las regionales se excluyen explícitamente.
    """
    ancho = ws.ncols
    candidatas = []
    for j in range(1, ancho):
        partes = []
        for i in range(min(8, ws.nrows)):
            c = ws.cell(i, j)
            if c.ctype != xlrd.XL_CELL_TEXT:
                continue
            t = _norm(c.value)
            if not t or _RE_BANNER.search(t):
                continue
            partes.append(t)
        hdr = " ".join(partes)
        if not hdr or "variacion" in hdr:
            continue
        if any(r in hdr for r in _REGIONALES):
            continue
        if "icc" in hdr and "nacional" in hdr:
            candidatas.append(j)
    if len(candidatas) != 1:
        raise ValueError(
            f"no se pudo ubicar una única columna «ICC Nacional» "
            f"(candidatas: {candidatas}); el cuadro de la UTDT cambió de forma")
    return candidatas[0]


def _parse_icc_xls(content: bytes, columna: int | None = None) -> dict:
    """
    Parsea el Excel del ICC UTDT.
    La serie histórica tiene formato: columna fecha, columnas de índice.
    Busca la última fila con datos válidos.

    `columna=None` ubica la del total nacional por encabezado. El Índice Líder
    usa el mismo layout pero tiene una sola serie, y ahí se pasa la columna.
    """
    wb = xlrd.open_workbook(file_contents=content)
    ws = wb.sheets()[0]
    col = columna if columna is not None else columna_icc_nacional(ws)

    ultimo_fecha = None
    ultimo_valor = None

    for row_idx in range(ws.nrows - 1, -1, -1):
        fecha_cell = ws.cell(row_idx, 0)
        valor_cell = ws.cell(row_idx, col)

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

    return {"valor": ultimo_valor, "fecha": ultimo_fecha, "unidad": "Índice",
            "cobertura": "total nacional" if columna is None else "serie única"}


def _fetch_indice_lider(results: dict) -> None:
    """Índice Líder de la UTDT (ADR-0112): mismo mecanismo de descarga que el
    ICC, otra página de serie histórica. Un fallo acá no debe tumbar el ICC."""
    from config import UTDT_IL_LISTADO
    try:
        r = requests.get(UTDT_IL_LISTADO, headers=HTTP_HEADERS,
                         timeout=HTTP_TIMEOUT, verify=False)
        r.raise_for_status()
        fnames = sorted(set(re.findall(r"download\.php\?fname=([^\"'&]+)", r.text)))
        if not fnames:
            raise ValueError("sin link de descarga en el listado del Índice Líder")
        x = requests.get(UTDT_ICC_DOWNLOAD_BASE + fnames[0], headers=HTTP_HEADERS,
                         timeout=HTTP_TIMEOUT, verify=False)
        x.raise_for_status()
        il = _parse_icc_xls(x.content, columna=1)   # una sola serie: col 0 fecha, col 1 valor
        results["indice_lider"] = il
        logger.info("Índice Líder UTDT OK: %s = %s", il["fecha"], il["valor"])
    except Exception as e:
        logger.error("Índice Líder UTDT FAIL: %s", e)


def fetch_icc() -> dict:
    """
    Descarga y parsea el ICC UTDT y el Índice Líder.
    Retorna {'icc_utdt': {...}, 'indice_lider': {...}}.
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
    _fetch_indice_lider(results)
    return results
