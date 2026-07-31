"""Cierra las relaciones entre ADR y regenera el índice del README.

Dos cosas que la migración por archivo no puede hacer, porque necesitan
mirar el corpus entero:

  - **Relaciones bidireccionales.** ADR-0061 declara que supersede a
    ADR-0050, pero 0050 no se entera: quien abre el ADR viejo no tiene
    forma de saber que ya no rige. Acá se escribe el reverso en el ADR
    apuntado y se le corrige el estado.
  - **Índice generado.** La tabla del README se mantenía a mano y ya había
    derivado: 163 filas para 164 archivos, 29 valores distintos de estado
    en texto libre y dos filas rotas por un pipe suelto.

Uso:
    python scripts/adr_coherencia.py --simular
    python scripts/adr_coherencia.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"
README = ADR_DIR / "README.md"

# Relación directa -> relación inversa que hay que escribir en el destino.
INVERSAS = {
    "supersede": "superado_por",
    "supersede_parcialmente": "superado_parcialmente_por",
    "corrige": "corregido_por",
    "modifica": "modificado_por",
    "extiende": "extendido_por",
    "complementa": "complementado_por",
    "revierte": "revertido_por",
    "continua": "continuado_por",
    "cierra": "cerrado_por",
    "relacionado": "relacionado",
}

CINTURONES_ORDEN = [
    ("macro", "Macro (ITCM)"),
    ("politica", "Política (ITCP)"),
    ("gestion", "Gestión (ITCG)"),
    ("vida", "Vida cotidiana (ITVC)"),
    ("espiritu", "Espíritu de época"),
    ("transversal", "Transversal"),
    ("", "Sin cinturón declarado"),
]

ETIQUETA_ESTADO = {
    "aceptado": "vigente",
    "superado": "superado",
    "rechazado": "rechazado",
    "parcial": "parcial",
    "propuesto": "propuesto",
}


def leer(p: Path) -> tuple[dict, str, str]:
    """Devuelve (frontmatter, bloque_yaml_crudo, resto_del_archivo)."""
    texto = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return {}, "", texto
    return yaml.safe_load(m.group(1)) or {}, m.group(1), texto[m.end():]


def escribir(p: Path, meta: dict, resto: str) -> None:
    """Reescribe el frontmatter conservando el orden de campos."""
    orden = [
        "madr", "id", "estado", "nota_estado", "fecha", "cinturon", "indice",
        "indicadores", "parametros", "archivos",
        *INVERSAS.keys(), *INVERSAS.values(),
        "ambito", "origen", "commit",
    ]
    vistos, lineas = set(), []
    for clave in orden:
        if clave in vistos or clave not in meta or meta[clave] in (None, "", []):
            continue
        vistos.add(clave)
        valor = meta[clave]
        if clave == "id":
            lineas.append(f"id: '{str(valor).zfill(4)}'")
            continue
        if isinstance(valor, list):
            # Los ids de ADR van siempre citados: sin comillas YAML los lee
            # como octal (0036 -> 30) y las relaciones apuntan a otro ADR.
            es_relacion = clave in INVERSAS or clave in INVERSAS.values()
            cuerpo = ", ".join(
                f"'{str(v).zfill(4)}'" if es_relacion
                else (f"'{v}'" if isinstance(v, str) and not re.fullmatch(r"[a-z0-9_]+", v) else str(v))
                for v in valor
            )
            lineas.append(f"{clave}: [{cuerpo}]")
        elif isinstance(valor, str):
            lineas.append(f"{clave}: '{valor.replace(chr(39), chr(39) * 2)}'")
        else:
            lineas.append(f"{clave}: {valor}")
    p.write_text("---\n" + "\n".join(lineas) + "\n---\n" + resto,
                 encoding="utf-8", newline="\n")


def _como_lista(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).zfill(4) for x in v]
    return [str(v).zfill(4)]


def main() -> int:
    simular = "--simular" in sys.argv
    archivos = sorted(p for p in ADR_DIR.glob("[0-9]*.md"))
    corpus = {}
    for p in archivos:
        meta, _, resto = leer(p)
        corpus[str(meta.get("id", p.name[:4])).zfill(4)] = {"path": p, "meta": meta, "resto": resto}

    # --- 1. reverso de cada relación declarada
    agregados = 0
    faltantes: list[str] = []
    for propio, dato in corpus.items():
        for directa, inversa in INVERSAS.items():
            for destino in _como_lista(dato["meta"].get(directa)):
                if destino not in corpus:
                    faltantes.append(f"ADR-{propio} apunta a ADR-{destino}, que no existe")
                    continue
                if destino == propio:
                    continue
                meta_dest = corpus[destino]["meta"]
                actual = _como_lista(meta_dest.get(inversa))
                if propio not in actual:
                    meta_dest[inversa] = sorted(set(actual) | {propio})
                    agregados += 1

    # --- 2. estado de los superados
    reestados = 0
    for propio, dato in corpus.items():
        if dato["meta"].get("superado_por") and dato["meta"].get("estado") == "aceptado":
            dato["meta"]["estado"] = "superado"
            quien = ", ".join(f"ADR-{x}" for x in _como_lista(dato["meta"]["superado_por"]))
            if not dato["meta"].get("nota_estado"):
                dato["meta"]["nota_estado"] = f"Superado por {quien}"
            reestados += 1

    if not simular:
        for dato in corpus.values():
            escribir(dato["path"], dato["meta"], dato["resto"])

    # --- 3. índice del README
    filas_por_cinturon: dict[str, list[str]] = {}
    for propio in sorted(corpus):
        meta = corpus[propio]["meta"]
        titulo = ""
        m = re.search(r"^#\s+ADR-\d+\s*[—-]\s*(.+?)\s*$", corpus[propio]["resto"], re.M)
        if m:
            titulo = m.group(1).strip()
        estado = ETIQUETA_ESTADO.get(meta.get("estado", ""), meta.get("estado", ""))
        if meta.get("superado_por"):
            estado += " por " + ", ".join(
                f"[{x}]({corpus[x]['path'].name})" for x in _como_lista(meta["superado_por"])
                if x in corpus
            )
        nombre = corpus[propio]["path"].name
        ind = ", ".join(f"`{i}`" for i in (meta.get("indicadores") or [])[:3])
        filas_por_cinturon.setdefault(meta.get("cinturon") or "", []).append(
            f"| [{propio}]({nombre}) | {titulo.replace('|', '\\|')} | {ind} | {estado} |"
        )

    partes = [
        "## Índice",
        "",
        "> Generado por `scripts/adr_coherencia.py` a partir del frontmatter de",
        "> cada ADR. No editar a mano: `tests/test_adr_format.py` comprueba que",
        "> esta tabla coincida con los archivos.",
        "",
    ]
    for clave, etiqueta in CINTURONES_ORDEN:
        filas = filas_por_cinturon.get(clave)
        if not filas:
            continue
        partes += [f"### {etiqueta}", "", "| # | Decisión | Indicadores | Estado |",
                   "|---|---|---|---|", *filas, ""]

    texto_readme = README.read_text(encoding="utf-8").replace("\r\n", "\n")
    cabecera = texto_readme.split("## Índice")[0].rstrip()
    if not simular:
        README.write_text(cabecera + "\n\n" + "\n".join(partes).rstrip() + "\n",
                          encoding="utf-8", newline="\n")

    print(f"{'Simulación' if simular else 'Aplicado'}:")
    print(f"  relaciones inversas escritas: {agregados}")
    print(f"  ADR marcados como superados:  {reestados}")
    print(f"  filas del índice:             {sum(len(v) for v in filas_por_cinturon.values())}")
    for f in faltantes:
        print(f"  AVISO  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
