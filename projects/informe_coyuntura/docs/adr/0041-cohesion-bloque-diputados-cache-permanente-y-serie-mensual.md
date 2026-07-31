---
madr: 4
id: '0041'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_cohesion_bloque_diputados_actas_anio, fetch_cohesion_bloque, fetch_cohesion_bloque_diputados_mensual, cohesion_bloque]
parametros: ['POLITICA_DERIVADAS']
archivos: ['scripts/politica.py', _acta_diputados_cacheada, '_cargar/_guardar_cache_cohesion_diputados', _descubrir_actas_diputados_pdf, 'scripts/descargar_series.py', _actas_cohesion_diputados_cacheadas, 'tests/test_politica_cohesion.py', 'tests/test_descargar_series_cohesion.py']
ambito: '`scripts/politica.py` (`_acta_diputados_cacheada`, `_cargar/_guardar_cache_cohesion_diputados`, `fetch_cohesion_bloque_diputados_actas_anio` reescrito, `fetch_cohesion_bloque` reescrito, `_descubrir_actas_diputados_pdf` eliminada) · `scripts/descargar_series.py` (`_actas_cohesion_diputados_cacheadas`, `fetch_cohesion_bloque_diputados_mensual`, `cohesion_bloque` vuelve a `POLITICA_DERIVADAS`) · `tests/test_politica_cohesion.py` · `tests/test_descargar_series_cohesion.py`'
---

# ADR-0041 — cohesion_bloque (Diputados): caché permanente por acta y serie mensual real

## Contexto y planteo del problema

ADR-0040 (2026-07-09, mismo día) desbloqueó `cohesion_bloque` (Diputados)
vía el endpoint PDF directo, pero dejó dos deudas explícitas en su sección
de Consecuencias:

1. `cohesion_bloque` había sido sacado de `POLITICA_DERIVADAS` porque su
   backfill anual caminaba TODA la historia desde el id más reciente en
   cada una de las 4 llamadas por año (~53min extra en el pipeline
   completo, sin caché de por medio).
2. Sin ese backfill, el chart del indicador en la web solo mostraba 3
   puntos ANUALES en vez de una serie mensual real — mismo problema que ya
   se había resuelto para `alineamiento_senadores_prov` (ADR-0038) y
   `cohesion_bloque_senado` (ADR-0039).

Al retomar este trabajo se encontró además un bug real en el código ya
escrito (no llegó a producción): `fetch_cohesion_bloque_diputados_actas_anio`
(y su antecesora `_descubrir_actas_diputados_pdf`) cortaba el walk al
acumular `MARGEN_SALIDA` actas seguidas con `fecha.year != anio` — pero el
walk SIEMPRE arranca desde el id más reciente de HOY, así que pedir un año
pasado (ej. 2023, con el walk arrancando en actas de 2026) topaba con 5
actas "de año equivocado" de entrada y cortaba antes de llegar siquiera a
2023. El único test existente (`anio == año del id_maximo`) no ejercitaba
ese camino y no lo detectó.

## Opciones consideradas

- **Dejar `cohesion_bloque` fuera de `POLITICA_DERIVADAS` indefinidamente**
  (mantener el estado post-ADR-0040) — descartada: el usuario señaló
  explícitamente que el chart mostraba solo 3 puntos anuales y que el
  próximo paso lógico, ahora que existe la caché, es tener resolución
  mensual real como los otros dos indicadores de la misma familia.
- **Cachear solo las actas CON señal** (como se había escrito en un primer
  borrador de `_acta_diputados_cacheada`) — descartada: una corrida
  repetida seguiría re-descargando cualquier acta sin señal cada vez,
  contradiciendo el pedido explícito de que "la próxima corrida solo baje
  lo no cacheado".

## Decisión

