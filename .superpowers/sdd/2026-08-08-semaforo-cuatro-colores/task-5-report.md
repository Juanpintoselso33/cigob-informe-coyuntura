# Task 5 — La web lee el color en vez de calcularlo — Reporte

## Qué se implementó

1. `web/src/lib/datos.ts`: reemplazado `semaforoDimension(puntaje, base100)` (3
   colores, dos varas distintas — tensión 4 para índices 0-100, tensión 6 para
   el ITVC base-100) por `semaforoDe(x)`, que solo lee `x.semaforo.color` del
   snapshot publicado por `publicar.py`/`parametrica.py` (ADR-0181). Se agregó
   el tipo exportado `ColorSemaforo = "verde" | "amarillo" | "naranja" | "rojo"`.
2. `web/src/components/CinturonCard.astro`: import y línea 45 convertidos de
   `semaforoDimension(dim.puntaje, !!indice.base100)` a `semaforoDe(dim)`.
3. `web/src/components/IndicadorTile.astro`: import de `semaforoDe`, `const
   color = semaforoDe(ind)`, y un punto de color (`<span class="cg-tile-dot
   sem-{color}" aria-hidden="true" title={ind.semaforo?.por_que ?? undefined}>`)
   en el head de la card, antes del nombre.
4. `web/public/dashboard.css`: reglas `.cg-tile-dot` + `.cg-tile-dot.sem-*`
   junto a las demás reglas `.sem-*` del genoma.
5. `tests/test_web_semaforo.py`: agregada la clase `TestSinCortesDuplicadosEnTs`
   del brief, tal cual.

## Divergencia del brief (con motivo)

**`web/public/overrides.css` también se modificó** (no estaba en la lista de
archivos del brief). Motivo: al agregar el punto como PRIMER hijo de
`.cg-tile-head`, ese contenedor pasa de 2 a 3 hijos directos (punto, nombre,
badge). La regla existente era:

```css
.cg-tile-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
```

Con `justify-content: space-between` y 3 hijos sin `flex-grow`, el espacio
libre del contenedor se reparte por igual entre los DOS huecos (punto↔nombre
y nombre↔badge) — el hueco punto↔nombre deja de ser el `gap: 8px` fijo y pasa
a llevarse la mitad del espacio libre de la card (~130px en una tile típica).
Resultado: el punto queda pegado al borde izquierdo y el nombre flota lejos,
cerca del centro de la card — separados, no juntos como muestra el markup del
brief. No es un detalle cosmético menor: rompe la lectura del head completo.

Arreglado sacando `justify-content: space-between` de `.cg-tile-head` y
agregando `margin-left: auto` a `.cg-tile-badge` (mismo recurso que ya usa
`.cg-tile-micro` unas líneas más abajo en el mismo archivo, así que es
consistente con la convención local). Con eso: punto y nombre quedan pegados
por el `gap: 8px`, y el badge se empuja solo al borde derecho. Verificado
visualmente en `web/dist/macro/index.html` tras el build — ver sección de
verificación abajo. También agregué `align-self: center` a `.cg-tile-dot` (en
`dashboard.css`) para que el punto de 8px se centre verticalmente contra el
texto en vez de alinearse arriba (la card usa `align-items: flex-start`,
pensado para que nombres de dos líneas no empujen el badge hacia abajo; tocar
ese `align-items` global habría afectado esa relación nombre/badge sin
necesidad — `align-self` en el punto es un cambio acotado a un solo elemento).

Nada de esto toca cortes de color ni datos: es exclusivamente el layout que
introduce el nuevo elemento.

## Call sites de `semaforoDimension` — inventario completo

Un solo call site en todo `web/src/` (confirmado con
`grep -rn "semaforoDimension" web/src/` antes de borrar):

- `web/src/components/CinturonCard.astro:45` → convertido a `semaforoDe(dim)`.

