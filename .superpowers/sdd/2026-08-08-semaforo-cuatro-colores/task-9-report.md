# Task 9 — Reporte: `verdictDeCinturon` no conocía el vocabulario real de `estado`

## Qué cambié

- `projects/informe_coyuntura/web/src/lib/datos.ts` (líneas ~230-241):
  `verdictDeCinturon` comparaba contra `"critico"` y `"alerta"`, valores que
  `_estado()` nunca produce. Reemplacé esas dos ramas muertas por
  `estado === "tensionado"` (que ahora sí pinta rojo) y agregué un
  comentario en castellano explicando (a) por qué son 3 colores acá y 4 en
  el semáforo de indicadores/índices (ADR-0181), y (b) que el mapeo espeja
  `generar_informe.py:192`.

  ```ts
  export function verdictDeCinturon(estado: string): "verde" | "amarillo" | "rojo" {
    if (estado === "estable") return "verde";
    if (estado === "tensionado") return "rojo";
    return "amarillo"; // en_tension
  }
  ```

- `projects/informe_coyuntura/tests/test_web_semaforo.py`: agregué el test
  bidireccional (no creé un archivo nuevo — este archivo ya existía desde la
  Task 7 con tests del semáforo de 4 colores en CSS; los dejé intactos y
  aunque el `Write` inicial casi lo pisa, el tool lo bloqueó porque no lo
  había leído todavía. Se preservaron sus 5 tests originales).

No toqué `UMBRALES`, `_estado()`, ningún score/índice, el semáforo de 4
colores, ni `web/dist/`.

## TDD — RED

Comando:
```
python -m pytest tests/test_web_semaforo.py -v
```

Salida (antes del fix, 8 tests, 2 fallan):

```
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_tienen_token_y_variante_soft PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_genoma_y_verdict PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_el_punto_del_verdict PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_datos_ts_no_recalcula_el_semaforo PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_ningun_ts_deriva_el_color_de_un_numero PASSED
tests/test_web_semaforo.py::TestVerdictDeCinturonConoceElVocabularioDeEstado::test_todo_estado_real_resuelve_a_un_color_valido PASSED
tests/test_web_semaforo.py::TestVerdictDeCinturonConoceElVocabularioDeEstado::test_verdict_de_cinturon_no_compara_contra_estados_fantasma FAILED
tests/test_web_semaforo.py::test_verdict_de_cinturon_espeja_el_color_de_generar_informe FAILED

AssertionError: verdictDeCinturon compara contra {'critico', 'alerta'}, que _estado()
nunca produce (vocabulario real: {'tensionado', 'en_tension', 'estable'})

AssertionError: 'tensionado' resuelve a 'amarillo' en el chip web, pero
generar_informe.py lo pinta 'rojo'

2 failed, 6 passed in 4.69s
```

