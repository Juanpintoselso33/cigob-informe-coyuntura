# -*- coding: utf-8 -*-
"""Línea de base auditable de un snapshot, y el diff entre dos de ellas.

La remediación de la auditoría del 25-ago-2026 mueve valores, pesos y bandas de
varios indicadores a la vez. Sin un manifiesto congelado antes de tocar nada, un
movimiento de score no se puede atribuir: no hay forma de separar "corregí el
dato" de "se recalibró la banda" o de "se renormalizaron los pesos porque
suspendí un vecino de dimensión".

    python scripts/manifiesto_remediacion.py capturar -o base.json
    python scripts/manifiesto_remediacion.py comparar base.json [--contra otro.json]

`capturar` lee el snapshot publicado (`web/src/data/informe.json` por defecto) y
emite, por cada indicador: valor, unidad, fecha del dato, si integra el índice,
dimensión, puntaje de banda, peso efectivo y aporte. Guarda además el sha256 del
snapshot leído, para que el manifiesto no pueda atribuirse a otra corrida.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"

# el bloque paramétrico de cada cinturón se llama distinto en cada uno
PARAMETRICA = {
    "macro": "itcm",
    "politica": "itcp",
    "vida_cotidiana": "itvc",
    "gestion": "itcg",
}


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def capturar(ruta: Path = SNAPSHOT) -> dict:
    """Manifiesto plano del snapshot: un registro por indicador publicado."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))

    indicadores = {}
    cinturones = {}
    for cint, bloque in datos["cinturones"].items():
        par = bloque.get(PARAMETRICA[cint]) or {}
        cinturones[cint] = {
            "score": bloque.get("score"),
            "estado": bloque.get("estado"),
            "parametrica": PARAMETRICA[cint],
            "parametrica_valor": par.get("valor"),
            "parametrica_banda": par.get("banda"),
            "dimensiones": {
                dim: {"peso": d.get("peso"), "puntaje": d.get("puntaje")}
                for dim, d in (par.get("dimensiones") or {}).items()
            },
        }
        for nombre, ind in bloque["indicadores"].items():
            indicadores[nombre] = {
                "cinturon": cint,
                "valor": ind.get("valor"),
                "unidad": ind.get("unidad"),
                "fuente": ind.get("fuente"),
                "fecha_dato": ind.get("fecha_dato"),
                "en_indice": ind.get("en_indice"),
                "dimension": ind.get("dimension"),
                "puntaje_banda": ind.get("puntaje_banda"),
                "peso_efectivo": ind.get("peso_efectivo"),
                "aporte_score": ind.get("aporte_score"),
                "semaforo": (ind.get("semaforo") or {}).get("color"),
            }

    return {
        "origen": str(ruta.relative_to(RAIZ)),
        "sha256_snapshot": _sha256(ruta),
        "generated_at": datos.get("generated_at"),
        "period": datos.get("period"),
        "score_global": datos.get("score_global"),
        "cinturon_dominante": datos.get("cinturon_dominante"),
        "cinturones": cinturones,
        "n_indicadores": len(indicadores),
        "indicadores": dict(sorted(indicadores.items())),
    }


def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def comparar(antes: dict, despues: dict) -> list[str]:
    """Tabla antes/después. Recorre los 69, no sólo los intervenidos."""
    lineas = []
    lineas.append(f"snapshot antes  : {antes['generated_at']}  score_global={_fmt(antes['score_global'])}")
    lineas.append(f"snapshot después: {despues['generated_at']}  score_global={_fmt(despues['score_global'])}")
    lineas.append("")

    lineas.append("## Cinturones")
    lineas.append("| cinturón | score antes | score después | Δ | paramétrica antes | después |")
    lineas.append("|---|---:|---:|---:|---:|---:|")
    for cint in sorted(set(antes["cinturones"]) | set(despues["cinturones"])):
        a = antes["cinturones"].get(cint, {})
        d = despues["cinturones"].get(cint, {})
        delta = ""
        if isinstance(a.get("score"), (int, float)) and isinstance(d.get("score"), (int, float)):
            delta = f"{d['score'] - a['score']:+.2f}"
        lineas.append(
            f"| {cint} | {_fmt(a.get('score'))} | {_fmt(d.get('score'))} | {delta} | "
            f"{_fmt(a.get('parametrica_valor'))} | {_fmt(d.get('parametrica_valor'))} |"
        )
    lineas.append("")

    campos = ["valor", "unidad", "fecha_dato", "en_indice", "dimension",
              "puntaje_banda", "peso_efectivo", "aporte_score", "semaforo"]
    ia, idd = antes["indicadores"], despues["indicadores"]

    salieron = sorted(set(ia) - set(idd))
    entraron = sorted(set(idd) - set(ia))
    if salieron:
        lineas.append(f"**Desaparecieron del snapshot:** {', '.join(salieron)}")
    if entraron:
        lineas.append(f"**Aparecieron en el snapshot:** {', '.join(entraron)}")
    if salieron or entraron:
        lineas.append("")

    lineas.append("## Indicadores con cambios")
    lineas.append("| indicador | campo | antes | después |")
    lineas.append("|---|---|---:|---:|")
    sin_cambios = []
    for nombre in sorted(set(ia) & set(idd)):
        a, d = ia[nombre], idd[nombre]
        diffs = [(c, a.get(c), d.get(c)) for c in campos if a.get(c) != d.get(c)]
        if not diffs:
            sin_cambios.append(nombre)
            continue
        for c, va, vd in diffs:
            lineas.append(f"| `{nombre}` | {c} | {_fmt(va)} | {_fmt(vd)} |")
    lineas.append("")
    lineas.append(f"Sin cambios: {len(sin_cambios)} de {len(set(ia) & set(idd))} indicadores comunes.")
    return lineas


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("capturar", help="congela el snapshot actual como línea de base")
    c.add_argument("-o", "--salida", type=Path, required=True)
    c.add_argument("--snapshot", type=Path, default=SNAPSHOT)

    m = sub.add_parser("comparar", help="tabla antes/después contra una línea de base")
    m.add_argument("base", type=Path)
    m.add_argument("--contra", type=Path, default=None,
                   help="manifiesto 'después'; por defecto captura el snapshot actual")
    m.add_argument("-o", "--salida", type=Path, default=None)

    a = p.parse_args(argv)

    if a.cmd == "capturar":
        man = capturar(a.snapshot)
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        a.salida.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print(f"línea de base: {a.salida} — {man['n_indicadores']} indicadores, "
              f"score_global {man['score_global']}, sha {man['sha256_snapshot'][:12]}")
        return 0

    base = json.loads(a.base.read_text(encoding="utf-8"))
    otro = json.loads(a.contra.read_text(encoding="utf-8")) if a.contra else capturar()
    texto = "\n".join(comparar(base, otro)) + "\n"
    if a.salida:
        a.salida.write_text(texto, encoding="utf-8")
        print(f"comparación escrita en {a.salida}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
