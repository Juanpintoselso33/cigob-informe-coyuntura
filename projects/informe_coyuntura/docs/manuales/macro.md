# Manual metodológico — cinturón Macro (ITCM)

> **Generado** por `scripts/manual_cinturon.py` desde el código que corre
> (`scripts/itcm.py`) y el frontmatter de los ADR. No editar a mano.
>
> Dice el **método**, no el valor: los números los deriva el pipeline
> (ADR-0156), así que este documento no caduca cuando cambia el dato.

Los ADR responden *por qué* se decidió cada cosa y *cuándo*. Este manual
responde *qué rige hoy*. Para la historia de una decisión, seguí el link
al ADR.

## Dimensiones y pesos

| Dimensión | Peso | Indicadores |
|---|---:|---|
| `estabilidad_monetaria` | 26% | `ipc_total`, `rem_ipc_12m`, `idm`, `desequilibrio_monetario` |
| `viabilidad_fiscal_comercial` | 24% | `resultado_primario`, `recaudacion`, `saldo_comercial_12m` |
| `financiamiento` | 16% | `reservas_bcra`, `idc`, `costo_financiamiento_tesoro`, `credito_privado` |
| `actividad` | 11% | `emae_ia`, `emae_difusion`, `ipi_manufacturero` |
| `competitividad_externa` | 11% | `tcrm` |
| `inversion` | 12% | `iai`, `icip` |

Suma de pesos: 100%.

## Qué mide cada indicador

### Dimensión `estabilidad_monetaria` (26%)

#### Inflación mensual (IPC)

`ipc_total`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **10.4%** |
| Procedencia del ancla | `conceptual` — bandas normativas: metas de estabilidad de precios, deliberadamente NO ancladas a la historia para no blanquear la señal (ADR-0120) |

**Bandas**: ≤ 1 → 100 · 1–2 → 85 · 2–3 → 65 · 3–5 → 40 · > 5 → 10

**Lo gobiernan**: [ADR-0077](../adr/0077-ipc-nucleo-serie-acompanante.md) El IPC general se lee junto al núcleo · [ADR-0122](../adr/0122-riesgo-sistemico-del-deflactor-ipc.md) El riesgo sistémico del deflactor IPC, declarado en la metodología · [ADR-0193](../adr/0193-peso-del-desequilibrio-monetario.md) El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó

#### Expectativas inflación (REM 12m)

`rem_ipc_12m`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.2%** |
| Procedencia del ancla | `conceptual` — hereda las bandas normativas del ipc_total —misma vara para inflación esperada y realizada— (ADR-0120) |

**Bandas**: ≤ 1 → 100 · 1–2 → 85 · 2–3 → 65 · 3–5 → 40 · > 5 → 10

**Lo gobiernan**: [ADR-0002](../adr/0002-rem-equivalente-mensual.md) El REM se puntúa por su equivalente mensual (raíz-12), no por nivel absoluto · [ADR-0193](../adr/0193-peso-del-desequilibrio-monetario.md) El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó

#### Exceso de pesos sobre la demanda (IDM)

`idm`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.2%** |
| Procedencia del ancla | `convencion` — «calibrado con la historia 2024-2026» |

**Bandas**: ≤ -2 → 100 · -2–2 → 85 · 2–5 → 60 · 5–8 → 35 · > 8 → 10

**Lo gobiernan**: [ADR-0053](../adr/0053-transparencia-y-agregados-monetarios-idm.md) Transparencia y agregados monetarios del IDM · [ADR-0193](../adr/0193-peso-del-desequilibrio-monetario.md) El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó

#### Dolarización dentro y fuera del sistema

`desequilibrio_monetario`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.2%** |
| Procedencia del ancla | `convencion` — cortes por percentiles (p0/p25/p50/p75/p100) de cada componente, como pide la sección 7 de la ficha; la matriz A×B y sus cuatro esquinas vienen del documento (ADR-0192) |

**Bandas**: ≤ 20 → 100 · 20–50 → 60 · 50–80 → 35 · > 80 → 10

**Lo gobiernan**: [ADR-0192](../adr/0192-desequilibrio-monetario-stock-por-flujo.md) Desequilibrio monetario: cruzar el stock que se ve con el flujo que se va · [ADR-0193](../adr/0193-peso-del-desequilibrio-monetario.md) El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó

