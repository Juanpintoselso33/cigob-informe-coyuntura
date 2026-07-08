# ITCP — Profundización: granularidad real, corrección y sensibilidad standalone

| | |
|---|---|
| **Fecha** | 2026-07-08 |
| **Ámbito** | `scripts/politica.py` · `scripts/descargar_series.py` · `scripts/sensibilidad.py` · `data/politica/manuales.json` · `docs/cinturon_politica.md` · `tests/` |
| **Precedente directo** | ADR-0036 (paramétrica ITCP), ADR-0037 (bloqueo `cohesion_bloque`), `.superpowers/sdd/task-14-validacion-externa-report.md` |

## Contexto

El ITCP (paramétrica del cinturón política) se construyó ayer (2026-07-07) en una
sesión de ~35 commits. El reporte de la tarea de validación externa (Task 14) ya
documentó honestamente que 5 de los 12 indicadores del índice recién tienen 1-2
puntos de historia real. Este documento cubre la investigación de qué parte de esa
falta de granularidad es un límite real de las fuentes y qué parte es un bug de
código, más una auditoría de corrección dedicada del módulo nuevo y un agregado
mecánico de paridad (sensibilidad standalone).

**Auditoría de corrección** (agente `code-reviewer` dedicado, alcance:
`itcp.py`, `parametrica.py`, las funciones ITCP-relacionadas de `politica.py`,
`publicar.py` y `validacion_externa.py`): **sin bugs críticos ni importantes**.
Direcciones de banda, sumas de pesos, propagación de `var_vs_2023`, degradación de
cohesión a cache y códigos de salida — todos correctos. Dos hallazgos menores (ver
Sub-proyecto 3).

**Investigación de granularidad** (agente de research, verificación en vivo propia
con `requests.post`): de los 4 indicadores candidatos, 1 tiene un bug de código real
con arreglo verificado, 1 es viable parcialmente (límite real de la fuente), y 2 son
callejones sin salida ya confirmados (sin cambios de código).

## Sub-proyecto 1 — Backfill real de `cohesion_bloque_senado`

### El bug

`fetch_cohesion_bloque_senado_serie(anio_inicio=2023)` en `descargar_series.py`
(línea ~477) ya itera correctamente `range(2023, año_actual+1)` llamando a
`politica.fetch_cohesion_bloque_senado(anio=anio, dias_ventana=366)` — el bucle de
backfill está bien. El bug vive un nivel más abajo: `_descubrir_actas_senado()`
(`politica.py` línea ~1023) hace

```python
r = _paced_get(session, SENADO_BASE, "/votaciones/actas")
```

un **GET sin parámetro de año** — el servidor siempre devuelve el listado del año en
curso, y el filtro posterior `if fecha.year != anio: continue` descarta todo cuando
`anio` es un año pasado. Resultado: la serie "backfilleada" solo produce 1 punto real
(el año en curso), exactamente lo que documentó el Task 14 report
(`cohesion_bloque_senado: 1 pt, 2026-07`).

### El fix (verificado en vivo, no hipotético)

Confirmé con `requests.post` directo (fuera del repo) que
`senado.gob.ar/votaciones/actas` acepta `POST` con form-data
`{"busqueda_actas[anio]": "<año>"}` y responde con el listado real de ESE año, sin
bloqueo anti-bot (a diferencia de HCDN Diputados):

| Año | Actas devueltas (HTTP 200) |
|---|---|
| 2023 | 26 |
| 2024 | 91 |
| 2025 | 95 |
| 2026 (parcial) | 80 |

Cambios:

1. Nuevo helper `_paced_post(session, base_url, path, data, **kwargs)` en
   `politica.py`, espejo exacto de `_paced_get` (mismo pacing, mismo retry/backoff
   ante 403, hasta 3 intentos) pero con `session.post(url, data=data, ...)`.
2. `_descubrir_actas_senado(session, anio)` pasa a llamar
   `_paced_post(session, SENADO_BASE, "/votaciones/actas", data={"busqueda_actas[anio]": str(anio)})`
   en vez del GET sin parámetros. El resto de la función (parseo de `<tr>`,
   `_RE_DETALLE_ACTA_SENADO`, `_RE_DISPLAY_NONE`) no cambia — ya asume que la
   respuesta trae las actas del año pedido.
3. Sin cambios en `fetch_cohesion_bloque_senado()`, `fetch_cohesion_bloque_senado_serie()`
   ni en el registro de `POLITICA_DERIVADAS` — el bug estaba aislado a una función.

### Qué NO incluye este sub-proyecto

