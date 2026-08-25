# Manual metodológico — cinturón Política (ITCP)

> **Generado** por `scripts/manual_cinturon.py` desde el código que corre
> (`scripts/itcp.py`) y el frontmatter de los ADR. No editar a mano.
>
> Dice el **método**, no el valor: los números los deriva el pipeline
> (ADR-0156), así que este documento no caduca cuando cambia el dato.

Los ADR responden *por qué* se decidió cada cosa y *cuándo*. Este manual
responde *qué rige hoy*. Para la historia de una decisión, seguí el link
al ADR.

## Dimensiones y pesos

| Dimensión | Peso | Indicadores |
|---|---:|---|
| `poder_legislativo` | 21% | `ratio_dnu`, `eficacia_legislativa`, `veto_quorum`, `desafios_legislativos`, `bloqueo_sostenido`, `produccion_legislativa` |
| `alianzas_territoriales` | 19% | `iaf_transferencias`, `alineamiento_senadores_prov`, `adhesion_reformas_provincial` |
| `cohesion_interna` | 15% | `cohesion_bloque` |
| `conflicto_social` | 10% | `conflictividad_nacional`, `jornadas_individuales_no_trabajadas_12m` |
| `imagen_voto` | 7% | `votometro_ventaja_lla` |
| `poder_judicial` | 15% | `cobertura_judicial`, `velocidad_resolucion`, `paralisis_denuncias` |
| `sector_privado` | 13% | `brecha_obra_publica` |

Suma de pesos: 100%.

## Qué mide cada indicador

### Dimensión `poder_legislativo` (21%)

#### Ratio DNU / leyes

`ratio_dnu`

| | |
|---|---|
| Peso dentro de la dimensión | 20% |
| Peso efectivo en el índice | **4.2%** |
| Familia de lectura | capacidad propia |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `externa` — ACIJ 2011-2024, cuatro presidencias: 344 DNU / 1.058 leyes ≈ 0,33 (ADR-0058/0059) |

**Bandas**: ≤ 0.3 → 100 · 0.3–0.7 → 85 · 0.7–1.2 → 65 · 1.2–2 → 40 · > 2 → 10

**Lo gobiernan**: [ADR-0058](../adr/0058-ratio-dnu-ventana-movil-12m.md) ratio_dnu: ventana móvil de 365 días (reemplaza al acumulado del año calendario) · [ADR-0059](../adr/0059-ratio-dnu-no-recalibrar-anclas.md) ratio_dnu: se revierte la recalibración de anclas de ADR-0058 · [ADR-0090](../adr/0090-que-pregunta-responde-el-ratio-dnu.md) Qué pregunta responde el ratio DNU (y por qué no se agrega "éxito por decreto") · [ADR-0241](../adr/0241-un-dnu-es-un-tipo-juridico-no-una-frase.md) Un DNU es un tipo jurídico, no una frase

#### Eficacia parlamentaria

`eficacia_legislativa`

| | |
|---|---|
| Peso dentro de la dimensión | 27% |
| Peso efectivo en el índice | **5.7%** |
| Familia de lectura | capacidad propia |
| Rezago declarado | 18 meses |
| Procedencia del ancla | `externa` — Directorio Legislativo: 40-50% Macri · 63-67% Alberto Fernández · 75-82% CFK (ADR-0061) |

**Bandas**: > 50 → 100 · 30–50 → 85 · 15–30 → 65 · 5–15 → 40 · ≤ 5 → 10

**Lo gobiernan**: [ADR-0061](../adr/0061-eficacia-legislativa-cohorte-madura.md) eficacia_legislativa: cohorte madura en vez de ventana compartida, anclas contra benchmark histórico externo · [ADR-0063](../adr/0063-eficacia-legislativa-expedientes-jgm.md) eficacia_legislativa: los expedientes JGM (Jefatura de Gabinete) son del Ejecutivo — el Presupuesto era invisible · [ADR-0070](../adr/0070-eficacia-mascara-era-validacion.md) máscara de era para eficacia_legislativa en la reconstrucción del ITCP

