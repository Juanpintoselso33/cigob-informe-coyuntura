# Task 3 report — Publicar el semáforo en el snapshot

## Qué se implementó

`scripts/publicar.py` ahora importa `parametrica` y define, cerca de las demás
funciones de scoring (justo antes de `aplicar_scoring`, línea ~1709):

- `_ESCALAS_SEMAFORO`: mapa cinturón → (clave del índice, módulo, sigla) para
  macro/gestión/política (los tres con paramétrica por bandas).
- `_INDICE_DE_CINTURON`: mapa cinturón → clave del bloque de índice que cuelga
  de él (`itcm`/`itcg`/`itcp`/`itvc`), usado para el semáforo del índice y sus
  dimensiones.
- `_escala_de(mod, sigla)`: arma un `parametrica.Escala` desde `BANDAS_*` /
  `ANCLAS_*` / `TRANSFORMACIONES_*` del módulo (con `getattr(..., None)` para
  ITCG/ITCP, que no declaran anclas ni transformaciones).
- `_por_que(color, valor, unidad, tramos)`: genera (no escribe) la frase que
  explica el color, con la misma convención de borde del motor.
- `_semaforo_de(...)`: arma el dict `{color, tension, umbrales, unidad, por_que}`.
- `_semaforos(informe)`: recorre cada cinturón, calcula la tensión sin
  redondear desde el dato más crudo disponible por rama (puntaje 0-100 para
  ITCM/ITCG/ITCP, `indice_itvc` para vida cotidiana, `aporte_score` solo para
  espíritu de época), la adjunta a cada indicador, y hace lo mismo para el
  índice del cinturón y cada una de sus dimensiones.

Llamada desde el final de `aplicar_scoring`, inmediatamente antes de su
`return informe` (línea ~1895).

## Divergencias del código del brief, con motivo

**1. Colores del índice/dimensión vía las funciones públicas, no reimplementando
la fórmula.** El brief calculaba `tension = (100-p)/10` (o la fórmula base-100)
a mano y después llamaba `color_de_tension(tension)`. Cambié las tres ramas del
loop por indicador para llamar directamente a `parametrica.color_de_puntaje(p)`
/ `parametrica.color_de_indice_base100(idx100)` — funciones ya testeadas en
`test_semaforo.py` que hacen exactamente esa cuenta puertas adentro. Sigo
necesitando `tension` sin redondear para el campo `tension` del payload (no hay
wrapper público que la devuelva junto con el color), así que esa parte del
cálculo se mantiene duplicada — pero el **color**, que es lo que puede romper
un borde, ya no depende de dos copias de la misma fórmula quedando en sync a
mano. Motivo: `color_de_tension(manual)` y `color_de_puntaje` son la misma
cuenta escrita dos veces; si mañana cambia una sin la otra, el color se
desincroniza en silencio. No es una corrección de un bug (ambas daban el mismo
resultado en todos los casos que probé) — es cerrar ese riesgo antes de que
exista.

**2. `base100` por mapa explícito, no por identidad de objeto.** El brief
detectaba si un índice era base-100 así:
```python
indice = bloque.get(clave) if clave else bloque.get("itvc")
base100 = "itvc" in bloque and indice is bloque.get("itvc")
```
Lo reemplacé por `_INDICE_DE_CINTURON` (cinturón → clave del índice) y
`color_idx = color_de_indice_base100 if indice_key == "itvc" else color_de_puntaje`.
Verifiqué que el original no era incorrecto hoy: dado que solo vida_cotidiana
tiene clave `None` en `_ESCALAS_SEMAFORO` y solo su bloque contiene la llave
`"itvc"`, la expresión se reducía en la práctica a `clave is None and "itvc" in
bloque`. Pero es un mecanismo indirecto (identidad de objeto + presencia de
llave) para expresar algo que es, en realidad, una relación cinturón→tipo de
índice — un mapa explícito lo dice directo y no depende de que ningún otro
cinturón adquiera una llave `"itvc"` el día de mañana. Confirmé con los datos
reales que ambas versiones producen el mismo resultado en los 4 índices
(ITCM/ITCG/ITCP verdes por `color_de_puntaje`, ITVC naranja por
`color_de_indice_base100`, dimensiones de cada uno coherentes con su propia
fórmula — el ITVC en particular tiene dimensiones en escala base-100, no
puntaje 0-100: confirmado leyendo `itvc['dimensiones']` del snapshot, valores
como `vulnerabilidad: 17.2`, imposibles en una escala de puntaje 0-100 sana).

