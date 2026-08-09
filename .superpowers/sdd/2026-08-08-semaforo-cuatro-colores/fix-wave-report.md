# Fix wave — semáforo de 4 colores (revisión final antes de mergear a `main`)

Rama: `semaforo-cuatro-colores`. Working dir: `projects/informe_coyuntura/`.

## C2 (Crítico) — `por_que` publicaba el corte lejano en vez del más cercano

**Cambio:** `scripts/publicar.py`, función `_por_que`. Antes tomaba `desde` si
existía, sin comparar contra `hasta`:

```python
borde = actual["desde"] if actual["desde"] is not None else actual["hasta"]
```

Ahora compara las dos distancias y toma el borde finito más cercano:

```python
bordes = [b for b in (actual["desde"], actual["hasta"]) if b is not None]
if not bordes:
    return f"{coma(valor)} {unidad}: {color.capitalize()} en todo el rango."
borde = min(bordes, key=lambda b: abs(valor - b))
```

**Evidencia:** reproduje el bug y el fix corriendo `parametrica.umbrales_en_unidad`
+ la lógica de distancia contra el `valor` real de cada indicador en el
snapshot committeado (sin persistir nada). Distancias corregidas, exactamente
las que pedía el hallazgo:

| Indicador | Valor | Tramo | Distancia ROTA (a `desde`) | Distancia CORREGIDA (borde más cercano) |
|---|---|---|---|---|
| `ipi_manufacturero` | −1,07 | (−3,5, −1,0] naranja | 2,43 | **0,07** |
| `costo_financiamiento_tesoro` | 8,07 | (−1,89, 12,5] verde | 9,96 | **4,43** |
| `libertad_opcion_salud` | 31,8 | (20, 36] amarillo | 11,8 | **4,2** |
| `ratio_dnu` | 1,84 | (1,6, 1,8667] naranja | 0,24 | **0,03** |
| `apoyo_empresario` | −0,429 | (−0,5333, −0,4] naranja | 0,10 | **0,03** |

Además de esos 5, encontré y verifiqué las 7 restantes de las "12 de 49"
mencionadas en el hallazgo: `idc` (0,34→0,26), `emae_difusion` (9,33→6,67),
`credito_privado` (6,85→2,9), `reestructuracion_organismos` (10,0→6,0),
`conflictividad_nacional` (3,1→2,5), `judicializacion` (0,17→0,15),
`cobertura_judicial` (4,63→3,37). Total exacto: 12/49, igual al hallazgo.

**Test nuevo:** `tests/test_publicar_semaforo.py::TestPorQue` (3 tests,
sintéticos y deterministas — no dependen de datos en vivo que puedan
correrse de tramo con el próximo cron):
- `test_toma_el_borde_mas_cercano_cuando_es_hasta` — tramo `[10, 20]`, valor
  `19`: el borde correcto es `hasta` (distancia 1), no `desde` (distancia 9).
- `test_sigue_tomando_desde_cuando_es_el_mas_cercano` — mismo tramo, valor
  `11`: cubre que el camino "desde" no se rompió.
- `test_borde_abierto_usa_el_unico_borde_finito` — tramo con `desde=None`.

**Dientes verificados:** reviertí el fix, corrí `test_toma_el_borde_mas_cercano_cuando_es_hasta`
→ falló con `AssertionError: ... 'a 9,0 del corte más cercano' ...` (el texto
roto). Restauré el fix exactamente y volvió a pasar.

## C3 (Crítico) — plan Task 8 no regeneraba el cache de `macro.py`

**Cambio:** solo en el documento del plan,
`docs/superpowers/plans/2026-08-08-semaforo-cuatro-colores.md`, Task 8 Step 1.
No toqué ningún colector ni corrí `scripts/macro.py`.

Antes decía "el cambio es de presentación y no toca colectores" y arrancaba
directo en `generar_informe.py`. Ahora el Step 1 explica que la Task 3 sí
tocó un colector (`scripts/macro.py:635`, `semaforo`→`banda_idc`, leído por
`publicar.py:454`) y agrega `python scripts/macro.py` como primer comando,
con la explicación de qué pasa si se omite (el modal público de `idc`
publica el paréntesis vacío).

**Evidencia de que el hallazgo era real:** confirmé el estado actual de
`output/cache/macro.json` (sin tocarlo):

```
{'semaforo': 'amarillo', 'banda_idc': None, 'valor': -0.26}
```

Efectivamente la clave vieja sigue presente y la nueva es `None` — exactamente
el síntoma del hallazgo.

## I1 (Importante) — tramos fusionados con 6 decimales

**Cambio:** `scripts/parametrica.py`, dentro de `umbrales_en_unidad`, en el
path que fusiona tramos contiguos del mismo color:

