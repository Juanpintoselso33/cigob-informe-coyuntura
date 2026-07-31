---
madr: 4
id: '0060'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'politica'
archivos: ['scripts/generar_informe.py', 'scripts/politica.py']
relacionado: ['0058']
ambito: '`scripts/generar_informe.py` · `scripts/politica.py` (refactor) · pipeline completo (4 cinturones)'
---

# ADR-0060 — generar_informe.py recalcula ITCM/ITCG/ITCP desde los valores crudos, no confía en el caché del colector

## Contexto y planteo del problema

Al corregir `BANDAS_ITCP["ratio_dnu"]` (ADR-0059) y correr
`python scripts/generar_informe.py`, el puntaje publicado de `ratio_dnu`
**no cambió** — siguió reflejando las anclas viejas (recalibradas por error
en ADR-0058) hasta que se volvió a correr `python scripts/politica.py`.

Investigación de la arquitectura de cacheo (los 3 índices por bandas):

- `scripts/macro.py`, `scripts/gestion.py` y `scripts/politica.py` son el
  **único lugar del repo** donde `itcm.calcular_itcm()` /
  `itcg.calcular_itcg()` / `itcp.calcular_itcp()` se invocan con datos —
  y el resultado se **persiste tal cual** en `output/cache/{macro,gestion,
  politica}.json` bajo la clave `itcm`/`itcg`/`itcp`, calculado con el
  código de `itcm.py`/`itcg.py`/`itcp.py` **vigente en el momento del
  fetch**.
- `scripts/generar_informe.py::construir_informe()` leía ese bloque
  **verbatim** (`cinturones_data[nombre][indice] = cache[indice]`) — nunca
  volvía a llamar al motor de scoring. Si las bandas/pesos/ajustes cambian
  sin volver a correr el colector, el índice publicado queda
  desincronizado del código actual, silenciosamente: no hay ningún error,
  ningún test lo detecta, ninguna advertencia se imprime.
- `scripts/publicar.py::_scoring_indice()` hereda ese mismo bloque desde
  `output/informe.json` — documentado explícitamente en su propio
  docstring (`publicar.py:220-222`): *"su puntaje viene del ITCM/ITCG/ITCP
  calculado por el colector... se traduce en aplicar_scoring()"*. Solo la
  dispersión Monte Carlo de `robustez` usa `itcm.py`/`itcg.py`/`itcp.py`
  en frío (bandas vigentes); el **punto central** que se perturba sigue
  siendo el heredado, stale.
- `scripts/sensibilidad.py` lee `web/src/data/informe.json` (la salida de
  `publicar.py`) — hereda la misma staleness una capa más abajo.
- **`ITVC` no tiene este problema**: `publicar.py::_scoring_vida_itvc()`
  reconstruye los índices base-100 desde `output/series/*.csv` y llama a
  `itvc.calcular_itvc()` **en cada corrida**, sin cache intermedio. Es el
  patrón correcto; los otros tres no lo seguían.
