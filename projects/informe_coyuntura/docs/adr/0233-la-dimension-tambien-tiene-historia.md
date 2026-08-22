---
madr: 4
id: '0233'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'transversal'
archivos: ['scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/bigquery_export.py', 'tests/test_series_dimensiones.py', 'web/src/components/DimensionesEvolucion.astro', 'web/src/lib/sparkline.ts', 'web/src/lib/datos.ts', 'web/src/pages/[slug].astro']
relacionado: ['0019', '0020', '0033', '0045', '0067', '0082', '0086', '0108', '0109', '0154', '0169', '0180', '0197', '0208', '0209', '0224', '0226']
ambito: 'Los cuatro índices · la serie mensual por dimensión: qué se publica, cómo se agrega, qué se hace con los huecos'
origen: 'Editor, 21-ago-2026: el informe publica la serie del índice y la de cada componente, pero «la capa del medio —las dimensiones— sólo existe como el valor del mes actual», así que no se puede ver qué dimensión explica el movimiento'
---

# ADR-0233 — La dimensión también tiene historia

`scripts/validacion_externa.py` · `scripts/publicar.py` · `scripts/bigquery_export.py`
- **Relacionados**: [[0019-validacion-y-robustez-del-indice]] (la reconstrucción
  histórica de la que sale todo esto), [[0197-piso-de-cobertura-de-las-series-reconstruidas]]
  (el criterio de qué mes se publica y cuál no),
  [[0082-los-componentes-se-derivan-del-indice-no-se-listan-a-mano]] (la regla
  que evita dos definiciones del mismo conjunto),
  [[0033-winsorizacion-asimetrica-del-itvc]] (el techo, que se aplica al
  componente), [[0020-dimension-critica]] (el otro atributo de dimensión que ya
  se publica), [[0180-espejo-en-bigquery]] (el archivo histórico)

## Contexto y planteo del problema

El informe publica dos capas: la **serie del índice** —31 a 33 meses
reconstruidos desde las series de sus componentes— y la **serie de cada
componente**, dieciocho en el ITCIS. Entre las dos hay una tercera que el índice
usa en cada cuenta y que nunca se publicó hacia atrás: la **dimensión**. Existía
sólo como el `puntaje` del mes en la card.

El costo de esa ausencia no es estético. Un índice agregado que no se mueve
puede significar dos cosas opuestas —que nada se movió, o que dos fuerzas
grandes se movieron en direcciones contrarias— y sin la capa del medio no hay
forma de distinguirlas. En el ITCIS el segundo caso es el que está pasando:

| mes | Ingresos | Precios | Vulnerab. | Empleo | Confianza | Seguridad | ITCIS |
|---|---|---|---|---|---|---|---|
| 2023-12 | 89,4 | 97,3 | 99,7 | 98,4 | 94,7 | — | 95,3 |
| 2024-12 | 100,6 | 86,1 | 99,7 | 94,0 | 102,5 | 107,1 | 95,7 |
| 2025-06 | 114,2 | 87,8 | 44,2 | 93,3 | 105,7 | 111,7 | 94,7 |
| 2026-05 | 113,7 | 82,7 | **17,2** | 92,5 | 101,1 | — | 89,1 |

**El índice cae seis puntos y esconde dos movimientos enormes que se
compensan**: ingresos y consumo sube veinticuatro puntos mientras la
vulnerabilidad financiera se derrumba ochenta y dos. Y esconde también lo
contrario: precios lleva dos años entre 83 y 87, empleo un año y medio en 92.
Un lector que mire el ITCIS solo se lleva "deterioro leve y sostenido"; lo que
hay es un cinturón donde una dimensión colapsó y otra la tapó.

La cuenta ya está hecha. `parametrica.calcular_indice` y `itvc.calcular_itvc`
producen el puntaje de cada dimensión **en cada mes** de la reconstrucción, y
lo tiraban: `_serie_con_piso` se quedaba con `r["valor"]` y descartaba
`r["dimensiones"]`. Publicarlo no agrega ningún cálculo nuevo.

## Factores de decisión

- **No puede haber dos verdades sobre el mismo número.** La dimensión ya se
  publica como el `puntaje` del mes. Si su historia se calculara por otro
  camino, tarde o temprano diría algo distinto del mismo mes y nada avisaría:
  son dos campos del mismo JSON y ninguno de los dos "falla".
- **Los huecos se declaran, no se resuelven en silencio.** Hay fuentes anuales
  y componentes que arrancan tarde. Arrastrar, interpolar o dejar el hueco son
  tres decisiones distintas y las tres producen un JSON igualmente válido.
- **Legible con seis series.** El ITCIS tiene seis dimensiones y el ITCP siete.
  Un gráfico que no se lee no publica nada.
- **Esto expone lo que ya se calcula.** No es la oportunidad de corregir el
  índice: cualquier cambio de indicador, peso o banda necesita su propio ADR.

## Opciones consideradas