`tensionDeDimension` (usado en `Evolucion.astro:25` y dentro de
`peorDimension` en `datos.ts`) y `peorDimension` (usado en `Bluf.astro`,
`CinturonCard.astro`, `Recomendaciones.astro`) **no se tocaron** — comparan
tensión entre índices de escala distinta, no son el semáforo.

## Fallback elegido para indicadores sin bloque `semaforo`

Mantuve el `"amarillo"` del brief. Razón: hay dos casos reales donde falta el
bloque —

1. `asistencia_directa` (gestión): deliberadamente fuera del índice, sin
   `aporte_score`, así que `_semaforos()` en `publicar.py` nunca le asigna
   color.
2. Cualquier indicador mientras el snapshot publicado no se haya regenerado
   desde que aterrizó `_semaforos()` (ver nota de datos abajo) — hoy mismo,
   de hecho, todo `web/src/data/informe.json` está en este caso.

En ningún caso "sin dato" debería leerse como certeza (verde = todo bien) ni
como alarma (rojo = crítico); son los dos extremos y ambos serían un mensaje
falso. El tipo `ColorSemaforo` del brief solo admite 4 valores (no hay un
5º "gris/sin dato", y agregar uno rompería el contrato de interfaz del propio
Step 4 y el CSS de las tareas anteriores, que solo definen 4 tokens).
`amarillo` es el escalón intermedio de la escala de 4 — ni la falsa calma de
verde ni la falsa alarma de rojo/naranja — y es coherente con el idioma ya
usado en el proyecto para "dato incierto, no alarmante" (p. ej. `badgeEstado`
usa "Estimación", no un rótulo de alarma, para datos degradados).

## Nota sobre los datos (no es un bug de esta tarea)

`web/src/data/informe.json` tiene `generated_at: 2026-08-06T04:25:29`, que es
ANTERIOR a los commits `72892a1`/`174eed4`/`f93c673`/`3c99d3b`/`2253c13`
(Tasks 1-4, que agregan `_semaforos()` a `publicar.py`). Por eso hoy **ningún**
indicador/dimensión/índice del snapshot tiene bloque `semaforo` — confirmado
leyendo el JSON directamente. Consecuencia visible: el build actual muestra
TODOS los puntos en amarillo (fallback), no colores reales. Esto no es un
defecto de esta tarea — el snapshot se regenera con la corrida normal del
pipeline (`generar_informe.py` → `publicar.py`), que está fuera del alcance
de "la web lee el color" y probablemente es una corrida posterior a estas 8
tareas. Lo dejo documentado para que no se lea como una regresión al mirar la
página antes de la próxima corrida.

## TDD — RED

```
$ python -m pytest tests/test_web_semaforo.py -v -k Ts
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_datos_ts_no_recalcula_el_semaforo FAILED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_ningun_corte_del_semaforo_hardcodeado_en_ts FAILED
AssertionError: semaforoDimension calculaba el color en el cliente; tiene que leer el color publicado
AssertionError: datos.ts: corte hardcodeado >= 95
2 failed, 3 passed in 0.22s
```

(los 3 passed son `TestTokensCss`, ya verdes desde tareas anteriores)

## TDD — GREEN

```
$ python -m pytest tests/test_web_semaforo.py -v
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_tienen_token_y_variante_soft PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_genoma_y_verdict PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_el_punto_del_verdict PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_datos_ts_no_recalcula_el_semaforo PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_ningun_corte_del_semaforo_hardcodeado_en_ts PASSED
5 passed in 0.15s
```

## tsc y build

```
$ cd web && npx tsc --noEmit
(sin salida — limpio)

$ npm run build
...
[build] 81 page(s) built in 3.70s
[build] Complete!
```

Verificación visual del fix de layout, leyendo el HTML generado
(`web/dist/macro/index.html`):

```html
<div class="cg-tile-head">
  <span class="cg-tile-dot sem-amarillo" aria-hidden="true"></span>
  <span class="cg-tile-name">Inflación mensual (IPC)</span>
  <span class="cg-tile-badge auto" title="Actualización automática · dato a 2026-06-01">jun 2026</span>
</div>
```

