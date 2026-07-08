# Reemplazo de fuente de `movilizacion_cepa` por conflictividad laboral oficial (Secretaría de Trabajo)

## Contexto

Auditoría adversarial del ITCP (2026-07-08) encontró que `movilizacion_cepa` probablemente subestima la conflictividad social real: CEPA cuenta ~101 "conflictos acumulados" desde enero-2026 (todo el año), mientras que un tracker independiente (Huella del Sur / Observatorio de Trabajo y Derechos Humanos, UBA) contó más de 200 eventos en **un solo mes** (junio-2026). Investigación posterior confirmó que los 2 informes de CEPA usados hoy citan específicamente "conflictos laborales de **trabajadores estatales**" — un recorte más angosto que "conflictividad social" en sentido amplio, que es lo que el indicador dice medir según `docs/cinturon_politica.md`.

Se evaluaron 3 fuentes alternativas:

1. **OTDH-UBA** (vía huelladelsur.ar): boletín mensual desde 2024, metodología rigurosa (6 tablas de desglose: región/tipo de medida/motivo/colectivo/DDHH) hasta ~2024, pero degrada a estimación narrativa ("Estimamos 225") sin tablas en 2025-2026. Editor abiertamente militante (aunque las cifras son separables de la prosa).
2. **Secretaría de Trabajo (Ministerio de Capital Humano)** — oficial, `argentina.gob.ar/trabajo/estadisticas/conflictos-laborales`: informes trimestrales desde al menos 2016 (32 informes confirmados), metodología documentada (monitoreo diario de 120+ medios, 10 variables de clasificación: ámbito institucional, actividad económica, localización, tipo de conflicto, tipo de acción, etc.), la propia Secretaría cita series históricas hasta 2006.
3. CEPA (fuente actual): descartada por alcance angosto y ~4 informes irregulares.

**Decisión: usar la Secretaría de Trabajo como fuente.** Es la más rigurosa metodológicamente y con la historia más profunda. Mide específicamente "conflictos **con paro**" (huelga efectiva) — más angosto que "conflictividad social" amplia, pero es un recorte claro y consistente (a diferencia del alcance ambiguo/oscilante de CEPA entre informes). Precedente directo: el proyecto ya usa fuentes oficiales del mismo gobierno para medir su propia gestión en los otros 3 cinturones (INDEC para ITCM, datos.hcdn.gob.ar para ITCG, BCRA para reservas) — se documenta el sesgo conocido, no se descarta la fuente por eso.

**Caveat metodológico real a documentar (no descalificante):** la Ley de Bases (Ley 27.742) encareció legalmente la participación en bloqueos/tomas de establecimiento ("causal objetiva de extinción del contrato de trabajo"), y la propia Secretaría atribuye parte de la baja reciente de conflictividad a este cambio. Esto es un quiebre estructural real en la serie (mismo tipo de nota que la brecha REM o la alícuota efectiva ya tienen en ITCM/ITCG) — se documenta en el ADR, no invalida la fuente.

## Qué se reemplaza

- Indicador renombrado: `movilizacion_cepa` → `conflictividad_laboral_srt` (Secretaría de Trabajo). El nombre viejo queda purgado del histórico (mismo patrón que la purga de `cohesion_bloque` legacy, commit `3973d00`).
- Métrica puntuada: **cantidad de conflictos con paro, por mes** (no acumulado desde enero — mejora adicional: elimina el caveat de "acumulado-desde-enero" que tenía la versión CEPA). Los informes trimestrales de la SRT traen desglose mensual dentro de cada trimestre (confirmado: informe T2-2025 cita "46 conflictos... en junio de 2025", con comparación a mayo-2025 y junio-2024).
- Los 2 puntos ya backfilleados con CEPA (abr-2026=46.0, jun-2026=50.5) se descartan — son de una fuente y métrica distintas, no comparables.

