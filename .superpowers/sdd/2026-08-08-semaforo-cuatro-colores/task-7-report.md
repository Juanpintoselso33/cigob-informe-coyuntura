# Task 7 — Los tres ADR · reporte

**Rama:** `semaforo-cuatro-colores` · **Commits:** `0caa41f`, `53b2e74`

---

## Qué dice cada ADR

**ADR-0181 — El color es la tensión que ya se publica, no una escala nueva**
(`aceptado`, transversal, `relacionado: ['0121','0021']`, `continuado_por: ['0182']`).
Plantea que los tres documentos CIGOB de agosto traen tres reglas de color
distintas, y reconstruye de dónde sale cada una: las 15 fichas de Gestión
cortan en puntaje 65/45/25 —verificado exacto contra `BANDAS_ITCG` en 12
indicadores independientes, no es un sistema paralelo sino el motor leído al
revés—; `ITCG_completo_semaforo` propone 85/55/25 justificándolo como el punto
medio entre anclas 100/70/40/10 que el ITCG no tiene (son 100/85/65/40/10 en 13
de sus 15 tablas), y por eso contradice a las fichas del mismo lote en 5 de 14
indicadores. Adopta la opción C, 60/40/20, porque no es una escala nueva: son
los bordes de `BANDAS_INTERPRETACION` que el informe ya publica como etiqueta
de cada índice, y los del ITVC salen de despejar su propia fórmula
`tensión = 5 − (índice−100) × 0,2`. Documenta que la decisión **corrige** una
inconsistencia previa —`semaforoDimension()` pintaba verde a tensión 4 en los
índices 0-100 y a tensión 6 en el ITVC— y deja escrito el efecto **en las dos
direcciones**: los 6 indicadores que mejoran contra la regla de las fichas,
diciendo explícitamente que eso es consecuencia mecánica de bajar los cortes y
no una virtud, y los 6 componentes de vida cotidiana que empeoran (contra 2 que
mejoran), con el ITVC total 90,3 pasando de amarillo a naranja. Registra la
pregunta abierta (si CIGOB conserva la vara vieja para el ITVC, es una
excepción declarada, y revertirla son dos líneas en
`color_de_indice_base100`), la histéresis de dos meses descartada, la colisión
de nombre `semaforo` → `banda_idc` en el indicador `idc`, y que
`verdictDeCinturon(estado)` **no** se unificó a propósito porque sale del enum
editorial que alimenta el BLUF y `score_global`.

**ADR-0182 — Los umbrales del semáforo se calculan, no se escriben**
(`aceptado`, `continua: ['0181']`). Los umbrales en unidad propia no se
escriben en la ficha porque un número copiado a prosa envejece con el dato y
lo hace en silencio: las fichas de agosto se escribieron contra la corrida del
31-jul y una semana después decían RIGI 24,6% (hoy 31,6%) e ITCG 78,22 (hoy
79,4), sin que ningún gate pudiera enterarse porque nada del pipeline lee un
`.docx`. `umbrales_en_unidad` interpola las anclas hacia atrás en los puntajes
60/40/20 y devuelve una **lista de tramos**, no un mapa por color, porque un
color puede aparecer más de una vez: `costo_financiamiento_tesoro` tiene el
óptimo en el medio (anclas `[(−5,20),(−2,5,55),(3,100),(9,75),(16,45),(20,15)]`)
y cada corte lo cruza dos veces — verde es un intervalo cerrado (−1,89 a 12,50),
amarillo y naranja quedan partidos, y del lado izquierdo nunca hay rojo porque
el puntaje satura en 20. Documenta la trampa del redondeo (`aporte_score` viene
a un decimal; 59,9 daría tensión 4,01 → 4,0 → verde), la inversa de la
transformación (`rem_ipc_12m`), la deduplicación cuando el corte cae en un
ancla, la guarda que falla fuerte ante una inversa decreciente, y que los
indicadores sin anclas reciben color pero no tabla. Anota como consecuencia de
la revisión que re-derivar a mano la tensión del ITVC en vez de reusar
`itvc.tension_de_itvc()` puso seis tensiones fuera del dominio 0-10
(`mora_familias` 21,6, `patentamiento_motos` −3,0) sin cambiar ningún color, así
que ningún test de color podía verlo.