#### Sesiones caídas por falta de quórum

`veto_quorum`

| | |
|---|---|
| Peso dentro de la dimensión | 13% |
| Peso efectivo en el índice | **2.7%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `conceptual` — tasa de fracaso de quórum anclada en el cero (Congreso funcionando), cortes redondos (ADR-0121) |

**Bandas**: ≤ 5 → 100 · 5–10 → 85 · 10–20 → 65 · 20–30 → 40 · > 30 → 10

**Lo gobiernan**: [ADR-0091](../adr/0091-veto-quorum-contaba-mal-el-fracaso.md) El indicador de quórum contaba mal el fracaso

#### Normas desafiadas en el recinto

`desafios_legislativos`

| | |
|---|---|
| Peso dentro de la dimensión | 13% |
| Peso efectivo en el índice | **2.7%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `convencion` — anclas sobre el conteo observado (4 a 13 en 22 meses), leído contra el carácter excepcional del acto (ADR-0089) |

**Bandas**: ≤ 2 → 100 · 2–5 → 85 · 5–9 → 65 · 9–12 → 40 · > 12 → 10

**Lo gobiernan**: [ADR-0089](../adr/0089-desafios-en-lugar-de-derrotas.md) Desafíos legislativos en lugar de derrotas legislativas

#### Bloqueo legislativo sostenido

`bloqueo_sostenido`

| | |
|---|---|
| Peso dentro de la dimensión | 12% |
| Peso efectivo en el índice | **2.5%** |
| Familia de lectura | capacidad propia |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `externa` — ninguna insistencia exitosa entre 2003 y 2025: ~100% histórico de sostenimiento (ADR-0069) |

**Bandas**: > 90 → 100 · 75–90 → 85 · 50–75 → 60 · 25–50 → 35 · ≤ 25 → 10

**Lo gobiernan**: [ADR-0069](../adr/0069-bloqueo-sostenido-indicador.md) bloqueo_sostenido: la cara ganada del pulso legislativo entra al ITCP

#### Producción legislativa del Congreso

`produccion_legislativa`

| | |
|---|---|
| Peso dentro de la dimensión | 15% |
| Peso efectivo en el índice | **3.1%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 1.5 meses |
| Procedencia del ancla | `externa` — el techo es el promedio histórico de 74,4 leyes/año de los 18 años completos del dataset de HCDN (2008-2025, 1.340 leyes, cuatro presidencias), no el rango 15-47 observado bajo esta administración (ADR-0168) |

**Bandas**: > 74 → 100 · 50–74 → 85 · 35–50 → 65 · 20–35 → 40 · ≤ 20 → 10

**Lo gobiernan**: [ADR-0168](../adr/0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp.md) Los cuatro indicadores desbloqueados entran al ITCP

### Dimensión `alianzas_territoriales` (19%)

#### Armonía federal (transferencias)

`iaf_transferencias`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **7.6%** |
| Familia de lectura | recursos |
| Rezago declarado | 12 meses |
| Procedencia del ancla | `conceptual` — variación real anclada en el cero con cortes simétricos de 10 pp, como recaudacion/emae del ITCM (ADR-0121) |

**Bandas**: > 10 → 100 · 0–10 → 85 · -10–0 → 65 · -20–-10 → 40 · ≤ -20 → 10

**Lo gobiernan**: [ADR-0066](../adr/0066-iaf-transferencias-solo-provincias.md) iaf_transferencias: el CSV RON incluye la porción del Tesoro Nacional y la ANSES — se filtra a provincias · [ADR-0093](../adr/0093-la-dimension-federal-dice-que-no-mide.md) La dimensión federal declara lo que no mide · [ADR-0239](../adr/0239-el-deflactor-lo-pondera-el-flujo-no-el-calendario.md) El deflactor lo pondera el flujo, no el calendario

#### Alineamiento de senadores por provincia

`alineamiento_senadores_prov`

