"""Buscador de proyectos de la Cámara de Diputados (ADR-0432).

Reemplaza a `datos.hcdn.gob.ar` (el portal CKAN de datos abiertos, caído para
todos desde el 4-nov-2026) en las dos cards que lo usan:

- `eficacia_legislativa`: los proyectos de ley que mandó el Ejecutivo y su
  sanción.
- `votos_sobre_bancas`: de qué proyecto es cada Orden del Día votada en
  Diputados y si ese proyecto es del Ejecutivo.

Es la API JSON que usa la página `www.hcdn.gob.ar/proyectos/buscador/`.
Devuelve 20 proyectos por página y corta con 429 si se le pide rápido, así que
cada pedido va espaciado.

**Lo que el buscador no trae y el CKAN sí.** El CKAN separaba «MENSAJE» de
«MENSAJE Y PROYECTO DE LEY». El buscador llama «MENSAJE» a todo lo que manda el
Ejecutivo, así que la separación se hace por el título: los avisos empiezan con
«Comunica…», «Remite…» o «Solicita…» (DNU y decretos delegados, informes,
pedidos de acuerdo) y los proyectos de ley no. Con esa regla salen los mismos 14
proyectos que la auditoría de cohorte del 8-sep-2026 y la serie de eficacia
coincide punto por punto desde enero de 2026 (ADR-0432).
"""
from __future__ import annotations

import re
import time

import requests

