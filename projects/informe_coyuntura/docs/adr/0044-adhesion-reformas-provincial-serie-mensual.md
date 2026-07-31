---
madr: 4
id: '0044'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_adhesion_reformas_provincial_serie]
archivos: ['data/politica/adhesion_reformas_provincial_fechas.json', 'scripts/politica.py', _provincias_adheridas_rigi, 'scripts/descargar_series.py', 'scripts/itcp.py', 'tests/test_descargar_series_adhesion.py']
ambito: '`data/politica/adhesion_reformas_provincial_fechas.json` (nuevo) · `scripts/politica.py` (`_provincias_adheridas_rigi` factorizada) · `scripts/descargar_series.py` (`fetch_adhesion_reformas_provincial_serie` reescrita) · `scripts/itcp.py` (comentario de banda, sin cambio de anclas) · `tests/test_descargar_series_adhesion.py`'
---

# ADR-0044 — adhesion_reformas_provincial: serie mensual real vía investigación manual de fechas provinciales

## Contexto y planteo del problema

`adhesion_reformas_provincial` (% de provincias, sobre 24, adheridas
formalmente al RIGI — Título VII, Ley 27.742) era la última banda del ITCP
que seguía PROVISIONAL, con un solo punto en el chart web (el valor actual)
en vez de una serie histórica. La razón documentada hasta hoy: la fuente
(tabla de MAGyP) no tiene fecha de adhesión por provincia, y la única
fuente alternativa con esa fecha (trivia.consejo.org.ar) devuelve "Request
Rejected" (WAF) ante fetch directo — mismo patrón categórico que bloqueaba
a Diputados antes de ADR-0040.

A diferencia de Diputados (un único sitio con un endpoint alternativo
esperando a ser encontrado), acá no existe NINGÚN endpoint único: cada
provincia adhirió con su propia ley, sancionada por su propia legislatura y
publicada en su propio Boletín Oficial — 16 fuentes provinciales distintas,
sin scraper genérico posible. La única vía real es investigar cada una a
mano.

## Opciones consideradas

- **Dejar el punto único, sin serie histórica** (statu quo) — descartada
  por la regla de proyecto de no sentarse sobre gaps sin datos cuando
  investigarlos es viable, y por ser la única banda del ITCP que seguía en
  ese estado.
- **Recalibrar las anclas junto con la serie**, mismo patrón que las otras
  4 de hoy — descartada explícitamente: ver razonamiento del "trinquete" en
  la Decisión. Recalibrar ahora ancla las bandas a un punto de partida que
  quedaría obsoleto apenas sigan adhiriendo provincias.
- **Scraper genérico contra las 16 fuentes provinciales** — descartada por
  desproporcionada: 16 sitios con estructuras completamente distintas, sin
  patrón común reutilizable (a diferencia de HCDN/Senado, que sí comparten
  la misma plataforma de votaciones). Investigación manual, una vez, es más
  barata que mantener 16 parsers distintos para un dataset que crece a lo
  sumo un puñado de eventos por año.

## Decisión

Se investigaron las 16 provincias (de 24) que figuran en la tabla MAGyP,
una por una, vía búsqueda web con fuentes oficiales (Boletín Oficial
provincial, portal de la legislatura provincial) como fuente primaria y
prensa como corroboración cuando el sitio oficial no fue accesible sin
evadir ninguna protección (dos casos: Misiones, cuyo Boletín Oficial no
permitió fetch directo — resuelto con dos fuentes de prensa independientes
que coinciden en fecha y número de ley; trivia.consejo.org.ar, bloqueado
por WAF, usado solo como corroboración cruzada en San Juan, no como fuente
única). Ninguna protección de acceso fue evadida — cuando un sitio bloqueó
el acceso, se buscó una fuente distinta, nunca un bypass.

El resultado (fecha, criterio — publicación en Boletín Oficial o, si no se
encontró, sanción/promulgación —, confianza, ley, fuente) quedó en
`data/politica/adhesion_reformas_provincial_fechas.json`, un dataset
**investigado manualmente, no auto-scrapeado** (mismo espíritu que
`data/gestion/rigi_fechas.json`, aunque ese sí se auto-completa vía scraper
porque el RIGI de proyectos SÍ tiene un endpoint único por norma).

`fetch_adhesion_reformas_provincial_serie()` cruza el set de provincias
adheridas HOY (`politica._provincias_adheridas_rigi()`, factorizada del
fetch live existente) contra este dataset, y construye un punto por fin de
mes con el % acumulado de provincias con fecha conocida ≤ ese mes. Provincias
que aparezcan en el futuro sin fecha investigada quedan excluidas del
histórico (con un `[WARN]` en consola) hasta que se las investigue a mano y
se agreguen al dataset — siguen contando en el valor LIVE de la card
igual, que sigue re-leyendo la tabla MAGyP fresca en cada corrida y no
depende de este dataset para nada.

**Las anclas de banda (80/60/40/20) NO se tocaron** — a diferencia de las
otras 4 recalibraciones de hoy (ADR-0038/0039/0042/0043), acá el chequeo
contra los 24 puntos reales (4,2%→66,7%, jul-2024→jun-2026) no encontró
saturación ni aplanamiento: el puntaje interpolado se mueve de verdad en
todo el rango observado (10→82). La razón de fondo: la adhesión al RIGI es
IRREVERSIBLE por provincia (un trinquete, no una tasa que puede subir o
bajar), así que el rango de hoy es el arranque de un proceso todavía en
curso, no una muestra representativa de su rango final contra la cual
calibrar anclas permanentes.

### Consecuencias

- `adhesion_reformas_provincial` tiene resolución mensual real (24 puntos)
  en vez de 1 punto — misma familia de fix que los otros 3 indicadores de
  política hoy, pero llegando ahí por investigación manual en vez de
  backfill automatizado.
- El dataset de fechas es un artefacto MANUAL: si una provincia nueva
  adhiere, no se descubre sola — hay que investigar su fecha y agregarla a
  `adhesion_reformas_provincial_fechas.json` con el mismo criterio (ver
  `_meta` del archivo). Mientras eso no pase, el histórico queda un mes
  atrás de la card para esa provincia puntual (documentado también en el
  docstring de la función) — deliberadamente NO se agregó una excepción en
  `G3_EXCEPCIONES` de gate_calidad.py para este caso: si algún día aparece
  el desfasaje, G3 debe fallar y avisar, no quedar silenciado de antemano.
- El campo "ley" de Tucumán en el dataset corrige un error real de la tabla
  fuente de MAGyP (esa fila cita "Ley ASIP N° 3912", copiada por error de
  la fila de Santa Cruz — verificado que el hipervínculo real de esa fila
  apunta a la Ley 9803/2024, la adhesión real de Tucumán). No se reporta a
  MAGyP como parte de este ADR; queda anotado acá por si alguna vez se
  vuelve relevante.