### Dimensión `viabilidad_fiscal_comercial` (24%)

#### Resultado primario del Estado nacional

`resultado_primario`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **12.0%** |
| Procedencia del ancla | `convencion` — referencias dic-2023 (−12,0%) y el programa estabilizado en +6/+8% (ADR-0072) |

**Bandas**: > 8 → 100 · 4–8 → 85 · 0–4 → 60 · -5–0 → 30 · ≤ -5 → 10

**Lo gobiernan**: [ADR-0072](../adr/0072-resultado-primario-dimension-fiscal.md) resultado_primario: la dimensión fiscal pasa a medir resultado, no ingresos · [ADR-0127](../adr/0127-la-recaudacion-mide-la-base-imponible-no-la-caja.md) La recaudación mide la base imponible, no la caja: pasa a DGI

#### Base imponible real (nación + provincias)

`recaudacion`

| | |
|---|---|
| Peso dentro de la dimensión | 30% |
| Peso efectivo en el índice | **7.2%** |
| Procedencia del ancla | `conceptual` — bandas de variación real en torno al cero; los cortes caen razonablemente en la distribución 2021-2023 de la serie DGI que se puntúa desde ADR-0127 (mediana +4,5%; p0/p14/p57/p80) y NO se recalibraron al cambiar de fuente (ADR-0120) |

**Bandas**: > 110 → 100 · 100–110 → 85 · 90–100 → 60 · 80–90 → 35 · ≤ 80 → 10

**Lo gobiernan**: [ADR-0003](../adr/0003-recaudacion-interanual-real.md) La recaudación se mide en variación interanual REAL (deflactada) · [ADR-0029](../adr/0029-recaudacion-promedio-movil-3m.md) Recaudación real: promedio móvil de 3 meses sobre IPC cerrado · [ADR-0072](../adr/0072-resultado-primario-dimension-fiscal.md) resultado_primario: la dimensión fiscal pasa a medir resultado, no ingresos · [ADR-0127](../adr/0127-la-recaudacion-mide-la-base-imponible-no-la-caja.md) La recaudación mide la base imponible, no la caja: pasa a DGI

#### Saldo comercial 12m

`saldo_comercial_12m`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **4.8%** |
| Procedencia del ancla | `conceptual` — bandas en torno al equilibrio comercial (cero), techo institucional 85; consistentes con la mediana histórica (ADR-0120) |

**Bandas**: > 15000 → 85 · 10000–15000 → 75 · 5000–10000 → 60 · -5000–5000 → 50 · -15000–-5000 → 30 · ≤ -15000 → 10

**Lo gobiernan**: [ADR-0056](../adr/0056-suavizado-ajuste-automatico-saldo-comercial.md) Suavizado del ajuste automático de saldo comercial por composición expo/impo · [ADR-0080](../adr/0080-cuenta-corriente-contexto-saldo-comercial.md) La cuenta corriente acompaña al saldo comercial, y el texto público se corrige

### Dimensión `financiamiento` (16%)

#### Reservas netas

`reservas_bcra`

| | |
|---|---|
| Peso dentro de la dimensión | 34% |
| Peso efectivo en el índice | **5.4%** |
| Procedencia del ancla | `conceptual` — bandas en torno al cero de reservas netas: nivel de cobertura, no distribución observada (ADR-0120) |

**Bandas**: > 20000 → 100 · 15000–20000 → 85 · 10000–15000 → 70 · 5000–10000 → 50 · 0–5000 → 30 · ≤ 0 → 10

**Lo gobiernan**: [ADR-0005](../adr/0005-reservas-netas-a-secas.md) Reservas: netas "a secas" calculadas de la planilla SDDS + Tesoro + Bopreal

#### Capacidad prestable (IdC)

`idc`

| | |
|---|---|
| Peso dentro de la dimensión | 21% |
| Peso efectivo en el índice | **3.4%** |
| Procedencia del ancla | `conceptual` — anclas en desvíos estándar: +1σ ≈ p84 · −1σ ≈ p16 (ADR-0028) |

**Bandas**: > 1 → 100 · 0.5–1 → 85 · -0.5–0.5 → 60 · -1–-0.5 → 35 · ≤ -1 → 10

