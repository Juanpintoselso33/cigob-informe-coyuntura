# ITCP — Profundización (granularidad, corrección, sensibilidad) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Precedente:** `docs/superpowers/specs/2026-07-08-itcp-profundizacion-design.md` (spec aprobado). Este plan asume que `scripts/itcp.py`, `scripts/parametrica.py`, `scripts/politica.py` y `scripts/sensibilidad.py` están en el estado del commit `d18d18f` (validación externa ITCP, 2026-07-07).

**Goal:** Corregir un bug real de backfill (`cohesion_bloque_senado`), sumar backfill parcial honesto de `movilizacion_cepa`, blindar un borde latente de `protestas_caba`, agregar el ITCP al script standalone de sensibilidad, y documentar dos investigaciones sin salida (`gobernadores_alineamiento`, `adhesion_reformas_provincial`) para no repetirlas.

**Architecture:** Todos los cambios de código viven en `scripts/politica.py` (funciones nuevas/corregidas) y `scripts/descargar_series.py` (registro de backfill), siguiendo el patrón 4-tupla `(clave, unidad, fuente, fetch_fn)` de `POLITICA_DERIVADAS` ya establecido. `scripts/sensibilidad.py` gana una entrada de dict, sin cambios de lógica. `docs/cinturon_politica.md` se actualiza al final reflejando los resultados de una corrida real.

**Tech Stack:** Python 3, `requests` + `BeautifulSoup` (`html.parser`, ya en `requirements.txt`), `pytest`.

## Global Constraints

- Convención de bandas y motor: sin cambios — este plan NO toca `itcp.py` ni `parametrica.py`.
- Ningún cambio recalibra bandas "provisionales" (`cohesion_bloque_senado`, `movilizacion_cepa` ya tiene bandas no-provisionales — no aplica). Eso queda fuera de alcance (spec, sección "Qué NO incluye").
- No se toca `cohesion_bloque` (Diputados, bloqueado ADR-0037) ni el comportamiento de `parametrica.calcular_indice` sobre overrides ausentes (motor compartido con ITCM/ITCG/ITVC).
- Todo fetcher nuevo/modificado sigue el estilo defensivo ya establecido: `try/except` amplio en las funciones `fetch_*` públicas, `_warn(nombre, mensaje)` en vez de dejar propagar la excepción.
- Todo commit corre `cd projects/informe_coyuntura && python -m pytest tests/ -v` limpio antes de commitear.

---

### Task 1: Blindar el gate de frescura de `protestas_caba`

**Files:**
- Modify: `scripts/politica.py:1179-1189` (agrega función nueva después de `_valor_itcp`), `scripts/politica.py:1239-1246` (wiring en `main()`)
- Test: `tests/test_politica_cohesion.py` (agrega 4 tests al final del bloque `_valor_itcp`, después de la línea 565)

**Interfaces:**
- Consumes: `politica._valor_itcp(nombre: str, entry: dict)` (ya existe, sin cambios)
- Produces: `politica._resultado_utilizable(nombre: str, resultado: dict | None) -> bool`

- [ ] **Step 1: Write the failing tests**

Agregar al final de `tests/test_politica_cohesion.py`:

```python
# ── _resultado_utilizable (hallazgo de auditoría 2026-07-08) ────────────────
# protestas_caba puntúa en el ITCP sobre var_vs_2023, no sobre "valor" (conteo
# crudo). El gate de frescura de main() históricamente miraba solo "valor" --
# si algún día base_2023 fuera 0, gestion.fetch_protestas_caba() deja
# var_vs_2023 en None pero "valor" sigue presente, y el indicador se contaría
# como fresco sin aportar realmente al ITCP. Reusa _valor_itcp para que el
# gate de frescura y el cálculo del índice usen SIEMPRE el mismo valor.

def test_resultado_utilizable_protestas_caba_requiere_var_vs_2023():
    entry = {"valor": 347, "var_vs_2023": None}
    assert not politica._resultado_utilizable("protestas_caba", entry)


def test_resultado_utilizable_protestas_caba_con_var_vs_2023():
    entry = {"valor": 347, "var_vs_2023": 15.3}
    assert politica._resultado_utilizable("protestas_caba", entry)


def test_resultado_utilizable_otro_indicador_usa_valor_directo():
    assert politica._resultado_utilizable("cohesion_bloque", {"valor": 62.5})


def test_resultado_utilizable_none_no_es_utilizable():
    assert not politica._resultado_utilizable("cohesion_bloque", None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k resultado_utilizable -v`
Expected: 4 FAIL con `AttributeError: module 'politica' has no attribute '_resultado_utilizable'`

- [ ] **Step 3: Implementar `_resultado_utilizable` en `politica.py`**

Insertar inmediatamente después de la función `_valor_itcp` (que termina en la línea 1189, justo antes de `def _anotar_indicadores_itcp`):

```python
def _resultado_utilizable(nombre: str, resultado: dict | None) -> bool:
    """True si el resultado de un fetcher tiene el valor que efectivamente se
    usa en el ITCP para `nombre` (vía _valor_itcp), no solo un "valor" crudo
    presente. Cierra un borde latente (auditoría 2026-07-08): protestas_caba
    puntúa sobre var_vs_2023; si var_vs_2023 fuera None con "valor" presente
    (base_2023 == 0), el indicador se contaría como fresco sin aportar
    realmente al índice. Para el resto de los indicadores es equivalente a
    `resultado.get("valor") is not None` (_valor_itcp devuelve "valor" directo)."""
    return resultado is not None and _valor_itcp(nombre, resultado) is not None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k resultado_utilizable -v`
Expected: 4 PASS

- [ ] **Step 5: Wiring en `main()`**

En `scripts/politica.py`, la función `main()` tiene este bloque (líneas 1239-1246):

```python
    for nombre, fetcher in colectores:
        resultado = fetcher()
        if resultado is not None and resultado.get("valor") is not None:
            frescos[nombre] = resultado
            frescos_count += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}
```

Reemplazar la condición del `if` por una llamada a `_resultado_utilizable`:

```python
    for nombre, fetcher in colectores:
        resultado = fetcher()
        if _resultado_utilizable(nombre, resultado):
            frescos[nombre] = resultado
            frescos_count += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}
```

- [ ] **Step 6: Correr la suite completa**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS, sin regresión (este cambio es no-op en producción hoy: `base_2023` siempre es > 0 con los datos reales de ACLED).

- [ ] **Step 7: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "fix(politica): gate de frescura de protestas_caba usa var_vs_2023, no el conteo crudo

