---
madr: 4
id: '0040'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_cohesion_bloque_diputados_actas_anio, fetch_cohesion_bloque]
archivos: ['scripts/politica.py', _parsear_acta_diputados_pdf, _diputados_acta_fecha, _diputados_acta_pdf, _diputados_acta_id_maximo, _descubrir_actas_diputados_pdf, 'tests/test_politica_cohesion.py', 'tests/fixtures/acta_diputados_5959.pdf']
ambito: '`scripts/politica.py` (`_parsear_acta_diputados_pdf`, `_diputados_acta_fecha`, `_diputados_acta_pdf`, `_diputados_acta_id_maximo`, `_descubrir_actas_diputados_pdf`, `fetch_cohesion_bloque_diputados_actas_anio`, `fetch_cohesion_bloque` reescrito) · `tests/test_politica_cohesion.py` · `tests/fixtures/acta_diputados_5959.pdf`'
---

# ADR-0040 — cohesion_bloque (Diputados): desbloqueado vía endpoint PDF directo, sin evadir el anti-bot de la SPA

## Contexto y planteo del problema

ADR-0037 (2026-07-07) documentó que `cohesion_bloque` (Diputados) tiene el
scraper implementado y correcto pero **bloqueado en producción**: la SPA de
`votaciones.hcdn.gob.ar` devuelve un shell de carga sin JS y, con headless
browser, un bloqueo explícito de anti-bot. El ADR dejó 4 caminos "a
evaluar" (gestión institucional, monitoreo pasivo de terceros, re-test
periódico, cohesion_bloque_senado como vía independiente) y descartó
explícitamente cualquier técnica de evasión (proxies, rotación de
fingerprint, resolución de CAPTCHA) por decisión editorial.

**Este ADR no evade nada de eso.** El usuario encontró en vivo que el
propio sitio sirve el PDF de cada acta en un endpoint DISTINTO
(`votaciones.hcdn.gob.ar/pdf/acta/{id}`) que no pasa por la SPA ni por su
protección: HTTP 200 directo, sin JavaScript, sin bloqueo, con una petición
GET común. Es una ruta de acceso pública y legítima del mismo sitio, no un
bypass — el hallazgo fue "hay otra puerta", no "cómo forzar esta puerta".

## Opciones consideradas

- **Evadir el anti-bot de la SPA** (proxies, fingerprint, CAPTCHA) —
  rechazada explícitamente, dos veces, en esta sesión. No es lo que hace
  este ADR.
- **Reusar el listado `_descubrir_actas` (SPA) solo para ids, y el PDF solo
  para contenido** — descartada: la SPA sigue devolviendo el shell sin JS,
  no expone ningún id ahí tampoco.
- **Buscar un listado id↔fecha en otro endpoint del mismo dominio** — no
  investigado a fondo por tiempo; si existe, simplificaría
  `_descubrir_actas_diputados_pdf` (hoy paga una descarga completa por
  fecha). Queda anotado como mejora futura, no bloqueante.

## Decisión

Reemplazar el mecanismo de descubrimiento/parseo de `fetch_cohesion_bloque`
por uno basado en el endpoint PDF:

- `_parsear_acta_diputados_pdf`: el PDF no tiene tabla con bordes
  detectable por `pdfplumber.extract_tables()` (solo encuentra el bloque de
  metadata) — se agrupan palabras por fila (mismo `top`) y se cortan
  columnas donde el hueco horizontal supera ~15pt (~2pt dentro de una
  columna vs. 50-120pt entre columnas, medido en vivo). El título
  decorativo del PDF viene con cada carácter duplicado (fuente en negrita
  simulada del generador) — no hace falta arreglarlo, esas filas no forman
  4 columnas limpias y se descartan solas; la fila de metadata repetida por
  página sí arma 4 columnas por casualidad, se filtra exigiendo que la
  última sea un voto válido.
- `_diputados_acta_id_maximo`: no hay listado id↔fecha, así que se
  descubre el id más reciente caminando desde una semilla conocida
  (5959 = 24-jun-2026, sembrada en el código) hacia adelante hasta el
  primer 404; si la semilla ya no existe, retrocede de a 50 primero.
- `fetch_cohesion_bloque` (live, ventana de 90 días): camina hacia ATRÁS
  desde el id máximo descargando cada acta (no hay forma de conocer la
  fecha sin descargar, a diferencia de Senado que tiene un listado liviano)
  hasta acumular `MARGEN_SALIDA=5` actas seguidas fuera de la ventana.
  Verificado en vivo 2026-07-09: **99,9% de cohesión, 33 actas, dato del
  24-jun-2026** — el indicador vuelve a traer datos reales por primera vez
  desde que se automatizó.
