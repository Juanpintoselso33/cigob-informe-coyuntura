# Task 6 cross-fix report — `fetch_cohesion_bloque` window anchoring bug

## Context

Discovered by Task 10's implementer while using the already-approved
`fetch_cohesion_bloque(anio=..., dias_ventana=...)` (from Task 6) for its
documented purpose (historical backfill via `descargar_series.py`). This is a
defect in already-committed code, not a new feature.

## The bug

`limite = datetime.now() - timedelta(days=dias_ventana)` was always anchored
to the real wall-clock "now", ignoring the `anio` parameter. A backfill call
`fetch_cohesion_bloque(anio=2023, dias_ventana=366)` run today (2026-07-07)
computes `limite ≈ 2025-07-06` — every 2023 acta has `fecha < limite`, so
every historical acta got discarded regardless of whether the scrape
succeeded. The `anio` parameter was therefore inert for backfill purposes;
only the current (and partially the previous) year could ever populate.

## The fix

File: `scripts/politica.py`, function `fetch_cohesion_bloque` (line 941).

### Before

```python
def fetch_cohesion_bloque(anio: int | None = None, dias_ventana: int = 90) -> dict | None:
    """Cohesión del bloque LLA en Diputados: índice de Rice promedio sobre
    las actas nominales divididas de los últimos `dias_ventana` días.
    `anio`: para backfill (descargar_series.py itera años pasados).
    Devuelve None SOLO si el scraping en sí falló (sin llegar al sitio) —
    'sin votos en la ventana' (receso legislativo) es un resultado válido con
    valor=None pero corrida_exitosa_en seteado, para que el guard de frescura
    (Tarea 7) no lo confunda con un scraper roto."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas(session, anio)
    if actas is None:
        return None

    limite = datetime.now() - timedelta(days=dias_ventana)
    indices = []
    fecha_max = None
    for acta in actas:
        ...
```

### After

```python
def fetch_cohesion_bloque(anio: int | None = None, dias_ventana: int = 90) -> dict | None:
    """Cohesión del bloque LLA en Diputados: índice de Rice promedio sobre
    las actas nominales divididas de los últimos `dias_ventana` días.
    `anio`: para backfill (descargar_series.py itera años pasados).
    Devuelve None SOLO si el scraping en sí falló (sin llegar al sitio) —
    'sin votos en la ventana' (receso legislativo) es un resultado válido con
    valor=None pero corrida_exitosa_en seteado, para que el guard de frescura
    (Tarea 7) no lo confunda con un scraper roto.
    La ventana de recencia se ancla a HOY para el año en curso, y al 31 de
    diciembre de `anio` para años pasados (backfill) — así `dias_ventana`
    mide 'actividad dentro de ese año', no 'actividad reciente respecto de
    la fecha de corrida real'."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas(session, anio)
    if actas is None:
        return None

    referencia = datetime.now() if anio == datetime.now().year else datetime(anio, 12, 31)
    limite = referencia - timedelta(days=dias_ventana)
    indices = []
    fecha_max = None
    for acta in actas:
        ...
```

Only the docstring gained an anchoring note, and the single `limite = ...`
line was replaced by two lines computing `referencia` first. No other logic
in the function changed.

## New regression test

Added to `tests/test_politica_cohesion.py`, right after
`test_fetch_cohesion_bloque_falla_de_red_devuelve_none` (still inside the
`fetch_cohesion_bloque` test group, before the `_cohesion_desactualizada`
tests):

```python
def test_fetch_cohesion_bloque_ventana_de_backfill_ancla_al_anio_pedido(monkeypatch):
    anio_backfill = datetime.now().year - 2   # un año claramente pasado, no el actual
    acta_de_ese_anio = datetime(anio_backfill, 6, 15)   # bien adentro del año pedido
    actas = [{"id": "1", "slug": "a", "fecha": acta_de_ese_anio}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_get", lambda s, p: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque(anio=anio_backfill, dias_ventana=366)
    # Con el bug (limite anclado a HOY), esta acta habría quedado SIEMPRE fuera de ventana
    # (un año pasado nunca puede estar a <366 días de "hoy" salvo el año en curso/anterior parcial).
    # Con el fix (limite anclado al 31-dic de anio_backfill), esta acta SÍ debe entrar.
    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)
```

## RED — confirming the bug reproduces before the fix

Temporarily stashed the `scripts/politica.py` fix (keeping the new test in
place) and ran only the new test against the buggy code:

```
$ git stash push -- scripts/politica.py
$ python -m pytest tests/test_politica_cohesion.py -v -k backfill

collected 1 item
tests/test_politica_cohesion.py::test_fetch_cohesion_bloque_ventana_de_backfill_ancla_al_anio_pedido FAILED

    resultado = politica.fetch_cohesion_bloque(anio=anio_backfill, dias_ventana=366)
    ...
>   assert resultado["n_actas"] == 1
E   assert 0 == 1

tests\test_politica_cohesion.py:305: AssertionError
========================== 1 failed, 31 deselected in 0.47s ==========================
```

This confirms the exact regression described: with `limite` anchored to real
`datetime.now()`, a 2024-era acta (anio_backfill = 2026 − 2 = 2024) is always
outside the 366-day window measured from 2026-07-07, so `n_actas` comes back
`0` instead of `1`.

Restored the fix via `git stash pop`.

## GREEN — full `test_politica_cohesion.py` after the fix

