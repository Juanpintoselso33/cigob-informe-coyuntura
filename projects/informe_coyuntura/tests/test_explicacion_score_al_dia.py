"""La explicación del score de cada cinturón sale del índice publicado.

Escrita a mano, la de política siguió listando «imagen y voto» y 7 dimensiones
meses después de ADR-0344, y la de macro hubo que retocarla en el #75.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INFORME = json.loads((RAIZ / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SIGLAS = {"macro": "itcm", "politica": "itcp", "gestion": "itcg", "vida_cotidiana": "itvc"}


@pytest.mark.parametrize("ckey,sigla", SIGLAS.items())
def test_la_explicacion_nombra_cada_dimension_publicada_y_solo_esas(ckey, sigla):
    c = INFORME["cinturones"][ckey]
    dims = list(c[sigla]["dimensiones"].values())
    texto = c["score_explicacion"]
    assert f"ponderado por {len(dims)} dimensiones" in texto
    for d in dims:
        assert d["nombre"][1:] in texto, f"{ckey}: falta «{d['nombre']}»"
    assert "imagen y voto" not in texto.lower() or any("imagen" in d["nombre"].lower() for d in dims)
