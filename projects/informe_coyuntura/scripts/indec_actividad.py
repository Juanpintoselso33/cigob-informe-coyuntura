"""IPI e ISAC desde las planillas originales, compartidos por todos los motores."""
from datetime import date, datetime
from functools import lru_cache
import math
import re
import unicodedata
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import xlrd

SERIES = {
    "453.1_SERIE_ORIGNAL_0_0_14_46": ("ipi", "original"),
    "453.1_SERIE_DESEADA_0_0_24_58": ("ipi", "desestacionalizada"),
    "33.2_ISAC_NIVELRAL_0_M_18_63": ("isac", "original"),
    "33.2_ISAC_SIN_EDAD_0_M_23_56": ("isac", "desestacionalizada"),
}
PAGINAS = {"ipi": "https://www.indec.gob.ar/Nivel4/Tema/3/6/14",
           "isac": "https://www.indec.gob.ar/Nivel4/Tema/3/3/42"}
MESES = {m: i + 1 for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}


def _normalizar(valor):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(valor))
                            if not unicodedata.combining(c)).lower().split())


def descubrir(html, tipo, hoy=None):
    """El año del archivo cambia; se sigue el enlace oficial de la operación."""
    hoy = hoy or date.today()
    nombre = "ipi_manufacturero" if tipo == "ipi" else "isac"
    candidatos = set()
    for enlace in BeautifulSoup(html, "html.parser").select("a[href]"):
        url = urljoin(PAGINAS[tipo], enlace["href"])
        partes = urlparse(url)
        m = re.fullmatch(r"/ftp/cuadros/economia/sh_" + nombre + r"_(20\d{2})\.xls", partes.path)
        if (partes.scheme == "https" and partes.netloc == "www.indec.gob.ar"
                and m and int(m[1]) <= hoy.year):
            candidatos.add((int(m[1]), url))
    if not candidatos:
        raise ValueError("No se encontró la planilla oficial de " + tipo)
    return max(candidatos)[1]


def parsear(contenido, tipo, hoy=None):
    """Exige identidad, niveles positivos y meses consecutivos ya cerrados."""
    hoy = hoy or date.today()
    libro = xlrd.open_workbook(file_contents=contenido)
    hojas = [s for s in libro.sheets() if _normalizar(s.name) == "cuadro 1"]
    if len(hojas) != 1:
        raise ValueError("Cuadro de nivel general ausente o ambiguo")
    hoja = hojas[0]
    titulo = _normalizar(hoja.cell_value(0, 0))
    esperado = "ipi manufacturero nivel general" if tipo == "ipi" else "indicador sintetico de la actividad de la construccion"
    if esperado not in titulo or "base 2004=100" not in titulo:
        raise ValueError("Identidad o base del cuadro de actividad incorrecta")
    cabeceras = [(i, j) for i in range(min(8, hoja.nrows)) for j in range(hoja.ncols)
                 if _normalizar(hoja.cell_value(i, j)) == "serie original"]
    if len(cabeceras) != 1:
        raise ValueError("Serie original ausente o ambigua")
    inicio, original = cabeceras[0]
    des = [j for j in range(hoja.ncols)
           if _normalizar(hoja.cell_value(inicio, j)).startswith("serie desestacionalizada")]
    if original < 2 or len(des) != 1:
        raise ValueError("Columnas de actividad no identificables")
    salida = {"original": {}, "desestacionalizada": {}}
    anio, anterior = None, None
    for i in range(inicio + 1, hoja.nrows):
        m = re.fullmatch(r"(20\d{2})(?:\.0|\*)?", str(hoja.cell_value(i, original - 2)).strip())
        if m:
            anio = int(m[1])
        mes = MESES.get(_normalizar(hoja.cell_value(i, original - 1)))
        if not mes:
            if anio and isinstance(hoja.cell_value(i, original), (int, float)):
                raise ValueError("Nivel de actividad sin mes reconocible")
            continue
        if anio is None:
            raise ValueError("Mes de actividad sin año")
        ordinal = anio * 12 + mes
        if ordinal >= hoy.year * 12 + hoy.month:
            raise ValueError("Actividad contiene un mes no cerrado")
        if anterior is not None and ordinal != anterior + 1:
            raise ValueError("Meses de actividad duplicados o discontinuos")
        anterior = ordinal
        for clave, columna in (("original", original), ("desestacionalizada", des[0])):
            valor = float(hoja.cell_value(i, columna))
            if not math.isfinite(valor) or valor <= 0:
                raise ValueError("Nivel de actividad inválido")
            salida[clave][f"{anio}-{mes:02d}"] = valor
    if len(salida["original"]) < 13:
        raise ValueError("Historia de actividad insuficiente para un interanual")
    return salida


@lru_cache(maxsize=2)
def niveles(tipo):
    """Una descarga por operación y proceso; no vuelve a una API atrasada."""
    pagina = requests.get(PAGINAS[tipo], timeout=40)
    pagina.raise_for_status()
    url = descubrir(pagina.text, tipo)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return {**parsear(r.content, tipo), "fuente_url": url,
            "obtenido_en": datetime.now().astimezone().isoformat(timespec="seconds")}


def filas(series_id, limit=48):
    tipo, variante = SERIES[series_id]
    serie = niveles(tipo)[variante]
    return [[mes + "-01", serie[mes]] for mes in sorted(serie, reverse=True)[:limit]]
