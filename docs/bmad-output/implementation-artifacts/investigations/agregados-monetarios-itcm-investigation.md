# Investigación: agregados monetarios del ITCM

## Hand-off Brief

1. **Qué se comprobó.** El IDM vigente ya usa exactamente el M2 Transaccional del Sector Privado propuesto; su M3 es el agregado privado en pesos y el peso efectivo del indicador es 7,8% del ITCM.
2. **Qué arrojó la alternativa.** Sumar depósitos privados en dólares valuados en pesos es automatizable y responde a un M3* históricamente utilizado por el BCRA, pero no es un reemplazo neutral: en 30 meses elevó el IDM medio en 6,91 pp, cambió el signo en cinco meses y llevó el dato actual de 4,30 a 8,18 pp.
3. **Recomendación.** Conservar el IDM puntuable en pesos, no incorporar M3* en la fórmula vigente, y mejorar la transparencia pública del peso y aporte; la liquidez bimonetaria puede mostrarse como contexto separado y no puntuable.

## Case Info

| Field            | Value |
| ---------------- | ----- |
| Ticket           | N/A |
| Date opened      | 2026-07-13 |
| Status           | Concluded |
| System           | Informe de Coyuntura CIGOB/UBA — cinturón macro (ITCM), Windows 11, rama `main` |
| Evidence sources | Código, datos publicados, series históricas, ADRs, tests, API y documentación oficial del BCRA, API de Series de Tiempo de la República Argentina |

## Problem Statement

El usuario solicita auditar estas sugerencias recibidas de Diego por intermedio de Luis Babino: tomar el “M2 Transaccional del Sector Privado (circulante en poder del público + depósitos en cuentas corrientes y cajas de ahorro del sector privado en pesos, excluyendo vista remunerada de personas jurídicas)”; tomar el “M3' (prima) o M3 ampliado que incluye los depósitos en dólares”; y aclarar cómo pondera el índice de desequilibrio monetario en el total del cinturón macro. Se evalúan pertinencia conceptual, disponibilidad y automatización, impacto histórico, efecto sobre bandas y claridad pública, sin implementar cambios de producto.

## Evidence Inventory

| Source | Status | Notes |
| ------ | ------ | ----- |
| Colector y fórmula IDM | Available | Variables, cierre mensual, deflactación y fórmula trazados en `projects/informe_coyuntura/scripts/macro.py:59-70`, `:172-190`, `:215-250` y `:744-764`. |
| Scoring y ponderaciones | Available | Bandas y pesos trazados en `projects/informe_coyuntura/scripts/itcm.py:91-98` y `:153-187`; interpolación y aportes en `projects/informe_coyuntura/scripts/parametrica.py:42-72` y `:169-191`. |
| Snapshot público vigente | Available | Valor, score, composición y peso efectivo en `projects/informe_coyuntura/output/informe.json:162-174`. |
| Serie histórica IDM | Available | Serie versionada en `projects/informe_coyuntura/output/series/macro.csv` y `projects/informe_coyuntura/web/src/data/series.json:10510-10638`. |
| Definición BCRA de M2 transaccional | Available | Variable 197 y metodología oficial verificadas por API; coincide con la sugerencia. |
| Definición y componentes de M3* | Available | Antecedentes oficiales BCRA y variables 104, 108 y 84 verificadas; reconstrucción reproducible. |
| Comparación numérica | Available | 30 observaciones mensuales completas, dic-2023–may-2026, replicando exactamente el cálculo vigente. |
| Transparencia web | Available | Modal de indicador, modal de dimensión y ficha metodológica auditados. |

## Investigation Backlog

