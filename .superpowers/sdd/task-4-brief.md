### Task 4: Verificación de la limpieza (antes de tocar nada de GitHub)

**Files:** ninguno nuevo — solo corridas de verificación sobre lo hecho en
Tasks 1-3.

- [ ] **Step 1: Suite de tests de `informe_coyuntura`**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python -m pytest tests -q
```

Expected: todo en verde. Si algo de `test_itcp.py` o
`test_descargar_series_cohesion.py` falla, es señal de que el path nuevo de
`VOTOMETRO_HTML` rompió algo — no asumir que es un test flaky, revisar el
path del Step 3 de la Task 1.

- [ ] **Step 2: Correr el colector de política (scoped — un solo cinturón tocado)**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python scripts/politica.py
```

Expected: exit code 0 o 1 (fresh o mixed cache — ambos ok). Revisar en el
output que `votometro_ventaja_lla` no aparezca con warning de "archivo no
encontrado" — si `_cargar_votometro_html()` cae al fallback, tiene que
poder leer el archivo nuevo sin error.

- [ ] **Step 3: Confirmar que no queda ninguna referencia colgante**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
grep -rn "projects/votometro\|web/votometro.html\|web/bibliotecario.html\|actualizar_encuestas" --include="*.yml" --include="*.md" --include="*.html" --include="*.py" .
```

Expected: sin resultados (o resultados dentro de `docs/superpowers/` /
`backup/`, que están gitignored y no importan).

- [ ] **Step 4: Push**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git status --short
git pull --rebase
git push
```

---

