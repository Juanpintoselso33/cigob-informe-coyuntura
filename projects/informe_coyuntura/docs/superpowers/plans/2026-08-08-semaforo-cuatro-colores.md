# Capa de semáforo de 4 colores — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar un color de 4 niveles (verde/amarillo/naranja/rojo) por indicador, dimensión e índice en los cinco cinturones, y mostrar en la ficha pública los umbrales que determinan ese color expresados en la unidad real del indicador — sin mover ningún puntaje, peso ni índice.

**Architecture:** Tres capas con una responsabilidad cada una. `parametrica.py` calcula (color desde la tensión sin redondear; umbrales por interpolación inversa de las anclas). `publicar.py` publica el resultado en `informe.json`. La web **lee** el color publicado y no recalcula nada. Hoy el color se calcula en el cliente (`datos.ts`) con 3 niveles y dos varas distintas según la escala del índice; este trabajo lo unifica y lo mueve a Python.

**Tech Stack:** Python 3 (sin dependencias nuevas), pytest, Astro + TypeScript, CSS plano en `web/public/dashboard.css`.

**Spec:** `docs/superpowers/specs/2026-08-08-semaforo-cuatro-colores-design.md`

## Global Constraints

- **Directorio de trabajo:** todos los comandos se corren desde `projects/informe_coyuntura/`.
- **Prosa en castellano.** Comentarios, docstrings y texto de la web en castellano, como el resto del repo.
- **No se toca ninguna tabla de bandas ni ningún peso.** `itcg.py`, `itcm.py`, `itcp.py`, `itvc.py` no cambian. Si el diff toca `BANDAS_*` o `DIMENSIONES_*`, algo se salió del alcance.
- **Los cortes viven en un solo lugar:** `CORTES_SEMAFORO` en `parametrica.py`. Ningún otro archivo, Python o TypeScript, puede tener los números 4/6/8, 60/40/20 ni 105/95/85 escritos.
- **El color se calcula sobre la tensión SIN redondear.** `aporte_score` está redondeado a un decimal y usarlo como insumo rompe el borde: puntaje 59,9 → tensión 4,01 → redondeada 4,0 → verde, cuando corresponde amarillo.
- **Nunca `git add -A` ni `git add .`** en este repo (OneDrive restaura snapshots viejos encima de los buenos). Cada commit stagea archivos explícitos.
- **Tests con el pool limitado** si se corre algo en paralelo; `pytest` de este repo es secuencial y no necesita flags.
- **Convención de bordes del motor:** low exclusivo, high inclusivo. El semáforo la respeta: puntaje 60,0 es verde, 59,9 es amarillo.
- **Dos conceptos de color conviven, y acá no se unifican.** `verdictDeCinturon(estado)` pinta el chip del cinturón desde su `estado` editorial (`estable` / `en_tension` / `tensionado`, los tres únicos valores que emite `_estado()`) y **sigue con 3 colores**: ese enum alimenta el BLUF, el panel de tensión y `cinturonesRojos`, así que cambiarlo sería un cambio de índice y no de presentación — justamente lo que §4.4 de la spec prohíbe. (`score_global` no es parte de esa cadena: es un promedio ponderado de los *scores* 0-10 de cada cinturón, y `estado` se deriva por separado de ese mismo score vía `_estado()` — son dos lecturas del mismo número, no una alimenta a la otra.) El semáforo nuevo pinta indicadores, dimensiones e índices desde la tensión, con 4 colores. `.cg-verdict` es la clase de chip compartida —está indexada por nombre de color, no por qué concepto lo produjo— y se le agrega `naranja`. Unificar el chip del cinturón con el color de su índice queda como pendiente declarado, no como olvido.

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/parametrica.py` | Motor: `CORTES_SEMAFORO`, `color_de_tension`, `color_de_puntaje`, `color_de_indice_base100`, `umbrales_en_unidad` | Modificar |
| `scripts/publicar.py` | Adjuntar el bloque `semaforo` a cada indicador, dimensión e índice del snapshot | Modificar |
| `tests/test_semaforo.py` | Tests del motor (cortes, reversibilidad, no monotonía, transformaciones, dedup) | Crear |
| `tests/test_publicar_semaforo.py` | Tests del snapshot (cobertura, coherencia, invariancia de los índices) | Crear |
| `web/public/dashboard.css` | Tokens `--naranja` / `--naranja-soft` y reglas `.sem-naranja` / `.cg-verdict.naranja` | Modificar |
| `web/src/lib/datos.ts` | `semaforoDe()` leyendo el color publicado; retiro del cálculo en cliente | Modificar |
| `web/src/components/CinturonCard.astro` | Genoma con 4 tramos | Modificar |
| `web/src/components/IndicadorTile.astro` | Punto de color en la card | Modificar |
| `web/src/pages/metodologia/[id].astro` | Tres secciones nuevas de la ficha | Modificar |
| `tests/test_web_semaforo.py` | Que los 4 colores tengan token CSS y que no queden cortes hardcodeados en TS | Crear |
| `docs/adr/0181-…`, `0182-…`, `0183-…` | Decisiones | Crear |

El motor va en `parametrica.py` y no en un archivo nuevo porque ahí ya viven `puntaje_desde_anclas`, `_anclas` y `Escala` — el semáforo es la inversa de lo que ese archivo ya hace, y separarlo obligaría a exportar internos.

---

### Task 1: Cortes y color en `parametrica.py`

La pieza más chica que se puede testear sola: dado un número de tensión, qué color es.

**Files:**
- Modify: `scripts/parametrica.py` (agregar al final, después de `tension_de_indice`)
- Test: `tests/test_semaforo.py` (crear)

**Interfaces:**
- Consumes: nada.
- Produces: `CORTES_SEMAFORO: tuple[tuple[str, float], ...]` · `color_de_tension(tension: float) -> str` · `color_de_puntaje(puntaje: float) -> str` · `color_de_indice_base100(indice: float) -> str`. Todas devuelven uno de `"verde" | "amarillo" | "naranja" | "rojo"`.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_semaforo.py`:

