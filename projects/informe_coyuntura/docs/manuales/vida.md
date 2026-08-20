# Manual metodológico — cinturón Impacto social (ITCIS)

> **Generado** por `scripts/manual_cinturon.py` desde el código que corre
> (`scripts/itvc.py`) y el frontmatter de los ADR. No editar a mano.
>
> Dice el **método**, no el valor: los números los deriva el pipeline
> (ADR-0156), así que este documento no caduca cuando cambia el dato.

Los ADR responden *por qué* se decidió cada cosa y *cuándo*. Este manual
responde *qué rige hoy*. Para la historia de una decisión, seguí el link
al ADR.

## Dimensiones y pesos

| Dimensión | Peso | Indicadores |
|---|---:|---|
| `ingresos` | 28% | `brecha_salario_cbt`, `pobreza_nowcast`, `consumo_carne`, `patentamiento_motos` |
| `precios` | 25% | `ipc_alimentos`, `peso_tarifas`, `alquiler_real` |
| `vulnerabilidad` | 10% | `mora_familias` |
| `empleo` | 24% | `informalidad`, `empleo_registrado`, `mortalidad_pymes`, `despacho_cemento`, `pluriempleo` |
| `percepcion` | 8% | `icc_utdt`, `sentimiento_digital` |
| `seguridad` | 4% | `inseguridad` |

Suma de pesos: 100%.

## Cómo puntúa este cinturón

A diferencia de los índices por bandas, acá **no hay tabla de cortes**:
cada componente ya es un índice base 100 = 4T-2023 (ADR-0018), y el
número que se promedia es el índice mismo. La conversión a puntaje es
la **identidad**, no una escala ausente (ADR-0108).

Por eso el cinturón no tiene anclas que calibrar contra el período: su
ancla es una fecha fija, el arranque del mandato, así que no hay cortes
donde colar una calibración (ADR-0123).

## Qué mide cada indicador

### Dimensión `ingresos` (28%)

#### Salario real vs. canasta

`brecha_salario_cbt`

| | |
|---|---|
| Peso dentro de la dimensión | 61% |
| Peso efectivo en el índice | **17.1%** |
| Procedencia del ancla | `conceptual` — rebase base-100 a la fecha fija 4T-2023 (RIPTE/CBT), no al rango observado (ADR-0123) |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

#### Pobreza (estimación mensual)

`pobreza_nowcast`

| | |
|---|---|
| Peso dentro de la dimensión | 33% |
| Peso efectivo en el índice | **9.3%** |
| Procedencia del ancla | `conceptual` — rebase base-100 al 2º semestre de 2023, invertido (ADR-0153). La base sale de la serie oficial del INDEC porque el nowcast mensual no llega al 4T-2023; el desvío del empalme está medido y declarado en la ficha |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0113](../adr/0113-nowcast-de-pobreza.md) La pobreza se publica, con la única fuente mensual que existe · [ADR-0114](../adr/0114-pobreza-oficial-acompana-al-nowcast.md) La pobreza oficial acompaña al nowcast en el mismo gráfico

#### Consumo de carne vacuna per cápita

`consumo_carne`

| | |
|---|---|
| Peso dentro de la dimensión | 4% |
| Peso efectivo en el índice | **1.1%** |
| Procedencia del ancla | `conceptual` — consumo per cápita rebaseado a 4T-2023; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0119](../adr/0119-pendientes-de-baja-prioridad-vida.md) Los tres pendientes de baja prioridad del cinturón de vida

#### Patentamiento de motos

`patentamiento_motos`

| | |
|---|---|
| Peso dentro de la dimensión | 2% |
| Peso efectivo en el índice | **0.6%** |
| Procedencia del ancla | `conceptual` — móvil 12m rebaseado a 4T-2023 (ADR-0024); el tope conceptual de 140 le recorta el boom, no lo calibra |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

### Dimensión `precios` (25%)

#### Inflación de alimentos