**3. Tramo-membresía en `_por_que` y en el test: sin cambios, porque ya estaban
bien.** El brief pedía escrutinar esto explícitamente. Repasé
`parametrica.puntaje_banda` (`low < valor <= high`, documentado como la
convención del motor) contra la membresía usada en `_por_que` y en
`test_los_umbrales_contienen_el_valor_vigente`:
```python
(t["desde"] is None or valor > t["desde"]) and (t["hasta"] is None or valor <= t["hasta"])
```
Es low-exclusivo / high-inclusivo, la misma convención. No encontré una
inconsistencia real — dejé el código del brief tal cual y solo agregué una
línea al docstring de `_por_que` y al docstring del test señalando
explícitamente la convención, para que quede escrita y no dependa de que
alguien la vuelva a derivar mirando `puntaje_banda`.

**Nada de lo anterior cambia ningún resultado observable**: verificado
comparando color-por-color y valor-por-valor entre una versión con la
identidad-de-objeto del brief y la versión final con el mapa explícito, sobre
el snapshot regenerado completo — coinciden en los 67 indicadores + 4 índices
+ sus dimensiones.

## Sitio de la llamada y cómo se verificó el orden

`_semaforos(informe)` se llama al final de `aplicar_scoring`, justo antes de su
`return informe` — after del `for ckey, c in informe["cinturones"].items():`
completo, no dentro de una rama.

Verifiqué la condición de orden ("después de que `indice_itvc` exista")
leyendo el cuerpo completo de `aplicar_scoring`: el branch
`ckey == "vida_cotidiana"` llama a `_scoring_vida_itvc(c, series)` (que escribe
`indice_itvc` en cada indicador) y termina en `continue` — es decir, para
cuando el loop principal avanza al último cinturón, vida cotidiana ya
completó su escritura de `indice_itvc`. `_semaforos` corre después de que las
5 iteraciones del loop terminaron, así que lee `indice_itvc` ya presente sin
importar el orden de iteración de `informe["cinturones"]`.

También confirmé que nada que corre DESPUÉS de `aplicar_scoring` en
`main()` — `recomputar_vida_y_global` (solo toca `informe["score_global"]`),
`_validacion_cruzada`, `acumular_historico`, `resumir.anotar` — muta ningún
campo que `_semaforos` lee (`valor`, `puntaje_*`, `indice_itvc`,
`aporte_score`, `en_indice`, dimensiones/`puntaje`). El brief sugería mover la
llamada al final de `main()` "si `aplicar_scoring` no fuera el último lugar
donde eso pasa" — no hizo falta: sí lo es.

## Hallazgo no pedido: colisión de nombre con un campo `semaforo` preexistente

Antes de escribir el test descubrí que `macro.py` (colector, función que
arma `idc`) ya escribe un campo `"semaforo"` — un STRING de 3 colores
("verde"/"amarillo"/"rojo") calculado por z-score, sin relación con el motor
de 4 colores de este plan:
```python
# macro.py línea 615
semaforo = "verde" if z > 0.5 else "amarillo" if z >= -0.5 else "rojo"
...
"semaforo": semaforo,
```
Ese campo llega intacto hasta `web/src/data/informe.json` (confirmado antes de
tocar nada: `cinturones.macro.indicadores.idc.semaforo == "amarillo"`, un
string). Verifiqué que nada lo consume: ni `web/src/lib/datos.ts` ni ningún
componente Astro leen `indicador.semaforo` — el frontend calcula su propio
semáforo de 3 colores para dimensiones vía `semaforoDimension(puntaje,
base100)`, sin leer ningún campo persistido. Tampoco hay test ni gate que lo
mire. Es dato muerto.