**Dónde se calcula**

1. **Reusar el resultado mensual del motor** que ya produce la serie del
   índice.
2. Una función nueva que agregue los componentes por dimensión.
3. Derivarla en el front desde los componentes publicados.

**Cómo se muestra**

1. **Small multiples**: un panel por dimensión, eje vertical compartido.
2. Un gráfico con las seis series superpuestas.
3. Sólo las dos o tres que explican el movimiento.

**Dónde va en BigQuery**

1. **Tabla propia** `series_dimensiones` con columnas `indice · dimension ·
   periodo · valor`.
2. Filas de `series_indices` con nombre compuesto (`itvc_dim_empleo`).

## Decisión

**Se publica la serie mensual por dimensión de los cuatro índices**, calculada
reusando el resultado del motor (opción 1), dibujada como small multiples con
eje compartido (opción 1) y archivada en tabla propia (opción 1).

**Los cuatro entran.** La pregunta abierta era si los tres índices por bandas
podían: sí, y sin trabajo extra. `validacion_externa` ya reconstruye sus
componentes mes a mes (`_valores_itcm_por_mes`, `_valores_itcg_por_mes`,
`_valores_itcp_por_mes`) y sus motores emiten `dimensiones[k]["puntaje"]` con
la misma forma que el del ITCIS. La única diferencia real es la escala —puntaje
0-100 de banda contra base 100 = 4T-2023— y se declara en cada sección.

**La agregación es la del índice, literalmente.** `_anotar_dimensiones` recibe
el `r` que el motor ya calculó para ese mes y le saca `dimensiones[k]["puntaje"]`.
No hay una segunda implementación del promedio ponderado ni de la
renormalización por peso presente, así que no hay dos reglas que puedan
divergir. Y como el techo de winsorización se aplica al **componente** antes de
que el motor vea el mes (ADR-0033), la dimensión agrega componentes ya
recortados por construcción.

**Los meses son exactamente los del índice.** Un mes recortado por el piso de
cobertura o por ser el mes en curso (ADR-0197) tampoco deja punto de dimensión:
publicar la parte de un número que se decidió no publicar es peor que no
publicar ninguno de los dos.

**Los huecos se muestran como huecos.** Ni arrastre ni interpolación en esta
capa. Concretamente:

- **Seguridad no tiene punto en dic-2023** y la serie arranca en ene-2024: la
  encuesta que la mide estuvo suspendida y no hay dato que mostrar. Lo mismo con
  alianzas territoriales del ITCP, que arranca en feb-2024. El panel lo dice en
  texto ("32 de 33 meses, arranca en ene-2024") en vez de dibujar una línea que
  empieza donde empiezan las otras.
- **Dentro de la serie no hay ni un hueco interior** en ninguna de las
  veintitrés dimensiones publicadas, así que la regla no está eligiendo entre
  alternativas hoy: está fijada antes de que el caso aparezca.
- El único arrastre del proyecto —el del ITCIS a nivel **componente**, "último
  dato disponible" del doc IV.2.1— sigue donde estaba y ocurre antes de que el
  motor vea el mes. No se agrega un segundo arrastre encima.

**La dimensión de un solo componente se publica igual.** En vulnerabilidad
financiera, `mora_familias` es el 100% del peso: la fila no agrega ninguna
información sobre el componente. Se publica porque lo pone **en la misma escala
que las otras cinco**, que es lo único que permite decir que se derrumbó ochenta
y dos puntos mientras precios recorría catorce. La ficha lo dice.

### Consecuencias

- Cualquiera puede ver de dónde viene el movimiento del índice sin abrir
  dieciocho cards.
- El snapshot crece unos 30 KB (≈700 puntos en cuatro índices).
- La sección hereda la procedencia de la reconstrucción y hay que decirla: sin
  ajustes del analista, y terminando en el último mes con cobertura suficiente,
  que en los tres índices por bandas es **anterior** al mes de la card.
- BigQuery gana una tabla que se une con `dimensiones` por `(indice, dimension)`
  sin parsear strings.

### Confirmación

`tests/test_series_dimensiones.py`. La guarda que sostiene todo lo demás es la
**reagregación**: los puntajes de dimensión de un mes, ponderados por su peso
nominal renormalizado sobre las presentes, tienen que reproducir **exacto** el
punto del índice de ese mes. El motor agrega sobre los puntajes ya redondeados a
un decimal, así que la igualdad es exacta y no admite tolerancia — si la serie
por dimensión se calculara con otros pesos, con otro criterio de faltantes o
sobre otro conjunto de componentes, el número deja de dar.

Las otras cinco: que la cola de la serie coincida con el `puntaje` de la card
cuando hablan del mismo mes; que el snapshot publique la serie que calculó la
validación (el eslabón que este proyecto ya rompió antes: un valor calculado en
`output/` que `publicar.py` nunca sube a la página); que no haya relleno,
verificado reconstruyendo en vivo y comparando los meses; que ninguna dimensión
sin componentes exentos supere el techo de winsorización; y que BigQuery reciba
las filas.

