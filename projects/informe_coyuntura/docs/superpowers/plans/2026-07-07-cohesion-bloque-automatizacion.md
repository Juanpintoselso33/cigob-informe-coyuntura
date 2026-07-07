# Automatización de `cohesion_bloque` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el placeholder manual de `cohesion_bloque` (78%, congelado desde 2026-05-23) por un scraper propio contra `votaciones.hcdn.gob.ar` que calcula un índice de Rice real, con backfill histórico y un guard de frescura que no confunda receso legislativo con scraper roto.

**Architecture:** Todo vive en `scripts/politica.py` (mismo archivo que los demás `fetch_*`, sin módulo nuevo): una sesión HTTP persistente con pacing evita el WAF del sitio; se descubren actas por año (POST + regex/BeautifulSoup), se parsea cada acta, se filtra al bloque LLA, se calcula el índice de Rice por acta dividida, y se promedia en ventana móvil. Un guard de frescura separado trackea "¿la corrida de hoy llegó al sitio?" independientemente de "¿hay votos nuevos?".

**Tech Stack:** Python 3, `requests`, `BeautifulSoup4` (`lxml` parser) — ambos ya son dependencias del proyecto (usados en `movilizacion_cepa`/`gestion.py`). `pytest` + `unittest.mock` para tests (ya usado en `tests/test_itcg.py`).

## Global Constraints

- Convención de pacing: `time.sleep(0.3)` entre requests a `votaciones.hcdn.gob.ar`, sesión única, User-Agent estable (`HTTP_HEADERS` ya definido en `politica.py:65`) — variar esto reactiva el WAF F5 BIG-IP del sitio (confirmado empíricamente).
- Backfill mínimo desde dic-2023 (convención del proyecto, `feedback_backfill_series`).
- `HTTP_TIMEOUT = 20` (ya definido en `politica.py:64`) para todo request nuevo.
- Nunca marcar `desactualizado=True` solo por ausencia de votos nuevos — solo si la corrida de scraping en sí no llegó al sitio en `UMBRAL_FRESCURA_COHESION = 10` días.
- Todas las funciones nuevas van en `scripts/politica.py`; los tests nuevos en `tests/test_politica_cohesion.py` (archivo nuevo, mismo estilo que `tests/test_itcg.py`).

---

### Task 1: Índice de Rice

**Files:**
- Modify: `scripts/politica.py` (agregar función, cerca de `calcular_score`)
- Test: `tests/test_politica_cohesion.py` (nuevo)

**Interfaces:**
- Produces: `politica.indice_rice(afirmativos: int, negativos: int) -> float | None`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_politica_cohesion.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica


def test_indice_rice_unanime_afirmativo():
    assert politica.indice_rice(93, 0) == 100.0


def test_indice_rice_dividido_parejo():
    assert politica.indice_rice(50, 50) == 0.0


def test_indice_rice_mayoria_parcial():
    # 93 a favor, 1 en contra -> |93-1|/94*100 = 97.87
    assert politica.indice_rice(93, 1) == 97.87


def test_indice_rice_sin_votos():
    assert politica.indice_rice(0, 0) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/test_politica_cohesion.py -v`
Expected: FAIL con `AttributeError: module 'politica' has no attribute 'indice_rice'`

- [ ] **Step 3: Write minimal implementation**

Agregar en `scripts/politica.py`, cerca de `calcular_score`:

```python
def indice_rice(afirmativos: int, negativos: int) -> float | None:
    """Índice de Rice de cohesión (0-100): |afirm-neg|/(afirm+neg) * 100.
    Ausentes/abstenciones ya excluidos por el caller (no forman parte de la
    votación dividida). None si no hubo votos afirmativos ni negativos del
    bloque en esa acta (no aporta información de cohesión)."""
    total = afirmativos + negativos
    if total == 0:
        return None
    return round(abs(afirmativos - negativos) / total * 100.0, 2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/test_politica_cohesion.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): índice de Rice para cohesión de bloque"
