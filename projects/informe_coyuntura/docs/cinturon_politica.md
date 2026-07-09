# Cinturón Político

| Campo | Valor |
|---|---|
| Script | `scripts/politica.py` (+ `scripts/itcp.py`) |
| Cache | `output/cache/politica.json` |
| Datos de carga manual | Ninguno hoy — `data/politica/manuales.json` queda como registro histórico de `gobernadores_alineamiento` (retirado del ITCP el 8 de julio de 2026, ver Encuadre); el archivo ya no se lee en `main()` |
| Peso en score global | 30% |
| Barbarismo de riesgo | político — confundir popularidad con poder |

## Encuadre

Fuente conceptual: Carlos Matus, *Política, Planificación y Gobierno*. Mide el capital político como recurso acumulable en cinco dimensiones independientes: poder legislativo, alianzas territoriales, cohesión interna del oficialismo, conflicto social e imagen y voto.

**Nota metodológica (mayo 2026):** el ICG UTDT fue removido del cinturón. Mide confianza ciudadana en el gobierno —dimensión que corresponde al cinturón vida cotidiana / Votómetro—, no la capacidad de gobernar con actores políticos. Según Luis Babino (reunión 12 de mayo de 2026): "yo no lo veo" en este cinturón. Fue reemplazado por `ratio_dnu`, indicador de debilidad legislativa y exposición judicial.

**Nota metodológica (8 de julio de 2026):** `gobernadores_alineamiento` —carga manual, placeholder de 55% congelado desde abril de 2026, sin fuente estructurada automatizable pese a dos rondas de investigación (ver detalle más abajo)— fue retirado del peso del ITCP y reemplazado por `alineamiento_senadores_prov`, indicador automático: % de votos de senadores no-LLA que coincide con la posición del bloque LLA en el Senado, promediado por provincia. Caveat honesto: mide comportamiento de voto de **senadores**, no la postura pública del gobernador (Poder Ejecutivo provincial) —un senador no depende del gobernador de turno—; es la mejor señal automatizable disponible hoy, no una medición directa del alineamiento del Ejecutivo provincial. `gobernadores_alineamiento` queda documentado en este archivo como intento manual descartado: su definición de banda se conserva en `itcp.py::BANDAS_ITCP` como referencia histórica inerte (mismo criterio que se aplicó a `cohesion_bloque` mientras está bloqueado), pero ya no pondera en el ITCP ni se lee desde `manuales.json`.

El cinturón se puntúa con el **ITCP** (Índice de Tensión del Cinturón Político), escala 0–100 donde 0 = máxima tensión (mínimo capital político) y 100 = mínima tensión (máximo capital político). La tensión 0–10 que consume el resto del informe se deriva como `(100 − ITCP) / 10`, así los umbrales globales no cambian: 0–3 estable, 4–6 en tensión, 7–10 tensionado. Reemplaza al promedio simple de los 9 indicadores previamente activos (mismo tipo de cambio metodológico que ITCM/ITCG/ITVC ya atravesaron en sus cinturones).

A diferencia de ITCM/ITCG/ITVC, **no hay un documento CIGOB que fije los pesos** de las cinco dimensiones —ya descriptas en este documento desde mayo 2026, pero nunca ponderadas—. Los pesos de abajo son una decisión editorial explícita, consistente con la lectura ya presente en el propio proyecto: "capital político según Matus: capacidad de gobernar, NO popularidad". Por eso "imagen y voto" pesa deliberadamente menos que las demás dimensiones.

### Estructura del ITCP

```
ITCP = 0,30 × (0,25×P_ratio_dnu + 0,30×P_eficacia_legislativa + 0,20×P_veto_quorum + 0,25×P_comisiones_caidas)
     + 0,25 × (0,40×P_iaf_transferencias + 0,30×P_alineamiento_senadores_prov + 0,30×P_adhesion_reformas_provincial)
     + 0,20 × (0,65×P_cohesion_bloque + 0,35×P_cohesion_bloque_senado)
     + 0,15 × (0,60×P_movilizacion_cepa + 0,40×P_protestas_caba)
     + 0,10 × P_votometro_ventaja_lla
```

