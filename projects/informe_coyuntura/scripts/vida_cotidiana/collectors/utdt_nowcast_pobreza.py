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

# Cada informe nombra su semestre DOS veces y a veces las dos no coinciden
# (ADR-0153): el título de RESULTADOS y el enunciado que trae la tasa. Las dos
# las escribe el autor a mano y cualquiera de las dos puede quedar del mes
# anterior — se verificó en los dos sentidos sobre los 18 informes publicados:
#
#   · 16-jun-2026: título «Noviembre 2025 - Abril 2026», enunciado «diciembre
#     2025 - mayo 2026». Vale el enunciado (el gráfico del propio informe rotula
#     ese 29,6 como Dic25May26).
#   · 13-nov-2025: título «Mayo 2025 - Octubre 2025», enunciado «abril 2025 -
#     septiembre 2025». Vale el título — el informe del mes anterior ya había
#     estimado abril-septiembre.
#
# Por eso NO se prefiere una fuente sobre la otra: se toma el semestre MÁS
# NUEVO de los dos. Lo que queda viejo es siempre el mes anterior, nunca el
# siguiente, así que la desactualización sólo puede apuntar hacia atrás. Con esa
# regla los 18 informes dan 18 meses consecutivos, sin huecos ni duplicados;
# fechando por el título solo se perdía mayo-2026 y se pisaba abril, y por el
# enunciado solo se perdía octubre-2025.
_RE_RESULTADO_MESES = re.compile(
    r"tasa de pobreza de\s+([\d.,]+)\s*por\s+ciento\s+para el semestre\s+"
    r"([^\s\d]+)\s+(\d{4})\s*-\s*([^\s\d]+)\s+(\d{4})", re.IGNORECASE)
# Variante del informe que cierra un semestre calendario: «31,6 por ciento para
# el primer semestre calendario de 2026» — y «del 2025», que también aparece.
_RE_RESULTADO_CALENDARIO = re.compile(
    r"tasa de pobreza de\s+([\d.,]+)\s*por\s+ciento\s+para el\s+(primer|segundo)\s+"
    r"semestre\s+calendario\s+de[l]?\s+(\d{4})", re.IGNORECASE)

_MESES_NORM = {m.lower(): i for m, i in _MESES.items()}


def _listar_informes() -> list:
    """fnames de los PDF publicados, del más viejo al más nuevo."""
    r = requests.get(NOWCAST_PAGINA, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    return sorted(set(re.findall(r"/download\.php\?fname=(_\d+\.pdf)", r.text)))


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _semestre(mes_ini: str, ini: str, mes_fin: str, fin: str) -> tuple[str, str] | None:
    """(periodo, semestre) de un par de meses nombrados.

    Se fecha por el FIN del semestre estimado: es el mes más reciente que el dato
    describe, y así ordena junto al resto de las series.
    """
    n_fin = _MESES_NORM.get(mes_fin.lower())
    if not n_fin:
        return None
    return (f"{fin}-{n_fin:02d}",
            f"{mes_ini.capitalize()} {ini} - {mes_fin.capitalize()} {fin}")


def _resultado(texto: str) -> tuple[float, str, str] | None:
    """(tasa, periodo, semestre) del informe, o None si no se puede leer.

    El período es el más nuevo entre el que declara el título y el que declara el
    enunciado de la tasa; ver el comentario de los regex para por qué no se
    prefiere uno de los dos.
    """
    tasa = _RE_TASA.search(texto)
    if not tasa:
        return None

    candidatos = []
    m = _RE_RESULTADO_MESES.search(texto)
    if m:
        # la tasa del enunciado es la del semestre estimado; más abajo los
        # informes traen otra, la del mismo semestre del año anterior
        sem = _semestre(m.group(2), m.group(3), m.group(4), m.group(5))
        if sem:
            candidatos.append(sem)
            tasa = m
    c = _RE_RESULTADO_CALENDARIO.search(texto)
    if c:
        mes_fin = 6 if c.group(2).lower() == "primer" else 12
        anio = c.group(3)
        candidatos.append((f"{anio}-{mes_fin:02d}",
                           f"{'Enero' if mes_fin == 6 else 'Julio'} {anio} - "
                           f"{'Junio' if mes_fin == 6 else 'Diciembre'} {anio}"))
        tasa = c
    t = _RE_SEMESTRE.search(texto)
    if t:
        sem = _semestre(t.group(1), t.group(2), t.group(3), t.group(4))
        if sem:
            candidatos.append(sem)
    if not candidatos:
        return None
    periodo, semestre = max(candidatos)
    if len({p for p, _ in candidatos}) > 1:
        logger.warning("nowcast: el informe declara más de un semestre %s — se toma "
                       "el más nuevo (%s)", sorted({p for p, _ in candidatos}), periodo)
    return (_num(tasa.group(1)), periodo, semestre)


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
    res = _resultado(texto)
    if res is None:
        return None
    ic = _RE_IC.search(texto)
    return {
        "periodo": res[1],
        "semestre": res[2],
        "valor": res[0],
        "ic_inf": _num(ic.group(1)) if ic else None,
        "ic_sup": _num(ic.group(2)) if ic else None,
    }


def _huecos(serie: dict) -> list:
    """Meses ausentes entre el primero y el último período de la serie."""
    if len(serie) < 2:
        return []
    n_de = lambda p: int(p[:4]) * 12 + int(p[5:7])
    p_de = lambda n: f"{(n - 1) // 12}-{(n - 1) % 12 + 1:02d}"
    presentes = {n_de(p) for p in serie}
    return [p_de(n) for n in range(min(presentes) + 1, max(presentes))
            if n not in presentes]


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
            ultimo["huecos"] = _huecos(serie)
            if ultimo["huecos"]:
                # El autor publica un informe por mes y cada uno corre el
                # semestre móvil un mes: un hueco NO es un mes sin publicar, es
                # un informe mal fechado (ADR-0153). Vale como control porque el
                # síntoma es el mismo que el del bug que se corrigió.
                logger.warning("nowcast: la serie tiene huecos en %s — probable "
                               "informe mal fechado, no un mes sin publicar",
                               ultimo["huecos"])
        results["pobreza_nowcast"] = {
            **ultimo,
            "fecha": f"{ultimo['periodo']}-01",
            "unidad": "% de personas en hogares pobres",
        }
        logger.info("Nowcast pobreza OK: %s = %s%%", ultimo["periodo"], ultimo["valor"])
    except Exception as e:
        logger.error("Nowcast pobreza FAIL: %s", e)
    return results
