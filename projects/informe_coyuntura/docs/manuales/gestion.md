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
| `reforma_estado` | 25% | `reduccion_estado`, `gasto_funcionamiento`, `masa_salarial`, `reestructuracion_organismos` |
| `reforma_laboral` | 15% | `fal_modernizacion_laboral`, `litigiosidad_laboral` |
| `privatizaciones_inversion` | 15% | `privatizaciones`, `rigi_inversiones`, `concesiones_infraestructura` |
| `social_orden` | 10% | `protocolo_antipiquetes`, `libertad_opcion_salud` |

Suma de pesos: 100%.

## Qué mide cada indicador

### Dimensión `reformas_economicas` (35%)

#### Brecha cambiaria (cepo)

`cepo_mulc`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **14.0%** |
| Procedencia del ancla | `documento` — «brecha sostenida <10-15% = condiciones óptimas de unificación» (doc 260702) |

**Bandas**: ≤ 5 → 100 · 5–10 → 85 · 10–15 → 65 · 15–25 → 40 · > 25 → 10

**Lo gobiernan**: [ADR-0006](../adr/0006-brecha-cambiaria-ccl-mayorista.md) La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista

#### Apertura comercial (alícuota)

`apertura_comercial`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **14.0%** |
| Procedencia del ancla | `documento` — anclas sobre la lineal del documento: 0% → 100 · 15% → 0 (ADR-0021) |

**Bandas**: ≤ 1 → 100 · 1–3.5 → 85 · 3.5–7 → 65 · 7–11 → 40 · > 11 → 10

**Lo gobiernan**: [ADR-0021](../adr/0021-interpolacion-y-apertura-sin-brecha.md) Puntaje interpolado en ITCM/ITCG y apertura comercial sin brecha

#### Desregulación normativa

`desregulacion_normativa`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **7.0%** |
| Procedencia del ancla | `convencion` — la meta de 100 normas = plan completo es convención propia, declarada en ADR-0096 |

**Bandas**: > 30000 → 100 · 15000–30000 → 85 · 7000–15000 → 60 · 2500–7000 → 35 · ≤ 2500 → 10

**Lo gobiernan**: [ADR-0096](../adr/0096-desregulacion-cuenta-normas-no-menciones.md) Desregulación: contar normas derogadas, no menciones de una palabra · [ADR-0125](../adr/0125-la-desregulacion-pasa-a-la-fuente-oficial.md) La desregulación pasa a medirse con la fuente oficial · [ADR-0143](../adr/0143-la-desregulacion-se-mide-en-articulos.md) La desregulación se mide en artículos, no en normas

### Dimensión `reforma_estado` (25%)

#### Dotación del Estado (APN)

`reduccion_estado`

| | |
|---|---|
| Peso dentro de la dimensión | 35% |
| Peso efectivo en el índice | **8.8%** |
| Procedencia del ancla | `convencion` — «calibrado con el dato real»: el recorte observado de ~10-12% define la banda 85 |

**Bandas**: ≤ -12 → 100 · -12–-8 → 85 · -8–-4 → 65 · -4–0 → 40 · > 0 → 10

**Lo gobiernan**: [ADR-0097](../adr/0097-que-universo-mide-la-dotacion-del-estado.md) Qué universo mide la dotación del Estado · [ADR-0128](../adr/0128-fuerzas-en-la-dotacion-y-peso-del-fal.md) Las fuerzas están en la dotación, y el FAL baja a la mitad de su dimensión

#### Gasto de funcionamiento

`gasto_funcionamiento`

| | |
|---|---|
| Peso dentro de la dimensión | 25% |
| Peso efectivo en el índice | **6.2%** |
| Procedencia del ancla | `convencion` — bandas anchas por el ajuste de 2024, que la propia ficha llama históricamente atípico |

**Bandas**: ≤ -25 → 100 · -25–-15 → 85 · -15–-5 → 65 · -5–0 → 40 · > 0 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0013).

#### Masa salarial pública

`masa_salarial`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.0%** |
| Procedencia del ancla | `convencion` — gemela de gasto_funcionamiento: los cortes son grados de recorte fijados contra el ajuste 2024, sin serie previa (ADR-0121) |

**Bandas**: ≤ -20 → 100 · -20–-12 → 85 · -12–-5 → 65 · -5–0 → 40 · > 0 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0013).

#### Reestructuración de organismos

`reestructuracion_organismos`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **5.0%** |
| Procedencia del ancla | `conceptual` — medidor de avance 0-100 hacia el plan de disoluciones/fusiones; el 100 es el ancla, no el rango observado (ADR-0121) |

**Bandas**: > 80 → 100 · 60–80 → 85 · 40–60 → 65 · 20–40 → 40 · ≤ 20 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0013).

### Dimensión `reforma_laboral` (15%)

#### Fondo de Asistencia Laboral

`fal_modernizacion_laboral`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **7.5%** |
| Procedencia del ancla | `conceptual` — cortes sobre los estados que la escala puede tomar, no sobre el rango observado (ADR-0098) |

**Bandas**: > 75 → 100 · 25–75 → 50 · ≤ 25 → 10

