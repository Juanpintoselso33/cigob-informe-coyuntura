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

