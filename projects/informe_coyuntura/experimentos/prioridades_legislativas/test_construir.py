import json
from pathlib import Path

from construir import construir

HERE = Path(__file__).resolve().parent


def test_escenario_base_no_es_banda_en_el_ultimo_corte():
    # Issue #27, punto 3: con el defecto, el corte 2026-09-10 (posterior al
    # verificado_hasta simulado) mostraba "50% a 100%" en vez de 50% limpio.
    construir()
    data = json.loads((HERE / "vista" / "resultados.json").read_text())
    base = next(c for c in data["casos"] if c["id"] == "base")
    ultimo = base["cortes"][-1]
    assert ultimo["corte"] == data["fechas"][-1]
    assert ultimo["porcentaje"] == 50
    assert ultimo["maximo"] == 50
    assert ultimo["estado"] == "calculable"
