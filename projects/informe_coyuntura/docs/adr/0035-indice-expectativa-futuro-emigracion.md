# ADR-0035 — Índice de Expectativa de Futuro (intención migratoria): evaluar como 4º indicador de espíritu_epoca

| | |
|---|---|
| **Estado** | Propuesto — evaluación pendiente, no implementar todavía |
| **Fecha** | 2026-07-07 |
| **Ámbito** | `scripts/espiritu_epoca.py` · `scripts/vida_cotidiana/collectors/trends.py` (patrón a espejar) · futura ficha metodológica |

## Contexto

El usuario acercó una guía (`guia_google_trends_indice_emigracion.md`, fuera del repo) para un
"Componente A — Índice de Expectativa de Futuro" del cinturón espíritu de época: mide intención
de emigrar vía Google Trends (términos tipo "emigrar", "ciudadanía italiana/española", "trabajo
en el exterior"), organizados en 5 tandas de hasta 5 términos, con un desglose regional opcional
y una tanda de control filtrada por categoría "Empleo". La guía está escrita como instructivo
manual paso a paso (abrir trends.google.com, descargar CSV, pegar en Excel/pandas cada mes).

Hoy `espiritu_epoca.py` tiene 3 proxies "v1 PROVISIONAL", todos reutilizando datos que el
pipeline ya extrae en otro lado (política de diseño explícita del archivo: "no re-fetchea
nada, evita rate-limits y doble parseo"):
- `icc_utdt` — confianza del consumidor (UTDT), leído de vida_cotidiana.
- `sentimiento_digital` — Google Trends de malestar inmediato ("inflación", "precios",
  "inseguridad", "trabajo"), leído de `vida_cotidiana/collectors/trends.py` (pytrends,
  automatizado, ADR-0034).
- `clima_electoral` — ventaja LLA−PJ del Votómetro, leído de política.

## Análisis (esta conversación)

**No es redundante con `sentimiento_digital`.** Miden constructos distintos: `sentimiento_digital`
es ansiedad económica/seguridad del momento (reactivo al ciclo); intención migratoria es un
indicador de "salida" en el sentido de Hirschman (voz vs. salida) — gente que dejó de creer en
el cambio político/económico del país, un signal más estructural y más severo. Ninguno de los
3 proxies actuales de espíritu_epoca captura esto — llenaría un hueco conceptual real, no un
duplicado.

**Desajuste de nombre/alcance.** "Índice de Expectativa de Futuro" es más amplio que lo que la
guía realmente mide (intención migratoria pura, vía términos de emigración). Si se implementa,
documentar explícitamente el alcance angosto en la ficha pública, o renombrar a algo más preciso
(ej. "índice de intención migratoria").

**El proceso manual de la guía está desalineado con el proyecto — pero es automatizable
directamente.** Google Trends ya está automatizado en este mismo repo vía `pytrends`
(`scripts/vida_cotidiana/collectors/trends.py`) sin necesidad de clicks manuales. El problema de
normalización cruzada entre tandas que la guía resuelve manualmente (término ancla "dólar
blue") ya tiene un precedente arquitectónico mejor en el propio repo: ADR-0034 diseñó
`sentimiento_digital` con "ventana fija + cociente intra-consulta, inmune a la renormalización
de Trends" — evita el problema de fondo en vez de parchearlo con un ancla.

**Riesgo real: multiplicación de exposición a rate-limit.** La guía propone hasta 7 corridas de
Trends por mes (5 tandas de términos + desglose regional + tanda de control "Empleo") — mucho
más que el único batch que ya usa `sentimiento_digital`, que la propia `trends.py` documenta
como frágil ("Rate limits: Google bloquea requests frecuentes. Aceptar fallas silenciosas").
Automatizar esto tal cual multiplicaría ese punto de fragilidad ya conocido.

**Disciplina correcta que la guía sí trae:** nunca reportar el indicador solo — cruzarlo
siempre contra un "Componente B" de datos duros (fuga real de investigadores CONICET, trámites
de ciudadanía/visa reales). Coincide con el patrón ya establecido en el proyecto de no confiar
en un proxy de búsqueda aislado.

## Decisión

**Ninguna todavía.** Este ADR deja registrada la evaluación para retomarla en una sesión
dedicada. Preguntas a resolver antes de implementar:

1. ¿Automatizar con `pytrends` espejando `trends.py`, con cuántos términos/tandas reales (no
   los ~25 de la guía completa — hay que acotar para no saturar el rate-limit compartido con
   `sentimiento_digital`)?
2. ¿Nombre final del indicador — mantener "Índice de Expectativa de Futuro" con alcance
   documentado, o renombrar a algo más angosto y preciso?
3. ¿Existe una fuente real y automatizable para el "Componente B" (fuga de investigadores
   CONICET, trámites de ciudadanía/visa) con la que cruzarlo, o queda como validación cualitativa
   manual del analista?
4. ¿Backfill desde dic-2023 (convención del proyecto) en vez de 2020-01-01 (rango de la guía) —
   pytrends permite pedir rangos históricos, confirmar si sufre el mismo problema de
   normalización cruzada entre ventanas temporales distintas?
5. ¿Pesos/integración en `calcular_score()` de espíritu_epoca (hoy promedio simple de 3;
   pasaría a 4)?

## Consecuencias (si se implementa más adelante)

- Nuevo indicador en `INDICADORES_ESPERADOS` de `espiritu_epoca.py` (`icc_utdt`,
  `sentimiento_digital`, `clima_electoral`, + el nuevo).
- Nueva función `fetch_*` reutilizando el patrón pytrends de `trends.py`, no un proceso manual.
- Ficha metodológica nueva, con el alcance (intención migratoria, no "expectativa" genérica)
  documentado explícitamente y la limitación búsqueda≠intención real ya incorporada como nota
  permanente (mismo estándar que las 55 fichas existentes).

## Opciones descartadas

- **Seguir la guía tal cual (proceso manual mensual)**: descartado — contradice ADR-0001 y el
  patrón ya automatizado de Trends en este mismo repo.
