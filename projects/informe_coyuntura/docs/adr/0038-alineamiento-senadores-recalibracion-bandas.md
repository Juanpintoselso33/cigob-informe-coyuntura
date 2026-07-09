# ADR-0038 — alineamiento_senadores_prov: recalibración de anclas ITCP con backfill mensual real

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Ámbito** | `scripts/itcp.py` (`BANDAS_ITCP["alineamiento_senadores_prov"]`) · `scripts/politica.py` (`fetch_alineamiento_senadores_actas_anio`, `_agregar_alineamiento_ventana`) · `scripts/descargar_series.py` (`_actas_alineamiento_cacheadas`, `_fines_de_mes`, `fetch_alineamiento_senadores_prov_mensual`) · `data/politica/alineamiento_senadores_actas.json` · `tests/test_itcp.py`, `tests/test_politica_cohesion.py`, `tests/test_descargar_series_cohesion.py` |

## Contexto

`alineamiento_senadores_prov` (alta 2026-07-08, ver ADR-0036/0037) heredó las anclas de
banda de `gobernadores_alineamiento` (65/45/25/10) sin validarlas contra datos propios — el
comentario original en `itcp.py` ya las marcaba PROVISIONAL, "a recalibrar cuando el backfill
esté corriendo". El indicador solo tenía 4 puntos ANUALES (un valor por año, ventana de 366
días, `data/politica/alineamiento_senadores_serie.json`), resolución insuficiente para evaluar
si el techo de 65% era razonable.

Disparador concreto: con el valor live de julio (68,3%), la card publicaba "0,0/10 de tensión".
Al revisar por qué, se encontró que 68,3% cae en la banda superior abierta `(65, ∞, 100)`, que
aplana a puntaje pleno cualquier valor por encima de 65 sin distinguir 66% de 100%. Con el
lanzamiento público del informe fijado para agosto de 2026, no había margen para dejar el gap
"a recalibrar cuando haya más historia" sin resolver.

## Qué se construyó para poder decidir con datos

Antes de tocar las anclas, se construyó la infraestructura para backfillear resolución MENSUAL
(no solo anual) sin gastar scraping de más:

- `politica.fetch_alineamiento_senadores_actas_anio(anio)`: detalle CRUDO por acta de un año
  completo (fecha + resultado por provincia), factorizado de `fetch_alineamiento_senadores_prov`
  sin modificarla (cero riesgo para el valor live diario, que sigue pidiendo solo las actas
  dentro de su ventana de 90 días).
- `politica._agregar_alineamiento_ventana(detalle, referencia, dias_ventana)`: función pura que
  agrega ese detalle crudo en cualquier ventana arbitraria — misma fórmula que el valor live.
- `descargar_series._actas_alineamiento_cacheadas` / `_fines_de_mes` /
  `fetch_alineamiento_senadores_prov_mensual`: cachean el detalle crudo por año
  (`data/politica/alineamiento_senadores_actas.json`, años cerrados inmutables, mismo criterio
  que `_serie_cohesion_cacheada`) y derivan un punto por CADA fin de mes con ventana rolling de
  90 días (misma definición "Continua (90d)" que ya muestra la card) — una sola pasada de
  scraping por año, no una por mes.

Backfill real corrido 2026-07-09: ~276 actas del Senado (18 en 2023, 89 en 2024, 89 en 2025, 80
en 2026 a la fecha) → **29 puntos mensuales reales, feb-2024→jun-2026**.

## Distribución real observada

Rango 19,4–100,0 · media 56,9 · mediana 57,7 · p25 46,0 · p75 69,3.

Con las anclas viejas (65/45/25/10): el techo `>65→100` saturaba en **8 de 29 meses (28%)** —
no un caso de borde, casi 1 de cada 3 meses reales quedaban indistinguibles entre sí pese a
valores muy distintos (66% y 100% puntúan igual). El piso `≤10→10` casi no se tocaba (0/29;
solo ago-2025, con 19,4, cayó en la banda 10–25).

## Decisión

Recalibrar `BANDAS_ITCP["alineamiento_senadores_prov"]` a anclas 70/60/50/40 (números redondos,
chequeados contra los 29 puntos reales: 6/6/6/7/4 meses por banda, casi equidistribuido):

```
(70.0, INF, 100), (60.0, 70.0, 85), (50.0, 60.0, 65), (40.0, 50.0, 40), (-INF, 40.0, 10)
```

Los tramos extremos se mantienen ABIERTOS (INF/-INF), mismo criterio que el resto de las bandas
del ITCP: un tramo superior finito `(70,100,100)` desplazaría el ancla del motor interpolado
(ADR-0021) al punto medio (85 en vez de 70) — mismo gotcha que ya documentaba el comentario
original de esta tabla antes de este cambio.

Efecto inmediato: el valor live de julio (68,3%) pasa de puntaje interpolado 100,0 (tensión 0,0)
a **94,9 (tensión 0,5)** — deja de caer en el techo plano.

## Opciones consideradas

- **Esperar a acumular más historia antes de recalibrar** — descartada: el lanzamiento público
  es en agosto 2026, sin margen para dejar bandas sin validar (decisión explícita del usuario,
  2026-07-09).
- **Bandas por cuantiles exactos de la muestra** (p20/p40/p60/p80 = 44,9/50,6/60,9/70,2) —
  descartada a favor de números redondos (40/50/60/70): la diferencia práctica es mínima (la
  distribución queda casi igual de equilibrada) y los redondos son más legibles/institucionales,
  consistente con el resto de las tablas del ITCP.
- **Ventana anual (366 días) para los puntos de backfill, igual que `cohesion_bloque_senado`** —
  descartada para ESTE indicador: la card ya publica "Continua (90d)" como frecuencia; calibrar
  con una ventana distinta a la que muestra el valor live hubiera sido inconsistente. Puede
  seguir siendo la elección correcta para otros indicadores de Senado que no comparten esa
  convención (fuera de alcance de este ADR).

## Consecuencias

- Primera banda del ITCP en salir del estado PROVISIONAL con **datos propios** en vez de anclas
  heredadas de otro indicador — precedente para cuando `cohesion_bloque` / `cohesion_bloque_senado`
  / `adhesion_reformas_provincial` / `protestas_caba` acumulen recorrido suficiente (siguen
  PROVISIONAL, ver ADR-0036).
- La infraestructura de backfill mensual (`fetch_alineamiento_senadores_prov_mensual`) queda
  disponible pero **NO** está wireada al pipeline diario ni al chart web — se usó puntualmente
  para calibrar. Si se quiere subir la resolución del gráfico público de este indicador (hoy la
  card usa la serie ANUAL, `fetch_alineamiento_senadores_prov_serie`), es un paso aparte, no
  incluido acá.
- `data/politica/alineamiento_senadores_actas.json` (detalle crudo por acta, ~276 filas) queda
  versionado como insumo reproducible de esta recalibración — permite re-derivar la serie
  mensual con otra ventana sin volver a scrapear el Senado.