| Dimensión | Peso | Indicadores (peso interno) |
|---|---|---|
| Poder legislativo | 30% | `ratio_dnu` (25%) + `eficacia_legislativa` (30%) + `veto_quorum` (20%) + `comisiones_caidas` (25%) |
| Alianzas territoriales | 25% | `iaf_transferencias` (40%) + `alineamiento_senadores_prov` (30%) + `adhesion_reformas_provincial` (30%) |
| Cohesión interna del oficialismo | 20% | `cohesion_bloque` (65%) + `cohesion_bloque_senado` (35%) |
| Conflicto social | 15% | `movilizacion_cepa` (60%) + `protestas_caba` (40%) |
| Imagen y voto | 10% | `votometro_ventaja_lla` (100%) |

Cada indicador puntúa 0–100 por **tabla de bandas** (implementadas en `scripts/itcp.py::BANDAS_ITCP`):

| Indicador | Bandas → puntaje |
|---|---|
| `votometro_ventaja_lla` (pp LLA−PJ) | >15 → 100 · 5–15 → 85 · −5–5 → 65 · −15–−5 → 40 · <−15 → 10 |
| `ratio_dnu` (DNUs/leyes) | ≤0,3 → 100 · 0,3–0,7 → 85 · 0,7–1,2 → 65 · 1,2–2,0 → 40 · >2,0 → 10 |
| `eficacia_legislativa` (%) | >55 → 100 · 35–55 → 85 · 15–35 → 65 · 5–15 → 40 · <5 → 10 |
| `veto_quorum` (%) | ≤5 → 100 · 5–10 → 85 · 10–20 → 65 · 20–30 → 40 · >30 → 10 |
| `comisiones_caidas` (%, 20–30% es "normal") | ≤30 → 100 · 30–50 → 85 · 50–70 → 65 · 70–85 → 40 · >85 → 10 |
| `iaf_transferencias` (% var. real i.a.) | >10 → 100 · 0–10 → 85 · −10–0 → 65 · −20–−10 → 40 · <−20 → 10 |
| `alineamiento_senadores_prov` (%) — **provisional** | >65 → 100 · 45–65 → 85 · 25–45 → 65 · 10–25 → 40 · <10 → 10 |
| `adhesion_reformas_provincial` (%) — **provisional** | >80 → 100 · 60–80 → 85 · 40–60 → 65 · 20–40 → 40 · <20 → 10 |
| `cohesion_bloque` (índice de Rice, %) — **provisional** | >90 → 100 · 75–90 → 85 · 60–75 → 65 · 40–60 → 40 · <40 → 10 |
| `cohesion_bloque_senado` (índice de Rice, %) — **provisional** | mismas bandas que `cohesion_bloque` (mismo constructo) |
| `movilizacion_cepa` (índice 0–100) | ≤20 → 100 · 20–40 → 85 · 40–60 → 65 · 60–80 → 40 · >80 → 10 |
| `protestas_caba` (% var. eventos vs. base 2023) — **provisional** | ≤−30 → 100 · −30–−10 → 85 · −10–10 → 65 · 10–30 → 40 · >30 → 10 |

Convención de bordes: cada banda es `(low, high]` — low exclusivo, high inclusivo. Los puntajes intermedios se **interpolan linealmente entre anclas contiguas** (el motor común `parametrica.py` que también usan ITCM/ITCG/ITVC), no son escalones discretos: el puntaje real aplicado a un valor casi nunca cae justo en 100/85/65/40/10 (ver el detalle por indicador más abajo, donde se cita el puntaje efectivamente aplicado).

Las bandas marcadas **provisional** (`cohesion_bloque`, `cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`, `alineamiento_senadores_prov`) son anclas propias sin serie histórica todavía — a recalibrar cuando el backfill correspondiente esté corriendo con datos reales. La banda de `gobernadores_alineamiento` (retirado, ver Encuadre) queda en `itcp.py::BANDAS_ITCP` únicamente como referencia histórica inerte — ya no se usa para puntuar nada.

Interpretación del ITCP: 0–20 severamente apretado · 20–40 apretado · 40–60 moderadamente apretado · 60–80 moderadamente aflojado · 80–100 aflojado.

Ante indicadores faltantes los pesos se renormalizan (dentro de la dimensión y, si una dimensión queda vacía, entre dimensiones) — consistente con el "ignorar ausencias" del resto del informe.