Las siete se probaron **rompiéndolas a propósito** —cambiando el puntaje de una
card, el peso de una dimensión, rellenando un mes ausente, pasando el techo,
borrando la serie del snapshot y borrando una dimensión del export— y las siete
fallaron por el motivo correcto.

## Pros y contras de las opciones

### Dónde se calcula

- **Reusar el resultado del motor** — no hay segunda regla de agregación que
  mantener; la serie no puede diferir del índice en cómo suma. Contra: obliga a
  pasar un acumulador por los cuatro constructores.
- Función nueva — más independiente. Contra: es exactamente el patrón que este
  proyecto viene pagando caro (ADR-0082: dos listas de componentes que se
  fueron separando; ADR-0224: el techo declarado en dos lugares). Dos caminos
  que agregan "igual" hasta que uno se actualiza.
- Derivarla en el front — cero código de pipeline. Contra: el navegador no tiene
  la reconstrucción histórica, sólo el mes; y pondría la metodología del índice
  en TypeScript.

### Cómo se muestra

- **Small multiples con eje compartido** — cada recorrido se lee solo y las
  alturas se comparan. Contra: con una dimensión que recorre ochenta y dos
  puntos, las que recorren catorce quedan planas. Se mitiga —no se disimula—
  imprimiendo el rango propio de cada panel: la planicie queda **medida** en vez
  de sugerida, que es lo correcto, porque esas dimensiones efectivamente llevan
  dos años quietas.
- Seis series superpuestas — un solo gráfico. Contra: se probó y no se lee. Los
  recorridos del ITCIS se cruzan repetidamente entre 17 y 140; hacen falta seis
  colores distinguibles, seis entradas de leyenda y un ojo que siga una línea
  entre las otras cinco. El patrón que el tablero ya tiene compara **dos**
  series, y por eso funciona.
- Sólo las dos o tres que explican el movimiento — legible sin discusión.
  Contra: elegirlas es una decisión editorial que cambia mes a mes, y esconder
  las quietas es esconder el hallazgo (que cuatro de seis estén planas es la
  mitad de la historia).

### Dónde va en BigQuery

- **Tabla propia** — la dimensión va en su columna y se une con `dimensiones`
  —el peso y el puntaje del mes de cada corrida— sin parsear nada. Es el mismo
  criterio con el que la matriz de redundancia se guarda en formato largo.
  Contra: una tabla más.
- Nombre compuesto en `series_indices` — cero esquema nuevo. Contra: esa tabla
  tiene una sola columna de identidad, así que la dimensión quedaría codificada
  dentro de un string que cada consulta tiene que volver a partir.

## Más información

### Lo que apareció al construirlo y NO se tocó

`informalidad` se rebasea distinto en los dos caminos, y por eso la dimensión
**empleo** del ITCIS cierra en 93,4 en la serie reconstruida y en 92,5 en la
card del mismo mes:

- El índice vivo (`itvc.indices_desde_series`) la trata como la serie
  **trimestral** que es y toma como base el 4T-2023 exacto, o sea el punto
  2023-10 (35,7 → índice 94,2).
- La reconstrucción (`validacion_externa.COMPONENTES`) la sigue declarando
  `anual=True`, así que su base es el **primer valor de 2023**, el punto 2023-01
  (36,7 → índice 96,8).

El comentario de `itvc.py` dice textualmente que la serie trimestral "reemplaza
la excepción anual"; la reconstrucción nunca se actualizó. Es un defecto real y
anterior a este ADR, y **no se corrige acá**: cambiar el flag mueve la serie
histórica publicada del ITCIS y las correlaciones que se publican con ella, y
eso necesita su propio ADR con su propia corrida. Queda declarado en
`DIVERGENCIAS_DECLARADAS` dentro de `tests/test_series_dimensiones.py`, con la
causa localizada, y el test falla si la divergencia **desaparece** —para que el
registro no quede tapando la próxima— tanto como si aparece una nueva.

### Por qué la guarda de la cola sólo corre sobre el ITCIS

Es la única reconstrucción que alcanza el mes de la card. Las tres por bandas
cortan en el último mes completo con cobertura suficiente, que hoy es junio o
julio contra una card de agosto; exigirles la coincidencia sería comparar dos
meses distintos y llamar bug a la diferencia entre ellos. La condición es
**dependiente del dato, no una excepción escrita**: el día que una de esas
reconstrucciones alcance el mes de la card, la guarda se enciende sola.

### Dimensiones sin serie

`inversion` del ITCM no se dibuja: sus dos componentes (IAI e ICIP) no tienen
serie mensual, así que la reconstrucción nunca produjo la dimensión y el motor
la renormaliza. Sigue puntuando en la card, y la nota de la sección la nombra en
vez de dejarla desaparecer sin explicación.