| | |
|---|---|
| Peso dentro de la dimensión | 30% |
| Peso efectivo en el índice | **5.7%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 1.5 meses |
| Procedencia del ancla | `convencion` — recalibrada con 29 puntos propios de feb-2024 en adelante (ADR-0038) |

**Bandas**: > 70 → 100 · 60–70 → 85 · 50–60 → 65 · 40–50 → 40 · ≤ 40 → 10

**Lo gobiernan**: [ADR-0093](../adr/0093-la-dimension-federal-dice-que-no-mide.md) La dimensión federal declara lo que no mide

#### Adhesión provincial al RIGI

`adhesion_reformas_provincial`

| | |
|---|---|
| Peso dentro de la dimensión | 30% |
| Peso efectivo en el índice | **5.7%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 0 meses |
| Procedencia del ancla | `conceptual` — anclas NO tocadas: la adhesión es un evento irreversible y el rango de hoy es un punto de partida, no el rango final (ADR-0044) |

**Bandas**: > 80 → 100 · 60–80 → 85 · 40–60 → 65 · 20–40 → 40 · ≤ 20 → 10

**Lo gobiernan**: [ADR-0044](../adr/0044-adhesion-reformas-provincial-serie-mensual.md) adhesion_reformas_provincial: serie mensual real vía investigación manual de fechas provinciales

### Dimensión `cohesion_interna` (15%)

#### Cohesión del bloque LLA (bicameral)

`cohesion_bloque`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **15.0%** |
| Familia de lectura | capacidad propia |
| Rezago declarado | 1.5 meses |
| Procedencia del ancla | `convencion` — calibrada contra su propia serie reconstruida desde 2024 (ADR-0042/0048) |

**Bandas**: > 99.9 → 100 · 99–99.9 → 85 · 97–99 → 65 · 95–97 → 40 · ≤ 95 → 10

**Lo gobiernan**: [ADR-0041](../adr/0041-cohesion-bloque-diputados-cache-permanente-y-serie-mensual.md) cohesion_bloque (Diputados): caché permanente por acta y serie mensual real

### Dimensión `conflicto_social` (10%)

#### Conflictividad social (país)

`conflictividad_nacional`

| | |
|---|---|
| Peso dentro de la dimensión | 60% |
| Peso efectivo en el índice | **6.0%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `convencion` — calibrada contra los 30 puntos propios de la serie ACLED desde 2024 (ADR-0052) |

**Bandas**: ≤ -32 → 100 · -32–-29 → 85 · -29–-26 → 65 · -26–-15 → 40 · > -15 → 10

**Lo gobiernan**: [ADR-0132](../adr/0132-conflictividad-nacional-de-donde-viene-y-sobre-que-actua.md) Conflictividad nacional: de dónde viene y sobre qué actúa · [ADR-0232](../adr/0232-la-intensidad-laboral-complementa-la-calle.md) La intensidad laboral complementa la calle

#### Intensidad de los paros

`jornadas_individuales_no_trabajadas_12m`

| | |
|---|---|
| Peso dentro de la dimensión | 40% |
| Peso efectivo en el índice | **4.0%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 6 meses |
| Procedencia del ancla | `historia_larga` — anclas fijadas sobre los 17 años completos 2006-2022 de la serie oficial, anteriores al mandato (ADR-0232) |

**Bandas**: ≤ 5e+06 → 100 · 5e+06–6.5e+06 → 85 · 6.5e+06–8e+06 → 65 · 8e+06–1e+07 → 40 · > 1e+07 → 10

**Lo gobiernan**: [ADR-0232](../adr/0232-la-intensidad-laboral-complementa-la-calle.md) La intensidad laboral complementa la calle

### Dimensión `imagen_voto` (7%)

#### Ventaja LLA−PJ (Votómetro)

`votometro_ventaja_lla`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **7.0%** |
| Familia de lectura | recursos |
| Rezago declarado | 1 meses |
| Procedencia del ancla | `conceptual` — ventaja electoral anclada en el cero (empate) con márgenes simétricos redondos (ADR-0121) |

