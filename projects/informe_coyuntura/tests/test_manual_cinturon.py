"""El manual metodológico de un cinturón se genera del código que corre, así
que puede quedar viejo en silencio: alguien cambia un peso en `itcp.py`, el
índice se recalcula solo, y el manual sigue diciendo el peso anterior.

Es exactamente el modo de falla del índice del README (163 filas para 164
archivos) y de la sección de robustez del ITVC (ADR-0116): un documento
paralelo mantenido aparte del dato.

Este test no compara byte a byte —el motivo de una procedencia de ancla es
prosa que puede reescribirse sin que el método cambie— sino los hechos
estructurales: que el manual liste exactamente las dimensiones, los
indicadores y los pesos que el índice usa hoy.

Si falla: `python scripts/manual_cinturon.py --todos`
"""
import importlib
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import manual_cinturon as MC  # noqa: E402

GENERADOS = [c for c in MC.CINTURONES if (MC.SALIDA / f"{c}.md").exists()]


def test_hay_al_menos_un_manual():
    assert GENERADOS, (
        "no hay ningún manual en docs/manuales/. Corré "
        "`python scripts/manual_cinturon.py --todos`."
    )


@pytest.mark.parametrize("cinturon", GENERADOS)
def test_dimensiones_y_pesos_al_dia(cinturon):
    modulo, indice, _ = MC.CINTURONES[cinturon]
    mod = importlib.import_module(modulo)
    dimensiones = getattr(mod, f"DIMENSIONES_{indice}")
    texto = (MC.SALIDA / f"{cinturon}.md").read_text(encoding="utf-8")

    for dim, d in dimensiones.items():
        assert f"`{dim}`" in texto, (
            f"{cinturon}.md no menciona la dimensión `{dim}`, que hoy pondera "
            f"{d['peso']:.0%}. Regenerá el manual."
        )
        assert f"### Dimensión `{dim}` ({d['peso']:.0%})" in texto, (
            f"{cinturon}.md tiene un peso viejo para `{dim}`: hoy es "
            f"{d['peso']:.0%}. Regenerá el manual."
        )
        for ind, peso_int in d["indicadores"].items():
            assert f"`{ind}`" in texto, (
                f"{cinturon}.md no documenta `{ind}`, que hoy puntúa en "
                f"`{dim}`. Regenerá el manual."
            )
            efectivo = d["peso"] * peso_int
            assert f"**{efectivo:.1%}**" in texto, (
                f"{cinturon}.md no declara el peso efectivo {efectivo:.1%} de "
                f"`{ind}`. Regenerá el manual."
            )


@pytest.mark.parametrize("cinturon", GENERADOS)
def test_no_documenta_indicadores_que_ya_no_puntuan(cinturon):
    """Un indicador que salió del índice no puede seguir en «Qué mide»."""
    modulo, indice, _ = MC.CINTURONES[cinturon]
    mod = importlib.import_module(modulo)
    vivos = {i for d in getattr(mod, f"DIMENSIONES_{indice}").values()
             for i in d["indicadores"]}
    texto = (MC.SALIDA / f"{cinturon}.md").read_text(encoding="utf-8")
    seccion = texto.split("## Qué mide cada indicador")[1].split("\n## ")[0]
    documentados = set(re.findall(r"^`(\w+)`$", seccion, re.M))
    sobran = documentados - vivos
    assert not sobran, (
        f"{cinturon}.md documenta como puntuables indicadores que ya salieron "
        f"del índice: {sorted(sobran)}. Regenerá el manual."
    )


@pytest.mark.parametrize("cinturon", GENERADOS)
def test_los_adr_enlazados_existen(cinturon):
    texto = (MC.SALIDA / f"{cinturon}.md").read_text(encoding="utf-8")
    for destino in set(re.findall(r"\]\(\.\./adr/([^)]+)\)", texto)):
        assert (MC.ADR_DIR / destino).exists(), (
            f"{cinturon}.md enlaza a docs/adr/{destino}, que no existe"
        )
