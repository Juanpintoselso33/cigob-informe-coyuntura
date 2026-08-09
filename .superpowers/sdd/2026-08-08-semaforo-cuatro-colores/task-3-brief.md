### Task 3: Publicar el semáforo en el snapshot

**Files:**
- Modify: `scripts/publicar.py` (agregar `_semaforos(informe)` y llamarla al final de `aplicar_scoring`, que arranca en la línea 1708)
- Test: `tests/test_publicar_semaforo.py` (crear)

**Interfaces:**
- Consumes: `parametrica.color_de_puntaje`, `parametrica.color_de_indice_base100`, `parametrica.umbrales_en_unidad`, `parametrica.Escala`.
- Produces: en cada indicador, dimensión e índice del snapshot, la clave `semaforo` con `{color, tension, umbrales, unidad, por_que}`. `umbrales` y `unidad` son `None` donde no hay escala puntuable.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_publicar_semaforo.py`:

```python
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
        caer en un tramo del color que se publicó."""
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
```

- [ ] **Step 2: Capturar los índices previos al cambio**

Antes de tocar `publicar.py`, congelar los números que el semáforo no puede mover:

```bash
python -c "
import json, pathlib
d = json.load(open('web/src/data/informe.json', encoding='utf-8'))
c = d['cinturones']
out = {'indices': [[cint, clave, c[cint][clave]['valor']]
                   for cint, clave in [('macro','itcm'), ('gestion','itcg'),
                                       ('politica','itcp'), ('vida_cotidiana','itvc')]],
       'score_global': d['score_global']}
pathlib.Path('tests/fixtures/indices_previos_semaforo.json').write_text(
    json.dumps(out, indent=2), encoding='utf-8')
print(out)
"
```

Expected: imprime los cuatro índices y el score global, y crea el fixture.

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_publicar_semaforo.py -v`
Expected: FAIL — `test_todo_indicador_con_tension_tiene_color` lista los 66 indicadores sin `semaforo`.

- [ ] **Step 4: Implementar en `publicar.py`**

**Primero el import que falta.** `publicar.py` importa `itcm`, `itcg`, `itcp`,
`itvc` y `sensibilidad`, pero **no** `parametrica`. Agregarlo junto a los otros,
alrededor de la línea 33:

```python
import parametrica                                    # motor de puntaje y semáforo
```

Después, cerca de las otras funciones de scoring, y llamarla desde el final de `aplicar_scoring`:

```python
# ── Semáforo de 4 colores (ADR-0181) ──────────────────────────────────────────
# Capa de LECTURA: no toca ningún puntaje, peso ni índice. El color sale de la
# tensión sin redondear — `aporte_score` está redondeado y usarlo rompe el borde.
_ESCALAS_SEMAFORO = {
    "macro": ("itcm", itcm, "ITCM"),
    "gestion": ("itcg", itcg, "ITCG"),
    "politica": ("itcp", itcp, "ITCP"),
}


def _escala_de(mod, sigla):
    return parametrica.Escala(
        getattr(mod, f"BANDAS_{sigla}"),
        getattr(mod, f"ANCLAS_{sigla}", None),
        getattr(mod, f"TRANSFORMACIONES_{sigla}", None),
    )


def _por_que(color, valor, unidad, tramos):
    """Una frase que explica el color con la misma aritmética que lo produjo.

    Se genera y no se escribe: es lo que evita que la prosa de la ficha se
    desincronice del dato (ADR-0182).
    """
    if valor is None or not tramos:
        return None
    actual = next((t for t in tramos
                   if (t["desde"] is None or valor > t["desde"])
                   and (t["hasta"] is None or valor <= t["hasta"])), None)
    if actual is None:
        return None
    borde = actual["desde"] if actual["desde"] is not None else actual["hasta"]
    if borde is None:
        return f"{coma(valor)} {unidad}: {color.capitalize()} en todo el rango."
    return (f"{coma(valor)} {unidad} cae en el tramo que corresponde a "
            f"{color.capitalize()}, a {coma(round(abs(valor - borde), 2))} "
            f"del corte más cercano.")


def _semaforo_de(color, tension, umbrales, unidad, valor):
    return {"color": color,
            "tension": None if tension is None else round(tension, 1),
            "umbrales": umbrales,
            "unidad": unidad,
            "por_que": _por_que(color, valor, unidad, umbrales)}


def _semaforos(informe):
    """Adjunta el bloque `semaforo` a cada indicador, dimensión e índice."""
    for cinturon, bloque in informe["cinturones"].items():
        clave, mod, sigla = _ESCALAS_SEMAFORO.get(cinturon, (None, None, None))
        escala = _escala_de(mod, sigla) if mod else None

        for ikey, ind in bloque["indicadores"].items():
            idx100 = ind.get("indice_itvc")
            p = ind.get(f"puntaje_{clave}") if clave else None
            if isinstance(p, (int, float)) and ind.get("en_indice"):
                tension = (100.0 - float(p)) / 10.0
                color = parametrica.color_de_tension(tension)
                umbrales = parametrica.umbrales_en_unidad(ikey, escala)
                unidad = ind.get("unidad")
            elif isinstance(idx100, (int, float)):
                tension = 5.0 - (float(idx100) - 100.0) * 0.2
                color = parametrica.color_de_tension(tension)
                umbrales, unidad = None, None
            elif ind.get("aporte_score") is not None:
                tension = float(ind["aporte_score"])
                color = parametrica.color_de_tension(tension)
                umbrales, unidad = None, None
            else:
                continue
            ind["semaforo"] = _semaforo_de(color, tension, umbrales, unidad,
                                           ind.get("valor"))

        indice = bloque.get(clave) if clave else bloque.get("itvc")
        if not indice:
            continue
        base100 = "itvc" in bloque and indice is bloque.get("itvc")
        color_idx = (parametrica.color_de_indice_base100 if base100
                     else parametrica.color_de_puntaje)
        indice["semaforo"] = {"color": color_idx(indice["valor"]),
                              "umbrales": None, "unidad": None, "por_que": None,
                              "tension": None}
        for dim in indice.get("dimensiones", {}).values():
            dim["semaforo"] = {"color": color_idx(dim["puntaje"]),
                               "umbrales": None, "unidad": None,
                               "por_que": None, "tension": None}
```

Y al final de `aplicar_scoring(informe, series)`, antes del `return`:

```python
    _semaforos(informe)
```

**Cuidado con el orden:** `_semaforos` tiene que correr **después** de que
`_scoring_vida_itvc` haya escrito `indice_itvc` en los indicadores de vida
cotidiana. Si `aplicar_scoring` no es el último lugar donde eso pasa, moverla
al final de `main()`.

- [ ] **Step 5: Regenerar el snapshot y correr los tests**

```bash
python scripts/generar_informe.py
python scripts/publicar.py
python -m pytest tests/test_publicar_semaforo.py -v
```

Expected: PASS. Si `test_los_indices_siguen_donde_estaban` falla, el cambio movió un número y hay que averiguar por qué antes de seguir.

- [ ] **Step 6: Correr la suite completa**

Run: `python -m pytest tests -q`
Expected: PASS. Es la puerta separada del gate; ninguna de las dos sustituye a la otra.

- [ ] **Step 7: Commit**

```bash
git add scripts/publicar.py tests/test_publicar_semaforo.py tests/fixtures/indices_previos_semaforo.json
git commit -m "feat(semaforo): el snapshot publica color, umbrales y por que"
```

---

