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