```python
"""Capa de semáforo: color por tensión y umbrales en unidad propia (ADR-0181, ADR-0182)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import parametrica


class TestColorDeTension:
    def test_los_cuatro_colores(self):
        assert parametrica.color_de_tension(0.0) == "verde"
        assert parametrica.color_de_tension(5.0) == "amarillo"
        assert parametrica.color_de_tension(7.0) == "naranja"
        assert parametrica.color_de_tension(9.5) == "rojo"

    def test_los_bordes_son_inclusivos_hacia_el_mejor_color(self):
        # low exclusivo / high inclusivo, la convención del motor
        assert parametrica.color_de_tension(4.0) == "verde"
        assert parametrica.color_de_tension(4.01) == "amarillo"
        assert parametrica.color_de_tension(6.0) == "amarillo"
        assert parametrica.color_de_tension(6.01) == "naranja"
        assert parametrica.color_de_tension(8.0) == "naranja"
        assert parametrica.color_de_tension(8.01) == "rojo"

    def test_puntaje_0_100_usa_los_bordes_de_las_bandas_de_interpretacion(self):
        assert parametrica.color_de_puntaje(60.0) == "verde"
        assert parametrica.color_de_puntaje(40.0) == "amarillo"
        assert parametrica.color_de_puntaje(20.0) == "naranja"
        assert parametrica.color_de_puntaje(19.9) == "rojo"

    def test_no_usa_la_tension_redondeada(self):
        # 59,9 da tensión 4,01; redondeada a un decimal es 4,0 y daría verde.
        # Es el error que rompe el borde, y este test es el que lo ataja.
        assert parametrica.color_de_puntaje(59.9) == "amarillo"

    def test_base100_despeja_su_propia_formula_de_tension(self):
        # tensión = 5 − (índice − 100) × 0,2  →  t≤4 ⟺ i≥105, t≤6 ⟺ i≥95, t≤8 ⟺ i≥85
        assert parametrica.color_de_indice_base100(105.0) == "verde"
        assert parametrica.color_de_indice_base100(104.9) == "amarillo"
        assert parametrica.color_de_indice_base100(95.0) == "amarillo"
        assert parametrica.color_de_indice_base100(94.9) == "naranja"
        assert parametrica.color_de_indice_base100(85.0) == "naranja"
        assert parametrica.color_de_indice_base100(84.9) == "rojo"
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `python -m pytest tests/test_semaforo.py -v`
Expected: FAIL — `AttributeError: module 'parametrica' has no attribute 'color_de_tension'`

- [ ] **Step 3: Implementar**

En `scripts/parametrica.py`, después de `tension_de_indice`:

```python
# ── Semáforo de 4 colores (ADR-0181) ──────────────────────────────────────────
# El color NO es una escala nueva: es la tensión 0-10 que el informe ya publica,
# partida en cuatro tramos. Para los índices 0-100 eso da los cortes 60/40/20,
# que son los bordes de BANDAS_INTERPRETACION; para el ITVC base-100 sale de
# despejar su propia fórmula (tensión = 5 − (índice−100) × 0,2).
#
# El color se calcula SIEMPRE sobre la tensión sin redondear. `aporte_score` en
# el snapshot está redondeado a un decimal y usarlo acá rompe el borde: puntaje
# 59,9 da tensión 4,01, que redondeada es 4,0 y saldría verde.
CORTES_SEMAFORO = (("verde", 4.0), ("amarillo", 6.0), ("naranja", 8.0), ("rojo", INF))


def color_de_tension(tension: float) -> str:
    """Color del semáforo para una tensión 0-10 (sin redondear)."""
    for color, tope in CORTES_SEMAFORO:
        if tension <= tope:
            return color
    return CORTES_SEMAFORO[-1][0]


def color_de_puntaje(puntaje: float) -> str:
    """Color de un puntaje 0-100 (ITCM/ITCG/ITCP), vía su tensión equivalente."""
    return color_de_tension((100.0 - float(puntaje)) / 10.0)


def color_de_indice_base100(indice: float) -> str:
    """Color de un índice base-100 (ITVC), vía su fórmula de tensión publicada."""
    return color_de_tension(5.0 - (float(indice) - 100.0) * 0.2)
```

- [ ] **Step 4: Correr los tests**

Run: `python -m pytest tests/test_semaforo.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add scripts/parametrica.py tests/test_semaforo.py
git commit -m "feat(semaforo): el color es la tension publicada, en cuatro tramos"
```

---

### Task 2: Umbrales en la unidad propia del indicador

Interpolación inversa: dado un indicador y su escala, en qué valores crudos cambia de color.

**Files:**
- Modify: `scripts/parametrica.py`
- Test: `tests/test_semaforo.py`

**Interfaces:**
- Consumes: `CORTES_SEMAFORO`, `_anclas`, `Escala` (ya existe, con `.bandas`, `.anclas`, `.transformaciones`).
- Produces: `umbrales_en_unidad(indicador: str, escala: Escala) -> list[dict] | None`. Cada dict es `{"color": str, "desde": float | None, "hasta": float | None}`, ordenado por `desde` ascendente con `None` primero. Devuelve `None` si el indicador no tiene anclas ni bandas.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_semaforo.py`:

