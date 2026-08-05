# Tarea de seguimiento — ITCP nunca llegó al pipeline público (informe_coyuntura)

Rama: `feature/itcp-cohesion-bloque-politica`
Commit: `da3b85c` — "fix(politica): conecta el ITCP al pipeline público — publicar.py, generar_informe.py y datos.ts nunca se enteraron del índice"

## Resumen ejecutivo

El motor ITCP (`scripts/itcp.py`) y su cálculo en `scripts/politica.py::main()`
ya existían y estaban probados a nivel unitario, pero **tres eslabones reales
del pipeline público seguían ciegos al índice**:

1. `scripts/generar_informe.py::construir_informe()` solo reenviaba
   `("itcm", "itcg")` del cache al informe — nunca `"itcp"`.
2. `scripts/publicar.py::aplicar_scoring()` no tenía rama `politica` → caía
   al promedio simple legacy (dict `SCORING`).
3. **Hallazgo adicional no anticipado en el brief**: `politica.py::main()`
   tampoco anotaba cada indicador con `en_indice`/`dimension`/`puntaje_itcp`/
   `peso_efectivo` — el paso que `gestion.py::anotar_indicadores()` sí hace
   para el ITCG. Sin esa anotación, `_scoring_indice()` en `publicar.py`
   no tenía nada que enriquecer: aunque se agregara la rama `politica`, todos
   los `aporte_score` habrían quedado en `None`. Verificado por grep (cero
   matches de `en_indice`/`puntaje_` en `politica.py` antes del fix) y
   confirmado con el advisor antes de tocar código — no es un caso del
   "itcp.py no matchea la interfaz", es un paso entero ausente en
   `politica.py`, análogo a `gestion.py` pero nunca escrito.

## Root cause de `test_publicar_genera_snapshot` (el que pedía investigar)

El assert que fallaba (`"desactualizado" in ind`) apuntaba a **dos**
indicadores de política: `adhesion_reformas_provincial` y
`cohesion_bloque_senado`. Sus fetchers (`fetch_adhesion_reformas_provincial`,
`fetch_cohesion_bloque_senado`, ambos nuevos en este mismo plan ITCP, commits
`16d54b4` y `7e1002b`) devuelven su dict de resultado **sin la clave
`"desactualizado"`** — a diferencia de todos los demás fetchers de
`politica.py`, que siempre la incluyen (constante `False` o calculada). En
`main()`, cuando el fetch es fresco estos dicts se guardan tal cual
(`frescos[nombre] = resultado`), así que la clave faltante viaja intacta
hasta `informe.json` → `web/src/data/informe.json`.

**Fix**: agregar `"desactualizado": False` al `return` de ambas funciones
(mismo patrón que `ratio_dnu`, `iaf_transferencias`, etc. en el mismo
archivo). No relacionado con el forwarding del ITCP — es un bug de forma
independiente que el nuevo test de snapshot atrapó porque exige la forma
mínima en TODOS los indicadores publicados, de cualquier cinturón.

## Cambios (Parte A — Python)

- `scripts/politica.py`:
  - `desactualizado: False` agregado a `fetch_cohesion_bloque_senado()` y
    `fetch_adhesion_reformas_provincial()`.
  - Nueva función `_anotar_indicadores_itcp(indicadores, resultado)` (mismo
    patrón que `gestion.py::anotar_indicadores`), llamada en `main()` justo
    después de `itcp.calcular_itcp()` y antes de armar `payload`. Marca cada
    indicador con `en_indice`, `dimension`, `puntaje_itcp`, `puntaje_banda`,
    `peso_efectivo`. A diferencia del ITCG, el ITCP no declara indicadores de
    contexto (`itcp.py` no tiene `INDICADORES_CONTEXTO`), así que la rama
    `else` es simplemente `en_indice = nombre in itcp.BANDAS_ITCP`.