| # | Path to Explore | Priority | Status | Notes |
| - | --------------- | -------- | ------ | ----- |
| 1 | Trazar colector, cálculo y publicación del IDM | High | Done | Fórmula y variables confirmadas. |
| 2 | Trazar bandas paramétricas y ponderaciones | High | Done | Peso interno 30%, dimensión 26%, peso efectivo 7,8%. |
| 3 | Verificar definición oficial de M2 Transaccional privado | High | Done | Variable 197 coincide con la propuesta. |
| 4 | Verificar definición y disponibilidad de M3 prima/ampliado | High | Done | Concepto oficial histórico; reconstrucción actual con 17 + 100 + 104. |
| 5 | Comparar continuidad histórica y sensibilidad | Medium | Done | Backtest dic-2023–may-2026 completado. |
| 6 | Auditar claridad de fórmula, ficha y textos públicos | Medium | Done | La información existe, pero la cadena completa está fragmentada. |
| 7 | Evaluar validez predictiva de un indicador bimonetario nuevo | Low | Deferred | Sólo corresponde si se decide diseñar un indicador distinto, no para reemplazo directo. |

## Timeline of Events

| Time | Event | Source | Confidence |
| ---- | ----- | ------ | ---------- |
| 2026-07-13 15:25 ART | Diego propone, vía Luis, M2 Transaccional privado y M3 ampliado con depósitos en dólares; consulta la ponderación del IDM. | Mensaje aportado por el usuario | Confirmed |
| 2026-07-13 | Se reconstruyen código, fórmula, bandas, ponderaciones y presentación pública. | Código y salidas del repositorio | Confirmed |
| 2026-07-13 | Se validan variables y metodologías BCRA 17, 84, 100, 104, 108 y 197. | API BCRA v4.0 y documentación oficial | Confirmed |
| 2026-07-13 | Se reconstruye IDM alternativo con M3* privado para 30 meses. | APIs BCRA/INDEC y fórmula del repositorio | Confirmed |

## Confirmed Findings

### Finding 1: El M2 sugerido ya está implementado

**Evidence:** `projects/informe_coyuntura/scripts/macro.py:66-69`; metodología BCRA de la variable 197.

**Detail:** La variable 197 es “M2 transaccional del sector privado” e incluye circulante en poder del público, cuentas corrientes y cajas de ahorro privadas en pesos, excluyendo depósitos a la vista remunerados de personas jurídicas. No corresponde cambiar el cálculo por esta sugerencia; sí puede alinearse el texto público con la definición oficial exacta.

### Finding 2: El IDM vigente compara dos agregados privados en pesos

**Evidence:** `projects/informe_coyuntura/scripts/macro.py:215-250`.

**Detail:**

\[
M3_{pesos}=\text{var17}+\text{var100}
\]

\[
IDM=g^{real}_{12m}(M3_{pesos})-g^{real}_{12m}(M2_{transaccional})
\]

Ambos stocks se toman al último dato disponible de cada mes y se deflactan con el mismo IPC mensual del INDEC.

### Finding 3: El peso efectivo del IDM es 7,8% del ITCM

**Evidence:** `projects/informe_coyuntura/scripts/itcm.py:153-187`; `projects/informe_coyuntura/scripts/parametrica.py:169-191`; `projects/informe_coyuntura/output/informe.json:162-174`.

**Detail:** El IDM pesa 30% dentro de `estabilidad_monetaria`, dimensión que pesa 26% del ITCM:

\[
0,30\times0,26=0,078=7,8\%
\]

Con score vigente cercano a 53,2/100, aporta aproximadamente 4,15 puntos al ITCM:

\[
53,2\times0,078\approx4,15
\]

### Finding 4: M3* es un concepto oficial histórico, aunque no una variable agregada única en la publicación actual

**Evidence:** BCRA, *Informe Monetario Mensual* de octubre de 2008; BCRA, *Objetivos y planes... 2013*; BCRA, *Informe Monetario Mensual* de diciembre de 2017.

**Detail:** El BCRA definió M3* como circulante más depósitos en pesos y moneda extranjera, y publicó una variante privada. Su perímetro histórico no fue completamente invariable: en algunos períodos incluyó cheques cancelatorios en moneda extranjera y CEDIN. Los informes actuales vuelven a definir M3 privado como agregado en pesos y presentan los depósitos en dólares en un segmento separado.

### Finding 5: La alternativa es técnicamente automatizable

