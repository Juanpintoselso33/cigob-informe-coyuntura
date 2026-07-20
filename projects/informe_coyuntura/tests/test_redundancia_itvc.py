# -*- coding: utf-8 -*-
"""Redundancia interna del ITVC (ADR-0108)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itvc
import validacion_externa as ve


def test_la_escala_del_itvc_es_la_identidad():
    """Sus componentes YA son índices base 100: el número que se promedia es el
    índice mismo, no un puntaje derivado de bandas."""
    e = ve._EscalaIdentidad({"mora_familias"})
    assert e.puntuable("mora_familias") and not e.puntuable("ipc_total")
    assert e.puntaje(118.4, "mora_familias") == 118.4


def test_matriz_y_reconstruccion_no_pueden_divergir():
    """Comparten `_indices_itvc_por_componente`.

    Si cada una armara sus índices por su lado, con el tiempo la matriz mediría
    una composición distinta de la que el informe publica y nadie lo notaría.
    """
    serie, _, _ = ve.construir_series_itvc()
    vals = ve._valores_itvc_por_mes()
    assert set(vals) == set(serie), "la matriz y la serie no cubren los mismos meses"
    # y los componentes que la matriz mira son exactamente los que el índice
    # pondera: ni uno de más (mediría algo que no entra) ni de menos
    comp_dim = {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    assert set(vals[max(vals)]) == comp_dim, (
        f"sobran {set(vals[max(vals)]) - comp_dim}, faltan {comp_dim - set(vals[max(vals)])}"
    )


def test_todo_componente_puntuable_entra_a_la_matriz():
    """Un componente que pondera y no se mide deja un hueco invisible."""
    m = ve.matriz_redundancia_itvc()
    comp = {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    assert m["n_indicadores"] == len(comp), (
        f"la matriz mide {m['n_indicadores']} de {len(comp)} componentes"
    )


def test_motos_no_es_redundante_con_el_icc():
    """La pregunta que la auditoría pidió responder empíricamente.

    Planteaba que `patentamiento_motos` podía ser en gran medida redundante con
    el ICC. No lo es: queda muy por debajo del umbral en niveles y también en
    cambios mes a mes. Si algún día superara el umbral, la recomendación de la
    auditoría pasaría a estar respaldada y habría que revisarlo.
    """
    m = ve.matriz_redundancia_itvc()
    r = m["matriz"]["patentamiento_motos"]["icc_utdt"]
    assert abs(r) < m["umbral"], (
        f"motos ↔ ICC alcanzó |r|={abs(r):.3f} ≥ {m['umbral']}: la hipótesis de "
        f"la auditoría pasaría a estar respaldada"
    )


def test_el_acoplamiento_en_niveles_no_se_publica_solo():
    """En niveles el ITVC muestra 12 pares altos y en cambios ninguno.

    Publicar sólo el número de niveles diría que el cinturón repite doce veces
    la misma señal, cuando lo que comparten es la época. La lectura en
    diferencias tiene que viajar junto al dato.
    """
    m = ve.matriz_redundancia_itvc()
    assert "diferencias" in m and m["diferencias"]["r_abs_medio"] is not None
    assert m["diferencias"]["r_abs_medio"] < m["r_abs_medio"], (
        "si el acoplamiento ya no cae al destendenciar, la conclusión publicada "
        "sobre «época en común» dejó de ser cierta"
    )