- `scripts/publicar.py`:
  - `import itcp` agregado junto a `itcm`/`itcg`/`itvc`.
  - `POLITICA_CONTEXTO` agregada (sin uso activo hoy — los 12 indicadores
    puntúan, ninguno es contexto puro; mismo patrón que las otras 3).
  - `_politica_input_txt(ikey, ind)`: fallback genérico a `detalle_txt`, más
    dos descomposiciones puntuales (`adhesion_reformas_provincial` → cuenta
    de provincias; `cohesion_bloque_senado` → cantidad de actas).
  - Rama `if ckey == "politica": _scoring_indice(c, "itcp", itcp,
    POLITICA_CONTEXTO, _politica_input_txt); continue` agregada en
    `aplicar_scoring()`, en la misma posición que macro/gestión/vida.
  - Se retiró el bloque `# ── política ──` (9 entradas) del dict `SCORING`:
    quedaba inalcanzable desde que se agregó la rama `politica` (mismo
    criterio ya aplicado a macro cuando se agregó ITCM — el comentario del
    dict ya documentaba esa convención).
  - `SCORE_EXPLICACION["politica"]` actualizado: de "promedio simple" a la
    descripción del ITCP con sus 5 pesos de dimensión.

- `scripts/generar_informe.py`: `for indice in ("itcm", "itcg"):` →
  `for indice in ("itcm", "itcg", "itcp"):`.

## Cambios (tests)

- `tests/test_publicar.py`:
  - Se retiró `test_aporte_score_reconcilia_con_score_publicado` (su
    docstring decía "solo política queda como promedio simple", premisa ya
    falsa). No se repurpuseó a `espiritu_epoca` porque
    `test_espiritu_epoca_presente_y_coherente` ya reconciliaba ese cinturón
    de forma explícita (línea 42 de ese test) — mantenerlo habría sido
    duplicado.
  - Se agregó `test_politica_itcp_reconcilia()`, mismo patrón que
    `test_gestion_itcg_reconcilia()`: 12 indicadores en el índice (verificado
    en vivo, no asumido), 0 de contexto, suma ponderada de
    `puntaje_itcp × peso_efectivo` reconcilia con `itcp.valor` (±0.15), score
    del cinturón = `(100-ITCP)/10` (±0.05), pesos de dimensión
    `{"poder_legislativo": 0.30, "alianzas_territoriales": 0.25,
    "cohesion_interna": 0.20, "conflicto_social": 0.15, "imagen_voto": 0.10}`
    (verificados contra `itcp.py::DIMENSIONES_ITCP` directamente), y cada
    indicador del índice con `aporte_score` reconciliando individualmente.

## Cambios (Parte B — web)

- `web/src/lib/datos.ts`:
  - `Indicador.puntaje_itcp?: number` agregado a la interfaz.
  - `Cinturon.itcp?: IndiceParametrico` agregado.
  - `indiceDe()`: rama `if (c.itcp) return {...}` agregada, mismo patrón que
    ITCM/ITCG/ITVC (sigla "ITCP", descripción con los 5 pesos, sin
    `base100`).