**Bandas**: > 15 → 100 · 5–15 → 85 · -5–5 → 65 · -15–-5 → 40 · ≤ -15 → 10

**Lo gobiernan**: sin ADR propio — se definió con la paramétrica del cinturón (ADR-0036).

### Dimensión `poder_judicial` (15%)

#### Cobertura de cargos judiciales

`cobertura_judicial`

| | |
|---|---|
| Peso dentro de la dimensión | 50% |
| Peso efectivo en el índice | **7.5%** |
| Familia de lectura | capacidad propia |
| Rezago declarado | 1 meses |
| Procedencia del ancla | `conceptual` — niveles redondos de cobertura de un cuerpo (>90 completa · 80-90 buena · 70-80 aceptable · 60-70 deficitaria · ≤60 crítica), explícitamente NO calibrados contra el rango observado 64-73%, que es desempeño real y bajo (ADR-0126) |

**Bandas**: > 90 → 100 · 80–90 → 85 · 70–80 → 65 · 60–70 → 40 · ≤ 60 → 10

**Lo gobiernan**: [ADR-0126](../adr/0126-el-itcp-abre-la-dimension-poder-judicial.md) El ITCP abre la dimensión del Poder Judicial · [ADR-0144](../adr/0144-el-piloto-de-concursos-corrobora-cobertura-judicial.md) El piloto de concursos corrobora la cobertura judicial · [ADR-0240](../adr/0240-el-numerador-viaja-con-su-fecha.md) El numerador viaja con su fecha

#### Velocidad de resolución de la Corte

`velocidad_resolucion`

| | |
|---|---|
| Peso dentro de la dimensión | 25% |
| Peso efectivo en el índice | **3.8%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 12 meses |
| Procedencia del ancla | `conceptual` — el 100% es el punto donde la Corte resuelve exactamente lo que le entra, sin acumular ni descargar atraso; los cortes son márgenes redondos alrededor de ese valor y no el rango observado 26-142 (ADR-0168) |

**Bandas**: ≤ 40 → 100 · 40–70 → 85 · 70–100 → 65 · 100–130 → 40 · > 130 → 10

**Lo gobiernan**: [ADR-0168](../adr/0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp.md) Los cuatro indicadores desbloqueados entran al ITCP

#### Actividad de las comisiones de control

`paralisis_denuncias`

| | |
|---|---|
| Peso dentro de la dimensión | 25% |
| Peso efectivo en el índice | **3.8%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 2 meses |
| Procedencia del ancla | `conceptual` — cortes redondos sobre sesiones por año de dos comisiones —una por semestre, por trimestre, por bimestre—, no calibrados contra el rango observado 2-7 (ADR-0168) |

**Bandas**: ≤ 2 → 100 · 2–4 → 85 · 4–6 → 65 · 6–9 → 40 · > 9 → 10

**Lo gobiernan**: [ADR-0168](../adr/0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp.md) Los cuatro indicadores desbloqueados entran al ITCP · [ADR-0170](../adr/0170-judicializacion-y-paralisis-pasan-a-fuente-viva.md) Judicialización y parálisis de denuncias pasan a fuente viva

### Dimensión `sector_privado` (13%)

#### Brecha de expectativas: obra pública vs. privada

`brecha_obra_publica`

| | |
|---|---|
| Peso dentro de la dimensión | 100% |
| Peso efectivo en el índice | **13.0%** |
| Familia de lectura | tensión externa |
| Rezago declarado | 7.5 meses |
| Procedencia del ancla | `conceptual` — números redondos alrededor del cero, explícitamente NO calibrados contra el rango observado (ADR-0088) |

**Bandas**: > 10 → 100 · 0–10 → 85 · -10–0 → 65 · -20–-10 → 40 · ≤ -20 → 10

**Lo gobiernan**: [ADR-0088](../adr/0088-dimension-sector-privado.md) El ITCP incorpora una dimensión de sector privado · [ADR-0095](../adr/0095-la-brecha-cambia-de-signo-segun-el-gobierno.md) La brecha de obra pública cambia de signo según el gobierno

## Se releva y no puntúa

