---
madr: 4
id: '0025'
estado: 'aceptado'
nota_estado: 'aceptada (revisión uno-por-uno de gestión; mandato del editor:'
fecha: 2026-07-03
cinturon: 'gestion'
indicadores: [protocolo_antipiquetes]
---

# ADR-0025 — Protocolo antipiquetes automatizado con Diagnóstico Político (y corrección 55 → 74,2)

"el objetivo es conseguir los datos, seguir buscando hasta encontrar")

## Contexto y planteo del problema

El protocolo antipiquetes era el único indicador manual de gestión (55%,
"estimado"). La barrida de fuentes automáticas descartó: registro GCBA
(muerto), Ministerio de Seguridad (sin dataset), ACLED (nivel Open sin API de
eventos; investigado a fondo — OAuth funciona, el entitlement no; categoría
de la cuenta subida a Academic por si el Access Team re-evalúa). La fuente
apareció donde nació el dato: **Diagnóstico Político** — la consultora que el
propio doc CIGOB cita — publica sus monitoreos de piquetes (relevamiento
diario sobre 100+ medios desde 2009) con los agregados anuales ABIERTOS en su
web y replicados por la prensa (Chequeado, La Nación). Su definición de
piquete coincide con la de la Res. 943/23.

## Opciones consideradas

- **Colector automático** con el IRPC (1 − cortes CABA del último año / cortes CABA 2023) y anclajes anuales curados y fechados — elegida.
- **Seguir con carga manual** — reemplazada por el colector.

## Decisión

1. **Colector automático** (`fetch_protocolo_antipiquetes`): IRPC = 1 −
   cortes CABA último año / cortes CABA 2023, con anclajes anuales curados y
   fechados en `data/gestion/dp_piquetes.json` (mismo patrón de hitos que
   privatizaciones/concesiones): 2023 = 931 (11,3% de 8.239) · 2024 = 440 ·
   2025 = 240 (6,2% de 3.893). El colector además scrapea la página pública
   de monitoreos como DETECTOR de informes nuevos (avisa en el log del
   pipeline para actualizar el store). Serie por escalones anuales desde
   ene-2024. La entrada de manuales.json queda como fallback.
2. **Corrección del valor: 55 → 74,2.** El 55% manual era la foto de 2024
   ("caída superior al 50%") y coincidía con la caída NACIONAL 2023→2025
   (52,8%) — pero la métrica definida es CABA: 1 − 240/931 = **74,2%**. El
   indicador estaba subcalibrado ~20 puntos. Puntaje 79,0 → **92,0**
   (interpolado); dimensión social y orden 82,6 → 87,8; **ITCG +0,5**.
3. El histórico del valor viejo se purgó (regla ADR-0012 de recalibración).

## Más información

### Limitaciones

- Granularidad ANUAL (los reportes mensuales por distrito de DP son por
  suscripción — info@diagnosticopolitico.com.ar; si CIGOB se suscribe, el
  mismo colector pasa a mensual).
- caba_2023 es derivado del share publicado (11,3% × 8.239 = 931), no un
  conteo directo; documentado en el store con fuentes.
- El detector de novedades depende del formato de los títulos de DP
  ("N piquetes en YYYY"); si cambia, el aviso deja de saltar pero el
  indicador sigue sirviendo el último ancla (nunca se rompe).
