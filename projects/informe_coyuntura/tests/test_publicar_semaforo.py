"""El semáforo publicado: cobertura, coherencia y que no movió ningún número."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import parametrica

SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"


@pytest.fixture(scope="module")
def informe():
    with open(SNAPSHOT, encoding="utf-8") as f:
        return json.load(f)


def _indicadores(informe):
    for cinturon, bloque in informe["cinturones"].items():
        for ikey, ind in bloque["indicadores"].items():
            yield cinturon, ikey, ind


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


class TestNoMovioNingunNumero:
    """El semáforo es una capa de lectura. Estos son los números que NO puede
    tocar; si alguno cambia, el cambio se salió del alcance."""

    def test_los_indices_siguen_donde_estaban(self, informe):
        # Los valores se pinean contra el snapshot PREVIO al cambio, que el
        # implementador congela en el Step 2 de esta tarea. Comparar el snapshot
        # contra sí mismo no verificaría nada.
        cinturones = informe["cinturones"]
        esperado = json.loads((RAIZ / "tests" / "fixtures" /
                               "indices_previos_semaforo.json").read_text(encoding="utf-8"))
        assert len(esperado["indices"]) == 4
        for cinturon, clave, valor in esperado["indices"]:
            assert cinturones[cinturon][clave]["valor"] == pytest.approx(valor, abs=0.05), (
                f"el semáforo movió {clave}: {cinturones[cinturon][clave]['valor']} "
                f"en vez de {valor}")
        assert informe["score_global"] == pytest.approx(esperado["score_global"], abs=0.05)
