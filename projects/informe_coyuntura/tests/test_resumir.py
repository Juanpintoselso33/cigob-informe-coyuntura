# -*- coding: utf-8 -*-
"""Tests del resumen de cards (ADR-0165)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import resumir  # noqa: E402

LARGO = (
    "La correlación media entre pares es 0,472: ni componentes independientes ni "
    "repetidos. Cinco pares superan 0,8, y ese es el dato a mirar. La dimensión de "
    "reformas económicas concentra la mayor parte de la redundancia. Se publica "
    "porque el estándar pide explicar las diferencias."
)


def test_un_texto_corto_queda_intacto():
    corto = "El ITCG queda entre 61,8 y 66,2 en el 90% de los casos."
    assert resumir.resumen(corto) == corto
    assert resumir.cola(corto) == ""


def test_corta_en_limite_de_oracion_y_no_a_mitad_de_frase():
    r = resumir.resumen(LARGO)
    assert r.endswith("."), r
    assert "…" not in r and "..." not in r
    assert LARGO.startswith(r)


def test_el_resumen_respeta_el_tope():
    assert len(resumir.resumen(LARGO, tope=120)) <= 260


def test_el_resto_no_se_pierde():
    r, c = resumir.resumen(LARGO), resumir.cola(LARGO)
    # juntando los dos se recupera el texto entero, salvo el espacio del corte
    assert (r + " " + c).replace("  ", " ") == LARGO


def test_no_corta_en_un_numero_con_punto():
    t = ("El índice se recalcula en 1.000 escenarios perturbando los pesos. "
         "La curva es la distribución de resultados y la franja sombreada el 90%. "
         "Se publica con la lectura puesta para que no quede como un adorno técnico.")
    assert resumir.resumen(t).startswith("El índice se recalcula en 1.000 escenarios")


def test_no_corta_en_una_abreviatura():
    t = ("La fuente es la Sec. de Energía y publica todos los meses sin excepción "
         "desde 1994. El resto del panel viene del INDEC y del BCRA, con la misma "
         "frecuencia mensual y sin revisiones retroactivas.")
    assert "de Energía" in resumir.resumen(t)


def test_una_primera_oracion_muy_corta_se_acompana_de_la_siguiente():
    t = ("No alcanza. La correlación media entre pares es 0,472, y eso deja al "
         "índice lejos de los dos extremos que preocupan. Se publica igual porque "
         "es lo que el contraste enseña sobre estos treinta meses.")
    r = resumir.resumen(t)
    assert r.startswith("No alcanza.")
    assert "0,472" in r


def test_anotar_recorre_todo_el_informe():
    informe = {"cinturones": {"gestion": {"itcg": {
        "validacion": {"conclusion": LARGO},
        "redundancia": {"conclusion": "Corto y listo."},
        "lista": [{"conclusion": LARGO}],
    }}}}
    resumir.anotar(informe)
    v = informe["cinturones"]["gestion"]["itcg"]
    assert v["validacion"]["resumen"] and v["validacion"]["detalle_texto"]
    assert "resumen" not in v["redundancia"], "un texto corto no necesita resumen"
    assert v["lista"][0]["resumen"]


def test_anotar_no_toca_la_conclusion_original():
    """El modal y la ficha siguen mostrando el texto completo: si `anotar` lo
    recortara, el desarrollo se perdería en vez de mudarse."""
    informe = {"validacion": {"conclusion": LARGO}}
    resumir.anotar(informe)
    assert informe["validacion"]["conclusion"] == LARGO


def test_anotar_tambien_resume_la_bajada_de_la_seccion():
    """`sub` es lo PRIMERO que se lee, arriba de la card: llegaba a 796
    caracteres y el lector se comía un párrafo antes de ver un número."""
    informe = {"validacion": {"sub": LARGO, "conclusion": LARGO}}
    resumir.anotar(informe)
    v = informe["validacion"]
    assert v["sub_resumen"] and v["sub_detalle"]
    assert v["sub"] == LARGO, "la bajada completa se conserva para el desplegable"
    assert v["sub_resumen"] != v["resumen"] or v["sub"] == v["conclusion"]
