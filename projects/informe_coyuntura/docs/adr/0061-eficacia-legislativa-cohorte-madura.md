# ADR-0061 — eficacia_legislativa: cohorte madura en vez de ventana compartida, anclas contra benchmark histórico externo

| | |
|---|---|
| **Estado** | Aceptado · supersede ADR-0050 |
| **Ámbito** | Cinturón política · ITCP · `eficacia_legislativa` · dimensión `poder_legislativo` |
| **Fecha** | 2026-07-15 |
| **Precedentes directos** | ADR-0050 (superado) · ADR-0059 (mismo criterio de benchmark externo, aplicado hoy mismo a ratio_dnu) · ADR-0045 (recalibración válida de comisiones_caidas, patrón que ADR-0050 invocó sin verificar) |

## Contexto

`eficacia_legislativa` mide % de proyectos del Poder Ejecutivo aprobados.
ADR-0050 diagnosticó correctamente un defecto real en la métrica original:
exigía que la SANCIÓN cayera dentro de la MISMA ventana móvil de 365 días en
que se PUBLICÓ el proyecto — un proyecto enviado hace pocos meses casi nunca
alcanza a completar el trámite legislativo entero (comisión, recinto en
ambas cámaras, promulgación) dentro de lo que resta de esa ventana. ADR-0050
concluyó que "ni un Ejecutivo con mayoría sólida podría acercarse al
35-55%" y recalibró las anclas a 1/3/5/7 contra el rango observado de la
propia serie (0-8,7%, 18 de 32 meses en 0,0 exacto) — **sin comparar ese
diagnóstico con ningún caso externo**, el mismo vacío metodológico que causó
el error de `ratio_dnu` en ADR-0058 (corregido hoy mismo en ADR-0059).

Auditoría de hoy, pedida explícitamente por sospecha de valores "demasiado
bajos": benchmark contra Directorio Legislativo (organización que mide esto
mismo para todas las presidencias desde el retorno democrático) muestra
tasas de éxito legislativo del Ejecutivo muy superiores en gestiones reales:

| Gestión | Tasa de éxito (Directorio Legislativo) |
|---|---:|
| CFK, 2do mandato | 82% (198 proyectos, 163 sancionados) |
| CFK, 1er mandato | 75% (220 proyectos, ~165 sancionados) |
| Alberto Fernández, 1er año | 67% (33 proyectos, 22 sancionados, 63 días de trámite promedio) |
| Macri, sin mayoría en ninguna cámara | 40-50% según el año (91 enviados/37 sancionados en su mandato; 25/50 en 2016) |

Con un trámite típico histórico de 63-112 días, un proyecto publicado en
cualquiera de los primeros ~9-10 meses de una ventana de 12 meses tiene
margen de sobra para completarse — el sesgo de ventana compartida de
ADR-0050 era real, pero mucho menor al que esa ADR asumió sin verificar.

## Decisión

### 1. Reemplazar la ventana compartida por una cohorte madura

En vez de exigir que publicación Y sanción caigan en la misma ventana móvil,
`fetch_eficacia_legislativa()` (`scripts/politica.py`) ahora define:

```text
cohorte_hasta = hoy − 365 días
cohorte_desde = hoy − 730 días
pe_cohorte    = proyectos PE con PUBLICACION_FECHA en [cohorte_desde, cohorte_hasta]
aprobados     = de esa cohorte, los sancionados EN CUALQUIER MOMENTO hasta hoy
                (excluyendo medias sanciones, igual que antes)
valor         = aprobados / |pe_cohorte| × 100
```

Cada proyecto de la cohorte tuvo, como mínimo, 365 días de margen antes de
evaluarse (hasta 730 para los más viejos de la cohorte) — elimina el sesgo
de raíz en vez de compensarlo con anclas más generosas. Costo: el indicador
deja de ser sobre "lo más reciente" — reporta sobre una cohorte de hace
12-24 meses, no sobre el año corriente.

La serie histórica (`fetch_eficacia_serie()`, `scripts/descargar_series.py`)
reutiliza `_hcdn_ventanas_12m()` reinterpretando su `cutoff` como el límite
superior de la cohorte de publicación (antes era el piso de la ventana
compartida), y acota la sanción a lo ocurrido hasta el CIERRE de cada mes
histórico — no hasta hoy — para que un punto ya publicado no cambie
retroactivamente solo porque el proyecto finalmente se sancionó después.

### 2. Recalibrar anclas contra el benchmark externo, no contra el rango de esta gestión

Con la métrica ya sin el sesgo de ventana, el rango real observado (32
meses, dic-2023→jul-2026) es **0-14,8% (mediana 6,5%)** — sigue muy por
debajo de cualquier antecedente histórico. Las anclas nuevas usan los tramos
de Directorio Legislativo como referencia, no el rango de esta gestión:

| Eficacia legislativa (cohorte madura) | Puntaje | Referencia histórica aproximada |
|---:|---:|---|
| > 50% | 100 | CFK/Alberto Fernández (relación fluida) |
| 30-50% | 85 | Macri (gobierno en minoría, pero funcional) |
| 15-30% | 65 | — |
| 5-15% | 40 | mitad de los 32 puntos reales de esta gestión |
| ≤ 5% | 10 | la otra mitad de los 32 puntos reales |

**Que el 100% de la serie real de esta gestión quede en las dos bandas del
piso es intencional, no un error de escala** — a diferencia de ADR-0050 (que
recalibró para que la propia serie se distribuyera "bien" entre las cinco
bandas), acá las bandas altas quedan deliberadamente fuera de alcance de
esta gestión porque **ningún gobierno argentino post-1983 medido por
Directorio Legislativo estuvo, en materia de éxito legislativo del
Ejecutivo, tan por debajo del resto como esta gestión** — eso es
exactamente lo que el indicador debe mostrar.

## Opciones consideradas

### Mantener la ventana compartida y solo re-recalibrar sus anclas

Rechazada. No resuelve el sesgo estructural real (aunque menor de lo que
ADR-0050 asumió) — cualquier recalibración posterior seguiría empujando
contra un numerador artificialmente deprimido por diseño. Corregir la
métrica en la raíz es más robusto que ajustar anclas dos veces.

### Anclas calibradas contra el rango observado de esta gestión (patrón ADR-0050/ADR-0058)

Rechazada por el mismo motivo que ADR-0059 revirtió la recalibración de
`ratio_dnu`: el rango bajo observado (0-14,8%) es desempeño real de esta
administración específica, verificado contra un benchmark externo
(Directorio Legislativo) que muestra que otras gestiones alcanzaron 40-82%
bajo la misma definición de "éxito legislativo del Ejecutivo". Recalibrar
contra el propio historial habría hecho exactamente lo que causó el error
de ADR-0058: definir "buena práctica" como "lo mejor que esta gestión ha
logrado".

### Mantener la cohorte pero fijar las anclas antiguas 5/15/35/55 (pre-ADR-0050)

Considerada. A diferencia de `ratio_dnu` (donde el benchmark externo,
ACIJ, coincidía casi exactamente con las anclas viejas 0,3/0,7/1,2/2,0), acá
las anclas pre-ADR-0050 (5/15/35/55) no tienen un origen externo declarado
— ADR-0050 las describe como "heredadas de la fórmula ad hoc
pre-paramétrica, nunca validadas". Se prefirió derivar anclas nuevas
directamente de los tramos reales de Directorio Legislativo en vez de
reflotar un número sin trazabilidad.

## Limitaciones

- Las anclas (50/30/15/5) son una **estimación razonada** a partir de los
  tramos de Directorio Legislativo, no una calibración estadística
  rigurosa (no se dispone del dato exacto de "% con cohorte madura de 12-24
  meses" para otras gestiones, solo su tasa de éxito eventual sin ese piso
  de maduración) — quedan sujetas a stress test como el resto de las
  anclas de la Paramétrica (ADR-0019).
- El indicador deja de ser sobre el año corriente: reporta el desempeño de
  una cohorte de proyectos de hace 12-24 meses. Es el costo necesario de
  eliminar el sesgo estructural.
- La serie histórica seguirá subestimando levemente el % de cohortes
  recientes en la práctica: un proyecto de la cohorte madura de un mes dado
  puede sancionarse DESPUÉS de la fecha de esa corrida histórica; el punto
  ya publicado no se revisa retroactivamente (ver diseño de
  `fetch_eficacia_serie`), así que la serie es reproducible pero
  conservadora respecto del "éxito eventual" total de cada cohorte.

## Consecuencias

- `fetch_eficacia_legislativa()` y `fetch_eficacia_serie()` cambian de
  fórmula (cohorte madura, no ventana compartida) — nuevos campos
  `cohorte_desde`/`cohorte_hasta`/`dias_madurado_min` en el indicador
  publicado, reemplazan a `ventana_dias` (que describía la semántica vieja).
- `BANDAS_ITCP["eficacia_legislativa"]` cambia de 1/3/5/7 a 50/30/15/5,
  ancladas al benchmark histórico externo de Directorio Legislativo.
- El puntaje de `eficacia_legislativa` para el valor vigente cambia
  materialmente — la dimensión `poder_legislativo` y el ITCP se regeneran
  en la misma corrida scoped, con el fix de ADR-0060 (generar_informe.py ya
  recalcula desde el crudo, no hace falta re-correr el colector solo por
  el cambio de anclas — sí hace falta correrlo porque también cambió la
  FÓRMULA del indicador, que si depende de red).
- Nuevos tests: `tests/test_politica_cohesion.py` (cohorte madura,
  proyecto demasiado reciente excluido) y
  `tests/test_descargar_series_eficacia.py` (reproducibilidad histórica).
- ADR-0050 queda superado; se conserva como registro de la decisión
  anterior (diagnóstico del sesgo estructural correcto, magnitud de la
  recalibración incorrecta por falta de benchmark externo).
