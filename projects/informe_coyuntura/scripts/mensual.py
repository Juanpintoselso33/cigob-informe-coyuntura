"""Informe mensual del Monitor (punto 8 de la reunión del 6-oct-2026, ADR-0347).

`informe.cigob.org` muestra la FOTO DEL MES: el código de hoy con los dos
archivos de datos del sitio (`web/src/data/informe.json` y `series.json`)
congelados en la última corrida nocturna del mes. El seguimiento de cada noche
sigue en `main` y se publica en la URL interna del diario.

Cada mes publicado queda marcado con una etiqueta `mensual-AAAA-MM` sobre el
commit del bot que tiene su foto, así las fotos viejas se pueden reconstruir.

Uso (lo corre .github/workflows/mensual.yml; también a mano):

    python scripts/mensual.py elegir 2026-09     # imprime el commit de la foto de ese mes
    python scripts/mensual.py vigente            # imprime la etiqueta del mes publicado
    python scripts/mensual.py congelar <commit>  # copia los dos JSON de ese commit al árbol
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
DATOS = "projects/informe_coyuntura/web/src/data"
ARCHIVOS = ("informe.json", "series.json")
BOT = r"github-actions\[bot\]"  # --author es una regex: los corchetes van escapados


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, check=True, capture_output=True, text=True).stdout


def elegir(mes: str, rama: str = "origin/main") -> str:
    """La foto del mes es la ÚLTIMA corrida nocturna cuyo snapshot dice ser de
    ese mes (`period`). Se decide por el campo del snapshot y no por la fecha
    del commit: la corrida de las 00:30 del día 1 ya es del mes siguiente."""
    commits = _git("log", rama, f"--author={BOT}", "--format=%H", "--", f"{DATOS}/informe.json").split()
    for sha in commits:  # del más nuevo al más viejo
        try:
            periodo = json.loads(_git("show", f"{sha}:{DATOS}/informe.json")).get("period")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        if periodo == mes:
            return sha
        if periodo and periodo < mes:
            break
    raise SystemExit(f"no hay ninguna corrida nocturna con period={mes} en {rama}")


def vigente() -> str:
    """La etiqueta mensual-AAAA-MM más nueva: el mes que está publicado."""
    etiquetas = sorted(_git("tag", "--list", "mensual-*").split())
    if not etiquetas:
        raise SystemExit("todavía no se publicó ningún mensual (no hay etiquetas mensual-*)")
    return etiquetas[-1]


def congelar(ref: str) -> None:
    for nombre in ARCHIVOS:
        contenido = subprocess.run(["git", "show", f"{ref}:{DATOS}/{nombre}"], cwd=RAIZ,
                                   check=True, capture_output=True).stdout
        (RAIZ / DATOS / nombre).write_bytes(contenido)
    periodo = json.loads((RAIZ / DATOS / "informe.json").read_text(encoding="utf-8")).get("period")
    print(f"datos congelados de {ref[:10]} (period={periodo})")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("elegir", "vigente", "congelar"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "elegir":
        print(elegir(sys.argv[2]))
    elif sys.argv[1] == "vigente":
        print(vigente())
    else:
        congelar(sys.argv[2])