**Ajustes discrecionales:** `data/politica/ajustes_itcp.json` permite pisar el puntaje interpolado de un indicador puntual con vencimiento (`vigente_hasta`) y justificación — mismo mecanismo que `ajustes_itcm.json`/`ajustes_itcg.json`/`ajustes_itvc.json`. A diferencia de ITCM (ajuste automático del saldo comercial), el ITCP no tiene ninguna regla de ajuste automático: el archivo existe pero hoy está vacío.

## Indicadores activos

| Indicador | Qué mide | Fuente | Frecuencia | Estado |
|---|---|---|---|---|
| `ratio_dnu` | DNUs / leyes sancionadas, año corriente | InfoLeg, sesión POST | Mensual | Automático |
| `eficacia_legislativa` | % de proyectos PE aprobados, ventana 12 meses | datos.hcdn.gob.ar CKAN | Mensual | Automático |
| `veto_quorum` | % de sesiones frustradas por falta de quórum | datos.hcdn.gob.ar CKAN | Mensual | Automático |
| `comisiones_caidas` | % de proyectos con dictamen OD que no llegan al recinto | datos.hcdn.gob.ar CKAN | Mensual | Automático |
| `iaf_transferencias` | Variación real interanual de transferencias federales (RON) | Hacienda, CSV | Anual | Automático |
| `alineamiento_senadores_prov` | % de votos de senadores no-LLA alineados con LLA, promedio por provincia | Scraping `senado.gob.ar` | Mensual | Automático |
| `adhesion_reformas_provincial` | % de provincias adheridas al RIGI | MAGyP (scraping tabla) | Variable | Automático |
| `cohesion_bloque` | Índice de Rice del bloque LLA en Diputados | Scraping `votaciones.hcdn.gob.ar` | Mensual | Automático — **bloqueado en producción** (hoy sin dato: cache pre-Rice purgado) |
| `cohesion_bloque_senado` | Índice de Rice del bloque LLA en Senado | Scraping `senado.gob.ar` | Mensual | Automático |
| `movilizacion_cepa` | Conflictividad social: conflictos laborales y protesta | centrocepa.com.ar (scraping) | Por informe | Automático |
| `protestas_caba` | Variación % de eventos de protesta en CABA vs. base 2023 | ACLED (reutiliza fetcher de gestión) | Semanal | Automático |
| `votometro_ventaja_lla` | Brecha ponderada LLA − PJ en intención de voto | Votómetro CIGOB (HTML) | Por encuesta | Automático |

**Score actual del cinturón (corrida en vivo, 8 de julio de 2026):** `python scripts/politica.py` → **ITCP = 68,4 (moderadamente aflojado)**, tensión derivada **3,2/10**. 11 de 12 indicadores frescos (exit code 1): el único indicador que no pudo actualizarse en vivo es `cohesion_bloque` —bloqueado en producción (ver detalle abajo)—, hoy **ausente** del cache (el placeholder manual pre-automatización de 78% fue purgado, commit `3973d00`; la dimensión `cohesion_interna` se renormaliza al 100% sobre `cohesion_bloque_senado`). Esto es hoy el estado normal esperable de cada corrida, no una falla puntual, hasta que se resuelva el acceso a `votaciones.hcdn.gob.ar`.

Nota de continuidad: el score bajo la métrica anterior (promedio simple) era 4,7/10. El salto a 3,2/10 bajo el ITCP es un cambio de metodología —ponderación por dimensión en vez de promedio plano, y varios indicadores nuevos que hoy puntúan relativamente bien (`cohesion_bloque_senado`, `iaf_transferencias`, `adhesion_reformas_provincial`, `alineamiento_senadores_prov`)—, no una mejora real de golpe en la situación política. Mismo efecto de escala que tuvo ITCG al adoptar su paramétrica. El ITCP subió levemente respecto de la corrida anterior documentada en este archivo (67,2 → 68,4, ambas del 8 de julio de 2026, corridas distintas el mismo día): parte del movimiento es el reemplazo de `gobernadores_alineamiento` (placeholder 55% → puntaje banda 85,0) por `alineamiento_senadores_prov` (68,3% en vivo → puntaje banda 100,0, la banda satura), con el resto siendo deriva normal de las demás fuentes en vivo entre corridas (ej. `ratio_dnu` pasó de 1,471 a 1,529).

