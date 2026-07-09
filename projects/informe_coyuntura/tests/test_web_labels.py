"""Todo indicador que puntúa en algún índice paramétrico (ITCM/ITCG/ITCP) o
integra una dimensión del ITVC debe tener label + unidad corta + unidad
larga en web/src/lib/datos.ts -- si falta una clave, datos.ts::label() cae
a `key.replace(/_/g, " ")` y la card pública muestra el nombre crudo en
minúsculas ("cohesion bloque senado" en vez de "Cohesión del bloque LLA
(Senado)"). Ya pasó tres veces en este proyecto (Plan2-Task10/11,
alineamiento_senadores_prov, y cohesion_bloque_senado/adhesion_reformas_provincial
el 2026-07-09) sin que ningún gate lo detectara -- gate_calidad.py chequea
que la CARD tenga datos completos, nunca cruzó contra la capa de display.
Este test cierra la clase de bug en vez de solo el síntoma puntual.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itcm
import itcg
import itcp
import itvc

DATOS_TS = (ROOT / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")


def _todos_los_indicadores() -> dict:
    """{indicador: cinturon} de todo lo que puntúa en un índice paramétrico
    o integra el ITVC -- la misma superficie que necesita display en la web."""
    todos = {}
    todos.update({k: "macro" for k in itcm.BANDAS_ITCM})
    todos.update({k: "gestion" for k in itcg.BANDAS_ITCG})
    todos.update({k: "politica" for k in itcp.BANDAS_ITCP})
    for dim in itvc.DIMENSIONES_ITVC.values():
        todos.update({k: "vida" for k in dim["indicadores"]})
    todos.update({k: "vida" for k in itvc.INDICADORES_CONTEXTO})
    return todos


def _apariciones_en_datos_ts(clave: str) -> int:
    """Cuenta cuántas de las 3 tablas de datos.ts (LABELS, unidad corta,
    unidad larga) declaran esta clave como propiedad -- 3 = completo."""
    patron = re.compile(r"(?<![a-zA-Z_])" + re.escape(clave) + r":")
    return len(patron.findall(DATOS_TS))


def test_todo_indicador_paramétrico_tiene_label_y_unidades_en_datos_ts():
    faltantes = [
        f"{cinturon}/{clave} ({_apariciones_en_datos_ts(clave)}/3)"
        for clave, cinturon in sorted(_todos_los_indicadores().items())
        if _apariciones_en_datos_ts(clave) < 3
    ]
    assert not faltantes, (
        "Faltan entradas en LABELS/unidad-corta/unidad-larga de datos.ts "
        f"(o el key.replace(/_/g,' ') de datos.ts::label() se activa en la "
        f"card pública): {faltantes}"
    )