```

---

### Task 2: Normalización y filtro del bloque LLA

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Produces: `politica.es_bloque_lla(nombre_bloque: str) -> bool`

- [ ] **Step 1: Write the failing tests**

```python
def test_es_bloque_lla_variantes():
    assert politica.es_bloque_lla("LA LIBERTAD AVANZA")
    assert politica.es_bloque_lla("Libertad Avanza")
    assert politica.es_bloque_lla("  la libertad avanza  ")


def test_es_bloque_lla_excluye_aliados_y_otros():
    assert not politica.es_bloque_lla("Fuerzas del Cielo - Espacio Liberal F.C.E.")
    assert not politica.es_bloque_lla("PRO")
    assert not politica.es_bloque_lla("Unión por la Patria")
    assert not politica.es_bloque_lla("")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k es_bloque_lla`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
# Bloque propio de LLA en Diputados/Senado. Excluye DELIBERADAMENTE aliados
# ambiguos (ej. "Fuerzas del Cielo - Espacio Liberal F.C.E.") que no son el
# bloque propio — sumarlos infla artificialmente la cohesión medida.
BLOQUES_LLA = {"la libertad avanza", "libertad avanza"}


def es_bloque_lla(nombre_bloque: str) -> bool:
    return nombre_bloque.strip().lower() in BLOQUES_LLA
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k es_bloque_lla`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): filtro de bloque LLA para cohesión"
```

---

### Task 3: Sesión HTTP con pacing y retry/backoff

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: `HTTP_HEADERS`, `HTTP_TIMEOUT` (ya definidos en `politica.py:64-65`)
- Produces: `politica._hcdn_votaciones_session() -> requests.Session`, `politica._hcdn_votaciones_get(session, path: str, **kwargs) -> requests.Response | None`

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import MagicMock


def test_hcdn_votaciones_get_reintenta_ante_403(monkeypatch):
    session = MagicMock()
    resp_403 = MagicMock(status_code=403)
    resp_200 = MagicMock(status_code=200)
    session.get.side_effect = [resp_403, resp_403, resp_200]
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert resultado is resp_200
    assert session.get.call_count == 3


def test_hcdn_votaciones_get_agota_reintentos(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=403)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    resultado = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert resultado is None
    assert session.get.call_count == 3


def test_hcdn_votaciones_get_devuelve_none_ante_excepcion(monkeypatch):
    session = MagicMock()
    session.get.side_effect = politica.requests.RequestException("timeout")
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    assert politica._hcdn_votaciones_get(session, "/votaciones/actas") is None


def test_hcdn_votaciones_session_setea_headers():
    session = politica._hcdn_votaciones_session()
    assert session.headers["User-Agent"] == politica.HTTP_HEADERS["User-Agent"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k hcdn_votaciones`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

Agregar `import time` al tope de `politica.py` si no está, y luego:

```python
HCDN_VOTACIONES_BASE = "https://votaciones.hcdn.gob.ar"
_HCDN_VOTACIONES_DELAY = 0.3  # segundos entre requests — evita el WAF F5 BIG-IP
                              # (confirmado: Como_voto corre a diario con este patrón)


def _hcdn_votaciones_session() -> requests.Session:
    """Sesión persistente con headers estables. El WAF del sitio devuelve 403
    ante ráfagas o headers que varían entre requests — reusar la misma sesión
    y no variar el UA es lo que lo evita."""
    s = requests.Session()
    s.headers.update(HTTP_HEADERS)
    return s


def _hcdn_votaciones_get(session: requests.Session, path: str, **kwargs):
    """GET con pacing fijo y retry/backoff ante 403 (hasta 3 intentos).
    None si se agotan los reintentos o hay un error de red."""
    url = f"{HCDN_VOTACIONES_BASE}{path}"
    for intento in range(3):
        time.sleep(_HCDN_VOTACIONES_DELAY)
        try:
            r = session.get(url, timeout=HTTP_TIMEOUT, **kwargs)
        except requests.RequestException:
            return None
        if r.status_code == 200:
            return r
        if r.status_code == 403:
            continue
        return None
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k hcdn_votaciones`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): sesión HTTP con pacing para votaciones.hcdn.gob.ar"
```

---

### Task 4: Descubrimiento de actas por año (fecha + id + slug)

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: `HCDN_VOTACIONES_BASE`, `HTTP_TIMEOUT`
- Produces: `politica._descubrir_actas(session, anio: int) -> list[dict] | None` — cada dict `{"id": str, "slug": str, "fecha": datetime}`. `None` si el request en sí falló (para distinguir de "sin actas ese año", que es `[]`).

- [ ] **Step 1: Write the failing tests**

```python
from datetime import datetime