## Detalle por indicador

### `ratio_dnu` — Ratio DNU / leyes sancionadas

- Qué mide: proporción de DNUs emitidos respecto a leyes sancionadas por el Congreso en el año corriente. Mayor ratio implica mayor dependencia del decreto, debilidad legislativa y exposición a judicialización (dimensión poder legislativo, Babino: Agregados de Poder).
- Fuente: InfoLeg, búsqueda mediante sesión POST.
- Cálculo: `ratio = count(DNUs enero–hoy) / count(leyes sancionadas enero–hoy)`.
- Bandas: ver tabla en Encuadre. Referencia histórica: año normal 0,3–0,7; gobierno DNU-intensivo >1,2.
- Último valor (8 de julio de 2026): 1,529 (26 DNUs / 17 leyes, período 2026) → puntaje banda 42,7.

### `eficacia_legislativa` — Eficacia legislativa del Ejecutivo

- Qué mide: porcentaje de proyectos del Poder Ejecutivo aprobados por el Congreso en una ventana de 12 meses (dimensión poder legislativo).
- Fuente: datos.hcdn.gob.ar (CKAN, proyectos parlamentarios filtrados por origen PE versus sanciones).
- Bandas: ver tabla en Encuadre.
- Último valor: 4,3% (1 de 23 proyectos PE aprobados en los últimos 12 meses) → puntaje banda 10,0.

### `veto_quorum` — Poder de bloqueo por quórum

- Qué mide: porcentaje de sesiones de Diputados frustradas por falta de quórum. Captura la capacidad de la oposición —o desorganización del oficialismo— de frustrar la agenda legislativa antes del debate. Complementa `eficacia_legislativa`: esta mide el bloqueo pre-debate; `eficacia_legislativa` mide el resultado del debate.
- Fuente: datos.hcdn.gob.ar (CKAN, sesiones del período legislativo con `REUNION_TIPO` que contenga "Fracasada").
- Nota metodológica: incluye frustraciones tanto por acción opositora activa como por inasistencia del propio bloque oficialista. Ambas son señales de debilidad del capital legislativo.
- Último valor: 0,0% (0 de 3 sesiones del período HCDN144 fracasadas) → puntaje banda 100,0.

### `comisiones_caidas` — Proyectos varados post-dictamen

- Qué mide: porcentaje de proyectos que obtuvieron dictamen favorable de al menos una comisión pero no fueron incluidos en el orden del día del plenario. Captura el "cementerio post-comisión": proyectos que pasan el filtro técnico pero mueren antes del recinto.
- Fuente: datos.hcdn.gob.ar (CKAN, dictámenes con orden del día versus sanciones).
- Nota metodológica: un 20–30% es normal (no todo dictamen llega de inmediato al recinto); por encima del 50% indica bloqueo sistemático.
- Último valor: 97,7% (424 de 434 proyectos con OD sin sanción, ventana 12 meses) → puntaje banda 10,0. Refleja el estructural argentino donde la mayoría de los dictámenes no llegan al plenario, no necesariamente un bloqueo activo puntual.

### `iaf_transferencias` — Variación real de transferencias federales

- Qué mide: variación real interanual de las transferencias federales totales al sistema provincial (Régimen de Coparticipación + otros regímenes). Captura la dimensión fiscal del Índice de Armonía Federal (IAF) de Babino: el cumplimiento del flujo de recursos a provincias. Mayor caída real implica mayor tensión fiscal federal y mayor presión sobre gobernadores.
- Fuente: CSV anual de la Serie RON (Recaudación por Origen y Naturaleza), Ministerio de Hacienda.
- Cálculo: variación nominal deflactada por IPC interanual diciembre INDEC (con fallback hardcodeado si la API INDEC falla).
- Último valor: +7,0% real i.a. (período 2025 vs. 2024; nominal +40,7%, IPC aplicado 31,5%) → puntaje banda 91,0.

### `alineamiento_senadores_prov` — Alineamiento de senadores no-LLA por provincia (nuevo, 8 de julio de 2026)

