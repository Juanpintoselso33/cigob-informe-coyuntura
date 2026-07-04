# 08 — Decisiones metodológicas abiertas (agenda CIGOB)

Las decisiones que exceden el mandato técnico de los barridos y esperan
definición del equipo. Cada una tiene propuesta armada — decidir es elegir,
no investigar desde cero. Numeración heredada de las sesiones de trabajo
(las D anteriores se resolvieron en ADRs).

## D5 — Segundo componente de vulnerabilidad financiera

**Qué:** la dimensión Vulnerabilidad del ITVC (10%) tiene UN solo indicador
(endeudamiento real×mora), que además está en zona crítica (31,7) y es el
dominante del índice (leave-one-out: sin él el ITVC salta de 90,7 a ~98).
**Propuesta:** sumar un segundo componente (candidatos: cheques rechazados
BCRA, cantidad de deudores en situación irregular ≥2, morosidad de servicios).
**Para decidir:** elegir candidato y peso interno; el motor renormaliza solo.

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
indicador: un error de fuente se transmite entero al índice.
**Relación:** D5 es el caso urgente (por crítica); D9 es la política general.
**Para decidir:** mínimo de 2 componentes por dimensión como regla, o
aceptar mono-indicador con flag.

## D10 — Taxonomía de dimensiones del ITVC

**Qué (auditoría 04-jul, ADR-0033):**
- "Prospectivas de empleo" no contiene medidas directas de empleo (IPI +
  cemento + subocupación 2,25%); la informalidad —laboral pura— vive en
  Ingresos.
- "Confianza y seguridad" es un cajón mixto: ánimo (ICC), delito (IVI),
  consumo simbólico (carne), durable a crédito (motos), atención (Trends).
- Concentración: la brecha salario/CBT pesa 22,75% del índice ella sola.
**Para decidir:** renombrar dimensiones vs rearmar la asignación
indicador→dimensión vs repesar. Cambia la lectura pública del índice:
decisión editorial, no técnica.

## Resueltas recientemente (para no reabrir)

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