FIXTURE_LISTADO_ACTAS = """
<table>
<tr>
  <td><span style="display:none">20260211</span> 11/02/2026</td>
  <td>Modernización Laboral. Título I.
    <a onclick="redirectActa(2623,1,'modernizacion-laboral-titulo-i')">Ver</a>
  </td>
</tr>
<tr>
  <td><span style="display:none">20260520</span> 20/05/2026</td>
  <td>Régimen de Zona Fría
    <a onclick="redirectActa(5939,1,'regimen-de-zona-fria')">Ver</a>
  </td>
</tr>
</table>
"""


def test_descubrir_actas_empareja_fecha_con_acta():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_ACTAS)
    actas = politica._descubrir_actas(session, 2026)
    assert actas == [
        {"id": "2623", "slug": "modernizacion-laboral-titulo-i", "fecha": datetime(2026, 2, 11)},
        {"id": "5939", "slug": "regimen-de-zona-fria", "fecha": datetime(2026, 5, 20)},
    ]


def test_descubrir_actas_ignora_filas_sin_fecha_o_sin_acta():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=200, text="<table><tr><td>sin nada util</td></tr></table>")
    assert politica._descubrir_actas(session, 2026) == []


def test_descubrir_actas_deduplica_por_id():
    session = MagicMock()
    texto = FIXTURE_LISTADO_ACTAS.replace("5939", "2623")  # simula id repetido
    session.post.return_value = MagicMock(status_code=200, text=texto)
    actas = politica._descubrir_actas(session, 2026)
    assert len(actas) == 1


def test_descubrir_actas_request_fallido_devuelve_none():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=500, text="")
    assert politica._descubrir_actas(session, 2026) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k descubrir_actas`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
_RE_REDIRECT_ACTA = re.compile(r"redirectActa\((\d+),\s*(\d+),\s*'([^']*)'\)")


def _descubrir_actas(session: requests.Session, anio: int):
    """POST a /votaciones/search por año -> [{id, slug, fecha}] de cada acta
    nominal encontrada. Cada fila del listado trae la fecha en un
    <span style="display:none">YYYYMMDD</span> y el link de detalle en un
    onclick=redirectActa(id, ?, 'slug') — se emparejan por fila (no por regex
    global sobre toda la página) para no desalinear fecha/acta.
    None si el request en sí falló (distinto de 'sin actas ese año' = [])."""
    r = session.post(f"{HCDN_VOTACIONES_BASE}/votaciones/search",
                      data={"anoSearch": str(anio)}, timeout=HTTP_TIMEOUT)
    if r is None or r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "lxml")
    actas = []
    vistos = set()
    for fila in soup.select("tr"):
        m = _RE_REDIRECT_ACTA.search(str(fila))
        span_fecha = fila.find("span", style=lambda s: s and "display:none" in s)
        if not m or span_fecha is None:
            continue
        id_acta, _, slug = m.groups()
        if id_acta in vistos:
            continue
        try:
            fecha = datetime.strptime(span_fecha.get_text(strip=True), "%Y%m%d")
        except ValueError:
            continue
        vistos.add(id_acta)
        actas.append({"id": id_acta, "slug": slug, "fecha": fecha})
    return actas
```

Confirmar que `from bs4 import BeautifulSoup` ya está importado en `politica.py` (se usa en `fetch_cepa_movilizacion`); si no, agregarlo.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k descubrir_actas`
Expected: 4 passed

- [ ] **Step 5: Verificación en vivo (obligatoria antes de continuar)**

Esta estructura de listado (`<span style="display:none">` + `redirectActa`) fue
confirmada en vivo por Senado durante la investigación previa; para Diputados
la evidencia es indirecta (inferida del scraper de terceros `Como_voto`, nunca
observada directamente — todos los intentos directos devolvieron 403 durante
esa investigación). Antes de continuar a la Tarea 5:

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
s = politica._hcdn_votaciones_session()
actas = politica._descubrir_actas(s, 2026)
print(actas[:3] if actas else actas)
"
```

