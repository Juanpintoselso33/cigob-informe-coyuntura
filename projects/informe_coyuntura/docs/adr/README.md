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

## Contexto general

Todas estas decisiones corresponden al **rediseño del cinturón macro (ITCM)** de
junio 2026, a partir de los documentos de la Fundación CIGOB (`260602 Parametrica
Macro`, `260602 (2)`, `260626 aportes para el cinturon macro`) y de las
observaciones del analista. El marco base del ITCM (4 dimensiones, pesos, escala
0–100, tensión = (100−ITCM)/10) está descrito en `docs/cinturon_macro.md`.