Hallazgo de auditoría 2026-07-08: main() marcaba protestas_caba como
'fresco' con solo chequear 'valor' (conteo crudo), pero el ITCP puntúa
sobre var_vs_2023 (_valor_itcp). Si base_2023 fuera 0, el indicador se
contaría como fresco sin aportar al índice, sin ninguna señal visible.
Nuevo _resultado_utilizable() reusa _valor_itcp como fuente única de
verdad para 'qué valor cuenta'. No-op en producción hoy (2023 tuvo
cientos de eventos reales en CABA)."
```

---

### Task 2: Registrar investigaciones sin salida + corregir línea desactualizada

**Files:**
- Modify: `data/politica/manuales.json:6`
- Modify: `scripts/descargar_series.py:492-501` (docstring de `fetch_adhesion_reformas_provincial_serie`)
- Modify: `docs/cinturon_politica.md:148`

**Interfaces:** ninguna — solo texto/datos, sin cambios de comportamiento.

- [ ] **Step 1: Actualizar `data/politica/manuales.json`**

El archivo tiene hoy (línea 5-7):

```json
    "pendiente_automatizacion": {
      "gobernadores_alineamiento": "métrica cualitativa — sin fuente estructurada disponible. Proxies investigados y DESCARTADOS (2026-07-07, no volver a evaluar sin fuente nueva): (1) composición partidaria del Senado por provincia — mide bancas legislativas, no conducta del Poder Ejecutivo provincial; (2) composición de Diputados por distrito (CKAN HCDN) — varios legisladores de distinto signo por provincia simultáneamente, sin campo de gobernador; (3) API de Presupuesto Abierto (transferencias/ATN) — sin columna de corte provincial confirmada, y el organismo correcto para ATN es Interior, no Economía; (4) tabla de adhesión provincial al RIGI — mide adhesión fiscal a un régimen puntual, no alineamiento político general (se automatiza como indicador NUEVO y DISTINTO, adhesion_reformas_provincial, ver ADR-0036). Único camino identificado: NLP sobre cobertura periodística (La Nación Data, Infobae) — proyecto separado."
    }
```

Reemplazar el valor de `gobernadores_alineamiento` agregando una oración al final (antes de la comilla de cierre):

```json
    "pendiente_automatizacion": {
      "gobernadores_alineamiento": "métrica cualitativa — sin fuente estructurada disponible. Proxies investigados y DESCARTADOS (2026-07-07, no volver a evaluar sin fuente nueva): (1) composición partidaria del Senado por provincia — mide bancas legislativas, no conducta del Poder Ejecutivo provincial; (2) composición de Diputados por distrito (CKAN HCDN) — varios legisladores de distinto signo por provincia simultáneamente, sin campo de gobernador; (3) API de Presupuesto Abierto (transferencias/ATN) — sin columna de corte provincial confirmada, y el organismo correcto para ATN es Interior, no Economía; (4) tabla de adhesión provincial al RIGI — mide adhesión fiscal a un régimen puntual, no alineamiento político general (se automatiza como indicador NUEVO y DISTINTO, adhesion_reformas_provincial, ver ADR-0036). Único camino identificado: NLP sobre cobertura periodística (La Nación Data, Infobae) — proyecto separado. Reinvestigado 2026-07-08 (sesión de profundización del ITCP): se buscaron fuentes nuevas (observatorios universitarios UNSAM/CIPPEC/SAAP, encuestas de gestión provincial, comunicados de 'gobernadores aliados') — ninguna aporta una base estructurada y actualizada; toda la cobertura encontrada es narrativa de prensa. Sigue sin fuente automatizable, no volver a reinvestigar sin una fuente concreta nueva en mano."
    }
```

- [ ] **Step 2: Validar que el JSON sigue siendo válido**

Run: `cd projects/informe_coyuntura && python -c "import json; json.load(open('data/politica/manuales.json', encoding='utf-8')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Agregar nota en `fetch_adhesion_reformas_provincial_serie`**

En `scripts/descargar_series.py`, la función tiene hoy (líneas 492-501):

```python
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

Reemplazar el docstring (sin tocar el cuerpo de la función):

```python
def fetch_adhesion_reformas_provincial_serie() -> list:
    """adhesion_reformas_provincial es un STOCK: la adhesión al RIGI es un
    evento único e irreversible por provincia, no una magnitud que fluctúe
    mes a mes — un solo punto con el valor actual, no un backfill año por
    año (no hay fuente con la fecha en la que cada provincia adhirió, así
    que no hay forma de reconstruir el pasado). Confirmado en vivo
    (2026-07-08): la tabla de MAGyP solo tiene 2 columnas (provincia, link a
    la ley), sin fecha de adhesión; el sitio que sí podría tenerla
    (trivia.consejo.org.ar, donde apuntan los links de ley) devuelve
    "Request Rejected" ante fetch directo — mismo patrón de WAF categórico
    que HCDN Diputados (ADR-0037), no reintentar sin una vía nueva.
    [[YYYY-01-01, % provincias]]."""
    resultado = politica.fetch_adhesion_reformas_provincial()
    if not resultado or resultado.get("valor") is None:
        return []
    return [[f"{date.today().year}-01-01", resultado["valor"]]]
```

- [ ] **Step 4: Corregir la línea desactualizada de `docs/cinturon_politica.md`**

El documento tiene hoy (línea 148, dentro de la sección `### cohesion_bloque`):

```
- Último valor publicado: 78% — este es el **placeholder manual pre-automatización** (congelado desde abril de 2026), no una medición de índice de Rice real: hasta que el bloqueo se resuelva, el nuevo cálculo todavía no tiene datos en vivo fluyendo → puntaje banda 79,0 (aplicado sobre ese placeholder, no sobre un dato Rice).
```

Reemplazar por:

```
- Último valor: **ausente**. El placeholder manual pre-automatización (78%, congelado desde abril de 2026) fue purgado del cache real (commit `3973d00`, 2026-07-07): al no ser una medición de índice de Rice genuina, arrastrarlo para siempre habría corrompido el ITCP con un valor de significado distinto (auditoría de código, hallazgo P1 de revisión externa). Mientras el bloqueo de HCDN no se resuelva (ver abajo), el indicador queda ausente y la dimensión `cohesion_interna` (20% del ITCP) se renormaliza al 100% sobre `cohesion_bloque_senado` — hoy sostiene sola esa dimensión completa (nota metodológica de auditoría, 2026-07-08).
```

- [ ] **Step 5: Correr la suite completa**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS (este task no toca ningún código ejecutable relevante a los tests).

- [ ] **Step 6: Commit (`scripts/descargar_series.py` tiene un WIP ajeno sin commitear — stagear solo el hunk propio)**

`scripts/descargar_series.py` ya tenía cambios sin commitear ANTES de este plan (un WIP de otra tarea, "motos" — visible en `git status` desde el inicio de la sesión). Verificar primero:

```bash
git diff scripts/descargar_series.py
```

El diff debe mostrar el WIP preexistente MÁS el docstring nuevo de `fetch_adhesion_reformas_provincial_serie` (Step 3). Stagear con `git add -p` y aceptar (`y`) SOLO el hunk del docstring nuevo, rechazando (`n`) cualquier otro hunk:

```bash
git add data/politica/manuales.json docs/cinturon_politica.md
git add -p scripts/descargar_series.py
```

Verificar antes de commitear que solo el hunk correcto quedó staged:

```bash
git diff --cached scripts/descargar_series.py
```

Expected: el diff staged muestra ÚNICAMENTE el cambio de docstring de `fetch_adhesion_reformas_provincial_serie` (Step 3) — ningún otro hunk del WIP preexistente.

