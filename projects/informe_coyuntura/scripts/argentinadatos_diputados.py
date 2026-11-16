"""Actas de votación de Diputados desde ArgentinaDatos (ADR-0434).

Desde el 16-nov-2026 el sitio de votaciones de la Cámara
(`votaciones.hcdn.gob.ar`) devuelve 403 a todo, PDF y páginas. ArgentinaDatos
(`api.argentinadatos.com/v1/diputados`, proyecto abierto que replica las actas
de la Cámara) publica las mismas actas en JSON: id, fecha, título, resultado,
tipo de mayoría, totales y el voto de cada diputado por nombre. El bloque y la
provincia de cada voto salen de su padrón, que guarda el bloque de cada
diputado con sus fechas.

`ActaAD` es un `bytes` vacío que lleva el acta: los colectores que caminan ids
preguntan `isinstance(contenido, bytes)` para saber si un acta existe, y los
lectores de PDF de politica.py reconocen el tipo y leen el JSON en vez del PDF.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone

import requests

API = "https://api.argentinadatos.com/v1/diputados"
_TIMEOUT = 90
_ART = timezone(timedelta(hours=-3))
_ACTAS: dict[int, dict] = {}       # año -> {id: acta}
_PADRON: list | None = None


class ActaAD(bytes):
    """Marcador de un acta leída de ArgentinaDatos (ver docstring del módulo)."""
    acta: dict

    def __new__(cls, acta: dict):
        obj = super().__new__(cls, b"")
        obj.acta = acta
        return obj


def _get(url: str):
    r = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "CIGOB-Monitor/1.0"})
    r.raise_for_status()
    return r.json()


def actas_del_anio(anio: int) -> dict:
    if anio not in _ACTAS:
        _ACTAS[anio] = {int(a["id"]): a for a in _get(f"{API}/actas/{anio}")}
    return _ACTAS[anio]


def _anio_actual() -> int:
    return datetime.now(_ART).year


def maximo_id() -> int | None:
    actas = actas_del_anio(_anio_actual()) or actas_del_anio(_anio_actual() - 1)
    return max(actas) if actas else None


def buscar_acta(id_acta: int, desde_anio: int = 2023) -> dict | None:
    """El acta con ese id, o None si no existe en ArgentinaDatos. Los ids
    crecen con el tiempo: se mira del año actual hacia atrás y se corta en el
    primer año cuyo id más chico ya es menor que el buscado."""
    for anio in range(_anio_actual(), desde_anio - 1, -1):
        actas = actas_del_anio(anio)
        if id_acta in actas:
            return actas[id_acta]
        if actas and min(actas) < id_acta:
            return None
    return None


def fecha_local(acta: dict) -> datetime:
    """La fecha de ArgentinaDatos viene en UTC; el acta de la Cámara fecha en
    hora argentina (una votación a las 3 de la mañana es del día anterior en
    UTC-0 pero del mismo día de sesión en el PDF)."""
    utc = datetime.fromisoformat(acta["fecha"].replace("Z", "+00:00"))
    return utc.astimezone(_ART).replace(tzinfo=None)


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    t = re.sub(r'"[^"]*"', " ", t)          # apodos: Ali, Ernesto "Pipi"
    return " ".join(t.upper().replace(",", " ").replace(".", " ").split())


def _padron() -> list:
    global _PADRON
    if _PADRON is None:
        _PADRON = list(_get(f"{API}/diputados"))
    return _PADRON


def bloque_y_provincia(nombre: str, fecha: datetime) -> tuple[str, str]:
    """Bloque y provincia del diputado `nombre` («Apellido, Nombre») el día de
    la votación. ("", "") si el padrón no lo encuentra."""
    clave = _norm(nombre)
    dia = fecha.date().isoformat()
    candidatos = [p for p in _padron() if _norm(f"{p.get('apellido')} {p.get('nombre')}") == clave]
    if not candidatos:
        # «Matzkin, Martin» contra «Matzkin, Martín Alberto»: mismo apellido y
        # el primer nombre del acta abre el nombre del padrón (o al revés).
        apellido, _, nombres = nombre.partition(",")
        ap, nom = _norm(apellido), _norm(nombres).split()
        candidatos = [p for p in _padron() if _norm(p.get("apellido")) == ap and nom
                      and _norm(p.get("nombre")).split()[:1] == nom[:1]]
    for p in candidatos:
        pb = p.get("periodoBloque") or p.get("periodoMandato") or {}
        if (pb.get("inicio") or "")[:10] <= dia <= ((pb.get("fin") or "9999")[:10]):
            return p.get("bloque") or "", p.get("provincia") or ""
    if candidatos:
        return candidatos[-1].get("bloque") or "", candidatos[-1].get("provincia") or ""
    return "", ""


def filas(acta: dict) -> list[dict]:
    """[{nombre, bloque, provincia, voto}] como las del PDF de la Cámara."""
    fecha = fecha_local(acta)
    out = []
    for v in acta.get("votos") or []:
        if (v.get("tipoVoto") or "").lower() == "presidente":
            continue   # el PDF de la Cámara no lista al que preside
        bloque, provincia = bloque_y_provincia(v.get("diputado", ""), fecha)
        out.append({"nombre": v.get("diputado", ""), "bloque": bloque, "provincia": provincia,
                    "voto": (v.get("tipoVoto") or "").upper()})
    return out