`ipc_alimentos`

| | |
|---|---|
| Peso dentro de la dimensión | 35% |
| Peso efectivo en el índice | **8.8%** |
| Procedencia del ancla | `conceptual` — encarecimiento relativo rebaseado a 4T-2023 (ADR-0033); ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0033](../adr/0033-itvc-doble-conteo-y-winsorizacion.md) ITVC: doble conteo salario/comida eliminado y winsorización asimétrica

#### Peso de tarifas (regulados)

`peso_tarifas`

| | |
|---|---|
| Peso dentro de la dimensión | 45% |
| Peso efectivo en el índice | **11.2%** |
| Procedencia del ancla | `conceptual` — nivel de regulados vs salario rebaseado a 4T-2023; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

#### Costo real del alquiler

`alquiler_real`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.0%** |
| Procedencia del ancla | `conceptual` — encarecimiento relativo del alquiler rebaseado a 4T-2023 (ADR-0111) |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0111](../adr/0111-alquiler-real-entra-al-itvc.md) El costo del alquiler entra al cinturón; pobreza y expectativas no

### Dimensión `vulnerabilidad` (10%)

#### Mora de las familias

`mora_familias`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **10.0%** |
| Procedencia del ancla | `conceptual` — nivel B100 vs 4T-2023, invertido (ADR-0067); ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0067](../adr/0067-mora-familias-indicador-propio.md) la mora de las familias sale del compuesto de endeudamiento y puntúa como indicador propio del ITVC

### Dimensión `empleo` (24%)

#### Informalidad laboral

`informalidad`

| | |
|---|---|
| Peso dentro de la dimensión | 38% |
| Peso efectivo en el índice | **9.2%** |
| Procedencia del ancla | `conceptual` — rebase base-100 a 4T-2023, invertido; ancla en la fecha fija (ADR-0123) |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0214](../adr/0214-la-informalidad-es-una-condicion-del-empleo.md) La informalidad es una condición del empleo, no del ingreso

#### Empleo registrado privado

`empleo_registrado`

| | |
|---|---|
| Peso dentro de la dimensión | 25% |
| Peso efectivo en el índice | **6.0%** |
| Procedencia del ancla | `conceptual` — asalariados privados registrados (SIPA) rebaseados a 4T-2023, sin invertir (ADR-0130); ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0130](../adr/0130-la-dimension-empleo-pasa-a-medir-empleo.md) La dimensión de empleo pasa a medir empleo

#### Actividad industrial (IPI)

`mortalidad_pymes`

| | |
|---|---|
| Peso dentro de la dimensión | 16% |
| Peso efectivo en el índice | **4.0%** |
| Procedencia del ancla | `conceptual` — nivel del IPI desestacionalizado rebaseado a 4T-2023; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

#### Construcción (ISAC)

`despacho_cemento`

| | |
|---|---|
| Peso dentro de la dimensión | 15% |
| Peso efectivo en el índice | **3.6%** |
| Procedencia del ancla | `conceptual` — nivel del ISAC desestacionalizado rebaseado a 4T-2023; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

#### Subocupación demandante

`pluriempleo`

| | |
|---|---|
| Peso dentro de la dimensión | 6% |
| Peso efectivo en el índice | **1.4%** |
| Procedencia del ancla | `conceptual` — subocupación demandante rebaseada a 4T-2023, invertida; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

### Dimensión `percepcion` (8%)

#### Confianza del consumidor (ICC)

`icc_utdt`

| | |
|---|---|
| Peso dentro de la dimensión | 82% |
| Peso efectivo en el índice | **6.8%** |
| Procedencia del ancla | `conceptual` — ICC rebaseado a 4T-2023; ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0018).

#### Sentimiento digital (Trends)

`sentimiento_digital`

