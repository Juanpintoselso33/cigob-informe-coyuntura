"""El semáforo publicado: cobertura, coherencia y que no movió ningún número.

Corre `publicar._semaforos()` EN MEMORIA sobre una copia profunda del
snapshot ya committeado (`web/src/data/informe.json`), en vez de leer el
resultado de una corrida real de `publicar.py`. Motivo: el snapshot
committeado en esta rama no se regenera hasta la Task 8 (pipeline completo,
se corre en `main` después del merge — así no choca con el cron nocturno).
Si estos tests dependieran del snapshot ya publicado con `semaforo`,
quedarían en rojo durante las Tasks 4-7 enteras, sin decir nada sobre si
`_semaforos` sigue funcionando. El snapshot committeado YA pasó por
`aplicar_scoring` (sin el paso `_semaforos`, que es justo lo que se agrega
acá) así que trae todo lo que `_semaforos` necesita como insumo
(`puntaje_itcm/itcg/itcp`, `indice_itvc`, `aporte_score`, `en_indice`,
`valor`, `unidad`) — correrla en memoria sobre una copia es válido y no
escribe ningún archivo (ADR-0179)."""
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import parametrica
import publicar

SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"


def _cargar_snapshot():
    with open(SNAPSHOT, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def informe():
    """Copia del snapshot committeado con `_semaforos` aplicado en memoria."""
    copia = copy.deepcopy(_cargar_snapshot())
    publicar._semaforos(copia)
    return copia


def _indicadores(informe):
    for cinturon, bloque in informe["cinturones"].items():
        for ikey, ind in bloque["indicadores"].items():
            yield cinturon, ikey, ind


def _indices_y_score(informe):
    """Los cuatro índices + score_global: los números que `_semaforos` NO
    puede tocar."""
    c = informe["cinturones"]
    return {
        "itcm": c["macro"]["itcm"]["valor"],
        "itcg": c["gestion"]["itcg"]["valor"],
        "itcp": c["politica"]["itcp"]["valor"],
        "itvc": c["vida_cotidiana"]["itvc"]["valor"],
        "score_global": informe["score_global"],
    }


class TestCobertura:
    def test_todo_indicador_con_tension_tiene_color(self, informe):
        sin_color = [f"{c}/{k}" for c, k, i in _indicadores(informe)
                     if i.get("aporte_score") is not None
                     and not (i.get("semaforo") or {}).get("color")]
        assert sin_color == []

    def test_el_color_es_uno_de_los_cuatro(self, informe):
        validos = {c for c, _ in parametrica.CORTES_SEMAFORO}
        for c, k, i in _indicadores(informe):
            sem = i.get("semaforo")
            if sem:
                assert sem["color"] in validos, f"{c}/{k}: {sem['color']}"

    def test_los_indices_y_sus_dimensiones_tienen_color(self, informe):
        for clave in ("itcm", "itcg", "itcp", "itvc"):
            bloque = next((b[clave] for b in informe["cinturones"].values()
                           if clave in b), None)
            assert bloque, f"falta el bloque {clave}"
            assert bloque["semaforo"]["color"]
            for dim in bloque["dimensiones"].values():
                assert dim["semaforo"]["color"]


class TestCoherencia:
    def test_ningun_color_contradice_su_puntaje(self, informe):
        for cinturon, ikey, ind in _indicadores(informe):
            sem = ind.get("semaforo")
            if not sem:
                continue
            for clave in ("puntaje_itcm", "puntaje_itcg", "puntaje_itcp"):
                p = ind.get(clave)
                if isinstance(p, (int, float)) and ind.get("en_indice"):
                    esperado = parametrica.color_de_puntaje(p)
                    assert sem["color"] == esperado, f"{cinturon}/{ikey}"

    def test_vida_cotidiana_usa_la_formula_base100(self, informe):
        for ikey, ind in informe["cinturones"]["vida_cotidiana"]["indicadores"].items():
            idx = ind.get("indice_itvc")
            if idx is None:
                continue
            assert ind["semaforo"]["color"] == parametrica.color_de_indice_base100(idx), ikey

    def test_los_umbrales_contienen_el_valor_vigente(self, informe):
        """Si el indicador tiene tabla de umbrales, el valor de hoy tiene que
        caer en un tramo del color que se publicó.

        Membresía low-exclusivo / high-inclusivo: la misma convención del
        motor (parametrica.puntaje_banda: `low < valor <= high`), no una
        elegida ad hoc para el test.
        """
        for cinturon, ikey, ind in _indicadores(informe):
            sem = ind.get("semaforo") or {}
            if not sem.get("umbrales") or ind.get("valor") is None:
                continue
            v = float(ind["valor"])
            tramos = [t for t in sem["umbrales"]
                      if (t["desde"] is None or v > t["desde"])
                      and (t["hasta"] is None or v <= t["hasta"])]
            assert tramos, f"{cinturon}/{ikey}: {v} no cae en ningún tramo"
            assert tramos[0]["color"] == sem["color"], f"{cinturon}/{ikey}"


class TestTensionEnDominio:
    """La tensión PUBLICADA (no el color) tiene que quedar en la escala 0-10
    del informe. El color no la delata si se sale del dominio: los cuatro
    cortes de CORTES_SEMAFORO caen todos adentro de [0, 10], así que un valor
    fuera de rango puede seguir dando un color válido (visto en vida
    cotidiana: mora_familias tensión 21,6, pobreza_nowcast −0,4, etc., todas
    con color correcto pese a la tensión fuera de dominio — bug real que este
    test existe para atajar)."""

    def test_ninguna_tension_publicada_sale_de_0_10(self, informe):
        fuera = [(c, k, i["semaforo"]["tension"]) for c, k, i in _indicadores(informe)
                 if i.get("semaforo") and i["semaforo"]["tension"] is not None
                 and not (0.0 <= i["semaforo"]["tension"] <= 10.0)]
        assert fuera == []


class TestNoMovioNingunNumero:
    """El semáforo es una capa de lectura. Estos son los números que NO puede
    tocar; si alguno cambia, el cambio se salió del alcance."""

    def test_los_indices_siguen_donde_estaban(self):
        # Invariancia directa: mismo snapshot base, antes y después de
        # aplicar _semaforos. Más fuerte que pinear contra una fixture
        # congelada en un commit anterior (que solo prueba "no cambió desde
        # tal momento", no "_semaforos específicamente no mueve nada").
        base = _cargar_snapshot()
        antes = _indices_y_score(base)

        despues_informe = copy.deepcopy(base)
        publicar._semaforos(despues_informe)
        despues = _indices_y_score(despues_informe)

        assert despues == antes, (
            f"_semaforos movió un índice o el score global: {despues} en vez de {antes}")
