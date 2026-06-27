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

## Contexto general

Todas estas decisiones corresponden al **rediseño del cinturón macro (ITCM)** de
junio 2026, a partir de los documentos de la Fundación CIGOB (`260602 Parametrica
Macro`, `260602 (2)`, `260626 aportes para el cinturon macro`) y de las
observaciones del analista. El marco base del ITCM (4 dimensiones, pesos, escala
0–100, tensión = (100−ITCM)/10) está descrito en `docs/cinturon_macro.md`.
