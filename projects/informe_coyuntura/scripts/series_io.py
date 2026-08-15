"""Lectura de `output/series/*.csv` — el único armador de series del pipeline.

Vivía sólo dentro de `publicar.py`. `generar_informe.py`, que corre antes, no
tenía cómo leer las series y por eso no podía calcular el ITVC: publicaba el
score legacy que dejaba el colector viejo de vida cotidiana, y los dos
artefactos del informe terminaban diciendo números distintos del mismo mes
(ADR-0206). Acá lo importan los dos (ADR-0208).

Es I/O puro: no sabe nada de índices ni de cinturones.
"""

from __future__ import annotations

import csv
import glob
from pathlib import Path


def build_series(dir_series: Path) -> dict[str, list[dict]]:
    """Agrupa los CSV en {indicador: [{fecha, valor}, ...]} ascendente."""
    series: dict[str, list[dict]] = {}
    for csv_path in sorted(glob.glob(str(Path(dir_series) / "*.csv"))):
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ind = row["indicador"]
                try:
                    val = float(row["valor"])
                except (TypeError, ValueError):
                    continue
                series.setdefault(ind, []).append({"fecha": row["fecha"], "valor": val})
    for ind in series:
        # Deduplicar por fecha: si un indicador aparece en más de un CSV de
        # cinturón con la MISMA métrica, colapsar a un punto por fecha. (Las
        # métricas distintas van bajo claves distintas — ej. ipc_total en % m/m
        # vs ipc_nivel como insumo deflactor.)
        por_fecha = {p["fecha"]: p for p in series[ind]}
        series[ind] = sorted(por_fecha.values(), key=lambda p: p["fecha"])
    return series