- **No** se recalibran las bandas "provisionales" de `cohesion_bloque_senado`
  (`itcp.BANDAS_ITCP`) aunque la serie pase de 1 a 4 puntos. Recalibrar bandas con 4
  puntos anuales sigue siendo poca base estadística y merece su propio análisis
  dedicado, no una decisión de pasada dentro de este fix. El flag "provisional" se
  mantiene en `docs/cinturon_politica.md`.
- **No** toca `cohesion_bloque` (Diputados) — sigue bloqueado por el anti-bot de
  HCDN (ADR-0037), fuera de alcance de esta sesión (decisión ya tomada al elegir
  los frentes de trabajo).

## Sub-proyecto 2 — Backfill parcial de `movilizacion_cepa`

### Límite real de la fuente (no un bug)

CEPA (`centrocepa.com.ar/documentos/informes`) recién empezó a publicar informes
con "conflictividad"/"conflictos-laborales" en la URL a fines de 2025. La
investigación (paginación GET plana, sin bloqueo, verificada hasta ~30 páginas /
id≈483) encontró exactamente 4 informes de este tipo:

| ID informe | Período | Cifra citada (a extraer en vivo con el regex existente) |
|---|---|---|
| 739 | dic-2025/ene-2026 | pendiente de extracción en la implementación |
| 748 | feb-2026 | agregados: 507 casos ene-2024→sep-2025, 210 casos oct-2025→feb-2026 (sin desagregado mensual) |
| 773 | abr-2026 | "al menos 92 conflictos" |
| 809 | jun-2026 | ya cubierto por el fetch en vivo actual (indicador vigente) |

Ninguna cifra se hardcodea en el código ni en este documento: las cuatro se extraen
en vivo con el mismo regex ya usado por `fetch_cepa_movilizacion()`, igual que
cualquier otra corrida del pipeline. No hay nada anterior a dic-2025 — a diferencia
de `cohesion_bloque_senado`, este NO es un bug de código, es que la fuente no
existía antes. El resultado esperado es ~4-6 puntos reales (dic-2025→jul-2026), no
una serie desde dic-2023.

### Cambios

1. Ampliar el rango de páginas escaneadas en `fetch_cepa_movilizacion()` (hoy mira
   5 páginas) lo suficiente para cubrir el id≈739 histórico — con margen, no
   hardcodear el ID exacto (el sitio puede publicar informes nuevos entre medio).
2. Extraer fecha + cifra de cada informe histórico encontrado, con la misma lógica
   de regex ya usada para el informe corriente (`fetch_cepa_movilizacion()` línea
   ~441-510) — reusar, no duplicar.
3. Registrar `fetch_cepa_movilizacion_serie()` en `descargar_series.py` /
   `POLITICA_DERIVADAS`, mismo patrón 4-tupla que `cohesion_bloque_senado`.
4. El informe 748 mezcla dos períodos agregados (no mensual limpio) — documentar
   explícitamente en el código/commit cómo se resuelve (ej. un punto por período
   agregado, fechado al cierre del período, en vez de inventar un desglose mensual
   que la fuente no da).

### Qué NO incluye

- No se recalibran bandas de `movilizacion_cepa` (ya tiene bandas no-provisionales,
  esto solo densifica la serie).
- No se persigue backfill anterior a dic-2025: confirmado que la fuente no lo tiene.

## Sub-proyecto 3 — Correcciones menores

1. **`protestas_caba`: gate de frescura inconsistente con lo que puntúa.**
   `politica.py` main() (línea ~1241) cuenta el indicador como fresco si
   `resultado.get("valor") is not None` (conteo crudo), pero lo que efectivamente
   entra al ITCP es `var_vs_2023` (`_valor_itcp`, línea ~1187). Si algún día
   `base_2023` fuera 0, `protestas_caba` podría contarse como fresco y sin embargo
   no aportar al índice, sin ninguna señal visible. Hoy no se dispara (2023 tuvo
   cientos de eventos reales), pero es un borde barato de cerrar: el gate de
   frescura debe exigir también `var_vs_2023 is not None`.
2. **`docs/cinturon_politica.md:148`** describe `cohesion_bloque` publicando
   "78% → puntaje banda 79,0" — desactualizado desde la purga de legado
   (`3973d00`, cache real hoy tiene el indicador ausente). Corregir la
   descripción para reflejar el estado real (ausente, degradado, sin placeholder).
   Aprovechar el mismo pase para actualizar la sección de "Score actual del
   cinturón" y "Bandas provisionales" con los resultados de los sub-proyectos 1 y
   2 una vez corridos en vivo.