`_semaforos` lo sobrescribe con el dict de 4 colores (mismo nombre de campo,
tipo distinto) — lo confirmé después de implementar: `idc.semaforo` pasa de
`"amarillo"` (string) a `{"color": "amarillo", "tension": 4.9, "umbrales": [...],
...}` (coincidencia de color, no de mecanismo — son dos escalas totalmente
distintas). Dado que nada lo lee, sobrescribirlo es seguro y es exactamente lo
que este plan busca: unificar en un solo semáforo por indicador. No toqué
`macro.py` — mover/borrar ese campo muerto en el colector es un cambio de
alcance distinto (no está en la lista de archivos de esta tarea) y no rompe
nada dejarlo escribiendo un valor que ahora se pisa. Lo señalo para que quede
registrado, no como una tarea pendiente urgente.

## TDD: evidencia RED → GREEN

**RED** — `python -m pytest tests/test_publicar_semaforo.py -v` (antes de
tocar `publicar.py`, con el import de `parametrica` ya en su lugar):
```
FAILED ...TestCobertura::test_todo_indicador_con_tension_tiene_color
FAILED ...TestCobertura::test_el_color_es_uno_de_los_cuatro
FAILED ...TestCobertura::test_los_indices_y_sus_dimensiones_tienen_color
FAILED ...TestCoherencia::test_ningun_color_contradice_su_puntaje
FAILED ...TestCoherencia::test_vida_cotidiana_usa_la_formula_base100
FAILED ...TestCoherencia::test_los_umbrales_contienen_el_valor_vigente
6 failed, 1 passed in 0.26s
```
(el único que pasaba de entrada, `test_los_indices_siguen_donde_estaban`, no
depende de `semaforo` — compara el snapshot sin tocar contra sí mismo vía la
fixture recién congelada, así que pasa trivialmente hasta que el snapshot se
regenere). Las fallas restantes son exactamente las esperadas: sin ningún
indicador con bloque `semaforo`, `TypeError`/`KeyError`/`AttributeError` al
intentar leerlo — confirma que el test falla por AUSENCIA de la feature, no
por un error de fixture o de importación.

**GREEN** — tras implementar `_semaforos` y regenerar el snapshot:
```
python -m pytest tests/test_publicar_semaforo.py -v
7 passed in 0.19s
```

## Qué se probó y resultados