Si la estructura real difiere (columnas distintas, span en otro formato), ajustar
`_descubrir_actas` contra lo observado ANTES de seguir — no asumir que el fixture
de test alcanza para producción.

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): descubrimiento de actas de votación por año"
```

---

### Task 5: Parsing de una acta individual

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Produces: `politica._parsear_acta(html: str) -> list[dict]` — cada dict `{"nombre": str, "bloque": str, "voto": str}`.

- [ ] **Step 1: Write the failing tests**

```python
FIXTURE_ACTA = """
<table>
<tr><td>JUEZ, LUIS ALFREDO</td><td class="ocultar">LA LIBERTAD AVANZA</td><td>AFIRMATIVO</td></tr>
<tr><td>KUEIDER, EDGARDO</td><td class="ocultar">UNION POR LA PATRIA</td><td>NEGATIVO</td></tr>
<tr><td>ALGUIEN, AUSENTE</td><td class="ocultar">PRO</td><td>AUSENTE</td></tr>
</table>
"""


def test_parsear_acta_extrae_filas():
    filas = politica._parsear_acta(FIXTURE_ACTA)
    assert filas == [
        {"nombre": "JUEZ, LUIS ALFREDO", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "KUEIDER, EDGARDO", "bloque": "UNION POR LA PATRIA", "voto": "NEGATIVO"},
        {"nombre": "ALGUIEN, AUSENTE", "bloque": "PRO", "voto": "AUSENTE"},
    ]


def test_parsear_acta_ignora_filas_incompletas():
    assert politica._parsear_acta("<table><tr><td>Solo una celda</td></tr></table>") == []


def test_parsear_acta_html_vacio():
    assert politica._parsear_acta("") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k parsear_acta`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
def _parsear_acta(html: str) -> list[dict]:
    """Parsea el HTML de una acta de votación nominal (misma estructura de
    tabla en Diputados y Senado: nombre, bloque, voto por fila) ->
    [{nombre, bloque, voto}]. Ignora filas sin las 3 columnas esperadas."""
    soup = BeautifulSoup(html, "lxml")
    filas = []
    for tr in soup.select("table tr"):
        celdas = tr.find_all("td")
        if len(celdas) < 3:
            continue
        nombre = celdas[0].get_text(strip=True)
        bloque = celdas[1].get_text(strip=True)
        voto = celdas[2].get_text(strip=True).upper()
        if not nombre or not bloque:
            continue
        filas.append({"nombre": nombre, "bloque": bloque, "voto": voto})
    return filas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k parsear_acta`
Expected: 3 passed

- [ ] **Step 5: Verificación en vivo (obligatoria antes de continuar)**

Esta estructura (`<td>nombre</td><td class="ocultar">bloque</td><td>voto</td>`)
fue confirmada en vivo para el Senado. Para Diputados es inferencia del código
de `Como_voto`, nunca observada de primera mano. Confirmar contra una acta real:

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
s = politica._hcdn_votaciones_session()
actas = politica._descubrir_actas(s, 2026)
r = politica._hcdn_votaciones_get(s, f'/votacion/{actas[0][\"slug\"]}/{actas[0][\"id\"]}')
print(politica._parsear_acta(r.text)[:5] if r else 'sin respuesta')
"
```

Ajustar los selectores de `_parsear_acta` si la tabla real usa otra estructura
(por ejemplo, columnas en otro orden, o el bloque en un `<span>` en vez de `<td>`
directo) antes de seguir a la Tarea 6.

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): parsing de tabla nominal de una acta"
```

---