```python
import itcg
import itcm
import itcp

ESCALA_ITCG = parametrica.Escala(
    itcg.BANDAS_ITCG,
    getattr(itcg, "ANCLAS_ITCG", None),
    getattr(itcg, "TRANSFORMACIONES_ITCG", None),
)
ESCALA_ITCM = parametrica.Escala(
    itcm.BANDAS_ITCM,
    getattr(itcm, "ANCLAS_ITCM", None),
    getattr(itcm, "TRANSFORMACIONES_ITCM", None),
)
ESCALA_ITCP = parametrica.Escala(
    itcp.BANDAS_ITCP,
    getattr(itcp, "ANCLAS_ITCP", None),
    getattr(itcp, "TRANSFORMACIONES_ITCP", None),
)
ESCALAS = {"ITCG": ESCALA_ITCG, "ITCM": ESCALA_ITCM, "ITCP": ESCALA_ITCP}


def _tramos(indicador, escala, color):
    return [t for t in parametrica.umbrales_en_unidad(indicador, escala)
            if t["color"] == color]


class TestUmbralesEnUnidad:
    def test_indicador_creciente_apertura_comercial(self):
        # apertura: menor alícuota = mejor. Verde es un "≤".
        verde = _tramos("apertura_comercial", ESCALA_ITCG, "verde")
        assert len(verde) == 1
        assert verde[0]["desde"] is None
        assert verde[0]["hasta"] == pytest.approx(6.0, abs=0.01)

    def test_indicador_decreciente_desregulacion(self):
        # desregulación: más artículos = mejor. Verde es un "≥".
        verde = _tramos("desregulacion_normativa", ESCALA_ITCG, "verde")
        assert len(verde) == 1
        assert verde[0]["desde"] == pytest.approx(11000.0, abs=1.0)
        assert verde[0]["hasta"] is None

    def test_reversibilidad_en_las_57_tablas(self):
        # El test que detecta un error de interpolación inversa sin pinear
        # ningún valor: puntuar el umbral tiene que devolver el corte.
        cortes = {"verde": 60.0, "amarillo": 40.0, "naranja": 20.0}
        revisados = 0
        for sigla, escala in ESCALAS.items():
            for indicador in escala.bandas:
                tramos = parametrica.umbrales_en_unidad(indicador, escala)
                assert tramos, f"{sigla}/{indicador} sin umbrales"
                for tramo in tramos:
                    corte = cortes.get(tramo["color"])
                    if corte is None:
                        continue
                    for borde in (tramo["desde"], tramo["hasta"]):
                        if borde is None:
                            continue
                        p = escala.puntaje(borde, indicador)
                        assert p == pytest.approx(corte, abs=0.2), (
                            f"{sigla}/{indicador}: puntaje({borde}) = {p}, esperado {corte}")
                        revisados += 1
        assert revisados > 100

    def test_no_monotono_costo_financiamiento_tesoro(self):
        # Anclas (−5,20) (−2,5,55) (3,100) (9,75) (16,45) (20,15): óptimo en el
        # medio. Verde es un INTERVALO CERRADO y los partidos en dos son
        # amarillo y naranja. Por izquierda nunca hay rojo: el puntaje satura
        # en 20 y se queda en naranja.
        tramos = parametrica.umbrales_en_unidad("costo_financiamiento_tesoro", ESCALA_ITCM)
        verde = [t for t in tramos if t["color"] == "verde"]
        assert len(verde) == 1
        assert verde[0]["desde"] == pytest.approx(-1.89, abs=0.02)
        assert verde[0]["hasta"] == pytest.approx(12.52, abs=0.02)
        assert len([t for t in tramos if t["color"] == "amarillo"]) == 2
        assert len([t for t in tramos if t["color"] == "naranja"]) == 2
        assert len([t for t in tramos if t["color"] == "rojo"]) == 1

    def test_transformacion_devuelve_unidad_cruda(self):
        # rem_ipc_12m se publica como expectativa ANUAL y se puntúa por su
        # equivalente MENSUAL. El umbral tiene que salir en anual, que es lo
        # que muestra la card.
        tramos = parametrica.umbrales_en_unidad("rem_ipc_12m", ESCALA_ITCM)
        bordes = [b for t in tramos for b in (t["desde"], t["hasta"]) if b is not None]
        assert max(bordes) > 5.0, f"parecen equivalentes mensuales, no anuales: {bordes}"

    def test_sin_bandas_devuelve_none(self):
        assert parametrica.umbrales_en_unidad("no_existe", ESCALA_ITCG) is None

    def test_sin_tramos_duplicados(self):
        # Cuando un corte cae en un ancla exacta, dos segmentos lo reportan.
        for escala in ESCALAS.values():
            for indicador in escala.bandas:
                tramos = parametrica.umbrales_en_unidad(indicador, escala)
                vistos = [(t["color"], t["desde"], t["hasta"]) for t in tramos]
                assert len(vistos) == len(set(vistos)), f"{indicador}: tramos repetidos"
```

