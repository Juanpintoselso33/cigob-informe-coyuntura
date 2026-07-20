# ADR-0076 — La dimensión de actividad deja de colgar de un único dato

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · ITCM · dimensión Actividad económica · `ipi_manufacturero` (nuevo) · `emae_ia` |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0029 (promedio móvil contra el ruido del interanual de un mes suelto) · ADR-0021 (puntaje interpolado) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 3 |
| **Enmendado por** | ADR-0079 (18-jul-2026): peso 35% → 20% y corrección de tres afirmaciones de este documento |

## Contexto

La dimensión de actividad pesaba 11% del ITCM y tenía **un solo componente**,
el EMAE, con peso 1,0. La auditoría lo marcó como riesgo de fuente única
agravado por el rezago: el EMAE es el indicador simple más rezagado del índice
(~2 meses). La propia ficha del EMAE ya declaraba la limitación —"es la única
variable de su dimensión: el 11% del índice cuelga de un solo dato"— sin que
hubiera un segundo indicador que la resolviera.

### Candidatos descartados

- **Demanda de energía eléctrica**: descartada en la versión original de este
  ADR con la afirmación de que "las series de energía disponibles en la API
  pública terminan en 2015-2016. Sin fuente automatizable".

  > **ESA AFIRMACIÓN ERA FALSA** (corregido 2026-07-18). La serie existe, es
  > mensual y está vigente: `367.3_DEMANDA_TOTAL__13`, dataset "Demanda de
  > electricidad", **305 puntos desde ene-2001 hasta may-2026**. La búsqueda
  > original usó términos que no la devolvían; se dio el punto por cerrado sin
  > insistir.
  >
  > La corrección importa doblemente porque el indicador tenía dos ventajas que
  > el ADR nunca llegó a sopesar: lo publica la **Secretaría de Energía, no el
  > INDEC** —así que habría atendido el riesgo de organismo único que este mismo
  > ADR declara como limitación— y tiene **veinticinco años de historia**, contra
  > los treinta meses de casi todo lo demás del índice.

  **Se mantiene fuera del índice, pero por una razón distinta y medida.** Sobre
  los meses comunes:

  | | |
  |---|---|
  | correlación con el EMAE | +0,441 (n=60) |
  | correlación con el IPI | **+0,020** (n=30) |
  | salto mediano de un mes al siguiente | **11,2 pp** |

  El salto mensual de 11,2 pp es **casi el doble del ruido del IPI crudo** (6,2)
  que motivó suavizarlo, y su causa no se arregla promediando: la demanda
  eléctrica la mueve el **clima**. Una ola de calor sube el consumo residencial
  sin que la actividad económica cambie, y un promedio móvil suaviza la serie
  pero no separa el componente térmico del económico. Usarla exigiría
  desestacionalizar por temperatura, que es trabajo real y no un ajuste de
  ventana.

  La correlación de +0,02 con el IPI dice que **mide algo genuinamente distinto**,
  que es a la vez su mayor atractivo como diversificador y la señal de que no es
  intercambiable con lo que ya hay. **Queda como candidata abierta y evaluada**,
  no como callejón sin salida.
- **Patentamientos comerciales**: ya se acumulan en el proyecto como insumo del
  IAI, pero el caché tiene **un solo mes** (may-2026). Sin historia, no puede
  puntuar ni reconstruirse hacia atrás. Vuelve a ser candidato cuando el cron
  acumule suficientes meses.

## Decisión

Entra el **IPI manufacturero** (Índice de Producción Industrial, nivel general)
como variación interanual **promediada a tres meses**.

> El reparto original era 65/35. **ADR-0079 lo llevó a 80/20** el mismo día,
> tras auditoría externa: el EMAE ya contiene a la industria, así que el 35%
> dejaba a la dimensión con casi la mitad de su exposición en un solo sector.
> Las secciones que siguen conservan las cifras del reparto original cuando
> describen mediciones hechas con él.

### Por qué el promedio de tres meses

La variación interanual del IPI original **salta hasta 9 puntos porcentuales de
un mes al siguiente** (feriados móviles, días hábiles, paradas de planta): en
2026, feb −8,87%, mar +5,02%, abr −2,53%. Ese ruido no dice nada sobre el
estado de la industria. El promedio de tres meses **reduce el desvío de los
cambios mensuales de 6,2 a 2,5 puntos** —un factor 2,5— sin agregar rezago
apreciable: la serie sigue siendo interanual, sólo deja de vibrar. Es el mismo
criterio que ADR-0029 aplicó a la recaudación.

### Por qué las mismas bandas que el EMAE

> **Corregido tras auditoría externa (18-jul-2026).** La versión original de
> este ADR afirmaba que ensanchar las bandas del IPI "no lo respaldan los
> datos", porque el rango del IPI suavizado (26,0 pp) y el del EMAE (23,5 pp)
> eran comparables. **La comparación estaba doblemente viciada**: medía el EMAE
> sobre sesenta meses que arrancan en may-2021 e incluyen el rebote post-COVID,
> contra treinta del IPI; y comparaba el IPI ya suavizado contra el EMAE sin
> suavizar. Sobre la ventana comparable el rango del EMAE es **16,1 pp** contra
> 26,0 del IPI: la industria oscila **1,6 veces más**.