- No existe ningún test que verifique el invariante real ("el índice
  publicado es lo que el código VIGENTE de `itcm.py`/`itcg.py`/`itcp.py`
  calcularía a partir de los valores crudos persistidos"). Los tests de
  "reconciliación" existentes (`test_publicar.py`) son aritméticamente
  tautológicos: solo confirman que la suma ponderada de los puntajes YA
  PUBLICADOS reproduce el total YA PUBLICADO — cierran igual estén stale o
  no, porque suman los mismos números que ya se sumaron para producir el
  total.

Costo de la corrección "documentada" (`docs/arquitectura/02-pipeline-datos.md`):
volver a correr el colector completo (`macro.py`/`gestion.py`/`politica.py`),
que re-dispara TODOS los fetchers de red del cinturón (INDEC/BCRA/InfoLeg/
HCDN/etc.) solo para re-puntuar una fórmula que no necesitaba ningún dato
nuevo — caro, lento, y frágil (cualquier fuente caída ese día degrada
indicadores a "desactualizado" sin necesidad).

## Opciones consideradas

- Arreglar solo `politica.py` (recordar re-correr el colector)
- Recalcular en `publicar.py` en vez de `generar_informe.py`
- Agregar un test que fuerce recalcular y comparar contra el caché

## Decisión

### 1. Extraer el cálculo del ITCP a una función reutilizable

`scripts/politica.py` tenía el cálculo del ITCP inline dentro de `main()`
(a diferencia de `macro.py`/`gestion.py`, que ya exponían
`calcular_itcm_cinturon()`/`calcular_itcg_cinturon()` como funciones de
módulo). Se extrae a `calcular_itcp_cinturon(indicadores: dict) -> dict |
None`, mismo patrón: toma valores ya persistidos, sin red.

### 2. `generar_informe.py` recalcula, no copia

`construir_informe()` deja de copiar `cache["itcm"/"itcg"/"itcp"]`
verbatim. Para los 3 cinturones con índice paramétrico, llama a
`calcular_itcm_cinturon`/`calcular_itcg_cinturon`/`calcular_itcp_cinturon`
con `cache["indicadores"]` (los valores crudos ya persistidos — sin red) y
usa ESE resultado, recalculando también `score` con
`itcm.tension_de_itcm`/`itcg.tension_de_itcg`/`itcp.tension_de_itcp`
sobre el valor fresco. `vida_cotidiana`/`espiritu_epoca` (sin índice
paramétrico propio en este generador) no cambian: siguen usando
`cache["score"]` tal cual, igual que antes.

### 3. El resto de la cadena hereda el fix gratis

`publicar.py` parte de `output/informe.json` (ya corregido) y
`sensibilidad.py` de `web/src/data/informe.json` (ya corregido
transitivamente) — no hicieron falta cambios en esos dos archivos. La
"robustez" (Monte Carlo) queda centrada en el valor fresco automáticamente,
porque perturba alrededor de `bloque["valor"]`, que ahora es fresco.
Verificado empíricamente: cambiar una banda de `itcp.py` y correr
únicamente `generar_informe.py` + `publicar.py` (sin tocar `politica.py`)
propaga el cambio a `output/informe.json` y a `web/src/data/informe.json`
por igual.

### Consecuencias

- Un cambio en `itcm.py`/`itcg.py`/`itcp.py` (bandas, pesos, ajustes) se
  refleja correctamente con solo `generar_informe.py` + `publicar.py` —
  ya no hace falta re-correr el colector (con su costo de red) para
  re-puntuar con datos que ya estaban frescos en caché.
- `politica.py` gana `calcular_itcp_cinturon()` como función de módulo,
  igual que `macro.py`/`gestion.py` — API interna más simétrica entre los
  3 cinturones paramétricos.
- Nuevo archivo `tests/test_generar_informe.py` (5 tests) — antes no
  existía ningún test de `generar_informe.py`.
- La corrección de ratio_dnu de ADR-0059, que ya se había publicado
  re-corriendo `politica.py` manualmente, queda ahora protegida
  estructuralmente: el próximo cambio de bandas no requerirá ese paso
  extra ni arriesgará quedar stale si alguien lo olvida.

## Pros y contras de las opciones

### Arreglar solo `politica.py` (recordar re-correr el colector)

Rechazada. Ya se documentó la regla ("si cambia el motor de scoring, hay
que re-correr el colector") en `docs/arquitectura/02-pipeline-datos.md` —
y aun así se violó hoy mismo, en la misma sesión que escribió esa regla
para otro propósito. Una regla que hay que recordar manualmente en cada
cambio de bandas/pesos es exactamente el tipo de paso que se saltea bajo
presión; el fix estructural (recalcular siempre) elimina la clase entera
de error.

### Recalcular en `publicar.py` en vez de `generar_informe.py`

Considerada. Habría arreglado `web/src/data/informe.json` y, por herencia,
`sensibilidad.py`, pero **no** `output/informe.json`/`informe.md`
(consumidos directamente por `validacion_externa.py` en algunos casos y
por lectura humana). Recalcular en `generar_informe.py` (más arriba en la
cadena) arregla todo aguas abajo sin duplicar la lógica en dos lugares.

### Agregar un test que fuerce recalcular y comparar contra el caché

Considerada como complemento, no como sustituto. Un test de reconciliación
real (crudo → `itcm.py` vigente → comparar contra lo publicado) habría
detectado el bug de hoy, pero no lo previene en la próxima sesión si el
código vuelve a leer del caché por comodidad. Se agregó igual
`tests/test_generar_informe.py` (5 casos: recalcula ITCM/ITCG/ITCP,
cinturones sin paramétrica no tocados, `None` conserva el score cacheado)
como red de contención adicional.

## Más información

### Precedentes directos

ADR-0058/0059 (ratio_dnu — el bug se descubrió corrigiendo esas anclas)

### Limitaciones

- El recálculo depende de que `cache["indicadores"]` tenga los mismos
  valores crudos con los que se calculó `cache["itcm"/"itcg"/"itcp"]`
  originalmente — si el colector cambia qué campo de un indicador se
  puntúa (ej. `_valor_itcp` para `protestas_caba`), ese mapeo vive en el
  colector, no en `generar_informe.py`, y debe mantenerse sincronizado ahí.
- Los ajustes manuales del analista (`data/*/ajustes_itc*.json`) se
  releen desde disco en cada recálculo — correcto (reflejan vigencia por
  mes), pero significa que `generar_informe.py` ahora depende de esos
  archivos además del caché.
- No se tocó `sensibilidad.py` ni `publicar.py` directamente: ambos heredan
  el fix por leer, en cadena, la salida ya corregida de
  `generar_informe.py`. Si algún día alguno de los dos deja de leer desde
  ahí (lee directo del caché del colector, por ejemplo), la staleness
  reaparecería en ese punto específico.