1. `tests/test_publicar_semaforo.py` (el propio, 7 tests): GREEN, ver arriba.
2. Suite completa, `python -m pytest tests -q`, ejecutada **contra un snapshot
   regenerado localmente para la verificación** (ver nota de alcance del
   snapshot más abajo — esa regeneración NO forma parte del commit):
   ```
   3 failed, 1936 passed, 3 skipped, 4 warnings, 1 error
   ```
   Descompuesto:
   - 2 preexistentes ya declaradas fuera de alcance por el brief:
     `test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
     y el error en `test_gestion_privatizaciones_novedades.py`. Sin cambios.
   - **2 nuevas** (`test_gate_bloqueante_vs_demora.py::test_el_gate_pasa_con_el_snapshot_vigente`
     y `test_una_demora_sola_no_bloquea`) — investigadas a fondo, ver sección
     siguiente. **No las causa el semáforo.**

## Hallazgo no pedido: staleness preexistente en `patentamiento_motos` (G3)

Al regenerar el snapshot (`generar_informe.py` + `publicar.py`) para correr la
suite completa, `gate_calidad.py` reporta:
```
[FALLA] G3 vida_cotidiana/patentamiento_motos: serie[-1]=72433.0 ≠ card=69319 (tolerancia 693.19)
```
Investigación: el archivo de caché más reciente en
`scripts/vida_cotidiana/data/` (`vida_cotidiana_20260730_0440.json`, el único
candidato — confirmé que no hay ningún archivo más nuevo ni en el disco ni en
`git ls-files`, coinciden exactamente) trae `cafam.patentamiento_motos.valor =
69319` (dato de 2026-06). La serie ya publicada en
`output/series/vida_cotidiana.csv` tiene un punto más nuevo (72433, dato de
2026-07) que evidentemente entró por otra vía (probablemente un colector
corrido en `main` después de que se creó esta rama) sin que el archivo crudo
correspondiente quedara en `scripts/vida_cotidiana/data/` de esta rama.

Verificación de que no lo causa mi código (mismo protocolo que usó el
controlador para las 2 fallas ya conocidas): hice `git stash` de
`scripts/publicar.py` (dejando el código EXACTAMENTE como estaba antes de esta
tarea), regeneré el snapshot y corrí `gate_calidad.py` — **falla idéntica**,
carácter por carácter. Confirma que es un problema de datos preexistente en la
rama, ajeno al semáforo.

Importante: esta falla es sobre el valor de **display** (`ind["valor"]`,
la card), no sobre el valor que puntúa el ITVC — `_itvc_indices` calcula el
componente `patentamiento_motos` a partir de la SERIE (vía
`_itvc_rebase_movil12(series, ...)`), no del campo `valor` de la card. Lo
confirmé numéricamente: el ITVC dio 90.3 tanto con el snapshot committeado
como con el regenerado (con card=69319) — **el índice no se movió un
milímetro** pese a esta discrepancia. Es decir, el gate está señalando un
problema real (la card no refleja lo mismo que puntúa) pero es puramente
cosmético para el índice, y de todos modos no forma parte de lo que esta tarea
publica ni compromete `TestNoMovioNingunNumero`.

No lo intenté arreglar (no es de esta tarea, y correr el colector de vida
cotidiana en vivo para refrescar el caché habría sido un efecto colateral no
pedido, con fetch de red, para una tarea que es puramente de capa de lectura).
Queda documentado para quien corra la Task 8 (pipeline completo en `main`).

## Nota de alcance: la regeneración del snapshot NO se commiteó

Leí `progress.md` del plan antes de cerrar la tarea y encontré un acuerdo
explícito documentado ahí (línea 4-6): **"tareas 1-7 en la rama; la 8
(pipeline + snapshot + producción) se corre en main después del merge, para
no chocar con el cron nocturno en `web/src/data/informe.json`."** Esto explica
por qué el `git add` del brief (Step 7) lista solo `scripts/publicar.py
tests/test_publicar_semaforo.py tests/fixtures/indices_previos_semaforo.json`
y deliberadamente NO incluye `output/informe.json`, `web/src/data/informe.json`,
`output/informe.md` ni `data/historico/indicadores.json`.

Por eso: regeneré el snapshot LOCALMENTE (sin commitear) para poder correr
`tests/test_publicar_semaforo.py` y la suite completa contra datos reales — es
lo que exige el Step 5 del brief y es la única forma de verificar la
feature —, y después de confirmar GREEN reviertí esos 4 archivos a su estado
de HEAD (`git checkout --`) antes de armar el commit, exactamente como pide
el brief y como exige el acuerdo del plan.

**Consecuencia que hay que tener presente**: con esto, el commit de esta tarea
deja `tests/test_publicar_semaforo.py` en el repo pero el snapshot committeado
en esta rama TODAVÍA no tiene bloques `semaforo` (porque no se corrió
`publicar.py` sobre el commit final). Si alguien corre `pytest
tests/test_publicar_semaforo.py` contra el estado actual de la rama sin
regenerar antes, va a fallar — igual que el RED de más arriba. Esto es
consistente con el acuerdo del plan (Task 8 hace la corrida real en `main`)
pero quiero que quede explícito para que no se lea como una tarea a medio
terminar.

## Distribución de colores observada (con el snapshot regenerado)

```
espiritu_epoca  verde   1
gestion         amarillo 5   verde 9
macro           amarillo 6   naranja 3   verde 8
politica        amarillo 5   naranja 4   verde 9
vida_cotidiana  amarillo 3   naranja 5   rojo 3   verde 5
```
67 indicadores con `aporte_score` no nulo → 67 con color (0 sin color;
`asistencia_directa` en gestión, el único sin `aporte_score`, correctamente
sin bloque `semaforo`).

## Los cuatro índices, antes y después (prueba de que nada se movió)

| índice | antes (fixture) | después (regenerado) |
|---|---|---|
| macro/itcm    | 61.9 | 61.9 |
| gestion/itcg  | 79.4 | 79.4 |
| politica/itcp | 66.9 | 66.9 |
| vida_cotidiana/itvc | 90.3 | 90.3 |
| score_global  | 3.4  | 3.4  |

Coinciden exactos (no solo dentro de tolerancia). `TestNoMovioNingunNumero`
pasa.

## Archivos modificados/creados

- `projects/informe_coyuntura/scripts/publicar.py` — import de `parametrica`
  + `_ESCALAS_SEMAFORO`, `_INDICE_DE_CINTURON`, `_escala_de`, `_por_que`,
  `_semaforo_de`, `_semaforos`, llamada desde `aplicar_scoring`. Commiteado.
- `projects/informe_coyuntura/tests/test_publicar_semaforo.py` — nuevo, 7
  tests. Commiteado.
- `projects/informe_coyuntura/tests/fixtures/indices_previos_semaforo.json` —
  nuevo, fixture congelada (Step 2). Commiteado.
- `projects/informe_coyuntura/output/informe.json`,
  `projects/informe_coyuntura/output/informe.md`,
  `projects/informe_coyuntura/web/src/data/informe.json`,
  `projects/informe_coyuntura/data/historico/indicadores.json` — regenerados
  localmente para verificar, **revertidos a HEAD antes de commitear** (ver
  nota de alcance arriba). No forman parte de este commit.

Commit: `3c99d3b` — "feat(semaforo): el snapshot publica color, umbrales y por que".

## Self-review

- **Completitud**: los tres tipos de nodo (indicador, índice, dimensión)
  reciben `semaforo`; `umbrales`/`unidad` son `None` donde corresponde
  (índices, dimensiones, y ramas base-100/aporte_score de indicadores).
  Cobertura verificada: 0 indicadores con `aporte_score` sin color.
- **Calidad**: sin hardcodear ningún corte (4/6/8, 60/40/20, 105/95/85) en
  `publicar.py` — grep confirma que esos números no aparecen en el diff.
  Prosa en castellano. No se tocó `itcm.py`/`itcg.py`/`itcp.py`/`itvc.py`.
- **YAGNI**: no agregué manejo para casos que no existen hoy (p. ej. no
  intenté generalizar `_INDICE_DE_CINTURON` para un cinturón hipotético con
  dos índices, ni anticipé una quinta escala).
- **Higiene de tests**: el archivo de test es el del brief, con un único
  agregado (dos líneas de docstring documentando la convención de borde ya
  usada) — sin lógica nueva. Ningún test usa datos inventados: todo lee el
  snapshot real regenerado.
- **Git**: nunca `git add -A`; se stashearon y restauraron con cuidado los
  archivos regenerados sin tocar el cambio ajeno preexistente en
  `.superpowers/sdd/.gitignore` (seguía intacto después de todo el proceso).

## Preocupaciones para el controlador

1. **`tests/test_publicar_semaforo.py` fallará si se corre contra el snapshot
   committeado tal cual queda esta rama ahora** — mismo RED documentado arriba
   — hasta que Task 8 regenere y publique en `main`. Es la consecuencia
   directa del acuerdo de `progress.md`, no un olvido.
2. **Staleness preexistente en `patentamiento_motos`** (sección dedicada
   arriba): cuando Task 8 corra el pipeline completo en `main`, puede que ya
   esté resuelta por commits nocturnos posteriores, o puede que siga — vale
   la pena que quien corra Task 8 la tenga presente en vez de asumir que un
   G3 nuevo es un bug del semáforo.
3. **Campo `semaforo` de 3 colores en `macro.py` (`idc`)**, ahora pisado por
   el de 4 colores: dato muerto confirmado, sin consumidor, seguro de
   sobrescribir — pero si alguna tarea posterior del plan reintroduce lectura
   de ese campo específico esperando el string viejo, hay que saber que ya no
   existe.

---

# Fix round 1/5 — review de la coordinación

La review devolvió spec ❌ / calidad "needs work" con 4 hallazgos (2 críticos,
2 importantes). Los dos divergencias declaradas en el reporte original
(reuso de los wrappers públicos de color, `_INDICE_DE_CINTURON` explícito)
fueron confirmadas correctas y quedan como están — no se tocaron en esta
ronda.

## C1 (crítico) — tensión del ITVC publicada fuera de su dominio 0-10

**El bug**: `_semaforos` recalculaba `5.0 - (idx100 - 100.0) * 0.2` a mano
para la tensión publicada de cada indicador de vida cotidiana, sin el
acotado a `[0, 10]` que `itvc.tension_de_itvc()` (`scripts/itvc.py:237-240`)
ya aplica — y que `_scoring_vida_itvc`, en el mismo archivo, sí usa. El
color no lo delataba porque los cuatro cortes de `CORTES_SEMAFORO` caen
dentro de `[0, 10]`: un valor de tensión de 21,6 o −3,0 podía seguir cayendo
en el tramo correcto de color sin que ningún test lo notara.

**El fix**: `scripts/publicar.py`, rama `elif isinstance(idx100, (int,
float))` de `_semaforos` — la tensión publicada ahora es
`itvc.tension_de_itvc(float(idx100))` (acotada). El **color** sigue
viniendo de `parametrica.color_de_indice_base100(float(idx100))` sobre el
valor CRUDO, sin cambios — es conservar exactamente lo que pide la
review: "el color no debe cambiar".

**Verificación de que el test nuevo lo hubiera atajado**: antes de dar por
cerrado el fix, monkeypatcheé `itvc.tension_de_itvc` para que devolviera la
fórmula vieja sin acotar y corrí `_semaforos` sobre el snapshot committeado.
Salieron exactamente los 6 indicadores que señaló la review, con los mismos
valores:
```
[('vida_cotidiana', 'peso_tarifas', 10.7), ('vida_cotidiana', 'alquiler_real', 12.1),
 ('vida_cotidiana', 'pobreza_nowcast', -0.4), ('vida_cotidiana', 'sentimiento_digital', -2.5),
 ('vida_cotidiana', 'patentamiento_motos', -3.0), ('vida_cotidiana', 'mora_familias', 21.6)]
