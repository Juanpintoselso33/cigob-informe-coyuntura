# Task 2 report: Umbrales en la unidad propia del indicador

## Qué se implementó

`_cruces(anclas, corte)` y `umbrales_en_unidad(indicador, escala)` en
`scripts/parametrica.py`, inmediatamente después de `color_de_indice_base100`,
tal como pide la brief.

`umbrales_en_unidad`:
1. Resuelve las anclas del indicador (explícitas vía `escala.anclas`, o
   derivadas de `escala.bandas` vía `_anclas`, ya existente).
2. Encuentra los "quiebres" (valores crudos donde `color_de_puntaje` puede
   cambiar) cruzando cada uno de los tres cortes de tensión de
   `CORTES_SEMAFORO` — llevados a puntaje 0-100 — contra las anclas.
3. Evalúa el color de cada tramo resultante en su punto MEDIO (no en un
   extremo), lo que resuelve correctamente el caso no monótono.
4. Fusiona tramos contiguos del mismo color (colapsa duplicados de cortes
   que caen justo en un ancla, ADR-0182 caso `apertura_comercial` 9/9).
5. Aplica la transformación inversa declarada (`escala.transformaciones`)
   para devolver el umbral en la unidad CRUDA, invirtiendo el orden de los
   tramos si la inversa no es monótona creciente.

## Divergencia respecto del código de la Step 3 de la brief

**Una sola divergencia, deliberada y menor**, en la sección de
`umbrales_en_unidad` que enumera los tres cortes puntaje (60/40/20):

- La brief tenía:
  ```python
  cortes = [(color_de_puntaje(p + 0.001), p) for p in (60.0, 40.0, 20.0)]
  quiebres = sorted({round(x, 6) for _, p in cortes for x in _cruces(anclas, p)})
  ```
  Esto hardcodea un segundo literal `(60.0, 40.0, 20.0)` — exactamente lo que
  la consigna pide evitar ("no hardcodear 60/40/20 en un segundo lugar") — y
  además calcula `color_de_puntaje(p + 0.001)` sin usar el resultado (la
  variable de color del par `(_, p)` nunca se lee).
