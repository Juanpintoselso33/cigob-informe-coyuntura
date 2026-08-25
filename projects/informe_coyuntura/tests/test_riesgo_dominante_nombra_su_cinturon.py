# -*- coding: utf-8 -*-
"""El riesgo dominante dice DE QUÉ CINTURÓN sale (ADR-0237).

`BARBARISMO_MAP` manda dos cinturones al mismo barbarismo: `politica` y
`vida_cotidiana` son los dos "político". Así que el nombre del barbarismo no
identifica al cinturón que lo produjo, y la portada lo publicaba solo.

El 25-ago-2026 eso se veía así: "Riesgo dominante: Político" arriba, y abajo
Política en 3,3 y verde contra Impacto social en 6,1 y naranja. El lector
buscaba la card Política, la encontraba entre las más flojas del tablero, y el
veredicto parecía contradecir a su propia tabla. El número estaba bien —lo
calculaba ADR-0208— y aun así la exposición no cerraba.

Estos tests fijan la propiedad, no los números de agosto: mientras dos
cinturones compartan barbarismo, el campo `cinturon_dominante` tiene que estar
y tiene que ser el cinturón de mayor score.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from config import BARBARISMO_MAP, UMBRALES  # noqa: E402
import generar_informe  # noqa: E402

SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"
INTERMEDIO = RAIZ / "output" / "informe.json"


def _datos(scores: dict) -> dict:
    return {k: {"score": v} for k, v in scores.items()}


def test_el_barbarismo_no_alcanza_para_encontrar_el_cinturon():
    """La razón de ser del campo. Si esto deja de valer, el resto es de más."""
    por_barbarismo: dict[str, list[str]] = {}
    for cinturon, barbarismo in BARBARISMO_MAP.items():
        por_barbarismo.setdefault(barbarismo, []).append(cinturon)
    compartidos = {b: cs for b, cs in por_barbarismo.items() if len(cs) > 1}
    assert compartidos, (
        "ningún barbarismo lo comparten dos cinturones: si BARBARISMO_MAP pasó "
        "a ser 1-a-1, este ADR se puede simplificar — pero borralo a mano, no "
        "dejes el campo sin dueño"
    )


def test_el_dominante_es_el_cinturon_de_mayor_score():
    scores = {"macro": 3.6, "politica": 3.3, "vida_cotidiana": 6.1, "gestion": 2.7}
    barbarismo, dominante, _ = generar_informe.detectar_barbarismo(_datos(scores))
    assert dominante == "vida_cotidiana"
    assert barbarismo == BARBARISMO_MAP["vida_cotidiana"]


def test_el_dominante_puede_no_ser_el_cinturon_homonimo():
    """El caso de agosto: gana vida cotidiana y el barbarismo dice "político"."""
    scores = {"macro": 3.6, "politica": 3.3, "vida_cotidiana": 6.1, "gestion": 2.7}
    barbarismo, dominante, _ = generar_informe.detectar_barbarismo(_datos(scores))
    assert barbarismo == "político" and dominante != "politica", (
        "el barbarismo apunta a un cinturón que NO es el dominante: es "
        "exactamente lo que el lector no puede resolver solo"
    )


def test_sin_cinturones_sobre_el_umbral_no_hay_dominante():
    tope = UMBRALES["ESTABLE_MAX"]
    barbarismo, dominante, alerta = generar_informe.detectar_barbarismo(
        _datos({"macro": tope, "politica": tope - 1}))
    assert barbarismo is None and dominante is None and alerta is False


@pytest.mark.parametrize("artefacto", [SNAPSHOT, INTERMEDIO])
def test_lo_publicado_nombra_su_cinturon(artefacto):
    if not artefacto.exists():
        pytest.skip(f"falta {artefacto.relative_to(RAIZ)}: no hubo corrida todavía")
    pub = json.loads(artefacto.read_text(encoding="utf-8"))
    if not pub.get("barbarismo_activo"):
        pytest.skip("sin barbarismo activo este mes")
    dominante = pub.get("cinturon_dominante")
    assert dominante in pub["cinturones"], (
        f"{artefacto.name} publica barbarismo '{pub['barbarismo_activo']}' sin "
        f"decir de qué cinturón sale (cinturon_dominante={dominante!r})"
    )
    assert BARBARISMO_MAP[dominante] == pub["barbarismo_activo"], (
        "el cinturón dominante publicado no produce el barbarismo publicado"
    )
    peor = max(pub["cinturones"].items(), key=lambda kv: kv[1]["score"])[0]
    assert dominante == peor, (
        f"cinturon_dominante={dominante} pero el de mayor score es {peor}: el "
        "veredicto quedó calculado sobre scores que después cambiaron (ADR-0208)"
    )