### Task 6: Orquestación `fetch_cohesion_bloque()`

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: `_hcdn_votaciones_session`, `_descubrir_actas`, `_hcdn_votaciones_get`, `_parsear_acta`, `es_bloque_lla`, `indice_rice`
- Produces: `politica.fetch_cohesion_bloque(anio: int | None = None, dias_ventana: int = 90) -> dict | None`. El dict tiene forma `{"valor": float | None, "unidad": str, "fuente": str, "fecha_dato": str | None, "n_actas": int, "corrida_exitosa_en": str}`. `None` solo si `_descubrir_actas` devolvió `None` (falla de red/HTTP, no "sin votos").

- [ ] **Step 1: Write the failing tests**

```python
from datetime import timedelta


def test_fetch_cohesion_bloque_promedia_solo_actas_en_ventana(monkeypatch):
    hoy = datetime.now()
    actas = [
        {"id": "1", "slug": "a", "fecha": hoy - timedelta(days=10)},
        {"id": "2", "slug": "b", "fecha": hoy - timedelta(days=200)},  # fuera de ventana
    ]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    monkeypatch.setattr(politica, "_hcdn_votaciones_get", lambda s, p: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "NEGATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)
    assert resultado["n_actas"] == 1
    assert resultado["valor"] == politica.indice_rice(1, 1)
    assert resultado["fecha_dato"] == (hoy - timedelta(days=10)).strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_sin_actas_en_ventana_pero_corrida_exitosa(monkeypatch):
    hoy = datetime.now()
    actas = [{"id": "1", "slug": "a", "fecha": hoy - timedelta(days=200)}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: actas)
    resultado = politica.fetch_cohesion_bloque(dias_ventana=90)
    assert resultado is not None
    assert resultado["valor"] is None
    assert resultado["n_actas"] == 0
    assert resultado["corrida_exitosa_en"] == hoy.strftime("%Y-%m-%d")


def test_fetch_cohesion_bloque_falla_de_red_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas", lambda s, a: None)
    assert politica.fetch_cohesion_bloque() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k fetch_cohesion_bloque`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

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
        if acta["fecha"] < limite:
            continue
        r = _hcdn_votaciones_get(session, f"/votacion/{acta['slug']}/{acta['id']}")
        if r is None:
            continue
        filas = _parsear_acta(r.text)
        afirm = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "AFIRMATIVO")
        neg = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "NEGATIVO")
        rice = indice_rice(afirm, neg)
        if rice is None:
            continue
        indices.append(rice)
        fecha_max = acta["fecha"] if fecha_max is None else max(fecha_max, acta["fecha"])

    return {
        "valor": round(sum(indices) / len(indices), 1) if indices else None,
        "unidad": "% cohesión (índice de Rice), promedio actas divididas últimos 90 días",
        "fuente": "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
        "fecha_dato": fecha_max.strftime("%Y-%m-%d") if fecha_max else None,
        "n_actas": len(indices),
        "corrida_exitosa_en": datetime.now().strftime("%Y-%m-%d"),
    }
```

Confirmar que `from datetime import datetime, date, timedelta` ya cubre `timedelta`
(el import existente en `politica.py:32` ya lo trae).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k fetch_cohesion_bloque`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): orquestación fetch_cohesion_bloque con ventana de 3 meses"
```

---

### Task 7: Guard de frescura desacoplado

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Produces: `politica._cohesion_desactualizada(cache_previo: dict | None, corrida_actual: dict | None, umbral_dias: int = 10) -> bool`

- [ ] **Step 1: Write the failing tests**

```python
def test_cohesion_desactualizada_corrida_exitosa_hoy():
    assert not politica._cohesion_desactualizada(None, {"valor": 90.0, "corrida_exitosa_en": "2026-07-07"})


def test_cohesion_desactualizada_sin_corrida_previa_ni_actual():
    assert politica._cohesion_desactualizada(None, None)


def test_cohesion_desactualizada_corrida_previa_reciente():
    reciente = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert not politica._cohesion_desactualizada({"corrida_exitosa_en": reciente}, None)


