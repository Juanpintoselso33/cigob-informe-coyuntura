### Task 5: La web lee el color en vez de calcularlo

**Files:**
- Modify: `web/src/lib/datos.ts:175-182` (`semaforoDimension`)
- Modify: `web/src/components/CinturonCard.astro:45`
- Modify: `web/src/components/IndicadorTile.astro`
- Test: `tests/test_web_semaforo.py` (agregar)

**Interfaces:**
- Consumes: el campo `semaforo.color` que publica la Task 3.
- Produces: `semaforoDe(x: { semaforo?: { color: string } }): "verde" | "amarillo" | "naranja" | "rojo"` exportada desde `datos.ts`.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_web_semaforo.py`:

```python
class TestSinCortesDuplicadosEnTs:
    def test_datos_ts_no_recalcula_el_semaforo(self):
        """Los cortes viven solo en parametrica.py. Si el cliente los repite,
        se desincronizan sin que falle nada."""
        ts = (LIB / "datos.ts").read_text(encoding="utf-8")
        assert "semaforoDimension" not in ts, (
            "semaforoDimension calculaba el color en el cliente; "
            "tiene que leer el color publicado")
        assert "semaforoDe" in ts, "falta el lector semaforoDe"

    def test_ningun_corte_del_semaforo_hardcodeado_en_ts(self):
        prohibidos = (">= 95", ">= 90", ">= 105", ">= 85")
        for archivo in LIB.glob("*.ts"):
            texto = archivo.read_text(encoding="utf-8")
            for patron in prohibidos:
                assert patron not in texto, f"{archivo.name}: corte hardcodeado {patron}"
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `python -m pytest tests/test_web_semaforo.py -v -k Ts`
Expected: FAIL — `semaforoDimension` sigue en `datos.ts`.

- [ ] **Step 3: Implementar en `datos.ts`**

Reemplazar el bloque `semaforoDimension` (líneas 175-182) por:

```ts
export type ColorSemaforo = "verde" | "amarillo" | "naranja" | "rojo";

// El color LO CALCULA parametrica.py y viaja en el snapshot (ADR-0181). Acá
// solo se lee: si el cliente lo recalculara, habría dos definiciones del corte
// y se desincronizarían sin que falle nada. Hasta agosto de 2026 esta función
// calculaba 3 colores en el cliente, con una vara distinta para el ITVC
// base-100 (verde a tensión 6) que para los índices 0-100 (verde a tensión 4).
export function semaforoDe(x: { semaforo?: { color?: string } } | null | undefined): ColorSemaforo {
  const c = x?.semaforo?.color;
  return c === "verde" || c === "amarillo" || c === "naranja" || c === "rojo"
    ? c
    : "amarillo";
}
```

Buscar los usos de `semaforoDimension` y `tensionDeDimension` en el resto del
repo antes de borrar, con `grep -rn "semaforoDimension" web/src/`.
`tensionDeDimension` y `peorDimension` **se conservan**: comparan tensión entre
índices de escala distinta y no son parte del semáforo.

- [ ] **Step 4: Implementar en los componentes**

En `CinturonCard.astro`, la línea 45 pasa de calcular a leer:

```astro
class:list={["cg-genoma-seg", `sem-${semaforoDe(dim)}`, "cg-dim--clickable", { "is-critica": dim.critica }]}
```

y el import de la línea 2 cambia `semaforoDimension` por `semaforoDe`.

En `IndicadorTile.astro`, agregar el import y un punto de color en el head de la card:

```astro
---
import { presentacion, label, visualDe, badgeEstado, periodoDato, series, formatValor, semaforoDe } from "../lib/datos.ts";
...
const color = semaforoDe(ind);
---
  <div class="cg-tile-head">
    <span class:list={["cg-tile-dot", `sem-${color}`]} title={ind.semaforo?.por_que ?? undefined} aria-hidden="true"></span>
    <span class="cg-tile-name">{label(ikey)}</span>
    <span class:list={["cg-tile-badge", badgeCls]} title={chipTitle}>{chip}</span>
  </div>
```

y en `dashboard.css`, junto a las otras reglas `.sem-*`:

```css
.cg-tile-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 8px; }
.cg-tile-dot.sem-verde    { background: var(--verde); }
.cg-tile-dot.sem-amarillo { background: var(--amarillo); }
.cg-tile-dot.sem-naranja  { background: var(--naranja); }
.cg-tile-dot.sem-rojo     { background: var(--rojo); }
```

El punto lleva `aria-hidden` y el color no es el único portador de la
información: el número y el texto del `por_que` siguen ahí.

- [ ] **Step 5: Compilar y correr los tests**

```bash
cd web && npx tsc --noEmit && npm run build && cd ..
python -m pytest tests/test_web_semaforo.py -v
```

Expected: build limpio y 4 tests en verde.

- [ ] **Step 6: Commit**

```bash
git add web/src/lib/datos.ts web/src/components/CinturonCard.astro web/src/components/IndicadorTile.astro web/public/dashboard.css tests/test_web_semaforo.py
git commit -m "feat(semaforo): la web lee el color publicado en vez de recalcularlo"
```

---

