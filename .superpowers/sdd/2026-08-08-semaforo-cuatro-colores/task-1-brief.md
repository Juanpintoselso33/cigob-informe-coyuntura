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

