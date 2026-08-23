"""Canasta de servicios públicos del AMBA sobre el RIPTE (IIEP UBA-CONICET).

El dato sustituye como card al IPC Regulados: éste incluye salud, educación,
telefonía y cigarrillos y no mide el peso de las tarifas en un ingreso.
"""
from __future__ import annotations

import html
import re
from functools import lru_cache
from io import BytesIO
from datetime import date

import requests
from pypdf import PdfReader

try:  # import de paquete en tests; fallback para main.py ejecutado como script
    from ..config import HTTP_HEADERS, HTTP_TIMEOUT
except ImportError:  # pragma: no cover - ruta operativa del colector
    try:
        from config import HTTP_HEADERS, HTTP_TIMEOUT
    except ImportError:  # import aislado junto al config raíz del proyecto
        HTTP_TIMEOUT = 30
        HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}


BUSQUEDA = "https://economicas.uba.ar/iiep/wp-json/wp/v2/search"
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def _texto(markup: str) -> str:
    limpio = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(limpio)).strip()


def _periodo(titulo: str) -> str | None:
    m = re.search(
        r"Tarifas y Subsidios\s+(" + "|".join(MESES) + r")\s+(20\d{2})",
        titulo,
        re.I,
    )
    if not m:
        return None
    return f"{int(m.group(2)):04d}-{MESES[m.group(1).lower()]:02d}-01"


def _parsear_reporte(markup: str, titulo: str, url: str) -> dict:
    texto = _texto(markup)
    peso = re.search(r"(-?\d+(?:[.,]\d+)?)%\s+PESO EN EL SALARIO", texto, re.I)
    if not peso:
        raise ValueError(f"IIEP sin 'PESO EN EL SALARIO': {url}")
    variacion = re.search(r"(-?\d+(?:[.,]\d+)?)%\s+CANASTA DE SERVICIOS", texto, re.I)
    cobertura = re.search(r"(-?\d+(?:[.,]\d+)?)%\s+COBERTURA TARIFARIA", texto, re.I)
    transporte = re.search(
        r"transporte\s*\(\s*(\d+(?:[.,]\d+)?)%\s+de la canasta\s*\)", texto, re.I
    )
    numero = lambda m: float(m.group(1).replace(",", ".")) if m else None
    return {
        "valor": numero(peso),
        "peso_salario_pct": numero(peso),
        "variacion_mensual_pct": numero(variacion),
        "cobertura_costos_pct": numero(cobertura),
        "transporte_pct_canasta": numero(transporte),
        "fecha": _periodo(titulo),
        "url": url,
    }


def _parsear_texto_pdf(texto: str, titulo: str, url: str) -> dict:
    """Extrae valores textuales del informe; nunca interpola barras del gráfico."""
    limpio = re.sub(r"\s+", " ", texto).strip()
    patron_num = r"(\d(?:\s*\d)*(?:[.,]\d+)?)"
    peso = re.search(r"representa\s+el\s+" + patron_num + r"%\s+del\s+salario", limpio, re.I)
    transporte = re.search(
        r"peso\s+del\s+gasto\s+en\s+transporte\s+explica\s+el\s+"
        + patron_num + r"%",
        limpio,
        re.I,
    )
    if not transporte:
        transporte = re.search(r"gasto\s+en\s+transporte\s+explica\s+el\s+" + patron_num + r"%", limpio, re.I)
    if not transporte:
        transporte = re.search(
            r"peso\s+del\s+gasto\s+en\s+transporte\s+sobre\s+el\s+salario\s+"
            r"representa\s+el\s+" + patron_num + r"%",
            limpio,
            re.I,
        )
    if not peso or not transporte:
        raise ValueError(f"IIEP PDF sin carga o desglose textual: {url}")
    variacion = re.search(
        r"Este\s+gasto\s+(aumentó|se\s+redujo)\s+" + patron_num + r"%\s+respecto",
        limpio,
        re.I,
    )
    numero = lambda s: float(re.sub(r"\s+", "", s).replace(",", "."))
    variacion_pct = None
    if variacion:
        variacion_pct = numero(variacion.group(2)) * (-1 if "redujo" in variacion.group(1).lower() else 1)
    return {
        "valor": numero(peso.group(1)),
        "peso_salario_pct": numero(peso.group(1)),
        "variacion_mensual_pct": variacion_pct,
        "cobertura_costos_pct": None,
        "transporte_pct_canasta": numero(transporte.group(1)),
        "fecha": _periodo(titulo),
        "url": url,
    }


