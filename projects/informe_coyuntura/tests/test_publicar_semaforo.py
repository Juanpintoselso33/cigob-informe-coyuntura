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


def _tensiones_publicadas(nodo, ruta=""):
    """Recorre el snapshot ENTERO (dicts y listas, cualquier profundidad) y
    devuelve (ruta, valor) de cada clave `tension` que encuentra -- sin
    enumerar a mano indicador/dimensión/índice, que son los tres lugares que
    hoy la publican.

    Motivo (ADR-0182, ADR-0184): el mismo bug -- perder el acotamiento a
    [0, 10] al re-derivar la fórmula de tensión a mano en vez de reusar
    `itvc.tension_de_itvc()` -- ya ocurrió dos veces, cada vez en un lugar
    que el guard anterior no miraba porque `TestTensionEnDominio` solo
    iteraba `_indicadores(informe)`. Un recorrido genérico cubre también un
    cuarto lugar que empiece a publicar `tension` mañana, sin que nadie
    tenga que acordarse de extender esta función a mano -- que es
    exactamente el error que produjo el bug las dos veces anteriores.
    """
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            sub_ruta = f"{ruta}.{clave}" if ruta else clave
            if clave == "tension":
                yield sub_ruta, valor
            else:
                yield from _tensiones_publicadas(valor, sub_ruta)
    elif isinstance(nodo, list):
        for i, valor in enumerate(nodo):
            yield from _tensiones_publicadas(valor, f"{ruta}[{i}]")


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
    del informe, la publique quien la publique -- indicador, dimensión o
    índice. El color no la delata si se sale del dominio: los cuatro cortes
    de CORTES_SEMAFORO caen todos adentro de [0, 10], así que un valor fuera
    de rango puede seguir dando un color válido.

    El mismo defecto ya pasó dos veces, siempre por re-derivar a mano una
    fórmula que ya existe como función (perdiendo su clamp) en vez de
    reusarla:
    - ADR-0182: seis tensiones de INDICADOR del ITVC fuera de [0, 10]
      (mora_familias 21,6, patentamiento_motos −3,0, etc.), todas con color
      correcto pese al valor fuera de dominio. Se atajó reusando
      `itvc.tension_de_itvc()`, que clampea.
    - ADR-0184: la misma re-derivación, ahora en una DIMENSIÓN
      (`vulnerabilidad`, ITVC, puntaje 17,2 → tensión cruda 21,6, acotada a
      10,0 antes de publicarse). El guard de arriba no lo hubiera detectado
      porque `TestTensionEnDominio` en ese momento solo recorría
      `_indicadores(informe)` -- nunca miraba `dimensiones[k]["semaforo"]`.

    Por eso este test recorre el snapshot ENTERO con `_tensiones_publicadas`
    en vez de iterar una de las formas conocidas: la lección de las dos
    veces anteriores es que enumerar los lugares a mano es precisamente lo
    que deja pasar el próximo.

    `tension: null` (hoy, el bloque del ÍNDICE -- ITCM/ITCG/ITCP/ITVC en su
    nivel superior -- lo publica así a propósito, ADR-0184: no tiene todavía
    ningún modal que lo consuma) no es "fuera del dominio": no es un número
    publicado, así que no hay nada que acotar. Se ignora, no se falla.
    """

    def test_ninguna_tension_publicada_sale_de_0_10(self, informe):
        fuera = [(ruta, v) for ruta, v in _tensiones_publicadas(informe)
                 if v is not None and not (0.0 <= v <= 10.0)]
        assert fuera == []


class TestPorQue:
    """`_por_que` arma "a X del corte más cercano" -- tiene que comparar las
    DOS distancias del tramo (a `desde` y a `hasta`), no asumir que el corte
    más cercano es siempre `desde`.

    Bug real de la revisión final de esta rama: tomaba `desde` cuando existía
    y nunca miraba `hasta`, así que en cualquier tramo donde el valor cae más
    cerca de `hasta` la prosa publicaba la distancia al corte LEJANO. Afectó
    12/49 indicadores del snapshot real -- p. ej. `ratio_dnu` (tramo
    naranja 1,6–1,8667, valor 1,84): el corte más cercano es `hasta` a 0,03,
    y la versión rota publicaba 0,24 (la distancia a `desde`)."""

    def test_toma_el_borde_mas_cercano_cuando_es_hasta(self):
        # Tramo [10, 20]; el valor 19 está a 9 de `desde` y a 1 de `hasta` --
        # el corte más cercano es `hasta`, no `desde`.
        tramo = [{"color": "amarillo", "desde": 10.0, "hasta": 20.0}]
        frase = publicar._por_que("amarillo", 19.0, "%", tramo)
        assert "a 1,0 del corte más cercano" in frase, frase
        assert "a 9,0 del corte más cercano" not in frase, (
            "publicó la distancia al borde lejano (desde) en vez del cercano (hasta)")

    def test_sigue_tomando_desde_cuando_es_el_mas_cercano(self):
        # Mismo tramo, valor 11: ahora el más cercano es `desde` (distancia 1).
        tramo = [{"color": "amarillo", "desde": 10.0, "hasta": 20.0}]
        frase = publicar._por_que("amarillo", 11.0, "%", tramo)
        assert "a 1,0 del corte más cercano" in frase, frase

    def test_borde_abierto_usa_el_unico_borde_finito(self):
        # `desde=None` (tramo abierto por abajo): no hay dos distancias para
        # comparar, tiene que seguir usando el único borde finito (`hasta`).
        tramo = [{"color": "verde", "desde": None, "hasta": 6.0}]
        frase = publicar._por_que("verde", 5.0, "%", tramo)
        assert "a 1,0 del corte más cercano" in frase, frase


class TestCortesExpuestos:
    """A3 (revisión de coherencia UI, ago-2026): la leyenda web arma su texto
    ("tensión ≤ 4") leyendo `informe.semaforo_cortes`, no escribiendo los
    números a mano. Este test ata lo publicado a CORTES_SEMAFORO -- si
    alguien cambia el motor sin tocar `_semaforos`, o serializa mal el
    infinito de "rojo", se desincroniza en silencio sin esto."""

    def test_semaforo_cortes_espeja_cortes_semaforo(self, informe):
        esperado = [
            {"color": color, "hasta": None if tope == parametrica.INF else tope}
            for color, tope in parametrica.CORTES_SEMAFORO
        ]
        assert informe["semaforo_cortes"] == esperado


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
