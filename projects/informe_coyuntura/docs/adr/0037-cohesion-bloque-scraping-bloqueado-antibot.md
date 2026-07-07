# ADR-0037 — cohesion_bloque: scraping directo implementado y correcto, pero bloqueado en producción por detección de bots de HCDN

| | |
|---|---|
| **Estado** | Implementado, bloqueado en producción — revisar cuando exista una vía de acceso alternativa |
| **Fecha** | 2026-07-07 |
| **Ámbito** | `scripts/politica.py` (`indice_rice`, `es_bloque_lla`, `_hcdn_votaciones_session`, `_hcdn_votaciones_get`, `_descubrir_actas`, `_url_acta`, `_parsear_acta`, `fetch_cohesion_bloque`, `_cohesion_desactualizada`) · `data/politica/manuales.json` · `scripts/descargar_series.py` |

## Contexto

`cohesion_bloque` era manual (78%, congelado desde 2026-05-23). Una investigación previa
(workflow de 33 agentes) encontró que el blocker documentado ("requiere headless browser") era
falso a esa fecha: `votaciones.hcdn.gob.ar` era HTML server-rendered, scrapeable sin headless
browser. Se decidió automatizar con scraping directo propio (no depender de `Como_voto`, un
repo de terceros sin licencia formal).

## Qué se construyó (correcto y ya mergeado)

Sesión HTTP con pacing (0.3s, sesión única, evita el WAF F5 por ráfagas) + descubrimiento de
actas por año + parsing de la tabla nominal + índice de Rice de cohesión + guard de frescura
que distingue "sin votos nuevos" (receso legislativo, normal) de "el scraper no llegó al sitio"
(problema real) + backfill 2023→actual. Todo con TDD y revisión de código, dos hallazgos reales
corregidos en el camino:
- El slug de `redirectActa` viene vacío en el 100% de las filas reales → la URL correcta es
  `/votacion/{id}`, no `/votacion/{slug}/{id}` (resuelto con `_url_acta`).
- La tabla real de Diputados tiene 6 columnas, no 3 (foto, nombre, bloque, provincia, voto
  anidado en `<span>`, columna vacía) — el fixture original (por analogía con Senado) estaba
  mal; corregido contra HTML real archivado (Wayback Machine, snapshot 2026-01-15).

## Hallazgo que bloquea la Tarea 11 (validación en producción)

Verificado en vivo desde un runner real de GitHub Actions (no bloqueado por IP, a diferencia
del sandbox de desarrollo):

1. **`requests` + BeautifulSoup**: la respuesta (200 OK, 26KB) es el shell de carga de una SPA
   (`<div id="loading">` con spinner, 0 `<tr>`, 0 `redirectActa`) — no la tabla de resultados.
2. **Headless browser completo (Playwright/Chromium, JS ejecutando)**: la respuesta es una
   página EXPLÍCITA de bloqueo — *"Acceso temporalmente bloqueado — Se detectaron demasiados
   intentos fallidos de verificación. Por favor, intentá nuevamente en 14 minutos y 58
   segundos."* Confirmado que es un muro categórico, no un rate-limit real: se repitió la
   prueba 22 minutos después (bien pasado el plazo anunciado) y apareció el **mismo texto
   estático** — no es un contador que baja, es la respuesta fija que el sitio da a todo cliente
   que su sistema anti-bot marca como sospechoso, sea cual sea el pacing.
3. **Como_voto (terceros) tampoco lo resolvió**: su propio `data/diputados.json` está congelado
   desde 2026-05-21 (7 semanas a la fecha de esta verificación), mientras que su scraping de
   Senado (sitio distinto, `senado.gob.ar`) siguió actualizándose hasta 2026-06-23. Su código
   nunca lanza excepción ante esto (`raise_for_status=False` + except amplios), así que su
   propio workflow diario sigue en verde sin que nadie lo note — mismo patrón de falla
   silenciosa que ya documentó este proyecto con CICCRA (commit `2ec13f5`).

## Decisión

Mergear el código de automatización tal cual (Tareas 1-10 del plan) — es correcto, testeado,
y degrada con gracia al cache/valor anterior sin marcar falsamente `desactualizado` cuando el
sitio está inaccesible (Tarea 7). El indicador queda con el mecanismo de automatización listo
pero **sin datos reales fluyendo** hasta que se resuelva el acceso — no se intenta ningún
bypass del muro anti-bot (proxies, CAPTCHA-solving, rotación de IP): son técnicas que violan
los términos de uso del sitio y no son el estilo de este proyecto.

## Caminos a evaluar en una revisión futura (ninguno intentado todavía)

1. **Gestión institucional directa con HCDN** (mencionado como opción en la investigación
   original) — pedir acceso a datos abiertos de votaciones nominales vigentes, o un dataset
   CKAN actualizado (el actual está congelado en período 137/2019).
2. **Monitoreo pasivo de Como_voto**: si en algún momento su `diputados.json` vuelve a
   actualizarse con normalidad, señal de que encontraron una vía — revisar su código de nuevo
   en ese momento.
3. **Re-test periódico** (ej. trimestral): las configuraciones anti-bot cambian; lo que está
   bloqueado hoy puede no estarlo en unos meses (como pasó al revés: enero-2026 estaba abierto,
   julio-2026 no).
4. **`cohesion_bloque_senado`** (plan ITCP, ADR-0036) es una vía independiente — Senado es un
   sitio distinto sin evidencia de este mismo bloqueo — no depende de que esto se resuelva.

## Opciones descartadas

- **Headless browser (Playwright) como solución**: probado y descartado — el sitio bloquea
  clientes automatizados categóricamente, con o sin ejecución de JS.
- **Depender de Como_voto como fuente**: descartado — está en el mismo problema, solo que no
  lo sabe (falla silenciosa).
- **Técnicas de evasión de la detección anti-bot** (proxies residenciales, rotación de
  fingerprint, resolución de CAPTCHA): descartado por decisión editorial — fuera del estilo del
  proyecto y de los términos de uso del sitio.

## Consecuencias

- `cohesion_bloque` publica desde cache/último valor conocido indefinidamente hasta que se
  resuelva el acceso — riesgo real de un indicador "congelado" por un período largo, pero
  preferible a fabricar un dato o a depender de una fuente derivada igualmente bloqueada.
- Documentado explícitamente para que una futura sesión no vuelva a probar requests directos ni
  headless browser sin saber que ya se intentaron y fallaron por esta razón específica.