```bash
git commit -m "docs(politica): registra 2 investigaciones sin salida + corrige línea desactualizada de cohesion_bloque

gobernadores_alineamiento (manuales.json) y adhesion_reformas_provincial
(descargar_series.py) fueron reinvestigados 2026-07-08 buscando backfill:
ninguno tiene fuente nueva (evita repetir la investigación en el futuro).
cinturon_politica.md:148 describía cohesion_bloque como si publicara un
valor (78) cuando el cache real ya lo tiene ausente desde la purga de
legado (3973d00) — corrige el texto y documenta la consecuencia
metodológica (cohesion_interna 100% sobre cohesion_bloque_senado)."
```

---

### Task 3: Sensibilidad standalone para ITCP en `sensibilidad.py`

**Files:**
- Modify: `scripts/sensibilidad.py:38-58`

**Interfaces:**
- Consumes: `itcp.BANDAS_ITCP` (ya existe, sin cambios)
- Produces: nada nuevo — `INDICES["itcp"]` sigue el mismo contrato que `INDICES["itcm"]`/`INDICES["itcg"]` que ya consume `analizar()`/`main()`.

- [ ] **Step 1: Agregar el import**

En `scripts/sensibilidad.py`, la sección de imports (líneas 37-40) es:

```python
import parametrica
import itcm
import itcg
import itvc as itvc_mod
```

Agregar `import itcp`:

```python
import parametrica
import itcm
import itcg
import itvc as itvc_mod
import itcp
```

- [ ] **Step 2: Agregar la entrada al dict `INDICES`**

El dict (líneas 51-58) es:

```python
INDICES = {
    "itcm": {"cinturon": "macro", "bandas": itcm.BANDAS_ITCM,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itcg": {"cinturon": "gestion", "bandas": itcg.BANDAS_ITCG,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itvc": {"cinturon": "vida_cotidiana", "bandas": None,   # continuo
             "tension": lambda v: round(min(10.0, max(0.0, 5 - (v - 100) * 0.2)), 1)},
}
```

Agregar la entrada `itcp` (mismo patrón que itcm/itcg — bandas discretas, tensión lineal):

```python
INDICES = {
    "itcm": {"cinturon": "macro", "bandas": itcm.BANDAS_ITCM,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itcg": {"cinturon": "gestion", "bandas": itcg.BANDAS_ITCG,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itvc": {"cinturon": "vida_cotidiana", "bandas": None,   # continuo
             "tension": lambda v: round(min(10.0, max(0.0, 5 - (v - 100) * 0.2)), 1)},
    "itcp": {"cinturon": "politica", "bandas": itcp.BANDAS_ITCP,
             "tension": lambda v: round((100 - v) / 10, 1)},
}
```

- [ ] **Step 3: Correr el script standalone (verificación en vivo — no hay suite de pytest para este archivo, mismo precedente que itcm/itcg/itvc)**

Run: `cd projects/informe_coyuntura && python scripts/sensibilidad.py`
Expected: en la salida de consola aparece un bloque `== ITCP —` con las 3 líneas de experimentos (`pesos`, `insumos`, `combinado`) y el listado de "componentes dominantes"; sin excepciones.

- [ ] **Step 4: Verificar el JSON de salida**

Run:
```bash
cd projects/informe_coyuntura && python -c "
import json
d = json.load(open('output/sensibilidad.json', encoding='utf-8'))
assert 'itcp' in d, 'falta la clave itcp'
assert set(d['itcp'].keys()) >= {'valor_publicado', 'valor_recomputado', 'experimentos', 'leave_one_out', 'tension'}
print('OK', d['itcp']['valor_publicado'], list(d['itcp']['leave_one_out'].items())[:2])
"
```
Expected: `OK <valor> [...]` sin excepción — el primer componente del leave-one-out (mayor |Δ|) debería ser `cohesion_bloque_senado`, consistente con lo que ya muestra `robustez_compacta` en el snapshot publicado (`informe.json` → `cinturones.politica.itcp.robustez.dominante`).

- [ ] **Step 5: Correr la suite completa de pytest**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS (este cambio no toca ningún archivo con tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/sensibilidad.py output/sensibilidad.json
git commit -m "feat(politica): agrega ITCP al análisis de sensibilidad standalone

sensibilidad.py ya cubría ITCM/ITCG/ITVC (output/sensibilidad.json) pero
no el ITCP -- gap de paridad analítica, no de producción (el ITCP YA
tiene robustez compacta corriendo en el snapshot publicado vía
publicar.py::_scoring_indice, confirmado en informe.json). Este agregado
suma el desglose completo (pesos/insumos/combinado + leave-one-out) al
artefacto standalone, mismo patrón que itcm/itcg. Componente dominante:
cohesion_bloque_senado (consistente con la robustez ya publicada)."
```

---

### Task 4: Backfill real de `cohesion_bloque_senado` (fix del bug de año)

**Files:**
- Modify: `scripts/politica.py:144-160` (agrega `_paced_post` después de `_paced_get`), `scripts/politica.py:1023-1057` (`_descubrir_actas_senado`)
- Test: `tests/test_politica_cohesion.py:425-447` (agrega test nuevo, modifica `test_descubrir_actas_senado_extrae_id_y_fecha`)

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `politica._paced_post(session, base_url, path, data, **kwargs)` — mismo contrato que `_paced_get` pero con form-data.

- [ ] **Step 1: Escribir el test que falla para `_paced_post`**

Agregar en `tests/test_politica_cohesion.py`, inmediatamente después de `test_paced_get_reusa_logica_de_pacing` (línea 431):

```python
def test_paced_post_reusa_logica_de_pacing(monkeypatch):
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._paced_post(session, "https://www.senado.gob.ar", "/votaciones/actas",
                              data={"busqueda_actas[anio]": "2024"})
    assert r.status_code == 200
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2024"},
        timeout=politica.HTTP_TIMEOUT,
    )


def test_paced_post_reintenta_ante_403(monkeypatch):
    session = MagicMock()
    resp_403 = MagicMock(status_code=403)
    resp_200 = MagicMock(status_code=200)
    session.post.side_effect = [resp_403, resp_403, resp_200]
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._paced_post(session, "https://www.senado.gob.ar", "/votaciones/actas",
                                      data={"busqueda_actas[anio]": "2023"})
    assert resultado is resp_200
    assert session.post.call_count == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k paced_post -v`
Expected: 2 FAIL con `AttributeError: module 'politica' has no attribute '_paced_post'`

- [ ] **Step 3: Implementar `_paced_post`**

En `scripts/politica.py`, inmediatamente después de `_paced_get` (que termina en la línea 160, justo antes de `def _hcdn_votaciones_get`):

```python
def _paced_post(session: requests.Session, base_url: str, path: str, data: dict, **kwargs):
    """POST con el mismo pacing/retry que _paced_get (backoff ante 403, hasta
    3 intentos). Usado por _descubrir_actas_senado: el listado de actas de
    Senado requiere POST con busqueda_actas[anio] en el form -- un GET plano
    siempre devuelve el año en curso (bug encontrado en auditoría 2026-07-08,
    ver commit)."""
    url = f"{base_url}{path}"
    for intento in range(3):
        time.sleep(_HCDN_VOTACIONES_DELAY)
        try:
            r = session.post(url, data=data, timeout=HTTP_TIMEOUT, **kwargs)
        except requests.RequestException:
            return None
        if r.status_code == 200:
            return r
        if r.status_code == 403:
            continue
        return None
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k paced_post -v`
Expected: 2 PASS

- [ ] **Step 5: Actualizar el test existente `test_descubrir_actas_senado_extrae_id_y_fecha`**

Este test (línea 443-447) hoy mockea `session.get` porque `_descubrir_actas_senado` hace un GET. Después del fix va a hacer un POST — actualizar el mock y agregar el assert del año pedido:

Reemplazar:

```python
def test_descubrir_actas_senado_extrae_id_y_fecha():
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    actas = politica._descubrir_actas_senado(session, 2026)
    assert actas == [{"id": "2623", "fecha": datetime(2026, 2, 11)}]
