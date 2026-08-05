### Task 10: Fichas metodológicas en la web

**Files:**
- Modify: `web/src/lib/fichas.ts`

- [ ] **Step 1: Leer las fichas existentes de `cohesion_bloque` y `gobernadores_alineamiento`**

```bash
grep -n "cohesion_bloque\|gobernadores_alineamiento" web/src/lib/fichas.ts
```

Usar la ficha existente de `cohesion_bloque` como plantilla de formato (misma
interfaz TS que las 55 fichas ya publicadas — sin números de ADR en el texto
público, per convención vigente).

- [ ] **Step 2: Actualizar la ficha de `cohesion_bloque`**

Actualizar el texto de metodología para reflejar el índice de Rice (dejar de
decir "% alineado con la posición oficial"; explicar en lenguaje llano qué es
cohesión de bloque y cómo se calcula, sin jerga de "índice de Rice" si el
estándar de las fichas es explicar en términos llanos — seguir el mismo
registro que usan las fichas de ITCM/ITCG ya publicadas).

- [ ] **Step 3: Agregar 3 fichas nuevas**

`cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`
(esta última puede reusar/adaptar texto de la ficha ya existente en gestión
si la hay, ajustando la lectura: en política mide condición de gobernabilidad,
no premia/castiga la protesta).

- [ ] **Step 4: Verificar que el sitio renderiza sin errores**

```bash
cd web && npm run build
```
Expected: build exitoso, sin errores de TypeScript.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/fichas.ts
git commit -m "feat(web): fichas metodológicas para ITCP — cohesion_bloque actualizada + 3 nuevas"
```

---

## Self-Review

**Cobertura del spec:** Tarea 1 cubre dimensiones/bandas/`calcular_itcp()`.
Tareas 2-4 cubren los 3 indicadores nuevos. Tarea 5 cubre el reemplazo de
`calcular_score()`. Tareas 6-7 cubren `ajustes_itcp.json` y el backfill.
Tareas 8-10 cubren ADR, doc del cinturón y fichas web. Todo lo comprometido en
la sección "Sub-proyecto 2" del spec tiene tarea.

**Placeholders:** el nombre exacto del fetcher ACLED en `gestion.py` (Tarea 4)
y la estructura exacta de `fichas.ts` (Tarea 10) no estaban confirmados en el
spec — ambas tareas empiezan con un `grep`/lectura concreta para resolverlo
antes de escribir código, no con una instrucción vaga.

**Consistencia de tipos:** `DIMENSIONES_ITCP` en Tarea 1 usa exactamente las
mismas 12 claves de indicador que se fetchean en Tareas 2-5 y que se backfillean
en Tarea 7 (`cohesion_bloque`, `cohesion_bloque_senado`,
`adhesion_reformas_provincial`, `protestas_caba` + los 8 ya existentes).
`_paced_get` introducido en Tarea 2 es consumido tanto por
`_hcdn_votaciones_get` (retrocompatibilidad con el plan anterior) como por
`_descubrir_actas_senado`/`fetch_cohesion_bloque_senado`.
