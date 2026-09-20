---
madr: 4
id: '0331'
estado: 'rechazado'
nota_estado: 'Rechazado, por ahora, construir un indicador de inversión tecnológica: el único candidato mensual no mide formación de capital y su aporte incremental reciente sobre el BK del IAI es chico. La dimensión `inversion` sigue con `iai` solo y `icip` sigue fuera del índice (ADR-0262).'
fecha: 2026-09-19
cinturon: 'macro'
indice: 'ITCM'
indicadores: [icip, iai]
relacionado: ['0253', '0262']
ambito: 'Cinturón macro · ITCM · dimensión `inversion` · si existe una serie que mida inversión tecnológica sin duplicar el componente BK del IAI'
origen: 'Apuntes de Juan del 15-sep-2026 (#monitor-de-proyecto-de-gobierno): «Revisar Indicador de inversión tecnológica diferenciada de la IAI». Es la opción B que ADR-0253 aplazó explícitamente.'
---

# ADR-0331 — La inversión tecnológica no tiene serie que la sostenga

## Contexto y planteo del problema

ADR-0253 renombró `icip` a «Pagos de servicios digitales y productividad»
porque el nombre anterior —«Índice de Capitalización Inteligente y
Productividad»— prometía formación de capital sobre un insumo que es consumo
intermedio. Eligió la opción mínima y **aplazó la opción B**: medir inversión
digital de verdad, lo que exigía «elegir una fuente de cuentas nacionales,
resolver su frecuencia y su rezago, y recalibrar la banda entera». ADR-0262
después sacó `icip` del índice por un defecto más profundo: sus dos insumos
necesitan signos opuestos y el compuesto los suma con el mismo.

Resultado al 19-sep-2026: **no existe ningún indicador de inversión
tecnológica**. La dimensión `inversion` (12% del ITCM) la sostiene `iai` solo,
con peso 1,0 — ISAC 65% + bienes de capital importados 35%.

La primera mitad del pedido ya estaba resuelta: `iai` e `icip` no comparten
**ninguna** serie, y el rótulo de `iai` perdió la sigla en ADR-0311. Lo que
queda por decidir es si se puede construir un indicador nuevo, y la restricción
«diferenciada de la IAI» aplica ahí: el componente BK del IAI es
`74.3_IIBCA_0_M_32`, el agregado de bienes de capital importados.

## Factores de decisión

- La serie tiene que ser **mensual y fresca**: una card del tablero no se
  alimenta con un dato trimestral de tres trimestres atrás.
- Tiene que **medir lo que su nombre dice**. El repo ya pagó dos veces esa
  cuenta (ADR-0218 con `mortalidad_pymes`, ADR-0217 con la proteína animal), y
  es el factor que termina decidiendo este caso.
- Tiene que **aportar algo que la dimensión no tenga ya** por el BK del IAI.
- Tiene que **discriminar** en una banda calibrada, no sólo moverse.

## Opciones consideradas

1. **Cuentas nacionales (la opción B de ADR-0253)** — la FBCF con apertura por
   software, bases de datos y equipos TIC.
2. **`184.1_BIENES_PAGICA_0_M_24` — «Bienes Pagos Informática»** (BCRA, balance
   cambiario): pagos al exterior por *bienes* del sector informática. Único
   candidato mensual y vivo que apareció en el barrido.
3. **No construir el indicador** y registrar por qué — elegida.

## Decisión

**No se construye, por ahora.** La dimensión `inversion` sigue con `iai` solo e
`icip` sigue en `INDICADORES_CONTEXTO`. No se toca código: este ADR registra una
medición, no un cambio.

El motivo principal es de **validez conceptual**, no estadístico. El motivo
secundario —la redundancia con el BK— es real en los datos recientes pero más
débil de lo que una primera lectura sugería, y se reporta abajo con los números
que lo favorecen y los que no.

### Evidencia 1 — la fuente que pedía ADR-0253 no existe

Barrido manual del catálogo de `apis.datos.gob.ar` el 19-sep-2026, con las
consultas «informatica», «TIC», «computacion», «intangible»,
«formacion+bruta+capital», «equipo+durable», «maquinaria+y+equipo» y
«equipo+de+informatica» contra `/series/api/search/`:

- **No apareció ninguna apertura de FBCF** por software, bases de datos o
  equipos TIC.