**Caché permanente por acta** (`data/politica/cohesion_bloque_diputados_actas_cache.json`,
versionada en git igual que `cohesion_bloque_senado_actas.json`/
`alineamiento_senadores_actas.json` — necesario para que la caché sobreviva
entre corridas del cron nocturno, que arranca de un checkout limpio en cada
ejecución: si el archivo no se commitea, "no volver a descargar lo ya
visto" solo valdría DENTRO de una misma corrida, no entre corridas): una
vez publicada, una acta no cambia — se cachea `{fecha, rice}` indexado por id,
con `rice=None` cuando el bloque LLA no aporta señal (empate o sin
presentes), para que un walk repetido NUNCA vuelva a descargar la misma
acta sin importar cuántas veces la vuelva a pisar (backfill de 4 años +
corridas diarias del valor live). Solo un 404 (puede ser transitorio) o un
PDF sin fecha legible quedan sin cachear.

**Bug de año corregido**: el corte por margen de salida ahora solo cuenta
actas con `fecha.year < anio` (ya pasamos el año pedido); las de
`fecha.year > anio` se saltean sin contar (todavía viajando desde HOY hacia
atrás). Test de regresión agregado
(`test_fetch_cohesion_bloque_diputados_actas_anio_anio_pasado_no_corta_de_mas`)
reproduce exactamente el escenario que fallaba.

**Serie mensual**: `_actas_cohesion_diputados_cacheadas` (caché por AÑO del
detalle crudo, mismo patrón que `_actas_cohesion_senado_cacheadas`) +
`fetch_cohesion_bloque_diputados_mensual` (reusa `politica._agregar_cohesion_ventana`,
ya genérica desde ADR-0039) — mismo patrón exacto que Senado y
alineamiento, ahora viable porque la caché por acta hace que recorrer años
ya vistos sea O(dict lookups), no O(descargas).

`cohesion_bloque` vuelve a `POLITICA_DERIVADAS`, registrado directamente
con `fetch_cohesion_bloque_diputados_mensual` (igual que
`cohesion_bloque_senado`/`alineamiento_senadores_prov` — la variante
`_serie` anual queda sin usar ahí, mismo estado que sus pares de Senado).

`fetch_cohesion_bloque` (valor live, ventana de 90 días) también fue
reescrita para usar la caché por acta — el cron nocturno y cualquier
corrida manual repetida ya no vuelven a descargar actas ya vistas, solo las
nuevas desde la corrida anterior.

`_descubrir_actas_diputados_pdf` (la función SPA-independiente pero sin
caché que hacía este mismo trabajo antes) queda eliminada: su único caller
era `fetch_cohesion_bloque_diputados_actas_anio`, ya reescrita, y tenía el
mismo bug de año sin corregir.

**Hallazgo real al revisar cómo persiste la caché entre corridas del cron
(2026-07-09)**: `.github/workflows/data-pipeline.yml` commitea el snapshot
diario con una lista EXPLÍCITA de archivos (`git add <lista>`), y esa lista
nunca incluyó nada de `data/politica/` — ni siquiera los cachés de
`cohesion_bloque_senado_actas.json`/`alineamiento_senadores_actas.json` que
ya existían desde ADR-0038/0039. Sin esto, cada corrida del cron arrancaba
de un checkout donde el año en curso NUNCA tenía caché (el cron nunca
empujaba de vuelta lo que había descargado esa noche), así que recorría el
año en curso desde cero cada vez — la caché por año solo beneficiaba
corridas manuales dentro de una misma sesión, no al cron real. Corregido
agregando los 4 archivos de caché de política (los 2 ya existentes + los 2
nuevos de este ADR) a la lista de `git add` del workflow — esto también
repara retroactivamente el beneficio de caché prometido por ADR-0038/0039
para el cron nocturno, no solo para este indicador nuevo.

**De paso** (pedido explícito del usuario en la misma sesión): estandarizadas
las etiquetas y textos de `cohesion_bloque` vs. `cohesion_bloque_senado`
(`datos.ts`, `descripciones.ts`, `fichas.ts`) — la card de Diputados no
tenía calificador de cámara mientras la de Senado sí decía "(Senado)".

### Consecuencias

- `cohesion_bloque` tiene ahora resolución mensual real en el chart web
  (esperado: ~29-31 puntos, feb-2024 a jun-2026, mismo rango que Senado/
  alineamiento) en vez de 3 puntos anuales.
- El backfill inicial (primera corrida que puebla la caché desde cero)
  paga el costo real de recorrer la historia completa una única vez — las
  corridas siguientes (cron nocturno incluido) son baratas.
- Sus anclas (90/75/60/40) quedaban PROVISIONALES al cierre de este ADR —
  recalibradas unas horas después, mismo día, en ADR-0042 (mismo criterio
  que ADR-0038/0039), una vez disponible la serie mensual construida acá.
- El archivo de caché por acta (`cohesion_bloque_diputados_actas_cache.json`)
  y el de detalle por año (`cohesion_bloque_diputados_actas.json`) son
  artefactos derivados, no fuente de verdad — si el endpoint PDF cambia de
  estructura, se pueden borrar y reconstruir desde cero (más lento, pero
  correcto) sin perder nada irrecuperable.