y el CSS generado incluye `.cg-tile-head { display: flex; align-items:
flex-start; gap: 8px; }` (sin `space-between`) y `.cg-tile-badge { ...
margin-left: auto; ... }`, confirmando que el punto quedó junto al nombre y
el badge empujado al borde.

## Suite completa

```
$ python -m pytest tests -q
...
FAILED tests/test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio
ERROR tests/test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes (teardown)
1 failed, 1944 passed, 3 skipped, 4 warnings, 1 error in 59.20s
```

Exactamente las dos fallas preexistentes indicadas como fuera de alcance;
nada nuevo.

## Archivos cambiados

- `projects/informe_coyuntura/web/src/lib/datos.ts`
- `projects/informe_coyuntura/web/src/components/CinturonCard.astro`
- `projects/informe_coyuntura/web/src/components/IndicadorTile.astro`
- `projects/informe_coyuntura/web/public/dashboard.css`
- `projects/informe_coyuntura/web/public/overrides.css` (divergencia, ver arriba)
- `projects/informe_coyuntura/tests/test_web_semaforo.py`

Commit: `f27e7f3 feat(semaforo): la web lee el color publicado en vez de
recalcularlo` en la rama `semaforo-cuatro-colores` (no `main` — es parte de
la secuencia de 8 tareas de este plan).

`.superpowers/sdd/.gitignore` aparece modificado en el working tree pero NO
se tocó ni se stageó — es un cambio preexistente ajeno a esta tarea (staging
explícito, no `git add -A`, según la regla del repo).

## Self-review

**Completitud**: los 5 pasos del brief están cubiertos; el único call site
real de `semaforoDimension` (confirmado por grep antes de borrar) quedó
convertido; `tensionDeDimension`/`peorDimension` intactos.

**Calidad**: comentarios en castellano, mismo estilo/tono que el resto de
`datos.ts` (explican el "por qué", no solo el "qué"); el fix de
`overrides.css` reutiliza un patrón ya existente en el mismo archivo
(`margin-left: auto`) en vez de inventar uno nuevo.

**YAGNI**: no agregué tipado explícito de `semaforo` a las interfaces
`Indicador`/`DimensionIndice`/`IndiceParametrico` en `datos.ts` — `tsc
--noEmit` pasa limpio sin eso porque ni `Astro.props` (sin `interface Props`
declarada) ni los `any` explícitos de `CinturonCard.astro` (`[string, any][]`
para `dims`) fuerzan ese chequeo. Es una decisión consciente de no ampliar el
contrato de tipos más allá de lo que esta tarea necesita; lo señalo porque
Task 6 (la tabla de tramos) probablemente sí va a querer `ind.semaforo.
umbrales` tipado en vez de `any` — juicio de esa tarea, no de esta.

**Accesibilidad**: el punto lleva `aria-hidden="true"`; el color nunca es el
único portador — el valor numérico de la card (`headline`) se muestra
siempre, independiente del color, y el `título` (`por_que`) queda disponible
como tooltip cuando el snapshot lo trae. No agregué el texto de `por_que`
como contenido visible/accesible por lector de pantalla más allá del
`title` — asumo que esa exposición más completa es del alcance de la ficha
modal (Task 6/7), no de la card compacta de esta tarea.

## Concerns

- El fallback "amarillo" hoy se ve en el 100% de los indicadores porque el
  snapshot publicado es anterior a `_semaforos()` (ver nota de datos arriba).
  No es una regresión de esta tarea, pero conviene que quien mire la rama en
  el navegador antes de una corrida de pipeline no lo lea como un bug.
- El fix de `overrides.css` no estaba en el alcance nominal del brief
  (`web/src/lib/datos.ts`, `CinturonCard.astro`, `IndicadorTile.astro`,
  `tests/test_web_semaforo.py`). Lo agregué porque sin él el punto rompe
  visualmente el head de cada card — lo marco explícitamente por si se
  prefiere revisarlo aparte.