BUSCADOR = "https://www.hcdn.gob.ar/proyectos/buscador/api/v1/proyectos"
_HEADERS = {"Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
_PAUSA = 0.4          # segundos entre pedidos: el buscador corta con 429
_TIMEOUT = 30
_MAX_PAGINAS = 200    # tope de seguridad: 4.000 proyectos por consulta

# Los avisos del Ejecutivo empiezan así; los proyectos de ley, no. «SE REMITE
# LA CUENTA DE INVERSION» es el mismo aviso que «REMITE LA CUENTA…».
_RE_AVISO = re.compile(r"^\s*(SE\s+)?(COMUNIC|REMIT|SOLICIT)", re.I)
# La sanción definitiva: «CONSIDERACION Y SANCION», con o sin aclaración.
_RE_SANCION = re.compile(r"\bSANCION\b", re.I)
_RE_MEDIA = re.compile(r"MEDIA\s+SANCION", re.I)


def _get(url: str, params: dict | None = None) -> dict:
    """GET con pausa y hasta cuatro intentos. Un 429 espera lo que diga
    Retry-After (o 15 s); un 5xx o un corte de red, cada vez más. Un 4xx que no
    sea 429 sube enseguida: es un pedido mal armado, no la red."""
    ultimo: Exception = requests.ConnectionError("buscador de Diputados sin respuesta")
    espera = _PAUSA
    for _ in range(4):
        time.sleep(espera)
        espera = max(espera * 5, 2.0)
        try:
            r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        except requests.RequestException as e:
            ultimo = e
            continue
        if r.status_code == 429:
            ultimo = requests.HTTPError("429 del buscador de Diputados")
            try:
                espera = min(float(r.headers.get("Retry-After") or 15), 60)
            except ValueError:
                espera = 15
            continue
        if r.status_code >= 500:
            ultimo = requests.HTTPError(f"{r.status_code} del buscador de Diputados")
            continue
        r.raise_for_status()
        return r.json()
    raise ultimo


def buscar(**filtros) -> list[dict]:
    """Todos los proyectos que devuelve el buscador con estos filtros."""
    out, pagina = [], 1
    while pagina <= _MAX_PAGINAS:
        d = _get(BUSCADOR, {"pagina": pagina, **filtros})
        if "items" not in d:
            raise ValueError(f"buscador de Diputados: {d.get('message') or d}")
        out += d["items"]
        # El corte sale del `total` que declara la respuesta, no de un tamaño
        # de página supuesto: una página corta no puede truncar en silencio.
        total = d.get("total")
        if not d["items"] or (isinstance(total, int) and not d.get("total_es_minimo")
                              and len(out) >= total):
            return out
        if not isinstance(total, int) and len(d["items"]) < (d.get("por_pagina") or 20):
            return out
        pagina += 1
    raise ValueError(f"buscador de Diputados: más de {_MAX_PAGINAS} páginas para {filtros}")


def detalle(clave: str) -> dict:
    return _get(f"{BUSCADOR}/{clave}")


def proyecto_id(clave: str) -> str | None:
    """La clave `pap-290726` del buscador es el PROYECTO_ID `HCDN290726` del
    CKAN. Las claves `folio-…` son expedientes viejos sin equivalente."""
    m = re.fullmatch(r"pap-(\d+)", clave or "")
    return f"HCDN{m.group(1)}" if m else None


def es_proyecto_de_ley(item: dict) -> bool:
    return not _RE_AVISO.match(item.get("titulo") or "")


def publicacion_id(item: dict) -> str:
    """El identificador de publicación del CKAN (`HCDN143TP109`): con él se
    aplican las rectificaciones de fecha del Trámite Parlamentario."""
    return f"HCDN{item.get('periodo')}{item.get('publicacion_tipo')}{item.get('publicacion_numero')}"


def fecha_sancion(det: dict) -> str | None:
    """Fecha de la sanción definitiva: el último movimiento «… Y SANCION» con
    fecha. None si el proyecto no tiene ninguno."""
    fechas = [m["fecha"] for m in det.get("movimientos") or []
              if m.get("fecha") and _RE_SANCION.search(m.get("texto") or "")
              and not _RE_MEDIA.search(m.get("texto") or "")]
    return max(fechas) if fechas else None


def proyectos_pe(desde: str) -> list[dict]:
    """Proyectos de ley del Ejecutivo (siglas PE y JGM) que entraron por
    Diputados desde `desde`, como filas con las columnas del CKAN que usan las
    cards: PROYECTO_ID, PUBLICACION_ID, PUBLICACION_FECHA, TITULO, LEY y
    SANCION_DEFINITIVA. La sanción sale del detalle de cada proyecto que el
    buscador marca con número de ley."""
    filas = []
    for sigla in ("PE", "JGM"):
        for it in buscar(sigla=sigla, fecha_desde=desde):
            pid = proyecto_id(it.get("clave"))
            if (not pid or it.get("camara_origen") != "Diputados"
                    or not it.get("publicacion_fecha") or not es_proyecto_de_ley(it)):
                continue
            sancion = fecha_sancion(detalle(it["clave"])) if it.get("ley_nro") else None
            filas.append({"PROYECTO_ID": pid, "PUBLICACION_ID": publicacion_id(it),
                          "PUBLICACION_FECHA": it["publicacion_fecha"],
                          "TITULO": it.get("titulo"), "LEY": it.get("ley_nro"),
                          "SANCION_DEFINITIVA": sancion})
    if not filas:
        raise ValueError("buscador de Diputados: sin proyectos de ley del Ejecutivo")
    return filas


def indice_origen_por_od(ods: set[int], desde_anio: int) -> dict:
    """Índice de origen de `votos_sobre_bancas` sólo para las Órdenes del Día
    de Diputados que hacen falta: {"ids", "dictamenes", "claves": None}.

    `dictamenes` es {número de OD: [(fecha, PROYECTO_ID)]}, sólo con dictámenes
    de Diputados; `ids` son los proyectos de esas OD que mandó el Ejecutivo
    (autor «PODER EJECUTIVO», también los que entraron por el Senado) y que son
    proyectos de ley. `claves` (la numeración del Senado) el buscador no la
    trae: queda None y las votaciones del Senado que la necesitan esperan."""
    ids, dictamenes, vistos = set(), {}, set()
    hasta_anio = time.localtime().tm_year
    for od in sorted(ods):
        # Con el año acotado cada OD trae unos pocos proyectos en vez de todos
        # los de ese número desde 1983 (de las dos cámaras).
        items = [it for anio in range(desde_anio, hasta_anio + 1)
                 for it in buscar(od_nro=od, od_anio=anio)]
        for it in items:
            pid = proyecto_id(it.get("clave"))
            if not pid or pid in vistos:
                continue
            vistos.add(pid)
            # Un proyecto se mira UNA vez, pero con todas las OD pedidas en las
            # que tiene dictamen: si sólo se anotara la primera, otra OD quedaría
            # sin él y su votación se daría por no ejecutiva para siempre.
            for d in detalle(it["clave"]).get("dictamenes") or []:
                n = d.get("od_nro")
                if (d.get("camara") == "Diputados" and n in ods and d.get("fecha")
                        and (d.get("od_anio") or 0) >= desde_anio
                        and (d["fecha"], pid) not in dictamenes.get(n, [])):
                    dictamenes.setdefault(n, []).append((d["fecha"], pid))
            if it.get("autor_bloque") == "PODER EJECUTIVO" and es_proyecto_de_ley(it):
                ids.add(pid)
    return {"ids": ids, "dictamenes": dictamenes, "claves": None}
