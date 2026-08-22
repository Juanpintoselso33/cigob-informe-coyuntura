# 08 — Decisiones metodológicas abiertas (agenda CIGOB)

Las decisiones que exceden el mandato técnico de los barridos y esperan
definición del equipo. Cada una tiene propuesta armada — decidir es elegir,
no investigar desde cero. Numeración heredada de las sesiones de trabajo
(las D anteriores se resolvieron en ADRs).

## D7 — TDPS saturado

**Qué:** `asistencia_directa` (TDPS) llegó a 100% — todo el gasto social
relevante ya va directo, sin intermediarios. Un indicador saturado no
discrimina más.
**Propuesta:** mantenerlo como conquista consolidada (con nota) o
reemplazarlo por una métrica con recorrido (ej. cobertura, tiempo de alta).
**Para decidir:** si la paramétrica de gestión premia *mantener* logros o
solo *avanzar*.

## D8 — Percentiles: régimen normativo vs posicional

**Qué:** las bandas del ITCM/ITCG son normativas (umbrales con significado
económico). La alternativa posicional (percentiles de la propia historia)
se armó con distribuciones reales y quedó **decidida NO aplicar por ahora**
— pendiente de discusión doctrinaria.
**Propuesta completa presentada en sesión (04-jul):** doctrina de dos
regímenes — normativo para indicadores con umbral económico duro (inflación,
reservas), posicional para los que solo tienen sentido relativo a su historia.
**Para decidir:** si se adopta el régimen mixto y para qué indicadores.

## D9 — Dimensiones mono-indicador

**Qué:** varias dimensiones (en los tres índices) descansan en un único
indicador: un error de fuente se transmite entero al índice. Vulnerabilidad
del ITCIS y Conflicto social del ITCP salieron de esa lista (ADR-0231 y
ADR-0232); quedan Competitividad externa (ITCM), Imagen y voto y Cohesión
interna (ITCP) y Seguridad (ITCIS).
**Para decidir:** mínimo de 2 componentes por dimensión como regla, o
aceptar mono-indicador con flag. El barrido se sigue haciendo dimensión por
dimensión mientras no haya regla escrita.

## Resueltas recientemente (para no reabrir)

- **D10 — La taxonomía del ITCIS quedó resuelta**: ADR-0115 separó
  percepción, seguridad e ingresos; ADR-0130 incorporó empleo directo y
  ADR-0214 trasladó informalidad a empleo. El manual vigente se genera desde
  `scripts/itvc.py` en [`docs/manuales/vida.md`](../manuales/vida.md).
- **D5 — Vulnerabilidad financiera ya tiene segundo componente** (ADR-0231,
  21-ago-2026): entra la carga del servicio de deuda de las familias sobre la
  masa salarial registrada (BCRA, IEF) con 30%, y la mora conserva 70% por ser
  directa, mensual y más fresca. La descripción vieja de esta D hablaba del
  compuesto endeudamiento real×mora, que ADR-0154 ya había desarmado.
- **Conflicto social del ITCP dejó de depender sólo de ACLED** (ADR-0232,
  21-ago-2026): suman las jornadas individuales no trabajadas de la Secretaría
  de Trabajo, acumuladas a 12 meses, con 40%.

- **Base 4T-2023 del ITVC se mantiene** pese al efecto base de la
  devaluación (la brecha marca +12,2% vs 4T-23 pero +2,7% vs oct-23
  pre-deval): es la definición del doc — "100 = arranque del mandato" — y el
  editor la ratificó (04-jul-2026).
- **Sentimiento digital puntúa** (ADR-0034) — cerró la pregunta de si Trends
  era metrizable.

## Pendientes externos (no requieren decisión, requieren que pase algo)

| Qué | Espera |
|---|---|
| ACLED nivel de cuenta UBA | re-evaluación asíncrona del upgrade Academic; sonda nocturna auto-destrabante ya corre |
| BK cantidades (IAI) | que INDEC publique mensual en API |
| Gasto/masa de gestión a media móvil 3m | decisión del editor (propuesto en barrido macro #5) |
| SAT mensual (inseguridad, granularidad) | tanda dic-2026 con datos 2025 |
| GDELT (ADR-0026, rechazado) | condiciones de reapertura documentadas en el ADR |
| Diagnóstico Político por suscripción / GTFS-RT | maduración de las fuentes |