Estos indicadores se siguen scrapeando y cacheando, pero están fuera
del índice y fuera del tablero. Sus bandas quedan como referencia
histórica.

- `apoyo_empresario` — Postura pública de las cámaras empresarias
- `cohesion_bloque_senado` — Cohesión del bloque LLA (Senado, fusionado)
- `comisiones_caidas` — Comisiones sin sanción (declarado como contexto)
- `derrotas_legislativas` — Derrotas legislativas del Ejecutivo (declarado como contexto)
- `gobernadores_alineamiento` — Alineamiento de gobernadores (retirado)
- `judicializacion` — Densidad de menciones cautelares en sumarios SAIJ
- `movilizacion_cepa` — Tensión social (CEPA, interno) (declarado como contexto)
- `protestas_caba` — Protestas en CABA (ACLED) (declarado como contexto)
- `rotacion_gabinete` — Rotación del gabinete (declarado como contexto)

## Decisiones abiertas

10 ADR vigentes de este cinturón declaran algo pendiente de decisión editorial. No son trabajo técnico: son llamadas que sólo puede hacer el editor.

> La detección lee la prosa, así que **sobre-reporta a propósito**: si un ADR anota un pendiente y lo resuelve unos párrafos más abajo, sigue apareciendo acá. Se prefiere ese error al contrario —perder una decisión realmente abierta—. La marca ⚠️ sí es firme: sale de las relaciones declaradas entre ADR, no de adivinar sobre el texto.

- **[ADR-0094](../adr/0094-lectura-por-partes-del-itcp.md)** — El ITCP se puede leer por partes: tensión, capacidad y recursos
  <br>como decisión editorial pendiente.
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0132, ADR-0171. Verificar antes de tratarlo como abierto.
- **[ADR-0132](../adr/0132-conflictividad-nacional-de-donde-viene-y-sobre-que-actua.md)** — Conflictividad nacional: de dónde viene y sobre qué actúa
  <br>quedó anotado como pendiente editorial si el indicador **corresponde al cinturón
- **[ADR-0134](../adr/0134-paralisis-de-denuncias-la-fuente-sirve-y-el-dato-contradice-la-hipotesis.md)** — Parálisis de denuncias: la fuente sirve, y el dato contradice la hipótesis
  <br>2. **No se incorpora todavía ningún indicador al ITCP.** Faltan dos decisiones
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0166, ADR-0168. Verificar antes de tratarlo como abierto.
- **[ADR-0135](../adr/0135-cautelares-judicializacion-si-bloqueo-no.md)** — Cautelares: judicialización sí, bloqueo cautelar no
  <br>- **Judicialización: viable** — queda como candidata construible. La densidad cautelar normalizada en jurisdicción Federal + Nacional nace discriminando: rango ×3,5, historia desde 2016 para calibrar 
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0166, ADR-0168. Verificar antes de tratarlo como abierto.
- **[ADR-0136](../adr/0136-apoyo-publico-de-camaras-el-problema-es-a-quien-le-hablan.md)** — Apoyo público de las cámaras: el problema es a quién le hablan
  <br>- Queda pendiente y explícito que **SRA y AmCham no se pudieron evaluar** por
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0139. Verificar antes de tratarlo como abierto.
- **[ADR-0137](../adr/0137-agenda-comun-el-cociente-se-mueve-por-el-denominador.md)** — Agenda común: el cociente se mueve por el denominador
  <br>3. **Queda pendiente la decisión editorial de orientación**, igual que en
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0166, ADR-0168. Verificar antes de tratarlo como abierto.
- **[ADR-0139](../adr/0139-correccion-tres-imposibles-que-no-lo-eran.md)** — Corrección: tres "imposibles" que no lo eran
  <br>3. **No se incorpora todavía ninguno**, por la misma razón que ADR-0134/0135/0137:
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0166, ADR-0168. Verificar antes de tratarlo como abierto.
- **[ADR-0147](../adr/0147-el-universo-de-un-caso-era-un-artefacto.md)** — El universo de un caso era un artefacto de la consulta
  <br>- **Suspender la decisión editorial pendiente, no responderla** — elegida: no tiene sentido decidir si el ITCP admite un indicador de evento antes de saber cuántos eventos hay.