---

## Fix — ronda 1 (revisión del coordinador)

La revisión aprobó el spec y el fix de `overrides.css` (verificado de forma
independiente: la rotura de flexbox era real, `.cg-tile-head` no tiene otro
consumidor, y `margin-left: auto` es la convención ya usada en el archivo).
Marcó dos hallazgos **Important**, los dos originados en el propio brief, no
en mi implementación.

### Hallazgo 1 — el fallback "amarillo" inventa una señal

`asistencia_directa` (TDPS) está al 100%, fuera del índice por saturado —
ADR-0100 lo describe como una promesa cumplida, "una noticia que hay que
dar". Pintarle un punto amarillo (el fallback de `semaforoDe` cuando falta
`semaforo`) lo hace indistinguible de un indicador con tensión real
4-a-6/10 en la misma pantalla: un logro leído como mediocridad, y sin forma
de que el usuario note la diferencia a simple vista.

**Fix aplicado** (`web/src/components/IndicadorTile.astro`): el contrato de
`semaforoDe` NO se tocó — sigue devolviendo uno de los 4 colores, nunca un
5º valor "sin dato". El gate se movió al render: el punto solo se pinta si
`ind.semaforo?.color` existe.

```ts
// semaforoDe() no distingue "sin dato" de un color real (su contrato son
// 4 colores, no 5) — por eso el gate va acá, en el render: sin bloque
// `semaforo` publicado no hay punto, en vez de pintar uno que el indicador
// no se ganó. Le pasa a asistencia_directa (TDPS 100%, fuera del índice por
// saturado — ADR-0100): amarillo ahí leería "tensión media" sobre un logro.
const color = ind.semaforo?.color ? semaforoDe(ind) : null;
```

```astro
{color && <span class:list={["cg-tile-dot", `sem-${color}`]} title={ind.semaforo?.por_que ?? undefined} aria-hidden="true"></span>}
```

También actualicé el comentario de `semaforoDe` en `datos.ts` para dejar
explícito que su fallback interno no es una recomendación de pintado — es
responsabilidad del llamador chequear `x.semaforo?.color` antes de decidir
si corresponde mostrar algo.

No se tocó `CinturonCard.astro`: cada dimensión de un índice recibe su
bloque `semaforo` sin excepción en `_semaforos()` (macro/gestión/política/
vida cotidiana), así que ese call site no tiene el mismo riesgo — no hay
ninguna dimensión hoy, ni prevista, que quede sin color asignado.

**Esto no se resuelve solo en Task 8.** `_semaforos()` en `publicar.py`
sigue sin asignarle bloque a `asistencia_directa` después de que el
snapshot se regenere — sus condiciones de rama no cambian (no está en el
índice, no tiene `aporte_score`). El indicador va a seguir sin punto
indefinidamente, por diseño: es lo correcto, no un pendiente.

Verificado en el build (`web/dist/gestion/index.html`): `asistencia_directa`
no tiene `<span class="cg-tile-dot...">` en su `cg-tile-head`; los demás
indicadores del cinturón tampoco lo tienen HOY, pero por la razón ya
documentada (snapshot anterior a `_semaforos()`, ningún indicador trae
`semaforo` todavía) — no por un bug del gate. El gate en sí se comprueba
correcto porque la ausencia de bloque en asistencia_directa y en el resto
del snapshot actual se trata igual (sin punto), que es exactamente lo que
tiene que pasar cuando no hay dato.

### Hallazgo 2 — el test de cortes hardcodeados tenía un agujero

La lista `(">= 95", ">= 90", ">= 105", ">= 85")` solo cubría los cortes del
ITVC base-100. Los cortes 60/40/20 de la escala 0-100 (ITCM, ITCG, ITCP) —
la que de hecho usaba la rama `if (base100) ... else ...` de
`semaforoDimension` para TRES de los cuatro cinturones paramétricos — no
estaban en la lista. La propia línea original de `semaforoDimension`,
`puntaje >= 60 ? "verde" : puntaje >= 40 ? "amarillo" : "rojo"`, no
contiene ningún `>= 9x`: el test nunca la habría atrapado.

