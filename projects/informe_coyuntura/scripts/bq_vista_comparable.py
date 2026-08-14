"""Crea en BigQuery la vista `corridas_comparables`: el score global de TODA la
historia recalculado sobre el mismo perímetro de cinturones.

Por qué existe. El 2026-08-14 espíritu de época salió del tablero
([[0205]]): el informe pasó de ponderar cinco cinturones a cuatro. Como era el
más bajo del tablero por margen amplio, el global publicado saltó de 3,5 a 4,2
ese día. **Ese salto es el cambio de perímetro, no coyuntura**, y deja la
columna `score_global` de la tabla `corridas` sin poder leerse de corrido:
las filas de antes se calcularon con cinco cinturones y las de después con
cuatro.

Qué hace. Recalcula el global de cada corrida archivada usando SOLO los cuatro
cinturones vigentes y los pesos de `config.PESOS_CINTURONES`. Sobre esa base la
serie de agosto de 2026 queda 4,0 → 4,2: sube apenas, sin escalón.

Qué NO hace. No toca `corridas` ni `cinturones`. El archivo guarda lo que se
publicó cada día, que es su trabajo; la vista es la lectura comparable al lado.
Y es una VISTA, no una tabla materializada, justamente para que el pipeline
siga sin leer de BigQuery — la regla de una sola dirección que declara
`bigquery_export.py` y que existe para que ningún camino paralelo esquive los
gates.

Los pesos se inyectan desde `config.py` al armar el SQL, así que siguen
teniendo un solo dueño. Si cambian —o si cambia el conjunto de cinturones—,
volvé a correr esto y la vista se redefine sola:

    python scripts/bq_vista_comparable.py --dry-run   # imprime el SQL
    python scripts/bq_vista_comparable.py             # crea/reemplaza la vista
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import PESOS_CINTURONES  # noqa: E402  (necesita el sys.path de arriba)

PROYECTO_POR_DEFECTO = "cigob-analytics"
DATASET_POR_DEFECTO = "informe_coyuntura"
UBICACION = "southamerica-east1"
VISTA = "corridas_comparables"


def sql_de_la_vista(proyecto: str, dataset: str) -> str:
    """El SQL de la vista, con los pesos vigentes inyectados desde config.py."""
    pesos = ",\n      ".join(
        f"STRUCT('{cinturon}' AS cinturon, {peso} AS peso)"
        for cinturon, peso in sorted(PESOS_CINTURONES.items())
    )
    ref = lambda tabla: f"`{proyecto}.{dataset}.{tabla}`"  # noqa: E731
    return f"""\
CREATE OR REPLACE VIEW {ref(VISTA)}
OPTIONS (
  description = "Score global de cada corrida recalculado sobre el perimetro vigente de cinturones (ADR-0205/0207). La tabla corridas guarda lo que se publico ese dia; esta vista lo hace comparable entre si. Generada por scripts/bq_vista_comparable.py -- no editar a mano."
)
AS
WITH pesos AS (
  SELECT * FROM UNNEST([
      {pesos}
  ])
)
SELECT
  r.generated_at,
  r.period,
  r.score_global                                    AS score_global_archivado,
  ROUND(SUM(c.score * p.peso) / SUM(p.peso), 1)     AS score_global_comparable,
  ROUND(SUM(c.score * p.peso) / SUM(p.peso) - r.score_global, 1)
                                                    AS delta,
  COUNT(c.cinturon)                                 AS cinturones_usados
FROM {ref('corridas')}   AS r
JOIN {ref('cinturones')} AS c USING (generated_at)
-- El JOIN es lo que hace el recorte: un cinturon que no esta en `pesos` queda
-- afuera del promedio. Por eso sacar uno del tablero no pide tocar este SQL,
-- solo volver a correr el script que lo genera.
JOIN pesos             AS p ON p.cinturon = c.cinturon
WHERE c.score IS NOT NULL
GROUP BY r.generated_at, r.period, r.score_global
ORDER BY r.generated_at
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto",
                        default=os.environ.get("GCP_PROJECT", PROYECTO_POR_DEFECTO))
    parser.add_argument("--dataset", default=DATASET_POR_DEFECTO)
    parser.add_argument("--dry-run", action="store_true",
                        help="imprime el SQL y no toca BigQuery")
    args = parser.parse_args()

    sql = sql_de_la_vista(args.proyecto, args.dataset)
    if args.dry_run:
        print(sql)
        return 0

    from google.cloud import bigquery

    cliente = bigquery.Client(project=args.proyecto)
    cliente.query(sql, location=UBICACION).result()
    print(f"[OK] vista {args.proyecto}.{args.dataset}.{VISTA} creada/reemplazada")
    print(f"     pesos: {PESOS_CINTURONES}")

    filas = list(cliente.query(
        f"SELECT * FROM `{args.proyecto}.{args.dataset}.{VISTA}` ORDER BY generated_at",
        location=UBICACION,
    ).result())
    print(f"\n{'corrida':21s} {'archivado':>10s} {'comparable':>11s} {'delta':>7s} {'cint':>5s}")
    for f in filas:
        print(f"{str(f.generated_at)[:19]:21s} {f.score_global_archivado:>10} "
              f"{f.score_global_comparable:>11} {f.delta:>+7} {f.cinturones_usados:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