3. **`data/politica/manuales.json._meta`**: agregar una entrada fechada
   2026-07-08 registrando que se reinvestigó `gobernadores_alineamiento` (sin
   fuente nueva encontrada más allá de los 4 proxies ya descartados) — evita que
   una sesión futura repita la misma investigación.
4. **Comentario en `fetch_adhesion_reformas_provincial()`**: documentar que la
   tabla MAGyP no tiene fecha de adhesión por provincia y que la fuente que sí la
   tendría (`trivia.consejo.org.ar`) está bloqueada por WAF — confirma que el
   diseño actual (stock de punto único) es intencional, no una limitación
   pendiente de resolver.

**No se toca** el comportamiento de `parametrica.calcular_indice` respecto a
overrides sobre indicadores ausentes (se descartan en silencio) — es una decisión
del motor genérico compartido con ITCM/ITCG/ITVC, no específica de política, y
está fuera de alcance de esta sesión.

## Sub-proyecto 4 — Sensibilidad standalone para ITCP

`scripts/sensibilidad.py` ya tiene todo el motor genérico (`analizar_bloque`,
`_perturbar`, `_agregar`, experimentos pesos/insumos/combinado + leave-one-out) —
solo falta declarar el ITCP en el dict `INDICES`:

```python
import itcp
...
INDICES = {
    "itcm": {...}, "itcg": {...}, "itvc": {...},
    "itcp": {"cinturon": "politica", "bandas": itcp.BANDAS_ITCP,
             "tension": lambda v: round((100 - v) / 10, 1)},
}
```

Nota: esto es **distinto** del `robustez_compacta()` que ya corre para ITCP dentro
de `publicar.py::_scoring_indice()` (confirmado en el snapshot real: `informe.json`
→ `cinturones.politica.itcp.robustez` ya existe, con `dominante: cohesion_bloque_senado`).
Este sub-proyecto agrega el análisis MÁS PROFUNDO (3 experimentos separados +
ranking leave-one-out completo) al artefacto standalone `output/sensibilidad.json`,
que hoy solo cubre ITCM/ITCG/ITVC — un gap de paridad documental/analítica, no de
producción.

Verificación esperada: `python scripts/sensibilidad.py` debe producir una clave
`"itcp"` en `output/sensibilidad.json` con la misma forma que `"itcm"`/`"itcg"`, y
el componente dominante del leave-one-out debería ser `cohesion_bloque_senado`
(consistente con lo que ya muestra `robustez_compacta` en el snapshot publicado).

## Orden de ejecución y commits

Mismo patrón que ayer: un commit atómico por sub-proyecto, en este orden (de menor
a mayor dependencia con datos en vivo):

1. Sub-proyecto 3 (correcciones menores) — no depende de scraping, más rápido de
   verificar con tests.
2. Sub-proyecto 4 (sensibilidad standalone) — mecánico, no depende de scraping.
3. Sub-proyecto 1 (`cohesion_bloque_senado`) — requiere corrida en vivo contra
   `senado.gob.ar`.
4. Sub-proyecto 2 (`movilizacion_cepa`) — requiere corrida en vivo contra
   `centrocepa.com.ar`; depende de que el 1 ya esté verificado como referencia del
   patrón de registro en `POLITICA_DERIVADAS`.
5. Actualización final de `docs/cinturon_politica.md` reflejando 1-4 ya corridos.

Cada commit corre `pytest` completo antes de commitear (sin regresión) y, para 1 y
2, una corrida real de `python scripts/politica.py` / `descargar_series.py` contra
las fuentes en vivo (no mockear scraping nuevo).

## Riesgos conocidos

- **`_paced_post` nuevo**: mismo mecanismo de retry/backoff que `_paced_get`, pero
  nunca ejercitado en producción contra Senado con POST — verificar que el WAF del
  sitio no reacciona distinto a POST vs GET repetidos (mismo `Session` + pacing que
  ya evita el 403 en `_paced_get`, no hay motivo a priori para que difiera, pero se
  confirma con la corrida real del sub-proyecto 1, no solo con la verificación
  puntual ya hecha).
- **CEPA informe 748** mezcla períodos agregados no mensuales — riesgo de que la
  extracción automática interprete mal el rango; requiere revisión manual del
  regex contra el texto real del informe antes de confiar en el valor extraído.
- Ninguno de los 4 sub-proyectos toca `cohesion_bloque` (Diputados) ni pesos/bandas
  del ITCP — el `valor` publicado del índice puede moverse levemente solo por
  tener más historia en `cohesion_bloque_senado`/`movilizacion_cepa` alimentando
  validación externa y sensibilidad, no por un cambio de metodología.