```
$ python -m pytest tests/test_politica_cohesion.py -v

collected 32 items

tests/test_politica_cohesion.py::test_indice_rice_unanime_afirmativo PASSED
tests/test_politica_cohesion.py::test_indice_rice_dividido_parejo PASSED
tests/test_politica_cohesion.py::test_indice_rice_mayoria_parcial PASSED
tests/test_politica_cohesion.py::test_indice_rice_sin_votos PASSED
tests/test_politica_cohesion.py::test_es_bloque_lla_variantes PASSED
tests/test_politica_cohesion.py::test_es_bloque_lla_excluye_aliados_y_otros PASSED
tests/test_politica_cohesion.py::test_hcdn_votaciones_get_reintenta_ante_403 PASSED
tests/test_politica_cohesion.py::test_hcdn_votaciones_get_agota_reintentos PASSED
tests/test_politica_cohesion.py::test_hcdn_votaciones_get_devuelve_none_ante_excepcion PASSED
tests/test_politica_cohesion.py::test_hcdn_votaciones_session_setea_headers PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_empareja_fecha_con_acta PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_ignora_filas_sin_fecha_o_sin_acta PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_deduplica_por_id PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_request_fallido_devuelve_none PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_acepta_slug_vacio PASSED
tests/test_politica_cohesion.py::test_descubrir_actas_excepcion_de_red_devuelve_none PASSED
tests/test_politica_cohesion.py::test_url_acta_con_slug PASSED
tests/test_politica_cohesion.py::test_url_acta_sin_slug PASSED
tests/test_politica_cohesion.py::test_parsear_acta_extrae_filas PASSED
tests/test_politica_cohesion.py::test_parsear_acta_ignora_filas_incompletas PASSED
tests/test_politica_cohesion.py::test_parsear_acta_ignora_fila_de_encabezado PASSED
tests/test_politica_cohesion.py::test_parsear_acta_html_vacio PASSED
tests/test_politica_cohesion.py::test_parsear_acta_ignora_fila_sin_bloque PASSED
tests/test_politica_cohesion.py::test_fetch_cohesion_bloque_promedia_solo_actas_en_ventana PASSED
tests/test_politica_cohesion.py::test_fetch_cohesion_bloque_sin_actas_en_ventana_pero_corrida_exitosa PASSED
tests/test_politica_cohesion.py::test_fetch_cohesion_bloque_falla_de_red_devuelve_none PASSED
tests/test_politica_cohesion.py::test_fetch_cohesion_bloque_ventana_de_backfill_ancla_al_anio_pedido PASSED
tests/test_politica_cohesion.py::test_cohesion_desactualizada_corrida_exitosa_hoy PASSED
tests/test_politica_cohesion.py::test_cohesion_desactualizada_sin_corrida_previa_ni_actual PASSED
tests/test_politica_cohesion.py::test_cohesion_desactualizada_corrida_previa_reciente PASSED
tests/test_politica_cohesion.py::test_cohesion_desactualizada_corrida_previa_vieja PASSED
tests/test_politica_cohesion.py::test_cohesion_desactualizada_corrida_exitosa_sin_votos_nuevos PASSED

============================= 32 passed in 0.28s ==============================
```

32 tests pass (31 pre-existing + 1 new). All three pre-existing
`fetch_cohesion_bloque` tests — which don't pass `anio` and rely on the
default-to-current-year behavior — pass unchanged:

- `test_fetch_cohesion_bloque_promedia_solo_actas_en_ventana`
- `test_fetch_cohesion_bloque_sin_actas_en_ventana_pero_corrida_exitosa`
- `test_fetch_cohesion_bloque_falla_de_red_devuelve_none`

This confirms the fix does not alter live-call (current-year) behavior: when
`anio == datetime.now().year`, `referencia` still equals `datetime.now()`
exactly as before.

## Full repo suite

```
$ python -m pytest tests/ -q
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 1.13s
```

All 74 tests in the repo pass.

## Task 10 backfill wrapper re-verification

```
$ python -c "import sys; sys.path.insert(0,'scripts'); import descargar_series as d; print(d.fetch_cohesion_bloque_serie())"
[]
```

Still returns `[]` in this sandbox because `votaciones.hcdn.gob.ar` is
IP-blocked here (confirmed in Tasks 4–10) — a separate, already-known,
already-accepted environmental limitation, not something this fix addresses
or needs to address. What matters is that the window logic itself is now
correct, which is verified by the new unit test with mocks (not by this
live/blocked call).

## Commit

```
commit bb9f9717614e1f2e43ce9ea7281167e405b7e5cd
Author: Juanpintoselso33 <juanpintoselso33@gmail.com>

    fix(politica): ventana de fetch_cohesion_bloque ancla al año de backfill, no a hoy (hallazgo cruzado de la Tarea 10)

 projects/informe_coyuntura/scripts/politica.py        |  9 +++++++--
 .../informe_coyuntura/tests/test_politica_cohesion.py | 19 +++++++++++++++++++
 2 files changed, 26 insertions(+), 2 deletions(-)
```

Only `scripts/politica.py` and `tests/test_politica_cohesion.py` were staged
and committed; the ~20 pre-existing unrelated modified/untracked files in the
working tree were left untouched (still showing as modified/untracked in
`git status`, not part of this commit).

Note: the commit landed on the currently checked-out branch
`feature/itcp-cohesion-bloque-politica` (not `main`) — this was the branch
already active in the working tree at task start; no branch switch was
performed.