Agregar `import pytest` arriba del archivo.

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `python -m pytest tests/test_semaforo.py -v -k Umbrales`
Expected: FAIL — `AttributeError: module 'parametrica' has no attribute 'umbrales_en_unidad'`

- [ ] **Step 3: Implementar**

En `scripts/parametrica.py`, después de `color_de_indice_base100`:

```python
def _cruces(anclas: list, corte: float) -> list:
    """Valores donde el puntaje interpolado cruza `corte`.

    Son varios cuando la escala no es monótona: costo_financiamiento_tesoro
    (ITCM) tiene el óptimo en el medio y cada corte lo cruza dos veces.
    """
    out = []
    for (x0, p0), (x1, p1) in zip(anclas, anclas[1:]):
        if p0 == p1:
            continue
        if min(p0, p1) <= corte <= max(p0, p1):
            out.append(x0 + (x1 - x0) * (corte - p0) / (p1 - p0))
    return out


def umbrales_en_unidad(indicador: str, escala: "Escala") -> list | None:
    """Tramos de color del indicador, EN LAS UNIDADES DEL VALOR CRUDO.

    Interpola las anclas hacia atrás en los puntajes de corte y devuelve
    [{color, desde, hasta}] ordenado, con None en los extremos abiertos.
    None si el indicador no tiene escala puntuable.

    Se calcula y no se escribe (ADR-0182): un umbral en prosa envejece con el
    dato — las fichas de agosto de 2026 quedaron desactualizadas en una semana.
    """
    if indicador in escala.anclas:
        anclas = sorted((float(x), float(p)) for x, p in escala.anclas[indicador])
    elif indicador in escala.bandas:
        anclas = _anclas(escala.bandas[indicador])
    else:
        return None
    if len(anclas) < 2:
        return None

    # Los puntos donde puede cambiar el color: los cruces de los tres cortes.
    cortes = [(color_de_puntaje(p + 0.001), p)
              for p in (60.0, 40.0, 20.0)]
    quiebres = sorted({round(x, 6)
                       for _, p in cortes
                       for x in _cruces(anclas, p)})

    # Fuera del rango de anclas el puntaje es plano, así que el color del
    # primer y del último tramo se evalúa en los bordes.
    limites = [None] + quiebres + [None]
    tramos = []
    for desde, hasta in zip(limites, limites[1:]):
        if desde is None and hasta is None:
            medio = anclas[0][0]
        elif desde is None:
            medio = hasta - 1.0
        elif hasta is None:
            medio = desde + 1.0
        else:
            medio = (desde + hasta) / 2.0
        color = color_de_puntaje(puntaje_desde_anclas(medio, anclas))
        if tramos and tramos[-1]["color"] == color:
            tramos[-1]["hasta"] = hasta        # fusiona tramos contiguos del mismo color
            continue
        tramos.append({"color": color,
                       "desde": None if desde is None else round(desde, 4),
                       "hasta": None if hasta is None else round(hasta, 4)})

    # Aplicar la inversa declarada: las anclas de algunos indicadores están en
    # unidades de la banda, no del valor crudo (mismo caso que span_crudo).
    t = escala.transformaciones.get(indicador)
    if isinstance(t, tuple):
        inversa = t[1]
        for tramo in tramos:
            for k in ("desde", "hasta"):
                if tramo[k] is not None:
                    tramo[k] = round(float(inversa(tramo[k])), 4)
        if any(tramo["desde"] is not None and tramo["hasta"] is not None
               and tramo["desde"] > tramo["hasta"] for tramo in tramos):
            for tramo in tramos:                # la inversa puede invertir el orden
                tramo["desde"], tramo["hasta"] = tramo["hasta"], tramo["desde"]
            tramos.reverse()
    return tramos
```

**Nota para quien implemente:** el `cortes` de arriba se usa solo para enumerar los puntajes de corte; el color de cada tramo se decide evaluando el puntaje en un punto interior, que es lo que hace correcto el caso no monótono. Si al correr los tests un tramo sale con el color equivocado, el problema está en la elección del punto interior (`medio`), no en `_cruces`.

- [ ] **Step 4: Correr los tests**

Run: `python -m pytest tests/test_semaforo.py -v`
Expected: PASS, 12 tests.

- [ ] **Step 5: Verificar a mano la tabla del ITCG contra la spec**

Run:

```bash
python -c "
import sys; sys.path.insert(0,'scripts')
import parametrica, itcg
e = parametrica.Escala(itcg.BANDAS_ITCG)
for k in itcg.BANDAS_ITCG:
    print(k, parametrica.umbrales_en_unidad(k, e))
"
```

Expected: los pisos de verde coinciden con la tabla de §4.1 de la spec — cepo ≤14, apertura ≤6, desregulación ≥11.000, dotación ≤−5,2, gasto ≤−8,5, masa salarial ≤−7,3, reestructuración ≥46, FAL ≥55, litigiosidad ≤2,5, privatizaciones ≥41, RIGI ≥29,5, concesiones ≥41, asistencia directa ≥67, orden público ≥32,5, libertad salud ≥36.

- [ ] **Step 6: Commit**

```bash
git add scripts/parametrica.py tests/test_semaforo.py
git commit -m "feat(semaforo): umbrales en unidad propia por interpolacion inversa"
```

---

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