def test_cohesion_desactualizada_corrida_previa_vieja():
    vieja = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    assert politica._cohesion_desactualizada({"corrida_exitosa_en": vieja}, None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k cohesion_desactualizada`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
UMBRAL_FRESCURA_COHESION = 10  # días SIN una corrida exitosa (no sin votos nuevos)


def _cohesion_desactualizada(cache_previo: dict | None, corrida_actual: dict | None,
                              umbral_dias: int = UMBRAL_FRESCURA_COHESION) -> bool:
    """True solo si no hubo NINGUNA corrida que haya llegado al sitio en los
    últimos `umbral_dias` días — nunca por ausencia de votos nuevos (el receso
    legislativo es normal y no debe marcarse como stale)."""
    if corrida_actual is not None:
        return False
    if cache_previo is None or not cache_previo.get("corrida_exitosa_en"):
        return True
    ultima = datetime.strptime(cache_previo["corrida_exitosa_en"], "%Y-%m-%d")
    return (datetime.now() - ultima).days > umbral_dias
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k cohesion_desactualizada`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): guard de frescura desacoplado para cohesion_bloque"
```

---

### Task 8: Wiring en `main()`

**Files:**
- Modify: `scripts/politica.py:854-902` (función `main`, ver contenido actual leído en la sesión de diseño)

**Interfaces:**
- Consumes: `fetch_cohesion_bloque`, `_cohesion_desactualizada`, `INDICADORES_ESPERADOS`
- Produces: n/a (efecto: `output/cache/politica.json` incluye `cohesion_bloque` con datos reales)

- [ ] **Step 1: Modificar `INDICADORES_ESPERADOS` y `colectores`**

En `scripts/politica.py`, dejar `INDICADORES_ESPERADOS` sin cambios (cohesion_bloque
ya está en la lista). En la lista `colectores` dentro de `main()`, reemplazar:

```python
        ("cohesion_bloque",             lambda: fetch_manual("cohesion_bloque")),
```

por sacarla de la lista genérica (se maneja aparte, ver Step 2) — la nueva lista
`colectores` queda:

```python
    colectores = [
        ("votometro_ventaja_lla",       fetch_votometro),
        ("ratio_dnu",                   fetch_ratio_dnu),
        ("movilizacion_cepa",           fetch_cepa_movilizacion),
        ("iaf_transferencias",          fetch_iaf_transferencias),
        ("eficacia_legislativa",        fetch_eficacia_legislativa),
        ("gobernadores_alineamiento",   lambda: fetch_manual("gobernadores_alineamiento")),
        ("veto_quorum",                 fetch_veto_quorum),
        ("comisiones_caidas",           fetch_comisiones_caidas),
    ]
```

- [ ] **Step 2: Agregar el manejo especial de `cohesion_bloque` en `main()`**

Inmediatamente después del `for nombre, fetcher in colectores:` loop existente
(antes de `score = calcular_score(frescos)`), agregar:

```python
    resultado_cohesion = fetch_cohesion_bloque()
    anterior_cohesion = indicadores_anteriores.get("cohesion_bloque")
    if resultado_cohesion is not None and resultado_cohesion.get("valor") is not None:
        frescos["cohesion_bloque"] = resultado_cohesion
        frescos_count += 1
    elif resultado_cohesion is not None and anterior_cohesion is not None:
        # corrida exitosa (llegó al sitio) pero sin votos nuevos en la ventana —
        # se reusa el último valor conocido, NO se marca desactualizado por eso
        frescos["cohesion_bloque"] = {
            **anterior_cohesion,
            "desactualizado": False,
            "corrida_exitosa_en": resultado_cohesion["corrida_exitosa_en"],
        }
        frescos_count += 1
    elif anterior_cohesion is not None:
        frescos["cohesion_bloque"] = {
            **anterior_cohesion,
            "desactualizado": _cohesion_desactualizada(anterior_cohesion, resultado_cohesion),
        }
```

Nota: como `calcular_score()` va a reemplazarse por `itcp.calcular_itcp()` en el
sub-proyecto 2 (paramétrica), no tocar esa línea acá — este plan deja
`calcular_score()` funcionando igual que antes (ahora con `cohesion_bloque` real
en vez de manual), y el reemplazo por la paramétrica es un plan separado.

- [ ] **Step 3: Correr los tests existentes para confirmar que no se rompió nada**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/ -v`
Expected: todos los tests existentes (`test_itcg.py`, `test_itcm.py` si existe,
`test_descargar_series.py`, `test_politica_cohesion.py`) pasan.

