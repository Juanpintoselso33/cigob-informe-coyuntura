### Task 1: Preservar el fallback del Votómetro y desacoplar `projects/votometro/`

**Files:**
- Move: `projects/votometro/web/votometro.html` → `projects/informe_coyuntura/data/politica/votometro_fallback.html`
- Modify: `projects/informe_coyuntura/scripts/politica.py:82-83`
- Delete: `projects/votometro/` (resto del árbol, tras el move de arriba)

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `VOTOMETRO_HTML` en `politica.py` apunta al nuevo path — Task 4
  lo verifica corriendo `politica.py` y la suite de tests.

- [ ] **Step 1: Mover el archivo preservando historial**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git mv projects/votometro/web/votometro.html projects/informe_coyuntura/data/politica/votometro_fallback.html
```

- [ ] **Step 2: Actualizar el path en `politica.py`**

En `projects/informe_coyuntura/scripts/politica.py`, reemplazar:

```python
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR.parent / "votometro" / "web" / "votometro.html"  # fallback local
```

por:

```python
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR / "data" / "politica" / "votometro_fallback.html"  # fallback local
```

- [ ] **Step 3: Verificar que el archivo movido existe donde el código lo espera**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python -c "from pathlib import Path; p = Path('data/politica/votometro_fallback.html'); print(p.resolve(), p.exists())"
```

Expected: imprime la ruta y `True`.

- [ ] **Step 4: Borrar el resto de `projects/votometro/`**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git rm -r projects/votometro
```

Expected: lista `projects/votometro/README.md`, `docs/...`,
`web/encuestas.json`, `web/.gitkeep`, `scripts/.gitkeep`, `output/.gitkeep`,
`docs/protocolo_actualizacion.md` como `deleted`. NO debe aparecer
`votometro.html` (ya se movió en el Step 1).

- [ ] **Step 5: Commit**

```bash
git add projects/informe_coyuntura/scripts/politica.py
git commit -m "refactor: mueve el fallback del Votómetro dentro de informe_coyuntura y saca projects/votometro/"
```

---

