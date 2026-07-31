"""Genera el manual metodológico vigente de un cinturón.

El registro de ADR responde *por qué se decidió cada cosa y cuándo*. Es un
log histórico de 165 documentos y ~142.000 palabras: sirve para auditar,
no para leer de corrido. Lo que falta es la otra mitad —la **referencia**:
qué mide el cinturón HOY, con qué pesos, con qué anclas y qué decisiones
siguen abiertas— y son dos documentos distintos, no uno largo.

Este manual se **genera** del código que corre y del frontmatter de los
ADR, nunca a mano: un documento paralelo mantenido a mano se desactualiza
en silencio, que es exactamente lo que le pasó al índice del README (163
filas para 164 archivos) y a la sección de robustez del ITVC (ADR-0116).

**No publica valores.** Dice el método; el número lo deriva el pipeline,
por la regla de ADR-0156. Así el manual no caduca cuando el dato cambia.

Uso:
    python scripts/manual_cinturon.py politica
    python scripts/manual_cinturon.py --todos
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ADR_DIR = RAIZ / "docs" / "adr"
SALIDA = RAIZ / "docs" / "manuales"
sys.path.insert(0, str(RAIZ / "scripts"))

# cinturón -> (módulo, índice, nombre legible)
CINTURONES = {
    "politica": ("itcp", "ITCP", "Política"),
    "macro": ("itcm", "ITCM", "Macro"),
    "gestion": ("itcg", "ITCG", "Gestión"),
    "vida": ("itvc", "ITVC", "Vida cotidiana"),
}

# ADR que define la paramétrica del cinturón. Los indicadores que no tienen
# ADR propio se definieron ahí, y decirlo con número es más útil que decir
# «el ADR fundacional».
FUNDACIONAL = {"politica": "0036", "gestion": "0013", "vida": "0018"}

FAMILIA_LEGIBLE = {
    "tension": "tensión externa",
    "capacidad": "capacidad propia",
    "recursos": "recursos",
}

RE_PEND = re.compile(
    r"(\bqueda\s+pendiente|\bpendiente[s]?\s+(?:de\s+decisi|editorial)"
    r"|decisi[oó]n\s+editorial\s+(?:pendiente|abierta)|no se incorpora todav"
    # «SUSPENDIDA» a secas matcheaba «la encuesta, suspendida 2020-2023»:
    # tiene que ser la decisión la que queda suspendida, no la fuente.
    r"|queda\s+SUSPENDIDA|queda abierta como decisi|queda como candidata)",
    re.I,
)


def _frontmatter(p: Path) -> dict:
    import yaml
    t = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1)) if m else {}


def _titulo(p: Path) -> str:
    m = re.search(r"^#\s+ADR-\d+\s*[—-]\s*(.+?)\s*$",
                  p.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else p.stem


def cargar_adrs(cinturon: str) -> tuple[dict, list, list]:
    """(indicador -> [(id, titulo, archivo)], del cinturón, decisiones abiertas)"""
    por_ind: dict[str, list] = defaultdict(list)
    del_cinturon, abiertas = [], []
    for p in sorted(ADR_DIR.glob("[0-9]*.md")):
        meta = _frontmatter(p)
        if meta.get("cinturon") != cinturon:
            continue
        if meta.get("estado") in ("superado", "rechazado"):
            continue
        fila = (meta["id"], _titulo(p), p.name)
        del_cinturon.append(fila)
        for ind in (meta.get("indicadores") or []):
            por_ind[ind].append(fila)
        # El cuerpo, sin el frontmatter: `origen: 'pendiente editorial abierto
        # desde…'` describe de dónde SALIÓ el ADR, no algo que deje abierto.
        cuerpo = re.sub(r"\A---\n.*?\n---\n", "",
                        p.read_text(encoding="utf-8"), flags=re.S)
        lineas = cuerpo.splitlines()
        for n_ln, ln in enumerate(lineas):
            if ln.startswith("#") or not ln.strip():
                continue
            # «Se resolvió con evidencia» cierra el pendiente, no lo abre. El
            # texto viene envuelto a 78 columnas, así que esa frase puede caer
            # varios renglones más abajo: se mira el PÁRRAFO entero, no una
            # ventana de N líneas, que es un número mágico que siempre queda
            # corto (con 3 se escapaba ADR-0132, que la tiene en el cuarto).
            parrafo = []
            for siguiente in lineas[n_ln:]:
                if not siguiente.strip():
                    break
                parrafo.append(siguiente)
            if re.search(r"\b(resuel\w+|resolvi[oó]|cierra)\b",
                         " ".join(parrafo), re.I):
                continue
            if RE_PEND.search(ln):
                # ¿Algún ADR posterior ya lo tocó? Sale de las relaciones
                # inversas que escribió adr_coherencia.py.
                cerradores = []
                for clave in ("corregido_por", "cerrado_por", "superado_por",
                              "modificado_por", "continuado_por"):
                    cerradores += [str(x) for x in (meta.get(clave) or [])]
                abiertas.append((meta["id"], _titulo(p), p.name,
                                 re.sub(r"\s+", " ", ln.strip()),
                                 sorted(set(cerradores))))
                break
    return por_ind, del_cinturon, abiertas


def cargar_labels() -> dict:
    txt = (RAIZ / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
    bloque = re.search(r"LABELS[^=]*=\s*\{(.*?)\n\}", txt, re.S)
    fuente = bloque.group(1) if bloque else txt
    return {k: v for k, v in re.findall(r'(\w+):\s*"([^"]+)"', fuente)}


def cargar_procedencia(indice: str) -> dict:
    """{indicador: (categoría, motivo)} desde `procedencia_anclas.json`.

    La clave del índice va en mayúsculas y el detalle es una lista de
    registros, no un dict por categoría.
    """
    p = RAIZ / "output" / "procedencia_anclas.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    detalle = d.get("por_indice", {}).get(indice.upper(), {}).get("detalle", [])
    return {r["indicador"]: (r.get("categoria", ""), r.get("motivo", ""))
            for r in detalle}


def cargar_ocultos(cinturon: str) -> set[str]:
    """Indicadores que se relevan y se cachean pero no se publican.

    La lista vive en `publicar.py`, no en el módulo del índice: derivarla de
    «tiene banda pero no está en ninguna dimensión» deja afuera a los que
    nunca tuvieron banda (`badlar`, `indice_lider`) y a los que salieron del
    tablero por decisión editorial.
    """
    import ast
    nombre = {"macro": "MACRO_OCULTOS", "politica": "POLITICA_OCULTOS",
              "gestion": "GESTION_OCULTOS", "vida": "VIDA_OCULTOS"}[cinturon]
    src = (RAIZ / "scripts" / "publicar.py").read_text(encoding="utf-8")
    m = re.search(rf"^{nombre}\s*=\s*(.+)$", src, re.M)
    if not m:
        return set()
    expr = m.group(1).strip()
    # Forma A: literal — {"badlar", "prestamos_privados", ...}
    try:
        return set(ast.literal_eval(expr))
    except (ValueError, SyntaxError):
        pass
    # Forma B: set(itcg.INDICADORES_CONTEXTO)
    ref = re.match(r"set\((\w+)\.(\w+)\)", expr)
    if ref:
        mod = importlib.import_module(ref.group(1))
        return set(getattr(mod, ref.group(2), []))
    return set()


def bandas_legibles(mod, indicador: str) -> str:
    bandas = getattr(mod, f"BANDAS_{mod.__name__.upper()}", {}).get(indicador)
    if not bandas:
        return "—"
    partes = []
    for lo, hi, pts in bandas:
        if lo == float("-inf"):
            partes.append(f"≤ {hi:g} → {pts}")
        elif hi == float("inf"):
            partes.append(f"> {lo:g} → {pts}")
        else:
            partes.append(f"{lo:g}–{hi:g} → {pts}")
    return " · ".join(partes)


def generar(cinturon: str) -> Path:
    modulo, indice, legible = CINTURONES[cinturon]
    mod = importlib.import_module(modulo)
    dimensiones = getattr(mod, f"DIMENSIONES_{indice}")
    familias = getattr(mod, f"FAMILIAS_{indice}", {})
    rezagos = getattr(mod, f"REZAGO_MESES_{indice}", {})
    contexto = getattr(mod, "INDICADORES_CONTEXTO", [])
    bandas_todas = getattr(mod, f"BANDAS_{indice}", {})

    por_ind, del_cinturon, abiertas = cargar_adrs(cinturon)
    labels = cargar_labels()
    procedencia = cargar_procedencia(indice)

    L = []
    L += [f"# Manual metodológico — cinturón {legible} ({indice})", ""]
    L += [
        "> **Generado** por `scripts/manual_cinturon.py` desde el código que corre",
        f"> (`scripts/{modulo}.py`) y el frontmatter de los ADR. No editar a mano.",
        ">",
        "> Dice el **método**, no el valor: los números los deriva el pipeline",
        "> (ADR-0156), así que este documento no caduca cuando cambia el dato.",
        "",
        "Los ADR responden *por qué* se decidió cada cosa y *cuándo*. Este manual",
        "responde *qué rige hoy*. Para la historia de una decisión, seguí el link",
        "al ADR.",
        "",
    ]

    # --- dimensiones
    L += ["## Dimensiones y pesos", "", "| Dimensión | Peso | Indicadores |", "|---|---:|---|"]
    for dim, d in dimensiones.items():
        inds = d["indicadores"]
        L.append(f"| `{dim}` | {d['peso']:.0%} | " +
                 ", ".join(f"`{i}`" for i in inds) + " |")
    L += ["", f"Suma de pesos: {sum(d['peso'] for d in dimensiones.values()):.0%}.", ""]

    if not bandas_todas:
        L += [
            "## Cómo puntúa este cinturón", "",
            "A diferencia de los índices por bandas, acá **no hay tabla de cortes**:",
            "cada componente ya es un índice base 100 = 4T-2023 (ADR-0018), y el",
            "número que se promedia es el índice mismo. La conversión a puntaje es",
            "la **identidad**, no una escala ausente (ADR-0108).",
            "",
            "Por eso el cinturón no tiene anclas que calibrar contra el período: su",
            "ancla es una fecha fija, el arranque del mandato, así que no hay cortes",
            "donde colar una calibración (ADR-0123).",
            "",
        ]

    # --- indicadores
    L += ["## Qué mide cada indicador", ""]
    for dim, d in dimensiones.items():
        L += [f"### Dimensión `{dim}` ({d['peso']:.0%})", ""]
        for ind, peso_int in d["indicadores"].items():
            efectivo = d["peso"] * peso_int
            L += [f"#### {labels.get(ind, ind)}", "", f"`{ind}`", ""]
            fila = [
                ("Peso dentro de la dimensión", f"{peso_int:.0%}"),
                ("Peso efectivo en el índice", f"**{efectivo:.1%}**"),
            ]
            if ind in familias:
                fila.append(("Familia de lectura",
                             FAMILIA_LEGIBLE.get(familias[ind], familias[ind])))
            if ind in rezagos:
                fila.append(("Rezago declarado", f"{rezagos[ind]:g} meses"))
            if ind in procedencia:
                cat, motivo = procedencia[ind]
                fila.append(("Procedencia del ancla",
                             f"`{cat}`" + (f" — {motivo}" if motivo else "")))
            L += ["| | |", "|---|---|"]
            L += [f"| {k} | {v} |" for k, v in fila]
            b = bandas_legibles(mod, ind)
            L += ["", (f"**Bandas**: {b}" if b != "—" else
                       "**Escala**: sin bandas — ver «Cómo puntúa este "
                       "cinturón» arriba."), ""]
            adrs = por_ind.get(ind, [])
            if adrs:
                L.append("**Lo gobiernan**: " + " · ".join(
                    f"[ADR-{i}](../adr/{f}) {t}" for i, t, f in adrs))
            else:
                fund = FUNDACIONAL.get(cinturon)
                L.append(
                    "**Lo gobiernan**: sin ADR propio — se definió con la "
                    + (f"paramétrica del cinturón (ADR-{fund})." if fund
                       else "paramétrica del cinturón.")
                )
            L += [""]

    # --- contexto
    puntuables = {i for d in dimensiones.values() for i in d["indicadores"]}
    fuera = sorted((set(bandas_todas) | cargar_ocultos(cinturon)) - puntuables)
    if fuera:
        L += ["## Se releva y no puntúa", "",
              "Estos indicadores se siguen scrapeando y cacheando, pero están fuera",
              "del índice y fuera del tablero. Sus bandas quedan como referencia",
              "histórica.", ""]
        for i in fuera:
            marca = " (declarado como contexto)" if i in contexto else ""
            L.append(f"- `{i}` — {labels.get(i, '')}{marca}")
        L += [""]

    # --- decisiones abiertas
    L += ["## Decisiones abiertas", ""]
    if abiertas:
        L += [f"{len(abiertas)} ADR vigentes de este cinturón declaran algo pendiente "
              "de decisión editorial. No son trabajo técnico: son llamadas que sólo "
              "puede hacer el editor.", "",
              "> La detección lee la prosa, así que **sobre-reporta a propósito**: si "
              "un ADR anota un pendiente y lo resuelve unos párrafos más abajo, sigue "
              "apareciendo acá. Se prefiere ese error al contrario —perder una "
              "decisión realmente abierta—. La marca ⚠️ sí es firme: sale de las "
              "relaciones declaradas entre ADR, no de adivinar sobre el texto.", ""]
        for i, tit, f, ln, cerradores in abiertas:
            L += [f"- **[ADR-{i}](../adr/{f})** — {tit}", f"  <br>{ln[:200]}"]
            if cerradores:
                L.append("  <br>⚠️ Puede estar resuelto: lo tocó "
                         + ", ".join(f"ADR-{c}" for c in cerradores)
                         + ". Verificar antes de tratarlo como abierto.")
    else:
        L.append("Ninguna declarada.")
    L += [""]

    # --- índice de ADR del cinturón
    L += ["## Todos los ADR vigentes de este cinturón", "",
          f"{len(del_cinturon)} en total. El índice completo, con los superados y "
          "rechazados, está en [docs/adr/README.md](../adr/README.md).", ""]
    for i, tit, f in del_cinturon:
        L.append(f"- [{i}](../adr/{f}) — {tit}")
    L += [""]

    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / f"{cinturon}.md"
    destino.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return destino


def indice_manuales() -> Path:
    """README de docs/manuales/, para que la carpeta se explique sola."""
    L = ["# Manuales metodológicos vigentes", "",
         "> Generados por `scripts/manual_cinturon.py`. No editar a mano.", "",
         "Qué mide hoy cada cinturón, con qué pesos, con qué anclas y qué",
         "decisiones siguen abiertas. Para saber **por qué** se decidió algo y",
         "cuándo, el registro histórico está en [docs/adr/](../adr/README.md).",
         "", "| Cinturón | Índice | Manual |", "|---|---|---|"]
    for c, (_, indice, legible) in CINTURONES.items():
        if (SALIDA / f"{c}.md").exists():
            L.append(f"| {legible} | `{indice}` | [{c}.md]({c}.md) |")
    L += ["", "Regenerar: `python scripts/manual_cinturon.py --todos`", ""]
    d = SALIDA / "README.md"
    d.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return d


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    objetivos = list(CINTURONES) if "--todos" in sys.argv else args
    if not objetivos:
        print(__doc__)
        return 2
    for c in objetivos:
        if c not in CINTURONES:
            print(f"cinturón desconocido: {c} (hay: {', '.join(CINTURONES)})")
            return 2
        d = generar(c)
        print(f"{d.relative_to(RAIZ)}  ({len(d.read_text(encoding='utf-8').split())} palabras)")
    print(indice_manuales().relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