**ADR-0183 — Rediseño del cinturón político según el documento de agosto**
(**`propuesto`**, no implementado, `relacionado: ['0048']`). Registra la
propuesta sin aplicarla para que CIGOB la apruebe o la baje sin bloquear el
semáforo. Diez de sus 11 indicadores mapean a indicadores vigentes; *"Postura de
los Sindicatos"* no existe y requiere fuente más el sistema de puntajes por tipo
de acción que el documento esboza. Los 8 que hoy puntúan y el documento no
menciona suman **34,7% del peso del ITCP** (tabla con el peso de cada uno), y la
dimensión conflicto social desaparecería entera. Reabrir la cohesión por cámara
revierte ADR-0048 e invalida la calibración del compuesto bicameral. Lista los
cinco defectos formales de sus umbrales —el hueco 90–99,9% en cohesión, que cae
justo donde vive el indicador (serie 90,3–100,0, media 97,6); el hueco por
encima de 3,0 en ratio DNU con un rojo definido sobre otro eje; los dos ejes
mezclados en designación de jueces; los tramos compuestos del votómetro; y
"Postura Pública de las Cámaras Empresarias" repetido— y explica por qué no se
resolvieron por cuenta propia: cada uno tiene una salida "razonable" que cambia
el puntaje de un indicador publicado, que es lo que ADR-0045 prohíbe.

---

## El rename

| Antes | Ahora |
|---|---|
| `docs/adr/0181-semaforo-de-4-colores.md` | `docs/adr/0181-el-color-es-la-tension-que-ya-se-publica.md` |
| `docs/adr/0182-umbrales-en-unidad-propia.md` | `docs/adr/0182-los-umbrales-del-semaforo-se-calculan.md` |

Hecho con `git mv` (git lo registró como `R`, no como delete+add). Los ids no
cambian.

**Cómo se verificó que nada apuntaba a los nombres viejos**, antes de renombrar:

1. `git grep -n "0181-semaforo-de-4-colores\|0182-umbrales-en-unidad-propia"`
   sobre todo el repo → **2 coincidencias, las dos en `docs/adr/README.md`**
   (líneas 266-267), que es el índice generado y se regenera.
2. El tool `Grep` sobre el árbol completo, que también cubre lo no versionado
   (`.superpowers/`, `_bmad/`) → las mismas 2 coincidencias, nada más.
3. `git grep "ADR-0181\|ADR-0182\|ADR-0183\|adr/0181\|adr/0182\|adr/0183"` para
   ver las citas por **id** (que son las que importan y no cambian): están en
   `scripts/macro.py`, `scripts/parametrica.py`, `scripts/publicar.py`,
   `tests/test_semaforo.py`, `web/src/lib/datos.ts`,
   `web/src/pages/metodologia/[id].astro` y en el plan/spec. Ninguna cita un
   nombre de archivo.

Después del rename, `test_adrs_citados_desde_el_codigo_existen` pasa: las
citas por id siguen resolviendo.

---

## Tests

| Comando | Resultado |
|---|---|
| `python scripts/adr_coherencia.py` | Aplicado · 4 relaciones inversas escritas · 183 filas de índice. Re-corrida posterior: 0 cambios (idempotente). |
| `python -m pytest tests/test_adr_format.py -q` | **1101 passed** |
| `python -m pytest tests -q` | **1950 passed, 3 skipped, 1 failed, 1 error** en 69 s |