**Fix aplicado** (`tests/test_web_semaforo.py`): reemplacé
`test_ningun_corte_del_semaforo_hardcodeado_en_ts` por
`test_ningun_ts_deriva_el_color_de_un_numero`, que verifica el invariante
real en vez de enumerar cortes conocidos: ninguna línea de ningún `.ts` bajo
`web/src/lib/` puede nombrar un color del semáforo (`verde`/`amarillo`/
`naranja`/`rojo`) Y contener una comparación numérica (`<`, `<=`, `>`, `>=`
junto a un dígito) en la misma línea.

```python
def test_ningun_ts_deriva_el_color_de_un_numero(self):
    color = re.compile("|".join(COLORES))
    comparacion_numerica = re.compile(r"[<>]=?\s*\d|\d\s*[<>]=?")
    for archivo in LIB.glob("*.ts"):
        for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            if color.search(linea) and comparacion_numerica.search(linea):
                raise AssertionError(
                    f"{archivo.name}:{n}: el color se deriva de una "
                    f"comparación numérica en el cliente — {linea.strip()!r}")
```

Confirmé que no rompe con `verdictDeCinturon` (el otro mapeo legítimo de
colores en `datos.ts`, que sigue vivo a propósito): compara strings
(`estado === "estable"`), sin ningún `<`/`>`/dígito en la misma línea — no
dispara el test. No hubo que debilitar nada para que pase.

**Prueba de que el test tiene dientes** — reintroduje temporalmente una
derivación numérica del lado del cliente en `datos.ts`, dentro de
`semaforoDe`:

```ts
const _teeth_check = p >= 60 ? "verde" : "amarillo";
```

```
$ python -m pytest tests/test_web_semaforo.py -v -k deriva
FAILED tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_ningun_ts_deriva_el_color_de_un_numero
AssertionError: datos.ts:191: el color se deriva de una comparación numérica
en el cliente — 'const _teeth_check = p >= 60 ? "verde" : "amarillo";'
1 failed, 4 deselected in 0.61s
```

Revertido exactamente esa línea (la única línea insertada) y confirmado con
`git diff` que `datos.ts` solo conserva el cambio real de esta ronda (el
comentario ampliado de `semaforoDe`) — sin restos del check.

### Verificación tras el fix

```
$ python -m pytest tests/test_web_semaforo.py -v
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_tienen_token_y_variante_soft PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_genoma_y_verdict PASSED
tests/test_web_semaforo.py::TestTokensCss::test_los_cuatro_colores_pintan_el_punto_del_verdict PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_datos_ts_no_recalcula_el_semaforo PASSED
tests/test_web_semaforo.py::TestSinCortesDuplicadosEnTs::test_ningun_ts_deriva_el_color_de_un_numero PASSED
5 passed in 0.53s

$ cd web && npx tsc --noEmit
(sin salida — limpio)

$ npm run build
...
[build] 81 page(s) built in 16.40s
[build] Complete!

$ python -m pytest tests -q
FAILED tests/test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio
ERROR tests/test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes (teardown)
1 failed, 1944 passed, 3 skipped, 4 warnings, 1 error in 146.61s
```

Las mismas dos fallas preexistentes señaladas como fuera de alcance; nada
nuevo.

### Archivos tocados en esta ronda

- `projects/informe_coyuntura/web/src/lib/datos.ts` (comentario de
  `semaforoDe` ampliado — el contrato de la función no cambió)
- `projects/informe_coyuntura/web/src/components/IndicadorTile.astro`
  (gate de render)
- `projects/informe_coyuntura/tests/test_web_semaforo.py` (test reemplazado)

`.superpowers/sdd/.gitignore` sigue apareciendo modificado en el working
tree y sigue sin tocarse ni stagearse — no es mío.
