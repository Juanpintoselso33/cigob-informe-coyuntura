# Task 6 Report: Sync de la capa web (fichas, descripciones, etiquetas)

## Status: DONE_WITH_CONCERNS

Todos los pasos del brief se ejecutaron con el texto verbatim indicado. Build limpio,
nueva ruta generada, commit aislado a los 3 archivos. Ver "Concerns" al final por una
inconsistencia menor dentro del propio brief (Step 1 vs. la nota "Expected" del Step 5).

## Step 1-3: Ediciones aplicadas

- `web/src/lib/datos.ts`:
  - LABELS (política): línea de `gobernadores_alineamiento` actualizada a
    `"Alineamiento de gobernadores (retirado)"` + nueva línea
    `alineamiento_senadores_prov: "Alineamiento de senadores por provincia"`.
  - Unidades cortas: agregada `alineamiento_senadores_prov: "%"`.
  - Unidades largas: `gobernadores_alineamiento` → `"% de gobernadores (retirado)"` +
    nueva línea `alineamiento_senadores_prov: "% de senadores no-LLA"`.
  - `BARRA_0_100`: `"gobernadores_alineamiento"` reemplazado por
    `"alineamiento_senadores_prov"`.
- `web/src/lib/descripciones.ts`:
  - Entrada `gobernadores_alineamiento` removida limpiamente (sin precedente de
    "retirado" en este archivo) y reemplazada por la nueva entrada
    `alineamiento_senadores_prov`.
  - Referencia cruzada en `adhesion_reformas_provincial.aporta` actualizada de
    "el indicador de gobernadores" a "el indicador de alineamiento de senadores por
    provincia".
- `web/src/lib/fichas.ts`:
  - Nueva ficha `alineamiento_senadores_prov` insertada inmediatamente después del
    cierre de la ficha `cohesion_bloque_senado`, antes de `adhesion_reformas_provincial`
    (texto verbatim del brief, sin números de ADR).
  - Ficha histórica `gobernadores_alineamiento`: agregada entrada de retiro al array
    `cambios` (fecha 2026-07-08).
  - Ficha `adhesion_reformas_provincial`: `incidenciaTexto` (ítems 1 y 3) actualizado
    con la referencia cruzada a "alineamiento de senadores por provincia".

## Step 4: Build

Comando ejecutado: `cd web && npm run build` (desde
`C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura`).

Resultado: build limpio, sin errores (solo un warning preexistente de Vite sobre
chunk size > 500kB, no relacionado con este cambio).

Extracto relevante del output — generación de rutas `/metodologia/[id]`:

```
21:20:51 ▶ src/pages/metodologia/[id].astro
  ...
  ├─ /metodologia/eficacia_legislativa/index.html (+13ms)
  ├─ /metodologia/cohesion_bloque/index.html (+11ms)
  ├─ /metodologia/cohesion_bloque_senado/index.html (+7ms)
  ├─ /metodologia/alineamiento_senadores_prov/index.html (+18ms)
  ├─ /metodologia/adhesion_reformas_provincial/index.html (+15ms)
  ├─ /metodologia/gobernadores_alineamiento/index.html (+18ms)
  ├─ /metodologia/veto_quorum/index.html (+8ms)
  ...
21:20:52 [build] 66 page(s) built in 9.20s
21:20:52 [build] Complete!
```

Confirmado: `/metodologia/alineamiento_senadores_prov/index.html` se generó, y la
ficha histórica `/metodologia/gobernadores_alineamiento/index.html` sigue existiendo
(referencia histórica, como se pedía).

## Step 5: Grep de verificación

Comando ejecutado:
```bash
cd projects/informe_coyuntura && grep -rn "gobernadores_alineamiento" web/src/lib/
```

Resultado real:
```
web/src/lib/datos.ts:184:  gobernadores_alineamiento: "Alineamiento de gobernadores (retirado)", veto_quorum: "Sesiones caídas por quórum",
web/src/lib/datos.ts:245:  gobernadores_alineamiento: "%", veto_quorum: "%", comisiones_caidas: "%",
web/src/lib/datos.ts:284:  gobernadores_alineamiento: "% de gobernadores (retirado)", veto_quorum: "% de sesiones",
web/src/lib/fichas.ts:1019:  gobernadores_alineamiento: {
web/src/lib/fichas.ts:1021:    id: "gobernadores_alineamiento",
```

`descripciones.ts` no tiene ninguna referencia (0 matches), tal como especifica el
Step 2.

**Nota sobre discrepancia con el texto "Expected" del Step 5**: el brief dice
"solo debe aparecer dentro de la ficha histórica en fichas.ts... ninguna referencia
suelta en datos.ts/descripciones.ts fuera de ese archivo" — pero el propio Step 1
del brief instruye explícitamente (código verbatim) a MANTENER `gobernadores_alineamiento`
en `datos.ts` (LABELS, unidades cortas y largas), solo agregándole el sufijo
"(retirado)". Es decir, el código verbatim de Step 1 y la nota "Expected" de Step 5
se contradicen entre sí. Implementé Step 1 tal cual estaba escrito (verbatim, como
indicó la tarea), ya que tiene sentido funcional: mantener la clave vieja resuelta a
un label legible evita que `datos.ts::label()` caiga al fallback crudo
`key.replace(/_/g, " ")` para cualquier dato histórico/cacheado que todavía use la
clave `gobernadores_alineamiento` (mismo problema que este task fue creado para
resolver, aplicado retroactivamente a los datos viejos). No modifiqué el Step 1 para
que coincidiera con la nota del Step 5, porque la instrucción explícita fue usar el
código verbatim de cada step tal como está escrito.

## Step 6: Commit

```bash
git add web/src/lib/datos.ts web/src/lib/descripciones.ts web/src/lib/fichas.ts
git commit -m "feat(web): sincroniza fichas/descripciones/etiquetas con alineamiento_senadores_prov"
```

`git diff --cached --stat` inmediatamente antes de commitear:
```
 projects/informe_coyuntura/web/src/lib/datos.ts    |  9 +++--
 .../informe_coyuntura/web/src/lib/descripciones.ts | 10 +++---
 projects/informe_coyuntura/web/src/lib/fichas.ts   | 40 ++++++++++++++++++++--
 3 files changed, 49 insertions(+), 10 deletions(-)
```

Commit resultante: `96d9b8e feat(web): sincroniza fichas/descripciones/etiquetas con alineamiento_senadores_prov`
(rama `main`, 3 files changed, 49 insertions(+), 10 deletions(-)).

`git status --short` post-commit confirma que no quedó nada más staged/commiteado de
este cambio; los archivos modificados/untracked preexistentes de tasks anteriores
(data/, output/, scripts/, tests/, web/src/data/) permanecen intactos y sin tocar, y
`dist/`/`.astro/` (generados por el build de verificación) están en `web/.gitignore`
por lo que no aparecieron como untracked.

## Concerns

1. **Inconsistencia menor dentro del brief** (documentada arriba): el código verbatim
   del Step 1 mantiene `gobernadores_alineamiento` en `datos.ts`, pero la nota
   "Expected" del Step 5 da a entender que solo debería sobrevivir en `fichas.ts`. Se
   priorizó el código verbatim (instrucción explícita de la tarea) sobre la nota de
   expectativa, porque además tiene justificación funcional (backward-compat de
   labels para datos históricos). No requiere acción, pero lo señalo para que quede
   registrado.
2. El repo tenía cambios sin commitear de tasks anteriores de este mismo plan (data/,
   output/, scripts/, tests/, web/src/data/) antes de empezar — no se tocaron ni se
   incluyeron en este commit.