### Task 4: Los cuatro colores en el CSS

**Files:**
- Modify: `web/public/dashboard.css` (tokens en `:root` ~línea 27; `.cg-genoma-seg.sem-*` ~línea 373; `.cg-verdict.*` ~línea 339)
- Test: `tests/test_web_semaforo.py` (crear)

**Interfaces:**
- Consumes: nada.
- Produces: variables CSS `--naranja` y `--naranja-soft`; reglas `.cg-genoma-seg.sem-naranja` y `.cg-verdict.naranja`.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_web_semaforo.py`:

```python
"""Los cuatro colores del semáforo existen en el CSS y no hay cortes duplicados en TS."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSS = RAIZ / "web" / "public" / "dashboard.css"
LIB = RAIZ / "web" / "src" / "lib"

COLORES = ("verde", "amarillo", "naranja", "rojo")


class TestTokensCss:
    def test_los_cuatro_colores_tienen_token_y_variante_soft(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert re.search(rf"--{color}:\s*#", css), f"falta el token --{color}"
            assert re.search(rf"--{color}-soft:\s*#", css), f"falta --{color}-soft"

    def test_los_cuatro_colores_pintan_genoma_y_verdict(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert f".cg-genoma-seg.sem-{color}" in css, f"falta .sem-{color}"
            assert f".cg-verdict.{color}" in css, f"falta .cg-verdict.{color}"
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `python -m pytest tests/test_web_semaforo.py -v`
Expected: FAIL — falta el token `--naranja`.

- [ ] **Step 3: Implementar**

En `web/public/dashboard.css`, junto a los otros tokens del semáforo:

```css
    --naranja:      #EA580C;
    --naranja-soft: #FFEDD5;
```

Junto a `.cg-genoma-seg.sem-amarillo`:

```css
.cg-genoma-seg.sem-naranja  { background: var(--naranja); }
```

Junto a `.cg-verdict.amarillo`:

```css
.cg-verdict.naranja  { background: var(--naranja-soft); color: #7C2D12; border-color: #FED7AA; }
```

`#EA580C` se distingue de `--amarillo #CA8A04` a tamaño de punto y mantiene el registro de la paleta; `#7C2D12` sobre `#FFEDD5` da contraste holgado, igual que los tres pares existentes.

- [ ] **Step 4: Correr el test**

Run: `python -m pytest tests/test_web_semaforo.py -v`
Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
git add web/public/dashboard.css tests/test_web_semaforo.py
git commit -m "feat(semaforo): token naranja y sus reglas en el CSS del tablero"
```

---

### Task 5: La web lee el color en vez de calcularlo

**Files:**
- Modify: `web/src/lib/datos.ts:175-182` (`semaforoDimension`)
- Modify: `web/src/components/CinturonCard.astro:45`
- Modify: `web/src/components/IndicadorTile.astro`
- Test: `tests/test_web_semaforo.py` (agregar)

**Interfaces:**
- Consumes: el campo `semaforo.color` que publica la Task 3.
- Produces: `semaforoDe(x: { semaforo?: { color: string } }): "verde" | "amarillo" | "naranja" | "rojo"` exportada desde `datos.ts`.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_web_semaforo.py`:

```python
class TestSinCortesDuplicadosEnTs:
    def test_datos_ts_no_recalcula_el_semaforo(self):
        """Los cortes viven solo en parametrica.py. Si el cliente los repite,
        se desincronizan sin que falle nada."""
        ts = (LIB / "datos.ts").read_text(encoding="utf-8")
        assert "semaforoDimension" not in ts, (
            "semaforoDimension calculaba el color en el cliente; "
            "tiene que leer el color publicado")
        assert "semaforoDe" in ts, "falta el lector semaforoDe"

    def test_ningun_corte_del_semaforo_hardcodeado_en_ts(self):
        prohibidos = (">= 95", ">= 90", ">= 105", ">= 85")
        for archivo in LIB.glob("*.ts"):
            texto = archivo.read_text(encoding="utf-8")
            for patron in prohibidos:
                assert patron not in texto, f"{archivo.name}: corte hardcodeado {patron}"
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `python -m pytest tests/test_web_semaforo.py -v -k Ts`
Expected: FAIL — `semaforoDimension` sigue en `datos.ts`.

- [ ] **Step 3: Implementar en `datos.ts`**

Reemplazar el bloque `semaforoDimension` (líneas 175-182) por:

```ts
export type ColorSemaforo = "verde" | "amarillo" | "naranja" | "rojo";

// El color LO CALCULA parametrica.py y viaja en el snapshot (ADR-0181). Acá
// solo se lee: si el cliente lo recalculara, habría dos definiciones del corte
// y se desincronizarían sin que falle nada. Hasta agosto de 2026 esta función
// calculaba 3 colores en el cliente, con una vara distinta para el ITVC
// base-100 (verde a tensión 6) que para los índices 0-100 (verde a tensión 4).
export function semaforoDe(x: { semaforo?: { color?: string } } | null | undefined): ColorSemaforo {
  const c = x?.semaforo?.color;
  return c === "verde" || c === "amarillo" || c === "naranja" || c === "rojo"
    ? c
    : "amarillo";
}
```

Buscar los usos de `semaforoDimension` y `tensionDeDimension` en el resto del
repo antes de borrar, con `grep -rn "semaforoDimension" web/src/`.
`tensionDeDimension` y `peorDimension` **se conservan**: comparan tensión entre
índices de escala distinta y no son parte del semáforo.

- [ ] **Step 4: Implementar en los componentes**

En `CinturonCard.astro`, la línea 45 pasa de calcular a leer:

```astro
class:list={["cg-genoma-seg", `sem-${semaforoDe(dim)}`, "cg-dim--clickable", { "is-critica": dim.critica }]}
```

y el import de la línea 2 cambia `semaforoDimension` por `semaforoDe`.

En `IndicadorTile.astro`, agregar el import y un punto de color en el head de la card:

```astro
---
import { presentacion, label, visualDe, badgeEstado, periodoDato, series, formatValor, semaforoDe } from "../lib/datos.ts";
...
const color = semaforoDe(ind);
---
  <div class="cg-tile-head">
    <span class:list={["cg-tile-dot", `sem-${color}`]} title={ind.semaforo?.por_que ?? undefined} aria-hidden="true"></span>
    <span class="cg-tile-name">{label(ikey)}</span>
    <span class:list={["cg-tile-badge", badgeCls]} title={chipTitle}>{chip}</span>
  </div>
```

y en `dashboard.css`, junto a las otras reglas `.sem-*`:

```css
.cg-tile-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 8px; }
.cg-tile-dot.sem-verde    { background: var(--verde); }
.cg-tile-dot.sem-amarillo { background: var(--amarillo); }
.cg-tile-dot.sem-naranja  { background: var(--naranja); }
.cg-tile-dot.sem-rojo     { background: var(--rojo); }
```

El punto lleva `aria-hidden` y el color no es el único portador de la
información: el número y el texto del `por_que` siguen ahí.

- [ ] **Step 5: Compilar y correr los tests**

```bash
cd web && npx tsc --noEmit && npm run build && cd ..
python -m pytest tests/test_web_semaforo.py -v
```

Expected: build limpio y 4 tests en verde.

- [ ] **Step 6: Commit**

```bash
git add web/src/lib/datos.ts web/src/components/CinturonCard.astro web/src/components/IndicadorTile.astro web/public/dashboard.css tests/test_web_semaforo.py
git commit -m "feat(semaforo): la web lee el color publicado en vez de recalcularlo"
```

---

### Task 6: Las tres secciones nuevas de la ficha

**Files:**
- Modify: `web/src/pages/metodologia/[id].astro`
- Test: verificación visual (esta tarea no agrega tests automáticos; lo que se puede testear ya está cubierto por las Tasks 3 y 5)

**Interfaces:**
- Consumes: `ind.semaforo` (`color`, `umbrales`, `unidad`, `por_que`) y `ind.detalle_txt`, ambos del snapshot.
- Produces: nada que otra tarea consuma.

- [ ] **Step 1: Leer la página y ubicar dónde insertar**

Run: `grep -n "anclas\|Anclas\|section\|<h2" web/src/pages/metodologia/\[id\].astro | head -40`

Las tres secciones nuevas van **después** del bloque de anclas —que explica el
puntaje— y antes de "limitaciones". El orden importa: primero cómo se puntúa,
después de qué color queda, después qué hay detrás del dato, y al final qué no
se puede afirmar.

- [ ] **Step 2: Sección "Semáforo — valores que determinan el color"**

```astro
{ind?.semaforo?.umbrales && (
  <section class="cg-ficha-sec">
    <h2>Semáforo — valores que determinan el color</h2>
    <p>
      Estos son los valores concretos, en la unidad propia de este indicador,
      que hacen que el semáforo esté en verde, amarillo, naranja o rojo.
    </p>
    <table class="cg-ficha-tabla">
      <thead>
        <tr><th>Rango ({ind.semaforo.unidad})</th><th>Color</th></tr>
      </thead>
      <tbody>
        {ind.semaforo.umbrales.map((t: any) => (
          <tr>
            <td>{rangoLegible(t)}</td>
            <td class:list={["cg-verdict", t.color]}>{t.color.toUpperCase()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
)}
```

con este helper en el frontmatter de la página:

```ts
// Un tramo con desde/hasta en null es extremo abierto. Un color puede
// aparecer más de una vez: el indicador de costo de financiamiento del Tesoro
// tiene el óptimo en el medio, así que amarillo y naranja quedan partidos en
// dos tramos, uno a cada lado.
function rangoLegible(t: { desde: number | null; hasta: number | null }): string {
  const n = (x: number) => String(x).replace(".", ",");
  if (t.desde === null && t.hasta === null) return "todo el rango";
  if (t.desde === null) return `≤ ${n(t.hasta!)}`;
  if (t.hasta === null) return `≥ ${n(t.desde)}`;
  return `${n(t.desde)} – ${n(t.hasta)}`;
}
```

- [ ] **Step 3: Sección "Datos concretos detrás del valor"**

Es el hallazgo §1.1(c) de la spec: **el dato ya existe**, solo estaba escondido
en el modal. No hay que producir nada nuevo.

```astro
{ind?.detalle_txt && (
  <section class="cg-ficha-sec">
    <h2>Datos concretos detrás del valor</h2>
    <p>Qué hay, específicamente, detrás del dato que define el color de este mes.</p>
    <p class="cg-ficha-detalle">{ind.detalle_txt}</p>
  </section>
)}
```

- [ ] **Step 4: Sección "Color vigente y por qué"**

```astro
{ind?.semaforo?.por_que && (
  <section class="cg-ficha-sec">
    <h2>Color vigente y por qué</h2>
    <p>{ind.semaforo.por_que}</p>
    <p>
      Color vigente: <span class:list={["cg-verdict", ind.semaforo.color]}>
        {ind.semaforo.color.toUpperCase()}
      </span>
    </p>
    <p class="cg-ficha-nota">
      El color es una lectura adicional del puntaje: no reemplaza ni cambia la
      ponderación del indicador en el índice.
    </p>
  </section>
)}
```

- [ ] **Step 5: Compilar y mirar tres fichas distintas**

```bash
cd web && npx tsc --noEmit && npm run build && npm run preview
```

Abrir y verificar:
- `/metodologia/apertura_comercial` — indicador con tabla de umbrales y un solo tramo por color.
- `/metodologia/costo_financiamiento_tesoro` — el no monótono: amarillo y naranja tienen que aparecer **dos veces** en la tabla, y verde una sola.
- `/metodologia/alquiler_real` — indicador de vida cotidiana: color sí, tabla de umbrales no. La sección de semáforo no debe renderizarse vacía.

- [ ] **Step 6: Commit**

```bash
git add web/src/pages/metodologia/\[id\].astro web/public/dashboard.css
git commit -m "feat(semaforo): la ficha muestra umbrales, dato duro y por que del color"
```

---

### Task 7: Los tres ADR

**Files:**
- Create: `docs/adr/0181-el-color-es-la-tension-que-ya-se-publica.md`
- Create: `docs/adr/0182-los-umbrales-del-semaforo-se-calculan.md`
- Create: `docs/adr/0183-rediseno-del-cinturon-politico.md`
- Modify: `docs/adr/README.md` (**generado** — no editar a mano)

**Interfaces:**
- Consumes: la spec.
- Produces: nada que otra tarea consuma.

- [ ] **Step 1: Leer el formato vigente**

Run: `head -20 docs/adr/0179-ningun-test-escribe-en-un-archivo-versionado.md`

MADR v4 en castellano: frontmatter YAML + `Contexto y planteo · Factores de
decisión · Opciones consideradas · Decisión (+ Consecuencias, Confirmación) ·
Pros y contras · Más información`.

**Los ids van entre comillas** (`id: '0181'`, `relacionado: ['0121']`). Sin
comillas, YAML 1.1 los lee como octal y la referencia apunta a otro ADR sin que
falle nada.

- [ ] **Step 2: Escribir ADR-0181 — la regla**

Frontmatter: `id: '0181'`, `estado: 'aceptado'`, `fecha: 2026-08-08`,
`cinturon: 'transversal'`, `indice: 'todos'`,
`archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/lib/datos.ts']`,
`relacionado: ['0121', '0021']`.

Contenido obligatorio, todo de la spec:

- Las **tres opciones** (§3.1) con la premisa falsa del doc `ITCG_completo`: propone 85/55/25 como "punto medio entre anclas 100/70/40/10", y las anclas del ITCG son 100/85/65/40/10.
- Que las fichas de Gestión ya implementaban 65/45/25, verificado exacto en 12 indicadores.
- Que 60/40/20 son los bordes de `BANDAS_INTERPRETACION`, que ya se publican.
- **Efecto honesto, las dos mitades.** Los 6 indicadores que mejoran (§3.2) **y** la tabla de vida cotidiana, donde 5 componentes empeoran y el ITVC total pasa a naranja. Este ADR no puede mostrar solo la mitad favorable.
- Que el cambio **corrige** una inconsistencia previa: `semaforoDimension` usaba verde a tensión 4 para los índices 0-100 y a tensión 6 para el ITVC.
- La histéresis de dos meses como opción **descartada**, con el motivo (§3.3).

- [ ] **Step 3: Escribir ADR-0182 — umbrales calculados**

`id: '0182'`, `estado: 'aceptado'`, `continua: ['0181']`,
`archivos: ['scripts/parametrica.py']`.

Contenido: por qué los umbrales se calculan por interpolación inversa y no se
escriben en la ficha (las fichas de agosto envejecieron en una semana: RIGI
24,6% → 31,6%); el caso no monótono de `costo_financiamiento_tesoro` con su
mapa de colores completo; la trampa del redondeo de `aporte_score`; y que los
indicadores sin anclas reciben color pero no tabla.

- [ ] **Step 4: Escribir ADR-0183 — rediseño del ITCP, propuesto**

`id: '0183'`, **`estado: 'propuesto'`**, `cinturon: 'politica'`,
`indice: 'itcp'`, `relacionado: ['0048']`.

Contenido: los 11 indicadores del documento, los 10 que mapean, el que no
existe (Postura de los Sindicatos, con el sistema de puntajes por tipo de
acción que el documento propone), los **8 que hoy puntúan y el documento no
menciona**, y que reabrir la cohesión por cámara revierte ADR-0048. Más los
**cinco defectos** de los umbrales del documento (§7.3 de la spec): el hueco
90–99,9% en cohesión, el hueco por encima de 3,0 en ratio DNU, los dos ejes
mezclados en designación de jueces, los tramos compuestos del votómetro, y el
indicador de cámaras empresarias duplicado.

Este ADR **no se implementa**: registra la propuesta para que CIGOB la apruebe
o la baje.

- [ ] **Step 5: Regenerar el índice y correr el gate de ADR**

```bash
python scripts/adr_coherencia.py
python -m pytest tests/test_adr_format.py -q
```

Expected: PASS. El índice del README y las relaciones inversas se generan; no
se editan a mano.

- [ ] **Step 6: Commit**

```bash
git add docs/adr/0181-*.md docs/adr/0182-*.md docs/adr/0183-*.md docs/adr/README.md
git commit -m "docs(adr): 0181 la regla de color, 0182 los umbrales calculados, 0183 el ITCP propuesto"
```

---

### Task 8: Publicar y verificar en producción

Un color que está en un commit y no en la página no está entregado.

**Files:** ninguno nuevo — se corre el pipeline y se verifica.

- [ ] **Step 1: Correr la ruta acotada — sin saltarse el colector que sí se tocó**

La capa de semáforo en sí es de presentación, pero la Task 3 **sí** tocó un
colector: `scripts/macro.py:635` renombró el campo `semaforo` → `banda_idc`
que lee `publicar.py:454` para armar el texto del modal de `idc`. Eso es
exactamente el caso "un cinturón tocado" de CLAUDE.md (macro), así que el
primer paso de la ruta acotada es ese colector — **no** el pipeline completo
de los cinco cinturones, pero tampoco cero colectores:

```bash
python scripts/macro.py
python scripts/generar_informe.py
python scripts/publicar.py
python scripts/gate_calidad.py
python -m pytest tests -q
```

Si se omite `scripts/macro.py`, `output/cache/macro.json` se queda con la
clave vieja (`semaforo`) y sin la nueva (`banda_idc: null`), y el modal
público de `idc` publica el texto con el paréntesis vacío: "… asignación
−1,11 () — niveles: …".

Expected: gate y pytest en verde. Son dos puertas distintas: que pase el gate
no implica que pasen los tests de reconciliación.

- [ ] **Step 2: Build de la web**

```bash
cd web && npm run build && cd ..
```

- [ ] **Step 3: Commit del snapshot regenerado, con archivos explícitos**

```bash
git status --short
git add output/informe.json web/src/data/informe.json
git commit -m "chore(semaforo): snapshot con la capa de color"
```

**Nunca `git add -A`.** El repo vive en OneDrive y un `add` a ciegas commitea
snapshots viejos restaurados encima de los buenos. Si `git status` muestra
modificados generados que nadie regeneró, revisar `generated_at` adentro antes
de stagear.

- [ ] **Step 4: Push a `main`**

```bash
git pull --rebase
git push
```

`git pull --rebase` primero: el bot nocturno commitea a `main` y un push plano
sale rechazado. **Una rama no llega al sitio** — Vercel construye `main`.

- [ ] **Step 5: Verificar en producción, no en el artefacto intermedio**

Esperar el deploy y abrir `https://cigob-informe-coyuntura.vercel.app/?cb=1`.
Verificar **en la página**, no en el JSON:

- Un indicador del ITCG con tabla de umbrales, en `/metodologia/apertura_comercial`.
- Un indicador de vida cotidiana sin tabla, en `/metodologia/alquiler_real` — con color y sin sección de umbrales vacía.
- El no monótono en `/metodologia/costo_financiamiento_tesoro`, con amarillo y naranja partidos en dos tramos.
- Que el genoma de los cinturones muestre los cuatro colores y que vida cotidiana se vea con naranja donde antes había amarillo y rojo.

- [ ] **Step 6: Espejar la corrida en BigQuery**

```bash
python scripts/bigquery_export.py
```

El nocturno lo hace solo; **una corrida manual no**, y lo que no se sube ese
día no se puede reconstruir después. Es idempotente.

---

## Self-Review

**Cobertura de la spec:**

| Sección de la spec | Tarea |
|---|---|
| §3 regla de color (60/40/20, ITVC 105/95/85) | Task 1 |
| §3.3 histéresis descartada | Task 7 (ADR-0181) |
| §4.1 motor, interpolación inversa, no monotonía, transformaciones, dedup, trampa de redondeo | Tasks 1 y 2 |
| §4.2 bloque `semaforo` en el snapshot, `por_que` generado | Task 3 |
| §4.3 CSS, `datos.ts`, componentes, tres secciones de la ficha | Tasks 4, 5 y 6 |
| §4.4 no tocar bandas ni pesos | Global Constraints + `TestNoMovioNingunNumero` (Task 3) |
| §5 tests | Tasks 1, 2, 3, 4 y 5 |
| §6 ADRs | Task 7 |
| §7 fuera de alcance | Task 7 (ADR-0183) — el resto no se implementa acá |
| §8 definition of done | Task 8 |

**Sin placeholders.** Ningún paso dice "agregar manejo de errores" ni "escribir
los tests correspondientes": el código de test está completo en cada tarea.

**Consistencia de tipos.** `color_de_tension` / `color_de_puntaje` /
`color_de_indice_base100` / `umbrales_en_unidad` se llaman igual en las Tasks 1,
2 y 3. `semaforoDe` se llama igual en las Tasks 5 y 6. La forma del bloque
`semaforo` que produce la Task 3 es la que consumen las Tasks 5 y 6.

**Riesgo conocido, no resuelto acá.** La Task 6 no tiene test automático: las
tres secciones de la ficha se verifican mirando. Es coherente con cómo está
testeada hoy la capa Astro del repo, y las partes testeables (el dato publicado
y el contrato de lectura) están cubiertas por las Tasks 3 y 5.