- Las líneas específicas de informática que existen están **discontinuadas**:
  `125.1_MOI_1993_0_28` («Máquinas de oficina e informática») termina en 2014;
  `326/327.x` («Fabricación de maquinaria de oficina, contabilidad e
  informática») en 2016 — y ésa mide producción, no inversión.
- La FBCF agregada (`166.2_F_BRUTAIJO_0_0_19`) es trimestral, en pesos
  corrientes, y su último punto es **4T-2025**.

**Es una observación de catálogo con fecha, no una prueba de inexistencia.** Un
barrido por palabra clave puede no dar con una serie mal titulada, y el catálogo
cambia. Lo que sostiene es que, al 19-sep-2026 y con esas consultas, la fuente
que la opción B necesitaba no está disponible.

### Evidencia 2 — el candidato no mide formación de capital (el motivo que decide)

`184.1_BIENES_PAGICA_0_M_24` es una serie **buena como serie**: 283 valores
mensuales de 2003-01 a 2026-07 y **sin huecos** —283 claves sobre un span
calendario de exactamente 283 meses—, con dos meses de rezago, mejor que varios
indicadores que sí puntúan.

El problema es qué es. Su título dice **pagos cambiarios por bienes del sector
informática**: no es formación bruta de capital fijo, y **no se verificó** que
sean equipos TIC, ni que sean bienes capitalizables, ni que correspondan a la
clasificación de bienes de capital. Puede incluir insumos, reventa o
inventarios. Además un pago cambiario y el valor importado se registran en
momentos distintos y por sistemas distintos.

Por el mismo motivo **queda sin verificar la afirmación simétrica**: que el
hardware informático importado esté «adentro» del agregado BK del IAI. Es
plausible por la clasificación por uso económico, pero este ADR no lo comprobó
contra la apertura por subpartida, que no está publicada.

Eso alcanza para no construirlo: un indicador rotulado «inversión tecnológica»
sobre una serie de pagos cambiarios sin destino económico verificado es
exactamente el error que ADR-0217 y ADR-0218 dejaron prohibido.

### Evidencia 3 — la redundancia con el BK: real y reciente, no universal

Crudo, el i.a. mensual es inbandeable: desvío **558,5** contra 40,0 del BK, con
recorrido de −96,5% a +3.052,4%. Suavizado con acumulado móvil de 12 meses el
desvío baja a **69,7** (BK: 26,5) y la serie se vuelve legible.

Correlación con el BK, **todas las ventanas medidas**, no sólo las favorables:

| Ventana | r (acum. 12m) | r (primeras dif.) |
|---|---|---|
| 2024-01 → 2026-07 | **+0,984** | +0,785 |
| 2016-2019 | **+0,974** | — |
| 2005-2011 | +0,822 | — |
| 2005-2019 | +0,777 | +0,325 |
| 2020-2023 | +0,210 | — |
| 2012-2015 | −0,118 | — |
| Histórico completo | **+0,654** | +0,429 |

**El +0,984 es el valor excepcional, no el típico.** En el histórico completo el
r suavizado es +0,654 (R² ≈ 0,428) y en 2005-2019 el R² es **0,604** — o sea
~40% de varianza propia, muy lejos del 3% que sugiere la ventana reciente. La
lectura honesta es: *en los datos recientes* el aporte incremental es chico; a lo
largo de la serie, no tanto.

Sobre la ventana reciente: R² = 0,968 (n=31; `candidato = −5,6 + 2,59·BK`), con
residuo de desvío 12,4. Eso es **3,2% de la varianza**, pero **17,8% del desvío**
(12,4/69,7) — y la segunda cifra es la que importa para un indicador que se
publica en puntos. Decir «3% de contenido» sobreinterpreta una proporción de
varianza residual, ajustada dentro de la misma muestra, sin validación fuera de
muestra ni test de estabilidad.

Tres límites más, que valen registrar:

- **Los 31 meses no son 31 evidencias independientes.** Cada punto es el i.a. de
  una suma móvil de 12 meses: los vecinos comparten casi todos sus datos y cada
  tasa involucra hasta 24 meses. Las primeras diferencias tampoco eliminan ese
  solapamiento.
- **Los cortes de ventana los elegimos nosotros.** Están puestos donde cambia el
  régimen cambiario, pero no se probaron fechas alternativas, y la ventana
  2024-2026 **no es de cambio libre**: contiene el desarme de los controles.
  Llamarla «cambio libre» sería falso.