## Bandas nuevas (reemplazan `BANDAS_ITCP["movilizacion_cepa"]`)

Anclas informadas por referencias históricas reales ya citadas por la propia Secretaría:
- "14 conflictos con paro en promedio por mes" en el 2do semestre de 2024 — "el menor número desde 2006".
- "pico de 47 conflictos en 2014".

Puntaje: más conflictos con paro = más tensión (mismo sentido que la banda actual). Propuesta de bandas (a validar con la serie completa cuando esté backfilleada, ya que estos son solo 2 puntos de referencia):
- ≤15 → 100 (mínimo histórico, 2do sem. 2024)
- 15–25 → 85
- 25–35 → 65
- 35–47 → 40
- >47 → 10 (por encima del pico histórico citado, 2014)

**Esto queda marcado como banda `provisional`** (mismo mecanismo que `cohesion_bloque`/`adhesion_reformas_provincial`/`protestas_caba` hoy) hasta que el backfill real permita ver la distribución completa 2016-2026 y recalibrar con cuantiles reales, no solo 2 puntos citados de memoria por la fuente.

## Arquitectura técnica

**Tarea 1 (investigación técnica, no de diseño): ubicar el patrón real de nombre de archivo para 2021-2026.** Confirmado el patrón `conflicto_laboral_{año}t{trimestre}.pdf` para 2016-2020 (ej. `conflicto_laboral_2020t2.pdf`), pero `2025t2.pdf`/`2026t1.pdf` devuelven 404 — el patrón pudo cambiar, o el listado (que se renderiza vía JS, 32 resultados paginados) tiene los nombres reales de archivos recientes bajo otro esquema. Requiere inspección HTTP real (`requests` + revisar la respuesta completa de `argentina.gob.ar/node/335319`, o su endpoint AJAX subyacente) antes de poder escribir el parser — no se puede resolver por búsqueda.

**Fetcher nuevo en `politica.py`:** `fetch_conflictividad_laboral_srt()` — descarga el informe trimestral más reciente (PDF), extrae el conteo mensual de "conflictos con paro" del último mes citado. Parseo de PDF: usar `pdfplumber` (ya es dependencia del proyecto, usado en `macro.py` para el SDDS del BCRA) para extraer texto y buscar el patrón "N conflictos... en/de {mes} de {año}" — necesita fixture real de al menos 1 PDF completo para diseñar el regex (parte de la implementación, no de este spec).

**Serie histórica en `descargar_series.py`:** `fetch_conflictividad_laboral_srt_serie()` — descarga los ~32+ informes trimestrales (cada uno trae 3 meses), extrae los 3 conteos mensuales de cada uno. Dado que son PDFs estáticos e inmutables una vez publicados (un trimestre cerrado no se re-edita), aplica el mismo patrón de caché persistente que `_serie_cohesion_cacheada()` (trimestres cerrados no se vuelven a descargar; el trimestre en curso sí, siempre) — se generaliza o se reusa esa función si el patrón calza.

## Alcance de esta sesión

Este spec cubre el diseño; NO cubre la implementación (queda para el plan). Fuera de alcance explícito:
- Recalibrar bandas de otros indicadores.
- Tocar `cohesion_bloque` (Diputados) o `gobernadores_alineamiento` — temas separados de la misma auditoría, a encarar después.
- Migrar `protestas_caba` (ya tiene su propia fuente ACLED, no se toca).

## Riesgos operativos

- El parseo de PDF de 32+ informes con posibles cambios de formato a lo largo de 10 años (algunos son `.docx`, no `.pdf`, según ya se vio en 2017-2018) puede requerir manejo de casos especiales por archivo — no asumir un único parser sirve para todos sin verificarlo contra una muestra real.
- Riesgo de que el sitio tenga el mismo tipo de intermitencia que ya se vio con `senado.gob.ar` — aplicar el mismo patrón de `_paced_get`/retry si hace falta.