- Qué mide: porcentaje de votos de senadores **no-LLA** que coincide con la posición del bloque LLA en cada votación nominal del Senado, agregado por provincia y promediado entre las provincias con al menos un senador no-LLA (las provincias 100% LLA se excluyen: su "alineamiento" con LLA sería tautológico y no aporta señal).
- Fuente: scraping directo de `senado.gob.ar/votaciones` — misma sesión y descubrimiento de actas que `cohesion_bloque_senado`.
- Cálculo: `Σ(votos no-LLA que coinciden con LLA) / Σ(votos no-LLA totales)`, por provincia, sobre las actas divididas de los últimos 90 días; el resultado final es el promedio simple entre provincias (no ponderado por cantidad de senadores).
- Reemplaza a `gobernadores_alineamiento` (ver Encuadre): placeholder manual de 55%, congelado desde abril de 2026, sin fuente pública estructurada pese a dos rondas de investigación que descartaron cuatro proxies (documentadas en `data/politica/manuales.json._meta.pendiente_automatizacion`): composición del Senado por provincia (mide bancas, no conducta del Ejecutivo), composición de Diputados por distrito (sin campo de gobernador), API de Presupuesto Abierto/ATN (sin corte provincial confirmado) y la tabla de adhesión al RIGI (automatizada aparte, ver `adhesion_reformas_provincial` abajo). El único camino identificado para automatizar `gobernadores_alineamiento` tal cual estaba definido —NLP sobre cobertura periodística— seguía fuera de alcance; `alineamiento_senadores_prov` es una vía distinta, aprovechando el mismo scraping ya construido para `cohesion_bloque_senado`.
- **Caveat honesto:** mide comportamiento de voto de **senadores**, no la postura pública del gobernador (Poder Ejecutivo provincial) —un senador no depende del gobernador de turno—. Es la mejor señal automatizable disponible hoy, no una medición directa del alineamiento del Ejecutivo provincial con la Nación. Mismo tipo de proxy que `adhesion_reformas_provincial`/RIGI: automatizable y honesto sobre lo que mide, pero no idéntico al constructo original.
- Bandas provisionales: mismas anclas que tenía `gobernadores_alineamiento` (sin serie histórica propia todavía, ver nota en Encuadre).
- Último valor: 68,3% (24 de 24 provincias con senador no-LLA, dato del 4 de junio de 2026, corrida exitosa confirmada el 8 de julio de 2026) → puntaje banda 100,0 (la banda satura por encima de 65%).
- Backfill real disponible desde 2026-07-08: serie anual 2023-2026 (4 puntos: 2023=71,9% · 2024=57,7% · 2025=45,3% · 2026=51,9%), ver `output/series/politica.csv`.
- Nota de consistencia: el valor vigente (68,3%) usa una ventana móvil de 90 días; el punto 2026 de la serie backfilleada (51,9%) usa una ventana anual completa (`dias_ventana=366`, todas las actas divididas del año) — mismo patrón de "card vivo vs. serie anual" que `cohesion_bloque_senado`. La diferencia acá es más marcada que en `cohesion_bloque_senado` porque el alineamiento subió notablemente en los meses recientes respecto del promedio de todo el año 2026 — no es un error de cálculo, es una lectura genuina de una tendencia dentro del año.

### `adhesion_reformas_provincial` — Adhesión provincial al RIGI (nuevo)

- Qué mide: porcentaje de provincias (sobre 24) adheridas formalmente al Régimen de Incentivo para Grandes Inversiones (RIGI, Título VII de la Ley 27.742).
- Fuente: tabla de provincias adheridas publicada por el Ministerio de Agricultura, Ganadería y Pesca (MAGyP), scraping directo.
- Alcance honesto: mide adhesión **fiscal** a un régimen puntual, no alineamiento político general con el gobierno nacional. No reemplaza a `alineamiento_senadores_prov` ni al retirado `gobernadores_alineamiento`: son constructos distintos que conviven en la dimensión "alianzas territoriales".
- Bandas provisionales: sin serie histórica propia todavía (ver nota en Encuadre).
- Último valor: 66,7% (16 de 24 provincias, dato del 8 de julio de 2026) → puntaje banda 81,7.

### `cohesion_bloque` — Cohesión del bloque LLA en Diputados

