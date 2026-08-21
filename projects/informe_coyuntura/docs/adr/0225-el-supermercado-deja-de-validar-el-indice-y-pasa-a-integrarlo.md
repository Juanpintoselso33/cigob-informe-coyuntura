---
madr: 4
id: '0225'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [consumo_supermercados]
archivos: ['scripts/vida_cotidiana/collectors/indec_supermercados.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/panel_validacion.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'tests/test_itvc.py']
cierra: ['0155']
relacionado: ['0031', '0045', '0108', '0130', '0153', '0159', '0161', '0162', '0163', '0167', '0176', '0216', '0219', '0223', '0226']
ambito: 'ITCIS · dimensión de ingresos y consumo · validación externa del cinturón'
origen: 'Pedido del editor: buscar una validación externa que sea UN SOLO INDICADOR, no el factor común de varias'
---

# ADR-0225 — El supermercado deja de validar el índice y pasa a integrarlo

## Contexto y planteo del problema

El editor abrió con una objeción sobre la **forma** de la validación externa:

> «Buscar alguna validación externa que sea UN SOLO INDICADOR. No se entiende
> esto que hicimos de comparar con el factor común de varias variables. Tiene
> que ser contra una que sea un BUEN validador, no cualquier cosa que
> correlacione bien.»

La investigación que siguió confirmó la objeción y terminó en otro lado. Lo que
se encontró al medir el panel vigente:

- **El factor común explica el 37,6% de la varianza** de sus cuatro series. Casi
  dos tercios del movimiento del panel no es común: el compuesto que se
  construyó en [[0161-el-contraste-externo-es-un-factor-comun-no-una-variable]]
  para dejar de medir «una faceta publicada como el todo» terminó midiendo otra
  faceta, más difícil de nombrar.
- **Por la propia prueba del proyecto rinde peor que el ancla que reemplazaba.**
  [[0162-aporte-del-indice-por-encima-de-la-tendencia]] fijó el aporte
  incremental de R² sobre una tendencia como vara. El factor da **0,006 con
  signo negativo**; el ancla de supermercados, **0,347 con signo positivo**. Dos
  órdenes de magnitud, y en la dirección del editor.
- **El panel no está entregando la validez discriminante para la que se
  construyó**: la brecha convergente-discriminante del ITCIS es **+0,004 en
  niveles y −0,030 en diferencias**. El índice se parece a las estadísticas
  ajenas tanto como a las propias.
- Y la correlación más alta de las catorce del panel —**+0,564 en niveles,
  +0,508 en los cambios**— la tiene el **Índice Líder de la UTDT**, que es del
  terreno del ITCM.

Con eso sobre la mesa, el editor no aceptó la recomendación de volver al ancla
única. Dijo:

> «No me convence la verdad solo ventas de supermercados, lo pondría como
> indicador, no como validación externa.»

Y el argumento es más fuerte que el que traía la investigación: **las ventas en
supermercados a precios constantes miden condiciones materiales del hogar**. Si
lo hacen, son un componente del ITCIS, no un juez del ITCIS. Es la versión suave
del problema que sacó al ICC en [[0155-el-ancla-del-itvc-pasa-a-ser-el-consumo-medido]],
y la regla editorial que ordenó todo lo que sigue:

> «No vamos a privar al índice de validez, robustez y capacidad por tener un
> validador externo que es un accesorio.»

**El índice manda; el ancla se elige de lo que queda.**

## Factores de decisión

- Un indicador no puede ser componente y juez del mismo índice.
- Antes de mover un indicador hay que medir si duplica señal: el criterio del
  cinturón es la matriz de redundancia con umbral 0,7
  ([[0108-redundancia-interna-del-itvc]]), en niveles y destendenciado.
- Las altas ceden proporcionalmente y conservan el orden relativo
  ([[0130-empleo-registrado-entra-al-itvc]], [[0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto]],
  [[0219-el-trabajo-independiente-es-la-contracara-del-cierre-de-pymes]]). El peso nominal de la
  dimensión no se toca.
- Un ancla se elige por su correlación en primeras diferencias, no en niveles
  ([[0167-el-ancla-de-validacion-se-elige-en-diferencias]]).
- No se mueve ningún peso ni ninguna ancla para que un número quede mejor
  ([[0045-no-mover-pesos-para-que-un-test-de-mejor]]).

## Opciones consideradas

- **El supermercado entra como componente y el cinturón se queda sin ancla
  única, publicando el panel** — elegida.
- **Volver al ancla única de supermercados**, con el panel de respaldo en la
  ficha metodológica — era la recomendación de la investigación y el editor la
  rechazó: valida el índice contra algo que mide lo mismo que el índice.
- **Promover el consumo privado de Cuentas Nacionales a ancla ya** — descartada
  por muestra: nueve trimestres (ver abajo).
- **Elegir como ancla la mensual con mejor correlación** (naftas, +0,400 en
  diferencias) — descartada: es exactamente «cualquier cosa que correlacione
  bien», y su precio es un regulado que el índice ya puntúa en `peso_tarifas`.

## Decisión

### 1. `consumo_supermercados` entra al ITCIS con 20% de la dimensión de ingresos

Ventas a precios constantes, **serie desestacionalizada del INDEC**
(`455.1_VENTAS_PREADA_0_M_44_44`). Los cinco componentes previos ceden ×0,80 y
conservan su orden relativo; el peso nominal de la dimensión no se toca.

| componente | interno antes | interno después | efectivo después |
|---|---:|---:|---:|
| `brecha_salario_cbt` | 59,59% | 47,67% | 13,38% |
| `pobreza_nowcast` | 32,53% | 26,02% | 7,30% |
| **`consumo_supermercados`** | — | **20,00%** | **5,61%** |
| `consumo_carnes_total` | 3,92% | 3,14% | 0,88% |
| `motorizacion_total` | 3,96% | 3,17% | 0,89% |

**Por qué 20%, fijado antes de mirar el efecto.** En esta dimensión
`brecha_salario_cbt` mide la capacidad de comprar y `pobreza_nowcast` cuenta a
quién no le alcanza: las dos son estructurales. Los únicos rastros de compra
*realizada* eran la carne y la motorización, que juntos no llegan al 8% de la
dimensión. El supermercado mide la canasta cotidiana entera, con 113 meses de
historia, así que tiene que pesar bastante más que esos tres y bastante menos
que las dos estructurales. 20% es el número redondo de esa banda.

### 2. La cesión proporcional se escribe como REGLA, no como decimales

`itvc.alta_proporcional(previos, nuevo, peso)`. Hasta acá cada alta dejaba en el
código los pesos ya multiplicados y la regla vivía en un comentario al lado.
Eso funciona hasta que dos altas se cruzan: los pesos previos cambian y unos
decimales calculados a mano quedan inválidos **en silencio**. Escrita como
función, la cesión se recalcula sobre lo que efectivamente haya en la dimensión.

Tiene además la consecuencia de volver testeable la regla en sí —que la cesión
sea proporcional, que conserve el orden, que no se pueda pisar un componente
existente— en lugar de testear cinco números.

**Y el caso que lo justificó apareció el mismo día.** Este alta se escribió
cuando la dimensión tenía cinco componentes —los dos vehículos por separado— y
[[0224-puntua-la-motorizacion-total-no-cada-vehiculo]] los fundió en
`motorizacion_total` mientras esta rama estaba abierta. Con los decimales
calculados a mano, el merge habría dejado una dimensión cuyos pesos no suman uno
**sin que ningún test lo dijera**, porque los tests fijaban los mismos números
que el código. Con la regla escrita como regla, la cesión se recalculó sola sobre
los cuatro componentes que quedaron y lo único que hubo que resolver fue el dict
de entrada.

Ese mismo choque dejó una segunda lección, y se aplicó dos veces: un test que
fija **decimales absolutos** se rompe con cualquier alta posterior y, peor,
*parece* denunciar que se rompió el invariante que cuida. Tanto el espejo
autos/motos de [[0223-el-espejo-de-las-motos-el-patentamiento-de-autos]] como el
peso de `motorizacion_total` se reescribieron como **razones con tolerancia**
—cuánto pesa un componente EN RELACIÓN a los otros—, que es lo que la cesión
proporcional conserva por construcción y lo que un cambio de contrabando sí
rompería.

### 3. Sale del panel de validación, y con él su plumbing de ancla

Se va de `panel_validacion.FAMILIA` (que pasa de 7 estadísticas propias a 6), de
`ETIQUETAS` y `FUENTES`, del registro de anclas que vigila G7
([[0176-las-anclas-de-validacion-tienen-quien-las-mire]]) y de
`validacion_externa`, donde se borran su descarga duplicada y las cuatro
correlaciones ITVC-vs-consumo. Su frescura la vigila ahora `MAX_DIAS`, como la
de cualquier componente.

### 4. El ITCIS se queda sin ancla única y publica el panel

El titular pasa a ser el **factor común de los volúmenes físicos consumidos por
el hogar** —luz, gas, transporte, combustible—, que es contra lo que el gráfico
ya venía comparando. La sección **dice por qué no hay una sola serie enfrente**,
porque esa explicación es parte del resultado y no una disculpa.

Un detalle que era fácil pasar por alto: la matriz de validación cruzada
([[0031-matriz-de-validacion-cruzada]]) lee `validacion.pares` del bloque del
ITCIS. Dejarla apuntando al supermercado habría vuelto **circular la matriz
entera** sin que ningún test avisara. `pares` sale ahora del factor y la columna
se renombra de `consumo` a `volumen_hogar`.

### 5. El consumo privado de Cuentas Nacionales queda declarado como referencia en formación

Es el reemplazo conceptualmente correcto y está identificado: no es un canal del
consumo del hogar sino **su agregado**, que es lo que el cinturón dice medir.
[[0163-el-itvc-se-contrasta-contra-volumenes-fisicos-del-hogar]] evaluó índices
salariales, carne, patentamientos y los tres canales de comercio; el agregado de
cuentas nacionales no aparece en esa lista, y ése era el hueco.

No puede usarse todavía y el motivo se publica: es trimestral y arranca junto
con la base del índice, así que son **nueve trimestres**. Su correlación en
primeras diferencias es +0,348, pero el jackknife —sacar un trimestre por vez—
la mueve entre **0,167 y 0,726**. Un número que depende de cuál dato se quite no
es un número publicable.

Tres cosas quedan fijadas por adelantado para que la promoción no dependa de
mirar el resultado el día que llegue:

- **Umbral**: pasa a ser la serie de referencia cuando acumule **20 trimestres**,
  hacia fines de 2028.
- **Solapamiento declarado**: el consumo privado *contiene* a las ventas en
  supermercados, que ahora son componente. Medido contra las series a precios
  corrientes del INDEC, la encuesta de supermercados es el **4,49% del consumo
  privado** en promedio del período (5,68% en el 4T-2023, 3,68% en el 1T-2026).
  El acoplamiento existe, es de segundo orden y se publica.
- **Rezago**: el 1T-2026 se publicó el 23-jun-2026, 84 días después del cierre
  del trimestre.

### Consecuencias

#### El costo, medido

La familia del ITCIS en el panel pasa de 7 estadísticas a 6, y la brecha
convergente-discriminante **empeora en niveles de +0,004 a −0,052**. En
diferencias se mueve poco: de −0,030 a **−0,035**. Es un costo real, y es chico
sobre todo porque la prueba ya no discriminaba.

Los dos números no son estrictamente comparables y conviene decirlo: el «antes»
se midió sobre el índice de 18 componentes y el «después» sobre el de 19, así
que parte del movimiento es que el índice cambió, no sólo el panel. El
diagnóstico no depende de esa distinción —una brecha que pasa de +0,004 a −0,05
sigue diciendo que no discrimina— pero leerlos como un antes/después limpio sí
sería sobreafirmar.

Y hay un resultado que la corrida deja a la vista, contra el índice nuevo: en la
matriz de validación cruzada el ITCIS correlaciona **+0,48 en niveles con la
actividad** (par del ITCM) contra **−0,09 con su propio contraste**. En los
cambios mes a mes el orden se corrige (+0,45 contra el propio, +0,52 con la
actividad) pero sigue sin separarse. Se publica: es el mismo criterio con el que
[[0159-validacion-por-panel-para-los-socioeconomicos]] publica el caso que no
confirma.

#### El límite duro, para que nadie lo cruce sin darse cuenta

[[0161-el-contraste-externo-es-un-factor-comun-no-una-variable]] exige **tres
series como mínimo** para estimar un factor. El del ITCIS se arma con cuatro
volúmenes físicos. Con el supermercado afuera la familia queda en 6 y el factor
sigue en 4; **si la electricidad también pasara a componente, el factor quedaría
en 3, es decir en el borde. Una tercera alta desde el panel deja al ITCIS sin
factor común**, como el ITCG.

#### La próxima alta candidata está nombrada y medida

**La demanda eléctrica residencial de CAMMESA.** Es la serie más limpia de las
ocho evaluadas: su correlación más alta contra cualquier componente del ITCIS es
**+0,296** (`pluriempleo`), el 69% de su nivel y el 73% de su movimiento mes a
mes son información que el índice no reproduce, tiene 259 meses de historia y
tres semanas de rezago —la fuente más rápida del panel—.

Se deja **para su propio movimiento y no se arrastra en éste**: el cinturón
viene haciendo una alta por vez y eso es lo que permite atribuir el efecto.
Queda además anotado lo que se midió y salió distinto de lo esperado: se
sospechaba doble conteo con `peso_tarifas` —el hogar consume menos luz porque
subió la tarifa, y la tarifa ya se puntúa— y **el número no lo sostiene**
(−0,159 en niveles, +0,010 en los cambios). Lo que sí la frena es que al 20%
sube el `|Δmes|` del índice de 1,11 a 1,43 con un cambio de nivel de −0,6: más
ruido, no más señal.

#### Lo que la revisión hacia atrás descartó

Se corrió la misma prueba sobre las seis estadísticas restantes del panel.
Fallan la redundancia: `consumo_mayoristas` (−0,80 contra `patentamiento_motos`),
`consumo_shoppings` (−0,78 contra `alquiler_real`) y `ventas_naftas` (+0,70
contra `brecha_salario_cbt`, justo en el umbral). Pasan la redundancia pero no
el concepto: `transporte_pasajeros` (signo ambiguo — menos viajes puede ser menos
actividad o sustitución del auto al colectivo) y `gas_residencial` (14,5% de
estacionalidad residual declarada, y −0,381 en niveles contra el índice).

## Más información

### Por qué mejora al índice, medido antes de incorporarlo

Regresando el candidato sobre las **seis dimensiones del ITCIS**: el **43% de su
nivel** y el **82% de su movimiento mes a mes** no los puede reproducir el
índice con todo lo que ya tiene. No es una serie que el ITCIS contenga
disfrazada.

Y el argumento de construcción, que pesa más que el número: **es el único
componente que mide volumen efectivamente comprado.** Los otros dieciocho miden
lo que entra (ingresos), lo que cuesta (precios), de dónde sale ese ingreso
(empleo), lo que no se paga (mora), lo que se opina (percepción) o el delito
sufrido. Ninguno miraba lo que el hogar se llevó de la góndola.

### El par alto con `pobreza_nowcast`, tratado de frente

Contra `pobreza_nowcast` da **−0,758 en niveles** (n=20) y **−0,093 al
destendenciar**. Es el único par del candidato por encima del umbral, y no se
esconde.

Lo que cambia su lectura es el contexto de la matriz, que hay que mirar entero:

- la matriz de los 17 componentes previos tiene **42 pares sobre 0,7 de 136**
  (31%), 33 de ellos entre dimensiones distintas;
- **13 de los 17** componentes tienen al menos un par alto — `mortalidad_pymes`
  tiene once, `trabajo_independiente` diez, `empleo_registrado` ocho;
- y **`pobreza_nowcast` ya arrastra cinco**: −0,883 con la mora, +0,877 con
  motos, −0,852 con trabajo independiente, −0,738 con mortalidad de PyMEs y
  −0,706 con empleo registrado. El par con el supermercado sería el sexto y
  quedaría **por debajo de tres de ellos**.

Vetar al que entra por 0,758 sería aplicarle un estándar que trece de los
diecisiete que ya están adentro no cumplen. Es la época en común que
[[0108-redundancia-interna-del-itvc]] documentó para todo el cinturón, no señal
repetida: el |r| medio de la matriz cae de 0,488 en niveles a 0,190 al
destendenciar. El precedente real de baja por redundancia —`endeudamiento_familiar`
en [[0154-endeudamiento-e-indice-lider-salen-del-itvc]]— fue con **0,943 y dos
motivos más**.

En primeras diferencias, que es donde se cuenta dos veces lo que se promedia, el
máximo del candidato contra cualquier componente es **+0,345** (`despacho_cemento`).

### Lo que se midió y no se cumplió

Antes de buscar candidatos se registró qué tendría que moverse en el mundo si el
ITCIS mide bien, y con qué signo. Dos predicciones fallaron y se anotan como
resultado y no como excusa:

| candidata pre-registrada | esperado en diferencias | medido |
|---|---|---|
| Turismo interno (viajeros residentes, EOH-INDEC) | +0,25 a +0,45 | **−0,104** (desestacionalizada, n=24) |
| Espectadores de cine (INDEC) | mismo canal «postergable» | **−0,290** (desestacionalizada, n=30) |

**El canal del gasto postergable no valida este índice.** La lectura sustantiva
es que esas series están dominadas por los deciles altos y por precios relativos
ajenos al hogar: el turismo interno cayó en 2025 con el dólar barato porque los
argentinos viajaron afuera, no porque estuvieran peor. Un validador cuyo signo
depende del tipo de cambio no es un validador.

### El contraejemplo que explica el pedido del editor

La **recaudación real de IVA** da +0,554 en niveles y **+0,392 en diferencias**:
el segundo mejor de todo el conjunto. Y no sirve. Incluye IVA-DGA sobre
importaciones, que no tiene nada que ver con el hogar, y en dic-2023 se dio de
baja la devolución del IVA de alimentos, lo que subió la recaudación por decisión
administrativa y no por consumo. Correlaciona bien por los motivos equivocados,
que es exactamente lo que el editor pidió evitar.

### El rezago, medido y no copiado

Encadena dos demoras: el INDEC publica el mes M unos **52 días** después de
terminado (el informe de junio-2026 salió el 21-ago-2026) y la API de
datos.gob.ar tarda **~13 días más** en espejarlo (mayo-2026 apareció el
5-ago-2026). El último punto disponible tiene entre **95 y 126 días** según en
qué parte del ciclo caiga la corrida, así que `MAX_DIAS` es **140**: el default
de 110 habría marcado atraso todos los meses.

### Confirmación

- `tests/test_itvc.py` fija los pesos resultantes y prueba la regla de cesión
  como regla —proporcionalidad, orden conservado, alta duplicada, peso fuera de
  rango— en vez de fijar cinco decimales.
- `tests/test_panel_validacion.py::test_ninguna_estadistica_del_panel_es_componente_de_un_indice`
  es la guarda que impide volver atrás: si el supermercado reapareciera en el
  panel, falla.
- `tests/test_redundancia_itvc.py` verifica que la matriz publicada cubra todos
  los componentes que puntúan, así que el nuevo entra solo.