```

Por:

```python
def test_descubrir_actas_senado_extrae_id_y_fecha():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    actas = politica._descubrir_actas_senado(session, 2026)
    assert actas == [{"id": "2623", "fecha": datetime(2026, 2, 11)}]
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2026"},
        timeout=politica.HTTP_TIMEOUT,
    )


def test_descubrir_actas_senado_pide_el_anio_correcto_no_el_actual():
    # Regresión directa del bug de auditoría 2026-07-08: un año PASADO debe
    # pedirse explícitamente en el form, no depender de que el servidor
    # devuelva el año en curso por default.
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    politica._descubrir_actas_senado(session, 2023)
    session.post.assert_called_with(
        "https://www.senado.gob.ar/votaciones/actas",
        data={"busqueda_actas[anio]": "2023"},
        timeout=politica.HTTP_TIMEOUT,
    )
```

Nota: `FIXTURE_LISTADO_SENADO` tiene una fila fechada 2026 — con `anio=2023` el resultado de `_descubrir_actas_senado` será `[]` (la fila no matchea `fecha.year != anio`), pero eso no importa para este test: lo que se verifica es el PEDIDO (que el POST llevó `anio=2023`), no el resultado del parseo, que ya está cubierto por el test anterior.

- [ ] **Step 6: Implementar el fix en `_descubrir_actas_senado`**

La función (líneas 1023-1057) hoy empieza así:

```python
def _descubrir_actas_senado(session: requests.Session, anio: int):
    """..."""
    r = _paced_get(session, SENADO_BASE, "/votaciones/actas")
    if r is None:
        return None
```

Reemplazar la línea del request (sin tocar el resto de la función ni su docstring más allá de la nota agregada):

```python
def _descubrir_actas_senado(session: requests.Session, anio: int):
    """GET a /votaciones/actas (listado con fecha en <span style="display:none">
    YYYYMMDD</span> y link <a href="/votaciones/detalleActa/{id}">) ->
    [{id, fecha}] del año dado. Estructura confirmada en vivo (Senado, HTML
    server-side, sin headless browser). parser="html.parser": lxml no está en
    requirements.txt (Tarea 4 del plan de cohesion_bloque). Reusa
    _RE_DISPLAY_NONE (mismo plan, Tarea 4) en vez de un match exacto de
    "display:none" — la Tarea 4 confirmó que el HTML real de HCDN usa
    "display: none" CON espacio; dado que Senado es la misma familia de sitios
    de gobierno, no asumir que acá sí será sin espacio sin verificarlo en vivo
    (ver Step de verificación más abajo).

    FIX (auditoría 2026-07-08): un GET plano a esta URL siempre devuelve el
    listado del año EN CURSO -- el filtro `fecha.year != anio` de abajo
    descartaba todo cuando `anio` era un año pasado, y el backfill
    'funcionaba' produciendo 1 solo punto real (el año en curso). Verificado
    en vivo: el sitio acepta POST con busqueda_actas[anio]=<año> y devuelve el
    listado real de ESE año (26 actas en 2023, 91 en 2024, 95 en 2025, sin
    bloqueo anti-bot, a diferencia de HCDN Diputados)."""
    r = _paced_post(session, SENADO_BASE, "/votaciones/actas",
                     data={"busqueda_actas[anio]": str(anio)})
    if r is None:
        return None
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -v`
Expected: todos PASS, incluidos los 2 tests de `_descubrir_actas_senado` y los 2 de `_paced_post`.

- [ ] **Step 8: Correr la suite completa**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS.

- [ ] **Step 9: Verificación en vivo del backfill real**

Run: `cd projects/informe_coyuntura && python scripts/descargar_series.py`

Este comando regenera los 4 CSV de `output/series/` (macro, política, vida, gestión) desde cero, contra fuentes en vivo — **antes de tocar git, revisar qué cambió realmente**:

Run: `cd projects/informe_coyuntura && git diff --stat output/series/`

Expected: `output/series/politica.csv` cambia (más filas de `cohesion_bloque_senado`); los otros 3 CSV pueden mostrarse "modificados" por el estado dirty preexistente del repo (ajeno a esta tarea, ya presente en `git status` antes de empezar) — **no tocar ni commitear esos otros 3 archivos**.

Run:
```bash
cd projects/informe_coyuntura && python -c "
import csv
filas = [r for r in csv.reader(open('output/series/politica.csv', encoding='utf-8')) if r[1] == 'cohesion_bloque_senado']
print(f'{len(filas)} puntos de cohesion_bloque_senado:')
for r in sorted(filas): print(' ', r[0], r[2])
"
```
Expected: 4 filas (una por año 2023, 2024, 2025, 2026), no 1. Si aparecen menos de 4, revisar si `senado.gob.ar` devolvió algún año sin actas divididas dentro de la ventana de 366 días (posible pero no lo esperado según la verificación previa) antes de continuar.

- [ ] **Step 10: Commit (solo los archivos de esta tarea)**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB" && git add \
  projects/informe_coyuntura/scripts/politica.py \
  projects/informe_coyuntura/tests/test_politica_cohesion.py \
  projects/informe_coyuntura/output/series/politica.csv
git commit -m "fix(politica): cohesion_bloque_senado — backfill real 2023-2026 (bug de año en _descubrir_actas_senado)

_descubrir_actas_senado() hacía un GET sin parámetro de año -- el
servidor siempre devuelve el listado del año en curso, y el backfill
'funcionaba' produciendo 1 solo punto real (el año en curso), como
documentó el Task 14 report. Verificado en vivo (auditoría 2026-07-08):
senado.gob.ar/votaciones/actas acepta POST con busqueda_actas[anio]=<año>
y devuelve el listado real de ese año, sin bloqueo anti-bot. Nuevo
_paced_post() (mismo pacing/retry que _paced_get) + fix quirúrgico en
_descubrir_actas_senado(). fetch_cohesion_bloque_senado_serie() (que ya
iteraba 2023-2026 correctamente) no necesitó cambios -- el bug estaba
aislado a una función. Corrida real: 4 puntos anuales, no 1."
```

---

### Task 5: Backfill parcial de `movilizacion_cepa`

**Files:**
- Modify: `scripts/politica.py:441-522` (refactor `fetch_cepa_movilizacion`, agrega `_extraer_cifra_cepa` y `_fecha_informe_cepa`, agrega `fetch_cepa_movilizacion_serie`)
- Modify: `scripts/descargar_series.py` (registrar en `POLITICA_DERIVADAS`)
- Test: `tests/test_politica_cohesion.py` (nuevos tests con fixtures reales)

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `politica._extraer_cifra_cepa(html: str) -> dict | None` (`{"valor", "cifra_cruda", "metrica"}`), `politica._fecha_informe_cepa(html: str) -> str` (`YYYY-MM-DD`), `politica.fetch_cepa_movilizacion_serie(max_paginas: int = 40) -> list[[str, float]]`.

