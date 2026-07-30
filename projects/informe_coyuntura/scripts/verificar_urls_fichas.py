# -*- coding: utf-8 -*-
"""Verifica las URL de procedencia de las fichas metodológicas públicas.

POR QUÉ EXISTE. La `url` de cada ficha es lo que el lector usa para ir a la
fuente, y es el único campo de la ficha que puede romperse **sin que nadie toque
el repo**: los organismos migran sus sitios. Ningún gate lo veía —
`gate_calidad.py` valida datos y estructura del snapshot, y los tests no salen a
la red.

Lo encontró el editor señalando UN link mal apuntado (victimización). Al auditar
las 64, el resultado fue: **7 caídas con 404, 1 con 403, 1 inalcanzable y 2
apuntando a otra cosa distinta** — y las dos peores no daban error, daban 200
sobre la página de OTRO índice de la misma universidad, que es justo el caso que
un chequeo de status code no encuentra:

  · victimización apuntaba al **ICG** (Índice de Confianza en el Gobierno);
  · el ICC apuntaba a «II LAIT (2008)».

De ahí las dos comprobaciones separadas de abajo. El status code encuentra las
migraciones; el título encuentra los apuntados a otra cosa, y ese hay que leerlo
a ojo — por eso se imprime siempre, no sólo cuando falla.

USO
    python scripts/verificar_urls_fichas.py            # todas
    python scripts/verificar_urls_fichas.py --solo-fallas
    python scripts/verificar_urls_fichas.py --timeout 60

Sale con código 1 si alguna URL falla, para poder colgarlo de un cron. NO se
mete en `gate_calidad.py` a propósito: depende de la red y de sitios de terceros
que se caen solos, así que no debe bloquear un deploy de datos.
"""
import argparse
import concurrent.futures as cf
import html
import re
import sys
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RAIZ = Path(__file__).resolve().parents[1]
FICHAS = RAIZ / "web" / "src" / "lib" / "fichas.ts"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Sitios que responden bien en un navegador y rechazan un cliente sin sesión.
# No son fallas de la ficha: se marcan aparte para no gritar en cada corrida.
TOLERADOS = {403, 429}


def urls_de_fichas() -> list:
    """[(indicador, url)] leídos del .ts. Se parsea el texto y no se importa el
    módulo porque es TypeScript; el formato del archivo es estable (una `url:`
    por bloque `fuente`)."""
    lineas = FICHAS.read_text(encoding="utf-8").split("\n")
    pares, actual = [], None
    for linea in lineas:
        cabecera = re.match(r"^  (\w+): \{$", linea)
        if cabecera:
            actual = cabecera.group(1)
            continue
        m = re.match(r'^\s*url: "([^"]+)",?\s*$', linea)
        if m and actual:
            pares.append((actual, m.group(1)))
    return pares


def titulo_de(texto: str) -> str:
    m = re.search(r"<title>(.*?)</title>", texto, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()


def verificar(par: tuple, timeout: int) -> dict:
    indicador, url = par
    try:
        r = requests.get(url, headers=UA, timeout=timeout, verify=False,
                         allow_redirects=True)
        tipo = r.headers.get("content-type", "")
        return {
            "indicador": indicador, "url": url, "codigo": r.status_code,
            "titulo": titulo_de(r.text) if "text/html" in tipo else f"[{tipo.split(';')[0]}]",
            "redirigio": r.url.rstrip("/") != url.rstrip("/"),
            "destino": r.url,
        }
    except Exception as e:
        return {"indicador": indicador, "url": url, "codigo": None,
                "titulo": f"{type(e).__name__}: {e}"[:90],
                "redirigio": False, "destino": url}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--solo-fallas", action="store_true",
                    help="omite las que responden 200")
    args = ap.parse_args()

    pares = urls_de_fichas()
    print(f"{len(pares)} fichas con URL de procedencia\n")
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        filas = list(ex.map(lambda p: verificar(p, args.timeout), pares))

    rotas, tolerados = [], []
    for f in sorted(filas, key=lambda x: x["indicador"]):
        ok = f["codigo"] == 200
        if f["codigo"] in TOLERADOS:
            tolerados.append(f)
        elif not ok:
            rotas.append(f)
        if ok and args.solo_fallas:
            continue
        marca = "OK  " if ok else ("TOL " if f["codigo"] in TOLERADOS else "ROTA")
        print("%-4s %-28s %-4s %s %s" % (
            marca, f["indicador"], f["codigo"] or "ERR",
            "R" if f["redirigio"] else " ", f["titulo"][:78]))

    print()
    if tolerados:
        print("Toleradas (el sitio bloquea clientes sin navegador, no es la ficha):")
        for f in tolerados:
            print(f"  {f['indicador']}: {f['codigo']} {f['url']}")
    if rotas:
        print(f"\n{len(rotas)} URL ROTAS — hay que buscar la página nueva del organismo:")
        for f in rotas:
            print(f"  {f['indicador']}: {f['codigo'] or 'sin respuesta'} {f['url']}")
        print("\nNo adivines la URL nueva: leé el menú del sitio que SÍ responde y\n"
              "sacá el link de ahí. Los organismos migran a slugs y las rutas\n"
              "inventadas dan 404 igual que la vieja (BCRA, jul-2026).")
    else:
        print("Ninguna URL rota.")

    print("\nRevisá los TÍTULOS a ojo: una URL puede dar 200 y apuntar a otra cosa.\n"
          "Los dos peores casos encontrados daban 200 sobre la página de otro\n"
          "índice de la misma universidad.")
    return 1 if rotas else 0


if __name__ == "__main__":
    sys.exit(main())
