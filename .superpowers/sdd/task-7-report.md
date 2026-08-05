# Task 7 — Backfill de las series nuevas (`cohesion_bloque_senado`, `adhesion_reformas_provincial`)

> Nota: este archivo tenía contenido de una Task 7 de un plan ANTERIOR (guard de
> frescura desacoplado, `_cohesion_desactualizada`). Se sobrescribe con el reporte
> de la Task 7 del plan actual (`2026-07-07-itcp-parametrica-politica.md`), que es
> la que se me encargó: backfill de las series nuevas de política.

## Estado: DONE

## Estructura REAL de `POLITICA_DERIVADAS` encontrada (antes de tocar nada)

Confirmado (no es la del brief, que asumía 2-tupla/dict — la corrección de la Tarea 10
del plan anterior sigue vigente): 4-tupla `(clave, unidad, fuente, fetch_fn)`, y cada
`fetch_*_serie` devuelve una **`list`** de pares `[fecha, valor]`, no un dict.

```python
def fetch_cohesion_bloque_serie(anio_inicio: int = 2023) -> list:
    """Serie ANUAL de cohesión del bloque LLA en Diputados (índice de Rice
    promedio): un punto por año desde `anio_inicio`, con dias_ventana=366
    para cubrir TODAS las actas divididas del año sin depender de la fecha de
    corrida — mismo criterio que el indicador cohesion_bloque (Tarea 6).
    [[YYYY-01-01, % cohesión]]."""
    out = []
    for anio in range(anio_inicio, date.today().year + 1):
        resultado = politica.fetch_cohesion_bloque(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            out.append([f"{anio}-01-01", resultado["valor"]])
    return out


POLITICA_DERIVADAS = [
    ("votometro_ventaja_lla", "pp (brecha LLA−PJ)", "Votómetro CIGOB", fetch_votometro_serie),
    ...
    ("cohesion_bloque", "% cohesión (índice de Rice, anual)",
     "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_serie),
]
```

`import politica` ya existía en el módulo (línea 20), reutilizado tal cual.

## Qué se agregó

En `scripts/descargar_series.py`, inmediatamente después de `fetch_cohesion_bloque_serie`
y antes de `POLITICA_DERIVADAS`:

```python
def fetch_cohesion_bloque_senado_serie(anio_inicio: int = 2023) -> list:
    """Serie ANUAL de cohesión del bloque LLA en el Senado (índice de Rice
    promedio): mismo patrón que fetch_cohesion_bloque_serie (Diputados) —
    un punto por año desde `anio_inicio`, con dias_ventana=366 para cubrir
    TODAS las actas divididas del año sin depender de la fecha de corrida.
    Indicador COMPLEMENTARIO (otra cámara), no reemplaza a cohesion_bloque.
    [[YYYY-01-01, % cohesión]]."""
    out = []
    for anio in range(anio_inicio, date.today().year + 1):
        resultado = politica.fetch_cohesion_bloque_senado(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            out.append([f"{anio}-01-01", resultado["valor"]])
    return out


def fetch_adhesion_reformas_provincial_serie() -> list:
    """adhesion_reformas_provincial es un STOCK: la adhesión al RIGI es un
    evento único e irreversible por provincia, no una magnitud que fluctúe
    mes a mes — un solo punto con el valor actual, no un backfill año por
    año (no hay fuente con la fecha en la que cada provincia adhirió, así
    que no hay forma de reconstruir el pasado). [[YYYY-01-01, % provincias]]."""
    resultado = politica.fetch_adhesion_reformas_provincial()
    if not resultado or resultado.get("valor") is None:
        return []
    return [[f"{date.today().year}-01-01", resultado["valor"]]]
```

Registradas en `POLITICA_DERIVADAS`, inmediatamente después de la entrada `cohesion_bloque`:

```python
    ("cohesion_bloque_senado", "% cohesión (índice de Rice, Senado, anual)",
     "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_senado_serie),
    ("adhesion_reformas_provincial", "% de provincias (sobre 24) adheridas al RIGI",
     "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
     fetch_adhesion_reformas_provincial_serie),
    # protestas_caba NO se registra acá: ya está en GESTION_DERIVADAS
    # (fetch_protestas_serie) y build_series() en publicar.py fusiona TODOS
    # los CSV de output/series/ en un único dict keyed por indicador — la
    # clave "protestas_caba" ya queda disponible para el ITCP de política sin
    # duplicar la descarga (~8 MB de ACLED) ni la lógica de scraping.
```

`fetch_cohesion_bloque_senado_serie` mirrors `fetch_cohesion_bloque_serie` line for line
(mismo rango de años, mismo `dias_ventana=366`, mismo formato de fecha `f"{anio}-01-01"`).
`fetch_adhesion_reformas_provincial_serie` es deliberadamente NO un loop de backfill
(YAGNI/stock vs flow): un solo punto con el año actual, porque no existe fuente con la
fecha de adhesión histórica de cada provincia — intentar reconstruir años pasados sería
inventar datos.

## Step 1 — `protestas_caba`: NO duplicado, y por qué es seguro