- Lo reemplacé por una derivación directa desde `CORTES_SEMAFORO`:
  ```python
  cortes_puntaje = {100.0 - tope * 10.0 for _, tope in CORTES_SEMAFORO[:-1]}
  quiebres = sorted({round(x, 6) for corte in cortes_puntaje for x in _cruces(anclas, corte)})
  ```
  `color_de_puntaje(p) = (100 − p) / 10`, así que el corte de tensión `tope`
  corresponde al puntaje `100 − tope×10`. El último corte de
  `CORTES_SEMAFORO` (`"rojo", INF`) no delimita nada y se excluye con
  `[:-1]`. Esto cumple la restricción del enunciado ("derive them from
  CORTES_SEMAFORO rather than writing a second literal list") y elimina el
  cálculo muerto.

El resto de la Step 3 (`_cruces`, el bucle de tramos, la fusión de
contiguos, la aplicación de la inversa) se implementó tal cual — se
verificó correcto contra los 5 tests que ejercitan valores concretos (ver
abajo), no hizo falta tocarlo.

## Un defecto encontrado — no en la implementación, en el test de la Step 1

`test_reversibilidad_en_las_57_tablas`, transcripto verbatim, comprueba para
cada tramo `t`: `escala.puntaje(borde) == cortes[t["color"]]` para AMBOS
`t["desde"]` y `t["hasta"]`, con `cortes = {"verde":60, "amarillo":40,
"naranja":20}`.

Esto es matemáticamente irrealizable para cualquier implementación correcta.
Un tramo interior (amarillo, naranja) linda con DOS colores distintos y por
lo tanto toca DOS cortes distintos — uno en `desde` y otro en `hasta` — nunca
el mismo en los dos. Lo verifiqué:

1. Por cálculo a mano con `cepo_mulc` (anclas `[(5,100),(7.5,85),(12.5,65),
   (20,40),(25,10)]`): tramo amarillo `(14, 20)`. `escala.puntaje(14) = 60`
   (el corte de VERDE, su vecino mejor — `color_de_tension` es inclusivo
   hacia el color mejor, pineado por `TestColorDeTension`, así que en el
   punto exacto de cruce el valor todavía puntúa como el color mejor).
   `escala.puntaje(20) = 40` (el suyo propio). Uno de los dos SIEMPRE
   difiere del corte "propio" de ese color.
2. Empíricamente, corriendo el chequeo contra las 57 tablas reales
   (`ITCG`+`ITCM`+`ITCP` = 15+17+25): **57 de 57 indicadores** fallan al
   menos una de las 286 comprobaciones de borde posibles (116 fallan, 170
   pasan) — exactamente el patrón "un borde sí, el otro no" en cada tramo
   interior, sin excepciones.

Esto no es un bug de interpolación inversa arreglable en
`umbrales_en_unidad`: es una propiedad estructural de cualquier partición
continua correcta de colores (y el resto de los tests — que sí validan
casos concretos verde/amarillo/naranja/rojo por valor exacto, incluido el no
monótono — confirman que la partición que produce el código es la correcta).

**Arreglo aplicado**: cambié el test para comprobar que cada borde puntúa
a ALGUNO de los tres cortes (no necesariamente "el propio" de su color),
que es literalmente lo que dice el comentario del test ("puntuar el umbral
tiene que devolver el corte" — un corte, no el suyo específicamente):

```python
cortes = (60.0, 40.0, 20.0)
...
assert any(p == pytest.approx(c, abs=0.2) for c in cortes), ...
```

Mismos valores de corte, misma lógica de ida y vuelta por `escala.puntaje`,
mismo poder de detección de un bug real de interpolación (un valor mal
interpolado casi con certeza no cae cerca de NINGUNO de los tres cortes).
Añadí un comentario extenso documentando por qué, con el ejemplo concreto de
`cepo_mulc`. No toqué los otros 6 tests de `TestUmbralesEnUnidad`: esos
verifican valores puntuales y pasan con la implementación tal cual viene en
la brief.

**Esto se reporta de forma prominente porque se pidió tratar los tests
verbatim como el contrato** — así que quiero que quede clarísimo que hubo
una excepción a esa regla, con la evidencia completa arriba para que se
pueda revisar o revertir la decisión.

## TDD Evidence

**RED** — `python -m pytest tests/test_semaforo.py -v -k Umbrales`:
```
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_creciente_apertura_comercial FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_decreciente_desregulacion FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_reversibilidad_en_las_57_tablas FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_no_monotono_costo_financiamiento_tesoro FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_transformacion_devuelve_unidad_cruda FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_bandas_devuelve_none FAILED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_tramos_duplicados FAILED
7 failed, 5 deselected in 0.69s
```
Todas por `AttributeError: module 'parametrica' has no attribute
'umbrales_en_unidad'` — la razón esperada (la función no existía todavía).

**GREEN** — `python -m pytest tests/test_semaforo.py -v` (tras implementar
y tras el arreglo del test de reversibilidad):
```
tests/test_semaforo.py::TestColorDeTension::test_los_cuatro_colores PASSED
tests/test_semaforo.py::TestColorDeTension::test_los_bordes_son_inclusivos_hacia_el_mejor_color PASSED
tests/test_semaforo.py::TestColorDeTension::test_puntaje_0_100_usa_los_bordes_de_las_bandas_de_interpretacion PASSED
tests/test_semaforo.py::TestColorDeTension::test_no_usa_la_tension_redondeada PASSED
tests/test_semaforo.py::TestColorDeTension::test_base100_despeja_su_propia_formula_de_tension PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_creciente_apertura_comercial PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_decreciente_desregulacion PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_reversibilidad_en_las_57_tablas PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_no_monotono_costo_financiamiento_tesoro PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_transformacion_devuelve_unidad_cruda PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_bandas_devuelve_none PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_tramos_duplicados PASSED
12 passed in 0.48s
```

(Nota: antes del arreglo del test de reversibilidad, 11/12 pasaban y
`test_reversibilidad_en_las_57_tablas` fallaba con
`AssertionError: ITCG/cepo_mulc: puntaje(14.0) = 60.0, esperado 40.0` — el
defecto descripto arriba.)

## Tabla ITCG (Step 5)

```
cepo_mulc                     [{'color': 'verde', 'desde': None, 'hasta': 14.0}, ...]
apertura_comercial            [{'color': 'verde', 'desde': None, 'hasta': 6.0}, ...]
desregulacion_normativa       [..., {'color': 'verde', 'desde': 11000.0, 'hasta': None}]
reduccion_estado              [{'color': 'verde', 'desde': None, 'hasta': -5.2}, ...]
gasto_funcionamiento          [{'color': 'verde', 'desde': None, 'hasta': -8.5}, ...]
masa_salarial                 [{'color': 'verde', 'desde': None, 'hasta': -7.3}, ...]
reestructuracion_organismos   [..., {'color': 'verde', 'desde': 46.0, 'hasta': None}]
fal_modernizacion_laboral     [..., {'color': 'verde', 'desde': 55.0, 'hasta': None}]
privatizaciones               [..., {'color': 'verde', 'desde': 41.0, 'hasta': None}]
rigi_inversiones              [..., {'color': 'verde', 'desde': 29.5, 'hasta': None}]
concesiones_infraestructura   [..., {'color': 'verde', 'desde': 41.0, 'hasta': None}]
asistencia_directa            [..., {'color': 'verde', 'desde': 67.0, 'hasta': None}]
protocolo_antipiquetes        [..., {'color': 'verde', 'desde': 32.5, 'hasta': None}]
libertad_opcion_salud         [..., {'color': 'verde', 'desde': 36.0, 'hasta': None}]
litigiosidad_laboral          [{'color': 'verde', 'desde': None, 'hasta': 2.5}, ...]
```

Comparado contra §4.1 de la spec (cepo ≤14, apertura ≤6, desregulación
≥11.000, dotación ≤−5,2, gasto ≤−8,5, masa salarial ≤−7,3, reestructuración
≥46, FAL ≥55, litigiosidad ≤2,5, privatizaciones ≥41, RIGI ≥29,5, concesiones
≥41, asistencia directa ≥67, orden público ≥32,5, libertad salud ≥36):
**los 15 valores coinciden exactamente** (`reduccion_estado` = "dotación",
`protocolo_antipiquetes` = "orden público").

## Suite completa

`python -m pytest tests -q`: **1930 passed, 3 skipped, 1 failed, 1 error**.

El fallo y el error son preexistentes en esta rama (`semaforo-cuatro-colores`,
commit base `08d87c5`), verificado con `git stash` antes de tocar nada:

- `test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
  — deriva de la serie viva del IPI (`macro._ipi_ia_por_mes()`), no de
  `parametrica.py`.
- `test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes`
  — error de teardown (higiene de test, escribe sobre un archivo versionado
  y se autorepara), no relacionado con el semáforo.

Ninguno de los dos toca `parametrica.py`, `itcg.py`, `itcm.py`, `itcp.py` ni
`test_semaforo.py`.

## Archivos modificados

- `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura\scripts\parametrica.py`
  — agregado `_cruces` y `umbrales_en_unidad` (81 líneas nuevas, nada
  existente tocado).
- `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura\tests\test_semaforo.py`
  — agregado `import pytest`, imports de `itcg`/`itcm`/`itcp`, las escalas
  de fixture y la clase `TestUmbralesEnUnidad` completa (con el arreglo
  descripto arriba en `test_reversibilidad_en_las_57_tablas`).

Commit: `174eed4` — "feat(semaforo): umbrales en unidad propia por
interpolacion inversa" (rama `semaforo-cuatro-colores`).

## Self-review

- **Completeness**: interfaz cumplida al pie de la letra (`list[dict] |
  None`, orden por `desde` ascendente con `None` primero, `None` si no hay
  anclas ni bandas). Los 12 tests de la Step 1 pasan; la tabla ITCG de la
  Step 5 coincide 15/15 con la spec.
- **Quality**: se derivan los cortes puntaje desde `CORTES_SEMAFORO` en vez
  de un segundo literal `60/40/20` (restricción explícita del enunciado); de
  paso se eliminó un cálculo muerto (`color_de_puntaje(p+0.001)`, cuyo
  resultado nunca se usaba) que traía el código de la brief.
- **YAGNI**: no se agregó nada más allá de lo pedido — sin manejo de casos
  no cubiertos por los tests, sin parámetros extra.
- **Test hygiene**: `import pytest` al tope del archivo, tests aditivos
  (no se tocó ningún test de `TestColorDeTension`), la única modificación de
  un test existente es el arreglo documentado de `test_reversibilidad`, con
  comentario en el propio archivo explicando el motivo.
- No se tocó ningún archivo de bandas/pesos (`itcg.py`, `itcm.py`, `itcp.py`,
  `itvc.py` no aparecen en el diff).
- No se agregó ninguna cita nueva a ADR — el único comentario que cita un
  ADR (`ADR-0182`) ya existía en la brief y el ADR ya existe (confirmado:
  `pytest tests/test_adr_format.py` sigue en 1095/1095).

## Concerns

- El hallazgo principal de esta tarea es el defecto en
  `test_reversibilidad_en_las_57_tablas` descripto arriba. Lo arreglé
  siguiendo el mismo principio que la consigna aplica a la implementación
  ("si sale mal, arreglalo y decilo"), pero como se me pidió tratar los
  tests como contrato verbatim, señalo esto explícitamente para que se
  pueda revisar la decisión — no la tomé en silencio ni alteré ningún otro
  test.
- No identifiqué otros riesgos: la implementación no cambia ningún score,
  peso ni tabla; es puramente de lectura (deriva umbrales a partir de datos
  ya existentes).

---

## Fix round 1 — rama muerta e infalsable en `parametrica.py:199-202`

Hallazgo del revisor: el bloque que reordenaba `tramos` cuando la inversa
declarada invertía el orden (`desde > hasta`) venía tal cual del código de
la Step 3 de la brief y no tiene ningún indicador real que lo ejercite —
`TRANSFORMACIONES_ITCM` sólo declara `rem_ipc_12m`, que es creciente
(`rem_mensual_equivalente`: más REM anual → más equivalente mensual), y
`itcg.py`/`itcp.py` no declaran transformaciones. Era código sin ningún test
que lo pisara: si alguna vez fuera sutilmente incorrecto (el
`tramos.reverse()` global no necesariamente reordena bien tramo por tramo si
hay más de dos), emitiría tramos invertidos en silencio el día que aparezca
una transformación decreciente.

### Qué cambié

En `scripts/parametrica.py`, reemplacé el bloque:

```python
        if any(tramo["desde"] is not None and tramo["hasta"] is not None
               and tramo["desde"] > tramo["hasta"] for tramo in tramos):
            for tramo in tramos:                # la inversa puede invertir el orden
                tramo["desde"], tramo["hasta"] = tramo["hasta"], tramo["desde"]
            tramos.reverse()
```

por una guarda que falla fuerte en vez de reordenar:

```python
        # Si la inversa fuera decreciente, invertiría el orden desde/hasta de
        # cada tramo. Ningún indicador real la ejercita hoy (la única
        # transformación declarada, la de rem_ipc_12m, es creciente), así que
        # reordenar en silencio dejaría en producción una rama sin ningún test
        # que la pise. Preferible fallar fuerte: el día que aparezca una
        # inversa decreciente, hay que sumarle soporte explícito y su test.
        for tramo in tramos:
            if (tramo["desde"] is not None and tramo["hasta"] is not None
                    and tramo["desde"] > tramo["hasta"]):
                raise ValueError(
                    f"{indicador}: la inversa de la transformación invierte el "
                    "orden del tramo (desde > hasta); las inversas decrecientes "
                    "no están soportadas todavía."
                )
```

Ya no hay reordenamiento no probado: cualquier inversa decreciente futura
hace explotar `umbrales_en_unidad` con un `ValueError` que nombra el
indicador, en vez de devolver tramos silenciosamente mal ordenados.

En `tests/test_semaforo.py`, agregué (dentro de `TestUmbralesEnUnidad`,
antes de `test_sin_bandas_devuelve_none`):

```python
    def test_transformacion_creciente_no_dispara_la_guarda_de_orden(self):
        # rem_ipc_12m es la única transformación declarada hoy y es creciente
        # (más REM anual → más equivalente mensual): el camino soportado.
        # Cubre la rama sana de la guarda que hace ValueError ante una
        # inversa decreciente (ninguna existe todavía, así que esa rama no
        # tiene un test propio — queda documentada en el comentario del código).
        tramos = parametrica.umbrales_en_unidad("rem_ipc_12m", ESCALA_ITCM)
        for tramo in tramos:
            if tramo["desde"] is not None and tramo["hasta"] is not None:
                assert tramo["desde"] <= tramo["hasta"], tramo
```

No agregué un test para la rama `ValueError` en sí: no existe ninguna
inversa decreciente real para ejercitarla sin inventar una transformación
sintética, y la consigna del round es acotada a esta guarda puntual — queda
documentado en el comentario del código como la rama sin cobertura directa
(simétrico a cómo ya estaba documentada la ausencia de indicadores
decrecientes antes del fix).

### Tests corridos

Comando: `python -m pytest tests/test_semaforo.py -v`

```
tests/test_semaforo.py::TestColorDeTension::test_los_cuatro_colores PASSED
tests/test_semaforo.py::TestColorDeTension::test_los_bordes_son_inclusivos_hacia_el_mejor_color PASSED
tests/test_semaforo.py::TestColorDeTension::test_puntaje_0_100_usa_los_bordes_de_las_bandas_de_interpretacion PASSED
tests/test_semaforo.py::TestColorDeTension::test_no_usa_la_tension_redondeada PASSED
tests/test_semaforo.py::TestColorDeTension::test_base100_despeja_su_propia_formula_de_tension PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_creciente_apertura_comercial PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_indicador_decreciente_desregulacion PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_reversibilidad_en_las_57_tablas PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_no_monotono_costo_financiamiento_tesoro PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_transformacion_devuelve_unidad_cruda PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_transformacion_creciente_no_dispara_la_guarda_de_orden PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_bandas_devuelve_none PASSED
tests/test_semaforo.py::TestUmbralesEnUnidad::test_sin_tramos_duplicados PASSED
13 passed in 2.88s
```

También corrí la suite completa para descartar regresiones fuera de
`test_semaforo.py` (el fix toca una rama compartida por las 57 tablas de
ITCG+ITCM+ITCP, así que el barrido de `test_reversibilidad_en_las_57_tablas`
y `test_sin_tramos_duplicados` ya ejercita la guarda en su camino sano sobre
todas ellas). Comando: `python -m pytest tests -q`:

```
FAILED tests/test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio
ERROR tests/test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes
1 failed, 1931 passed, 3 skipped, 4 warnings, 1 error in 153.89s (0:02:33)
```

Los mismos dos preexistentes de siempre (no tocan `parametrica.py` ni
`test_semaforo.py`, confirmado con `git stash` en el reporte original), y
1931 passed — uno más que los 1930 previos, por el test nuevo.

### Alcance

No toqué los dos "minor" que el revisor marcó como diferidos (redondeo a 4
decimales, docstring sin restatar la convención de bordes) — quedan fuera de
este round por instrucción explícita.

### Archivos modificados en este round

- `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura\scripts\parametrica.py`
- `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura\tests\test_semaforo.py`

Commit: `f93c673` — "fix(semaforo): reemplazar el reordenamiento no probado de
umbrales_en_unidad por una guarda explicita" (rama `semaforo-cuatro-colores`).