**Contexto verificado en vivo (2026-07-08):** los 4 informes de CEPA con "conflictividad"/"conflictos-laborales" en la URL (ids 809, 773, 748, 739) traen un tag `<meta property="datePublished" content="YYYY-MM-DD...">` — fecha real de publicación, no la fecha de la corrida. Pero **solo 2 de los 4** (809 y 773) citan la cifra con la MISMA ancla temporal que ya interpreta `fetch_cepa_movilizacion()` ("desde inicios del año en curso, se registraron, al menos, N conflictos laborales de trabajadores estatales") — 748 acumula desde ene-2024 y usa la palabra "casos" en vez de "conflictos"; 739 acumula desde dic-2023 ("durante el gobierno de Milei") y no trae ninguna de las dos frases-gatillo del regex existente. Ambos quedan **deliberadamente fuera** de la serie: forzarlos por la misma escala 0-200 los clavaría en el techo (100,0) sin representar una tendencia real, mezclando ventanas de acumulación no comparables.

- [ ] **Step 1: Escribir los tests que fallan (con fixtures = texto real verificado)**

Agregar en `tests/test_politica_cohesion.py`, en una sección nueva al final del archivo:

```python
# ── _extraer_cifra_cepa / _fecha_informe_cepa (backfill movilizacion_cepa) ──
# Fixtures = fragmentos REALES de 4 informes de centrocepa.com.ar verificados
# en vivo 2026-07-08 (ids 809, 773, 748, 739). 748 y 739 acumulan desde un
# ancla temporal distinta (ene-2024 / dic-2023, no "desde inicios del año en
# curso") y NO deben matchear -- se excluyen deliberadamente de la serie.

FRAGMENTO_809 = (
    '<meta property="datePublished" content="2026-06-09T15:40:01-03:00">'
    "Desde inicios del 2026 se registraron, al menos, 101 conflictos "
    "laborales de trabajadores estatales en todo el país."
)
FRAGMENTO_773 = (
    '<meta property="datePublished" content="2026-04-09T23:47:31-03:00">'
    "Desde inicios del 2026 se registraron, al menos, 92 conflictos "
    "laborales de trabajadores estatales en todo el país."
)
FRAGMENTO_748 = (
    '<meta property="datePublished" content="2026-02-18T18:29:01-03:00">'
    "Desde enero 2024 hasta el 5 de febrero 2026 se registraron al menos "
    "717 casos de conflictividad laboral en todo el país."
)
FRAGMENTO_739 = (
    '<meta property="datePublished" content="2025-12-31T20:40:01-03:00">'
    "Ofrecemos un recuentro gráfico de los 629 conflictos laborales y "
    "cierres de empresas registrados durante el gobierno de Javier Milei."
)


def test_extraer_cifra_cepa_informe_809():
    r = politica._extraer_cifra_cepa(FRAGMENTO_809)
    assert r["cifra_cruda"] == 101.0
    assert r["valor"] == round(min(100.0, 101.0 / 200.0 * 100.0), 1)


def test_extraer_cifra_cepa_informe_773():
    r = politica._extraer_cifra_cepa(FRAGMENTO_773)
    assert r["cifra_cruda"] == 92.0


def test_extraer_cifra_cepa_informe_748_no_matchea_ancla_distinta():
    # "717 casos" (no "conflictos") + ancla "desde enero 2024" -- no comparable
    assert politica._extraer_cifra_cepa(FRAGMENTO_748) is None


def test_extraer_cifra_cepa_informe_739_no_matchea_ancla_distinta():
    # "629 conflictos" pero sin ninguna de las 2 frases-gatillo del regex
    # ("al menos" / "se registraron" inmediatamente antes del número)
    assert politica._extraer_cifra_cepa(FRAGMENTO_739) is None


def test_fecha_informe_cepa_extrae_datepublished():
    assert politica._fecha_informe_cepa(FRAGMENTO_809) == "2026-06-09"
    assert politica._fecha_informe_cepa(FRAGMENTO_748) == "2026-02-18"


def test_fecha_informe_cepa_fallback_a_hoy_si_no_hay_meta():
    from datetime import date
    assert politica._fecha_informe_cepa("<html>sin meta tag</html>") == str(date.today())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k "extraer_cifra_cepa or fecha_informe_cepa" -v`
Expected: 6 FAIL con `AttributeError: module 'politica' has no attribute '_extraer_cifra_cepa'` (y luego `_fecha_informe_cepa`)

- [ ] **Step 3: Implementar `_extraer_cifra_cepa` y `_fecha_informe_cepa`**

En `scripts/politica.py`, agregar ANTES de `def fetch_cepa_movilizacion()` (línea 441) estas dos funciones y la constante de regex de fecha:

```python
_RE_CEPA_FECHA = re.compile(r'property="datePublished"\s+content="(\d{4}-\d{2}-\d{2})')


def _fecha_informe_cepa(html: str) -> str:
    """Fecha real de publicación del informe (meta datePublished), NO la
    fecha de la corrida del scraper -- necesaria para el backfill (cada
    informe histórico debe fechar SU período, no 'hoy'). Fallback a hoy si
    el informe no trae el tag (no esperado: confirmado presente en los 4
    informes históricos verificados en vivo, 2026-07-08)."""
    m = _RE_CEPA_FECHA.search(html)
    return m.group(1) if m else str(date.today())


def _extraer_cifra_cepa(html: str) -> dict | None:
    """Cifra de conflictividad de UN informe CEPA (índice 0-100
    normalizado), con el mismo regex que fetch_cepa_movilizacion() usa para
    el informe vigente. None si el informe no matchea ninguno de los dos
    patrones conocidos ("X casos por mes" / "al menos N conflictos") --
    DELIBERADO: informes que citan una cifra acumulada bajo un ancla
    temporal DISTINTA ("desde enero 2024" o "durante todo el gobierno de
    Milei", en vez de "desde inicios del año en curso") no son comparables
    en la misma escala 0-200 y no deben forzarse a la serie (verificado en
    vivo 2026-07-08: los informes CEPA de "conflictividad a 2 años" y
    "mapa federal" quedan fuera de la serie por este motivo, no por un
    error de parseo)."""
    m_mes = re.search(
        r"(\d+(?:[.,]\d+)?)\s+casos?\s+por\s+mes"
        r"|promedio\s+de\s+(\d+(?:[.,]\d+)?)\s+casos?\s+mensuales?",
        html, re.IGNORECASE
    )
    m_tot = re.search(
        r"(?:al menos,?\s+|se registraron,?\s+al menos,?\s+|se registraron\s+)"
        r"(\d+)\s+conflictos?",
        html, re.IGNORECASE
    )
    if m_mes:
        raw = (m_mes.group(1) or m_mes.group(2)).replace(",", ".")
        cifra = float(raw)
        return {"valor": round(min(100.0, (cifra / CEPA_MAX_CASOS_MES) * 100.0), 1),
                "cifra_cruda": cifra, "metrica": f"{cifra} casos/mes"}
    if m_tot:
        cifra = float(m_tot.group(1))
        return {"valor": round(min(100.0, (cifra / CEPA_MAX_CONFLICTOS_TOT) * 100.0), 1),
                "cifra_cruda": cifra, "metrica": f"{cifra} conflictos acumulados"}
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k "extraer_cifra_cepa or fecha_informe_cepa" -v`
Expected: 6 PASS

