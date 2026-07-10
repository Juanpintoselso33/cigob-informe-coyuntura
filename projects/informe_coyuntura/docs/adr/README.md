# Architecture Decision Records (ADRs) — Informe de Coyuntura

Registro de las **decisiones de diseño y metodología** del proyecto. Cada ADR
documenta una decisión, su contexto, las opciones que se consideraron (incluidas
las descartadas, para no volver a investigarlas) y sus consecuencias.

Formato de cada ADR: **Estado · Contexto · Decisión · Opciones consideradas · Consecuencias**.

Los ADR son inmutables: si una decisión se revierte, se crea un ADR nuevo que
*supersede* al anterior (y se actualiza el estado del viejo), no se reescribe.

## Índice

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-datos-calculados-no-hardcodeados.md) | Todos los indicadores se calculan de datos oficiales; nunca valores hardcodeados | Aceptado |
| [0002](0002-rem-equivalente-mensual.md) | El REM se puntúa por su equivalente mensual (raíz-12), no por nivel absoluto | Aceptado |
| [0003](0003-recaudacion-interanual-real.md) | La recaudación se mide en variación interanual REAL (deflactada) | Aceptado |
| [0004](0004-financiamiento-indice-capacidad-prestable.md) | La dimensión de financiamiento usa el Índice de Capacidad Prestable (IdC) | Aceptado |
| [0005](0005-reservas-netas-a-secas.md) | Reservas: netas "a secas" calculadas de la planilla SDDS + Tesoro + Bopreal | Aceptado |
| [0006](0006-brecha-cambiaria-ccl-mayorista.md) | La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista | Aceptado |
| [0007](0007-fichas-explican-concepto-no-fuente.md) | Las fichas de indicador explican qué mide, no de dónde sale el dato | Aceptado |
| [0008](0008-tcrm-itcrm-bcra.md) | El TCRM usa el ITCRM oficial del BCRA, no la serie discontinuada de INDEC | Aceptado |
| [0009](0009-idm-y-tcrm-en-el-itcm.md) | IDM (desequilibrio monetario, real-real i.a.) en estabilidad monetaria + TCRM como 5ª dimensión | Aceptado |
| [0010](0010-capitulo-inversion-iai-icip.md) | Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión; patentamientos por acumulación | Aceptado |
| [0011](0011-rigi-plataforma-oficial.md) | RIGI: inversión aprobada/pipeline desde la plataforma oficial (Google Sheet), no conteo de normas InfoLeg | Aceptado |
| [0012](0012-reconstruccion-series-historicas.md) | Reconstrucción de series históricas (backfill) para indicadores sin histórico + de-hardcode del deflactor IPC en iaf_transferencias | Aceptado |
| [0013](0013-itcg-parametrica-gestion.md) | ITCG: el cinturón de gestión se puntúa con la paramétrica de 5 dimensiones (doc 260702); motor común en parametrica.py | Aceptado |
| [0014](0014-piquetes-poller-gtfs-rt.md) | Piquetes: poller GTFS-RT acumulativo 3×/día (el registro de cortes del GCBA está muerto); protocolo_antipiquetes sigue manual hasta que la serie madure | Aceptado |
| [0015](0015-tdps-presupuesto-abierto.md) | TDPS (asistencia directa): verificado contra el devengado real vía API Presupuesto Abierto — 5.1.4 directo / inciso 5 total de Volver al Trabajo + Acompañamiento Social, baseline Potenciar 2023 | Aceptado |
| [0016](0016-concesiones-contratar-salud-sss.md) | Concesiones: km adjudicados de la RFC vía CONTRAT.AR (sin login) · Opción salud: derivación directa a prepagas vía padrones RNAS/RNEMP de la SSS. Gestión queda 15/16 auto | Aceptado |
| [0017](0017-protestas-acled.md) | Protestas CABA vía ACLED (agregado semanal, sesión Open): contexto con serie 2018→hoy. La protesta NO bajó vs 2023 — los cortes sí: el protocolo manual sigue puntuando (mide cortes, ACLED no los aísla) | Aceptado |
| [0018](0018-itvc-parametrica-vida-cotidiana.md) | ITVC-B100: vida cotidiana se puntúa con el índice base 100 = 4T-2023 (doc 260702) — niveles vs salarios, endeudamiento corregido por mora BCRA, tensión = 5−(ITVC−100)×0,2 | Aceptado |
| [0019](0019-revision-metodologica-parametricas.md) | Revisión metodológica de las 3 paramétricas vs el canon (JRC/OCDE, Ravallion, IDH, DB, ICRG): análisis de sensibilidad implementado (`sensibilidad.py`) + decisiones abiertas (bandas→interpolación, doble conteo brecha/ILCE, concentración I_EC, validación externa) | Parcial |
| [0020](0020-flag-dimension-critica.md) | Dimensión crítica: la compensabilidad de la agregación lineal se SEÑALIZA (flag + card en rojo cuando puntaje < 30 en bandas / < 85 en base-100), no se corrige — resuelve la Decisión 2 del ADR-0019 | Aceptado |
| [0021](0021-interpolacion-y-apertura-sin-brecha.md) | ITCM/ITCG puntúan por INTERPOLACIÓN entre las anclas de las bandas del doc (adiós escalones: ITCM 51,7→54,7 · tensión −0,3) y apertura comercial = alícuota efectiva sola (la brecha puntúa una vez, en cepo_mulc) — resuelve las Decisiones 3 y 4 del ADR-0019 | Aceptado |
| [0022](0022-credito-real-y-contexto-oculto.md) | Crédito privado REAL i.a. entra al ITCM (financiamiento 45/40/15: la señal de crédito realizado, complementa al IdC) y los 4 monetarios nominales quedan ocultos del snapshot pero vivos en la pipeline (insumos de IdC/IDM/TCRM) | Aceptado |
| [0023](0023-litigiosidad-al-itcg.md) | Litigiosidad SRT entra al ITCG (reforma laboral 70/30: instrumento Fondo de Cese + resultado juicios — la dimensión ya no descansa en un único indicador); protestas ACLED y alertas GTFS-RT siguen de contexto con razones documentadas | Aceptado |
| [0024](0024-motos-movil-12m-estacionalidad.md) | Auditoría de estacionalidad: casi todo cubierto por construcción (interanuales, ventanas 12m, fuentes desestacionalizadas); la excepción real era motos (enero ≈ 2× junio) → rebase por acumulado móvil 12m (motos 175,9 → 166,7; ITVC 92,0) | Aceptado |
| [0025](0025-protocolo-diagnostico-politico.md) | Protocolo antipiquetes AUTOMATIZADO con los anclajes anuales públicos de Diagnóstico Político (hitos curados + detector de informes nuevos) y CORREGIDO: 55% era la foto 2024/nacional — el IRPC de CABA con 2025 cerrado es 74,2% (240 vs 931 cortes); gestión queda sin indicadores manuales | Aceptado |
| [0026](0026-irpc-mensual-gdelt.md) | Mensualización del IRPC vía GDELT (forma mensual × anclajes DP): RECHAZADO por ahora — la DOC API estranguló con 429 persistente y la señal no pudo validarse; la vía mensual queda por suscripción DP o GTFS-RT al madurar (condiciones de reapertura documentadas) | Rechazado |
| [0027](0027-auditoria-idc-rediseno.md) | Auditoría adversarial del IdC vs la literatura FCI (NFCI/Goldman/Bloomberg): leyenda con signo invertido CORREGIDA; doble conteo de depósitos, asignación mal condicionada, derivada-no-nivel y sin estacionalidad — resuelta por opción (a) → ADR-0028 | Resuelto |
| [0028](0028-idc-z-scores.md) | IdC rediseñado como FCI simplificado: tres NIVELES (tasa real, depósitos i.a. real, holgura 1−R) en z-scores contra la historia 2018→hoy, pesos 30/40/30 del doc conservados, anclas por percentiles; jun-2026: 1,06 verde → −0,31 σ amarillo (el 100 lo sostenía el aguinaldo) | Aceptado |
| [0029](0029-recaudacion-promedio-movil-3m.md) | Recaudación real: promedio móvil 3 meses sobre IPC cerrado (práctica IARAF/OPC) — el i.a. de un mes suelto heredaba el calendario tributario y movía el ITCM ±7 pts con 14,4% de peso; el mes fresco queda provisorio en el detalle; jun: puntaje 10 → tendencia real −2,3% = ~33 | Aceptado |
| [0030](0030-borde-irregular-mes-comun.md) | Borde irregular (ragged edge): criterio de FAMILIA — titular al último mes COMÚN de todos los insumos + dato fresco provisorio en el detalle sin puntuar; imputación tipo Conference Board LEI descartada (datos estimados + revisiones retroactivas, inaceptable en un índice de rendición de cuentas) | Aceptado |
| [0031](0031-validacion-cruzada-tercer-pilar.md) | Tercer pilar de robustez: matriz de validación CRUZADA (3 índices × 2 contrastes, convergente+discriminante — ITCM/ITCG con el mercado, ITVC parejo y declarado); lead-lag probado y descartado como claim (coincidentes, no anticipan); validacion_externa.py al pipeline nocturno (se refrescaba a mano); ruido de insumos scale-free (±5% del ancho entre anclas) | Aceptado |
| [0032](0032-inseguridad-ivi-mensual.md) | Inseguridad MENSUALIZADA: del SNIC anual al IVI del LICIP-UTDT (encuesta de victimización, 40 centros urbanos, ventana 12m — capta la cifra negra); base declarada ene-2024 (encuesta suspendida 2020-2023); SNIC queda de contraste con store propio; divergencia registrado↓/declarado↑ visible = información | Aceptado |
| [0033](0033-itvc-doble-conteo-y-winsorizacion.md) | ITVC saneado: doble conteo salario/comida eliminado (brecha vs alimentos r=0,985 = 32,75% del índice repetido → alimentos pasa a encarecimiento RELATIVO vs IPC general) + winsorización ASIMÉTRICA (techo 140 para booms — motos 166,7; sin piso: las crisis se señalizan con la flag crítica, no se recortan); ITVC 91,5 → 90,5; D10 abierta (taxonomía de dimensiones, CIGOB) | Aceptado |
| [0034](0034-sentimiento-digital-puntuable.md) | Sentimiento digital PUNTUABLE: el cociente intra-consulta cancela la renormalización de Trends (verificado: 3 corridas amplitud 0,0; r=+0,76 vs IPC m/m; Wikipedia descartada con datos) — serie mensual ventana fija 2021→ con store de reemplazo total; entra a Confianza con 10% (ICC 45/IVI 30/sent 10/carne 10/motos 5); 13/13 puntúan, ITVC 90,7 | Aceptado |
| [0035](0035-indice-expectativa-futuro-emigracion.md) | Índice de Expectativa de Futuro (intención migratoria) evaluado como 4º indicador de `espiritu_epoca` | Aceptado |
| [0036](0036-itcp-parametrica-politica.md) | ITCP: el cinturón de política se puntúa con la paramétrica de 5 dimensiones (decisión editorial, sin doc CIGOB que fije los pesos) | Aceptado |
| [0037](0037-cohesion-bloque-scraping-bloqueado-antibot.md) | `cohesion_bloque` (Diputados): scraping directo implementado y correcto, pero bloqueado en producción por detección anti-bot de HCDN | Implementado, bloqueado en producción |
| [0038](0038-alineamiento-senadores-recalibracion-bandas.md) | `alineamiento_senadores_prov`: anclas ITCP recalibradas 65/45/25/10 → 70/60/50/40 con backfill mensual real (29 puntos feb-2024→jun-2026); el techo viejo saturaba en 28% de los meses reales | Aceptado |
| [0039](0039-cohesion-bloque-senado-recalibracion-bandas.md) | `cohesion_bloque_senado`: anclas ITCP recalibradas 90/75/60/40 → 95/90/85/80 con backfill mensual real (29 puntos feb-2024→jun-2026); el techo viejo saturaba en 86% de los meses reales — único insumo real hoy del 20% "cohesión interna" del ITCP mientras Diputados siga bloqueado | Aceptado |
| [0040](0040-cohesion-bloque-diputados-desbloqueo-pdf.md) | `cohesion_bloque` (Diputados) desbloqueado sin evadir el anti-bot de la SPA: endpoint PDF directo del mismo sitio (`/pdf/acta/{id}`), sin protección; verificado en vivo 99,9% de cohesión, 33 actas — supera el bloqueo de ADR-0037; anclas siguen provisionales, backfill pendiente | Aceptado |
| [0041](0041-cohesion-bloque-diputados-cache-permanente-y-serie-mensual.md) | `cohesion_bloque` (Diputados): caché permanente por acta (cada PDF se descarga una sola vez en la vida del proyecto) y serie mensual real backfilleada | Aceptado |
| [0042](0042-cohesion-bloque-diputados-recalibracion-bandas.md) | `cohesion_bloque` (Diputados): anclas ITCP recalibradas 90/75/60/40 → 99,9/99/98/97 con 31 puntos mensuales reales; el techo viejo saturaba en 31/31 meses | Aceptado |
| [0043](0043-protestas-caba-recalibracion-bandas.md) | `protestas_caba`: anclas ITCP recalibradas -30/-10/10/30 → -6/-3/0/10 con la serie ACLED ya existente (30 puntos válidos); 73% de los meses caía en una sola banda | Aceptado |
| [0044](0044-adhesion-reformas-provincial-serie-mensual.md) | `adhesion_reformas_provincial`: serie mensual real (24 puntos) vía investigación manual de la fecha de adhesión de cada provincia; anclas chequeadas y conservadas (proceso irreversible en curso) | Aceptado |
| [0045](0045-comisiones-caidas-recalibracion-bandas.md) | `comisiones_caidas`: anclas ITCP recalibradas 30/50/70/85 → 96/97/98/99 con 32 puntos mensuales reales; el rango observado (94,7–99,8) caía completo en la banda del piso | Aceptado |
| [0046](0046-derrotas-legislativas-itcp.md) | `derrotas_legislativas`: nuevo indicador del ITCP — conteo 12m de derrotas consumadas del Ejecutivo (vetos insistidos por ambas cámaras + decretos rechazados bajo la ley 26.122), fusión de dos investigaciones de factibilidad; registro de eventos versionado + detección incremental (InfoLeg + actas del Senado); pesos internos de poder_legislativo redistribuidos | Aceptado |
| [0047](0047-rotacion-gabinete-itcp.md) | `rotacion_gabinete`: salidas de rango ministerial (JGM + ministros) acumuladas 12m entra al ITCP como pata ejecutiva de cohesión interna (45/25/30); registro curado con decreto BO por salida + detector de alerta InfoLeg (recall 11/11); anclas 1/2/4/6 calibradas con la serie real de 32 meses, 5 bandas pobladas | Aceptado (superado por 0048: pasa a contexto) |
| [0048](0048-revision-editorial-cinturon-politica.md) | Revisión editorial CIGOB del cinturón política (lectura mínima): `rotacion_gabinete` y `protestas_caba` salen del índice a contexto; las dos cohesiones se fusionan en un compuesto bicameral 65/35 bajo `cohesion_bloque` (banda recalibrada 99,9/99/97/95 contra la serie compuesta); 14 → 11 indicadores puntuando + 2 contexto | Aceptado |

## Contexto general

Todas estas decisiones corresponden al **rediseño del cinturón macro (ITCM)** de
junio 2026, a partir de los documentos de la Fundación CIGOB (`260602 Parametrica
Macro`, `260602 (2)`, `260626 aportes para el cinturon macro`) y de las
observaciones del analista. El marco base del ITCM (4 dimensiones, pesos, escala
0–100, tensión = (100−ITCM)/10) está descrito en `docs/cinturon_macro.md`.