**Evidence:** API BCRA v4.0, variables 104, 108 y 84.

**Detail:** Para la propuesta auditada se reconstruyó:

\[
M3^*_{privado}=\text{var17}+\text{var100}+\text{var104}
\]

La variable 104 son depósitos privados no financieros en moneda extranjera expresados en millones de ARS. Se verificó en todos los cierres mensuales la identidad:

\[
\text{var104}=\text{var108 en USD}\times\text{var84 ARS/USD}
\]

### Finding 6: M3* no produce un ajuste marginal; cambia materialmente la señal

**Evidence:** reconstrucción mensual dic-2023–may-2026, 30 observaciones.

| Serie | Media | Desv. est. | Mínimo | Máximo |
| --- | ---: | ---: | ---: | ---: |
| IDM vigente | −0,72 | 6,86 | −13,44 | 7,13 |
| IDM con M3* | 6,19 | 8,28 | −9,33 | 23,65 |
| Diferencia | **+6,91** | 4,52 | −0,89 | +19,10 |

**Detail:**

- Correlación entre variantes: **0,838**.
- La variante M3* fue mayor en **29 de 30 meses**.
- Cambió el signo de la lectura en **cinco meses**.
- El componente en dólares representó en promedio **25,13%** del stock ampliado.
- En sep–nov de 2024 la diferencia llegó a 15,33–19,10 pp, coincidiendo con el fuerte ingreso de depósitos en dólares por la regularización de activos.

### Finding 7: La valuación cambiaria domina buena parte del período auditado

**Evidence:** descomposición interanual de variables BCRA 104, 108 y 84.

**Detail:** En el promedio de los 30 meses, el crecimiento de los depósitos en dólares expresados en ARS fue explicado aproximadamente en **68,7% por valuación cambiaria** y en **31,3% por la cantidad de depósitos en USD**. En el último dato la composición se invierte parcialmente: cantidad 59,6%, valuación 40,4%.

La evidencia refuta una explicación exclusivamente cambiaria: los flujos reales de depósitos, especialmente CERA, también alteran mucho la serie. Pero confirma que el tipo de cambio es un determinante sustantivo ajeno a la oferta transaccional de pesos.

### Finding 8: Conservar las bandas actuales produciría saturación y una caída mecánica del ITCM

**Evidence:** `projects/informe_coyuntura/scripts/itcm.py:91-98`; último dato del backtest.

**Detail:** En mayo de 2026:

| Variante | IDM | Score con bandas actuales | Aporte al ITCM |
| --- | ---: | ---: | ---: |
| Vigente | 4,30 pp | 53,3 | 4,16 pts aprox. |
| M3* | 8,18 pp | 10,0 | 0,78 pts |

El cambio aislado restaría aproximadamente **3,38 puntos** al ITCM, de 59,0 a cerca de 55,6, sin que exista una recalibración conceptual o empírica que justifique esa penalización.

### Finding 9: La ponderación está publicada, pero no se explica de manera integrada

**Evidence:** `projects/informe_coyuntura/web/src/components/IndicadorModal.astro:26`, `:292-306` y `:377-430`; `projects/informe_coyuntura/web/src/pages/metodologia/[id].astro:120-125` y `:182-184`.

**Detail:** La ficha metodológica muestra el peso efectivo de 7,8%, y otras vistas muestran por separado el 30% interno y el 26% de la dimensión. El modal principal del indicador no reúne la cadena completa ni muestra directamente el aporte actual en puntos ITCM. La consulta de Luis es consistente con un problema de encontrabilidad y explicación, no con ausencia del dato.

## Deduced Conclusions

### Deduction 1: La sugerencia sobre M2 es pertinente como validación, no como cambio de metodología

**Based on:** Findings 1 y 2.

**Reasoning:** La serie y exclusiones propuestas coinciden con la variable ya utilizada.

**Conclusion:** Conservar cálculo; precisar nomenclatura pública si se implementan ajustes de transparencia.

