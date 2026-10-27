"""Backfill reproducible del padrón de empleadores de ARCA desde el Wayback (ADR-0389).

ARCA no conserva archivos viejos; el Internet Archive guardó algunas copias del
archivo CON nombres (`apellidoNombreDenominacion.zip`: el mismo registro que el
sin nombres más una denominación de 30 caracteres antes de la marca de
empleador). Este script baja cada copia en streaming, **cuenta y descarta**: no
guarda nombres ni CUIT. Imprime los conteos; con `--escribir` los anota en
`data/vida/arca_empleadores.json`:

    .venv/bin/python scripts/vida_cotidiana/padron_arca_backfill.py [--escribir]
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent / "collectors"))
import padron_arca as pa  # noqa: E402

CON = ("https://web.archive.org/web/{ts}id_/{esquema}://www.afip.gob.ar/genericos/"
       "cInscripcion/archivos/apellidoNombreDenominacion.zip")
SIN = ("https://web.archive.org/web/{ts}id_/{esquema}://www.afip.gob.ar/genericos/"
       "cInscripcion/archivos/SINapellidoNombreDenominacion.zip")
# (timestamp de la copia, fecha del archivo interno, URL, formato). Las copias de
# 2011-2012 (`DDMMAAAAsd.zip`) quedan afuera: no está verificado que la marca de
# empleador ocupe la misma posición en ese formato.
COPIAS = [
    ("20140821015650", "2014-08-16", CON, "http", pa.LAYOUT_CON_NOMBRES),
    ("20150324211736", "2015-03-14", SIN, "http", pa.LAYOUT_SIN_NOMBRES),
    ("20200617071722", "2020-06-13", CON, "https", pa.LAYOUT_CON_NOMBRES),
    ("20210410220523", "2021-04-10", CON, "https", pa.LAYOUT_CON_NOMBRES),
    ("20240830074549", "2024-08-24", CON, "https", pa.LAYOUT_CON_NOMBRES),
]


def contar_copia(ts: str, plantilla: str = CON, esquema: str = "https",
                 layout=pa.LAYOUT_CON_NOMBRES) -> dict:
    url = plantilla.format(ts=ts, esquema=esquema)
    fd, tmp = tempfile.mkstemp(suffix=".zip", prefix="padron_wb_")
    os.close(fd)
    try:
        with requests.get(url, headers=pa.HTTP_HEADERS, stream=True, timeout=(30, 300)) as r:
            r.raise_for_status()
            with open(tmp, "wb") as out:
                for b in r.iter_content(1 << 20):
                    out.write(b)
        conteos, fecha = pa.contar_zip(tmp, layout=layout)
    finally:
        os.remove(tmp)
    return {"fecha_archivo": fecha, **conteos, "url": url}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    args = ap.parse_args()
    meses = pa.leer_registro() if args.escribir else {}
    for ts, esperada, plantilla, esquema, layout in COPIAS:
        c = contar_copia(ts, plantilla, esquema, layout)
        if c["fecha_archivo"] != esperada:
            raise SystemExit(f"{ts}: fecha interna {c['fecha_archivo']} != {esperada}")
        print(json.dumps(c, ensure_ascii=False))
        meses = pa.anotar(meses, c)
    if args.escribir:
        pa.guardar_registro(meses)


if __name__ == "__main__":
    main()