- [ ] **Step 4: Prueba manual end-to-end contra el sitio real**

Run: `cd "projects/informe_coyuntura" && python scripts/politica.py`
Expected: exit code 0 o 1 (no 2), y `output/cache/politica.json` tiene
`indicadores.cohesion_bloque.fuente == "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)"`.

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py
git commit -m "feat(politica): wiring de cohesion_bloque automático en main()"
```

---

### Task 9: Actualizar `data/politica/manuales.json`

**Files:**
- Modify: `data/politica/manuales.json`

- [ ] **Step 1: Editar el archivo**

Reemplazar el contenido completo por:

```json
{
  "_meta": {
    "descripcion": "Indicadores manuales del cinturón político (capital político según Matus). Actualizar cuando haya nuevos datos. desactualizado se setea automáticamente si fecha_dato > 45 días. Los automáticos (votometro, ratio_dnu, movilizacion_cepa, iaf_transferencias, eficacia_legislativa, cohesion_bloque, veto_quorum, comisiones_caidas) no van aquí.",
    "indicadores": ["gobernadores_alineamiento"],
    "pendiente_automatizacion": {
      "gobernadores_alineamiento": "métrica cualitativa — sin fuente estructurada disponible. Proxies investigados y DESCARTADOS (2026-07-07, no volver a evaluar sin fuente nueva): (1) composición partidaria del Senado por provincia — mide bancas legislativas, no conducta del Poder Ejecutivo provincial; (2) composición de Diputados por distrito (CKAN HCDN) — varios legisladores de distinto signo por provincia simultáneamente, sin campo de gobernador; (3) API de Presupuesto Abierto (transferencias/ATN) — sin columna de corte provincial confirmada, y el organismo correcto para ATN es Interior, no Economía; (4) tabla de adhesión provincial al RIGI — mide adhesión fiscal a un régimen puntual, no alineamiento político general (se automatiza como indicador NUEVO y DISTINTO, adhesion_reformas_provincial, ver ADR-0035). Único camino identificado: NLP sobre cobertura periodística (La Nación Data, Infobae) — proyecto separado."
    }
  },
  "gobernadores_alineamiento": {
    "valor": 55,
    "estado": "placeholder",
    "unidad": "% gobernadores alineados con política nacional",
    "fuente": "Análisis de declaraciones y adhesiones públicas — elaboración CIGOB",
    "notas": "% de gobernadores provinciales (sobre 24) cuya posición pública es de alineamiento o apoyo al programa del gobierno nacional. Incluye acuerdos fiscales, apoyo a reformas, participación en foros oficiales.",
    "fecha_dato": "2026-04-01"
  }
}
```

- [ ] **Step 2: Confirmar que `load_manuales()`/`fetch_manual()` siguen funcionando**

Run: `cd "projects/informe_coyuntura" && python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
print(politica.fetch_manual('gobernadores_alineamiento'))
print(politica.fetch_manual('cohesion_bloque'))  # debe advertir 'No encontrado' y devolver None
"`
Expected: primera línea imprime el dict de gobernadores_alineamiento; segunda
imprime un warning `[WARN] cohesion_bloque: No encontrado en ...` y `None`.

- [ ] **Step 3: Commit**

```bash
git add data/politica/manuales.json
git commit -m "fix(politica): cohesion_bloque deja de ser manual; blocker de gobernadores_alineamiento documentado con proxies descartados"
```

---

### Task 10: Backfill histórico en `descargar_series.py`

**Files:**
- Modify: `scripts/descargar_series.py`

**Interfaces:**
- Consumes: `politica.fetch_cohesion_bloque(anio, dias_ventana)` (Tarea 6) — para backfill se llama con `dias_ventana=366` por año, para capturar todo el año sin importar el mes de corrida.
- Produces: entrada nueva en `POLITICA_DERIVADAS` (lista ya existente en el archivo, líneas 463-470 según la exploración previa).