Las dos fallas de la suite completa son las conocidas y preexistentes:
`test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
(`assert -2.0 == -1.07`) y el ERROR de teardown en
`test_gestion_privatizaciones_novedades.py::test_la_card_publica_las_pendientes`
(escribe en `data/gestion/privatizaciones_novedades.json`; el guardián de
ADR-0179 lo restaura). Nada nuevo.

---

## Material fuente: lo que no cerraba

Cuatro cosas de la spec no se pudieron sostener tal como estaban escritas. En
los tres casos numéricos gané la aritmética reproducida contra el código, y lo
que quedó en los ADR es el número verificado.

**1. §3.2 se contradice con su propia tabla.** El texto dice *"Tres componentes
mejoran de rojo a naranja y cinco empeoran"*. La tabla de arriba lista **6 que
empeoran** (inseguridad, mortalidad de pymes y empleo registrado 🟢→🟡;
informalidad, ICC UTDT y pluriempleo 🟡→🟠) y **2 que mejoran** (consumo de
carne y despacho de cemento 🔴→🟠). Reconstruí el reparto desde el snapshot con
la regla vieja (`base100`: verde ≥95, amarillo ≥90, rojo <90, de
`datos.ts@f27e7f3^`) y la nueva: antes 8 verde · 3 amarillo · 5 rojo, ahora 5
verde · 3 amarillo · 5 naranja · 3 rojo. Sólo dos de los cinco rojos viejos
(89,3 y 85,7) suben a naranja; los otros tres (peso de tarifas 71,5, alquiler
real 64,3, mora de familias 17,2) siguen rojos. **ADR-0181 dice 6 empeoran y 2
mejoran.** El brief de la Task 7 ya coincidía con la tabla, no con la prosa.

**2. §4.1 y §5 se contradicen entre sí en el caso no monótono, y los tres
números de la derecha están mal.** §4.1 pone el borde superior del verde en
12,52 y §5 en 12,5. Calculado con `umbrales_en_unidad` sobre las anclas reales:
los seis tramos son `−∞ / −3,5714 / −1,8889 / 12,5 / 16,6667 / 19,3333`. Los de
la izquierda coinciden con la spec (−3,57 y −1,89); los tres de la derecha no
(la spec dice 12,52 / 16,68 / 19,35). **ADR-0182 publica los calculados**
(12,50 / 16,67 / 19,33), que además son los que pinea el test.

**3. §4.1 usa el par 1,82% / 24,2% como si fueran un umbral de
`rem_ipc_12m`.** No lo son: 24,2% anual ≡ 1,82% mensual es un **valor**, y el
valor vigente hoy es 22,3% anual. El corte de verde es 2,80% mensual ≡ 39,29%
anual (verificado con las dos direcciones de la transformación declarada).
**ADR-0182 usa el par correcto** y explica cuál es el valor y cuál el corte.

**4. La ficha no declara la ausencia de umbrales; la omite.** §4.1 pedía que en
los indicadores sin anclas *"la ficha declara que este indicador no tiene
umbrales en unidad propia y por qué"*. Lo implementado en
`web/src/pages/metodologia/[id].astro` es `{ind?.semaforo?.umbrales && (…)}`: la
sección sencillamente no se renderiza. No hay ningún texto en `web/src/` que
diga "no tiene umbrales" (grepeado). No engaña —no hay tabla falsa— pero un
lector que compare dos fichas ve una diferencia sin explicación. **ADR-0182 lo
describe como está y lo deja anotado como pendiente declarado**, no como si
estuviera hecho. Es una tarea de una línea en la rama negativa, en Task 6, no
mía: no toqué código.

**Lo que no se pudo verificar contra nada**, porque los cuatro `.docx` de CIGOB
no están en el repo: el "5 de 14 indicadores" de discrepancia del doc
`ITCG_completo`, los umbrales concretos de las fichas citados en §1.1(a)
—aunque sí verifiqué dos de ellos contra el código: `apertura_comercial` tiene
un ancla exacta en `(5,25 ; 65)` y `desregulacion_normativa` da 65,0 / 45,0 /
25,0 en 13.300 / 7.250 / 3.850— y los nombres de las 6 dimensiones del
documento político. En ADR-0183 esto queda dicho explícitamente en una sección
"Sobre la trazabilidad de este ADR": lo reproducible desde
`itcp.DIMENSIONES_ITCP` (los 8 no mencionados, el 34,7%, los 10 que mapean) se
marca como reproducible, y los nombres de dimensión no se transcriben para no
fijar como cita algo que no se puede comprobar.

---

## Archivos tocados

Commit `0caa41f`:

- `docs/adr/0181-semaforo-de-4-colores.md` → `0181-el-color-es-la-tension-que-ya-se-publica.md` (reescrito: 43 → 285 líneas)
- `docs/adr/0182-umbrales-en-unidad-propia.md` → `0182-los-umbrales-del-semaforo-se-calculan.md` (reescrito: 37 → 218 líneas)
- `docs/adr/0183-rediseno-del-cinturon-politico.md` (nuevo, 209 líneas)
- `docs/adr/README.md` (índice **generado**)
- `docs/adr/0021-…md`, `docs/adr/0048-…md`, `docs/adr/0121-…md` — **sólo
  frontmatter, escrito por `adr_coherencia.py`**: la relación inversa
  `relacionado: ['0181']` en 0021 y 0121, y `relacionado: ['0183']` en 0048.

Commit `53b2e74`: correcciones de autorrevisión en 0181 y 0182 (ver abajo).

**Desviación del brief:** el `git add` del brief listaba sólo
`0181-* 0182-* 0183-* README.md`. Agregué también 0021/0048/0121 porque son
salida del mismo `adr_coherencia.py` y dejarlos fuera habría dejado el árbol
sucio con las relaciones inversas a medio escribir. Se stagearon
explícitamente, uno por uno, nunca con `git add -A`. El mensaje de commit es el
del brief, con el cuerpo detallando el contenido.

---

## Autorrevisión

Repasé cada número de los tres documentos contra la spec o contra el código.
Encontré y corregí dos afirmaciones mías que el código no respaldaba (commit
`53b2e74`):

1. **ADR-0181 sobreafirmaba el alcance del test de invariancia.** Escribí que
   comparaba "los índices y las dimensiones". `_indices_y_score` en
   `test_publicar_semaforo.py` compara los cuatro índices y `score_global`; las
   dimensiones **no** están cubiertas. Corregido a lo que el test hace, más la
   nota de que es invariancia directa (mismo snapshot antes/después) y no
   comparación contra fixture congelada.
2. **ADR-0182 leía como si la card de `rem_ipc_12m` mostrara 39,29%.** Muestra
   22,3%. Reescrito para distinguir valor de corte.

Verificados contra el código, no sólo copiados de la spec: los cortes de
`BANDAS_INTERPRETACION` (20/40/60/80); que 13 de las 15 tablas del ITCG usan
100/85/65/40/10 y cuáles son las dos excepciones (`desregulacion_normativa`
100/85/60/35/10, `fal_modernizacion_laboral` 100/50/10); las anclas y los seis
tramos de `costo_financiamiento_tesoro`; que el corte de 40 de
`apertura_comercial` cae sobre un ancla exacta (9,0 ; 40,0), que es el caso de
deduplicación; los seis puntajes y valores de la tabla de efecto (43,0 · 64,5 ·
61,0 · 63,5 · 44,6 · 22,0); los 16 índices del ITVC y su total 90,3; las 57
tablas (17 ITCM + 15 ITCG + 25 ITCP); los 18 indicadores que puntúan en el ITCP
y el 34,7% de peso de los 8 no mencionados; el rango 90,3–100,0 y la media 97,6
de la serie de `cohesion_bloque`; y la regla vieja de `semaforoDimension`
recuperada de `git show f27e7f3^`.

La sección de efecto honesto conserva **las dos mitades** y no las separa: la
tabla de los 6 que mejoran va inmediatamente seguida de la frase que dice que
mejorar era mecánicamente inevitable, y de la tabla de vida cotidiana con el
ITVC pasando a naranja. Ninguna de las dos está en "Más información": las dos
están en `### Consecuencias`.