```python
tramos[-1]["hasta"] = None if hasta is None else round(hasta, 4)
```

(antes: `tramos[-1]["hasta"] = hasta`, sin redondear — asignaba el quiebre
crudo `round(x, 6)`).

**Evidencia — antes del fix**, `costo_financiamiento_tesoro`:
```
{'color': 'naranja', 'desde': None, 'hasta': -3.571429}
{'color': 'amarillo', 'desde': -3.5714, 'hasta': -1.8889}
```
Mismo borde, dos precisiones (`-3,571429` vs `-3,5714`) — exactamente el
hallazgo.

**Después del fix:**
```
{'color': 'naranja', 'desde': None, 'hasta': -3.5714}
{'color': 'amarillo', 'desde': -3.5714, 'hasta': -1.8889}
```

**Test nuevo:** `tests/test_semaforo.py::TestUmbralesEnUnidad::test_ningun_borde_tiene_mas_de_4_decimales`
— recorre las 57 tablas de ITCM/ITCG/ITCP y exige `borde == round(borde, 4)`.

**Dientes verificados:** reviertí el fix, corrí el test → falló con
`AssertionError: ITCM/costo_financiamiento_tesoro: borde con más de 4
decimales: -3.571429`. Restauré el fix exactamente y volvió a pasar.

## I2 (Importante) — `rangoLegible` no usaba el formateador del archivo

**Cambio:** `web/src/pages/metodologia/[id].astro`, función `rangoLegible`.
Reemplacé el helper local `n = (x) => String(x).replace(".", ",")` (sin
separador de miles, sin menos tipográfico, sin techo de precisión) por el
`num()` ya importado del archivo desde `datos.ts` — el "ÚNICO formateador de
números para pantalla" del proyecto según su propio comentario (separador de
miles es-AR, coma decimal, menos U+2212, máximo 2 decimales).

**Verificación — build real, cuatro fichas pedidas.** Regeneré localmente
`output/informe.json` + `web/src/data/informe.json` (sin tocar ningún
colector: solo `generar_informe.py` + `publicar.py` sobre los caches
existentes) para que el snapshot trajera el bloque `semaforo` — el
committeado en la rama es previo a `_semaforos()` (mismo motivo documentado
en el header de `test_publicar_semaforo.py`). Corrí `npm run build` y leí las
tablas renderizadas en `web/dist/`. Después **restauré los cuatro archivos
generados a su estado exacto** (`git checkout --` + verificación por sha256)
y reconstruí una vez más para dejar `dist/` (gitignorado) acorde al snapshot
committeado.

Tablas renderizadas (`Rango (unidad)` → `Color`):

**`apertura_comercial`** (`% del intercambio (alícuota efectiva)`):
```
≤ 6            → VERDE
6 – 9          → AMARILLO
9 – 10,33      → NARANJA
≥ 10,33        → ROJO
```

**`desregulacion_normativa`** (`artículos de normas modificados o eliminados, acumulados desde dic-2023`):
```
≤ 6.000        → NARANJA
6.000 – 11.000 → AMARILLO
≥ 11.000       → VERDE
```
Separador de miles presente y consistente con la tabla de anclas de la misma
ficha (`≤ 2.500`, `15.000 – 30.000`, etc.) — ya no "≥ 11000" vs "13.300".

**`costo_financiamiento_tesoro`** (`% real anual (TIREA vs. inflación esperada REM)`):
```
≤ −3,57        → NARANJA
−3,57 – −1,89  → AMARILLO
−1,89 – 12,5   → VERDE
12,5 – 16,67   → AMARILLO
16,67 – 19,33  → NARANJA
≥ 19,33        → ROJO
```
Menos tipográfico U+2212 correcto, y el borde fusionado (fix de I1) coincide
byte a byte entre filas adyacentes (`−3,57` en la fila 1 y en el `desde` de
la fila 2).

**`rem_ipc_12m`** (`% anual esperado`):
```
≤ 39,29        → VERDE
39,29 – 60,1   → AMARILLO
60,1 – 72,86   → NARANJA
≥ 72,86        → ROJO
```
2 decimales en vez del ruido crudo de interpolación (`39,2892` → `39,29`).

**Decisión de decimales:** usé `num()` tal cual (máximo 2 decimales, sin
ceros de relleno) en vez de inventar una regla de decimales por unidad. Es la
opción de menor riesgo: es el mismo formateador que ya usa el resto de la
página (pesos, puntajes, tensión, robustez) y el propio comentario de
`num()` en `datos.ts` lo declara como el único formateador del proyecto. No
inventé un tercer esquema de precisión.

## I3 (Importante) — el enum fantasma sobrevivía en dos lugares

**Cambios:**
1. `web/src/lib/datos.ts:69` — comentario de tipo de `Cinturon.estado`:
   `estable | en_tension | critico` → `estable | en_tension | tensionado`.
