---
madr: 4
id: '0039'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_cohesion_bloque_senado_actas_anio, fetch_cohesion_bloque_senado_mensual]
parametros: ['BANDAS_ITCP["cohesion_bloque_senado"]', 'G3_EXCEPCIONES']
archivos: ['scripts/itcp.py', 'scripts/politica.py', _agregar_cohesion_ventana, 'scripts/descargar_series.py', _actas_cohesion_senado_cacheadas, 'scripts/gate_calidad.py', 'data/politica/cohesion_bloque_senado_actas.json', 'tests/test_itcp.py', 'tests/test_politica_cohesion.py', 'tests/test_descargar_series_cohesion.py']
ambito: '`scripts/itcp.py` (`BANDAS_ITCP["cohesion_bloque_senado"]`) · `scripts/politica.py` (`fetch_cohesion_bloque_senado_actas_anio`, `_agregar_cohesion_ventana`) · `scripts/descargar_series.py` (`_actas_cohesion_senado_cacheadas`, `fetch_cohesion_bloque_senado_mensual`) · `scripts/gate_calidad.py` (`G3_EXCEPCIONES`) · `data/politica/cohesion_bloque_senado_actas.json` · `tests/test_itcp.py`, `tests/test_politica_cohesion.py`, `tests/test_descargar_series_cohesion.py`'
---

# ADR-0039 — cohesion_bloque_senado: recalibración de anclas ITCP con backfill mensual real

## Contexto y planteo del problema

Mismo hallazgo que ADR-0038, en un indicador con mayor impacto en el índice.
`cohesion_bloque_senado` (alta 2026-07-07) heredó las anclas de banda de
`cohesion_bloque` (Diputados) sin validarlas: 90/75/60/40. Esas anclas nunca
se ajustaron para el Senado, y `cohesion_bloque` (Diputados) sigue sin datos
propios porque su scraping está bloqueado por el anti-bot de HCDN
(ADR-0037) — mientras eso siga así, `cohesion_bloque_senado` es el ÚNICO
insumo real de la dimensión "cohesión interna" (20% del ITCP): su
calibración no afecta solo a su propio peso (7%), afecta a un quinto del
índice completo.

Aplicando el mismo procedimiento de ADR-0038 (backfill mensual real antes de
tocar las anclas): con la card live en 99,4%, el indicador publicaba
"0,0/10 de tensión" — la banda superior abierta `(90, ∞, 100)` aplana
cualquier valor por encima de 90 a puntaje pleno.

## Opciones consideradas

- **Mantener las anclas de Diputados también para el Senado** — descartada:
  es exactamente el problema que este ADR corrige; las dos cámaras tienen
  bloques de tamaño y dinámica muy distintos (el propio texto público del
  indicador ya lo advierte: "un bloque chico hace que un solo voto
  disidente mueva el promedio con más fuerza").
- **Recalibrar también `cohesion_bloque` (Diputados) por simetría** —
  descartada: no tiene serie real propia (bloqueado desde ADR-0037), 
  recalibrar sin datos sería inventar anclas, no derivarlas.
- **Rellenar la banda vacía (80–85) con una ancla intermedia inventada** —
  descartada: sin un punto real ahí, cualquier número sería arbitrario; se
  deja el hueco explícito en vez de fingir precisión.

## Decisión

Recalibrar `BANDAS_ITCP["cohesion_bloque_senado"]` a anclas 95/90/85/80
(números redondos, chequeados contra los 29 puntos reales: 12/13/3/0/1
meses por banda — la banda 80–85 queda vacía, no hay datos ahí; se conserva
como margen hasta que aparezcan, mismo criterio que el resto de las tablas
del ITCP):

```
(95.0, INF, 100), (90.0, 95.0, 85), (85.0, 90.0, 65), (80.0, 85.0, 40), (-INF, 80.0, 10)
```

Tramos extremos ABIERTOS, mismo motivo que ADR-0038 (el motor interpolado
ancla las bandas abiertas en su borde finito, no en un punto medio
artificial).

`cohesion_bloque` (Diputados) **NO se toca** — sigue con las anclas 90/75/60/40
heredadas, marcado PROVISIONAL, hasta que tenga datos propios (bloqueado por
ADR-0037).

Efecto inmediato: el valor live (99,4%) sigue en el techo (dentro del rango
real observado, 99,4 es genuinamente parte del 20% superior de la
distribución) — pero un valor típico de la franja 90–95% (ej. sep-2024,
92,8%), que antes saturaba en 100, ahora puntúa 86,8.

### Consecuencias

- Segunda banda del ITCP en salir del estado PROVISIONAL con datos propios
  (después de `alineamiento_senadores_prov`, ADR-0038) — mismo precedente:
  cuando `cohesion_bloque` (Diputados) o `adhesion_reformas_provincial`
  acumulen recorrido, este es el procedimiento a repetir.
- La dimensión "cohesión interna" del ITCP deja de estar prácticamente
  aplanada en 100 la mayor parte del tiempo — su tensión ahora refleja mejor
  la variación real de la cohesión del bloque en el Senado, con impacto
  directo en el 20% del índice mientras Diputados siga sin dato.
- `data/politica/cohesion_bloque_senado_actas.json` (detalle crudo por
  acta) queda versionado, mismo criterio que ADR-0038.
- `scripts/gate_calidad.py::G3_EXCEPCIONES` suma `cohesion_bloque_senado`
  (mismo motivo que `alineamiento_senadores_prov`: card y serie usan ambas
  ventana de 90 días, pero ancladas a fechas distintas — hoy vs. fin de mes).

## Más información

### Backfill

Reusando la infraestructura de ADR-0038 (mismo patrón: detalle crudo por
acta factorizado del fetch live, agregador puro por ventana, caché anual
persistente, derivación de un punto por fin de mes) — `politica.py`/
`descargar_series.py` ganaron el mismo trío de funciones para cohesión:
`fetch_cohesion_bloque_senado_actas_anio`, `_agregar_cohesion_ventana`,
`_actas_cohesion_senado_cacheadas`/`fetch_cohesion_bloque_senado_mensual`.

Backfill real corrido 2026-07-09: ~280 actas del Senado (22 en 2023, 89 en
2024, 89 en 2025, 80 en 2026 a la fecha) → **29 puntos mensuales reales,
feb-2024→jun-2026**.

### Distribución real observada

Rango 77,8–100,0 · media 94,4 · mediana 93,1 · p25 92,2 · p75 99,8.

Con las anclas viejas (90/75/60/40): el techo `>90→100` saturaba en **25 de
29 meses (86%)** — la inmensa mayoría del tiempo, no un caso de borde. Los
pisos `60–75→65` y `40–60→40` nunca se tocaron (0/29): el mínimo real
observado es 77,8% (ago-2025), muy por encima del "moderado"/"bajo" que
suponían esas bandas.
