# Manual metodológico — cinturón Gestión (ITCG)

> **Generado** por `scripts/manual_cinturon.py` desde el código que corre
> (`scripts/itcg.py`) y el frontmatter de los ADR. No editar a mano.
>
> Dice el **método**, no el valor: los números los deriva el pipeline
> (ADR-0156), así que este documento no caduca cuando cambia el dato.

Los ADR responden *por qué* se decidió cada cosa y *cuándo*. Este manual
responde *qué rige hoy*. Para la historia de una decisión, seguí el link
al ADR.

## Dimensiones y pesos

| Dimensión | Peso | Indicadores |
|---|---:|---|
| `reformas_economicas` | 35% | `cepo_mulc`, `apertura_comercial`, `desregulacion_normativa` |
| `reforma_estado` | 25% | `reduccion_estado`, `gasto_funcionamiento` |
| `reforma_laboral` | 15% | `fal_modernizacion_laboral`, `juicios_trabajo_capital` |
| `privatizaciones_inversion` | 15% | `privatizaciones`, `rigi_inversiones`, `concesiones_infraestructura` |
| `social_orden` | 10% | `asistencia_directa`, `protocolo_antipiquetes`, `libertad_opcion_salud` |

Suma de pesos: 100%.

## Qué mide cada indicador

### Dimensión `reformas_economicas` (35%)

#### Brecha cambiaria

`cepo_mulc`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **14.0%** |
| Procedencia del ancla | `documento` — «brecha sostenida <10-15% = condiciones óptimas de unificación» (doc 260702) |

**Bandas**: ≤ 5 → 100 · 5–10 → 85 · 10–15 → 65 · 15–25 → 40 · > 25 → 10

**Lo gobiernan**: [ADR-0006](../adr/0006-brecha-cambiaria-ccl-mayorista.md) La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista · [ADR-0280](../adr/0280-la-brecha-conserva-la-fecha-de-cotizacion.md) La brecha conserva la fecha de cotización · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

#### Impuestos sobre el comercio exterior

`apertura_comercial`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **14.0%** |
| Procedencia del ancla | `documento` — anclas sobre la lineal del documento: 0% → 100 · 15% → 0 (ADR-0021) |

**Bandas**: ≤ 1 → 100 · 1–3.5 → 85 · 3.5–7 → 65 · 7–11 → 40 · > 11 → 10

**Lo gobiernan**: [ADR-0021](../adr/0021-interpolacion-y-apertura-sin-brecha.md) Puntaje interpolado en ITCM/ITCG y apertura comercial sin brecha · [ADR-0282](../adr/0282-apertura-usa-el-ica-original-y-explicita-estadistica.md) Apertura usa el ICA original y explicita estadística

#### Desregulación normativa

`desregulacion_normativa`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **7.0%** |
| Procedencia del ancla | `convencion` — el conteo pasa a ser OFICIAL (informe mensual del Min. de Desregulación) pero la vara NO: el organismo no publica meta, así que los cortes 100/300/600/1200 los ponemos nosotros — misma limitación que declaraba ADR-0096, con otra fuente para el número (ADR-0125) |

**Bandas**: > 30000 → 100 · 15000–30000 → 85 · 7000–15000 → 60 · 2500–7000 → 35 · ≤ 2500 → 10

**Lo gobiernan**: [ADR-0096](../adr/0096-desregulacion-cuenta-normas-no-menciones.md) Desregulación: contar normas derogadas, no menciones de una palabra · [ADR-0125](../adr/0125-la-desregulacion-pasa-a-la-fuente-oficial.md) La desregulación pasa a medirse con la fuente oficial · [ADR-0143](../adr/0143-la-desregulacion-se-mide-en-articulos.md) La desregulación se mide en artículos, no en normas · [ADR-0229](../adr/0229-la-desregulacion-cuenta-actos-no-efectos.md) La desregulación cuenta actos, no efectos, y la ficha lo dice · [ADR-0269](../adr/0269-la-semilla-a-mano-no-le-gana-al-ultimo-valor-bueno.md) La semilla escrita a mano no le gana al último valor bueno · [ADR-0292](../adr/0292-desregulacion-incorpora-revisiones-mensuales.md) Desregulación incorpora las revisiones mensuales · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026) · [ADR-0363](../adr/0363-desregulacion-suma-la-clasificacion-por-sector-del-ministerio.md) Desregulación suma la clasificación por sector del Ministerio