---

## Preocupaciones

1. **Un ADR `propuesto` que nadie mire es una decisión postergada sin fecha.**
   ADR-0183 está escrito para que CIGOB decida, pero no hay ningún mecanismo en
   el repo que recuerde que hay una decisión pendiente. Está dicho en el propio
   ADR como contra de la opción elegida, pero conviene que alguien se lo lleve a
   CIGOB.
2. **La pregunta abierta del ITVC llega al sitio antes que la respuesta.** Con
   la Task 8, vida cotidiana va a mostrarse en naranja en producción con la vara
   unificada. Si CIGOB quería la vara vieja, lo va a ver publicado antes de
   opinar. Está declarado en ADR-0181 y revertirlo son dos líneas, pero el orden
   es ese.
3. **El pendiente de la ficha sin umbrales (punto 4 de arriba) es código, no
   documentación**, así que lo dejé anotado en ADR-0182 sin tocarlo. Si se
   arregla, hay que actualizar ese párrafo del ADR.
4. **`test_adr_format.py` no mira el cuerpo de ningún ADR.** Todo lo que
   verifiqué a mano acá —que los números coincidan con el código— no tiene gate.
   Si mañana se recalibra una banda, las cifras citadas en 0181/0182 envejecen
   exactamente igual que envejecieron las fichas de agosto, que es el problema
   que 0182 documenta. No es nuevo ni específico de esta tarea; vale anotarlo.