- Qué mide: cuán unido vota el bloque de diputados de La Libertad Avanza en las votaciones nominales. Redefinido de "% alineado con la posición oficial" (no calculable: no hay una posición oficial explícita por votación en los datos disponibles) a **índice de Rice**: `|afirmativos − negativos| / (afirmativos + negativos) × 100`, ausentes/abstenciones excluidos, promediado sobre las actas "divididas" (con al menos un voto a favor y uno en contra) de los últimos 90 días — estándar de ciencia política.
- Fuente: scraping directo y propio de `votaciones.hcdn.gob.ar` (sesión persistente con pacing de 0,3s, descubrimiento de actas por año, parsing de la tabla nominal). Deliberadamente no depende de scrapers de terceros (ej. `Como_voto`) por riesgo reputacional de citar una fuente derivada no oficial como insumo de un índice publicado.
- **Estado real: implementado y testeado (con backfill 2023→presente listo), pero bloqueado en producción.** Verificado en vivo desde un runner real de GitHub Actions: el sitio devuelve, tanto a requests directos como a un headless browser completo (Playwright, con JS ejecutando), una página explícita de "acceso bloqueado" — no es un rate-limit temporal sino un muro anti-bot categórico (el mismo texto estático se repitió en dos intentos separados por 22 minutos). Detalle completo en `docs/adr/0037-cohesion-bloque-scraping-bloqueado-antibot.md`.
- Degradación: mientras el scraper no pueda llegar al sitio, el indicador publica el último valor conocido sin marcarlo `desactualizado` por la sola ausencia de votos nuevos (el guard de frescura distingue "ninguna corrida llegó al sitio en 10+ días" —problema real— de "receso legislativo sin actas nuevas" —normal—).
- Último valor: **ausente**. El placeholder manual pre-automatización (78%, congelado desde abril de 2026) fue purgado del cache real (commit `3973d00`, 2026-07-07): al no ser una medición de índice de Rice genuina, arrastrarlo para siempre habría corrompido el ITCP con un valor de significado distinto (auditoría de código, hallazgo P1 de revisión externa). Mientras el bloqueo de HCDN no se resuelva (ver arriba, ADR-0037), el indicador queda ausente y la dimensión `cohesion_interna` (20% del ITCP) se renormaliza al 100% sobre `cohesion_bloque_senado` — hoy sostiene sola esa dimensión completa (nota metodológica de auditoría, 2026-07-08).
- Bandas provisionales: sin serie histórica propia todavía.

### `cohesion_bloque_senado` — Cohesión del bloque LLA en Senado (nuevo)

- Qué mide: mismo índice de Rice que `cohesion_bloque`, aplicado a las votaciones nominales del bloque LLA en el Senado. Reduce la dependencia de una sola cámara para la dimensión "cohesión interna".
- Fuente: scraping directo de `senado.gob.ar/votaciones` — sitio distinto al de Diputados, sin evidencia del mismo bloqueo anti-bot.
- **Estado real: automático y funcionando en producción.** A diferencia de Diputados, el Senado es alcanzable sin bloqueo. Último valor: 99,4% (18 actas divididas de los últimos 90 días, dato del 4 de junio de 2026, corrida exitosa confirmada el 8 de julio de 2026) → puntaje banda 100,0.
- Caveat: complementario, no reemplaza a `cohesion_bloque` de Diputados — cámaras distintas, composiciones de bloque distintas.
- Backfill real disponible desde 2026-07-08: serie anual 2023-2026 (4 puntos), ver `output/series/politica.csv`.
- Bandas provisionales: sin serie histórica propia todavía (mismas anclas que `cohesion_bloque`, mismo constructo).

### `movilizacion_cepa` — Conflictividad social