| | |
|---|---|
| Peso dentro de la dimensión | 18% |
| Peso efectivo en el índice | **1.5%** |
| Procedencia del ancla | `conceptual` — canasta de búsquedas rebaseada a 4T-2023, invertida (ADR-0034); ancla en fecha fija |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0034](../adr/0034-sentimiento-digital-puntuable.md) Sentimiento digital: de contexto a componente del ITVC

### Dimensión `seguridad` (4%)

#### Victimización (IVI)

`inseguridad`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **4.5%** |
| Procedencia del ancla | `conceptual` — IVI rebaseado a su base declarada ene-2024 (ADR-0032), también fecha fija, no rango observado |

**Escala**: sin bandas — ver «Cómo puntúa este cinturón» arriba.

**Lo gobiernan**: [ADR-0032](../adr/0032-inseguridad-ivi-mensual.md) Inseguridad: del SNIC anual al IVI mensual (LICIP-UTDT)

## Se releva y no puntúa

Estos indicadores se siguen scrapeando y cacheando, pero están fuera
del índice y fuera del tablero. Sus bandas quedan como referencia
histórica.

- `endeudamiento_familiar` — Endeudamiento de consumo
- `indice_lider` — Índice líder (anticipa el ciclo)

## Decisiones abiertas

6 ADR vigentes de este cinturón declaran algo pendiente de decisión editorial. No son trabajo técnico: son llamadas que sólo puede hacer el editor.

> La detección lee la prosa, así que **sobre-reporta a propósito**: si un ADR anota un pendiente y lo resuelve unos párrafos más abajo, sigue apareciendo acá. Se prefiere ese error al contrario —perder una decisión realmente abierta—. La marca ⚠️ sí es firme: sale de las relaciones declaradas entre ADR, no de adivinar sobre el texto.

- **[ADR-0110](../adr/0110-percepcion-seguridad-y-consumo.md)** — La dimensión se llama por lo que tiene adentro
  <br>**Queda abierta como decisión editorial**, con el costo ya medido para que se
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0115. Verificar antes de tratarlo como abierto.
- **[ADR-0111](../adr/0111-alquiler-real-entra-al-itvc.md)** — El costo del alquiler entra al cinturón; pobreza y expectativas no
  <br>**Queda como candidata a card de contexto**, donde su carga simbólica se publica
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0112, ADR-0113. Verificar antes de tratarlo como abierto.
- **[ADR-0154](../adr/0154-endeudamiento-e-indice-lider-salen-del-itvc.md)** — Endeudamiento e Índice Líder salen del ITVC; el líder pasa a validar el ITCM
  <br>Queda anotado como pendiente editorial: si el criterio del proyecto para elegir
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0167. Verificar antes de tratarlo como abierto.
- **[ADR-0155](../adr/0155-el-ancla-del-itvc-pasa-a-ser-el-consumo-medido.md)** — El ancla de validación del ITVC pasa a ser el consumo medido
  <br>lo que prohíbe ADR-0045. Lo que sí falta —y se anota como pendiente editorial— es
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0160. Verificar antes de tratarlo como abierto.
- **[ADR-0160](../adr/0160-la-dispersion-del-itvc-se-publica-junto-al-neto.md)** — La dispersión del ITVC se publica junto al neto
  <br>- Queda como pendiente editorial si la dispersión merece su propio gráfico: hoy
- **[ADR-0206](../adr/0206-los-dos-artefactos-publicados-dicen-lo-mismo.md)** — Los dos artefactos publicados dicen lo mismo
  <br>fondo y queda pendiente: `_scoring_vida_itvc` arrastra `_itvc_indices`, el

## Todos los ADR vigentes de este cinturón

28 en total. El índice completo, con los superados y rechazados, está en [docs/adr/README.md](../adr/README.md).