---

# Fix round 1/5 — dos hallazgos Important de la review

**Commit:** `8b4d9cf` · Los cinco Minor quedan diferidos, no se
tocaron.

## I-1 — `0181`: enum inexistente y flujo de datos invertido

**Verificado contra el código antes de escribir nada** (no se aceptó el
hallazgo de palabra):

| Afirmación | Verificación |
|---|---|
| `_estado()` emite tres valores, no cuatro | `scripts/publicar.py:342-348` y `scripts/generar_informe.py:63-68`: `estable` / `en_tension` / **`tensionado`**. |
| `alerta` / `critico` no los produce nada en `scripts/` | `grep -rn "'alerta'\|'critico'"` → sólo `generar_informe.py:152/163` y `bigquery_export.py:98`, que son un **campo distinto** (`cinturon.alerta = "multicinturon"`, `null` en los cinco del snapshot) y `datos.ts:233`. Ninguna ocurrencia asigna esos valores a `estado`. |
| El snapshot vivo | `estable`×2 (gestión 2,1 · espíritu 0,7), `en_tension`×2 (macro 3,8 · política 3,3), `tensionado`×1 (vida cotidiana 6,9). |
| `score_global` no lo alimenta `estado` | `recomputar_vida_y_global` (`publicar.py:351-361`) es la media ponderada de `c["score"]` por `PESOS_CINTURONES`. `_estado()` recibe el score como argumento: la causalidad va score → estado, no al revés. |
| La rama muerta | `verdictDeCinturon` (`datos.ts:231-235`) ramifica `estado === "critico" \|\| estado === "alerta"` → rojo; `tensionado` cae en el `else` → **amarillo**. |
| El alcance del daño | `cinturonesRojos` (`datos.ts:525-527`) es siempre 0, y lo consumen `Hero.astro`, `Archivo.astro`, `Metodologia.astro` y `TensionPanel.astro`. Además `Bluf.astro:10` arma `porVerdict("rojo")` con la misma función, así que la frase *"está en zona crítica"* (`Bluf.astro:25`) no puede dispararse. |

**Qué cambié.** Dos ediciones en `0181-el-color-es-la-tension-que-ya-se-publica.md`:

1. El párrafo de "Más información" (antes líneas 272-274). La conclusión —no
   unificar el chip con el semáforo— se mantiene; se reemplazó su
   justificación. Ahora dice que el `estado` lo deriva `_estado()` **del score
   0-10 agregado del cinturón** contra `UMBRALES`, con el vocabulario real de
   tres valores, y que lo consumen el BLUF, el panel de tensión, la frontada y
   `cinturonesRojos`. Se quitó `score_global` de la lista de consumidores y se
   agregó un párrafo corto que fija el sentido de la derivación (score →
   estado) y aclara que `score_global` es el promedio ponderado de los
   **scores**, sin pasar por `estado`. El argumento pasó de "sería un cambio de
   índice" (falso) a "es otro concepto y reemplaza una lectura en cuatro
   componentes editoriales" (que es lo que el código sostiene).
2. **Consecuencia nueva en `### Consecuencias`**, encabezada
   `HONESTIDAD SOBRE EL EFECTO` —el registro que el repo ya usa para esto—:
   describe la rama muerta, que `cinturonesRojos` es estructuralmente 0 y que
   el sitio no puede mostrar un cinturón rojo; dice que es preexistente y
   **fuera de alcance a propósito**; y da el caso visible de hoy —vida
   cotidiana `tensionado`, ITVC 90,3 en naranja, chip en amarillo, en la misma
   página—. Cierra explicando por qué se anota acá: este ADR pasó a ser el
   único documento que describe `verdictDeCinturon`, y una descripción que no
   mencione la rama muerta se lee como que la función anda.

**No se tocó código.** `datos.ts` no está en el diff.

## I-2 — `0183`: ADR-0045 no prohíbe nada

**Verificado leyendo ADR-0045 completo.** Es la recalibración de
`BANDAS_ITCP["comisiones_caidas"]` del 2026-07-09: las anclas viejas (30/50/70/85)
dejaban los 32 meses en la banda del piso porque el piso estructural observado
del indicador es 94,7%. Anclas nuevas 96/97/98/99; el valor vigente pasa de
puntuar 10 a ~60 y **el ITCP sube ~3 puntos** (tensión 3,3 → 2,9). El ADR
argumenta explícitamente *"No es maquillaje"*. Es decir: es un precedente de
recalibración legítima **bajo condiciones**, no una prohibición. La cita era
falsa y, peor, invitaba a un lector a encontrar lo contrario de lo que yo
afirmaba.

**Qué cambié.** Se reescribió el párrafo "Por qué esto no se resolvió por
cuenta propia":

- Se agregó lo que el argumento realmente necesitaba: que las cinco salidas
  "razonables" se elegirían **después** de ver el número que producen.
- Se cita **ADR-0105 — Regla para las anclas nuevas, con trinquete**, que sí
  establece la regla: orden de justificación (referencia externa → valor con
  significado propio → historia previa a dic-2023 → convención calibrada sobre
  el rango observado) y la exigencia de documentar la búsqueda de las tres
  primeras aunque falle. Verificado leyendo 0105 antes de citarlo: dice
  literalmente *"ahí todavía se puede elegir el criterio **antes** de mirar el
  dato"*. Las cinco salidas son la cuarta opción tomada de entrada.
- Se conserva ADR-0045, pero **descripto por lo que es**: el precedente de que
  las bandas del ITCP sí se pueden tocar cuando el argumento sale de la
  estructura de la métrica y no del resultado. Ese es el estándar que los cinco
  tramos del documento no alcanzan.
- El frontmatter no cambia: 0105 y 0045 se citan en prosa, como este ADR ya
  hace con otros, para no arrastrar back-references generadas a dos archivos
  más.

## Comandos

```
$ python scripts/adr_coherencia.py
Aplicado:
  relaciones inversas escritas: 0
  ADR marcados como superados:  0
  filas del índice:             183

$ python -m pytest tests/test_adr_format.py -q
1101 passed in 7.80s
```

`adr_coherencia.py` no escribió ninguna relación nueva y el índice del README no
cambió (los títulos son los mismos), así que esta ronda toca **sólo** los dos
ADR editados: `0181-el-color-es-la-tension-que-ya-se-publica.md` (+44/−16 con el
contexto) y `0183-rediseno-del-cinturon-politico.md`. Ningún archivo de código.
