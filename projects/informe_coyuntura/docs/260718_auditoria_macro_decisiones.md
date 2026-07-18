# Auditoría de consistencia · Cinturón Macro — registro de decisiones

**Documento de trabajo, vivo.** Se actualiza a medida que se revisa cada
observación de la auditoría del 17-jul-2026 (*"Auditoría de consistencia ·
Indicadores del Cinturón Macroeconomía"*, análisis de las 13 fichas vigentes).

Para cada observación: qué decidimos, por qué, y en qué estado quedó. Las
decisiones implementadas remiten a su ADR, que tiene el detalle técnico.

---

## Estado general

| | |
|---|---|
| Observaciones de la auditoría | 13 indicadores + 3 brechas transversales |
| **Implementadas** | 9 |
| **Pendientes de decisión** | 3 |
| **Rechazadas con fundamento** | 1 |
| Indicadores del ITCM | 13 → **16** |
| ITCM | 57,2 → **61,8** (cambió de banda) · tensión 4,3 → **3,8** |
| Validación externa (ITCM ↔ riesgo país) | r −0,726 → **−0,764** (mejoró) |

**Verificación previa:** se contrastó toda la aritmética de la auditoría contra
el snapshot vivo y **cierra exacta** (6 dimensiones 26/24/16/12/11/11 y los 13
pesos efectivos). Dos deslices menores del documento: dice que la recaudación
(32,1) es "el segundo peor del índice" cuando era **el peor**, y nuestro propio
`CLAUDE.md` decía "12 indicadores + 4 ocultos" cuando eran 13, todos en índice.

---

## Prioridad alta

### 1. Riesgo país en la dimensión de financiamiento — **RECHAZADO**, cubierto por otra vía

**La auditoría pedía:** incorporar el riesgo país (EMBI) como cuarto componente
de la dimensión, porque "se llama capacidad de financiamiento y no incluye el
precio del financiamiento soberano".

**Decisión: el riesgo país NO entra al índice y sigue siendo el validador
externo.** Tres razones:

1. **Rompe la validación.** El ITCM se valida contra el EMBI (r = −0,726) y el
   texto publicado dice que "no integra el índice". Adentro, la validación se
   vuelve circular.
2. **La fuente no es oficial.** Se toma de una API comunitaria, envuelta en un
   `try/except` que degrada a "no disponible". Sirve para validar, no para
   puntuar bajo los gates de frescura.
3. **Es político antes que macro.** Lo dice nuestra propia conclusión
   publicada: sus saltos mensuales "co-mueven con la reconstrucción del
   cinturón político, no con ésta".

**Pero el hueco que señalaba era real**, y se cubrió con un indicador distinto
→ ver decisión 2.

**Descartado en el camino:** el *spread* del Tesoro contra BADLAR/TAMAR. Se
implementó y se midió: oscila entre −43 y +36 pp sin tendencia, porque cada mes
el Tesoro coloca a plazos distintos y el promedio mezcla puntos de la curva
contra una tasa bancaria a 30 días. No es señal.

---

### 2. Costo del financiamiento soberano — **IMPLEMENTADO** (ADR-0071)

**Decisión:** entra `costo_financiamiento_tesoro`, la **tasa real ex-ante** que
paga el Tesoro por colocar deuda en pesos (TIREA de las colocaciones del mes,
ponderada por monto, deflactada por la inflación esperada del REM).

- **Fuente oficial** con historia: planillas de colocaciones de la Secretaría de
  Finanzas (desde 2020). Los nombres de archivo no son estables y se resuelven
  leyendo los enlaces de la página.
- **Sin circularidad**: es la curva en pesos, no el EMBI en dólares.
- **Universo**: solo instrumentos a tasa fija en pesos. CER, dólar linked y
  TAMAR quedan afuera porque su rendimiento no es comparable — ese problema de
  agregación era lo que había hecho fracasar el primer intento.
- **Escala de U invertida**, la única no monótona del ITCM: tasa real muy
  negativa = represión (se financia licuando al ahorrista); muy alta = bola de
  nieve.
- **Ponderación**: 25% de la dimensión; los otros tres se recortan en
  proporción (×0,75). **No** se aprovechó para rebalancear IdC contra crédito
  → eso queda pendiente (decisión 6).

**Validado contra prensa contemporánea**, que es la prueba que pidió el editor:

| momento | indicador | qué decía la prensa |
|---|---|---|
| dic-2023 | −12,2% real → puntaje 20 | *"animosidad licuatoria"* (El Cronista), *"Licuando los pesos"* (El Ágora) |
| ago-2025 | +33,5% real → puntaje 15 | *"tasas récord de 69,2%"* (BAE), *"duplica la inflación"* (Perfil), rollover 61% |

La banda negativa terminó llamándose igual que la palabra que usaba la prensa.

---

### 3. Resultado primario en la dimensión fiscal — **IMPLEMENTADO** (ADR-0072)

**La auditoría lo llamó "el problema central del sistema"**, y con razón: la
dimensión se llamaba "viabilidad fiscal" pero medía **ingresos**. La
recaudación pesaba 60% de la dimensión y **14,4% del ITCM** —el mayor peso
efectivo del índice— con el peor puntaje del cinturón (32,1) arrastrando el
titular, sin que se pudiera distinguir fragilidad fiscal de una baja deliberada
de impuestos.

**Decisión:** entra `resultado_primario` (superávit primario del SPN acumulado
12 meses, como % de la recaudación) y **pasa a liderar la dimensión con 50%**.
La recaudación baja a 30% y se **reinterpreta** como indicador de actividad y
formalidad de la base imponible; su ficha ahora lo declara. Saldo comercial 20%.

**Por qué normalizado contra recaudación y no contra PIB:** se verificó que no
hay PIB nominal mensual automatizable (las series de precios corrientes mueren
en 2013) ni agregado mensual de ingresos totales del SPN. Deflactar por IPC
habría sumado un **quinto** uso al mismo deflactor, que es justo el riesgo
sistémico que la auditoría marca en IV.2. El cociente es adimensional y se lee
solo: de cada peso recaudado, cuánto sobra antes de intereses.

**Efecto:** ITCM 58,5 → 62,7, **cambio de banda** ("moderadamente apretado" →
"moderadamente aflojado"). No es coyuntura: es la corrección de un sesgo de
medición. La dimensión leía fragilidad mirando ingresos cuando el resultado
venía sólido desde mediados de 2024.

**Composición 50/30/20**: es la que propone la auditoría. Verificado que
45/30/25 y 40/30/30 mueven la dimensión menos de 0,3 puntos con los datos
vigentes — hoy la elección entre variantes es indiferente.

---

### 4. Línea de base dic-2023 y brecha contra el punto de partida — **IMPLEMENTADO**

**La auditoría pedía:** publicar el ITCM de dic-2023 como referencia permanente
y una lectura mensual de "brecha contra el punto de partida", porque el índice
mide **nivel** contra anclas fijas y no responde la otra mitad de la pregunta
("¿estamos mejor que en la transición?").

**Hallazgo:** estaba medio hecho. La sección *Evolución* de la home ya publicaba
las trayectorias mensuales reconstruidas de los cuatro índices desde dic-2023,
con el caveat declarado. Faltaba el **número**.

**Decisión:** cada card de evolución cierra ahora con la brecha acumulada contra
su punto de partida, derivada de la propia serie.

| cinturón | brecha desde el inicio |
|---|---|
| Gestión | **−5,4** de tensión (aflojó) |
| Macro | **−2,6** (aflojó) |
| Vida cotidiana | −0,4 (aflojó) |
| Política | **+0,6** (se apretó) |

**Salvedad importante que la auditoría no menciona:** la brecha se calcula
**reconstruido contra reconstruido**. La reconstrucción excluye IAI/ICIP y los
ajustes del analista, así que su nivel difiere del publicado (hoy 52,3 contra
62,7). Restar el publicado de hoy menos el reconstruido de dic-2023 daría un
número inflado y **sería incorrecto**. Cada card usa además su propia fecha de
inicio (política arranca en ene-2024).

---

## Resueltas en la segunda tanda (18-jul-2026)

### 5. TCRM — regla anti-salto · **ADR-0073**

La banda `>110 → 100` premiaba igual una depreciación gradual y un salto
cambiario con el traspaso a precios pendiente. Caso real: dic-2023 saltó +50,1%
m/m y puntuó 100/100 durante tres meses; cuatro meses después la ganancia se
había evaporado entera.

Se implementó un descuento interpolado hacia un piso de 55, con la forma de la
regla del saldo comercial (ADR-0056). **Revisado el mismo día contra
literatura**: la primera versión usaba una ventana de 3 meses elegida sin
respaldo, y se extendió a **8 meses** sobre evidencia de pass-through argentino
(Frank 2017-2023: dura 6-8 meses; Bertholet 2026: se estabiliza al octavo). El
umbral de 8% se contrastó contra el criterio estándar de alerta temprana de
crisis cambiarias (KLR media+3σ, Edison media+2,5σ) y **todos detectan el mismo
único mes**, así que se conservó. Dispara en 7 de 31 meses y **se apaga sola**
cuando el nivel cae por debajo del piso. No mueve el ITCM de hoy.

### 6. Rebalanceo IdC ↔ crédito · **ADR-0074**

El IdC declara en su propia ficha, con más de cien meses de validación, que **no
anticipa el crédito futuro**; sin embargo pesaba 2,7× el crédito realizado. Se
repartió el 41% conjunto casi en partes iguales (21/20). Hoy mueve +0,014
puntos —ambos puntúan casi igual— pero en dic-2024 la brecha era de 45 puntos y
el reparto viejo **subrepresentaba sistemáticamente** el boom de crédito de
2024-25.

### 7. Segunda señal de actividad · **ADR-0076**

Entra el **IPI manufacturero** con 35% de la dimensión (EMAE 65%), variación
i.a. suavizada a 3 meses. Bonus no buscado: el IPI publica **un mes antes** que
el EMAE, así que además baja el rezago que la auditoría marcaba. Las dos señales
hoy divergen (EMAE +1,64% contra IPI −1,07%), que es exactamente el argumento de
la auditoría. Descartados con evidencia: demanda eléctrica (series muertas en
2015-2016) y patentamientos comerciales (el caché tiene **un** mes).

Costo declarado: la correlación externa con el riesgo país baja de −0,775 a
−0,764. Es lo esperable al sumar una señal sectorial que el mercado no pricea
como los agregados, y está dentro del ruido de n=31.

### 10. Núcleo del IPC · **ADR-0077**

La recomendación literal era "serie de contexto", pero eso chocaba con la regla
ya establecida de que **ningún cinturón publica cards de contexto**. Se resolvió
con el patrón del TCRM: el núcleo entra como **serie acompañante en el modal**
del IPC, dos curvas en el mismo gráfico. No puntúa, no crea card y no hace
excepción a la regla.

### IV.3 — Matriz de redundancia interna · **ADR-0075**

**Se verificó primero que no estuviera cubierto**: la matriz de validación
cruzada existente cruza los cuatro índices contra anclas externas, no los
componentes entre sí. Son preguntas distintas.

13 componentes, 78 pares, **|r| medio 0,502**, 26% por encima de 0,7 (17 de
ellos entre dimensiones distintas) y 27% prácticamente independientes. Se
publica **con la salvedad muestral por delante**: 31 meses de un único programa
de estabilización, donde desinflación, recuperación y consolidación fiscal
avanzaron juntas. No se reponderó nada por el hallazgo — sobreajustaría a un
período que no se repite. Lo que sí se afirma sin reservas es la advertencia al
lector: que varias dimensiones coincidan **no son varias confirmaciones
independientes**.

---

## Pendientes de decisión

| # | Observación | Prioridad | Nota |
|---|---|---|---|
| 8 | **Cuenta corriente** como contexto del saldo comercial | media | Trimestral: no puede puntuar, solo acompañar el gráfico. Búsqueda previa en la API de datos.gob.ar sin resultados; falta cerrar con evidencia. |
| 9 | **Calendarizar recalibraciones** de bandas de historia corta (IDM, dolarización, crédito) | baja | Ojo con el criterio: recalibrar contra el rango observado solo si el techo es inalcanzable; si el rango es desempeño real, blanquea la señal. |
| 11 | **Sensibilidad del 70/30** de presión de dolarización | baja | **Ya calculado**: sobre 14 meses con ambos canales, mover a 50/50 u 85/15 cambia el puntaje hasta 20,4 puntos en el peor mes (oct-2025), que con peso efectivo 0,026 son **0,53 puntos de ITCM**. Falta decidir si se documenta o se recalibra. |
| 12 | **Ambigüedad direccional del ICIP** declarada en ficha | baja | Los pagos al exterior por software se leen como capitalización o como dependencia tecnológica. |
| 13 | **Reservas en meses de importaciones** como ancla alternativa | baja | La auditoría misma lo marca como no urgente. |

### Brechas transversales

| # | Observación | Estado |
|---|---|---|
| IV.2 | **Propagación del IPC** como deflactor (toca 5 de los indicadores) | **Pendiente**: documentar como riesgo sistémico en la metodología general. Nota: ADR-0072 lo tuvo en cuenta y evitó sumar un sexto uso. |
| IV.3 | **Correlación procíclica** entre dimensiones; publicar matriz | **RESUELTO** — ADR-0075 (ver arriba). |

---

## Hallazgos propios (no estaban en la auditoría)

1. **Bug en la reconstrucción histórica del ITCM.** Usaba una lista
   **hardcodeada** de componentes: los indicadores nuevos no entraban y la
   validación externa se venía quedando atrás del índice en silencio. Corregido.
   **Al corregirlo, la correlación con el riesgo país mejoró de −0,724 a
   −0,771** — evidencia independiente de que las dos recomendaciones altas
   apuntaban bien: el costo del financiamiento y el resultado fiscal son lo que
   el mercado mira para ponerle precio al riesgo argentino.

2. **Texto público desactualizado.** El subtítulo de la validación decía "once
   de sus trece componentes" con catorce indicadores en el índice, y **había un
   test que fijaba ese texto a mano**, o sea que vigilaba el número equivocado.
   Ahora el recuento se **deriva** de la composición vigente, y el test también.

3. **Dos fallas G3 preexistentes en vida cotidiana** (`ipc_alimentos` card 2,46
   vs serie 1,3; `endeudamiento_familiar` 46,03 vs 43,4). Valores idénticos en
   HEAD, sin relación con este trabajo. Probablemente el artefacto conocido de
   correr colectores en forma despareja. **Conviene mirarlo aparte.**

---

## Convenciones que salieron de esta revisión

- **Verificar la aritmética de la auditoría antes de actuar** sobre sus
  recomendaciones: acá cerró, pero una premisa mal habría invalidado la
  recomendación.
- **Verificar los indicadores nuevos contra prensa contemporánea** en los
  extremos de su serie. Es lo que confirmó que las bandas caían donde la prensa
  ponía los adjetivos.
- **Los recuentos y textos que dependen de la composición del índice se
  derivan, no se escriben a mano.**
- **Una decisión por cambio**: ADR-0071 no aprovechó para rebalancear IdC, y
  ADR-0072 no aprovechó para tocar el saldo comercial más de lo necesario.