Se usan igual las bandas del EMAE, por una razón distinta de la que decía el
documento original. Lo que importa no es el rango del valor crudo sino **cuánto
movimiento aporta cada componente a la dimensión después de pasar por las
bandas**, que es donde el índice lo consume:

| | desvío del valor | desvío del puntaje | aporte al movimiento |
|---|---|---|---|
| EMAE | 4,15 pp | 32,3 | 60% |
| IPI | 7,85 pp | 39,5 | 40% |

*(con el reparto 65/35 vigente al momento de la medición)*

Y hay una segunda razón, más de fondo: **la brecha que producen estas bandas es
real y hay que dejarla ver**. Con ellas, un mes **mediano** del IPI puntúa 39,4 y
uno del EMAE 70,9 — 31 puntos — porque la industria argentina rindió peor que la
actividad agregada durante todo el período medido. Recalibrar para cerrar esa
brecha blanquearía desempeño real, que es exactamente lo que ADR-0045 prohíbe.
El arrastre estructural que produce se compensa con el **peso** del indicador
(ADR-0079), no retocando las anclas.

### Por qué el EMAE manda

El EMAE es la medida agregada oficial y cubre todos los sectores; el IPI mide
sólo manufactura, alrededor de un sexto del producto. El EMAE debe seguir
mandando por amplio margen. La versión original justificaba el 35% diciendo que
era "peso suficiente para que la segunda señal se note cuando diverge" —es
decir, eligiendo el peso por el efecto buscado sobre el resultado y no por la
importancia del componente, que es un criterio inválido y así lo señaló la
auditoría externa. El reparto vigente (80/20) está en ADR-0079, fundado en la
exposición sectorial resultante.

## Consecuencias

- **Baja el rezago de la dimensión, aunque menos de lo que decía la versión
  original de este ADR.** El IPI se publica hacia mediados del mes siguiente: al
  momento de este cambio llegaba a **may-2026** y el EMAE a **abr-2026**. Pero
  el indicador promedia tres meses, así que su centro de masa queda en t−1: el
  IPI de mayo informa, en el neto, sobre abril — el mismo mes del EMAE. La
  ganancia es real pero vale un tercio de lo declarado, no un mes entero.
- **Las dos señales divergen hoy, que es exactamente el punto.** EMAE +1,64%
  i.a. (puntaje 61,1) contra IPI −1,07% (puntaje 39,4): la actividad agregada
  crece mientras la industria se contrae. Con el EMAE solo, el índice no veía
  nada de eso.
- Dimensión de actividad **61,1 → 53,5**. **ITCM 62,7 → 61,8**, sin cambio de
  banda.
- Serie reconstruida de **30 puntos desde dic-2023**.

### Efecto sobre la validación externa

La correlación del ITCM con el riesgo país **baja de −0,775 a −0,764** con el
reparto original.

> **Corregido tras auditoría externa.** La versión original de este ADR
> descartaba ese deterioro como "dentro del ruido" y argumentaba que la
> validación externa "mide si el índice acompaña al mercado, no si describe bien
> la economía real". El problema es que **ese mismo estadístico se había usado
> como confirmación** cuando mejoró, en la misma tanda de trabajo. No se puede
> tener una métrica como prueba cuando sube y como irrelevante cuando baja.
>
> El barrido de pesos posterior (ADR-0079) mostró además que el deterioro es
> **monótono**: −0,775 sin IPI, −0,768 al 15%, −0,767 al 20%, −0,764 al 35%,
> −0,760 al 50%. No hay un peso donde el IPI mejore la validación externa. Eso
> es un argumento en contra, y así se pondera en ADR-0079 —junto a los demás, no
> como criterio único.

## Limitaciones declaradas

- El IPI mide sólo la industria manufacturera: acompaña al EMAE, no lo
  reemplaza.
- El suavizado a tres meses amortigua los quiebres de nivel: un cambio brusco
  tarda dos o tres meses en verse completo.
- Serie original, no desestacionalizada. La comparación interanual absorbe la
  estacionalidad pero no los efectos de calendario, que el suavizado atenúa sin
  eliminar.
- Los dos componentes de la dimensión son **medidas de actividad y correlacionan
  entre sí**: el segundo no las convierte en dos lecturas independientes (ver
  ADR-0075).
- **"Reduce el riesgo de fuente única" es parcialmente falso** y la versión
  original de este ADR lo afirmó sin matizar: el EMAE **ya contiene** a la
  industria manufacturera (~17% del agregado), así que el IPI no agrega un
  sector sino una segunda medición del mismo; y ambos los publica el INDEC, de
  modo que un cambio de metodología del organismo los movería juntos. Lo que sí
  reduce es el riesgo **operativo**: si falta o se revisa una serie, la
  dimensión conserva lectura.
  Conviene registrar que **existía una alternativa no-INDEC y no se la evaluó**
  por un descarte mal fundado: la demanda eléctrica (ver arriba). Que su
  descarte hoy tenga otro fundamento no borra que la decisión original se tomó
  sin haberla considerado de verdad.