Por qué era el resultado esperado: la dirección "todo estado real resuelve a
un color válido" YA valía antes del fix (hay un fallback que atrapa
cualquier string no reconocido, así que nunca hay un caso sin color) — el
brief lo anticipaba explícitamente. La dirección que debía fallar,
"ninguna comparación explícita menciona un valor que `_estado()` no puede
emitir", falló exactamente por `critico`/`alerta`. Agregué además un tercer
test (no pedido explícitamente pero en línea con el objetivo de "que no
vuelvan a divergir") que compara el color resuelto contra el mapeo real de
`generar_informe.py:192` — también falló, mostrando el síntoma concreto
(`tensionado` → `amarillo` en vez de `rojo`).

## TDD — GREEN

Mismo comando después del fix en `datos.ts`:

```
8 passed in 1.99s
```

## Diseño del test

- `_estados_reales()`: llama a `publicar._estado(0)`, `publicar._estado(5)`,
  `publicar._estado(9)` (un score de cada tramo dado `UMBRALES` =
  `ESTABLE_MAX=3`, `EN_TENSION_MAX=6`) para obtener
  `{"estable", "en_tension", "tensionado"}` corriendo el código real, no
  copiando los nombres a mano — así el test pinea los umbrales vigentes.
- `_cuerpo_verdict_de_cinturon()`: extrae con regex el cuerpo de la función
  `verdictDeCinturon` de `datos.ts` (texto crudo, sin ejecutar TypeScript).
- `_mapa_explicito(cuerpo)`: parsea cada `if (estado === "X" [|| estado ===
  "Y"]) return "Z";` a un dict `{valor_de_estado: color}` — reproduce en
  Python, sobre el texto real, qué color asigna cada comparación explícita.
- `_color_fallback(cuerpo)`: el color del único `return` sin condición.
- **Dirección 1** (`test_todo_estado_real_resuelve_a_un_color_valido`): para
  cada valor de `_estados_reales()`, resuelve el color (explícito o
  fallback) y verifica que sea uno de `{verde, amarillo, rojo}`. Vale
  siempre que exista un fallback, así que ya pasaba antes del fix —
  documentado en el docstring del test para que quede claro que no es la
  mitad que debía fallar.
- **Dirección 2** (`test_verdict_de_cinturon_no_compara_contra_estados_fantasma`):
  el set de claves de `_mapa_explicito` (los valores contra los que el chip
  compara) tiene que ser subconjunto de `_estados_reales()`. Esta es la
  mitad que falla hoy, por `critico`/`alerta`.
- Extra (`test_verdict_de_cinturon_espeja_el_color_de_generar_informe`):
  parsea el dict `{"estable": "🟢", ...}` de `generar_informe.py:192`,
  traduce emoji→color, y verifica que el color resuelto por el chip para
  cada estado real coincida exactamente con ese mapeo ya decidido. No lo
  pidió el brief en esos términos, pero cierra la clase de bug completa (no
  solo el vocabulario, también la asignación de color) con el mismo
  mecanismo de extracción por regex que ya usa `test_web_labels.py` en este
  repo.

## El efecto visible — BLUF

Construí el sitio (`npm run build`) y leí `dist/index.html`. Texto completo
del párrafo `cg-bluf-text` con el snapshot vigente:

> Vida cotidiana está en zona crítica; Con una tensión global de 3,4/10,
> vida cotidiana es el cinturón más exigido del tablero (6,9/10);
> macroeconomía y política operan en tensión; gestión y espíritu de época
> se mantienen estables. La mayor presión puntual del mes está en
> vulnerabilidad financiera (17,2), la dimensión que más tensión aporta al
> índice de vida cotidiana. El riesgo dominante del período es el
> barbarismo tecnocrático: el desequilibrio hacia el que más se inclina hoy
> el tablero si las tensiones no se procesan.

**Juicio: no se lee bien, por dos motivos independientes:**

1. **Error de gramática**: `"...en zona crítica; Con una tensión global..."`
   — mayúscula en `Con` en mitad de la oración, después de un punto y
   coma. Causa raíz en `Bluf.astro:28`: esa frase está hardcodeada con "C"
   mayúscula porque el código asumía que siempre sería la primera del
   párrafo (`frases[0]`) cuando no había ningún cinturón en rojo. Ahora que
   `rojos.length > 0` por primera vez, esa frase pasa a ser la segunda y
   arrastra su mayúscula fuera de lugar. Es un bug latente en
   `Bluf.astro`, no en el código que toqué — nunca se había ejecutado esa
   combinación de ramas hasta este fix.
2. **Redundancia**: la primera cláusula (`"Vida cotidiana está en zona
   crítica"`) y la segunda (`"...vida cotidiana es el cinturón más exigido
   del tablero (6,9/10)"`) dicen lo mismo dos veces seguidas — que vida
   cotidiana es el peor cinturón — con distinta fraseología.

No reescribí `Bluf.astro`: está fuera del alcance de esta tarea (el commit
del brief sólo incluye `datos.ts` y el test), y el brief pide explícitamente
reportar sin retocar la copia en silencio si lee mal.

## Verificación de build

`npx tsc --noEmit` (en `web/`): sin salida, sin errores.

`npm run build`: completó limpio, 81 páginas generadas, sin errores (sólo
el warning preexistente de Vite sobre chunks >500kB, no relacionado).

## Suite completa

```
python -m pytest tests -q
```
Resultado: `1 failed, 1953 passed, 3 skipped, 4 warnings, 1 error in 57.24s`

Los dos fallos son exactamente los preexistentes que el brief marca como
ajenos:
- `test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
- error de teardown en `test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes`

Nada nuevo falló.

## Archivos cambiados

- `projects/informe_coyuntura/web/src/lib/datos.ts`
- `projects/informe_coyuntura/tests/test_web_semaforo.py`

(No se tocó `.superpowers/sdd/.gitignore`, que ya estaba modificado sin
commitear al empezar esta tarea — lo dejé intacto y sin stagear.)

## Auto-revisión

- Revisé los 8 consumidores de `verdictDeCinturon`/`cinturonesRojos`
  (`CinturonCard.astro`, `TensionPanel.astro`, `frontada.astro`,
  `[slug].astro`, `Hero.astro`, `Archivo.astro`, `Metodologia.astro`,
  `Bluf.astro`): todos ya tenían el color/label/CSS de `"rojo"` totalmente
  implementado (`var(--rojo)`, `.cg-verdict.rojo`, `LABEL.rojo = "Crítico"`
  / `"En crisis"`, etc.) — la rama roja estaba muerta pero no faltante, así
  que activarla no dejó ningún hueco visual sin estilo. Confirmado también
  por los tests preexistentes `TestTokensCss` en el mismo archivo
  (`.cg-verdict.rojo` existe en `dashboard.css`), que siguen pasando.
- Confirmé que `web/dist/` sigue gitignorado (`git check-ignore` lo
  confirma) y no quedó nada de la build de verificación en el staging.
- Confirmé con `git status`/`git diff` que sólo se modificaron los dos
  archivos del commit, y que el cambio en `datos.ts` es mínimo (2 líneas de
  lógica + comentario).
- El "casi incidente" del `Write` inicial (que hubiera reemplazado el
  archivo completo de tests del semáforo de 4 colores de la Task 7 por mi
  contenido) fue bloqueado por la herramienta antes de tocar disco — lo
  arreglé usando `Edit` para añadir mis clases de test al final del archivo
  existente, preservando los 5 tests originales intactos (verificado:
  siguen los 8 pasando, no 3).

## Concerns

- El bug de gramática/redundancia del BLUF (`Bluf.astro:26-28`) es real,
  visible en producción una vez que se publique este cambio, y queda sin
  arreglar a propósito (fuera de alcance de esta tarea). Vale la pena una
  tarea de seguimiento: la frase de `masTenso` (línea 28) necesita minúscula
  cuando no es la primera del párrafo, y probablemente conviene fusionar
  esa frase con la de "está en zona crítica" cuando `masTenso` coincide con
  el único cinturón en rojo (el caso de hoy), para no repetir el mismo
  hecho dos veces.

---

# Fix round 1 — respuesta a la revisión

Dos hallazgos "Important", ambos corregidos. Commit: `29d698e` (sobre
`f333b0c`, el de la Task 9 original).

## Hallazgo 1 — la protección real dependía del test que sobraba

**Diagnóstico del revisor, confirmado**: `test_todo_estado_real_resuelve_a_un_color_valido`
sólo pedía "algún color de los tres" — eso ya valía con el bug (hay
fallback), así que borrar la rama `tensionado` no lo hacía fallar. La única
red era `test_verdict_de_cinturon_espeja_el_color_de_generar_informe`, un
test que agregué por iniciativa propia y que alguien podría podar como
"redundante" sin darse cuenta de que era el único que mordía.

**Fix**: fusioné ambos. `test_todo_estado_real_resuelve_a_un_color_valido`
pasó a llamarse `test_todo_estado_real_resuelve_al_color_canonico` y ahora
exige, para cada estado real, el color EXACTO que `generar_informe.py:192`
ya decidió (no "un color válido cualquiera"). Se eliminó el test standalone
`test_verdict_de_cinturon_espeja_el_color_de_generar_informe`: su lógica
vive ahora dentro de la aserción obligatoria, no al costado.

### Dientes verificados en las dos direcciones (comandos y salida reales)

**A. Sacar la rama `tensionado`** (`web/src/lib/datos.ts`, temporalmente
`if (estado === "estable") return "verde"; return "amarillo";`):

```
python -m pytest tests/test_web_semaforo.py::TestVerdictDeCinturonConoceElVocabularioDeEstado -v
```
```
test_todo_estado_real_resuelve_al_color_canonico FAILED
test_verdict_de_cinturon_no_compara_contra_estados_fantasma PASSED

AssertionError: 'tensionado' (real, emitido por _estado()) resuelve a
'amarillo' en el chip web, pero generar_informe.py (fuente de verdad) lo
pinta 'rojo'
```
Correcto: el test de cobertura/mapeo cae; el de fantasmas no tiene por qué
(no hay ninguna comparación fantasma en ese estado del código).

Restaurado a `if (estado === "tensionado") return "rojo";` y reverificado
en verde antes de seguir.

**B. Agregar una rama fantasma `critico`** (temporalmente
`if (estado === "tensionado" || estado === "critico") return "rojo";`):

```
python -m pytest tests/test_web_semaforo.py::TestVerdictDeCinturonConoceElVocabularioDeEstado -v
```
```
test_todo_estado_real_resuelve_al_color_canonico PASSED
test_verdict_de_cinturon_no_compara_contra_estados_fantasma FAILED

AssertionError: verdictDeCinturon compara contra {'critico'}, que _estado()
nunca produce (vocabulario real: {'en_tension', 'estable', 'tensionado'})
```
Correcto: el mapeo sigue siendo válido para `tensionado` (sigue apuntando a
rojo), así que sólo el chequeo de fantasmas se entera del agregado.

Restaurado a la versión correcta (`if (estado === "tensionado") return
"rojo";`) y confirmado `git diff` vacío contra `web/src/lib/datos.ts` tal
como quedó commiteado en la Task 9 original — las dos idas y vueltas no
dejaron rastro.

## Hallazgo 2 — el BLUF, reconstruido

**Fix en `Bluf.astro`**: saqué `cap()` de la cláusula de `rojos` y el `"Con"`
mayúscula hardcodeado de la cláusula de `masTenso` (ahora `"con"` minúscula
siempre); `cap()` se aplica una única vez, sobre `frases.join("; ")` ya
completo. Agregué además la condición pedida: cuando el único cinturón en
rojo es también el `masTenso`, la segunda cláusula ya no repite su nombre
("es además el cinturón más exigido del tablero" en vez de nombrarlo de
nuevo); cuando son cinturones distintos, se mantiene la redacción anterior
(nombrando a `masTenso` explícitamente, porque hace falta para desambiguar
cuál de los rojos es el más tenso).

### BLUF reconstruido — snapshot actual (vida_cotidiana en rojo)

```
npm run build
```
Párrafo `cg-bluf-text` extraído de `dist/index.html`:

> Vida cotidiana está en zona crítica; con una tensión global de 3,4/10, es
> además el cinturón más exigido del tablero (6,9/10); macroeconomía y
> política operan en tensión; gestión y espíritu de época se mantienen
> estables. La mayor presión puntual del mes está en vulnerabilidad
> financiera (17,2), la dimensión que más tensión aporta al índice de vida
> cotidiana. El riesgo dominante del período es el barbarismo tecnocrático:
> el desequilibrio hacia el que más se inclina hoy el tablero si las
> tensiones no se procesan.

**Juicio: se lee bien.** Mayúscula sólo al inicio del párrafo, minúscula
correcta después del primer punto y coma, y ya no repite "vida cotidiana"
dos cláusulas seguidas — dice una vez que está en zona crítica y una vez
que es además la más exigida, sin machacar el nombre.

### BLUF reconstruido — caso sin rojos (el de todos los meses hasta hoy)

Construido temporalmente editando `web/src/data/informe.json` (una sola
ocurrencia de `"estado": "tensionado"` en todo el archivo, la de
`vida_cotidiana`) a `"en_tension"`, para simular el escenario que existió
en la práctica desde que el sitio existe. Respaldé el archivo original
antes de tocarlo y lo restauré byte a byte después (`git status` sobre
`web/src/data/informe.json` quedó limpio, confirmado).

Párrafo resultante:

> Con una tensión global de 3,4/10, vida cotidiana es el cinturón más
> exigido del tablero (6,9/10); también macroeconomía y política en
> tensión; gestión y espíritu de época se mantienen estables. La mayor
> presión puntual del mes está en vulnerabilidad financiera (17,2), la
> dimensión que más tensión aporta al índice de vida cotidiana. El riesgo
> dominante del período es el barbarismo tecnocrático: el desequilibrio
> hacia el que más se inclina hoy el tablero si las tensiones no se
> procesan.

**Juicio: se lee bien, sin regresión.** La cláusula de `masTenso` vuelve a
ser la primera del párrafo (no hay cláusula de rojos antes) y `cap()` la
capitaliza igual que antes ("Con" con mayúscula, ahora dinámica en vez de
hardcodeada — mismo resultado visual). La rama `también macroeconomía y
política en tensión` (el caso `amarillos.length > 1` con `masTenso` incluido
entre los amarillos) no se tocó y sigue leyéndose correctamente en minúscula
tras el punto y coma, como ya lo hacía antes de este fix.

Rehice el build una tercera vez con el snapshot real restaurado para dejar
`dist/` (gitignorado, de todos modos) reflejando el estado final, y
reconfirmé el mismo párrafo del snapshot actual citado arriba.

## Verificación de build y suite (fix round 1)

- `npx tsc --noEmit` (en `web/`): sin salida, exit 0.
- `npm run build`: 81 páginas, limpio (mismo warning preexistente de Vite
  sobre chunks >500kB).
- `python -m pytest tests/test_web_semaforo.py -v`: 7/7 (uno menos que
  antes: se fusionaron dos tests en uno, no se perdió cobertura).
- `python -m pytest tests -q`: `1 failed, 1952 passed, 3 skipped, 4
  warnings, 1 error` — los mismos dos fallos preexistentes de siempre
  (`test_el_valor_vigente_del_ipi_no_cambio` y el error de teardown de
  `test_gestion_privatizaciones_novedades.py`), nada nuevo.

## Archivos cambiados (fix round 1)

- `projects/informe_coyuntura/tests/test_web_semaforo.py`
- `projects/informe_coyuntura/web/src/components/Bluf.astro`

(`web/src/lib/datos.ts` no cambió en esta ronda — sólo se probó y se
restauró para verificar los dientes del test.)

## Concerns (fix round 1)

- El mensaje del commit `29d698e` tiene un error de tipeo en el cuerpo
  ("Ahora esa misma dole la asercion real" — debía decir algo como "ahora
  esa misma dirección ES la aserción real"). No lo corregí con `--amend`
  porque la política del repo pide crear un commit nuevo en vez de
  enmendar salvo pedido explícito; lo señalo acá para que quede claro que
  es un typo de redacción, no un problema de contenido — el diff que
  describe es correcto y fue verificado línea por línea antes de commitear.
- El caso "más de un cinturón en rojo, y `masTenso` es uno de ellos mientras
  hay otro" queda con la redacción anterior (nombra a `masTenso`
  explícitamente) en vez de "es además..." — a propósito, para no perder la
  desambiguación de cuál de los rojos es el más tenso. No hay forma de
  construir ese escenario hoy (sólo un cinturón puede llegar a
  `tensionado` con los datos vigentes) así que quedó verificado sólo por
  lectura de código, no por build real.
