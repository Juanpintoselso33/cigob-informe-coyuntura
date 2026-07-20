# -*- coding: utf-8 -*-
"""El registro de procedencia de anclas no puede quedarse atrás (ADR-0103).

Un registro de procedencia desactualizado es peor que no tener ninguno: declara
una cobertura que ya no es cierta. Estos tests lo atan al código real, de modo
que agregar un indicador sin decir de dónde salen sus anclas rompe la suite en
vez de pasar en silencio.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import procedencia_anclas as pa


def test_todo_indicador_que_puntua_declara_su_procedencia():
    """El caso que motiva el archivo: un indicador nuevo sin declarar.

    Si esto falla, el indicador que aparece en el mensaje entró a un índice sin
    que nadie dijera de dónde salen sus cortes. Declararlo es parte de
    incorporar un indicador, no un extra.
    """
    faltantes = pa.informe()["sin_clasificar"]
    assert not faltantes, (
        f"indicadores que puntúan sin procedencia declarada: {faltantes}. "
        f"Agregalos a PROCEDENCIA en scripts/procedencia_anclas.py."
    )


def test_no_sobra_procedencia_de_indicadores_que_ya_no_puntuan():
    """El error espejo: dejar declarada un ancla de algo que ya salió del índice.

    Es menos grave —no oculta nada— pero infla la cobertura aparente y con el
    tiempo el registro deja de describir el índice vivo.
    """
    vivos = set(pa._indicadores_del_indice())
    sobrantes = sorted(set(pa.PROCEDENCIA) - vivos)
    assert not sobrantes, (
        f"PROCEDENCIA declara indicadores que ya no puntúan: {sobrantes}. "
        f"Sacalos, o el % de circularidad se calcula sobre un índice que no existe."
    )


@pytest.mark.parametrize("indicador,entrada", sorted(pa.PROCEDENCIA.items()))
def test_cada_entrada_esta_bien_formada(indicador, entrada):
    """Categoría conocida y motivo con contenido.

    El motivo es lo que hace auditable la clasificación: sin él, `externa` es
    una afirmación sin respaldo — exactamente lo que el registro viene a evitar.
    """
    categoria, motivo = entrada
    assert categoria in pa.CATEGORIAS, f"{indicador}: categoría desconocida «{categoria}»"
    assert motivo and len(motivo) > 15, f"{indicador}: el motivo no explica nada"


def test_una_ancla_externa_cita_su_fuente():
    """`externa` es la categoría que más pesa en la lectura del registro.

    Es la que afirma "esto no se calibró con el período que estamos midiendo",
    así que su motivo tiene que nombrar la referencia. Sin nombre verificable,
    la categoría correcta es otra.
    """
    sin_fuente = []
    for ind, (cat, motivo) in pa.PROCEDENCIA.items():
        if cat != "externa":
            continue
        # una fuente citable trae nombre propio o un período ajeno al medido
        tiene_nombre = any(c.isupper() for c in motivo.replace("ADR", ""))
        tiene_periodo = any(str(a) in motivo for a in range(1983, 2024))
        if not (tiene_nombre or tiene_periodo):
            sin_fuente.append(ind)
    assert not sin_fuente, f"declarados `externa` sin citar la referencia: {sin_fuente}"


def test_la_circularidad_no_sube():
    """El trinquete (ADR-0105): un índice no puede volverse MÁS circular.

    Si esto falla, se incorporó un indicador con anclas calibradas contra el
    período que se está midiendo, o se degradó uno existente. Eso puede estar
    bien —a veces no hay alternativa— pero tiene que ser una decisión tomada y
    visible, no un efecto lateral. Para eso hay que subir el techo a mano en
    scripts/procedencia_anclas.py, y ese cambio se ve en el diff.
    """
    for sig, bloque in pa.informe()["por_indice"].items():
        techo = pa.TECHOS[sig]["circular"]
        assert bloque["share_circular"] <= techo + 0.005, (
            f"{sig}: la fracción circular subió a {bloque['share_circular']:.1%} "
            f"(techo {techo:.1%}). Si es deliberado, subí el techo y explicá por qué."
        )


def test_las_anclas_sin_declarar_no_suben():
    """Caso aparte porque es el único que se arregla gratis.

    Una convención sin alternativa externa a veces es inevitable; una convención
    SIN DECLARAR nunca lo es — sólo hay que escribir de dónde salió. Que este
    número suba no tiene defensa posible.
    """
    for sig, bloque in pa.informe()["por_indice"].items():
        actual = bloque["share"].get("sin_declarar", 0.0)
        techo = pa.TECHOS[sig]["sin_declarar"]
        assert actual <= techo + 0.005, (
            f"{sig}: anclas sin procedencia declarada subieron a {actual:.1%} "
            f"(techo {techo:.1%}). Escribí de dónde salen las nuevas."
        )


def test_el_techo_sigue_a_la_mejora():
    """Un techo muy por encima del valor real deja de frenar nada.

    Si el número bajó de verdad, hay que bajar el techo en el mismo cambio: es
    lo que convierte una mejora puntual en una que no se puede deshacer sin que
    alguien lo note.
    """
    for sig, bloque in pa.informe()["por_indice"].items():
        holgura = pa.TECHOS[sig]["circular"] - bloque["share_circular"]
        assert holgura <= 0.05, (
            f"{sig}: la circularidad bajó a {bloque['share_circular']:.1%} pero el "
            f"techo sigue en {pa.TECHOS[sig]['circular']:.1%}. Bajalo para fijar la mejora."
        )


def test_todo_indice_tiene_techo():
    """Un índice nuevo sin techo entraría sin límite y sin que nadie lo note."""
    assert set(pa.informe()["por_indice"]) <= set(pa.TECHOS), (
        f"índices sin techo declarado: {set(pa.informe()['por_indice']) - set(pa.TECHOS)}"
    )


def test_el_informe_reparte_todo_el_peso():
    """Las categorías tienen que sumar el 100% del peso de cada índice.

    Si no suman, hay peso que se perdió en el camino y el % de circularidad
    publicado está calculado sobre una base equivocada.
    """
    for sig, bloque in pa.informe()["por_indice"].items():
        total = sum(bloque["share"].values())
        assert abs(total - 1.0) < 0.02, f"{sig}: las categorías suman {total:.3f}, no 1"