**Lo gobiernan**: [ADR-0068](../adr/0068-fal-regimen-ley-27802.md) fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802 · [ADR-0098](../adr/0098-fal-en-tres-etapas.md) El FAL se mide en tres etapas: construcción, vigencia y adopción · [ADR-0142](../adr/0142-el-fal-mide-sus-dos-actos-fundamentales.md) El FAL mide sus dos actos fundamentales

#### Litigiosidad laboral (SRT)

`litigiosidad_laboral`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **7.5%** |
| Procedencia del ancla | `historia_larga` — calibrada sobre 2021-2026, que incluye dos gobiernos (ADR-0023) |

**Bandas**: ≤ -15 → 100 · -15–-5 → 85 · -5–5 → 65 · 5–20 → 40 · > 20 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0013).

### Dimensión `privatizaciones_inversion` (15%)

#### Privatizaciones (etapas)

`privatizaciones`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **6.0%** |
| Procedencia del ancla | `documento` — etapas 0-4 definidas en el documento de diseño |

**Bandas**: > 75 → 100 · 55–75 → 85 · 35–55 → 65 · 15–35 → 40 · ≤ 15 → 10

**Lo gobiernan**: [ADR-0101](../adr/0101-privatizaciones-publica-la-norma-de-cada-etapa.md) Privatizaciones publica la norma que respalda cada etapa · [ADR-0129](../adr/0129-detector-de-novedades-de-privatizaciones.md) Privatizaciones: se automatiza la detección, no la clasificación

#### Inversiones RIGI

`rigi_inversiones`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **6.0%** |
| Procedencia del ancla | `convencion` — referencia el 22,1% de jun-2026 y la composición del pipeline de ese momento |

**Bandas**: > 60 → 100 · 40–60 → 85 · 25–40 → 65 · 10–25 → 40 · ≤ 10 → 10

**Lo gobiernan**: [ADR-0086](../adr/0086-serie-y-banda-tienen-que-medir-lo-mismo.md) La serie de un indicador tiene que medir lo mismo que puntúa su banda · [ADR-0102](../adr/0102-rigi-denominador-movil.md) El RIGI avisa cuando su porcentaje baja por el denominador

#### Concesiones viales

`concesiones_infraestructura`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **3.0%** |
| Procedencia del ancla | `conceptual` — tasa de adjudicación km/plan; el 100 (plan adjudicado) es el ancla (ADR-0121) |

**Bandas**: > 75 → 100 · 55–75 → 85 · 35–55 → 65 · 15–35 → 40 · ≤ 15 → 10

**Lo gobiernan**: [ADR-0087](../adr/0087-preadjudicado-no-es-adjudicado.md) "Preadjudicado" contiene "Adjudicado"

### Dimensión `social_orden` (10%)

#### Orden público (piquetes)

`protocolo_antipiquetes`

| | |
|---|---|
| Peso dentro de la dimensión | 67% |
| Peso efectivo en el índice | **6.7%** |
| Procedencia del ancla | `convencion` — calibrada con la caída observada en CABA en 2024-2025 |

**Bandas**: > 75 → 100 · 50–75 → 85 · 25–50 → 65 · 0–25 → 40 · ≤ 0 → 10

**Lo gobiernan**: [ADR-0025](../adr/0025-protocolo-diagnostico-politico.md) Protocolo antipiquetes automatizado con Diagnóstico Político (y corrección 55 → 74,2)

#### Libertad de opción en salud

`libertad_opcion_salud`

| | |
|---|---|
| Peso dentro de la dimensión | 33% |
| Peso efectivo en el índice | **3.3%** |
| Procedencia del ancla | `conceptual` — % de usuarios con libre opción; el 100 (libre opción plena) es el ancla (ADR-0121) |

**Bandas**: > 70 → 100 · 50–70 → 85 · 30–50 → 65 · 10–30 → 40 · ≤ 10 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0013).

## Se releva y no puntúa

Estos indicadores se siguen scrapeando y cacheando, pero están fuera
del índice y fuera del tablero. Sus bandas quedan como referencia
histórica.

- `alertas_manifestacion` — Alertas de manifestación (GCBA) (declarado como contexto)
- `asistencia_directa` — Asistencia directa (TDPS)
- `protestas_caba` — Protestas en CABA (ACLED) (declarado como contexto)

## Decisiones abiertas

1 ADR vigentes de este cinturón declaran algo pendiente de decisión editorial. No son trabajo técnico: son llamadas que sólo puede hacer el editor.

- **[ADR-0068](../adr/0068-fal-regimen-ley-27802.md)** — fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802
  <br>- Queda pendiente (mejor fuente): serie del MTEySS de convenios homologados
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0098. Verificar antes de tratarlo como abierto.

## Todos los ADR vigentes de este cinturón

26 en total. El índice completo, con los superados y rechazados, está en [docs/adr/README.md](../adr/README.md).

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
- [0142](../adr/0142-el-fal-mide-sus-dos-actos-fundamentales.md) — El FAL mide sus dos actos fundamentales
- [0143](../adr/0143-la-desregulacion-se-mide-en-articulos.md) — La desregulación se mide en artículos, no en normas
- [0164](../adr/0164-familia-del-itcg-la-respuesta-del-capital-privado.md) — Familia del ITCG: la respuesta del capital privado
