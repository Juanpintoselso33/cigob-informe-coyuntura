"""El Votómetro se publica por ediciones mensuales en la web de CiGob. El
colector toma la más reciente de las que enlaza el índice, por fecha y no por
orden de aparición (el índice es contenido editable)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica  # noqa: E402


def test_elige_la_edicion_mas_reciente_aunque_no_venga_primera():
    html = ('<a href="/votometro/julio-2026">x</a>'
            '<a href="/votometro/septiembre-2026">x</a>'
            '<a href="/votometro/diciembre-2025">x</a>')
    assert politica._edicion_vigente_votometro(html) == "septiembre-2026"


def test_ignora_enlaces_que_no_son_ediciones():
    html = '<a href="/votometro/metodologia-2026">x</a><a href="/votometro/agosto-2026">x</a>'
    assert politica._edicion_vigente_votometro(html) == "agosto-2026"


def test_sin_ediciones_devuelve_none():
    assert politica._edicion_vigente_votometro('<a href="/ranking-gobernadores">x</a>') is None