### Dimensión `reforma_estado` (25%)

#### Empleados de la administración nacional

`reduccion_estado`

| | |
|---|---|
| Peso dentro de la dimensión | 58% |
| Peso efectivo en el índice | **14.6%** |
| Procedencia del ancla | `externa` — meta del Gobierno de recortar otro 10% de la planta en 2026, informada por la prensa citando fuentes oficiales (sin número publicado): −25,7% vs dic-2023 = 100 (ADR-0364). Antes, convención calibrada con el recorte observado |

**Bandas**: ≤ -25.7 → 100 · -25.7–-17.1 → 85 · -17.1–-8.6 → 65 · -8.6–0 → 40 · > 0 → 10

**Lo gobiernan**: [ADR-0097](../adr/0097-que-universo-mide-la-dotacion-del-estado.md) Qué universo mide la dotación del Estado · [ADR-0128](../adr/0128-fuerzas-en-la-dotacion-y-peso-del-fal.md) Las fuerzas están en la dotación, y el FAL baja a la mitad de su dimensión · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026) · [ADR-0364](../adr/0364-la-dotacion-del-estado-se-mide-contra-la-meta-de-2026.md) La dotación del Estado se mide contra la meta de 2026

#### Gasto de funcionamiento

`gasto_funcionamiento`

| | |
|---|---|
| Peso dentro de la dimensión | 42% |
| Peso efectivo en el índice | **10.4%** |
| Procedencia del ancla | `convencion` — bandas anchas por el ajuste de 2024, que la propia ficha llama históricamente atípico |

**Bandas**: ≤ -25 → 100 · -25–-15 → 85 · -15–-5 → 65 · -5–0 → 40 · > 0 → 10

**Lo gobiernan**: [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

### Dimensión `reforma_laboral` (15%)

#### Fondo de Asistencia Laboral

`fal_modernizacion_laboral`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **7.5%** |
| Procedencia del ancla | `conceptual` — cortes sobre los estados que la escala puede tomar, no sobre el rango observado (ADR-0098) |

**Bandas**: > 90 → 100 · 62.5–90 → 80 · 37.5–62.5 → 55 · 10–37.5 → 30 · ≤ 10 → 10

**Lo gobiernan**: [ADR-0068](../adr/0068-fal-regimen-ley-27802.md) fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802 · [ADR-0098](../adr/0098-fal-en-tres-etapas.md) El FAL se mide en tres etapas: construcción, vigencia y adopción · [ADR-0228](../adr/0228-el-fal-puntua-lo-que-rige-no-lo-que-se-dicto.md) El FAL puntúa lo que rige, no lo que se dictó · [ADR-0269](../adr/0269-la-semilla-a-mano-no-le-gana-al-ultimo-valor-bueno.md) La semilla escrita a mano no le gana al último valor bueno · [ADR-0305](../adr/0305-fal-separa-consulta-y-revision-curada.md) Consultar CNV no actualiza la revisión judicial · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026) · [ADR-0370](../adr/0370-el-fal-cuenta-cinco-hitos-de-construccion.md) El FAL cuenta cinco hitos de construcción

#### Juicios en la Justicia del Trabajo (Capital)

`juicios_trabajo_capital`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **7.5%** |
| Procedencia del ancla | `convencion` — toma la escala de litigiosidad_laboral, que es la misma cuenta sobre otro universo; su serie arranca en 2023 y no alcanza para calibrar una propia (ADR-0365) |

