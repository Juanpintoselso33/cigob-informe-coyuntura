### Task 9: Reescribir `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md`

- [ ] **Step 1: Reescribir siguiendo el formato de `docs/cinturon_gestion.md`**

Leer primero `docs/cinturon_gestion.md` completo como plantilla de formato
(tabla de dimensiones y pesos, detalle por indicador, sección de ejecución,
notas de mantenimiento). Reemplazar en `docs/cinturon_politica.md`:
- La sección "Encuadre" para incluir la tabla de pesos de dimensión.
- Cada entrada de indicador para reflejar el estado real post-implementación
  (`cohesion_bloque` ya no es "carga manual", agregar `cohesion_bloque_senado`,
  `adhesion_reformas_provincial`, `protestas_caba`).
- El score actual del cinturón (correr `python scripts/politica.py` primero
  para tener el valor real de ITCP a citar).

- [ ] **Step 2: Commit**

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): reescribe cinturon_politica.md reflejando la paramétrica ITCP"
```

---

