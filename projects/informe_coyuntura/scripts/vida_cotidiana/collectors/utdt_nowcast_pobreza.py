# -*- coding: utf-8 -*-
"""Colector del Nowcast de Pobreza (UTDT, González-Rozada) — ADR-0113.

Es la única medición de pobreza de frecuencia MENSUAL que existe para la
Argentina. El INDEC publica la tasa oficial dos veces al año y con varios meses
de rezago; este nowcast proyecta la estructura del mercado laboral y los deciles
de ingreso total familiar de la EPH contra la canasta básica total, y publica un
informe nuevo todos los meses con el semestre móvil vigente.

De dónde sale el dato: la página del autor en la UTDT lista los informes en PDF,
uno por mes. El `fname` de cada uno es un timestamp, así que el mayor es el más
reciente — no hace falta parsear fechas del listado.

Por qué el PDF y no otra vía: la serie estuvo en RPubs hasta 2021 y hoy se
publica como app Shiny (`mrozada.shinyapps.io/shinynowcast`) más estos informes.
Scrapear una app Shiny exige mantener un websocket y se rompe con cada cambio de
la app; el PDF es el formato estable y citable.
"""
import io
import logging
import re

import requests

from config import HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)

NOWCAST_PAGINA = "https://www.utdt.edu/profesores/mrozada/pobreza"
NOWCAST_DESCARGA = "https://www.utdt.edu/download.php?fname="

_MESES = {m: i + 1 for i, m in enumerate(
    ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])}

_RE_SEMESTRE = re.compile(r"Semestre\s+(\w+)\s+(\d{4})\s*-\s*(\w+)\s+(\d{4})")
_RE_TASA = re.compile(r"tasa de pobreza de\s+([\d.,]+)\s*por ciento")
_RE_IC = re.compile(r"confianza entre\s*\[\s*([\d.,]+)\s*%\s*,\s*([\d.,]+)\s*%\s*\]")


def _listar_informes() -> list:
    """fnames de los PDF publicados, del más viejo al más nuevo."""
    r = requests.get(NOWCAST_PAGINA, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    return sorted(set(re.findall(r"/download\.php\?fname=(_\d+\.pdf)", r.text)))


def _leer_informe(fname: str) -> dict | None:
    """{periodo, valor, ic_inf, ic_sup} de un informe, o None si no se puede leer.

    Devolver None en vez de propagar es deliberado: los informes más viejos
    tienen otro layout y no parsean, y eso no debe impedir leer los recientes.
    """
    import pdfplumber

    x = requests.get(NOWCAST_DESCARGA + fname, headers=HTTP_HEADERS,
                     timeout=HTTP_TIMEOUT * 3, verify=False)
    x.raise_for_status()
    with pdfplumber.open(io.BytesIO(x.content)) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])
    sem, tasa = _RE_SEMESTRE.search(texto), _RE_TASA.search(texto)
    if not (sem and tasa):
        return None
    ic = _RE_IC.search(texto)
    num = lambda s: float(s.replace(",", "."))
    return {
        # se fecha por el FIN del semestre estimado: es el mes más reciente que
        # el dato describe, y así ordena junto al resto de las series
        "periodo": f"{sem.group(4)}-{_MESES[sem.group(3)]:02d}",
        "semestre": f"{sem.group(1)} {sem.group(2)} - {sem.group(3)} {sem.group(4)}",
        "valor": num(tasa.group(1)),
        "ic_inf": num(ic.group(1)) if ic else None,
        "ic_sup": num(ic.group(2)) if ic else None,
    }


def fetch_nowcast_pobreza(historico: bool = False) -> dict:
    """{'pobreza_nowcast': {...}} con el informe más reciente.

    Con `historico=True` recorre todos los informes publicados y agrega la serie
    en `serie` — lo usa descargar_series; el colector diario sólo baja el último
    para no traer 20 MB de PDFs en cada corrida.
    """
    results = {}
    try:
        informes = _listar_informes()
        if not informes:
            raise ValueError("la página no lista ningún informe PDF")
        ultimo = _leer_informe(informes[-1])
        if not ultimo:
            raise ValueError(f"no se pudo parsear el informe más reciente ({informes[-1]})")
        if historico:
            serie = {}
            for f in informes:
                try:
                    d = _leer_informe(f)
                except Exception as e:
                    logger.warning("nowcast: informe %s ilegible (%s)", f, e)
                    continue
                if d:
                    # si dos informes estiman el mismo semestre, gana el más
                    # nuevo: es la revisión del autor sobre el mismo período
                    serie[d["periodo"]] = d["valor"]
            ultimo["serie"] = serie
            ultimo["informes_leidos"] = len(serie)
            ultimo["informes_publicados"] = len(informes)
        results["pobreza_nowcast"] = {
            **ultimo,
            "fecha": f"{ultimo['periodo']}-01",
            "unidad": "% de personas en hogares pobres",
        }
        logger.info("Nowcast pobreza OK: %s = %s%%", ultimo["periodo"], ultimo["valor"])
    except Exception as e:
        logger.error("Nowcast pobreza FAIL: %s", e)
    return results
