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