- [ ] **Step 5: Refactorizar `fetch_cepa_movilizacion()` para reusar las 2 funciones nuevas**

La función completa hoy (líneas 441-522) es:

```python
def fetch_cepa_movilizacion() -> dict | None:
    """
    Conflictividad social CEPA — índice 0–100 normalizado.
    Estrategia: listar centrocepa.com.ar/informes → encontrar el último informe
    con "conflictividad" en la URL → parsear HTML del informe buscando
    "X casos por mes" o "al menos N conflictos".
    Dimensión: conflicto social (Matus).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        _warn("movilizacion_cepa", "beautifulsoup4 no disponible")
        return None

    try:
        # La sección de informes está paginada (start=0, 10, 20...).
        # Buscar en hasta 5 páginas (50 informes) para encontrar el más reciente
        # con "conflictividad" o "conflictos-laborales" en la URL.
        links = []
        for page in range(5):
            page_url = CEPA_INFORMES_URL if page == 0 else f"{CEPA_INFORMES_URL}?start={page * 10}"
            r = requests.get(page_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            page_links = [
                a for a in soup.find_all("a", href=True)
                if any(kw in a.get("href", "").lower() for kw in ("conflictividad", "conflictos-laborales"))
            ]
            links.extend(page_links)
            if links:
                break

        if not links:
            raise ValueError("No se encontraron links de conflictividad en las primeras 5 páginas de informes CEPA")

        def url_num(a):
            m = re.search(r"/(\d+)[/-]", a["href"])
            return int(m.group(1)) if m else 0

        links.sort(key=url_num, reverse=True)
        href = links[0]["href"]
        informe_url = ("https://centrocepa.com.ar" + href) if href.startswith("/") else href

        r2 = requests.get(informe_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r2.raise_for_status()

        m_mes = re.search(
            r"(\d+(?:[.,]\d+)?)\s+casos?\s+por\s+mes"
            r"|promedio\s+de\s+(\d+(?:[.,]\d+)?)\s+casos?\s+mensuales?",
            r2.text, re.IGNORECASE
        )
        m_tot = re.search(
            r"(?:al menos,?\s+|se registraron,?\s+al menos,?\s+|se registraron\s+)"
            r"(\d+)\s+conflictos?",
            r2.text, re.IGNORECASE
        )

        if m_mes:
            raw = (m_mes.group(1) or m_mes.group(2)).replace(",", ".")
            cifra = float(raw)
            val = round(min(100.0, (cifra / CEPA_MAX_CASOS_MES) * 100.0), 1)
            metrica = f"{cifra} casos/mes"
        elif m_tot:
            cifra = float(m_tot.group(1))
            val = round(min(100.0, (cifra / CEPA_MAX_CONFLICTOS_TOT) * 100.0), 1)
            metrica = f"{cifra} conflictos acumulados"
        else:
            raise ValueError(f"No se encontró patrón de conflictividad en {informe_url}")

        return {
            "valor": val,
            "cifra_cruda": cifra,
            "metrica": metrica,
            "unidad": "Índice (0–100)",
            "fuente": informe_url,
            "fecha_dato": str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("movilizacion_cepa", str(e))
        return None
```

Reemplazar TODO el bloque desde `r2 = requests.get(...)` hasta el `return {...}` (manteniendo intacto todo lo anterior: el docstring, el import de BeautifulSoup, el descubrimiento de `links`, y el `except Exception` final):

```python
def fetch_cepa_movilizacion() -> dict | None:
    """
    Conflictividad social CEPA — índice 0–100 normalizado.
    Estrategia: listar centrocepa.com.ar/informes → encontrar el último informe
    con "conflictividad" en la URL → parsear HTML del informe buscando
    "X casos por mes" o "al menos N conflictos".
    Dimensión: conflicto social (Matus).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        _warn("movilizacion_cepa", "beautifulsoup4 no disponible")
        return None

    try:
        # La sección de informes está paginada (start=0, 10, 20...).
        # Buscar en hasta 5 páginas (50 informes) para encontrar el más reciente
        # con "conflictividad" o "conflictos-laborales" en la URL.
        links = []
        for page in range(5):
            page_url = CEPA_INFORMES_URL if page == 0 else f"{CEPA_INFORMES_URL}?start={page * 10}"
            r = requests.get(page_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            page_links = [
                a for a in soup.find_all("a", href=True)
                if any(kw in a.get("href", "").lower() for kw in ("conflictividad", "conflictos-laborales"))
            ]
            links.extend(page_links)
            if links:
                break

        if not links:
            raise ValueError("No se encontraron links de conflictividad en las primeras 5 páginas de informes CEPA")

        def url_num(a):
            m = re.search(r"/(\d+)[/-]", a["href"])
            return int(m.group(1)) if m else 0

        links.sort(key=url_num, reverse=True)
        href = links[0]["href"]
        informe_url = ("https://centrocepa.com.ar" + href) if href.startswith("/") else href

        r2 = requests.get(informe_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r2.raise_for_status()

        cifra_info = _extraer_cifra_cepa(r2.text)
        if cifra_info is None:
            raise ValueError(f"No se encontró patrón de conflictividad en {informe_url}")

        return {
            **cifra_info,
            "unidad": "Índice (0–100)",
            "fuente": informe_url,
            "fecha_dato": _fecha_informe_cepa(r2.text),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("movilizacion_cepa", str(e))
        return None
```

Nota: este refactor cambia `fecha_dato` de `str(date.today())` (fecha de la corrida) a `_fecha_informe_cepa(r2.text)` (fecha real de publicación del informe) — mejora la corrección del indicador VIGENTE, no solo del backfill (el informe 809 fue publicado 2026-06-09, no el día que corre el scraper).

