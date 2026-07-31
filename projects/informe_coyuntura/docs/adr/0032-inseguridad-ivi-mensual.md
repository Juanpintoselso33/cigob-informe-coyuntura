---
madr: 4
id: '0032'
estado: 'aceptado'
fecha: 2026-07-04
cinturon: 'vida'
indicadores: [inseguridad]
ambito: 'Indicador `inseguridad` (30% de Confianza = 4,5% del ITVC)'
---

# ADR-0032 — Inseguridad: del SNIC anual al IVI mensual (LICIP-UTDT)

| **Disparador** | Barrido vida 10/13: el editor exigió investigar granularidad mejor que la anual |

## Contexto y planteo del problema

`inseguridad` puntuaba con el SNIC: total anual de hechos delictivos
denunciados (un dato por año, publicado en junio). La investigación de
alternativas encontró que el **Índice de Victimización (IVI)** del LICIP
(Universidad Di Tella — la misma casa del ICC y el ICG que ya usamos) está
vivo y es **mensual**: encuesta de hogares en 40 centros urbanos, pregunta
por delitos sufridos en los últimos 12 meses, denunciados o no.

Rutas investigadas y descartadas: bases SAT del Ministerio (mensuales pero
publicadas en tandas anuales cada diciembre, un año detrás del consolidado,
solo subconjuntos de delitos); fuentes jurisdiccionales mensuales (CABA:
cambia el alcance nacional); SNIC mensual (no existe).

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. **La métrica del ITVC pasa al IVI mensual**, invertido, con **base
   DECLARADA en enero 2024** — la primera medición tras la reanudación de la
   encuesta (suspendida 2020-2023, verificado en el archivo de informes: los
   PDF saltan de mar-2020 a ene-2024). No existe medición del 4T-2023; la
   ventana de 12 meses de la pregunta de ene-2024 cubre mayormente el año
   previo al mandato, así que aproxima bien el arranque.
2. **El SNIC anual queda como CONTRASTE declarado**: en el detalle de la card
   (hechos denunciados del año) y como serie propia (`inseguridad_snic`, con
   su store resiliente del mismo día). Registrado vs declarado: cuando
   divergen — como hoy: denuncias bajando, victimización subiendo desde
   mediados de 2025 — la divergencia es información (la cifra negra crece).
3. **Serie con store persistente** (`ivi_serie.json`): los PDFs mensuales del
   LICIP tienen URL por hash; cada corrida descubre los nuevos desde el
   listado del sitio UTDT, parsea la primera página (patrón verificado en
   informes de 2020, 2025 y 2026) y acumula. Backfill completo hecho:
   31 informes procesados, ene-2024 → abr-2026 continuos.

### Consecuencias

- Card: 2.418.600 hechos/año (2025) → **28,0% de hogares víctimas
  (abr-2026)**; B100 100,7 → **102,1**; ITVC 91,4 → 91,5.
- El indicador gana el gráfico mensual (28 meses desde el mandato) y pierde
  la excepción de frecuencia anual del doc.
- La divergencia IVI↑ / SNIC↓ queda visible y explicada en la ficha.

## Más información

### Ventajas del constructo

- **Mide lo que la gente sufre, no lo que denuncia** — para un cinturón de
  vida cotidiana es el constructo correcto (la tasa de denuncia es baja y
  variable, como advierte el propio LICIP).
- Mensual con ~1-2 meses de rezago (vs anual con 6).
- Sin estacionalidad por construcción (ventana móvil de 12 meses).
- Fuente académica de la misma familia que ya puntúa en el cinturón (UTDT).

### Declarables

- Error muestral ±3% mensual (~1.000 hogares); la ventana 12m suaviza.
- Cobertura: 40 centros urbanos (no rural).
- Base ene-2024 en lugar del 4T-2023 del doc — declarada en la fórmula
  publicada y en este ADR.
