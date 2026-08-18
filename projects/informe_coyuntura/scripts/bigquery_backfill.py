"""Rellena en BigQuery las corridas anteriores al 6-ago-2026, reconstruidas desde git.

Por qué existe. El espejo en BigQuery (ADR-0180) arrancó el 6-ago-2026, pero el
informe publica desde el 23-may. Las ~206 corridas del medio existen: cada una
quedó commiteada en `web/src/data/informe.json` y sus artefactos de análisis.
El archivo histórico las estaba perdiendo por no haber existido todavía el
exportador, no por falta de dato.

Cómo. Recorre los commits que tocaron el snapshot, materializa de CADA commit
los seis archivos que el exportador lee, y arma las filas con el código de HOY
sobre el dato de ENTONCES. Al final hace un load por tabla, no uno por corrida.

    python scripts/bigquery_backfill.py --dry-run        # no toca BigQuery
    python scripts/bigquery_backfill.py --limite 5       # las 5 más nuevas
    python scripts/bigquery_backfill.py                  # todo

Cuatro cosas que NO son obvias y que el script resuelve — cada una fue un
resultado medido, no una precaución teórica:

1. **`series` queda afuera.** Se escribe con WRITE_TRUNCATE porque el CSV es la
   verdad y acumular versiones duplicaría. Replayar corridas viejas la
   PISARÍA con las series de junio. La tabla de hoy ya está bien; el backfill
   no la toca.

2. **Los auxiliares se leen por commit, no del working tree.** El exportador
   lee `output/*.json` de `RAIZ`. Si sólo se restaurara el snapshot, las
   correlaciones de HOY quedarían estampadas con un `generated_at` de junio:
   no falla nada y el archivo queda mintiendo. Por eso se materializa el árbol
   de entrada commit por commit.

3. **195 filas traen `valor` de texto.** Cuatro indicadores de gestión fueron
   cualitativos hasta el 2-jul-2026. `bigquery_export._valor_y_texto` los manda
   a `valor_txt` y deja `valor` en NULL.

4. **`origen` distingue cron de manual.** De las 225 corridas sólo 71 son del
   nocturno; el resto son republicaciones a mano y regeneraciones de
   desarrollo. Sin la marca, julio —con 116 corridas manuales— parece un mes de
   saltos violentos del dato que en realidad son iteraciones de código.

Es idempotente: borra las corridas que va a escribir antes de escribirlas, así
que re-correrlo no duplica. Ver ADR-0209.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ.parent.parent  # .../Analisis CIGOB
sys.path.insert(0, str(RAIZ / "scripts"))

import bigquery_export as bq  # noqa: E402

# Ruta del snapshot RELATIVA a la raíz del repo: es como git nombra los blobs.
REL_PROY = "projects/informe_coyuntura"
REL_SNAPSHOT = f"{REL_PROY}/web/src/data/informe.json"

# Los únicos archivos que el exportador abre. Materializar sólo estos da la
# misma fidelidad por commit que un `git worktree` completo, a una fracción del
# costo: 6 blobs contra un checkout entero del árbol, 225 veces.
AUXILIARES = [
    "validacion_externa",
    "sensibilidad",
    "revision_bandas",
    "out_of_sample",
    "procedencia_anclas",
]

# `series` se excluye a propósito (ver el docstring). No es una omisión.
TABLAS_EXCLUIDAS = {"series"}


def git(*args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, errors="replace",
    )
    return r.stdout


def corridas_en_git() -> list[dict]:
    """Una entrada por `generated_at`, con el commit MÁS VIEJO que lo trae.

    Un mismo snapshot puede reaparecer en commits posteriores que tocaron otra
    cosa del archivo; el que interesa es aquel en el que la corrida se produjo,
    porque es el que tiene sus auxiliares al lado.
    """
    vistas: dict[str, dict] = {}
    log = git("log", "--format=%H|%ad|%an", "--date=short", "--follow", "--", REL_SNAPSHOT)
    for linea in log.splitlines():  # git log va de nuevo a viejo
        if not linea.strip():
            continue
        sha, fecha, autor = linea.split("|", 2)
        blob = git("show", f"{sha}:{REL_SNAPSHOT}")
        if not blob.strip():
            continue
        try:
            snap = json.loads(blob)
        except json.JSONDecodeError:
            continue
        gen = snap.get("generated_at")
        if not gen:
            continue
        # Al ir de nuevo a viejo, la última asignación es la del commit más viejo.
        vistas[gen] = {
            "generated_at": gen,
            "sha": sha,
            "fecha": fecha,
            "autor": autor,
            "origen": "cron" if "github-actions" in autor else "manual",
        }
    return sorted(vistas.values(), key=lambda c: c["generated_at"])


def materializar(sha: str, destino: Path) -> Path:
    """Deja en `destino` el árbol mínimo del commit y devuelve la raíz del proyecto."""
    raiz = destino / REL_PROY
    (raiz / "web" / "src" / "data").mkdir(parents=True, exist_ok=True)
    (raiz / "output").mkdir(parents=True, exist_ok=True)

    (raiz / "web" / "src" / "data" / "informe.json").write_text(
        git("show", f"{sha}:{REL_SNAPSHOT}"), encoding="utf-8"
    )
    for nombre in AUXILIARES:
        contenido = git("show", f"{sha}:{REL_PROY}/output/{nombre}.json")
        if contenido.strip():  # nació después: es ausencia legítima, no error
            (raiz / "output" / f"{nombre}.json").write_text(contenido, encoding="utf-8")
    return raiz


def filas_de(corrida: dict, tmp: Path) -> dict[str, list[dict]]:
    raiz = materializar(corrida["sha"], tmp)
    snap = json.loads((raiz / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    filas = bq.construir_filas(snap, raiz=raiz, origen=corrida["origen"])
    filas.update(bq.construir_filas_analisis(corrida["generated_at"], raiz=raiz))
    for t in TABLAS_EXCLUIDAS:
        filas.pop(t, None)
    return filas


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", default=os.environ.get("GCP_PROJECT", bq.PROYECTO_POR_DEFECTO))
    p.add_argument("--dataset", default=bq.DATASET_POR_DEFECTO)
    p.add_argument("--dry-run", action="store_true", help="arma todo y no toca BigQuery")
    p.add_argument("--limite", type=int, default=0, help="sólo las N corridas más nuevas")
    p.add_argument("--solo-origen", choices=["cron", "manual"], help="filtra por origen")
    args = p.parse_args()

    print("leyendo la historia del snapshot desde git...")
    corridas = corridas_en_git()
    if args.solo_origen:
        corridas = [c for c in corridas if c["origen"] == args.solo_origen]
    if args.limite:
        corridas = corridas[-args.limite:]
    if not corridas:
        print("no hay corridas para procesar")
        return 0

    n_cron = sum(1 for c in corridas if c["origen"] == "cron")
    print(f"corridas a procesar: {len(corridas)}  "
          f"(cron {n_cron} · manual {len(corridas) - n_cron})")
    print(f"rango: {corridas[0]['fecha']} → {corridas[-1]['fecha']}\n")

    acumulado: dict[str, list[dict]] = {}
    with tempfile.TemporaryDirectory(prefix="bq-backfill-") as td:
        tmp = Path(td)
        for n, c in enumerate(corridas, 1):
            try:
                filas = filas_de(c, tmp)
            except Exception as e:  # una corrida rota no debe tumbar el backfill
                print(f"  [FALLA] {c['fecha']} {c['sha'][:8]}: {type(e).__name__}: {e}")
                continue
            for tabla, rs in filas.items():
                if rs:
                    acumulado.setdefault(tabla, []).extend(rs)
            if n % 25 == 0 or n == len(corridas):
                print(f"  {n:>4}/{len(corridas)} corridas leídas "
                      f"({sum(len(v) for v in acumulado.values()):,} filas)")

    print("\n=== filas armadas ===")
    for tabla, rs in sorted(acumulado.items()):
        print(f"  {tabla:28} {len(rs):>8,}")
    print(f"  {'TOTAL':28} {sum(len(v) for v in acumulado.values()):>8,}")
    print(f"\n  (`series` excluida a propósito: se escribe con WRITE_TRUNCATE "
          f"y el backfill la pisaría)")

    if args.dry_run:
        print("\n[dry-run, no se escribió nada]")
        return 0

    if not bq._hay_credenciales():
        print("\nERROR: sin credenciales de Google Cloud.", file=sys.stderr)
        return 2

    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery

    cliente = bigquery.Client(project=args.proyecto)
    ds_id = f"{args.proyecto}.{args.dataset}"
    gens = [c["generated_at"] for c in corridas]

    print(f"\nescribiendo en {ds_id} ...")
    for tabla, rs in sorted(acumulado.items()):
        destino = f"{ds_id}.{tabla}"
        # Idempotencia: se borran las corridas que estamos por escribir. El
        # cast es necesario porque en BigQuery la columna es TIMESTAMP y acá
        # viajan como ISO string.
        try:
            cliente.query(
                f"DELETE FROM `{destino}` "
                "WHERE generated_at IN (SELECT TIMESTAMP(g) FROM UNNEST(@gens) AS g)",
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ArrayQueryParameter("gens", "STRING", gens)]
                ),
            ).result()
        except NotFound:
            pass  # la tabla todavía no existe; la crea el load

        cfg = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        )
        cliente.load_table_from_json(rs, destino, job_config=cfg).result()
        print(f"  {tabla:28} {len(rs):>8,} filas -> {destino}")

    # La vista comparable se redefine acá también: el backfill mete corridas de
    # cinco cinturones, y es justamente la vista la que las recorta al perímetro
    # vigente para que la serie se lea de corrido (ADR-0205/0207).
    try:
        import bq_vista_comparable
        cliente.query(
            bq_vista_comparable.sql_de_la_vista(args.proyecto, args.dataset),
            location=bq.UBICACION,
        ).result()
        print(f"\nvista {bq_vista_comparable.VISTA} redefinida")
    except Exception as e:
        print(f"\n  AVISO: no se pudo redefinir la vista comparable: {e}")

    print("\nlisto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