- Qué mide: intensidad de la protesta social: huelgas, cortes, conflictos laborales y movilizaciones (dimensión conflicto social del marco Matus).
- Fuente: scraping de `centrocepa.com.ar/informes`. Identifica el último informe con "conflictividad" en URL y extrae la cifra de conflictos del texto.
- Cálculo: extrae "X casos por mes" o "al menos N conflictos" y normaliza a escala 0–100.
- Último valor: 50,5 (101,0 conflictos acumulados, informe CEPA del 9 de junio de 2026) → puntaje banda 64,4.
- Backfill parcial disponible desde 2026-07-08: 2 puntos reales adicionales (abr-2026, jun-2026) — CEPA no publicaba este tipo de informe antes de fines de 2025, así que no hay historia más atrás que reconstruir (ver `output/series/politica.csv`). Alcance honesto: ambos puntos son conteos acumulados **desde inicio del año en curso** (no una tasa mensual) — el aumento aparente entre abril (46,0) y junio (50,5) refleja en parte que transcurrió más tiempo del año, no necesariamente una aceleración de la conflictividad. Comparar estos dos puntos como si fueran una serie mensual homogénea sería engañoso.

### `protestas_caba` — Protestas en CABA (nuevo, reutilizado de gestión)

- Qué mide: variación porcentual de eventos de protesta en CABA (marchas, concentraciones — no cortes de tránsito, que mide `protocolo_antipiquetes` en el cinturón gestión) respecto de la base 2023, según datos ACLED.
- Fuente: reutiliza el fetcher ACLED ya construido para `gestion.py` (protestas_caba) — no se duplica lógica de scraping.
- Lectura distinta según cinturón: en gestión es **contexto** y no puntúa ("premiaría menos marchas" si se puntuara como avance de reforma); en política **sí puntúa**, como condición objetiva de gobernabilidad (nivel de conflicto social, marco Matus) — no como juicio sobre la legitimidad de protestar.
- Detalle técnico: puntúa sobre la **variación porcentual vs. base 2023** (`var_vs_2023`), no sobre el conteo crudo de eventos (que puede estar en cientos) — una tabla de bandas pensada para escala 0–100 interpretaría mal un número en cientos.
- Bandas provisionales: sin serie histórica propia todavía.
- Último valor: +25,4% (301 eventos en 12 meses hasta mayo de 2026, contra 240 en 2023) → puntaje banda 23,8.

### `votometro_ventaja_lla` — Brecha electoral LLA − PJ

- Qué mide: diferencia ponderada en puntos porcentuales entre LLA y PJ en intención de voto. Sintetiza las encuestas espacio más recientes con decaimiento temporal y ponderación por calidad de consultora. Corresponde a la dimensión imagen/voto del marco Matus — deliberadamente la de menor peso (10%), porque el proyecto distingue capital político de popularidad.
- Fuente: parsing del array `encuestasRaw` en `projects/votometro/web/votometro.html` (o su versión live embebida en cigob.org/votometro).
- Filtros: solo entradas con `tipo='espacio'`; ventana de los últimos 60 días desde la encuesta más reciente.
- Ponderación: `exp(−0,015 × días) × calidad_mult` donde A=3, B=2, C=1.
- Último valor: +5,3 pp (LLA 33,4 / PJ 28,1), n=12 encuestas (dato del 28 de mayo de 2026) → puntaje banda 75,6.

## Ejecución

```bash
cd projects/informe_coyuntura
python scripts/politica.py
```

Códigos de salida:

| Código | Significado |
|---|---|
| 0 | Los 12 indicadores frescos |
| 1 | Al menos un indicador fresco (estado normal hoy: `cohesion_bloque` queda ausente mientras `votaciones.hcdn.gob.ar` esté bloqueado) |
| 2 | Ningún indicador fresco (todo desde cache) |

## Notas de mantenimiento

