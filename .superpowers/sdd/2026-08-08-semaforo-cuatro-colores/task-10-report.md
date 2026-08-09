# Task 10 — Reporte: ADR-0181 pasa de "pendiente declarado" a "resuelto en esta rama"

Commit: `c8e4266` — `docs(adr): 0181 registra el bug de verdictDeCinturon como resuelto, no pendiente`

## Qué cambié y dónde lo puse

Archivo: `projects/informe_coyuntura/docs/adr/0181-el-color-es-la-tension-que-ya-se-publica.md`.

Reescribí el bloque de `### Consecuencias` que empezaba con **"HONESTIDAD
SOBRE EL EFECTO..."** (era el párrafo que declaraba el bug de
`verdictDeCinturon` como preexistente y "fuera de alcance a propósito").
Lo dejé en el mismo lugar (`### Consecuencias`) porque sigue siendo
exactamente eso — una consecuencia real del trabajo de este ADR, sólo que
ahora con desenlace en vez de en suspenso. Moverlo a otra sección hubiera
separado la causa (el semáforo lo hizo visible) del efecto (se arregló acá
mismo), que es justamente el hilo que vale la pena que quede junto.

El reemplazo son cuatro párrafos:

1. **Qué era el bug** — mismo contenido factual que antes (comparaba contra
   `"critico"`/`"alerta"`, valores que `_estado()` nunca emite;
   `cinturonesRojos` estructuralmente 0), sin cambios de fondo porque esa
   parte seguía siendo cierta.
2. **Que se arregló, cuándo y con qué commits** — `f333b0c` (la comparación)
   y `29d698e` (el test con dientes reales + el BLUF), dos commits después
   de que este mismo ADR lo dejara anotado como pendiente.
3. **Por qué entraba en el alcance de un cambio de presentación** — el punto
   que me pareció más importante justificar con evidencia, no sólo afirmar:
   `generar_informe.py:192` ya pintaba `tensionado` de rojo desde antes de
   este ADR, así que alinear la web no fue una decisión editorial nueva, fue
   corregir la réplica que estaba desincronizada. Nada de `UMBRALES`, bandas
   ni scores cambió — verificable en el propio diff de `f333b0c`.
4. **El bug latente de `Bluf.astro`** — la mitad que pedías destacar como la
   más interesante: una rama que jamás se había ejecutado en producción
   porque `rojos.length > 0` nunca había sido cierto hasta este branch. La
   describo con la causa exacta (mayúscula hardcodeada asumiendo que la
   cláusula de `masTenso` siempre iba a ser la primera) y el efecto textual
   real (`"...en zona crítica; Con una tensión global..."`) tal como lo
   documentó `29d698e`.

También agregué una aclaración de una línea al final del párrafo
`**verdictDeCinturon(estado) NO se unificó, y es deliberado.**` (sección "Dos
consecuencias que aparecieron implementando", más abajo en el mismo ADR) para
que no se lea como contradictorio con lo de arriba: ese pasaje sigue vigente
tal cual estaba — es sobre si conviene **fusionar dos conceptos** (chip de
3 colores vs. semáforo de índice de 4), que sigue pendiente y no tiene nada
que ver con el bug de vocabulario ya cerrado.

## Otros pasajes revisados en 0181/0182/0183

- **0181, Confirmación — "26 tests"**: quedó desactualizado. Conté los tests
  reales de los tres archivos (`test_semaforo.py` + `test_publicar_semaforo.py`
  + `test_web_semaforo.py`) con
  `pytest --collect-only -q` y dan **28**, no 26 — el fix de esta rama sumó
  2 tests nuevos (`TestVerdictDeCinturonConoceElVocabularioDeEstado`) al
  mismo archivo. Actualicé el número a 28, aclaré que 26 son de la decisión
  original del ADR y 2 del fix descripto arriba, y agregué un bullet nuevo a
  la lista describiendo qué verifican esos 2 tests. No los fusioné con los
  bullets existentes porque verifican un concepto distinto (el chip de
  3 colores del cinturón, no el semáforo de 4 colores de índices).
- **0181, "Dos consecuencias que aparecieron implementando"**: revisado
  completo — sigue siendo válido sin cambios de contenido, sólo la
  aclaración de una línea mencionada arriba para evitar que se lea como
  contradicho por el pasaje de Consecuencias.
- **0182 (umbrales del semáforo)**: grep de `verdictDeCinturon|critico|
  alerta|cinturonesRojos|Bluf` sobre el archivo completo → sin resultados.
  Leí el archivo entero igual (no sólo el grep) para confirmar que ninguna
  otra afirmación depende del estado de `verdictDeCinturon`. No hay nada
  que tocar.
- **0183 (rediseño del cinturón político)**: mismo grep, mismo resultado
  vacío. Leí el archivo completo — es sobre el ITCP propuesto por CIGOB, no
  toca el chip de estado del cinturón ni el semáforo de 4 colores. Sin
  cambios.

## `archivos` del frontmatter

Lo cambié. Antes:
```
archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/lib/datos.ts']
```
Ahora agrego `'web/src/components/Bluf.astro'`:
```
archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/components/Bluf.astro']
```

Razón: `Bluf.astro` cambió de verdad por causa de este ADR (el bug que
describe expuso ese archivo), y ya estaba `datos.ts` en la lista aunque el
ADR no lo tocó en su commit original — el precedente en este mismo archivo
es "listar el código de producción que el ADR describe", no sólo "el código
que cambió en el commit fundacional". `tests/test_web_semaforo.py` NO lo
agregué: reviso otros ADR del repo (`0181` ya excluía tests pese a
depender fuertemente de ellos en Confirmación; otros como `0009`/`0010` sí
listan `'tests/'` genérico) y el precedente más cercano —el propio 0181— ya
había elegido no listar tests, así que seguí esa misma convención en vez de
inventar una nueva a mitad de documento.

## Verificación

```
python scripts/adr_coherencia.py
```
```
Aplicado:
  relaciones inversas escritas: 0
  ADR marcados como superados:  0
  filas del índice:             183
```
Sin cambios al índice (`docs/adr/README.md` no aparece en `git status`) —
esperable, porque no toqué frontmatter de relaciones (`relacionado`,
`continuado_por`, `continua`), sólo `archivos` y prosa.

```
python -m pytest tests/test_adr_format.py -q
```
```
1101 passed in 8.82s
```

Suite completa, para confirmar que no rompí nada fuera del scope de
documentación:
```
python -m pytest tests -q
```
```
1 failed, 1952 passed, 3 skipped, 4 warnings, 1 error in 59.10s
```
Los mismos dos fallos preexistentes que el brief marca como ajenos:
- `tests/test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
  (`assert -2.0 == -1.07`)
- error de teardown en
  `tests/test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes`

Nada nuevo falló.

## Archivos cambiados

- `projects/informe_coyuntura/docs/adr/0181-el-color-es-la-tension-que-ya-se-publica.md`
  (único archivo tocado — prosa y frontmatter `archivos`, nada de código).

No toqué `.superpowers/sdd/.gitignore`, que ya aparecía modificado en
`git status` al empezar esta tarea (ajeno a este cambio) — lo dejé intacto y
sin stagear, y no lo incluí en ningún commit.

## Concerns

- Ninguno bloqueante. Juicio de diseño documentado arriba: dejé el pasaje en
  `### Consecuencias` en vez de moverlo, mantuve `docs/adr/README.md` sin
  tocar (se regenera solo y no cambió), y no agregué `tests/` al frontmatter
  siguiendo la convención que el propio ADR-0181 ya había fijado.