**Bandas**: ≤ -15 → 100 · -15–-5 → 85 · -5–5 → 65 · 5–20 → 40 · > 20 → 10

**Lo gobiernan**: [ADR-0365](../adr/0365-los-juicios-de-la-justicia-del-trabajo-entran-a-la-reforma-laboral.md) Los juicios de la Justicia del Trabajo entran a la reforma laboral · [ADR-0369](../adr/0369-los-juicios-por-riesgos-del-trabajo-salen-de-la-reforma-laboral.md) Los juicios por riesgos del trabajo salen de la reforma laboral

### Dimensión `privatizaciones_inversion` (15%)

#### Privatizaciones (etapas)

`privatizaciones`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **6.0%** |
| Procedencia del ancla | `documento` — etapas 0-4 definidas en el documento de diseño |

**Bandas**: > 75 → 100 · 55–75 → 85 · 35–55 → 65 · 15–35 → 40 · ≤ 15 → 10

**Lo gobiernan**: [ADR-0101](../adr/0101-privatizaciones-publica-la-norma-de-cada-etapa.md) Privatizaciones publica la norma que respalda cada etapa · [ADR-0129](../adr/0129-detector-de-novedades-de-privatizaciones.md) Privatizaciones: se automatiza la detección, no la clasificación · [ADR-0277](../adr/0277-novedades-verifican-empresa-y-reintentan-textos-vacios.md) El detector verifica la empresa y reintenta lecturas vacías

#### Grandes inversiones aprobadas

`rigi_inversiones`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **6.0%** |
| Procedencia del ancla | `convencion` — referencia el 22,1% de jun-2026 y la composición del pipeline de ese momento |

**Bandas**: > 60 → 100 · 40–60 → 85 · 25–40 → 65 · 10–25 → 40 · ≤ 10 → 10

**Lo gobiernan**: [ADR-0086](../adr/0086-serie-y-banda-tienen-que-medir-lo-mismo.md) La serie de un indicador tiene que medir lo mismo que puntúa su banda · [ADR-0102](../adr/0102-rigi-denominador-movil.md) El RIGI avisa cuando su porcentaje baja por el denominador · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

#### Concesiones viales

`concesiones_infraestructura`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **3.0%** |
| Procedencia del ancla | `conceptual` — tasa de adjudicación km/plan; el 100 (plan adjudicado) es el ancla (ADR-0121) |

**Bandas**: > 75 → 100 · 55–75 → 85 · 35–55 → 65 · 15–35 → 40 · ≤ 15 → 10

**Lo gobiernan**: [ADR-0087](../adr/0087-preadjudicado-no-es-adjudicado.md) "Preadjudicado" contiene "Adjudicado" · [ADR-0244](../adr/0244-el-acto-juridico-manda-sobre-el-estado-del-portal.md) El acto jurídico manda sobre el estado del portal · [ADR-0269](../adr/0269-la-semilla-a-mano-no-le-gana-al-ultimo-valor-bueno.md) La semilla escrita a mano no le gana al último valor bueno · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

### Dimensión `social_orden` (10%)

#### Planes sin intermediarios

`asistencia_directa`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **4.0%** |
| Procedencia del ancla | `conceptual` — hito binario: 100 desde el cese de las unidades de gestión (Res. 84/2024), 0 antes; las bandas sólo se usan en sus extremos (ADR-0362) |

**Bandas**: > 95 → 100 · 85–95 → 85 · 60–85 → 65 · 30–60 → 40 · ≤ 30 → 10