- `_descubrir_actas_diputados_pdf` / `fetch_cohesion_bloque_diputados_actas_anio`:
  mismo patrón de detalle-crudo-por-año que `cohesion_bloque_senado`
  (ADR-0039), para un futuro backfill mensual — construidos y testeados,
  **no ejecutados todavía** (ver Consecuencias).

Las funciones viejas basadas en la SPA (`_descubrir_actas`, `_url_acta`,
`_parsear_acta`) quedan en el código, sin borrar, marcadas como dormidas —
`_parsear_acta` sigue viva de todos modos porque Senado la usa.

### Consecuencias

- `cohesion_bloque` deja de estar en None permanente y vuelve a pesar de
  verdad en la dimensión "cohesión interna" del ITCP (65% de esa dimensión,
  20% del ITCP — hasta ahora corría al 100% sobre `cohesion_bloque_senado`
  en solitario, ver ADR-0039).
- **Sus anclas (90/75/60/40) siguen PROVISIONALES** — no se hizo el
  backfill mensual ni la recalibración que sí se hizo para
  `cohesion_bloque_senado`/`alineamiento_senadores_prov` (ADR-0038/0039).
  La infraestructura para hacerlo (`fetch_cohesion_bloque_diputados_actas_anio`)
  ya está construida y testeada; falta correrla en vivo (potencialmente
  cientos de PDFs, uno por voto histórico, más caro que Senado porque no
  hay listado liviano) y evaluar la distribución real, igual que se hizo
  con los otros dos. Queda como próximo paso, no parte de este ADR.
- **Hallazgo real al correr el pipeline completo por primera vez con este
  cambio (2026-07-09)**: `cohesion_bloque` SÍ estaba registrado en
  `descargar_series.POLITICA_DERIVADAS` desde antes (backfill ANUAL vía
  `fetch_cohesion_bloque_serie` → `politica.fetch_cohesion_bloque(anio,
  dias_ventana=366)`, dormido porque siempre devolvía None mientras estuvo
  bloqueado). Ese patrón asumía `_descubrir_actas` (listado liviano por
  año, SPA) — el fetch nuevo ancla SIEMPRE al id más reciente de HOY sin
  importar `anio`, así que cada una de las 4 llamadas anuales (2023..2026)
  caminaba TODA la historia desde hoy hasta encontrar el año pedido. El
  pipeline completo pasó de ~20 a ~53 minutos por esto solo, con riesgo
  real de superar el `timeout-minutes: 20` del job de CI (rompería el cron
  nocturno, no solo tardar). Corregido sacando `cohesion_bloque` de
  `POLITICA_DERIVADAS` (comentario explicando por qué, en el propio
  archivo) hasta que exista un backfill propio y eficiente — el valor
  live (ventana de 90 días) no se vio afectado, solo el backfill anual.
- El endpoint PDF no está documentado públicamente ni versionado — puede
  cambiar de estructura sin aviso. Si deja de funcionar, `_descubrir_actas`/
  `_url_acta`/`_parsear_acta` (SPA, dormidas) quedan como referencia de lo
  ya investigado, y el ADR-0037 sigue documentando por qué ese camino
  estaba bloqueado.

## Más información

### Verificación en vivo (2026-07-09, antes de escribir código)

- `GET /pdf/acta/5959` → 200, `application/pdf`, 96KB. Confirmado con
  `curl` simple (sin sesión especial, sin headers de evasión) y con varios
  ids más (5900, 5955-5959) — ninguno bloqueado.
- El PDF trae la tabla nominal completa: apellido y nombre, bloque
  político, distrito, voto — mismo contenido que la SPA bloqueada.
- Los ids son un contador GLOBAL secuencial correlacionado con fecha
  (verificado: ids 5955-5959 = 5 votaciones de la sesión del 24-jun-2026;
  id 5900 = 08-abr-2026; ids >5959 dan 404 porque no hay sesión desde
  entonces). No hay un listado público id↔fecha para este endpoint.
- Señal pasiva de que la SPA en sí sigue bloqueada (no se re-probó
  activamente): el scraper de terceros Como_voto, que depende de esa SPA,
  sigue exactamente igual de congelado que en la fecha del ADR-0037 (último
  commit a `diputados.json`: 2026-05-21, sin cambios desde entonces).
