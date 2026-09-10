"""Bienes de capital del ICA: original vigente sobre la historia anterior de API."""
from datetime import date
from functools import lru_cache
import math
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import xlrd

from indec_actividad import _normalizar, MESES

CATALOGO = "https://www.indec.gob.ar/Nivel4/Tema/3/2/40"
MESES_CORTOS = {**MESES, **{m[:3]: n for m, n in MESES.items()}}


def descubrir(html, hoy=None):
    hoy = hoy or date.today()
    candidatos = []
    for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        url = urljoin(CATALOGO, a["href"])
        u = urlparse(url)
        m = re.fullmatch(r"/ftp/cuadros/economia/impo_uso_economico_(20\d{2})_(20\d{2})\.xls", u.path)
        if (u.scheme == "https" and u.netloc == "www.indec.gob.ar" and m
                and int(m[2]) == int(m[1]) + 1 and int(m[2]) <= hoy.year):
            candidatos.append((int(m[2]), url))
    if not candidatos:
        raise ValueError("ICA sin planilla mensual de usos económicos")
    return max(candidatos)[1]


def parsear(contenido, hoy=None):
    hoy = hoy or date.today()
    libro = xlrd.open_workbook(file_contents=contenido)
    hojas = [s for s in libro.sheets() if any(
        "importaciones mensuales por usos economicos" in _normalizar(s.cell_value(0, j))
        for j in range(min(3, s.ncols)))]
    if len(hojas) != 1:
        raise ValueError("Cuadro mensual de importaciones ausente o ambiguo")
    s = hojas[0]
    posiciones = [(i, j) for i in range(min(10, s.nrows)) for j in range(s.ncols)
                  if _normalizar(s.cell_value(i, j)) == "bienes de capital (bk)"]
    if len(posiciones) != 1:
        raise ValueError("Columna BK ausente o ambigua")
    fila, col = posiciones[0]
    periodos = [j for j in range(s.ncols) if _normalizar(s.cell_value(fila, j)) == "periodo"]
    if len(periodos) != 1:
        raise ValueError("Columna de períodos no identificable")
    if not any(_normalizar(s.cell_value(i, col)) == "millones de usd"
               for i in range(fila + 1, min(fila + 8, s.nrows))):
        raise ValueError("Unidad de bienes de capital no reconocida")
    anios = []
    for j in (col, col + 1):
        m = re.fullmatch(r"ano (20\d{2})\*?", _normalizar(s.cell_value(fila + 1, j)))
        if not m:
            raise ValueError("Año de bienes de capital no reconocido")
        anios.append(int(m[1]))
    if anios[0] != anios[1] + 1:
        raise ValueError("Años de bienes de capital no consecutivos")
    serie = {}
    for i in range(fila + 2, s.nrows):
        mes = MESES_CORTOS.get(_normalizar(s.cell_value(i, periodos[0])))
        if not mes:
            continue
        for offset, anio in enumerate(anios):
            v = s.cell_value(i, col + offset)
            if v == "":
                continue
            if not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ValueError("Nivel BK inválido")
            if anio * 12 + mes >= hoy.year * 12 + hoy.month:
                raise ValueError("BK contiene un mes no cerrado")
            clave = f"{anio}-{mes:02d}-01"
            if clave in serie:
                raise ValueError("Mes BK duplicado")
            serie[clave] = float(v)
    anterior = [k for k in sorted(serie) if k.startswith(str(anios[1]))]
    actual = [int(k[5:7]) for k in sorted(serie) if k.startswith(str(anios[0]))]
    if len(anterior) != 12 or not actual or actual != list(range(1, max(actual) + 1)):
        raise ValueError("Calendario BK incompleto")
    return serie


@lru_cache(maxsize=1)
def original():
    r = requests.get(CATALOGO, timeout=40)
    r.raise_for_status()
    url = descubrir(r.text)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return {"serie": parsear(r.content), "url": url}


def completar(api, original, limit):
    """El original reemplaza íntegramente su ventana, sin truncar los años previos.

    Si API va por delante, el original consultado no acredita estar vigente:
    se exige resolver esa discrepancia antes de producir un dato nuevo.
    """
    if not original:
        raise ValueError("BK sin original validado")
    fechas = [f for f, v in api if v is not None]
    if fechas and max(fechas) > max(original):
        raise ValueError("API BK más reciente que el original consultado")
    primero = min(original)
    serie = {}
    for f, v in api:
        if v is None or f >= primero:
            continue
        fecha = date.fromisoformat(f)
        if (fecha.day != 1 or f in serie or not isinstance(v, (int, float))
                or not math.isfinite(v) or v < 0):
            raise ValueError("Historia anterior de BK inválida o duplicada")
        serie[f] = v
    serie.update(original)
    return [[f, serie[f]] for f in sorted(serie, reverse=True)[:limit]]