- [ ] **Step 6: Ningún test existente debería romperse — verificar**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v -k cepa`
Expected: no hay tests previos de `fetch_cepa_movilizacion()` en la suite (confirmar con `grep -rn "fetch_cepa_movilizacion" tests/` antes de este step) — si aparece alguno con `fecha_dato` hardcodeado a `date.today()`, ajustarlo para no asumir esa fecha exacta.

- [ ] **Step 7: Implementar `fetch_cepa_movilizacion_serie` en `scripts/descargar_series.py`**

Agregar inmediatamente después de `fetch_adhesion_reformas_provincial_serie` (que termina en la línea 501, justo antes de `POLITICA_DERIVADAS`):

```python
def fetch_cepa_movilizacion_serie(max_paginas: int = 40) -> list:
    """Backfill histórico de movilizacion_cepa: escanea hasta `max_paginas`
    páginas de centrocepa.com.ar/documentos/informes (10 informes por
    página) buscando TODOS los links con "conflictividad"/"conflictos-laborales"
    en la URL -- no solo el más reciente, a diferencia de
    politica.fetch_cepa_movilizacion(). Verificado en vivo (2026-07-08): con
    40 páginas se cubren de sobra los ~4 informes de este tipo publicados
    hasta la fecha (CEPA recién empezó a publicarlos a fines de 2025 -- no
    hay nada más atrás que buscar). Reusa politica._extraer_cifra_cepa /
    politica._fecha_informe_cepa: informes que citan la cifra bajo un ancla
    temporal distinta (ver docstring de _extraer_cifra_cepa) devuelven None
    y se saltean, no rompen el backfill. [[YYYY-MM-DD, índice 0-100]]."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[WARN] movilizacion_cepa_serie: beautifulsoup4 no disponible")
        return []

    links = []
    for page in range(max_paginas):
        page_url = politica.CEPA_INFORMES_URL if page == 0 else f"{politica.CEPA_INFORMES_URL}?start={page * 10}"
        try:
            r = requests.get(page_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
        except requests.RequestException:
            break
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href_lower = a["href"].lower()
            if any(kw in href_lower for kw in ("conflictividad", "conflictos-laborales")):
                links.append(a["href"])

    out = []
    vistos = set()
    for href in links:
        if href in vistos:
            continue
        vistos.add(href)
        informe_url = ("https://centrocepa.com.ar" + href) if href.startswith("/") else href
        try:
            r2 = requests.get(informe_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r2.raise_for_status()
        except requests.RequestException as e:
            print(f"[WARN] movilizacion_cepa_serie: {informe_url}: {e}")
            continue
        cifra_info = politica._extraer_cifra_cepa(r2.text)
        if cifra_info is None:
            continue   # ancla temporal distinta -- ver docstring, no es un error
        fecha = politica._fecha_informe_cepa(r2.text)
        out.append([fecha, cifra_info["valor"]])

    out.sort(key=lambda x: x[0])
    return out
```

- [ ] **Step 8: Registrar en `POLITICA_DERIVADAS`**

El registro (líneas 504-524) tiene esta entrada relevante que hay que agregar junto a las demás, antes del comentario final sobre `protestas_caba`:

```python
POLITICA_DERIVADAS = [
    ("votometro_ventaja_lla", "pp (brecha LLA−PJ)", "Votómetro CIGOB", fetch_votometro_serie),
    ("iaf_transferencias", "% i.a. real", "RON Hacienda + IPC INDEC (dic-dic)", fetch_iaf_serie),
    ("ratio_dnu", "DNUs por ley", "InfoLeg (conteo anual)", fetch_ratio_dnu_serie),
    ("eficacia_legislativa", "% proyectos PE aprobados (12m móviles)", "datos.hcdn.gob.ar CKAN", fetch_eficacia_serie),
    ("veto_quorum", "% sesiones fracasadas (por período)", "datos.hcdn.gob.ar CKAN", fetch_veto_quorum_serie),
    ("comisiones_caidas", "% con dictamen sin sanción (12m móviles)", "datos.hcdn.gob.ar CKAN", fetch_comisiones_serie),
    ("cohesion_bloque", "% cohesión (índice de Rice, anual)",
     "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_serie),
    ("cohesion_bloque_senado", "% cohesión (índice de Rice, Senado, anual)",
     "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_senado_serie),
    ("adhesion_reformas_provincial", "% de provincias (sobre 24) adheridas al RIGI",
     "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
     fetch_adhesion_reformas_provincial_serie),
    # protestas_caba NO se registra acá: ...
```

Agregar la entrada de `movilizacion_cepa` inmediatamente después de `adhesion_reformas_provincial` y antes del comentario de `protestas_caba`:

```python
    ("adhesion_reformas_provincial", "% de provincias (sobre 24) adheridas al RIGI",
     "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
     fetch_adhesion_reformas_provincial_serie),
    ("movilizacion_cepa", "Índice de conflictividad social (0-100)",
     "Centro CEPA — informes de conflictividad (elaboración CIGOB)",
     fetch_cepa_movilizacion_serie),
    # protestas_caba NO se registra acá: ...
```

- [ ] **Step 9: Correr la suite completa**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS.

- [ ] **Step 10: Verificación en vivo del backfill**

Run: `cd projects/informe_coyuntura && python scripts/descargar_series.py`

Run:
```bash
cd projects/informe_coyuntura && python -c "
import csv
filas = [r for r in csv.reader(open('output/series/politica.csv', encoding='utf-8')) if r[1] == 'movilizacion_cepa']
print(f'{len(filas)} puntos de movilizacion_cepa:')
for r in sorted(filas): print(' ', r[0], r[2])
"
```
Expected: 2 puntos (2026-04-09 y 2026-06-09), no 1 — con los valores derivados de 92 y 101 conflictos acumulados respectivamente. Si CEPA publicó un informe nuevo entre el 2026-07-08 (fecha de esta investigación) y la corrida real, puede aparecer un tercer punto — no es un problema, es evidencia de que el backfill sigue funcionando hacia adelante.

- [ ] **Step 11: Commit (`scripts/descargar_series.py` sigue con el WIP ajeno — stagear solo los hunks propios de esta tarea)**

Mismo cuidado que en Task 2: `scripts/descargar_series.py` tiene el WIP ajeno ("motos") sin commitear desde antes de este plan, ahora además con el docstring del Task 2 ya commiteado (así que ESE hunk ya no aparece acá) y los 2 hunks nuevos de este task (la función `fetch_cepa_movilizacion_serie` + la línea en `POLITICA_DERIVADAS`).

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git diff projects/informe_coyuntura/scripts/descargar_series.py
```

Revisar el diff completo y confirmar cuáles hunks son de esta tarea. Stagear con `git add -p` aceptando (`y`) solo esos 2 hunks:

```bash
git add \
  projects/informe_coyuntura/scripts/politica.py \
  projects/informe_coyuntura/tests/test_politica_cohesion.py \
  projects/informe_coyuntura/output/series/politica.csv
git add -p projects/informe_coyuntura/scripts/descargar_series.py
```

Verificar antes de commitear:

```bash
git diff --cached projects/informe_coyuntura/scripts/descargar_series.py
```

Expected: el diff staged muestra ÚNICAMENTE `fetch_cepa_movilizacion_serie` (Step 7) y su registro en `POLITICA_DERIVADAS` (Step 8) — ningún hunk del WIP ajeno.

```bash
git commit -m "feat(politica): backfill parcial de movilizacion_cepa (2 puntos reales, dic-2025→jul-2026)

CEPA recién empezó a publicar informes de 'conflictividad' a fines de
2025 -- no hay nada más atrás que backfillear (límite real de la fuente,
no un bug). De los 4 informes existentes, solo 2 (jun/abr-2026) citan la
cifra bajo la MISMA ancla temporal ('desde inicios del año en curso')
que ya interpreta fetch_cepa_movilizacion(); los otros 2 acumulan desde
ene-2024/dic-2023 y quedan deliberadamente fuera de la serie (forzarlos
por la misma escala 0-200 los clavaría en el techo, sin representar una
tendencia real). Refactor: _extraer_cifra_cepa/_fecha_informe_cepa
compartidas entre el fetch vigente y el nuevo _serie -- de paso corrige
fecha_dato del indicador vigente (ahora usa la fecha real de publicación
del informe, datePublished, no la fecha de la corrida del scraper)."
```

---

### Task 6: Actualización final de `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md` (secciones "Score actual del cinturón", "Bandas provisionales", detalle de `cohesion_bloque_senado` y `movilizacion_cepa`)

**Depende de:** Tasks 1-5 ya commiteadas (corrida real con todos los fixes aplicados).

- [ ] **Step 1: Corrida real completa**

Run:
```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py && python scripts/politica.py
```

- [ ] **Step 2: Extraer los valores reales para el doc**

Run:
```bash
cd projects/informe_coyuntura && python -c "
import json
d = json.load(open('output/cache/politica.json', encoding='utf-8'))
print('score:', d['score'])
print('itcp:', d['itcp']['valor'], d['itcp']['banda_legible'])
csb = d['indicadores'].get('cohesion_bloque_senado', {})
print('cohesion_bloque_senado:', csb.get('valor'), csb.get('fecha_dato'), csb.get('n_actas'))
mc = d['indicadores'].get('movilizacion_cepa', {})
print('movilizacion_cepa:', mc.get('valor'), mc.get('fecha_dato'), mc.get('metrica'))
"
```

- [ ] **Step 3: Actualizar la fila de `cohesion_bloque_senado` en la sección "Detalle por indicador"**

Ubicar la sección `### cohesion_bloque_senado` (línea ~151-157 antes de este plan) y reemplazar la línea que dice "Último valor: 99,5%..." por el valor real de la corrida del Step 2, siguiendo el mismo formato que las demás secciones de detalle (ej. `"Último valor: {valor}% (dato del {fecha_dato}) → puntaje banda {puntaje}"`). Agregar una oración nueva: "Backfill real disponible desde 2026-07-08: serie anual 2023-2026 (4 puntos), ver `output/series/politica.csv`" — y quitar `cohesion_bloque_senado` de la lista de "Bandas provisionales" del Encuadre SOLO si el analista decide recalibrar (este plan NO recalibra bandas — dejar la marca "provisional" tal cual está, la nueva serie es un insumo para una recalibración futura, no una recalibración en sí).

- [ ] **Step 4: Actualizar la sección `### movilizacion_cepa`**

Agregar una oración al final de la sección existente: "Backfill parcial disponible desde 2026-07-08: 2 puntos reales adicionales (abr-2026, jun-2026) — CEPA no publicaba este tipo de informe antes de fines de 2025, así que no hay historia más atrás que reconstruir (ver `output/series/politica.csv`)."

- [ ] **Step 5: Actualizar "Score actual del cinturón" (línea ~83)**

Reemplazar la línea completa con los valores reales de la corrida del Step 2 (score, ITCP, banda, conteo de indicadores frescos), siguiendo el mismo formato que la versión actual pero con la fecha de esta corrida (no inventar una fecha — usar la fecha real en la que se ejecuta este step).

- [ ] **Step 6: Revisar el documento completo una vez editado**

Leer `docs/cinturon_politica.md` de punta a punta y confirmar que no queda ninguna referencia contradictoria entre las secciones tocadas por este plan (Encuadre, Detalle por indicador, Score actual) — en particular que la sección de `cohesion_bloque` (Diputados) siga describiendo el estado ausente/bloqueado correctamente (ya corregida en Task 2) y no haya quedado ninguna mención residual del placeholder 78%.

- [ ] **Step 7: Correr la suite completa (por higiene, este task no toca código)**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS.

- [ ] **Step 8: Commit**

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): sincroniza cinturon_politica.md con los resultados reales de la profundización ITCP

Refleja la corrida real post Tasks 1-5: backfill de cohesion_bloque_senado
(4 puntos anuales 2023-2026) y movilizacion_cepa (2 puntos reales
adicionales), score y valor ITCP actualizados. Las bandas provisionales
NO se recalibran en este pase (queda para un análisis dedicado con la
serie ya poblada)."
```

---

## Self-Review

**1. Cobertura del spec:**
- Sub-proyecto 1 (backfill cohesion_bloque_senado) → Task 4. ✓
- Sub-proyecto 2 (backfill parcial movilizacion_cepa) → Task 5. ✓
- Sub-proyecto 3 (correcciones menores: gate protestas_caba, doc stale, manuales.json, comentario adhesion) → Tasks 1 y 2. ✓
- Sub-proyecto 4 (sensibilidad standalone ITCP) → Task 3. ✓
- Orden de ejecución (3→4→1→2→5 del spec) → Tasks 1,2 (correcciones) → 3 (sensibilidad) → 4 (senado) → 5 (cepa) → 6 (doc final). ✓ mismo orden.
- "No se recalibran bandas provisionales" (constraint global del spec) → explícito en Tasks 4 y 6. ✓
- "No se toca cohesion_bloque Diputados ni el motor parametrica.py" → ningún task lo modifica. ✓

**2. Placeholder scan:** sin "TBD"/"fill in details". Los únicos pasos sin un valor numérico exacto pre-escrito son Task 6 (doc final, depende necesariamente de una corrida real que todavía no ocurrió) y están resueltos con comandos EXACTOS que extraen los campos exactos a usar — no son placeholders vagos, son pasos data-dependientes con procedimiento completo.

**3. Consistencia de tipos/nombres:**
- `_resultado_utilizable(nombre, resultado)` (Task 1) usado consistentemente en `main()`.
- `_paced_post(session, base_url, path, data, **kwargs)` (Task 4) con la misma firma en el test y en la implementación.
- `_extraer_cifra_cepa(html) -> dict | None` y `_fecha_informe_cepa(html) -> str` (Task 5) con firmas y claves (`valor`, `cifra_cruda`, `metrica`) consistentes entre `fetch_cepa_movilizacion()` refactorizado y `fetch_cepa_movilizacion_serie()` en el otro archivo.
- `POLITICA_DERIVADAS` sigue la 4-tupla `(clave, unidad, fuente, fetch_fn)` en la nueva entrada de `movilizacion_cepa`, igual que las 3 entradas existentes de política.

## Riesgos operativos a tener presente durante la ejecución

- `scripts/descargar_series.py` tiene un WIP ajeno sin commitear (feature de "motos", ya presente en `git status` antes de empezar este plan) — Tasks 2 y 5 lo tocan (docstring y función nueva respectivamente). Usar SIEMPRE `git add -p` + verificar con `git diff --cached` antes de commitear, nunca `git add scripts/descargar_series.py` a secas (ver Steps de commit de Tasks 2 y 5).
- Tasks 4 y 5 pegan contra sitios reales (`senado.gob.ar`, `centrocepa.com.ar`) — si algún fetch falla en el momento de ejecutar (caída temporal del sitio, cambio de estructura), no forzar: recibir `[]`/`None` y reportarlo, no inventar datos.
- `python scripts/descargar_series.py` regenera los 4 CSV de `output/series/` (todos los cinturones) — commitear SOLO `politica.csv` en cada task, dejando intacto cualquier estado dirty preexistente de los otros 3 archivos (ya presente en `git status` antes de empezar este plan, ajeno a este trabajo).
- `python scripts/politica.py` (Task 6) también toca `data/historico/indicadores.json` vía acumulación histórica incondicional — mismo cuidado: no commitear ese archivo si ya estaba dirty por trabajo ajeno (verificar con `git status` antes de cada `git add`).
