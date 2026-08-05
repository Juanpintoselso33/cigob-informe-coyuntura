### Task 7: Backfill de las series nuevas

**Files:**
- Modify: `scripts/descargar_series.py`

- [ ] **Step 1: Confirmar si `protestas_caba` ya tiene serie histórica**

```bash
grep -n "protestas_caba" scripts/descargar_series.py
```

Si ya existe (reutilizada de gestión), no duplicar — solo confirmar que
`POLITICA_DERIVADAS` también la referencia para el cinturón política.

- [ ] **Step 2: Agregar series para `cohesion_bloque_senado` y `adhesion_reformas_provincial`**

```python
def fetch_cohesion_bloque_senado_serie(anio_inicio: int = 2023) -> dict:
    """Backfill de cohesion_bloque_senado, mismo patrón que cohesion_bloque_serie."""
    serie = {}
    for anio in range(anio_inicio, datetime.now().year + 1):
        resultado = politica.fetch_cohesion_bloque_senado(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            serie[str(anio)] = resultado["valor"]
    return serie


def fetch_adhesion_reformas_provincial_serie() -> dict:
    """adhesion_reformas_provincial es un STOCK (adhesión es un evento único
    e irreversible por provincia, no una serie mensual suave) — un solo punto
    con el valor actual, no backfill año por año (no hay forma de reconstruir
    cuándo adhirió cada provincia sin una fuente con fecha de adhesión)."""
    resultado = politica.fetch_adhesion_reformas_provincial()
    if not resultado:
        return {}
    return {str(datetime.now().year): resultado["valor"]}
```

Registrar ambas en `POLITICA_DERIVADAS` junto a `fetch_cohesion_bloque_serie`
(Tarea 10 del plan anterior).

- [ ] **Step 3: Correr el backfill**

Run: `python scripts/descargar_series.py`
Expected: exit 0, series nuevas presentes en el archivo de históricos de política.

- [ ] **Step 4: Commit**

```bash
git add scripts/descargar_series.py data/politica/
git commit -m "feat(politica): backfill de cohesion_bloque_senado y adhesion_reformas_provincial"
```

---

