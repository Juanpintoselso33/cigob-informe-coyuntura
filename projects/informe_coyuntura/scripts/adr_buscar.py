"""Búsqueda por contenido sobre los ADR. Uso INTERNO, sin dependencias nuevas.

## Qué problema resuelve

`adr_coherencia.py` y `tests/test_adr_format.py` validan la ESTRUCTURA del
corpus: frontmatter, vocabulario de `estado`, bidireccionalidad de las
relaciones, índice sincronizado, que todo ADR citado exista. Lo que ninguno
responde es la pregunta que uno se hace antes de escribir el ADR 199:

    ¿esto ya lo decidimos?

Con 198 ADR y >1.300 citas desde código, buscar a mano por nombre de archivo no
alcanza — los títulos son frases, no palabras clave, y la decisión que uno busca
suele estar redactada con otras palabras que las que uno tiene en la cabeza.

## Por qué BM25 en stdlib y no embeddings

Los embeddings de BigQuery/Vertex facturan por token: no entran en el free tier
de 1 TiB de consultas, que sí cubre todo lo demás que hace el proyecto. Para 198
documentos cortos y consultas en castellano, BM25 sobre el cuerpo del ADR da
resultados suficientes a costo cero y sin agregar `sklearn` a requirements.txt
—que se instalaría en cada corrida del pipeline nocturno por una herramienta que
sólo se usa a mano.

No es búsqueda semántica: no va a encontrar "piso de cobertura" si buscás
"datos incompletos". Encuentra por vocabulario compartido, que para un corpus
escrito por las mismas personas con la misma jerga alcanza bastante.

Uso:
    python scripts/adr_buscar.py "renormalizacion de pesos ante faltantes"
    python scripts/adr_buscar.py --similares 0197      # antes de escribir uno nuevo
    python scripts/adr_buscar.py "bandas" --n 15
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ADR = RAIZ / "docs" / "adr"

# Parámetros estándar de BM25. k1 controla cuánto suma repetir un término
# (satura rápido); b, cuánto se penaliza un documento largo. Los ADR varían
# mucho de extensión, así que la normalización por longitud importa.
K1 = 1.5
B = 0.75

# Palabras que aparecen en casi todos los ADR y no discriminan: las vacías del
# castellano más la jerga estructural del propio formato MADR.
VACIAS = frozenset("""
a al algo alguna algunas alguno algunos ante antes aquel aquella aquello aqui
asi aun aunque cada como con contra cual cuales cuando de del desde donde dos
el ella ellas ello ellos en entre era eran es esa esas ese eso esos esta estan
estas este esto estos fue fueron ha habia hace hacia han hasta hay la las le
les lo los mas me mi mientras mismo mucho muy no nos o otra otras otro otros
para pero poco por porque pues que quien se sea segun ser si sin sobre solo son
su sus tambien tan tanto te tiene tienen todo todos tras un una uno unos y ya
adr contexto decision consecuencias opciones consideradas factores informacion
pros contras confirmacion planteo problema mas opcion bueno malo
""".split())


def _normalizar(texto: str) -> list[str]:
    """Minúsculas, sin tildes, sólo palabras de 3+ letras y sin vacías.

    Se sacan las tildes porque nadie las escribe al buscar desde la terminal, y
    una consulta sin tildes no puede quedar sin resultados por eso.
    """
    txt = unicodedata.normalize("NFD", texto.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return [t for t in re.findall(r"[a-z0-9_]{3,}", txt) if t not in VACIAS]


def _cuerpo(path: Path) -> tuple[str, str]:
    """(título, cuerpo sin frontmatter). El frontmatter es metadata repetida en
    todos los ADR y sólo agregaría ruido al índice."""
    txt = path.read_text(encoding="utf-8")
    # Sólo el bloque de frontmatter INICIAL. Partir por "---" a secas se lleva
    # puesto el encabezado en los ADR cuyo cuerpo usa reglas horizontales, que
    # en MADR son la mayoría: el título quedaba fuera del índice y volvía como
    # nombre de archivo.
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", txt, re.S)
    cuerpo = txt[m.end():] if m else txt
    t = re.search(r"^#\s+(.+)$", cuerpo, re.M)
    return (t.group(1).strip() if t else path.stem), cuerpo


def cargar() -> list[dict]:
    docs = []
    for p in sorted(ADR.glob("[0-9]*.md")):
        titulo, cuerpo = _cuerpo(p)
        # El título pesa triple: es donde está enunciada la decisión, y en un
        # corpus de este tamaño un acierto de título casi siempre es el bueno.
        tokens = _normalizar(cuerpo) + _normalizar(titulo) * 3
        docs.append({"id": p.stem[:4], "archivo": p.name, "titulo": titulo,
                     "cuerpo": cuerpo, "tf": Counter(tokens), "largo": len(tokens)})
    return docs


def _idf(docs: list[dict]) -> dict:
    n = len(docs)
    df = Counter(t for d in docs for t in d["tf"])
    return {t: math.log((n - c + 0.5) / (c + 0.5) + 1) for t, c in df.items()}


def puntuar(docs: list[dict], consulta: list[str]) -> list[tuple[float, dict]]:
    idf = _idf(docs)
    largo_medio = sum(d["largo"] for d in docs) / max(len(docs), 1)
    salida = []
    for d in docs:
        s = 0.0
        for t in consulta:
            f = d["tf"].get(t, 0)
            if not f:
                continue
            norm = f + K1 * (1 - B + B * d["largo"] / largo_medio)
            s += idf.get(t, 0.0) * f * (K1 + 1) / norm
        if s > 0:
            salida.append((s, d))
    return sorted(salida, key=lambda x: -x[0])


def _fragmento(doc: dict, consulta: list[str], ancho: int = 150) -> str:
    """La línea del ADR con más términos de la consulta: el porqué del match."""
    mejor, puntos = "", 0
    for linea in doc["cuerpo"].splitlines():
        if len(linea.strip()) < 30 or linea.lstrip().startswith(("#", "|", "-", "*")):
            continue
        toks = set(_normalizar(linea))
        p = sum(1 for t in set(consulta) if t in toks)
        if p > puntos:
            mejor, puntos = linea.strip(), p
    return (mejor[:ancho] + "…") if len(mejor) > ancho else mejor


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("consulta", nargs="*", help="palabras a buscar")
    p.add_argument("--similares", metavar="ID",
                   help="ADR cuyo contenido se usa como consulta (ej. 0197)")
    p.add_argument("--n", type=int, default=8, help="cuántos resultados (default 8)")
    args = p.parse_args()

    docs = cargar()
    if args.similares:
        base = next((d for d in docs if d["id"] == args.similares.zfill(4)), None)
        if not base:
            print(f"ERROR: no existe el ADR {args.similares}", file=sys.stderr)
            return 2
        # Los términos más distintivos del ADR base, no todos: usar el documento
        # entero como consulta trae los ADR largos por largos, no por parecidos.
        idf = _idf(docs)
        consulta = [t for t, _ in sorted(base["tf"].items(),
                                         key=lambda kv: -kv[1] * idf.get(kv[0], 0))[:25]]
        docs = [d for d in docs if d["id"] != base["id"]]
        print(f"Parecidos a ADR-{base['id']} — {base['titulo']}\n")
    elif args.consulta:
        consulta = _normalizar(" ".join(args.consulta))
        if not consulta:
            print("ERROR: la consulta quedó vacía tras sacar palabras vacías.",
                  file=sys.stderr)
            return 2
        print(f"Buscando: {' '.join(consulta)}\n")
    else:
        p.print_help()
        return 2

    resultados = puntuar(docs, consulta)[:args.n]
    if not resultados:
        print("Sin coincidencias.")
        return 0
    for s, d in resultados:
        print(f"  [{s:5.1f}]  ADR-{d['id']}  {d['titulo']}")
        frag = _fragmento(d, consulta)
        if frag:
            print(f"           {frag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