def _parsear_pdf_desde_pagina(markup: str, titulo: str, url: str) -> dict:
    enlace = re.search(r'href=["\']([^"\']+\.pdf)', html.unescape(markup), re.I)
    if not enlace:
        raise ValueError(f"IIEP sin enlace PDF: {url}")
    r = requests.get(enlace.group(1), headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
    r.raise_for_status()
    lector = PdfReader(BytesIO(r.content))
    # El bloque de salario está en las primeras páginas; limitar la extracción
    # evita recorrer anexos largos de combustibles y subsidios.
    texto = " ".join((p.extract_text() or "") for p in lector.pages[:6])
    return _parsear_texto_pdf(texto, titulo, url)


def _validar_para_puntuar(dato: dict) -> dict:
    """El total sin desglose sirve para una nota, pero no para este indicador."""
    faltantes = [k for k in ("valor", "transporte_pct_canasta", "fecha")
                 if dato.get(k) is None]
    if faltantes:
        raise ValueError(f"IIEP sin campos necesarios para puntuar: {', '.join(faltantes)}")
    if dato["valor"] <= 0:
        raise ValueError(f"IIEP con peso en el salario inválido: {dato['valor']}")
    if not 0 <= dato["transporte_pct_canasta"] <= 100:
        raise ValueError(
            f"IIEP con participación del transporte inválida: "
            f"{dato['transporte_pct_canasta']}"
        )
    return dato


def _reportes() -> list[dict]:
    r = requests.get(
        BUSQUEDA,
        params={"search": "Reporte de Tarifas y Subsidios", "per_page": 100},
        headers=HTTP_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    encontrados = []
    for item in r.json():
        periodo = _periodo(item.get("title", ""))
        if periodo and periodo >= "2023-12-01":
            encontrados.append({**item, "periodo": periodo})
    if not encontrados:
        raise ValueError("IIEP no devolvió reportes mensuales desde dic-2023")
    return sorted(encontrados, key=lambda x: x["periodo"])


def fetch_iiep_tarifas() -> dict:
    ultimo = _reportes()[-1]
    r = requests.get(ultimo["url"], headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    dato = _validar_para_puntuar(
        _parsear_reporte(r.text, ultimo["title"], ultimo["url"])
    )
    if not dato["fecha"] or dato["fecha"] > date.today().strftime("%Y-%m-01"):
        raise ValueError(f"período IIEP inválido: {dato['fecha']}")
    return dato


def fetch_iiep_tarifas_serie() -> list[list]:
    """Historia publicada en las páginas mensuales del observatorio."""
    return [[d["fecha"], d["valor"]] for d in fetch_iiep_tarifas_historia()]


@lru_cache(maxsize=1)
def fetch_iiep_tarifas_historia() -> list[dict]:
    """Historia con el desglose necesario para puntuar cada grupo de gasto."""
    out = []
    for item in _reportes():
        r = requests.get(item["url"], headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        try:
            dato = _parsear_reporte(r.text, item["title"], item["url"])
        except ValueError:
            try:
                dato = _parsear_pdf_desde_pagina(r.text, item["title"], item["url"])
            except Exception:
                # Un PDF viejo sin texto seleccionable no invalida los demás
                # períodos: se omite, nunca se estima desde la línea del gráfico.
                continue
        try:
            out.append(_validar_para_puntuar(dato))
        except ValueError:
            continue
    if not out:
        raise ValueError("IIEP no produjo una serie textual de peso en el salario")
    return out