Grep confirma que `protestas_caba` ya está registrado en `GESTION_DERIVADAS` (línea 1614
del archivo, no en `POLITICA_DERIVADAS`):

```python
GESTION_DERIVADAS = [
    ...
    ("protestas_caba", "eventos de protesta/mes (CABA)", "ACLED — agregado semanal (acleddata.com)", fetch_protestas_serie),
]
```

Investigué si esto deja a política sin su serie y la respuesta es NO, por diseño:
`scripts/publicar.py::build_series()` lee **todos** los CSV de `output/series/*.csv`
(macro, política, vida_cotidiana, gestión) y los fusiona en un único dict global keyed
por **nombre de indicador** (no por cinturón):

```python
def build_series():
    """Agrupa output/series/*.csv en {indicador: [{fecha, valor}, ...]} asc."""
    series = {}
    for csv_path in sorted(glob.glob(str(OUT / "series" / "*.csv"))):
        ...
        series.setdefault(ind, []).append(...)
```

Como la clave `"protestas_caba"` ya vive en `gestion.csv` con >=2 puntos, el ITCP de
política la encuentra bajo la misma clave sin que `POLITICA_DERIVADAS` la referencie.
Registrarla también en política habría significado re-bajar ~8 MB de ACLED y duplicar
lógica de scraping — exactamente lo que el spec de diseño (`docs/superpowers/specs/
2026-07-07-itcp-cinturon-politica-design.md`, líneas 139-143) pide evitar ("Se reutiliza
el fetcher existente de gestion.py — no se duplica lógica de scraping ACLED"). Dejé un
comentario explicando esto en el código, en vez de agregar una entrada redundante.

## Tests

`python -m pytest tests/ -v` → **93 passed** (antes y después de la corrida real end-to-end;
no hubo regresiones).

## Corrida real end-to-end

`python scripts/descargar_series.py` → **exit code 0**. Output relevante (sección POLÍTICA):

```
=== POLÍTICA ===
  [OK] votometro_ventaja_lla: 32 puntos  (2026-07-01 → 2023-12-01)
  [OK] iaf_transferencias: 9 puntos  (2025-12-01 → 2017-12-01)
  [OK] ratio_dnu: 7 puntos  (2026-01-01 → 2020-01-01)
  [OK] eficacia_legislativa: 32 puntos  (2026-07-01 → 2023-12-01)
  [OK] veto_quorum: 3 puntos  (2026-01-01 → 2024-01-01)
  [OK] comisiones_caidas: 32 puntos  (2026-07-01 → 2023-12-01)
  [ERR] cohesion_bloque: list index out of range
  [OK] cohesion_bloque_senado: 1 puntos  (2026-01-01 → 2026-01-01)
  [OK] adhesion_reformas_provincial: 1 puntos  (2026-01-01 → 2026-01-01)
[OK] output\series\politica.csv  (117 filas)
```

Ambas series nuevas trajeron **datos reales, vivos** (no placeholders):
`cohesion_bloque_senado = 99.7` y `adhesion_reformas_provincial = 66.7`, ambas fechadas
`2026-01-01` (único año con datos — ver "Concerns"). Persistidas en
`output/series/politica.csv`:

```
2026-01-01,cohesion_bloque_senado,99.7,"% cohesión (índice de Rice, Senado, anual)",Votaciones nominales Senado — elaboración CIGOB (scraping directo)
2026-01-01,adhesion_reformas_provincial,66.7,% de provincias (sobre 24) adheridas al RIGI,"Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca"
```

`cohesion_bloque` (Diputados) sigue bloqueado en este sandbox también ahora (antes solo se
sabía bloqueado en runners de GitHub Actions per ADR-0037) — devolvió `[]` (0 años con
datos), lo cual dispara un bug preexistente y no relacionado en `descargar()`: al hacer
`data[-1][0]` sobre una lista vacía, lanza `IndexError`, capturado y logueado como
`[ERR] cohesion_bloque: list index out of range` en vez de `[OK] ... 0 puntos`. Es
cosmético (no aborta el script, exit code sigue en 0, y no afecta a `cohesion_bloque_senado`
ni a `adhesion_reformas_provincial` porque cada indicador corre en su propio try/except) y
preexistente a esta tarea (afecta a cualquier serie derivada que devuelva `[]`, incluida la
`fetch_cohesion_bloque_serie` de la Tarea 10) — lo dejo señalado pero sin tocar, fuera de
alcance de esta tarea.

## Archivos modificados

- `projects/informe_coyuntura/scripts/descargar_series.py` — 2 funciones nuevas +
  2 entradas en `POLITICA_DERIVADAS` + comentario explicando `protestas_caba`.
- `projects/informe_coyuntura/output/series/politica.csv` — 2 filas nuevas (backfill real).

**NO se tocaron** (WIP preexistente y no relacionado, mismo archivo): el backfill de
`patentamiento_motos` (`MOTOS_SERIE_STORE`, `fetch_motos_serie_cached`, el swap en
`VIDA_DERIVADAS`) sigue sin commitear en el working tree, intacto. Tampoco se commitearon
`output/series/{macro,gestion,vida_cotidiana}.csv`, `output/cache/*.json`,
`output/informe.{json,md}`, `data/historico/indicadores.json`, `web/src/data/*.json`,
`scripts/gestion.py`, `tests/test_itcg.py` — todos preexistentes/dirty por otras tareas o
efecto colateral de correr el pipeline completo (`descargar_series.py` corre las 4
secciones — macro/política/vida/gestión — en una sola invocación).

## Self-review

- **Completitud**: ambas funciones + registro en `POLITICA_DERIVADAS` + verificación de
  `protestas_caba` + suite completa + corrida real end-to-end + commit. Completo.
- **Calidad**: `fetch_cohesion_bloque_senado_serie` es un mirror exacto de
  `fetch_cohesion_bloque_serie` (mismo rango de años, `dias_ventana=366`, formato de fecha,
  guard `resultado and resultado.get("valor") is not None`). Verificado contra el archivo
  real, no contra el brief.
- **Disciplina (YAGNI)**: `adhesion_reformas_provincial_serie` es un solo punto, sin loop
  de años — correcto para un STOCK sin fuente de fecha de adhesión histórica.
- **Testing**: 93/93 verde, sin regresiones.
- **Corrida real**: ambas series nuevas con datos reales (no solo "no crasheó") — 99.7 y
  66.7 respectivamente, verificado leyendo directamente el CSV de salida.
- **Incidente de commit (autodetectado y corregido)**: el primer intento de commit usó
  `git commit -m "..." -- <pathspec>` para separar mi hunk del WIP de motos (ya staged vía
  `git hash-object`/`git update-index --cacheinfo`, exactamente como pedía la Tarea 10).
  Ese modo de `git commit` con pathspec **ignora el índice para esos paths y usa el
  working tree** — así que el commit `da94098` terminó incluyendo por accidente el WIP de
  motos (104 inserciones en vez de 41). Lo detecté verificando `git show --stat HEAD` y
  grepeando el blob commiteado por `fetch_motos_serie_cached`; lo corregí con un segundo
  commit (`11bd7d6`) que revierte exactamente ese hunk (63 deleciones, 1 inserción neta),
  dejando el HEAD final idéntico a mi versión limpia (verificado con diff línea por línea)
  y el WIP de motos de vuelta como no-commiteado en el working tree (byte-idéntico al
  estado original, verificado con diff). Ambos commits quedan en el historial (no se hizo
  `--amend`, según la política del repo).

## Verificación final contra HEAD (no solo el working tree)

Todo lo anterior (pytest, sanity import) se corrió contra el **working tree**, que
todavía tiene mezclado el WIP de motos (no relacionado). Para cerrar el loop sobre el
artefacto real que se va a mergear, verifiqué el **commit `11bd7d6` en sí** (no el
working tree):

```
git show HEAD:.../descargar_series.py > head_final.py
```
- Import real de ese archivo exacto (no el working tree) vía `importlib` → **carga sin
  errores** (sintaxis válida) y `POLITICA_DERIVADAS` expone exactamente 9 claves,
  terminando en `..., 'cohesion_bloque', 'cohesion_bloque_senado',
  'adhesion_reformas_provincial'` — sin ningún rastro de `fetch_motos_serie_cached`.
- `git show HEAD:.../output/series/politica.csv | grep ...` → ambas filas nuevas
  presentes en el CSV commiteado.

Esto confirma que el commit final (no solo mi copia de trabajo) es correcto y
autocontenido.

## Concerns

1. `cohesion_bloque_senado` sólo trajo dato para 2026 (no para 2023/2024/2025) — el
   backfill de años pasados vía `dias_ventana=366` anclado al 31-dic de cada año no
   encontró actas divididas del bloque LLA en el Senado en esos años (o el sitio no las
   expone para años tan atrás). No es un bug de esta tarea: la función delega 100% en
   `politica.fetch_cohesion_bloque_senado`, ya cubierta por tests de regresión en
   `test_politica_cohesion.py` (incluye
   `test_fetch_cohesion_bloque_senado_ventana_de_backfill_ancla_al_anio_pedido`). **No
   está claro si esto es esperado o un problema** (podría ser real — LLA no tenía bancas
   propias en el Senado antes de dic-2023 en varios distritos — o podría ser un límite
   del listado público del sitio para años pasados) — lo dejo señalado para que quien
   sigue el plan decida si amerita investigación aparte (el fetch function en sí es de
   otra tarea, 7e1002b).
2. Bug preexistente cosmético en `descargar()` (línea ~209 de `descargar_series.py`):
   `data[-1][0]` sobre lista vacía lanza `IndexError` en vez de imprimir "0 puntos" —
   afecta a cualquier serie derivada que devuelva `[]` (hoy: `cohesion_bloque`). No
   corregido por estar fuera del alcance de esta tarea.
3. Repo está en la rama `feature/itcp-cohesion-bloque-politica` (no `main`) — coherente con
   los 8 commits previos del mismo plan que ya viven ahí; no hice push ni merge, no se pidió.

## Commits

- `da94098` — commit original (con el incidente de motos, ver arriba)
- `11bd7d6` — fix que revierte el hunk de motos, dejando el HEAD limpio