- [ ] **Step 1: Agregar la función de serie**

Junto a las demás `fetch_*_serie` de política en `descargar_series.py`:

```python
def fetch_cohesion_bloque_serie(anio_inicio: int = 2023) -> dict:
    """Backfill de cohesion_bloque: un punto por año desde `anio_inicio`,
    promedio de índice de Rice sobre TODAS las actas divididas de ese año
    (dias_ventana=366 para no depender de la fecha de corrida)."""
    serie = {}
    for anio in range(anio_inicio, datetime.now().year + 1):
        resultado = politica.fetch_cohesion_bloque(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            serie[str(anio)] = resultado["valor"]
    return serie
```

- [ ] **Step 2: Registrar en `POLITICA_DERIVADAS`**

Agregar la tupla `("cohesion_bloque", fetch_cohesion_bloque_serie)` a la lista
`POLITICA_DERIVADAS` existente, mismo formato que las demás entradas de política
ya registradas ahí (`fetch_votometro_serie`, `fetch_iaf_serie`, etc.).

- [ ] **Step 3: Correr el backfill y confirmar output**

Run: `cd "projects/informe_coyuntura" && python scripts/descargar_series.py`
Expected: exit 0, y `data/politica/... ` (el archivo de serie histórica que use
este script, según el patrón ya existente para los demás derivados) tiene una
entrada `cohesion_bloque` con puntos 2023→2026.

- [ ] **Step 4: Commit**

```bash
git add scripts/descargar_series.py data/politica/
git commit -m "feat(politica): backfill histórico de cohesion_bloque 2023-2026"
```

---

### Task 11: Validación manual en GitHub Actions real (no es código — verificación operativa)

**Files:** ninguno (tarea de verificación, no de implementación)

- [ ] **Step 1: Disparar una corrida manual del workflow**

El WAF de `votaciones.hcdn.gob.ar` nunca fue probado desde un runner real de
GitHub Actions (solo desde entornos de desarrollo/Anthropic) — este mismo repo
ya tuvo el failure mode "200 en local, 403/404 solo desde runners" (CICCRA,
commit `2ec13f5`). Antes de confiar en el indicador en producción:

```bash
gh workflow run data-pipeline.yml
```

- [ ] **Step 2: Revisar el log de la corrida**

```bash
gh run list --workflow=data-pipeline.yml --limit 1
gh run view <run-id> --log | grep -i cohesion
```

Expected: sin líneas de error 403 asociadas a `votaciones.hcdn.gob.ar`, y
`cohesion_bloque` aparece con un valor numérico (no null) en el log o en el
cache resultante.

- [ ] **Step 3: Si el runner es bloqueado (403 solo desde CI)**

Documentar el hallazgo como comentario en el PR/commit correspondiente y
evaluar mitigación (User-Agent más "de navegador", o backoff más largo) antes
de mergear — no dejar el indicador silenciosamente cayendo al cache en cada
corrida sin que quede registrado.

---

## Self-Review

**Cobertura del spec:** Tarea 1-2 cubren la metodología (índice de Rice, filtro
de bloque). Tareas 3-6 cubren el scraper completo (sesión/pacing, descubrimiento,
parsing, orquestación). Tarea 7-8 cubren el guard de frescura y su wiring.
Tarea 9 cubre el cambio en `manuales.json`. Tarea 10 cubre el backfill. Tarea 11
cubre la validación en CI real. Todo lo comprometido en el spec de sub-proyecto 1
tiene una tarea.

**Placeholders:** ninguno — cada paso de código tiene la implementación completa;
los dos únicos puntos de "verificar en vivo" (Tareas 4 y 5) son pasos de
verificación explícitos con comando exacto a correr, no instrucciones vagas.

**Consistencia de tipos:** `_descubrir_actas` devuelve `list[dict] | None` en
Tareas 4 y 6 de forma consistente; `fetch_cohesion_bloque` devuelve la misma
forma de dict en Tareas 6, 8 y 10; `_cohesion_desactualizada` se usa con la
misma firma en Tareas 7 y 8.