- **Que se despegue del BK bajo cepo (−0,118 y +0,210) y converja después
  admite más de una lectura.** La que este ADR no puede demostrar es la causal
  («su parte propia mide acceso a divisas»); otra igualmente compatible es que
  dos flujos importadores respondan al mismo ciclo macro midiendo universos
  distintos. Se deja como hipótesis, no como hallazgo.

### Evidencia 4 — tamaño y granularidad

En los **últimos doce meses medidos** (ago-2025 a jul-2026) el candidato pesa
entre **1,00% y 2,71%** de los BK importados; en julio 2026, 14,5 MUSD contra
1.167,2. No se midió esa proporción para el resto del histórico.

A ese tamaño el i.a. crudo es frágil por base chica: el +3.052,4% de enero 2025
sale de comparar 15,4 MUSD contra **0,5 MUSD** en enero 2024, y el +979,0% de
diciembre 2024, de 10,6 contra 1,0. El salto de nivel entre 2023-24 y 2025-26 es
de un orden de magnitud, lo que deja la historia previa a 2025 poco útil para
calibrar una banda.

Sobre discriminación: con bordes de prueba `[−20, 0, 20, 50]` el suavizado ocupa
los cinco tramos, pero **80,6% de los meses cae en los dos extremos** (38,7% y
41,9%). Los bordes son nuestros, no la banda real del tablero, y se fijaron
después de ver los datos: el test muestra que la serie se mueve, no que gradúe
bien.

### Consecuencias

- La dimensión `inversion` sigue descansando en un solo indicador. Eso ya estaba
  decidido (ADR-0262); este ADR lo confirma como el estado alcanzable hoy.
- **Queda registrado que el pedido no está pendiente por olvido.** Sin esto, la
  próxima revisión del tablero vuelve a proponer lo mismo — mismo patrón que
  ADR-0313.
- **La decisión es provisional y dice qué la daría vuelta**: que INDEC publique
  FBCF con apertura TIC, que el BCRA o Aduana abran los BK importados por
  subpartida, o que se verifique el destino económico de los pagos del sector
  informática. Lo que falta es la serie y su validación, no el diseño.
- Si alguna vez se retoma el candidato del BCRA, va con nombre de **pagos de
  equipamiento**, nunca de inversión, y con la redundancia re-medida sobre la
  ventana vigente.

### Confirmación

No hay código nuevo que probar; lo que hay que poder reproducir son las
mediciones. Las dos series salen de `apis.datos.gob.ar` con el mismo
`HTTP_HEADERS` que usa `scripts/macro.py` (sin User-Agent la API responde 403):
`184.1_BIENES_PAGICA_0_M_24` y `74.3_IIBCA_0_M_32`. De ahí, i.a. mensual e i.a.
sobre acumulado móvil de 12 meses, Pearson por ventana, y regresión bivariada
para el R² y el residuo.

Las guardas que cubren el perímetro y tienen que seguir en verde:

- `tests/test_idm_e_icip_no_puntuan.py` — `icip` no vuelve al índice.
- `tests/test_constructos_no_prometen_de_mas.py` — no se puede afirmar
  «capitalización» ni «inversión digital» en la capa pública.

## Más información

- ADR-0253 — por qué pagar la nube no es capitalizar, y la opción B que aplazó.
- ADR-0262 — por qué ninguna dimensión arregla un compuesto de signos opuestos.
- La otra mitad del pedido del 15-sep ya está: el rótulo de `iai` perdió la
  sigla «(IAI)» en ADR-0311, y su texto público dice «inversión
  física/tradicional», sin prometer nada tecnológico.

### Qué corrigió la revisión adversarial de este ADR

La primera versión afirmaba que el candidato «es el componente BK del IAI», que
conservaba «3,2% de contenido propio» y que su parte independiente «mide acceso
a divisas» — y citaba sólo las dos ventanas con r ≈ +0,98, omitiendo el r=+0,654
del histórico y el R²=0,604 de 2005-2019 que las mismas corridas habían
impreso. Una revisión con Codex (modelo distinto, contexto fresco) marcó la
selección de ventanas, la confusión entre proporción de varianza y proporción de
desvío, el n efectivo del suavizado y la contradicción de etiquetar 2024-2026
como «cambio libre». Todo eso está corregido arriba. El veredicto no cambió,
pero pasó a apoyarse en la validez conceptual —que es lo que de verdad lo
decide— en vez de en una correlación de ventana.