**Lo gobiernan**: [ADR-0027](../adr/0027-auditoria-idc-rediseno.md) Auditoría adversarial del IdC: hallazgos y opciones de rediseño · [ADR-0028](../adr/0028-idc-z-scores.md) IdC rediseñado: z-scores de nivel contra la propia historia · [ADR-0074](../adr/0074-rebalanceo-idc-credito.md) El crédito otorgado deja de pesar un tercio de la capacidad de prestar

#### Costo real del financiamiento del Tesoro

`costo_financiamiento_tesoro`

| | |
|---|---|
| Peso dentro de la dimensión | 25% |
| Peso efectivo en el índice | **4.0%** |
| Procedencia del ancla | `convencion` — extremos tomados de dic-2023 (−12,2%) y ago-2025 (+33,5%) (ADR-0071) |

**Bandas**: > 20 → 15 · 12–20 → 45 · 6–12 → 75 · 0–6 → 100 · -5–0 → 55 · ≤ -5 → 20

**Lo gobiernan**: [ADR-0071](../adr/0071-costo-financiamiento-tesoro.md) costo_financiamiento_tesoro: el precio del financiamiento soberano entra al ITCM

#### Crédito privado real

`credito_privado`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **3.2%** |
| Procedencia del ancla | `convencion` — «calibradas a la remonetización 2024-2026» (ADR-0022) |

**Bandas**: > 40 → 100 · 20–40 → 85 · 8–20 → 65 · 0–8 → 45 · -10–0 → 25 · ≤ -10 → 10

**Lo gobiernan**: [ADR-0074](../adr/0074-rebalanceo-idc-credito.md) El crédito otorgado deja de pesar un tercio de la capacidad de prestar

### Dimensión `actividad` (11%)

#### Actividad económica (EMAE i.a.)

`emae_ia`

| | |
|---|---|
| Peso dentro de la dimensión | 60% |
| Peso efectivo en el índice | **6.6%** |
| Procedencia del ancla | `conceptual` — bandas de crecimiento en torno al cero; el corte de crecimiento nulo cae en p26 de la historia 2021-2023 (ADR-0120) |

**Bandas**: > 5 → 100 · 3–5 → 80 · 0–3 → 60 · -2–0 → 40 · -5–-2 → 20 · ≤ -5 → 5

**Lo gobiernan**: [ADR-0076](../adr/0076-ipi-segunda-senal-actividad.md) La dimensión de actividad deja de colgar de un único dato · [ADR-0079](../adr/0079-peso-del-ipi-en-actividad.md) El IPI baja de 35% a 20%: es respaldo, no medida principal

#### Amplitud del crecimiento (sectores en alza)

`emae_difusion`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **2.2%** |
| Procedencia del ancla | `conceptual` — cortes por CANTIDAD DE SECTORES (14-15 generalizado · 11-13 mayoría amplia · 8-10 ajustada · 5-7 minoría · 0-4 contracción), puestos en el hueco entre valores alcanzables; explícitamente NO se ancló en el 50% de manual porque la mediana histórica argentina es 73,3% (ADR-0124) |

**Bandas**: > 90 → 100 · 70–90 → 80 · 50–70 → 60 · 30–50 → 35 · ≤ 30 → 10

**Lo gobiernan**: [ADR-0124](../adr/0124-la-actividad-se-mide-tambien-en-amplitud.md) La actividad se mide también en amplitud: entra la difusión sectorial del EMAE

#### Producción industrial (IPI i.a.)

`ipi_manufacturero`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **2.2%** |
| Procedencia del ancla | `conceptual` — hereda las bandas del EMAE a propósito para dejar ver la brecha industria-actividad, con cita a ADR-0045 (ADR-0076/0079) |

**Bandas**: > 5 → 100 · 3–5 → 80 · 0–3 → 60 · -2–0 → 40 · -5–-2 → 20 · ≤ -5 → 5

**Lo gobiernan**: [ADR-0076](../adr/0076-ipi-segunda-senal-actividad.md) La dimensión de actividad deja de colgar de un único dato · [ADR-0079](../adr/0079-peso-del-ipi-en-actividad.md) El IPI baja de 35% a 20%: es respaldo, no medida principal

### Dimensión `competitividad_externa` (11%)

#### Tipo de cambio real (TCRM)