```
Con el fix aplicado (código real, sin monkeypatch), el nuevo
`TestTensionEnDominio::test_ninguna_tension_publicada_sale_de_0_10` pasa:
cero indicadores fuera de rango.

## C2 (crítico) + I2 (importante) — colisión de nombre `semaforo` real, no muerta

Mi claim original de "dato muerto" en el reporte de Task 3 era incorrecto:
`scripts/publicar.py:454` (dentro de `_macro_input_txt`) SÍ leía
`ind.get('semaforo', '')` para armar el paréntesis de `aporte_input_txt` de
`idc` — confirmado en el snapshot real, `idc.aporte_input_txt` traía
literalmente `"(amarillo)"` tomado de ese campo. Lo que funcionaba hoy era
puro orden de ejecución: `_scoring_indice` (que llama a `_macro_input_txt`)
corre DENTRO del loop de `aplicar_scoring`, antes de que `_semaforos` — que
corre después de que el loop completo termina — pise ese mismo campo con el
dict de 4 colores. Cambiar el orden de esas dos llamadas en el futuro
rompería `idc` en silencio.

**Fix — eliminar la colisión en vez de depender del orden**:
- `scripts/macro.py`: el campo que escribe `fetch_idc()` pasa de
  `"semaforo"` a `"banda_idc"` (mismo valor, "verde"/"amarillo"/"rojo" por
  z-score — es un semáforo de 3 colores propio del IDC, sin relación con el
  motor paramétrico de 4 colores de este plan). Comentario agregado
  explicando por qué el nombre importa.
- `scripts/publicar.py:454`: `ind.get('banda_idc', '')` en vez de
  `ind.get('semaforo', '')`.
- Revisé `web/src/lib/fichas.ts` (línea 312, la mención de "semáforo" que
  señaló la review): es prosa que describe el CONCEPTO de la banda 3-color
  del IDC ("por encima de +0,5 desvíos, capacidad mayor a la habitual..."),
  no una referencia al campo JSON — no hacía falta tocarla. Grep confirmó
  que ningún `.ts`/`.astro` lee `indicador.semaforo` ni `indicador.banda_idc`
  directamente (el frontend calcula su propio semáforo de dimensión con
  `semaforoDimension()`, sin leer nada persistido).
- Grep en `tests/` confirmó que ningún test existente hace assert sobre el
  texto exacto de `idc.aporte_input_txt` (nada que se rompa por el rename).

**Caché vieja, sin arreglar a propósito**: `output/cache/macro.json`
(generado por una corrida anterior de `macro.py`) todavía tiene la clave
vieja `"semaforo": "amarillo"`, no `"banda_idc"` — confirmado leyendo el
archivo. Hasta que alguien corra `python scripts/macro.py` de nuevo (se
autocura solo, nada que hacer a mano), `ind.get('banda_idc', '')` en
`publicar.py` va a devolver `''`, y el paréntesis de `idc.aporte_input_txt`
va a salir vacío (`"... asignación X ()"`) en vez de mostrar la banda —
degradación silenciosa, no un crash. Tal como indicó la review, no lo
"arreglé" tocando la caché a mano.

## I1 (importante) — la suite no pasaba con el snapshot committeado

**El problema real**: `tests/test_publicar_semaforo.py` original leía
`web/src/data/informe.json` del disco. Contra el snapshot committeado en
esta rama (que todavía no tiene `semaforo` — Task 8 lo publica recién en
`main`), eso daba 3 tests en rojo (sin bloque `semaforo`) y otros 3 en
`AttributeError: 'str' object has no attribute 'get'` — este último por C2:
`test_ningun_color_contradice_su_puntaje` y compañía iteran indicadores
esperando que `ind.get("semaforo")` sea `None` o un dict, y con la colisión
sin resolver el campo de `idc` era el string viejo `"amarillo"`.

**Fix**: reescribí el fixture `informe` para cargar el snapshot committeado
como dato puro, clonarlo con `copy.deepcopy`, y llamar a
`publicar._semaforos(copia)` **en memoria** — sin escribir ningún archivo
(no choca con ADR-0179, ninguna corrida de `publicar.py` de por medio). El
snapshot committeado ya pasó por una versión de `aplicar_scoring` SIN el
paso `_semaforos` (la que estaba antes de esta tarea), así que ya trae todo
lo que `_semaforos` necesita como insumo (`puntaje_itcm/itcg/itcp`,
`indice_itvc`, `aporte_score`, `en_indice`, `valor`, `unidad`) — aplicarla
en memoria sobre una copia es válido independientemente de cuándo se
regenere el snapshot de verdad. Esto desacopla el test de la Task 8 por
completo: va a seguir siendo verde durante las Tasks 4-7, sin importar que
el snapshot publicado no cambie hasta el final.

`test_los_indices_siguen_donde_estaban` se reescribió como pide la review:
carga el snapshot base, guarda los 4 índices + `score_global`, clona,
corre `_semaforos` sobre la copia, y compara. Es estrictamente más fuerte
que la fixture congelada (prueba que `_semaforos` específicamente no mueve
nada, no solo que el snapshot no cambió desde un commit arbitrario) —
`tests/fixtures/indices_previos_semaforo.json` se borró con `git rm`.

No usé `pytest.skip` en ningún lado.

Agregué además `TestTensionEnDominio` (cubre C1), con docstring explicando
por qué el color no alcanza para detectar este bug.

## Comando y resultado, tras las 4 correcciones

```
python -m pytest tests/test_publicar_semaforo.py -v
```
```
collected 8 items
TestCobertura::test_todo_indicador_con_tension_tiene_color PASSED
TestCobertura::test_el_color_es_uno_de_los_cuatro PASSED
TestCobertura::test_los_indices_y_sus_dimensiones_tienen_color PASSED
TestCoherencia::test_ningun_color_contradice_su_puntaje PASSED
TestCoherencia::test_vida_cotidiana_usa_la_formula_base100 PASSED
TestCoherencia::test_los_umbrales_contienen_el_valor_vigente PASSED
TestTensionEnDominio::test_ninguna_tension_publicada_sale_de_0_10 PASSED
TestNoMovioNingunNumero::test_los_indices_siguen_donde_estaban PASSED
8 passed in 3.22s
```

Suite completa:
```
python -m pytest tests -q
```
```
1 failed, 1939 passed, 3 skipped, 4 warnings, 1 error in 135.91s
FAILED tests/test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio
ERROR tests/test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes
```
Exactamente las 2 fallas preexistentes que el brief autorizó — nada nuevo.
Confirmado además que esta corrida no tocó ningún archivo de snapshot
(`git status` limpio salvo los 4 archivos de este fix y el WIP ajeno de
`.gitignore`): las 8 pruebas de `test_publicar_semaforo.py` corren
enteramente en memoria, sin depender de que `web/src/data/informe.json` esté
regenerado.

## Archivos modificados en este round

- `projects/informe_coyuntura/scripts/publicar.py` — C1 (tensión ITVC
  acotada) + C2 (lee `banda_idc`).
- `projects/informe_coyuntura/scripts/macro.py` — I2 (`semaforo` →
  `banda_idc` en `fetch_idc()`).
- `projects/informe_coyuntura/tests/test_publicar_semaforo.py` — I1
  (fixture en memoria vía `publicar._semaforos()`) + nuevo
  `TestTensionEnDominio` (C1).
- `projects/informe_coyuntura/tests/fixtures/indices_previos_semaforo.json`
  — borrado (`git rm`), superado por la invariancia directa de I1.

Commit: `2253c13` — "fix(semaforo): tension del ITVC acotada, sin colision
con banda_idc, tests en memoria".

## Concerns para el próximo round

- `output/cache/macro.json` sigue con la clave vieja `"semaforo"` hasta la
  próxima corrida real de `python scripts/macro.py` (no forzada en esta
  tarea, sería un efecto colateral de red no pedido). Mientras tanto,
  `idc.aporte_input_txt` publica el paréntesis vacío si alguien regenerara
  el snapshot HOY sin antes correr el colector — otra razón más para que
  Task 8 corra el pipeline completo (colectores incluidos) y no solo
  `generar_informe.py` + `publicar.py`.
- El resto de las preocupaciones del reporte original (staleness de
  `patentamiento_motos`, deferral del snapshot a Task 8) siguen vigentes sin
  cambios — no las reabrí porque no las tocó este round de fixes.
