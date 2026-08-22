# -*- coding: utf-8 -*-
"""La serie por dimensión no puede contar otra cosa que el índice (ADR-0233).

Publicar la capa del medio crea un riesgo nuevo y concreto: **dos verdades
sobre el mismo número**. La dimensión ya se publicaba —el `puntaje` del mes en
la card— y ahora además se publica su historia. Si las dos se calcularan por
caminos distintos, tarde o temprano dirían cosas distintas del mismo mes y nada
avisaría: son dos campos del mismo JSON, ninguno de los dos "falla".

Las guardas de acá cierran esa clase, no un síntoma:

1. **Reagregación** — los puntajes de dimensión de un mes, ponderados por su
   peso nominal renormalizado sobre las presentes, tienen que reproducir EXACTO
   el punto del índice de ese mes. Es la aritmética del motor: si la serie por
   dimensión se calculara con otros pesos, con otro criterio de faltantes o
   sobre otro conjunto de componentes, este número deja de dar.
2. **La cola contra la card** — cuando la reconstrucción llega al mismo mes que
   publica el snapshot, el último punto de cada dimensión tiene que ser el
   `puntaje` de la card. Las divergencias conocidas van declaradas abajo con su
   causa: una guarda con excepciones enumeradas sigue siendo una guarda —lo que
   no puede haber es una divergencia que nadie escribió.
3. **Sin relleno** — un mes sin dato queda sin punto. Ni arrastre ni
   interpolación en esta capa.
4. **Techo de winsorización** — se aplica al COMPONENTE, y la dimensión agrega
   los componentes ya recortados. Una dimensión sin componentes exentos no
   puede superar el techo.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import bigquery_export
import itvc
import validacion_externa as ve

SNAPSHOT = json.loads((RAIZ / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
VALIDACION = json.loads((RAIZ / "output" / "validacion_externa.json").read_text(encoding="utf-8"))
SERIES_DIM = VALIDACION.get("series_dimensiones") or {}

CINTURON_DE_INDICE = {"itcm": "macro", "itcg": "gestion", "itvc": "vida_cotidiana",
                      "itcp": "politica"}
SIGLAS = sorted(CINTURON_DE_INDICE)


# ── Divergencias DECLARADAS entre la cola de la serie y la card ──────────────
#
# Cada entrada es un caso donde la reconstrucción histórica y el índice vivo NO
# calculan igual el mismo mes, con la causa localizada. No son tolerancias: son
# defectos conocidos, y están acá para que el día que aparezca uno NUEVO el test
# lo agarre en vez de quedar tapado por un margen genérico.
#
# NINGUNA se arregla desde este ADR: ADR-0233 expone lo que ya se calcula, no
# cambia qué se calcula. Arreglar una mueve la serie publicada del índice y sus
# correlaciones, y eso necesita su propio ADR.
DIVERGENCIAS_DECLARADAS = {
    ("itvc", "empleo"): (
        "`informalidad` se rebasea distinto en los dos caminos. El índice vivo "
        "(itvc.indices_desde_series) la trata como la serie TRIMESTRAL que es y "
        "toma como base el 4T-2023 exacto, o sea el punto 2023-10 (35,7 → índice "
        "94,2). La reconstrucción (validacion_externa.COMPONENTES) la sigue "
        "declarando `anual=True`, así que su base es el PRIMER valor de 2023, el "
        "punto 2023-01 (36,7 → índice 96,8). El propio comentario de itvc.py dice "
        "que la serie trimestral «reemplaza la excepción anual»; la reconstrucción "
        "nunca se actualizó. Diferencia en la dimensión: 0,9 puntos. Hallado al "
        "escribir ADR-0233 y NO tocado ahí — cambiar el flag mueve la serie "
        "histórica del ITCIS y las correlaciones que se publican con ella."
    ),
}


def _serie_indice(sigla):
    return VALIDACION.get(f"serie_{sigla}") or {}


def _indice_del_snapshot(sigla):
    return (SNAPSHOT["cinturones"][CINTURON_DE_INDICE[sigla]] or {}).get(sigla) or {}


def test_los_cuatro_indices_publican_serie_por_dimension():
    """No es una guarda de contenido sino de PERÍMETRO: si un índice deja de
    emitir sus dimensiones, el resto de los tests de este archivo no tendría
    nada que mirar y pasarían todos en verde sobre el vacío."""
    assert set(SERIES_DIM) == set(SIGLAS), f"faltan índices: {set(SIGLAS) - set(SERIES_DIM)}"
    for sigla in SIGLAS:
        assert SERIES_DIM[sigla], f"{sigla} publica un bloque de dimensiones vacío"


@pytest.mark.parametrize("sigla", SIGLAS)
def test_las_dimensiones_reagregadas_reproducen_el_indice(sigla):
    """LA guarda: el índice de cada mes tiene que salir de sus dimensiones.

    El motor calcula `indice = Σ puntaje_dim × peso_dim / Σ pesos presentes`
    sobre los puntajes YA redondeados a un decimal, así que la reproducción es
    exacta y no admite tolerancia. Que dé es la prueba de que la serie por
    dimensión salió del mismo cálculo que la serie del índice: mismos meses,
    mismos pesos, mismo criterio ante un componente faltante.
    """
    bloque, serie = SERIES_DIM[sigla], _serie_indice(sigla)
    assert serie, f"no hay serie del índice {sigla} contra la que reagregar"
    for ym, valor in sorted(serie.items()):
        presentes = [(d["peso"], d["serie"][ym]) for d in bloque.values() if ym in d["serie"]]
        assert presentes, f"{sigla} {ym}: el índice tiene punto y ninguna dimensión"
        suma = sum(p for p, _ in presentes)
        reagregado = round(sum(v * p / suma for p, v in presentes), 1)
        assert reagregado == valor, (
            f"{sigla} {ym}: reagregar las {len(presentes)} dimensiones da "
            f"{reagregado} y el índice publica {valor}")


@pytest.mark.parametrize("sigla", SIGLAS)
def test_los_meses_de_dimension_son_los_del_indice(sigla):
    """Ninguna dimensión puede tener un mes que el índice descartó (piso de
    cobertura, mes en curso): publicar la parte de un número que se decidió no
    publicar es peor que no publicar ninguno de los dos."""
    meses_indice = set(_serie_indice(sigla))
    for dkey, d in SERIES_DIM[sigla].items():
        sobra = set(d["serie"]) - meses_indice
        assert not sobra, f"{sigla}/{dkey} publica meses que el índice no tiene: {sorted(sobra)}"


@pytest.mark.parametrize("sigla", SIGLAS)
def test_la_cola_de_la_serie_coincide_con_la_card(sigla):
    """Cuando la reconstrucción alcanza el mes del snapshot, el último punto de
    cada dimensión ES el `puntaje` que ya publica la card.

    Sólo se exige donde los dos hablan del MISMO mes. Los tres índices por
    bandas cortan la reconstrucción en el último mes completo con cobertura
    suficiente, que hoy es anterior al de la card: comparar ahí sería comparar
    junio contra agosto y llamar bug a la diferencia entre dos meses.
    """
    indice = _indice_del_snapshot(sigla)
    dims_snapshot = indice.get("dimensiones") or {}
    serie = _serie_indice(sigla)
    assert dims_snapshot and serie
    if max(serie) != SNAPSHOT["period"]:
        pytest.skip(f"la reconstrucción de {sigla} llega a {max(serie)} y la card "
                    f"publica {SNAPSHOT['period']}: son meses distintos")
    ym = SNAPSHOT["period"]
    for dkey, d in SERIES_DIM[sigla].items():
        if ym not in d["serie"]:
            continue
        esperado = dims_snapshot[dkey]["puntaje"]
        obtenido = d["serie"][ym]
        if (sigla, dkey) in DIVERGENCIAS_DECLARADAS:
            assert obtenido != esperado, (
                f"{sigla}/{dkey} está declarada como divergente y ya no diverge "
                f"({obtenido}): sacala de DIVERGENCIAS_DECLARADAS, o el registro "
                f"empieza a tapar la próxima divergencia real")
            continue
        assert obtenido == esperado, (
            f"{sigla}/{dkey} en {ym}: la serie dice {obtenido} y la card {esperado}. "
            f"Son dos verdades sobre el mismo número. Si la divergencia es "
            f"legítima y conocida, declarala en DIVERGENCIAS_DECLARADAS con su "
            f"causa; no se tapa con una tolerancia.")


def test_el_snapshot_publica_la_serie_que_calculo_la_validacion():
    """El eslabón que este proyecto ya rompió antes: un valor calculado en
    `output/` que `publicar.py` nunca sube a la página. Acá se cruzan los dos
    artefactos punto por punto."""
    vistas = 0
    for sigla in SIGLAS:
        dims = (_indice_del_snapshot(sigla).get("dimensiones") or {})
        for dkey, dim in dims.items():
            publicada = dim.get("serie")
            calculada = (SERIES_DIM[sigla].get(dkey) or {}).get("serie") or {}
            if len(calculada) < 12:
                assert not publicada, (
                    f"{sigla}/{dkey} publica una serie de {len(calculada)} meses: "
                    f"por debajo del mínimo, un tramo corto se lee como pendiente")
                continue
            assert publicada, f"{sigla}/{dkey} calculó {len(calculada)} meses y no publicó ninguno"
            assert [list(p) for p in publicada] == [[ym, calculada[ym]] for ym in sorted(calculada)], (
                f"{sigla}/{dkey}: la serie del snapshot no es la que calculó la validación")
            vistas += 1
    assert vistas >= 20, f"sólo {vistas} dimensiones publicadas: el cruce no está mirando casi nada"


def test_cada_indice_declara_el_periodo_y_la_escala_de_su_seccion():
    """La sección se lee sin contexto: sin período declarado, un lector supone
    que la serie llega al mes de la card, y en tres de los cuatro índices no."""
    for sigla in SIGLAS:
        indice = _indice_del_snapshot(sigla)
        meta = indice.get("dimensiones_serie")
        assert meta, f"{sigla} publica series por dimensión sin encabezado"
        serie = _serie_indice(sigla)
        assert meta["desde"] == min(serie) or meta["desde"] >= min(serie)
        assert meta["hasta"] == max(serie), (
            f"{sigla}: el encabezado dice que llega a {meta['hasta']} y la serie "
            f"del índice llega a {max(serie)}")
        assert meta["base100"] == (sigla == "itvc")
        assert meta["n_dimensiones"] >= 2


def test_no_hay_arrastre_ni_interpolacion_en_la_capa_de_dimension():
    """Un mes sin ningún componente de la dimensión no deja punto.

    Se verifica RECONSTRUYENDO en vivo y comparando contra lo publicado, que es
    lo único que distingue "no había dato" de "se rellenó con el anterior": las
    dos formas producen un JSON igual de válido.

    El único arrastre del proyecto es el del ITCIS a nivel COMPONENTE ("último
    dato disponible", doc IV.2.1), y ocurre antes de que el motor vea el mes. Si
    alguien agrega un segundo arrastre acá, el conjunto de meses cambia.
    """
    vivo = {}
    ve.construir_series_itvc(vivo)
    publicado = SERIES_DIM["itvc"]
    assert set(vivo) == set(publicado)
    for dkey, d in publicado.items():
        assert set(d["serie"]) == set(vivo[dkey]["serie"]), (
            f"itvc/{dkey}: los meses publicados no son los que produce el motor")
    # Y el caso concreto que motiva la regla: la seguridad arranca después que
    # el resto (su fuente no medía en dic-2023) y ese hueco se publica como
    # hueco, no como un valor inventado hacia atrás.
    seguridad = publicado["seguridad"]["serie"]
    ingresos = publicado["ingresos"]["serie"]
    assert min(seguridad) > min(ingresos), (
        "seguridad dejó de tener arranque tardío: si la fuente cambió, revisar "
        "que el hueco inicial siga representándose como ausencia")


def test_el_techo_de_winsorizacion_se_aplico_al_componente():
    """El techo (ADR-0033) acota COMPONENTES, no dimensiones, y la dimensión
    agrega los componentes ya recortados. Entonces una dimensión cuyos
    componentes no tienen exención no puede superar el techo: si lo supera, se
    agregó sobre valores sin recortar y la serie y el índice miden distinto."""
    assert ve.ITVC_TECHO == itvc.WINSOR_TOPE
    assert ve.TECHO_EXENTOS == itvc.WINSOR_EXENTOS
    for dkey, dim in itvc.DIMENSIONES_ITVC.items():
        serie = (SERIES_DIM["itvc"].get(dkey) or {}).get("serie") or {}
        if not serie or (set(dim["indicadores"]) & set(itvc.WINSOR_EXENTOS)):
            continue
        techo = max(serie.values())
        assert techo <= ve.ITVC_TECHO, (
            f"itvc/{dkey} llega a {techo} sin componentes exentos del techo "
            f"({ve.ITVC_TECHO}): la agregación usó componentes sin recortar")


def test_la_dimension_dominada_por_un_componente_lo_pone_en_la_misma_escala():
    """La versión original de esta guarda exigía que `vulnerabilidad` fuera 100%
    `mora_familias`, y su docstring decía que si algún día dejaba de serlo el
    texto que lo explica quedaba mintiendo. **Disparó el mismo día**: ADR-0231
    le sumó la carga del servicio de deuda al 30%. La guarda hizo su trabajo y
    el texto de la ficha se reescribió.

    Lo que se cuida ahora es lo que sigue siendo cierto y es el motivo por el
    que la serie vale: una dimensión con pocos componentes tiene una serie muy
    pegada a la de ellos, y lo que aporta no es información nueva sobre el
    componente sino ponerlo en la MISMA ESCALA que las otras cinco, que es lo
    único que permite comparar cuánto se movió cada una."""
    dim = itvc.DIMENSIONES_ITVC["vulnerabilidad"]["indicadores"]
    assert len(dim) <= 2, (
        "vulnerabilidad dejó de ser una dimensión chica: revisá el texto de la "
        "ficha, que explica la serie apoyándose en que lo es")
    dominante = max(dim, key=lambda k: dim[k]["peso"] if isinstance(dim[k], dict) else dim[k])
    serie = SERIES_DIM["itvc"]["vulnerabilidad"]["serie"]
    comp = ve._indices_itvc_por_componente()[dominante]
    ym = max(serie)
    previos = [k for k in comp if k <= ym]
    # No son el mismo número —hay un segundo componente— pero la dimensión no
    # puede despegarse del que se lleva el 70%.
    assert abs(serie[ym] - comp[max(previos)]) < 40, (
        f"la dimensión ({serie[ym]}) se despegó de su componente dominante "
        f"{dominante} ({comp[max(previos)]}): revisá el reparto de pesos")


def test_bigquery_recibe_la_serie_por_dimension_en_tabla_propia():
    """Sin esto la serie queda sólo en el snapshot de hoy: el archivo histórico
    de BigQuery es lo que permite preguntar cómo se movió una dimensión a través
    de las corridas, y una tabla que nadie llena no da error."""
    filas = bigquery_export.construir_filas_analisis(SNAPSHOT["generated_at"])
    assert "series_dimensiones" in filas, "la tabla no está declarada en el export"
    rs = filas["series_dimensiones"]
    esperadas = sum(len(d["serie"]) for b in SERIES_DIM.values() for d in b.values())
    assert len(rs) == esperadas, f"se exportan {len(rs)} filas de {esperadas}"
    assert {"generated_at", "indice", "dimension", "nombre", "peso", "periodo", "valor"} == set(rs[0])
    # La dimensión va en su propia columna y no dentro del nombre de la serie:
    # es lo que permite unirla con la tabla `dimensiones` sin parsear strings.
    assert all(r["dimension"] and "_dim_" not in (r["indice"] or "") for r in rs)
    # Y no puede colarse por el barrido de `serie_*` a `series_indices`, que no
    # tiene dónde poner de qué dimensión se trata.
    assert not any("_dim_" in f["serie"] for f in filas["series_indices"])
