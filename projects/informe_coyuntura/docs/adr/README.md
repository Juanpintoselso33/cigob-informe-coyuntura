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

## Contexto general

Todas estas decisiones corresponden al **rediseño del cinturón macro (ITCM)** de
junio 2026, a partir de los documentos de la Fundación CIGOB (`260602 Parametrica
Macro`, `260602 (2)`, `260626 aportes para el cinturon macro`) y de las
observaciones del analista. El marco base del ITCM (4 dimensiones, pesos, escala
0–100, tensión = (100−ITCM)/10) está descrito en `docs/cinturon_macro.md`.