`tcrm`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **11.0%** |
| Procedencia del ancla | `historia_larga` — historia 1997-2026: p10≈75, p25≈87, mediana≈106 — 29 años, cinco gobiernos |

**Bandas**: > 110 → 100 · 95–110 → 80 · 85–95 → 60 · 75–85 → 35 · ≤ 75 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón.

### Dimensión `inversion` (12%)

#### Inversión física (IAI)

`iai`

| | |
|---|---|
| Peso dentro de la dimensión | 60% |
| Peso efectivo en el índice | **7.2%** |
| Procedencia del ancla | `convencion` — el umbral ±2% del documento «no sobrevive al dato»: se reemplazó por bandas calibradas a 2024-2026 |

**Bandas**: > 10 → 100 · 2–10 → 80 · -2–2 → 60 · -10–-2 → 35 · ≤ -10 → 10

**Lo gobiernan**: [ADR-0010](../adr/0010-capitulo-inversion-iai-icip.md) Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión del ITCM

#### Capitalización digital (ICIP)

`icip`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **4.8%** |
| Procedencia del ancla | `convencion` — banda ensanchada por la volatilidad observada del período |

**Bandas**: > 20 → 100 · 5–20 → 80 · -5–5 → 60 · -20–-5 → 35 · ≤ -20 → 10

**Lo gobiernan**: [ADR-0010](../adr/0010-capitulo-inversion-iai-icip.md) Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión del ITCM

## Se releva y no puntúa

Estos indicadores se siguen scrapeando y cacheando, pero están fuera
del índice y fuera del tablero. Sus bandas quedan como referencia
histórica.

- `badlar` — Tasa BADLAR (declarado como contexto)
- `base_monetaria` — Base monetaria (declarado como contexto)
- `prestamos_privados` — Préstamos al sector privado (declarado como contexto)
- `tc_mayorista` — Tipo de cambio mayorista (declarado como contexto)

## Decisiones abiertas

4 ADR vigentes de este cinturón declaran algo pendiente de decisión editorial. No son trabajo técnico: son llamadas que sólo puede hacer el editor.

> La detección lee la prosa, así que **sobre-reporta a propósito**: si un ADR anota un pendiente y lo resuelve unos párrafos más abajo, sigue apareciendo acá. Se prefiere ese error al contrario —perder una decisión realmente abierta—. La marca ⚠️ sí es firme: sale de las relaciones declaradas entre ADR, no de adivinar sobre el texto.

- **[ADR-0076](../adr/0076-ipi-segunda-senal-actividad.md)** — La dimensión de actividad deja de colgar de un único dato
  <br>intercambiable con lo que ya hay. **Queda como candidata abierta y evaluada**,
- **[ADR-0120](../adr/0120-el-itcm-declara-el-origen-de-sus-bandas.md)** — El ITCM declara el origen de sus bandas, y baja del 83% al 38% de circularidad
  <br>- Queda pendiente de otros frentes, no de éste: el ITCM sigue sin ancla
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0121. Verificar antes de tratarlo como abierto.
- **[ADR-0158](../adr/0158-validacion-del-itcm-por-puntos-de-giro.md)** — El ITCM se valida por puntos de giro, no sólo por correlación
  <br>- **Queda pendiente** el régimen socioeconómico para los otros tres cinturones.
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0159. Verificar antes de tratarlo como abierto.
- **[ADR-0192](../adr/0192-desequilibrio-monetario-stock-por-flujo.md)** — Desequilibrio monetario: cruzar el stock que se ve con el flujo que se va
  <br>- El peso definitivo dentro de la dimensión queda pendiente de definir con Diego.
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0193. Verificar antes de tratarlo como abierto.

## Todos los ADR vigentes de este cinturón

32 en total. El índice completo, con los superados y rechazados, está en [docs/adr/README.md](../adr/README.md).

