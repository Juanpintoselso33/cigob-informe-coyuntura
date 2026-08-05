---
madr: 4
id: '0179'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['tests/conftest.py']
continua: ['0178']
ambito: 'Suite de tests · invariante de aislamiento'
origen: 'ADR-0178 arregló el único test que escribía en el árbol y dejó anotado que el aislamiento era puntual y no estructural'
---

# ADR-0179 — Ningún test escribe en un archivo versionado

## Contexto y planteo del problema

ADR-0178 arregló `test_publicar_genera_snapshot`, que corría `publicar.py` de
verdad contra el repo, y cerró con esta limitación:

> El aislamiento es puntual, no estructural. Se arregló el único test que
> escribía, no se impidió que otro lo haga.

El costo de que vuelva a pasar no es el `git status` sucio. Un test que escribe
en `web/src/data/informe.json` **no rompe ese test: rompe los que corren
después**. El 5-ago-2026 eso produjo diez fallas G3 fantasma en el gate y dos
tests (`test_macro_itcm_reconcilia`, `test_puntaje_unico_camino`) que pasaban
solos y fallaban en conjunto. Esas fallas se confundieron **dos veces** con
problemas de datos reales antes de que se entendiera de dónde salían.

El síntoma aparece lejos de la causa, y encontrar al culpable requirió correr la
suite archivo por archivo con `git status` en el medio. Eso es lo que no puede
volver a costar.

## Factores de decisión

- El invariante es simple y absoluto —ningún test modifica un archivo
  versionado— así que se puede verificar sin conocer nada de cada test.
- Nombrar al culpable no alcanza: si el test contamina y sigue, el resto de la
  suite queda sin valor diagnóstico. Hay que **restaurar**.
- El chequeo corre ~1900 veces. Hashear 78 archivos cada vez costaría minutos;
  statearlos cuesta ~1 ms.
- `git checkout` como forma de restaurar pisaría las modificaciones locales
  legítimas de quien esté trabajando. La línea base tiene que ser el estado al
  arrancar la sesión, no `HEAD`.

## Opciones consideradas

- **Fixture `autouse` que compara antes y después de cada test, restaura y
  falla** — elegida.
- **Un solo chequeo al final de la sesión** — descartada: detecta que alguien
  ensució pero no quién, que es justamente la parte cara.
- **`git status` por test** — descartada por costo: ~100 ms × 1900 son más de
  tres minutos sobre una suite de uno.
- **Montar el repo de sólo lectura durante los tests** — descartada: los tests
  necesitan escribir en `tmp_path` y varios leen rutas del repo; el aislamiento
  a nivel filesystem rompe más de lo que arregla.

## Decisión

`tests/conftest.py` con una fixture `autouse` que, alrededor de cada test:

1. compara `(tamaño, mtime)` de los 78 archivos versionados bajo `data/`,
   `web/src/data/` y `output/` — el filtro barato;
2. sobre los que se movieron, compara el **contenido** contra la línea base
   tomada al arrancar la sesión;
3. si alguno cambió de verdad: **restaura** el contenido original y falla el
   test nombrándolo.

Un archivo reescrito con contenido idéntico mueve el `mtime` y no se reporta:
una falla que no corresponde a un daño real entrena a ignorar el guardián.

Un test que necesite escribir puede declararlo con
`@pytest.mark.escribe_en_el_arbol("motivo")`; ahí se acepta y se actualiza la
línea base, para que los tests siguientes no arrastren la culpa.

Sin `git` disponible el guardián se desactiva solo: un tarball sin `.git` tiene
que poder correr los tests igual.

### Consecuencias

- El próximo test que escriba en el árbol falla en el acto, con su nombre y el
  del archivo, en lugar de romper a otro tres archivos más adelante.
- Los resultados del resto de la suite siguen valiendo aunque uno contamine.
- Sobrecarga medida: **~5 segundos sobre 1895 tests** (101 s → 106 s).

### Confirmación

Verificado con un test de prueba que escribe en `informe.json`: el guardián lo
nombró, restauró el archivo, y un segundo test con el marcador declarado pasó
sin ruido.

## Más información

### Limitaciones

- **Se reporta como ERROR de teardown, no como FAIL.** Es una restricción de
  pytest: lo que se levanta en un finalizador no puede marcar el test como
  fallado. Se lee igual de claro y hasta distingue mejor el caso —las
  aserciones del test pasaron, lo que falló es que ensució— pero un filtro que
  cuente sólo `failed` lo pasa por alto.
- **Vigila tres carpetas, no el repo entero.** Un test que escriba en
  `scripts/`, `docs/` o `.github/` no lo detecta. Se acotó a las salidas
  versionadas porque son las que envenenan a otros tests; ampliarlo a todo el
  repo obligaría a leer y guardar bastante más que 3 MB.
- **La línea base se toma una vez por sesión.** Si un test corre otro proceso
  que escribe DESPUÉS de que el guardián comparó (un subproceso que quedó
  vivo), el cambio se le atribuye al test siguiente. No pasó nunca, pero el
  modo de falla existe.
- No impide que un test escriba: lo detecta y lo deshace. Un test que además
  dependa de haber escrito va a fallar de forma confusa la próxima vez, aunque
  ahora al menos con un mensaje que dice exactamente qué pasó.
