---
madr: 4
id: '0329'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'macro'
indicadores: [actividad_tributaria]
archivos: ['scripts/macro.py', 'scripts/itcm.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'web/src/lib/charts.ts', 'tests/test_itcm_difusion.py']
relacionado: ['0045', '0071', '0072', '0074', '0076', '0078', '0079', '0120', '0124', '0127', '0152', '0192', '0239', '0252', '0257', '0318', '0319', '0321']
ambito: 'Cinturón Macro · dimensión `actividad` del ITCM · nuevo indicador `actividad_tributaria`'
origen: 'Encargo del editor: el pedido original de ADR-0318/0319/0321 era un proxy de ACTIVIDAD y se había implementado como control dentro de la dimensión FISCAL'
---

# ADR-0329 — IVA-DGI + cheque puntúan como actividad, no sólo como control fiscal

## Contexto y planteo del problema

El apunte original del editor decía, textual: «Reca de IVA-DGI e Impuesto al
cheque como **proxy de actividad económica**». Lo que se construyó
(ADR-0318, ADR-0319, corregido de encuadre por ADR-0321) fue un **control
tributario dentro de la card de `recaudacion`**: una descomposición del
agregado DGI en la porción ligada a actividad (IVA + cheque) y el resto, que
sólo aparece en el `detalle_txt` y no puntúa. Eso es útil —ADR-0321 corrigió
para que dejara de llamarse "control independiente" cuando es aritmética de
composición— pero no es lo que se pidió: `recaudacion` puntúa en la dimensión
**fiscal** (`viabilidad_fiscal_comercial`), y un proxy de actividad tiene que
puntuar en la dimensión de **actividad**.

Este ADR no toca esa descomposición (sigue en `_control_tributario`,
`scripts/macro.py`, sin cambios): agrega un indicador **aparte**,
`actividad_tributaria`, que puntúa en `DIMENSIONES_ITCM["actividad"]` a partir
de las mismas dos series.

## Factores de decisión

1. **Composición: promedio ponderado, no matriz.** Se evaluó cruzar IVA-DGI y
   cheque en una matriz A×B, como hace `desequilibrio_monetario.py`
   (ADR-0192/ADR-0252). Se descarta: esa matriz existe porque sus dos
   componentes miden fenómenos **distintos** (stock de confianza en el peso
   vs. flujo de compra de divisas) que se refuerzan o se contrarrestan de
   forma declarada por la ficha que los definió, con números propios para las
   cuatro esquinas. Acá no hay una ficha que declare esa interacción: IVA-DGI
   y cheque son dos **mediciones ruidosas del mismo constructo** —cuánto se
   mueve la actividad—, cada una con su sesgo propio (el IVA por evasión y
   cambios de alícuota, el cheque por bancarización). Es la misma situación
   que ya conviven `emae_ia` e `ipi_manufacturero` en esta dimensión sin
   matriz: dos lecturas del mismo fenómeno se promedian; dos fenómenos
   distintos que interactúan se cruzan. Forzar una matriz sin una interacción
   declarada habría sido inventar anclas para parecer más sofisticado.
2. **Peso del promedio: 0,6 IVA-DGI / 0,4 cheque.** El IVA doméstico es un
   impuesto al consumo interno, más cerca del constructo "actividad"; el
   cheque grava **toda** transacción bancaria, así que además de actividad
   capta bancarización (más o menos pagos por transferencia en vez de
   efectivo) — un fenómeno que no se puede restar de la serie. Se le da menos
   peso por eso, no porque el dato sea peor.
3. **Bandas ancladas a la serie propia, no a números que queden bien
   (ADR-0045).** Ver medición abajo.
4. **Rezago de publicación.** Ver medición abajo.
5. **Doble uso con `recaudacion`.** Ver cuantificación abajo.

## Opciones consideradas

1. Dejar el control tributario como está (sólo texto, no puntúa) — no
   satisface el pedido original.
2. Reemplazar `recaudacion` por esta descomposición — se descarta:
   `recaudacion` sigue siendo la medida correcta de base imponible/viabilidad
   fiscal (ADR-0072), y perder esa card para ganar una de actividad no tiene
   sentido cuando se puede tener las dos.
3. Agregar `actividad_tributaria` como indicador nuevo en la dimensión
   `actividad`, dejando `recaudacion` y su descomposición intactas.

## Decisión

Opción 3.

### Composición y bandas — medido, no elegido

Serie construida con `macro._real_ia_mensual` (mismo deflactor IPC que el
resto del cinturón, ADR-0078) sobre `INDEC_IVA_DGI_ID` y `INDEC_CHEQUE_ID`.
La ventana la limita el IPC nacional de datos.gob.ar (arranca en 2016-12), no
las series tributarias (que llegan a 2001): la interanual real requiere IPC en
`t` y en `t-12`, así que el compuesto arranca en **2017-12** y llega a
**2026-08** — 105 meses.

Percentiles de esa serie (ponderación 0,6/0,4): p10 = −12,6 · p25 = −5,6 ·
p50 = +0,3 · p75 = +6,0 · p90 = +12,1 (mín −26,8, máx +30,0). Es 2 a 2,5 veces
más volátil que `emae_ia` en el mismo tipo de medida (p10/p90 del EMAE:
−5,4/+9,5 sobre 258 meses).

Se probó reusar las bandas de `emae_ia` tal cual (mismo criterio que
`ipi_manufacturero`, ADR-0076/0079): con los cortes del EMAE (5/3/0/−2/−5), el
compuesto satura **26,7-28,6% de los meses en el peor tramo y 32,4-33,3% en el
mejor** —61% de la historia en un extremo o el otro, lo opuesto a "nacer
discriminando" (ADR-0042). Se descarta.

Bandas nuevas, calibradas contra los 105 meses propios, con el cero como
frontera conceptual (mismo criterio que `emae_ia`/`ipi_manufacturero`,
ADR-0120) y cortes redondos de 5 puntos escalados a la volatilidad medida:

| Banda | Puntaje |
|---|---|
| > 10 | 100 |
| 5 – 10 | 80 |
| 0 – 5 | 60 |
| −5 – 0 | 40 |
| −10 – −5 | 20 |
| ≤ −10 | 5 |

Reparto resultante: 14,3 / 14,3 / 20,0 / 18,1 / 14,3 / 19,0% — ningún tramo
concentra más de una quinta parte de la historia. Clasificado `historia_larga`
en `procedencia_anclas.py` (calibrado contra la serie propia, incluyendo años
anteriores a esta gestión).

### Rezago medido de los cuatro indicadores de `actividad` (16-sep-2026)

Contra el último mes calendario cerrado (agosto de 2026):

| Indicador | Último dato disponible | Atraso |
|---|---|---|
| `actividad_tributaria` | 2026-08 | **0 meses** |
| `ipi_manufacturero` | 2026-07 | 1 mes |
| `emae_ia` | 2026-06 | 2 meses |
| `emae_difusion` | 2026-06 | 2 meses |

Confirma la premisa del encargo: Hacienda/ARCA publica IVA-DGI y cheque antes
de que el INDEC cierre el EMAE del mismo período — es la señal más fresca de
la dimensión.

### Peso dentro de la dimensión `actividad`

`actividad_tributaria` es una fuente **distinta** (Hacienda/ARCA, no INDEC), a
diferencia de `emae_difusion` (ADR-0124), que se financió restando su peso
entero al EMAE agregado porque es la MISMA fuente en otro registro. Acá se
recortan los tres indicadores INDEC **proporcionalmente** (×0,80), mismo
criterio que ADR-0071/0074 usaron en la dimensión `financiamiento`:

| Indicador | Peso anterior | Peso nuevo |
|---|---|---|
| `emae_ia` | 0,60 | 0,48 |
| `emae_difusion` | 0,20 | 0,16 |
| `ipi_manufacturero` | 0,20 | 0,16 |
| `actividad_tributaria` | — | 0,20 |

La proporción INTERNA EMAE/IPI (80/20, ADR-0124/0079) no se toca —sigue
siendo 0,48+0,16 = 0,64 de 0,80 (80%) y 0,16 de 0,80 (20%)—, sólo baja el peso
absoluto de los tres para hacerle lugar a la fuente nueva.

### Doble uso con `recaudacion` — cuantificado

IVA-DGI y cheque son, entre ambos, 30,2%–61,9% del agregado DGI que puntúa en
`recaudacion` (53,6% en ago-2026; medido en ADR-0321). Pero el solapamiento
real es menor de lo que ese porcentaje sugiere, por dos razones medidas:

1. **Transformación distinta.** `recaudacion` puntúa un NIVEL real
   desestacionalizado (100 = 4T-2023); `actividad_tributaria` puntúa una
   VARIACIÓN interanual real. No son la misma serie con otro nombre.
2. **Correlación medida entre el compuesto y la interanual real del propio
   agregado DGI:** r = 0,355 (n = 105, dic-2017/ago-2026) — apenas ~13% de
   varianza compartida (r²).

Peso de cada uno en el ITCM: `actividad_tributaria` aporta 0,11 × 0,20 = 2,2%
del ITCM; `recaudacion` aporta 0,24 × 0,30 = 7,2%. Asignándole a
`recaudacion` el 100% de su covarianza medida con IVA+cheque (7,2% × 13% ≈
0,9%) más el 2,2% directo, el ITCM tiene alrededor de **3% de su peso total**
potencialmente expuesto al mismo shock tributario puro (una moratoria, un
cambio de alícuota) en dos dimensiones distintas. Es menor que el 11% que ya
concentra `competitividad_externa` en un único indicador (`tcrm`), y menor que
el 7,2% que `recaudacion` sola aporta. **El efecto es chico**: no se ajustan
más pesos por esto, y se declara con el número en el `dobleUso` de la ficha de
`actividad_tributaria` en vez de dejarlo implícito.

### Consecuencias

- El ITCM gana un cuarto indicador de actividad, con menos atraso de
  publicación que los tres existentes.
- El texto y el cálculo de `recaudacion` (`_control_tributario`, ADR-0321) no
  cambian: siguen explicando de dónde vino un movimiento del agregado DGI.
- La proporción circular del ITCM (`procedencia_anclas.py`) no sube: la banda
  nueva es `historia_larga`, no `convencion`/`sin_declarar`.

### Confirmación

`tests/test_itcm.py`, `tests/test_itcm_peso_ipi.py`,
`tests/test_itcm_difusion.py` (actualizado: la proporción 80/20 EMAE/IPI ahora
se verifica DENTRO del peso INDEC conjunto, no como fracción de 1,0),
`tests/test_web_labels.py`, `tests/test_fichas_pesos.py`,
`tests/test_fichas_bandas.py`, `tests/test_la_ficha_no_se_queda_atras.py`.

## Pros y contras de las opciones

- **1. Dejarlo como control sin puntuar:** no requiere tocar pesos ni bandas,
  pero desatiende el pedido original de un proxy que puntúe.
- **2. Reemplazar `recaudacion`:** pierde la medida de viabilidad fiscal
  (ADR-0072) sin necesidad — las dos preguntas (¿el Estado se financia? ¿la
  economía se mueve?) son legítimas y separables.
- **3. Indicador nuevo, `recaudacion` intacta:** agrega la señal pedida sin
  perder la que ya existía; el costo es el doble uso parcial, cuantificado y
  declarado arriba.

## Más información

- ADR-0318/0319: la decisión original de sumar IVA-DGI y cheque como
  "control" dentro de `recaudacion`.
- ADR-0321: corrige el encuadre de esos dos ADR (descomposición, no control
  independiente) — no se toca con este ADR.
- ADR-0076/0079: por qué `ipi_manufacturero` entra como respaldo del EMAE y
  hereda sus bandas — el precedente que este ADR evalúa y descarta reusar tal
  cual, con la medición de por qué no cierra.
- ADR-0124: por qué `emae_difusion` se financia restando al EMAE agregado en
  vez de recortar proporcionalmente — el contraste que explica por qué acá sí
  se recorta proporcionalmente (fuente distinta, no la misma en otro
  registro).
- ADR-0192/ADR-0252/ADR-0257: la matriz de `desequilibrio_monetario`, el
  patrón evaluado y descartado para este indicador.
- ADR-0071/0074: el precedente de recorte proporcional al sumar un indicador
  de fuente nueva a una dimensión existente.
