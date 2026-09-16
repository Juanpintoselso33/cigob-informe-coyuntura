"""Tarea 0 (15-sep-2026): `imprimir_resumen` no puede leer un registro plano.

`fetch_consumo_carnes()` devuelve UN registro —{mes, total, vacuna, aviar,
porcina, variaciones}— y no un dict de indicadores. El resumen del pipeline
asumía la segunda forma para TODAS las fuentes, así que con datos frescos y
válidos imprimía "variaciones: None []": el único campo que pasaba el filtro
`isinstance(vals, dict)` era `variaciones`, y ese dict no tiene una clave
`valor` adentro. Se leyó como "el colector falló" cuando en realidad había
traído el mes más reciente sin ningún error.

Control positivo Y negativo en la misma corrida: un registro plano real
(vacuna con dato) tiene que mostrar la vacuna, y uno con la fuente
efectivamente caída (todo en None) tiene que seguir diciendo eso, no fingir
un valor.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "vida_main", ROOT / "scripts" / "vida_cotidiana" / "main.py")
vida_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vida_main)


def test_registro_plano_con_dato_no_dice_none(capsys):
    """Control positivo: el caso real del 15/16-sep-2026, la vacuna con dato
    fresco no puede imprimirse como None."""
    resultados = {
        "consumo_carnes": {
            "mes": "2026-07", "total": 113.94, "vacuna": 46.75,
            "aviar": 47.06, "porcina": 20.13, "ratio_bovina": 41.03,
            "variaciones": {"vacuna": -8.44, "aviar": 0.23,
                            "porcina": 10.13, "total": -2.02},
        }
    }
    vida_main.imprimir_resumen(resultados)
    salida = capsys.readouterr().out
    assert "vacuna: 46.75" in salida
    assert "variaciones: None" not in salida, (
        "el bug original: un registro plano con dato real se imprime como "
        "'variaciones: None', que se lee como fuente caída sin estarlo")


def test_fuente_con_indicadores_anidados_sigue_funcionando(capsys):
    """Control negativo de regresión: no hay que romper el caso mayoritario
    (dict de indicadores, cada uno con su propio {valor, fecha})."""
    resultados = {
        "utdt": {
            "icc_utdt": {"valor": 40.23, "fecha": "2026-08-01"},
        }
    }
    vida_main.imprimir_resumen(resultados)
    salida = capsys.readouterr().out
    assert "icc_utdt: 40.23" in salida


def test_fuente_realmente_caida_sigue_diciendolo(capsys):
    """Si el colector de verdad falló (`_seguro` devuelve None), la fuente ni
    siquiera entra al loop (el `if fuente == ... or not datos: continue`
    la salta) — este test cuida que ese camino siga existiendo."""
    resultados = {"consumo_carnes": None}
    vida_main.imprimir_resumen(resultados)
    salida = capsys.readouterr().out
    assert "CONSUMO_CARNES" not in salida
