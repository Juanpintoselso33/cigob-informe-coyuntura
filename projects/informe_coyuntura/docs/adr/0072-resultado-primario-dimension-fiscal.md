# ADR-0072 — resultado_primario: la dimensión fiscal pasa a medir resultado, no ingresos

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · ITCM · dimensión Viabilidad fiscal-comercial · `resultado_primario` (nuevo) · `recaudacion` (reinterpretada) |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0029 (recaudación como promedio móvil del i.a. real) · ADR-0056 (ajuste automático del saldo por contracción) · ADR-0021 (puntaje interpolado) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 2 — señalada como "el problema central del sistema" |

## Contexto

La auditoría marcó la inconsistencia más seria del índice: **la dimensión se
llamaba "viabilidad fiscal" pero su componente principal medía INGRESOS, no
resultado**. Y no era un componente cualquiera: la recaudación pesaba 60% de la
dimensión y **14,4% del ITCM, el mayor peso efectivo de todo el índice**.

El problema no es teórico. Un gobierno cuya promesa central es el equilibrio
fiscal puede sostener superávit con la recaudación cayendo —bajando el gasto—, y
el índice leería tensión creciente donde el programa registra cumplimiento. Peor:
una baja deliberada de impuestos reduce mecánicamente la recaudación real, y el
indicador convertiría una decisión de política en deterioro del puntaje.

Al momento de la auditoría el dato era **−3,16% i.a. real, puntaje 32,1: el peor
de los quince indicadores del cinturón**, arrastrando el índice sin que se
pudiera saber, desde el índice, si eso reflejaba fragilidad fiscal o alivio
tributario.

## Decisión

Entra **`resultado_primario`**: el resultado primario del Sector Público
Nacional acumulado en doce meses, medido como **porcentaje de la recaudación**
del mismo período.

### Por qué acumulado 12 meses

El resultado primario mensual es brutalmente estacional: diciembre da déficit
todos los años (aguinaldo y cierre de ejercicio) y enero superávit alto. Con
datos reales: dic-2024 −1.301.046 M$ y dic-2025 −2.876.450 M$, contra ene-2025
+2.434.865 M$ y ene-2026 +3.125.737 M$. Puntuar el mes suelto marcaría un
colapso fiscal cada diciembre.

### Por qué normalizado por recaudación y no por PIB ni por IPC

La auditoría sugería "% del PIB o meses de superávit". Se verificó que **no hay
PIB nominal mensual publicado** en las fuentes automatizables: las series de PIB
a precios corrientes de datos.gob.ar terminan en 2013. Tampoco existe un
agregado mensual de "ingresos totales" del SPN (solo subcomponentes).

Deflactar por IPC era la otra opción, y se descartó por una razón que la propia
auditoría plantea en su sección IV.2: **el IPC ya deflacta recaudación, crédito,
IDM y la tasa real del IdC**, y sumarle un quinto uso concentraría todavía más el
riesgo de una fuente única. El cociente contra la recaudación es adimensional,
no necesita deflactor y **se lee solo**: de cada peso que recauda el Estado,
cuánto le sobra después de gastar, antes de intereses.

### Escala

Monótona (más superávit = más sostenible), a diferencia de la U invertida de
ADR-0071:

| resultado / recaudación | puntaje |
|---|---|
| ≤ −5% | 10 |
| −5 – 0% | 30 |
| 0 – 4% | 60 |
| 4 – 8% | 85 |
| > 8% | 100 |

La serie reconstruida da **−12,0% en dic-2023** (puntaje 10), cruza el cero en
abr-2024 y se estabiliza en **+6/+8%** desde fines de 2024. Valor vigente:
**+6,4% (may-2026) → 87,9**.

### Reponderación

| componente | antes | ahora | peso efectivo |
|---|---|---|---|
| **resultado_primario** | — | **50%** | **12,0%** |
| recaudacion | 60% | 30% | 7,2% |
| saldo_comercial_12m | 40% | 20% | 4,8% |

Se adopta la composición que propone la auditoría (50/30/20). Se verificó que
45/30/25 y 40/30/30 mueven la dimensión **menos de 0,3 puntos** con los datos
vigentes, porque el resultado primario (87,9) y el saldo comercial (85) puntúan
casi igual: la elección entre esas variantes es hoy indiferente.

La recaudación **no sale del índice**: se reinterpreta como lo que realmente es,
un indicador de actividad y formalidad de la base imponible, y su ficha lo
declara. Su peso efectivo baja de 14,4% —el mayor del índice— a 7,2%.

## Consecuencias

- ITCM 58,5 → **62,7**. El cinturón **cambia de banda**: de "moderadamente
  apretado" a "moderadamente aflojado". Tensión 4,2 → **3,7**.
- La dimensión fiscal-comercial pasa de 53,3 a **70,6**. El salto no es
  coyuntura: es la corrección de un sesgo de medición. La dimensión leía
  fragilidad fiscal mirando ingresos, cuando el resultado —lo que la dimensión
  dice medir— venía sólido desde mediados de 2024.
- El peor puntaje del cinturón (recaudación, 32,1) sigue ahí, pero con la mitad
  del peso y con su rol declarado en la ficha.
- Serie de **30 puntos desde dic-2023**.

## Limitaciones declaradas

- El denominador es recaudación tributaria, no ingresos totales del SPN: sirve
  como escala estable, pero no es un cociente entre magnitudes del mismo
  universo contable.
- Es resultado **primario**: excluye intereses. Un superávit primario alto
  convive con déficit financiero si la carga de intereses es grande.
- La ventana de doce meses demora en reflejar un cambio de régimen fiscal.
- No mide la **calidad** del ajuste: el mismo resultado puede alcanzarse
  recortando obra pública o licuando jubilaciones, y el indicador no los
  distingue.