2. `docs/superpowers/plans/2026-08-08-semaforo-cuatro-colores.md:23` —
   corregí el vocabulario (`alerta`/`critico` → `tensionado`) y la afirmación
   falsa de que ese enum alimenta `score_global`. `score_global` es un
   promedio ponderado de los *scores* 0-10 de cada cinturón; `estado` se
   deriva por separado del mismo score vía `_estado()` — son dos lecturas
   del mismo número, no una cadena. El resto de la frase (que el enum
   alimenta BLUF, panel de tensión y `cinturonesRojos`) lo verifiqué grepeando
   los usos reales de `verdictDeCinturon`/`cinturonesRojos` en
   `Bluf.astro`, `TensionPanel.astro`, `Hero.astro`, `Metodologia.astro`,
   `Archivo.astro` — es correcto, lo dejé.

**Tests nuevos**, `tests/test_web_semaforo.py`, clase
`TestNingunEstadoFantasmaEnTodoElArchivo` (extiende la Dirección 2 más allá
del cuerpo de `verdictDeCinturon`, que es donde el hallazgo dice que el test
existente no llega):
- `test_el_comentario_de_tipo_de_cinturon_estado_no_lista_un_fantasma` —
  parsea el comentario de tipo (`estado: string; // ...`) y exige que su
  vocabulario sea EXACTAMENTE `_estados_reales()`.
- `test_ninguna_comparacion_de_estado_en_todo_el_archivo_es_fantasma` —
  busca `estado === "X"` en TODO el archivo (no solo en el cuerpo de una
  función nombrada), con `(?<!\.)` para excluir a propósito `ind.estado`/
  `c.estado` (el `estado` POR INDICADOR, vocabulario "placeholder" — un
  campo distinto sin relación con los tres valores de `_estado()`; la
  primera versión de este test tuvo un falso positivo ahí, lo detecté
  corriéndolo y lo corregí antes de darlo por bueno).

**Dientes verificados:** reintroduje `critico` en el comentario de tipo de
`datos.ts`, corrí la clase → falló en
`test_el_comentario_de_tipo_de_cinturon_estado_no_lista_un_fantasma` con:
```
AssertionError: el comentario de tipo de Cinturon.estado lista
{'en_tension', 'critico', 'estable'}, pero _estado() solo emite
{'en_tension', 'tensionado', 'estable'}
```
Restauré el comentario exactamente (`git diff --stat` mostró 1 línea
modificada, la esperada) y la suite volvió a pasar completa (9/9).

## Verificación final

- `python -m pytest tests -q` (proyecto completo): **1958 passed, 3 skipped,
  1 failed, 1 error** — los mismos dos preexistentes declarados fuera de
  alcance (`test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
  y el error de teardown en `test_gestion_privatizaciones_novedades.py`).
  Nada nuevo roto.
- `npx tsc --noEmit` (desde `web/`): limpio, sin salida.
- `npm run build` (desde `web/`): `81 page(s) built`, sin errores. Corrido
  dos veces — una con el snapshot regenerado temporalmente (para leer las
  tablas de I2) y una final con el snapshot committeado restaurado, para
  dejar `web/dist/` (gitignorado) acorde al estado del repo.

**`git status --short` final (repo completo):**
```
 M projects/informe_coyuntura/docs/superpowers/plans/2026-08-08-semaforo-cuatro-colores.md
 M projects/informe_coyuntura/scripts/parametrica.py
 M projects/informe_coyuntura/scripts/publicar.py
 M projects/informe_coyuntura/tests/test_publicar_semaforo.py
 M projects/informe_coyuntura/tests/test_semaforo.py
 M projects/informe_coyuntura/tests/test_web_semaforo.py
 M projects/informe_coyuntura/web/src/lib/datos.ts
 M projects/informe_coyuntura/web/src/pages/metodologia/[id].astro
?? .superpowers/sdd/2026-08-08-semaforo-cuatro-colores/
```
Ningún archivo generado (`output/*`, `web/src/data/*`, `data/historico/*`)
quedó modificado — verificado además por sha256 antes/después de la
regeneración temporal usada para I2.

## Nada más encontrado fuera de los cinco hallazgos

Al recorrer el código para C2/I1 encontré que el bug de C2 afecta
exactamente 12/49 indicadores (conteo exacto, no aproximado) — lo dejo
documentado arriba porque el hallazgo decía "plus seven more" sin
nombrarlos. No encontré ningún otro defecto de alcance comparable en
`_semaforos`, `umbrales_en_unidad` o el resto de la ficha que no estuviera
ya cubierto por los cinco hallazgos. No tengo desacuerdos con ninguno de los
cinco: los cinco eran reales y las correcciones descritas en cada uno eran
correctas tal como estaban planteadas.