- [0018](../adr/0018-itvc-parametrica-vida-cotidiana.md) — ITVC-B100: paramétrica base 100 del cinturón de Vida Cotidiana
- [0024](../adr/0024-motos-movil-12m-estacionalidad.md) — Motos por acumulado móvil de 12 meses (auditoría de estacionalidad)
- [0032](../adr/0032-inseguridad-ivi-mensual.md) — Inseguridad: del SNIC anual al IVI mensual (LICIP-UTDT)
- [0033](../adr/0033-itvc-doble-conteo-y-winsorizacion.md) — ITVC: doble conteo salario/comida eliminado y winsorización asimétrica
- [0034](../adr/0034-sentimiento-digital-puntuable.md) — Sentimiento digital: de contexto a componente del ITVC
- [0067](../adr/0067-mora-familias-indicador-propio.md) — la mora de las familias sale del compuesto de endeudamiento y puntúa como indicador propio del ITVC
- [0107](../adr/0107-vintages-del-itvc.md) — El cinturón de vida cotidiana declara de cuándo es cada dato
- [0108](../adr/0108-redundancia-interna-del-itvc.md) — La redundancia interna se mide también en el ITVC
- [0109](../adr/0109-saturacion-de-la-escala-de-tension.md) — Saturación de la escala de tensión: verificada, no requiere cambio
- [0110](../adr/0110-percepcion-seguridad-y-consumo.md) — La dimensión se llama por lo que tiene adentro
- [0111](../adr/0111-alquiler-real-entra-al-itvc.md) — El costo del alquiler entra al cinturón; pobreza y expectativas no
- [0112](../adr/0112-el-cinturon-mira-hacia-adelante.md) — El cinturón incorpora su primera medida prospectiva
- [0113](../adr/0113-nowcast-de-pobreza.md) — La pobreza se publica, con la única fuente mensual que existe
- [0114](../adr/0114-pobreza-oficial-acompana-al-nowcast.md) — La pobreza oficial acompaña al nowcast en el mismo gráfico
- [0115](../adr/0115-reorganizacion-de-la-dimension-de-percepcion.md) — La dimensión de percepción se parte en tres
- [0116](../adr/0116-la-robustez-del-itvc-estaba-vieja.md) — La sección de robustez del ITVC estaba vieja, y ahora avisa
- [0118](../adr/0118-el-indice-y-la-tension-son-dos-escalas.md) — El índice y la tensión son dos escalas, y ahora se dice dónde
- [0119](../adr/0119-pendientes-de-baja-prioridad-vida.md) — Los tres pendientes de baja prioridad del cinturón de vida
- [0123](../adr/0123-el-itvc-entra-al-registro-de-circularidad.md) — El ITVC entra al registro de circularidad (0%, y por qué)
- [0130](../adr/0130-la-dimension-empleo-pasa-a-medir-empleo.md) — La dimensión de empleo pasa a medir empleo
- [0153](../adr/0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto.md) — La pobreza entra al ITVC, y la categoría «card de contexto» queda cerrada
- [0154](../adr/0154-endeudamiento-e-indice-lider-salen-del-itvc.md) — Endeudamiento e Índice Líder salen del ITVC; el líder pasa a validar el ITCM
- [0155](../adr/0155-el-ancla-del-itvc-pasa-a-ser-el-consumo-medido.md) — El ancla de validación del ITVC pasa a ser el consumo medido
- [0160](../adr/0160-la-dispersion-del-itvc-se-publica-junto-al-neto.md) — La dispersión del ITVC se publica junto al neto
- [0163](../adr/0163-el-itvc-se-contrasta-contra-volumenes-fisicos-del-hogar.md) — El ITVC se contrasta contra volúmenes físicos consumidos por los hogares
- [0206](../adr/0206-los-dos-artefactos-publicados-dicen-lo-mismo.md) — Los dos artefactos publicados dicen lo mismo
- [0208](../adr/0208-el-itvc-vive-en-su-modulo-y-el-intermedio-nace-bien.md) — El ITVC vive en su módulo, y el intermedio nace bien
- [0214](../adr/0214-la-informalidad-es-una-condicion-del-empleo.md) — La informalidad es una condición del empleo, no del ingreso