- **Efecto secundario descubierto al regenerar y correr `npm run build`** (no
  estaba en el brief, encontrado por inspección del HTML generado):
  `web/src/pages/[slug].astro` calculaba `cruz` (la matriz de validación
  cruzada ITCM/ITCG/ITVC) con la condición `indice ? validacion_cruzada :
  null` — al volverse `indice` verdadero para política, la matriz (que NO
  incluye una fila ITCP) se filtraba a la página de política sin ninguna fila
  resaltada como "este cinturón". Fix: `cruz` ahora solo es no-nulo si
  `cruzRaw.filas` tiene una entrada con `indice === indice.sigla`. Verificado
  en el HTML generado: `grep cg-cruz-tabla` da 0 en `/politica/` y 1 en
  `/macro/`.
  - `web/src/components/Metodologia.astro` (portada): el chip "Índices"
    tenía hardcodeado `3` y el texto "ITCM, ITCG e ITVC; política y espíritu
    promedian sus tensiones" — ahora falso (política ya no promedia). Se
    cambió a `{indices.length}` (dinámico, da 4) y el texto a "ITCM, ITCP,
    ITVC e ITCG; solo espíritu de época promedia su tensión."
  - `web/public/overrides.css`: faltaba `.cg-met-ind--politica { --ind-c:
    var(--c-politica); }` (las otras 3 cinturones sí tenían su regla) — sin
    esto la card de ITCP en la portada caía al color de fallback (teal) en
    vez del rojo de política.
  - `web/src/pages/metodologia/index.astro`: encabezado hardcodeado "Los
    tres índices del informe" → "Los índices del informe" (la lista de
    índices ya es dinámica vía `indices.map`, solo el texto estaba fijo).
    No se tocó la ficha metodológica completa de ITCP (no existe en
    `fichas.ts` — está fuera de alcance de esta tarea; la fila del
    diccionario para ITCP queda correctamente en estado "Ficha en
    preparación", sin link, reflejando la realidad).

## Verificación end-to-end

Pipeline corrido en vivo, en orden: `politica.py` → `generar_informe.py` →
`publicar.py`. `web/src/data/informe.json → cinturones.politica`:
- `itcp.valor = 64.7`, `banda_legible = "Moderadamente aflojado"`.
- `itcp.robustez` presente (Monte Carlo, p05=62.5, p95=67.6).
- Las 5 dimensiones con pesos 0.30/0.25/0.20/0.15/0.10 y flag `critica`
  (ninguna crítica en esta corrida).
- Los 12 indicadores con `en_indice=true`, `puntaje_itcp`, `aporte_score`,
  `aporte_formula` poblados (no None) — ejemplo: `votometro_ventaja_lla`
  aporte_score=2.4, `veto_quorum` aporte_score=0.0 (puntaje pleno).

`npm run build`: **pasa**, 64 páginas generadas, incluida `/politica/` y las
12 fichas de indicador de política (`/metodologia/cohesion_bloque_senado/`,
etc.). Verificado en el HTML generado (`web/informe/` fuera del repo, según
`astro.config.mjs`):
- `/politica/index.html`: contiene los chips de dimensión ITCP y la sección
  de robustez; NO contiene la matriz de validación cruzada (correcto).
- `/macro/index.html`: sí contiene la matriz (control, no regresionó).
- `/index.html` (portada): chip "Índices" muestra `4`; 4 cards
  (`cg-met-ind--macro/politica/vida/gestion`), la de política con su color.
- `/metodologia/index.html`: encabezado corregido, fila ITCP presente con
  "Ficha en preparación".

## Test suite

- **Antes** (baseline limpio, antes de cualquier cambio):
  `tests/test_publicar.py` → 2 failed, 9 passed
  (`test_publicar_genera_snapshot`, `test_aporte_score_reconcilia_con_score_publicado`).
- **Después**: `tests/` completo (93 tests, todos los archivos) → **93
  passed**, sin regresiones. Incluye `test_itcg.py`, `test_itcm.py`,
  `test_itcp.py`, `test_itvc.py`, `test_politica_cohesion.py`,
  `test_publicar.py`.

## Higiene del working tree / staging

El tree tenía trabajo ajeno en curso (feature "motos", caches de
macro/gestión/vida/espíritu ya modificados por otros agentes de este mismo
plan, `scripts/descargar_series.py` y `scripts/gestion.py` modificados,
`tests/test_itcg.py` modificado, `docs/superpowers/plans/...` modificado,
`data/vida/motos_serie.json` sin trackear). Se verificó por **mtime de cada
archivo** (no solo `git diff`) cuáles fueron tocados específicamente por mis
comandos vs. cuáles ya estaban sucios antes de empezar:

- Cachés de macro/gestión/vida_cotidiana/espíritu_época (`output/cache/*.json`,
  `output/series/{gestion,macro,vida_cotidiana}.csv`,
  `output/{interpolacion_sombra,sensibilidad,validacion_externa}.json`,
  `data/gestion/*.json`, `data/vida/*.json` salvo lo tocado por mi corrida de
  `politica.py`): mtime **anterior** a mi sesión → NO tocados por mí, NO
  stageados.
- `data/gestion/protestas_caba.json`: SÍ tocado por mi corrida de
  `politica.py` (refresco en vivo del cache ACLED que comparte con
  `gestion.py`) — pero es un cache compartido fuera del alcance explícito de
  esta tarea; se deja sin stagear (queda modificado en el working tree, no
  en el commit).
- `data/historico/indicadores.json`: tocado por mi corrida de `publicar.py`,
  pero su diff mezcla entradas nuevas de política (legítimas) con valores
  de `cepo_mulc`/`rem_ipc_12m`/`sentimiento_digital` que vienen de los
  caches YA sucios de otros cinturones (no tocados por mí) — se decidió
  **no stagear** para no mezclar cambios ajenos en el commit, aunque el
  archivo queda actualizado en disco.

**Staged y commiteado** (commit `da3b85c`, 14 archivos): `scripts/publicar.py`,
`scripts/generar_informe.py`, `scripts/politica.py`, `tests/test_publicar.py`,
`web/src/lib/datos.ts`, `web/src/pages/[slug].astro`,
`web/src/components/Metodologia.astro`, `web/src/pages/metodologia/index.astro`,
`web/public/overrides.css`, `output/cache/politica.json`, `output/informe.json`,
`output/informe.md`, `web/src/data/informe.json`, `web/src/data/series.json`.

No se hizo push (no solicitado explícitamente en esta tarea de seguimiento).

**Nota importante sobre los snapshots commiteados**: `output/informe.json`,
`output/informe.md`, `web/src/data/informe.json` y `series.json` son una
reconstrucción de **pipeline completo** (`generar_informe.py` copia el bloque
`indicadores` de los 5 caches tal cual) — no un diff aislado de política.
Como las cachés de macro/gestión/vida/espíritu ya estaban sucias (de otro
trabajo en curso, no mío) antes de mi corrida, el commit `da3b85c` incluye
también el estado *actual* (no commiteado en su propio archivo de cache) de
esos 4 cinturones dentro de los snapshots agregados — mientras que, a
propósito, dejé sus archivos de cache fuente (`output/cache/{macro,gestion,
vida_cotidiana,espiritu_epoca}.json`) sin stagear. Revisé el diff completo de
`informe.json` entre este commit y el anterior: los cambios ajenos a
política son todos refrescos de valores en vivo (IPC, ITCM, etc.) de
magnitud chica y con forma sana — nada a medio escribir (verifiqué en
particular que no hay ninguna entrada relacionada a "motos"/patentamiento,
que es la feature en curso mencionada en la higiene del working tree). Si se
prefiere un commit de datos más aislado, habría que o bien pedirle a los
otros agentes que comiteen primero sus caches, o descartar los snapshots
agregados de este commit y dejar que se regeneren en la próxima corrida
completa del pipeline.

## Autorevisión

- Ambos fallos originales confirmados arreglados; suite completa en verde
  (93/93), sin nuevos fallos.
- `test_politica_itcp_reconcilia` ejercita reconciliación real: suma
  ponderada de puntajes contra el ITCP publicado, fórmula de tensión,
  pesos de dimensión verificados contra `itcp.py` (no copiados a ciegas del
  brief — de hecho coincidían exactamente), y aporte por indicador
  individual — no es un sello de goma.
- Cambio de `datos.ts` verificado contra el archivo real (`indiceDe()` leído
  completo antes de editar) y contra el HTML generado por `npm run build`,
  no solo por inspección de tipos.
- `npm run build` pasa limpio.

## Concerns / decisiones que el usuario podría querer revisar

1. **Alcance ampliado respecto del brief**: el brief afirmaba que "el wiring
   en `politica.py`'s main()/cache" ya estaba hecho — no lo estaba a nivel de
   anotación por indicador. Se agregó `_anotar_indicadores_itcp()` (no
   pedida explícitamente, pero indispensable para que el resto de la tarea
   funcionara — confirmado con el advisor antes de escribir código).
2. **Fix de `cruz` en `[slug].astro`**: no estaba en el brief; se descubrió
   inspeccionando el HTML generado. Es un fix mínimo y quirúrgico (una
   condición extra), pero es una decisión de producto menor (ocultar la
   matriz en vez de, por ejemplo, mostrarla igual sin resaltar fila) que
   vale la pena que el editor confirme.
3. **`data/gestion/protestas_caba.json`** quedó modificado en disco (refresco
   real de ACLED) pero sin stagear — si se quiere ese refresco de datos en
   el commit, hay que agregarlo a mano.
4. **Ficha metodológica completa de ITCP** (para `/metodologia/itcp/`) no
   existe todavía — deliberadamente fuera de alcance (redactar la ficha
   completa con fuente/transformaciones/limitaciones es trabajo editorial
   sustancial, no wiring). La fila del diccionario lo refleja correctamente
   ("Ficha en preparación").
5. No se creó `_validacion_itcp` (explícitamente fuera de alcance según el
   brief) — el chip "Validación externa" de la portada sigue mencionando
   solo ITCM/ITCG/ITVC, lo cual sigue siendo cierto.