### Deduction 2: M3* mide liquidez bimonetaria, pero no es comparable de forma directa con el M2 transaccional en pesos

**Based on:** Findings 4, 5, 6 y 7.

**Reasoning:** M3* amplía el inventario de pasivos líquidos del sistema, pero incorpora depósitos cuya moneda, función y régimen de intermediación difieren de los medios de pago domésticos en pesos. Convertirlos al tipo de cambio corriente añade además variaciones de valuación.

**Conclusion:** La sustitución cambiaría el constructo: dejaría de ser una brecha entre dinero amplio y transaccional en pesos y pasaría a ser una comparación asimétrica entre liquidez bimonetaria y transacciones en pesos.

### Deduction 3: Los episodios de regularización de activos no deben interpretarse automáticamente como “exceso de pesos”

**Based on:** Findings 6 y 7.

**Reasoning:** El salto de depósitos CERA aumentó la liquidez bancaria en dólares y formalizó activos externos, pero no creó por sí mismo pesos transaccionales ni presión inflacionaria equivalente.

**Conclusion:** La variante M3* produciría falsos positivos para el significado actual del IDM.

### Deduction 4: La sugerencia de transparencia es plenamente pertinente

**Based on:** Findings 3 y 9.

**Reasoning:** El cálculo existe y reconcilia, pero el usuario debe recorrer distintas pantallas para reconstruir `30% × 26% = 7,8%` y no ve el aporte corriente de aproximadamente 4,15 puntos.

**Conclusion:** Corresponde implementar una mejora de explicación pública.

## Hypothesized Paths

### Hypothesis 1: Incorporar depósitos en dólares mejora la representación de liquidez privada en una economía bimonetaria

**Status:** Confirmed for context; refuted as drop-in replacement.

**Theory:** Un M3 ampliado puede captar saldos líquidos relevantes que el agregado en pesos omite.

**Supporting indicators:** Antecedente oficial BCRA; depósitos en dólares equivalentes en promedio a una cuarta parte del stock ampliado.

**Would confirm replacement:** Mejora predictiva incremental y estable sobre inflación, brecha o desmonetización, controlando por IDM vigente, TCRM, grandes devaluaciones y regularizaciones.

**Would refute replacement:** Cambios de señal dominados por valuación, CERA u otros flujos ajenos al desequilibrio de pesos.

**Resolution:** El backtest demuestra alteraciones grandes, saturación de bandas y cinco cambios de signo. La hipótesis se conserva sólo para una serie contextual o un indicador nuevo con objetivo propio.

### Hypothesis 2: La duda sobre la ponderación refleja un déficit de transparencia pública

**Status:** Confirmed.

**Theory:** Aunque el peso esté codificado, puede no estar visible o explicarse insuficientemente en la vista principal.

**Resolution:** La ficha metodológica muestra 7,8%, pero el modal separa 30% interno, 26% de dimensión y aporte sin integrarlos. La información es correcta pero fragmentada.

## Source Code Trace

| Element | Detail |
| ------- | ------ |
| Variables actuales | `projects/informe_coyuntura/scripts/macro.py:59-70` |
| Selección fin de mes e IPC | `projects/informe_coyuntura/scripts/macro.py:172-190` |
| Fórmula IDM | `projects/informe_coyuntura/scripts/macro.py:215-250` |
| Dato corriente | `projects/informe_coyuntura/scripts/macro.py:744-764` |
| Bandas | `projects/informe_coyuntura/scripts/itcm.py:91-98` |
| Pesos | `projects/informe_coyuntura/scripts/itcm.py:153-187` |
| Interpolación y aporte | `projects/informe_coyuntura/scripts/parametrica.py:42-72`, `:169-191` |
| Publicación | `projects/informe_coyuntura/output/informe.json:162-174` |
| Transparencia web | `projects/informe_coyuntura/web/src/components/IndicadorModal.astro`; `projects/informe_coyuntura/web/src/pages/metodologia/[id].astro` |

## Conclusion

**Confidence:** High para rechazar el reemplazo directo; Medium para el diseño eventual de un indicador bimonetario separado.