- **[ADR-0148](../adr/0148-apoyo-empresario-con-uia-la-metrica-funciona.md)** — Apoyo empresario: con UIA, la métrica funciona
  <br>2. **NO se incorpora todavía al ITCP.** Falta la **segunda pasada de codificación
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0150. Verificar antes de tratarlo como abierto.
- **[ADR-0166](../adr/0166-regla-de-orientacion-para-indicadores-de-control.md)** — La orientación de un indicador sale de la pregunta que responde
  <br>dice explícitamente: *"No se incorpora todavía ninguno, por la misma razón que
  <br>⚠️ Puede estar resuelto: lo tocó ADR-0168. Verificar antes de tratarlo como abierto.

## Todos los ADR vigentes de este cinturón

68 en total. El índice completo, con los superados y rechazados, está en [docs/adr/README.md](../adr/README.md).

- [0012](../adr/0012-reconstruccion-series-historicas.md) — Reconstrucción de series históricas para indicadores sin histórico (backfill)
- [0036](../adr/0036-itcp-parametrica-politica.md) — ITCP: el cinturón de política se puntúa con la paramétrica de 5 dimensiones (decisión editorial, sin doc CIGOB)
- [0038](../adr/0038-alineamiento-senadores-recalibracion-bandas.md) — alineamiento_senadores_prov: recalibración de anclas ITCP con backfill mensual real
- [0039](../adr/0039-cohesion-bloque-senado-recalibracion-bandas.md) — cohesion_bloque_senado: recalibración de anclas ITCP con backfill mensual real
- [0040](../adr/0040-cohesion-bloque-diputados-desbloqueo-pdf.md) — cohesion_bloque (Diputados): desbloqueado vía endpoint PDF directo, sin evadir el anti-bot de la SPA
- [0041](../adr/0041-cohesion-bloque-diputados-cache-permanente-y-serie-mensual.md) — cohesion_bloque (Diputados): caché permanente por acta y serie mensual real
- [0042](../adr/0042-cohesion-bloque-diputados-recalibracion-bandas.md) — cohesion_bloque (Diputados): recalibración de bandas ITCP con backfill mensual real
- [0043](../adr/0043-protestas-caba-recalibracion-bandas.md) — protestas_caba: recalibración de bandas ITCP con la serie ACLED ya existente
- [0044](../adr/0044-adhesion-reformas-provincial-serie-mensual.md) — adhesion_reformas_provincial: serie mensual real vía investigación manual de fechas provinciales
- [0045](../adr/0045-comisiones-caidas-recalibracion-bandas.md) — comisiones_caidas: recalibración de bandas ITCP (saturación en espejo)
- [0046](../adr/0046-derrotas-legislativas-itcp.md) — `derrotas_legislativas`: nuevo indicador del ITCP (vetos insistidos + decretos rechazados, fusionados)
- [0047](../adr/0047-rotacion-gabinete-itcp.md) — rotacion_gabinete: la rotación ministerial entra al ITCP (pata ejecutiva de cohesión interna)
- [0048](../adr/0048-revision-editorial-cinturon-politica.md) — Revisión editorial del cinturón política: rotación y protestas a contexto, cohesión fusionada en un compuesto bicameral
- [0052](../adr/0052-conflictividad-nacional-acled.md) — Conflicto social del ITCP: `conflictividad_nacional` (ACLED país entero) reemplaza a `movilizacion_cepa`
- [0058](../adr/0058-ratio-dnu-ventana-movil-12m.md) — ratio_dnu: ventana móvil de 365 días (reemplaza al acumulado del año calendario)
- [0059](../adr/0059-ratio-dnu-no-recalibrar-anclas.md) — ratio_dnu: se revierte la recalibración de anclas de ADR-0058
- [0060](../adr/0060-generar-informe-recalcula-indices-desde-crudo.md) — generar_informe.py recalcula ITCM/ITCG/ITCP desde los valores crudos, no confía en el caché del colector
- [0061](../adr/0061-eficacia-legislativa-cohorte-madura.md) — eficacia_legislativa: cohorte madura en vez de ventana compartida, anclas contra benchmark histórico externo
- [0063](../adr/0063-eficacia-legislativa-expedientes-jgm.md) — eficacia_legislativa: los expedientes JGM (Jefatura de Gabinete) son del Ejecutivo — el Presupuesto era invisible
- [0064](../adr/0064-comisiones-caidas-contexto-oculto.md) — comisiones_caidas sale del ITCP a seguimiento interno (fuente ciega a las sanciones del Senado)
- [0066](../adr/0066-iaf-transferencias-solo-provincias.md) — iaf_transferencias: el CSV RON incluye la porción del Tesoro Nacional y la ANSES — se filtra a provincias
- [0069](../adr/0069-bloqueo-sostenido-indicador.md) — bloqueo_sostenido: la cara ganada del pulso legislativo entra al ITCP
- [0070](../adr/0070-eficacia-mascara-era-validacion.md) — máscara de era para eficacia_legislativa en la reconstrucción del ITCP
- [0082](../adr/0082-un-solo-camino-al-puntaje.md) — Un solo camino del valor crudo al puntaje
- [0085](../adr/0085-redundancia-en-los-tres-indices.md) — La redundancia interna se mide en los tres índices, y en cambios además de niveles
- [0088](../adr/0088-dimension-sector-privado.md) — El ITCP incorpora una dimensión de sector privado
- [0089](../adr/0089-desafios-en-lugar-de-derrotas.md) — Desafíos legislativos en lugar de derrotas legislativas
- [0090](../adr/0090-que-pregunta-responde-el-ratio-dnu.md) — Qué pregunta responde el ratio DNU (y por qué no se agrega "éxito por decreto")
- [0091](../adr/0091-veto-quorum-contaba-mal-el-fracaso.md) — El indicador de quórum contaba mal el fracaso
- [0092](../adr/0092-el-informe-declara-su-propio-rezago.md) — El informe declara de cuándo es la foto que muestra
- [0093](../adr/0093-la-dimension-federal-dice-que-no-mide.md) — La dimensión federal declara lo que no mide
- [0094](../adr/0094-lectura-por-partes-del-itcp.md) — El ITCP se puede leer por partes: tensión, capacidad y recursos
- [0095](../adr/0095-la-brecha-cambia-de-signo-segun-el-gobierno.md) — La brecha de obra pública cambia de signo según el gobierno
- [0099](../adr/0099-el-indice-declara-de-que-fecha-es-cada-dato.md) — El índice declara de qué fecha es cada dato
- [0117](../adr/0117-deriva-en-los-otros-indices.md) — Los otros tres índices: sólo el ITCG tenía deriva
- [0121](../adr/0121-itcg-e-itcp-declaran-el-origen-de-sus-bandas.md) — El ITCG y el ITCP declaran el origen de sus bandas; los tres convergen en ~40%
- [0126](../adr/0126-el-itcp-abre-la-dimension-poder-judicial.md) — El ITCP abre la dimensión del Poder Judicial
- [0131](../adr/0131-protocolo-de-codificacion-para-el-bloque-judicial.md) — SAIJ es automatizable, contar no: el protocolo de codificación
- [0132](../adr/0132-conflictividad-nacional-de-donde-viene-y-sobre-que-actua.md) — Conflictividad nacional: de dónde viene y sobre qué actúa
- [0134](../adr/0134-paralisis-de-denuncias-la-fuente-sirve-y-el-dato-contradice-la-hipotesis.md) — Parálisis de denuncias: la fuente sirve, y el dato contradice la hipótesis
- [0135](../adr/0135-cautelares-judicializacion-si-bloqueo-no.md) — Cautelares: judicialización sí, bloqueo cautelar no
- [0136](../adr/0136-apoyo-publico-de-camaras-el-problema-es-a-quien-le-hablan.md) — Apoyo público de las cámaras: el problema es a quién le hablan
- [0137](../adr/0137-agenda-comun-el-cociente-se-mueve-por-el-denominador.md) — Agenda común: el cociente se mueve por el denominador
- [0138](../adr/0138-exito-corporativo-y-velocidad-el-sumario-no-tiene-los-campos.md) — Éxito corporativo y velocidad: el sumario no tiene los campos
- [0139](../adr/0139-correccion-tres-imposibles-que-no-lo-eran.md) — Corrección: tres "imposibles" que no lo eran
- [0140](../adr/0140-el-dato-existe-y-esta-mejor-modelado-de-lo-que-suponiamos.md) — El dato existe y está mejor modelado de lo que suponíamos
- [0141](../adr/0141-detector-de-novedades-judiciales-de-la-csjn.md) — Detector de novedades judiciales de la CSJN
- [0144](../adr/0144-el-piloto-de-concursos-corrobora-cobertura-judicial.md) — El piloto de concursos corrobora la cobertura judicial
- [0145](../adr/0145-apoyo-empresario-la-fuente-sirve-la-metrica-no.md) — Apoyo empresario: la fuente sirve, la métrica no
- [0146](../adr/0146-reglamentacion-irrazonable-si-cuenta.md) — «Reglamentación irrazonable» sí cuenta como veto de constitucionalidad
- [0147](../adr/0147-el-universo-de-un-caso-era-un-artefacto.md) — El universo de un caso era un artefacto de la consulta
- [0148](../adr/0148-apoyo-empresario-con-uia-la-metrica-funciona.md) — Apoyo empresario: con UIA, la métrica funciona
- [0149](../adr/0149-detector-de-postura-empresaria.md) — Detector de postura empresaria
- [0150](../adr/0150-apoyo-empresario-entra-al-itcp.md) — Apoyo empresario entra al ITCP, y el bug que lo encontró
- [0151](../adr/0151-el-corpus-estaba-truncado-y-la-codificacion-se-rehace.md) — El corpus estaba truncado: `apoyo_empresario` se recodifica entero
- [0161](../adr/0161-el-contraste-externo-es-un-factor-comun-no-una-variable.md) — El contraste externo es un factor común, no una variable suelta
- [0166](../adr/0166-regla-de-orientacion-para-indicadores-de-control.md) — La orientación de un indicador sale de la pregunta que responde
- [0168](../adr/0168-los-cuatro-indicadores-desbloqueados-entran-al-itcp.md) — Los cuatro indicadores desbloqueados entran al ITCP
- [0170](../adr/0170-judicializacion-y-paralisis-pasan-a-fuente-viva.md) — Judicialización y parálisis de denuncias pasan a fuente viva
- [0171](../adr/0171-la-lectura-por-partes-no-ordena-empates.md) — La lectura por partes no ordena empates
- [0172](../adr/0172-la-serie-termina-donde-esta-la-card.md) — La serie termina donde está la card
- [0183](../adr/0183-rediseno-del-cinturon-politico.md) — Rediseño del cinturón político según el documento de agosto: registrado, no aplicado
- [0232](../adr/0232-la-intensidad-laboral-complementa-la-calle.md) — La intensidad laboral complementa la calle
- [0239](../adr/0239-el-deflactor-lo-pondera-el-flujo-no-el-calendario.md) — El deflactor lo pondera el flujo, no el calendario
- [0240](../adr/0240-el-numerador-viaja-con-su-fecha.md) — El numerador viaja con su fecha
- [0241](../adr/0241-un-dnu-es-un-tipo-juridico-no-una-frase.md) — Un DNU es un tipo jurídico, no una frase
- [0246](../adr/0246-el-saldo-empresario-se-calculaba-sobre-un-corpus-abierto.md) — El saldo empresario se calculaba sobre un corpus abierto
- [0255](../adr/0255-el-corpus-de-saij-no-identifica-al-ejecutivo.md) — El corpus de SAIJ no identifica al Ejecutivo