- [0002](../adr/0002-rem-equivalente-mensual.md) — El REM se puntúa por su equivalente mensual (raíz-12), no por nivel absoluto
- [0003](../adr/0003-recaudacion-interanual-real.md) — La recaudación se mide en variación interanual REAL (deflactada)
- [0005](../adr/0005-reservas-netas-a-secas.md) — Reservas: netas "a secas" calculadas de la planilla SDDS + Tesoro + Bopreal
- [0008](../adr/0008-tcrm-itcrm-bcra.md) — El TCRM usa el ITCRM oficial del BCRA, no la serie discontinuada de INDEC
- [0009](../adr/0009-idm-y-tcrm-en-el-itcm.md) — Índice de Desequilibrio Monetario (real-real i.a.) y el TCRM como 5ª dimensión del ITCM
- [0010](../adr/0010-capitulo-inversion-iai-icip.md) — Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión del ITCM
- [0022](../adr/0022-credito-real-y-contexto-oculto.md) — Crédito privado real al ITCM; los monetarios nominales quedan ocultos
- [0027](../adr/0027-auditoria-idc-rediseno.md) — Auditoría adversarial del IdC: hallazgos y opciones de rediseño
- [0028](../adr/0028-idc-z-scores.md) — IdC rediseñado: z-scores de nivel contra la propia historia
- [0029](../adr/0029-recaudacion-promedio-movil-3m.md) — Recaudación real: promedio móvil de 3 meses sobre IPC cerrado
- [0053](../adr/0053-transparencia-y-agregados-monetarios-idm.md) — Transparencia y agregados monetarios del IDM
- [0056](../adr/0056-suavizado-ajuste-automatico-saldo-comercial.md) — Suavizado del ajuste automático de saldo comercial por composición expo/impo
- [0057](../adr/0057-canal-informal-cripto-presion-dolarizacion.md) — Canal informal (dólar cripto) en la presión de dolarización
- [0071](../adr/0071-costo-financiamiento-tesoro.md) — costo_financiamiento_tesoro: el precio del financiamiento soberano entra al ITCM
- [0072](../adr/0072-resultado-primario-dimension-fiscal.md) — resultado_primario: la dimensión fiscal pasa a medir resultado, no ingresos
- [0074](../adr/0074-rebalanceo-idc-credito.md) — El crédito otorgado deja de pesar un tercio de la capacidad de prestar
- [0075](../adr/0075-redundancia-interna-itcm.md) — Se publica cuánta información distinta aporta cada componente del ITCM
- [0076](../adr/0076-ipi-segunda-senal-actividad.md) — La dimensión de actividad deja de colgar de un único dato
- [0077](../adr/0077-ipc-nucleo-serie-acompanante.md) — El IPC general se lee junto al núcleo
- [0078](../adr/0078-error-compartido-del-deflactor.md) — El error del deflactor deja de tratarse como independiente
- [0079](../adr/0079-peso-del-ipi-en-actividad.md) — El IPI baja de 35% a 20%: es respaldo, no medida principal
- [0080](../adr/0080-cuenta-corriente-contexto-saldo-comercial.md) — La cuenta corriente acompaña al saldo comercial, y el texto público se corrige
- [0083](../adr/0083-presion-dolarizacion-maximo.md) — La presión de dolarización pasa a ser el máximo de sus dos canales
- [0106](../adr/0106-linea-de-base-diciembre-2023.md) — El ITCM publica su punto de partida
- [0120](../adr/0120-el-itcm-declara-el-origen-de-sus-bandas.md) — El ITCM declara el origen de sus bandas, y baja del 83% al 38% de circularidad
- [0122](../adr/0122-riesgo-sistemico-del-deflactor-ipc.md) — El riesgo sistémico del deflactor IPC, declarado en la metodología
- [0124](../adr/0124-la-actividad-se-mide-tambien-en-amplitud.md) — La actividad se mide también en amplitud: entra la difusión sectorial del EMAE
- [0127](../adr/0127-la-recaudacion-mide-la-base-imponible-no-la-caja.md) — La recaudación mide la base imponible, no la caja: pasa a DGI
- [0152](../adr/0152-la-recaudacion-mide-nivel-no-variacion.md) — La recaudación pasa a medir NIVEL, y suma los impuestos provinciales
- [0158](../adr/0158-validacion-del-itcm-por-puntos-de-giro.md) — El ITCM se valida por puntos de giro, no sólo por correlación
- [0192](../adr/0192-desequilibrio-monetario-stock-por-flujo.md) — Desequilibrio monetario: cruzar el stock que se ve con el flujo que se va
- [0193](../adr/0193-peso-del-desequilibrio-monetario.md) — El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó
