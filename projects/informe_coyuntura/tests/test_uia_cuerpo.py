# -*- coding: utf-8 -*-
"""El texto de una novedad de la UIA se lee entero aunque venga en varios bloques.

Desde oct-2026 el sitio parte algunas notas en dos bloques de párrafos (una
imagen o un título en el medio). El extractor se quedaba con el más largo y
codificamos siete comunicados sobre la mitad de su texto; el truncamiento ya
había obligado a rehacer el corpus entero en jul-2026.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica


# El stream RSC trae las etiquetas escapadas: barra invertida + «u003c».
_LT, _GT = chr(92) + "u003c", chr(92) + "u003e"


def _p(texto: str) -> str:
    return f"{_LT}p data-block-key={chr(92)}\"x{chr(92)}\"{_GT}{texto}{_LT}/p{_GT}"


def test_une_los_bloques_en_orden_y_saca_la_plantilla_de_404():
    html = ("x" + _p("Es posible que el enlace sea incorrecto, que la página haya sido movida.")
            + "<img>" + _p("El miércoles 21 de octubre participamos del primer Plenario.")
            + "<figure>" + _p("Durante la jornada, los sectores intercambiaron propuestas."))
    t = politica._uia_cuerpo(html)
    assert t.startswith("El miércoles 21 de octubre")
    assert "Durante la jornada" in t
    assert "enlace sea incorrecto" not in t


def test_un_bloque_repetido_en_el_stream_no_se_duplica():
    bloque = _p("Celebramos el Día de la Industria.")
    t = politica._uia_cuerpo(bloque + "<br>" + bloque)
    assert t.count("Celebramos") == 1
