"""Leyes sancionadas desde la base abierta de InfoLeg (ADR-0435).

`datos.jus.gob.ar` publica todos los meses la base completa de InfoLeg (un ZIP
de ~50 MB con un CSV de ~260 MB): cada norma con su tipo, número y fecha de
sanción. Es el respaldo de `produccion_legislativa` mientras el catálogo de
leyes sancionadas de Diputados (`datos.hcdn.gob.ar`) no responda.

Sólo trae las leyes ya publicadas en el Boletín Oficial: una ley sancionada y
todavía no promulgada aparece en la actualización siguiente. Las vetadas en su
totalidad no se publican, igual que las que el indicador ya excluye.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import date

import requests

API = "https://datos.jus.gob.ar/api/3/action/package_search"
_CONSULTA = "Base Infoleg de Normativa Nacional"
_TIMEOUT = 300
_LEYES: list | None = None


def _url_zip() -> str:
    """La URL del ZIP se resuelve por la API: cambia con cada publicación."""
    r = requests.get(API, params={"q": "infoleg", "rows": 5}, timeout=60)
    r.raise_for_status()
    for paquete in r.json()["result"]["results"]:
        for recurso in paquete.get("resources", []):
            if (recurso.get("format", "").upper() == "ZIP"
                    and recurso.get("name", "").strip() == "Base Infoleg Normativa Nacional"):
                return recurso["url"]
    raise ValueError("datos.jus.gob.ar: sin el ZIP de la base de InfoLeg")


def leyes_sancionadas() -> list[tuple[str, date]]:
    """[("ley:NNNNN", fecha de sanción)] de todas las leyes de la base."""
    global _LEYES
    if _LEYES is None:
        r = requests.get(_url_zip(), timeout=_TIMEOUT)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        nombre = next(n for n in z.namelist() if n.endswith(".csv"))
        out = []
        with z.open(nombre) as f:
            for fila in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace")):
                if (fila.get("tipo_norma") or "").strip().lower() != "ley":
                    continue
                numero = (fila.get("numero_norma") or "").strip()
                sancion = (fila.get("fecha_sancion") or "")[:10]
                if numero.isdigit() and sancion:
                    try:
                        out.append(("ley:" + numero, date.fromisoformat(sancion)))
                    except ValueError:
                        continue
        if not out:
            raise ValueError("base de InfoLeg sin leyes")
        _LEYES = out
    return _LEYES
