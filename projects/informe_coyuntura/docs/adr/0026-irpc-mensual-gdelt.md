# ADR-0026 — Mensualización del IRPC: forma GDELT calibrada a anclajes DP

- **Fecha:** 2026-07-03
- **Estado:** RECHAZADO por ahora (fuente operativamente inviable; ver
  Resultados). La mensualización queda por la vía DP (suscripción, gestión
  CIGOB) y por el GTFS-RT propio al madurar.

## Contexto

El ADR-0025 automatizó el protocolo antipiquetes con los anclajes ANUALES
públicos de Diagnóstico Político. El editor exige granularidad mensual como
mínimo. Los reportes mensuales por distrito de DP son por suscripción (vía
limpia, pendiente de gestión de CIGOB); mientras tanto, la única fuente
mensual automática y gratuita candidata es GDELT (base global de noticias,
2017→hoy): mismo enfoque epistemológico que DP (ambos cuentan desde los
medios — DP releva 100+ medios argentinos a mano; GDELT indexa la prensa
global automáticamente).

## Decisión (condicional)

**Híbrido forma × ancla:** el volumen mensual de cobertura de piquetes en
GDELT aporta la FORMA de la curva; los anclajes anuales de DP aportan el
NIVEL. Cada año calendario del volumen GDELT se reescala para que su suma
coincida con el conteo anual CABA de DP (2023 = 931 · 2024 = 440 · 2025 =
240); el año corriente se reescala con el factor del último año cerrado
hasta que DP publique. IRPC mensual = 1 − (serie calibrada, suma móvil 12m) /
931.

**Criterio de aceptación:** los ratios anuales del volumen GDELT deben
reproducir la caída medida por DP (nacional 1 / 0,73 / 0,47 · CABA 1 / 0,47 /
0,26) con el mismo orden y magnitud comparable. Si la señal es ruido, este
ADR se rechaza y la mensualización espera a la suscripción DP.

## Resultados de la validación (03-jul-2026)

**UNUSABLE.** La GDELT DOC 2.0 API aplicó throttling persistente (HTTP 429)
desde nuestro entorno incluso con pausas de 10 s entre requests y backoffs de
75 s × 4 reintentos; las pocas respuestas que pasaron devolvieron volumen
cero para las tres variantes de query probadas (`piquete sourcecountry:AR`,
`"piquetes" ... sourcelang:spa`, `(piquete OR piquetes) "buenos aires" ...`)
en 2024-H1 — un período donde DP contó ~3.000 piquetes nacionales, así que el
cero es señal de bloqueo/indexación, no de realidad. No se pudo validar la
forma mensual, y una fuente que estrangula así no puede sostener un pipeline
nocturno.

## Condiciones de reapertura

- Probar desde la IP de los runners de CI (GitHub Actions): el throttling
  puede ser por IP/entorno.
- Si GDELT responde: correr la validación completa (ratios anuales vs DP
  nacional 1/0,73/0,47 y CABA 1/0,47/0,26) antes de cablear nada.
- Si CIGOB consigue la suscripción DP, este ADR queda obsoleto: los anclajes
  mensuales reales de DP entran directo al colector del ADR-0025 sin cambiar
  la métrica.

## Consecuencias

El IRPC queda con granularidad ANUAL (anclajes públicos DP, ADR-0025) hasta
que la suscripción DP o una GDELT operativa habiliten la mensualización. La
serie publicada lo declara ("IRPC, anual").