**Lo gobiernan**: [ADR-0100](../adr/0100-promesa-cumplida-no-es-contexto.md) Una promesa cumplida no es un indicador de contexto · [ADR-0189](../adr/0189-si-no-puntua-no-se-muestra.md) Si no puntúa no se muestra, y una promesa cumplida sí puntúa · [ADR-0296](../adr/0296-tdps-distingue-devengado-de-pago.md) TDPS distingue devengado de pago · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026) · [ADR-0362](../adr/0362-planes-sin-intermediarios-mide-el-cese-de-las-unidades-de-gestion.md) «Planes sin intermediarios» mide el cese de las unidades de gestión

#### Reducción de cortes de calle en la Ciudad

`protocolo_antipiquetes`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **4.0%** |
| Procedencia del ancla | `convencion` — calibrada con la caída observada en CABA en 2024-2025 |

**Bandas**: > 75 → 100 · 50–75 → 85 · 25–50 → 65 · 0–25 → 40 · ≤ 0 → 10

**Lo gobiernan**: [ADR-0025](../adr/0025-protocolo-diagnostico-politico.md) Protocolo antipiquetes automatizado con Diagnóstico Político (y corrección 55 → 74,2) · [ADR-0294](../adr/0294-cortes-explicita-base-estimada-y-fuente-no-verificable.md) Cortes explicita base estimada y fuente no verificable · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

#### Implementación de la libre elección de cobertura de salud

`libertad_opcion_salud`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **2.0%** |
| Procedencia del ancla | `conceptual` — % de usuarios con libre opción; el 100 (libre opción plena) es el ancla (ADR-0121) |

**Bandas**: > 95 → 100 · 75–95 → 85 · 55–75 → 65 · 35–55 → 40 · ≤ 35 → 10

**Lo gobiernan**: [ADR-0278](../adr/0278-salud-descubre-los-padrones-referenciados.md) Salud descubre los padrones referenciados por el portal · [ADR-0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026) · [ADR-0371](../adr/0371-la-libre-eleccion-en-salud-se-mide-por-hitos.md) La libre elección en salud se mide por hitos

## Se releva y no puntúa

Estos indicadores se siguen scrapeando y cacheando, pero están fuera
del índice y fuera del tablero. Sus bandas quedan como referencia
histórica.

- `alertas_manifestacion` — Alertas de manifestación (GCBA) (declarado como contexto)
- `litigiosidad_laboral` — Juicios por riesgos del trabajo (SRT)
- `masa_salarial` — Masa salarial pública
- `protestas_caba` — Protestas en CABA (ACLED) (declarado como contexto)
- `reestructuracion_organismos` — Reestructuración de organismos

## Decisiones abiertas

2 ADR vigentes de este cinturón declaran algo pendiente de decisión editorial. No son trabajo técnico: son llamadas que sólo puede hacer el editor.

> La detección lee la prosa, así que **sobre-reporta a propósito**: si un ADR anota un pendiente y lo resuelve unos párrafos más abajo, sigue apareciendo acá. Se prefiere ese error al contrario —perder una decisión realmente abierta—. La marca ⚠️ sí es firme: sale de las relaciones declaradas entre ADR, no de adivinar sobre el texto.

- **[ADR-0068](../adr/0068-fal-regimen-ley-27802.md)** — fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802
  <br>- Queda pendiente (mejor fuente): serie del MTEySS de convenios homologados
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0098. Verificar antes de tratarlo como abierto.
- **[ADR-0305](../adr/0305-fal-separa-consulta-y-revision-curada.md)** — Consultar CNV no actualiza la revisión judicial
  <br>valor y pesos; queda pendiente cerrar el expediente judicial y definir una

## Todos los ADR vigentes de este cinturón

53 en total. El índice completo, con los superados y rechazados, está en [docs/adr/README.md](../adr/README.md).

