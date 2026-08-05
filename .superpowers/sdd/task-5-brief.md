### Task 5: Sync final de `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md`

- [ ] **Step 1: Correr el pipeline completo**

```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py && python scripts/politica.py && python scripts/validacion_externa.py && python scripts/generar_informe.py && python scripts/publicar.py && python scripts/gate_calidad.py && python -m pytest tests/ -q
```

- [ ] **Step 2: Reemplazar la sección de `gobernadores_alineamiento` por `alineamiento_senadores_prov`**

Documentar qué mide (voto de senadores no-LLA vs. posición LLA, por provincia), el caveat honesto (no mide postura del gobernador), valor vigente real (de la corrida del Step 1), y agregar una nota breve indicando que `gobernadores_alineamiento` (55%, congelado desde abril) queda documentado como intento manual descartado, ya no pondera en el ITCP.

- [ ] **Step 3: Actualizar "Score actual del cinturón" y la tabla de bandas**

Con los valores reales de la corrida del Step 1. Marcar `alineamiento_senadores_prov` como **provisional** en la tabla de bandas.

- [ ] **Step 4: Staging cuidadoso y commit**

`scripts/descargar_series.py` sigue teniendo el WIP ajeno de motos sin commitear -- usar `git add -p` si se tocó ese archivo. Verificar `git diff --cached --stat` antes de cada commit.

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): sincroniza cinturon_politica.md con alineamiento_senadores_prov (reemplazo de gobernadores_alineamiento)"
```

---

