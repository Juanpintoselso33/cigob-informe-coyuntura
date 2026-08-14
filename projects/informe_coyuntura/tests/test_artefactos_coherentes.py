# -*- coding: utf-8 -*-
"""Los dos artefactos publicados dicen lo mismo (ADR-0206).

El informe publica DOS cosas que un tercero puede leer:

  · `output/informe.json` + `informe.md` — schema v1.0.0, "para dev externo",
    lo escribe `generar_informe.py`.
  · `web/src/data/informe.json` — el snapshot del sitio y de BigQuery, lo
    escribe `publicar.py`.

Hasta el 2026-08-14 **discrepaban en silencio**. `generar_informe.py` corre
antes y no puede calcular el ITVC: sólo ve el caché del colector viejo de vida
cotidiana (3 indicadores, score legacy). `publicar.py` lo calcula de verdad
desde las series (17 indicadores). Con la corrida de agosto de 2026 eso daba
vida cotidiana 2,9 contra 6,9, y score global 2,7 contra 3,5 — dos números
distintos del mismo mes, publicados a la vez, sin un solo test que fallara.

Se encontró de casualidad: al sacar espíritu de época, `generar_informe.py`
devolvió un global que no cuadraba con el esperado y hubo que ir a `git show`
para descartar que fuera un bug recién introducido. No lo era; era de antes.

Estos tests son el guard que faltaba. Si alguien saca la reconciliación de
`publicar.py`, o si el arreglo de fondo (mover el ITVC a un módulo compartido)
se hace mal, esto falla acá y no en la cara de un lector.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INTERMEDIO = RAIZ / "output" / "informe.json"
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"


def _cargar(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"falta {path.relative_to(RAIZ)}: no hubo corrida todavía")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def artefactos():
    return _cargar(INTERMEDIO), _cargar(SNAPSHOT)


def test_mismo_conjunto_de_cinturones(artefactos):
    intermedio, snapshot = artefactos
    assert set(intermedio["cinturones"]) == set(snapshot["cinturones"]), (
        "el artefacto intermedio y el snapshot publicado listan cinturones "
        "distintos: un cinturón se agregó o se retiró en un solo lado"
    )


def test_mismo_score_por_cinturon(artefactos):
    """El que se rompía: vida cotidiana, 2,9 contra 6,9."""
    intermedio, snapshot = artefactos
    difieren = {
        k: (intermedio["cinturones"][k].get("score"), v.get("score"))
        for k, v in snapshot["cinturones"].items()
        if k in intermedio["cinturones"]
        and intermedio["cinturones"][k].get("score") != v.get("score")
    }
    assert not difieren, (
        "output/informe.json y web/src/data/informe.json publican scores "
        f"distintos (intermedio, snapshot): {difieren}. La verdad la calcula "
        "publicar.py; si esto falla, se cayó _reconciliar_intermedio()"
    )


def test_mismo_score_global(artefactos):
    intermedio, snapshot = artefactos
    assert intermedio.get("score_global") == snapshot.get("score_global"), (
        f"score_global intermedio={intermedio.get('score_global')} "
        f"snapshot={snapshot.get('score_global')} — son el mismo mes"
    )


def test_el_md_declara_el_mismo_global(artefactos):
    """`informe.md` lleva el global en su frontmatter y es lo primero que lee
    un humano que abre el artefacto. Se regenera junto con el .json; si
    alguien parchea uno y no el otro, esto lo agarra."""
    _, snapshot = artefactos
    md = RAIZ / "output" / "informe.md"
    if not md.exists():
        pytest.skip("todavía no hay informe.md")
    linea = f"score_global: {snapshot['score_global']}"
    assert linea in md.read_text(encoding="utf-8"), (
        f"informe.md no declara '{linea}' — quedó con el global viejo"
    )