- [0006](../adr/0006-brecha-cambiaria-ccl-mayorista.md) — La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista
- [0011](../adr/0011-rigi-plataforma-oficial.md) — El RIGI se mide desde la plataforma oficial (inversión aprobada/pipeline), no por conteo de normas
- [0014](../adr/0014-piquetes-poller-gtfs-rt.md) — Piquetes: poller GTFS-RT acumulativo (el registro de cortes del GCBA está muerto)
- [0015](../adr/0015-tdps-presupuesto-abierto.md) — TDPS: la asistencia directa se verifica contra la ejecución presupuestaria (API Presupuesto Abierto)
- [0016](../adr/0016-concesiones-contratar-salud-sss.md) — Concesiones vía CONTRAT.AR + opción en salud vía padrones SSS (últimos manuales automatizados)
- [0019](../adr/0019-revision-metodologica-parametricas.md) — Revisión metodológica de las tres paramétricas (ITCM · ITCG · ITVC)
- [0021](../adr/0021-interpolacion-y-apertura-sin-brecha.md) — Puntaje interpolado en ITCM/ITCG y apertura comercial sin brecha
- [0023](../adr/0023-litigiosidad-al-itcg.md) — Litigiosidad SRT al ITCG; protestas y alertas siguen de contexto
- [0025](../adr/0025-protocolo-diagnostico-politico.md) — Protocolo antipiquetes automatizado con Diagnóstico Político (y corrección 55 → 74,2)
- [0031](../adr/0031-validacion-cruzada-tercer-pilar.md) — Tercer pilar de robustez: validación cruzada (matriz discriminante)
- [0051](../adr/0051-gestion-contexto-oculto.md) — Gestión: las cards de contexto salen del tablero (regla pareja en los 5 cinturones)
- [0068](../adr/0068-fal-regimen-ley-27802.md) — fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802
- [0086](../adr/0086-serie-y-banda-tienen-que-medir-lo-mismo.md) — La serie de un indicador tiene que medir lo mismo que puntúa su banda
- [0087](../adr/0087-preadjudicado-no-es-adjudicado.md) — "Preadjudicado" contiene "Adjudicado"
- [0096](../adr/0096-desregulacion-cuenta-normas-no-menciones.md) — Desregulación: contar normas derogadas, no menciones de una palabra
- [0097](../adr/0097-que-universo-mide-la-dotacion-del-estado.md) — Qué universo mide la dotación del Estado
- [0098](../adr/0098-fal-en-tres-etapas.md) — El FAL se mide en tres etapas: construcción, vigencia y adopción
- [0100](../adr/0100-promesa-cumplida-no-es-contexto.md) — Una promesa cumplida no es un indicador de contexto
- [0101](../adr/0101-privatizaciones-publica-la-norma-de-cada-etapa.md) — Privatizaciones publica la norma que respalda cada etapa
- [0102](../adr/0102-rigi-denominador-movil.md) — El RIGI avisa cuando su porcentaje baja por el denominador
- [0125](../adr/0125-la-desregulacion-pasa-a-la-fuente-oficial.md) — La desregulación pasa a medirse con la fuente oficial
- [0128](../adr/0128-fuerzas-en-la-dotacion-y-peso-del-fal.md) — Las fuerzas están en la dotación, y el FAL baja a la mitad de su dimensión
- [0129](../adr/0129-detector-de-novedades-de-privatizaciones.md) — Privatizaciones: se automatiza la detección, no la clasificación
- [0143](../adr/0143-la-desregulacion-se-mide-en-articulos.md) — La desregulación se mide en artículos, no en normas
- [0164](../adr/0164-familia-del-itcg-la-respuesta-del-capital-privado.md) — Familia del ITCG: la respuesta del capital privado
- [0185](../adr/0185-reestructuracion-organismos-habla-solo-de-disolucion-o-cierre.md) — `reestructuracion_organismos` habla solo de disolución o cierre
- [0186](../adr/0186-masa-salarial-sale-del-itcg.md) — `masa_salarial` sale del cálculo del ITCG
- [0188](../adr/0188-reestructuracion-organismos-numerador-caso-por-caso.md) — `reestructuracion_organismos`: el numerador cuenta solo cierres vigentes de organismos públicos, caso por caso
- [0189](../adr/0189-si-no-puntua-no-se-muestra.md) — Si no puntúa no se muestra, y una promesa cumplida sí puntúa
- [0221](../adr/0221-un-cable-trampa-mira-la-banda-no-el-puntaje.md) — Un cable trampa mira la banda, no el puntaje
- [0228](../adr/0228-el-fal-puntua-lo-que-rige-no-lo-que-se-dicto.md) — El FAL puntúa lo que rige, no lo que se dictó
- [0229](../adr/0229-la-desregulacion-cuenta-actos-no-efectos.md) — La desregulación cuenta actos, no efectos, y la ficha lo dice
- [0244](../adr/0244-el-acto-juridico-manda-sobre-el-estado-del-portal.md) — El acto jurídico manda sobre el estado del portal
- [0247](../adr/0247-un-porcentaje-entre-normas-y-una-meta-documental.md) — Un porcentaje entre normas y una meta documental
- [0269](../adr/0269-la-semilla-a-mano-no-le-gana-al-ultimo-valor-bueno.md) — La semilla escrita a mano no le gana al último valor bueno
- [0277](../adr/0277-novedades-verifican-empresa-y-reintentan-textos-vacios.md) — El detector verifica la empresa y reintenta lecturas vacías
- [0278](../adr/0278-salud-descubre-los-padrones-referenciados.md) — Salud descubre los padrones referenciados por el portal
- [0280](../adr/0280-la-brecha-conserva-la-fecha-de-cotizacion.md) — La brecha conserva la fecha de cotización
- [0282](../adr/0282-apertura-usa-el-ica-original-y-explicita-estadistica.md) — Apertura usa el ICA original y explicita estadística
- [0285](../adr/0285-litigiosidad-exige-ventanas-de-calendario.md) — Litigiosidad exige ventanas de calendario
- [0292](../adr/0292-desregulacion-incorpora-revisiones-mensuales.md) — Desregulación incorpora las revisiones mensuales
- [0294](../adr/0294-cortes-explicita-base-estimada-y-fuente-no-verificable.md) — Cortes explicita base estimada y fuente no verificable
- [0296](../adr/0296-tdps-distingue-devengado-de-pago.md) — TDPS distingue devengado de pago
- [0305](../adr/0305-fal-separa-consulta-y-revision-curada.md) — Consultar CNV no actualiza la revisión judicial
- [0336](../adr/0336-el-itcg-no-tiene-validacion-externa-por-definicion.md) — El ITCG no tiene validación externa, por definición
- [0361](../adr/0361-respuesta-a-la-auditoria-del-cinturon-de-gestion.md) — Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)
- [0362](../adr/0362-planes-sin-intermediarios-mide-el-cese-de-las-unidades-de-gestion.md) — «Planes sin intermediarios» mide el cese de las unidades de gestión
- [0363](../adr/0363-desregulacion-suma-la-clasificacion-por-sector-del-ministerio.md) — Desregulación suma la clasificación por sector del Ministerio
- [0364](../adr/0364-la-dotacion-del-estado-se-mide-contra-la-meta-de-2026.md) — La dotación del Estado se mide contra la meta de 2026
- [0365](../adr/0365-los-juicios-de-la-justicia-del-trabajo-entran-a-la-reforma-laboral.md) — Los juicios de la Justicia del Trabajo entran a la reforma laboral
- [0369](../adr/0369-los-juicios-por-riesgos-del-trabajo-salen-de-la-reforma-laboral.md) — Los juicios por riesgos del trabajo salen de la reforma laboral
- [0370](../adr/0370-el-fal-cuenta-cinco-hitos-de-construccion.md) — El FAL cuenta cinco hitos de construcción
- [0371](../adr/0371-la-libre-eleccion-en-salud-se-mide-por-hitos.md) — La libre elección en salud se mide por hitos