- **Votómetro desactualizado:** si `votometro_ventaja_lla.desactualizado=true`, agregar encuestas al Votómetro en `projects/votometro/web/votometro.html` → array `encuestasRaw` (campo `tipo='espacio'`).
- **Falla de `ratio_dnu`:** verificar que `servicios.infoleg.gob.ar/infolegInternet/` responde. La sesión requiere GET previo para obtener `jsessionid`. Si el formulario cambia estructura, actualizar el regex `action_m` en `fetch_ratio_dnu()`. El texto "necesidad y urgencia" en el campo `texto` filtra los DNUs dentro del tipo "Decreto".
- **Falla de CEPA:** revisar que `centrocepa.com.ar/informes` siga publicando links con "conflictividad" en la URL. Si cambia la estructura del texto del informe, ajustar los patrones regex en `fetch_cepa_movilizacion()`.
- **IAF transferencias:** el CSV de Hacienda se publica anualmente. Si el año cambia y no hay datos (`sin datos para AAAA`), actualizar `RON_CSV_URL` con el nuevo nombre de archivo. Actualizar `IPC_ANUAL` cada enero con la variación diciembre-diciembre INDEC del año que cierra (fallback: la función intenta primero la serie oficial de INDEC).
- **`cohesion_bloque` bloqueado:** no reintentar requests directos ni headless browser sin leer primero `docs/adr/0037-cohesion-bloque-scraping-bloqueado-antibot.md` — ya se probaron ambos y fallan por el mismo muro anti-bot. Caminos a evaluar (ninguno intentado todavía): gestión institucional directa con HCDN, monitoreo pasivo de si `Como_voto` (terceros) vuelve a actualizarse con normalidad, o re-test periódico (el bloqueo puede levantarse con el tiempo, como pasó al revés entre enero y julio de 2026).
- **`cohesion_bloque_senado`:** vía independiente de `cohesion_bloque` — si en el futuro Senado también empieza a bloquear, no asumir que es el mismo problema de Diputados sin verificarlo (son sitios distintos).
- **`adhesion_reformas_provincial`:** si `magyp.gob.ar` cambia de URL o estructura de tabla, ajustar `MAGYP_RIGI_URL` y el parsing en `fetch_adhesion_reformas_provincial()`.
- **`alineamiento_senadores_prov`:** comparte sesión y descubrimiento de actas con `cohesion_bloque_senado` — si Senado empieza a bloquear, ambos indicadores se ven afectados a la vez (a diferencia de `cohesion_bloque`, que es un sitio distinto). No se degrada a `desactualizado` solo por ausencia de votos nuevos en la ventana de 90 días (mismo criterio de `_cohesion_desactualizada` que el resto de la familia Senado).
- **Datos de carga manual:** hoy no hay ninguno activo. `data/politica/manuales.json` y `fetch_manual()` quedan en el código como mecanismo genérico sin uso — `gobernadores_alineamiento`, el único indicador que los usaba, fue retirado del ITCP el 8 de julio de 2026 (ver Encuadre) y ya no se lee desde `main()`.
- **Bandas provisionales:** `cohesion_bloque`, `cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba` y `alineamiento_senadores_prov` usan anclas propias sin historia — revisar cuando el backfill de cada uno esté corriendo con datos reales.
- **Ajustes puntuales:** overrides con vencimiento vía `data/politica/ajustes_itcp.json` — mismo mecanismo que `ajustes_itcm/itcg/itvc.json`.
- **Gate de calidad G3 (`scripts/gate_calidad.py`):** hoy falla para `alineamiento_senadores_prov` (serie[-1]=51,9 vs. card=68,3, fuera de tolerancia) por el mismo motivo de diseño documentado arriba (ventana anual vs. ventana móvil de 90 días) — pendiente agregar la excepción declarada correspondiente a `G3_EXCEPCIONES` (mismo mecanismo ya usado para `sentimiento_digital`, `rigi_inversiones` y `protestas_caba`); no se tocó en esta sincronización de docs por estar fuera de su alcance (cambio de código, no de documentación).

## Limitaciones documentadas de CKAN HCDN

- `q=` realiza búsqueda full-text por tokens, no substring. `q="HCDN144"` no matchea `HCDN144R02`. Usar `q=str(year)` y filtrar del lado Python con `startswith(periodo_prefix)`.
- Filtros por campo exacto con caracteres acentuados devuelven 0 resultados por encoding. Usar siempre Python-side con `.lower()` y substrings.
- `dictámenes.EXPEDIENTE` es el mismo campo que `movimientos.PROYECTO_ID`. Permite join directo sin pasar por proyectos-parlamentarios.
- Las sesiones desactivadas antes de la apertura formal no aparecen en HCDN. Solo aparecen sesiones formalmente iniciadas y luego fracasadas.
- `REUNION_TIPO` para sesiones fracasadas contiene "Fracasada" al final (por ejemplo, "Informativa Art. 71 CN - Citada - Fracasada").
- Período legislativo: `periodo_num = 144 + (año_actual − 2026)`. Prefijo `PERIODO_ID`: `HCDN{periodo_num}`.
