# -*- coding: utf-8 -*-
"""Redundancia interna del ITVC (ADR-0108)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itvc
import parametrica
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
    comp_dim = _componentes_vigentes()
    assert set(vals[max(vals)]) == comp_dim, (
        f"sobran {set(vals[max(vals)]) - comp_dim}, faltan {comp_dim - set(vals[max(vals)])}"
    )


def _componentes_vigentes():
    """Los que HOY puntúan. `DIMENSIONES_ITVC` conserva el peso de diseño de un
    suspendido (ADR-0245), así que usarla como definición de «componente» haría
    fallar a la matriz por describir correctamente el índice."""
    return {i for d in parametrica.indicadores_vigentes(
                itvc.DIMENSIONES_ITVC, itvc.INDICADORES_SUSPENDIDOS).values()
            for i in d}


def test_todo_componente_puntuable_entra_a_la_matriz():
    """Un componente que pondera y no se mide deja un hueco invisible."""
    m = ve.matriz_redundancia_itvc()
    comp = _componentes_vigentes()
    assert m["n_indicadores"] == len(comp), (
        f"la matriz mide {m['n_indicadores']} de {len(comp)} componentes"
    )


def test_el_componente_de_vehiculos_no_es_redundante_con_el_icc():
    """La pregunta que la auditoría pidió responder empíricamente.

    Planteaba que `patentamiento_motos` podía ser en gran medida redundante con
    el ICC —los dos podían estar midiendo humor del consumidor y no acceso—. No
    lo era, y la pregunta sigue viva sobre el componente que la heredó: desde
    ADR-0224 el que puntúa es `motorizacion_total`, que suma autos y motos.

    Si algún día superara el umbral, la recomendación de la auditoría pasaría a
    estar respaldada y habría que revisarlo.
    """
    m = ve.matriz_redundancia_itvc()
    r = m["matriz"]["motorizacion_total"]["icc_utdt"]
    assert abs(r) < m["umbral"], (
        f"motorización ↔ ICC alcanzó |r|={abs(r):.3f} ≥ {m['umbral']}: la "
        f"hipótesis de la auditoría pasaría a estar respaldada"
    )


def test_el_par_autos_motos_ya_no_esta_en_la_matriz():
    """ADR-0223 tuvo que declarar el par autos↔motos como el único del cinturón
    por encima de 0,7 al destendenciar (+0,801), y con un motivo incómodo: daba
    tan alto porque el techo aplanaba a motos y comparaba a autos contra una
    recta. ADR-0224 lo disuelve fundiendo los dos en un componente.

    Si el par volviera a aparecer, volvería con él ese artefacto de lectura.
    """
    m = ve.matriz_redundancia_itvc()
    assert "patentamiento_motos" not in m["matriz"]
    assert "patentamiento_autos" not in m["matriz"]


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


def test_lo_publicado_cubre_los_componentes_que_hoy_puntuan():
    """El guard que faltaba (ADR-0116).

    La matriz y la validación externa se calculan en `validacion_externa.py` y
    viajan al informe por su JSON. Si se incorpora un componente y no se vuelve
    a correr ese script, el informe publica una matriz de menos componentes y
    una correlación vieja SIN QUE NADA FALLE — pasó con ADR-0111 y ADR-0112:
    entraron `alquiler_real` e `indice_lider` y la matriz siguió diciendo 14
    indicadores mientras el índice ya tenía 16.
    """
    import json
    from pathlib import Path

    snap = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "informe.json"
    bloque = json.loads(snap.read_text(encoding="utf-8"))["cinturones"]["vida_cotidiana"]["itvc"]
    red = bloque.get("redundancia")
    if not red:
        return
    vivos = _componentes_vigentes()
    assert red["n_indicadores"] == len(vivos), (
        f"la matriz publicada mide {red['n_indicadores']} componentes y el índice tiene "
        f"{len(vivos)}: falta correr validacion_externa.py"
    )


def test_ningun_indice_publica_una_matriz_desfasada():
    """El guard de ADR-0116, extendido a los cuatro (ADR-0117).

    La revisión que lo motivó encontró que el ITCG publicaba 64 pares cuando su
    reconstrucción da 70: no faltaban componentes —el conteo coincidía— sino que
    la serie había crecido y más pares pasaron a tener datos. Comparar sólo el
    número de indicadores no lo habría visto; hay que comparar los PARES.
    """
    for sig, fn in (("itcm", ve.matriz_redundancia_itcm),
                    ("itcg", ve.matriz_redundancia_itcg),
                    ("itcp", ve.matriz_redundancia_itcp),
                    ("itvc", ve.matriz_redundancia_itvc)):
        guardada = ve.json.loads(ve.SALIDA.read_text(encoding="utf-8")).get(f"redundancia_{sig}")
        if not guardada:
            continue
        viva = fn()
        assert guardada["n_pares"] == viva["n_pares"], (
            f"{sig}: la matriz publicada mide {guardada['n_pares']} pares y la "
            f"reconstrucción da {viva['n_pares']}: falta correr validacion_externa.py"
        )