La primera sugerencia ya está implementada: el proyecto usa el M2 Transaccional del Sector Privado de la variable BCRA 197. La segunda es técnicamente viable y tiene antecedente metodológico oficial, pero no debe incorporarse a la fórmula vigente: M3* cambia la moneda y función económica del numerador, mezcla cantidad de depósitos con valuación cambiaria, reacciona a flujos extraordinarios como CERA y rompe las bandas actuales. La tercera sugerencia identifica un problema real: el peso efectivo de 7,8% y el aporte corriente de aproximadamente 4,15 puntos no se explican juntos en la vista principal.

## Recommended Next Steps

### Decisión por sugerencia

| Sugerencia | Veredicto | Acción recomendada |
| --- | --- | --- |
| Usar M2 Transaccional privado | **Ya implementada** | No cambiar la serie; ajustar la redacción para citar su composición oficial exacta. |
| Reemplazar M3 por M3* con depósitos en dólares | **No implementar en el IDM vigente** | Mantener M3 privado en pesos. Si interesa, mostrar liquidez bimonetaria como contexto no puntuable o diseñar otro indicador con ADR y bandas propias. |
| Aclarar ponderación del IDM | **Implementar** | Mostrar en el modal: 30% interno × 26% dimensión = 7,8% del ITCM; sumar el aporte corriente en puntos. |

### Alcance de una eventual implementación

1. Ajustar el modal y los textos públicos para presentar en una sola cadena:
   - score IDM;
   - peso interno 30%;
   - peso de la dimensión 26%;
   - peso efectivo 7,8%;
   - aporte corriente aproximado al ITCM.
2. Alinear la definición pública de M2 con la redacción oficial BCRA.
3. Si se agrega contexto bimonetario, hacerlo dentro de la ficha/metodología o como componente explicativo no puntuable, no como nueva card de contexto.
4. Documentar cualquier cambio metodológico adicional mediante ADR.
5. Al afectar sólo el cinturón macro, usar el pipeline acotado a un cinturón; sólo regenerar la serie de `idm` y la validación externa si efectivamente cambia una serie puntuable.

## Reproduction Plan

1. Descargar variables BCRA 17, 84, 100, 104, 108 y 197 desde abril de 2022.
2. Retener el último dato de cada mes con la misma lógica de `_bcra_fin_de_mes`.
3. Descargar el IPC nivel general usado por `macro.py`.
4. Calcular para cada mes desde diciembre de 2023:
   - IDM vigente con 17 + 100;
   - IDM alternativo con 17 + 100 + 104.
5. Verificar `104 = 108 × 84` y descomponer cantidad/valuación.
6. Aplicar las anclas y peso efectivo vigentes para medir el efecto mecánico sobre el ITCM.

## Side Findings

- La ejecución directa del último dato produjo IDM 4,30, mientras la salida versionada conserva 4,31; la diferencia de 0,01 es de redondeo/actualización y no altera el diagnóstico.
- El M3 privado construido como 17 + 100 no incorpora explícitamente cheques cancelatorios en pesos que aparecen en la definición textual oficial; su materialidad actual es previsiblemente mínima, pero puede revisarse en una auditoría futura de composición fina.
- Existe una modificación local previa y ajena en `projects/informe_coyuntura/web/.gitignore`; no se tocó durante esta investigación.

## Fuentes oficiales externas

- BCRA, catálogo y series monetarias v4.0: https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias
- BCRA, *Informe Monetario Mensual, octubre de 2008*: https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-octubre-de-2008/
- BCRA, *Objetivos y planes respecto del desarrollo de la política monetaria, financiera, crediticia y cambiaria para 2013*: https://www.bcra.gob.ar/archivos/Pdfs/Institucional/BMA2013.pdf
- BCRA, *Informe Monetario Mensual, diciembre de 2017*: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/Bol1217.pdf
- BCRA, *Informe Monetario Mensual, septiembre de 2024*: https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-septiembre-de-2024/
