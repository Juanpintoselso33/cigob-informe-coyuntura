"""Resultado primario y gasto de funcionamiento desde la planilla de Economía (ADR-0443).

El Informe Mensual de Ingresos y Gastos (IMIG) sale en la página de Hacienda el día
del comunicado del resultado fiscal (16 a 18 del mes siguiente). La serie de
datos.gob.ar con los mismos números se actualiza semanas después: septiembre de
2026 salió el 16-oct y entró a la API a mediados de noviembre; octubre salió el
16-nov y al 27-nov la API seguía en septiembre. Este módulo completa la serie de
la API con los meses que la planilla ya tiene y la API todavía no.

La historia sigue saliendo de la API (la planilla trae sólo el año en curso). Si
en un mes que tienen las dos los números no coinciden, no se usa la planilla:
mejor un mes de atraso que una serie cosida con dos fuentes que dicen distinto.
"""
from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from functools import lru_cache
from urllib.parse import urljoin, urlparse

import openpyxl
import requests
from bs4 import BeautifulSoup

PAGINA = "https://www.argentina.gob.ar/economia/sechacienda/infoestadistica"
HOJA = "mensualizacion"
# Serie de datos.gob.ar → fila de la hoja «Mensualizacion» del IMIG.
SERIES = {
    "452.3_RESULTADO_RIO_0_M_18_54": "resultado primario",
    "452.2_SALARIOSIOS_0_T_8_22": "salarios",
    "452.2_OTROS_GASTNTO_0_T_27_55": "otros gastos de funcionamiento",
}
MESES = {m: i + 1 for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}
TOLERANCIA = 0.001   # 0,1 %: en los meses comunes la planilla y la API dan lo mismo


def _norm(valor) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(valor))
                            if not unicodedata.combining(c)).lower().split())


def descubrir(html: str) -> list[str]:
    """Los enlaces mensuales del año más reciente, del último mes al primero.

    La página lista los años del más nuevo al más viejo y, dentro de cada uno,
    los meses de enero en adelante; los nombres de archivo no siguen ninguna
    regla (`octubre.zip`, `marzo_26.xlsx`, `cuentas_publicas3.rar`)."""
    bloque, anterior = [], 0
    for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        mes = MESES.get(_norm(a.get_text()))
        url = urljoin(PAGINA, a["href"])
        partes = urlparse(url)
        if not mes or partes.netloc != "www.argentina.gob.ar" or not partes.path.startswith("/sites/default/files/"):
            continue
        if mes <= anterior:
            break                      # empezó el año anterior
        bloque.append(url)
        anterior = mes
    if not bloque:
        raise ValueError("No se encontraron los archivos mensuales del IMIG")
    return bloque[::-1]


def libro(contenido: bytes, url: str) -> bytes:
    """El .xlsx del IMIG: suelto, o dentro de un .zip junto con el de base caja."""
    if not zipfile.is_zipfile(io.BytesIO(contenido)):
        raise ValueError(f"Formato no soportado: {url}")      # .rar, html de error
    with zipfile.ZipFile(io.BytesIO(contenido)) as z:
        nombres = z.namelist()
        if "[Content_Types].xml" in nombres:                   # ya es un .xlsx
            return contenido
        imig = [n for n in nombres if n.lower().endswith(".xlsx")
                and _norm(n.rsplit("/", 1)[-1]).startswith("imig")]
        if not imig:
            raise ValueError(f"El archivo {url} no trae la planilla del IMIG")
        return z.read(imig[0])


def parsear(contenido: bytes) -> dict[str, dict[str, float]]:
    """{fila: {AAAA-MM: valor en millones de pesos}} de la hoja «Mensualizacion»."""
    wb = openpyxl.load_workbook(io.BytesIO(contenido), data_only=True, read_only=True)
    hojas = [h for h in wb.sheetnames if _norm(h) == HOJA]
    if len(hojas) != 1:
        raise ValueError("Hoja «Mensualizacion» ausente o ambigua")
    filas = list(wb[hojas[0]].iter_rows(values_only=True))
    cab = next((r for r in filas if sum(hasattr(x, "year") for x in r) >= 1), None)
    if cab is None:
        raise ValueError("Sin fila de meses en la hoja")
    columnas = {j: f"{x.year}-{x.month:02d}" for j, x in enumerate(cab) if hasattr(x, "year")}
    salida: dict[str, dict[str, float]] = {}
    buscadas = set(SERIES.values())
    for r in filas:
        etiqueta = next((_norm(x) for x in r if isinstance(x, str) and x.strip()), None)
        if etiqueta in buscadas and etiqueta not in salida:
            valores = {ym: float(r[j]) for j, ym in columnas.items()
                       if j < len(r) and isinstance(r[j], (int, float))}
            if valores:
                salida[etiqueta] = valores
    faltan = buscadas - set(salida)
    if faltan:
        raise ValueError(f"Filas ausentes en el IMIG: {sorted(faltan)}")
    return salida


@lru_cache(maxsize=1)
def planilla() -> dict:
    """La planilla del último mes publicado. Un .rar o un archivo roto pasa al mes anterior."""
    pagina = requests.get(PAGINA, timeout=40, headers={"User-Agent": "Mozilla/5.0"})
    pagina.raise_for_status()
    errores = []
    for url in descubrir(pagina.text)[:3]:
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return {"filas": parsear(libro(r.content, url)), "url": url}
        except Exception as e:  # noqa: BLE001
            errores.append(f"{url}: {e}")
    raise ValueError("Ningún archivo reciente del IMIG se pudo leer: " + " | ".join(errores))


def completar(filas_api: list, series_id: str, limit: int, fuente: dict | None = None) -> list:
    """Las filas de la API ([fecha, valor], de la más nueva a la más vieja) más los
    meses posteriores que ya trae la planilla. Si en algún mes común no coinciden,
    devuelve las de la API sin tocar."""
    fuente = fuente if fuente is not None else planilla()
    pl = fuente["filas"][SERIES[series_id]]
    api = {str(f[0])[:7]: f[1] for f in filas_api if f[1] is not None}
    comunes = set(api) & set(pl)
    if not comunes:
        return filas_api
    for ym in comunes:
        if abs(pl[ym] - api[ym]) > TOLERANCIA * max(abs(api[ym]), 1.0):
            raise ValueError(f"IMIG y datos.gob.ar no coinciden en {ym}: {pl[ym]} contra {api[ym]}")
    ultimo = max(api)
    nuevos = {ym: v for ym, v in pl.items() if ym > ultimo}
    # Una fila de la API para ese mes con valor nulo no se conserva al lado de la
    # de la planilla: duplicaría el mes y le comería un lugar al límite (Codex).
    filas = [[f"{ym}-01", v] for ym, v in nuevos.items()] + \
        [list(f) for f in filas_api if str(f[0])[:7] not in nuevos]
    filas.sort(key=lambda f: str(f[0]), reverse=True)
    return filas[:limit]


def con_planilla(series_id: str, filas_api: list, limit: int) -> list:
    """`completar` para los colectores: si la planilla falla, quedan las filas de la
    API y se avisa en el log (el dato no se pierde, sólo vuelve a esperar a la API)."""
    if series_id not in SERIES:
        return filas_api
    try:
        return completar(filas_api, series_id, limit)
    except Exception as e:  # noqa: BLE001
        print(f"  [IMIG] {SERIES[series_id]}: se usa sólo datos.gob.ar ({e})")
        return filas_api
