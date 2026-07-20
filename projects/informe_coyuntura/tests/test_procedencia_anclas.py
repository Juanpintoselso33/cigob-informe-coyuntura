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


def test_el_informe_reparte_todo_el_peso():
    """Las categorías tienen que sumar el 100% del peso de cada índice.

    Si no suman, hay peso que se perdió en el camino y el % de circularidad
    publicado está calculado sobre una base equivocada.
    """
    for sig, bloque in pa.informe()["por_indice"].items():
        total = sum(bloque["share"].values())
        assert abs(total - 1.0) < 0.02, f"{sig}: las categorías suman {total:.3f}, no 1"
