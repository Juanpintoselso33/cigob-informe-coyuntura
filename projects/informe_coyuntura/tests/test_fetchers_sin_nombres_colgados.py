"""Ningún fetcher referencia un nombre global que no existe.

Por qué existe este test: `fetch_icg_serie` usaba `UTDT_ICG_LISTADO` y
`UTDT_ICG_REFERER`, que **no estaban definidas**. Levantaba `NameError` en cada
corrida y el `try/except` de `descargar()` lo tragaba como "fuente caída": la
serie se congelaba y el log culpaba a la UTDT.

ADR-0175 lo arregló el 5-ago-2026 definiendo las dos constantes. El 21-ago un
commit que editaba la función vecina (`fetch_fal_serie`) **se las llevó de
arrastre**, y el bug volvió sin que nada lo notara durante cuatro días.

Un `NameError` sólo aparece al ejecutar la función, y estas funciones salen a la
red: no se pueden correr en tests. Por eso se verifica estáticamente que cada
nombre global que el bytecode va a buscar realmente exista.
"""
import ast
import builtins
import importlib
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
FUENTE = RAIZ / "scripts" / "descargar_series.py"


def _funciones() -> dict[str, ast.FunctionDef]:
    arbol = ast.parse(FUENTE.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(arbol)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("fetch_")}


def _nombres_de_args(a: ast.arguments) -> set[str]:
    nombres = {p.arg for p in a.posonlyargs + a.args + a.kwonlyargs}
    if a.vararg:
        nombres.add(a.vararg.arg)
    if a.kwarg:
        nombres.add(a.kwarg.arg)
    return nombres


def _globales_usados(fn: ast.FunctionDef) -> set[str]:
    """Nombres que la función va a buscar afuera.

    Con AST y no con `co_names`, que mezcla globales con nombres de atributo:
    `xlrd.XL_CELL_DATE` mete `XL_CELL_DATE` ahí aunque no sea un global.

    Se descuenta todo lo que se define adentro, incluidas las funciones
    anidadas y las lambdas **con sus parámetros**: sin eso, un
    `def mensual(vid)` adentro del fetcher denuncia a `vid` como global.
    """
    locales: set[str] = set()

    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            locales.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                locales.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            locales.add(n.name)
            locales |= _nombres_de_args(n.args)
        elif isinstance(n, ast.Lambda):
            locales |= _nombres_de_args(n.args)
        elif isinstance(n, ast.ClassDef):
            locales.add(n.name)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            locales.add(n.name)

    usados = {n.id for n in ast.walk(fn)
              if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return usados - locales


def test_hay_fetchers_para_revisar():
    """Si el módulo se reorganiza y no queda ninguno, el test pasaría vacío."""
    assert len(_funciones()) > 10


@pytest.mark.parametrize("nombre", sorted(_funciones()))
def test_los_nombres_que_usa_existen(nombre):
    mod = importlib.import_module("descargar_series")
    faltan = sorted(
        g for g in _globales_usados(_funciones()[nombre])
        if not hasattr(mod, g) and not hasattr(builtins, g)
    )
    assert not faltan, (
        f"{nombre} usa {faltan}, que no existe(n) en descargar_series.\n"
        f"Al ejecutarse sería un NameError, y `descargar()` lo reporta como "
        f"'fuente caída': la serie se congela y el log culpa al organismo.\n"
        f"Pasó con UTDT_ICG_LISTADO/UTDT_ICG_REFERER (ADR-0175)."
    )
