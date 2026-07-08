# Reemplazo de movilizacion_cepa por conflictividad_laboral_srt — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la fuente del indicador `movilizacion_cepa` (CEPA, alcance angosto y ~4 informes irregulares) por la serie oficial de "Conflictividad Laboral" de la Secretaría de Trabajo (Ministerio de Capital Humano), con ~40 informes trimestrales confirmados desde 2016 y metodología documentada.

**Architecture:** Nuevo indicador `conflictividad_laboral_srt`, puntuado sobre el **total trimestral de "conflictos con paro"** (Cuadro 1 de cada informe PDF trimestral, fila "Total"). Se purga `movilizacion_cepa` del histórico (mismo patrón que la purga de `cohesion_bloque` legacy, commit `3973d00`). Caché persistente por trimestre (mismo patrón que `_serie_cohesion_cacheada`, generalizado o reusado).

**Tech Stack:** `pdfplumber` (ya es dependencia del proyecto, usada en `macro.py` para el SDDS del BCRA), `requests`.

## Global Constraints

- Spec de diseño: `docs/superpowers/specs/2026-07-08-conflictividad-laboral-fuente-oficial-design.md` — leer antes de empezar.
- El indicador mide **conflictos con paro** (huelga efectiva) — más angosto que "conflictividad social" amplia. Documentar esto en `docs/cinturon_politica.md`, no ocultarlo.
- Quiebre metodológico real a documentar: la Ley de Bases (27.742) encareció legalmente el paro — atribuido por la propia Secretaría como factor de la baja reciente. Se documenta como nota, no bloquea nada.
- Bandas nuevas quedan marcadas **provisional** hasta recalibrar con la serie completa backfilleada (mismo mecanismo que `cohesion_bloque`/`protestas_caba` hoy).
- NO tocar `cohesion_bloque` (Diputados), `gobernadores_alineamiento`, ni `protestas_caba` — fuera de alcance de este plan.
- URL base confirmada: `https://www.argentina.gob.ar/sites/default/files/conflicto_laboral_{año}t{trimestre}.pdf` (verificado en vivo 2026-07-08 para 2016-2020; algunos trimestres de 2017-2018 son `.docx` en vez de `.pdf`).
- Fixture real ya descargado y verificado: Q2-2020 (163 conflictos con paro, vs. 212 en Q2-2019, media Q2 2010-2019 = 330) — usar estos 3 números exactos en los tests, no inventar otros.

---

### Task 1: Descubrir URLs de informes trimestrales 2021-2026

**Files:**
- Create: `data/politica/srt_conflictividad_urls.json` (manifest de URLs confirmadas, `{"2016t1": "conflicto_laboral_2016t1.pdf", ...}`)

**Interfaces:**
- Produces: el manifest JSON que Task 4 (caché de la serie) va a leer/escribir.

- [ ] **Step 1: Confirmar el patrón para 2016-2020 y extender la búsqueda**

Ejecutar (ya verificado que este patrón funciona para 2016-2020; extender el rango y variar la extensión):

```bash
cd projects/informe_coyuntura && python3 -c "
import requests, json

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
base = 'https://www.argentina.gob.ar/sites/default/files/'
encontrados = {}

for anio in range(2016, 2027):
    for t in range(1, 5):
        clave = f'{anio}t{t}'
        for nombre in [
            f'conflicto_laboral_{anio}t{t}.pdf',
            f'conflicto_laboral_{anio}t{t}.docx',
            f'conflicto_laboral_{anio}_t{t}.pdf',
            f'conflictividad_laboral_{anio}t{t}.pdf',
            f'informe_conflictividad_laboral_{anio}t{t}.pdf',
            f'conflicto_laboral_{anio}_trim{t}.pdf',
        ]:
            url = base + nombre
            try:
                r = s.head(url, timeout=8, allow_redirects=True)
                if r.status_code == 200:
                    encontrados[clave] = nombre
                    print('OK', clave, nombre)
                    break
            except Exception:
                pass

print(json.dumps(encontrados, indent=2, ensure_ascii=False))
"
```

- [ ] **Step 2: Si el patrón de nombre cambió para años recientes, buscar en la página de listado**

Si el Step 1 no encuentra nada para 2021+, el listado completo (32+ resultados, paginado) vive en `https://www.argentina.gob.ar/node/335319` pero se renderiza vía AJAX (Drupal 7 + Views). Probar:

```bash
python3 -c "
import requests
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})
# Buscar el nombre real de la vista: inspeccionar el HTML de node/335319
# en busca de 'js-view-dom-id' o similar (Drupal 7 embebe esto en el div del bloque)
r = requests.get('https://www.argentina.gob.ar/node/335319', headers={'User-Agent':'Mozilla/5.0'})
import re
m = re.search(r'view-dom-id-(\w+)', r.text)
print(m.group(0) if m else 'no encontrado -- revisar r.text manualmente')
"
```

Si esto tampoco da resultado en un intento razonable (no más de 30 minutos de exploración), usar como fallback: los comunicados de prensa en `argentina.gob.ar/noticias/...` (ej. `continua-en-descenso-la-conflictividad-laboral`) dan cifras MENSUALES en prosa — no estructuradas, más frágiles de parsear, pero permiten al menos un valor vigente aproximado si no se encuentra el PDF trimestral más reciente. Documentar cuál camino se tomó en el manifest (`"fuente": "pdf_trimestral"` o `"fuente": "noticia_mensual_fallback"`).

- [ ] **Step 3: Guardar el manifest**

Escribir `data/politica/srt_conflictividad_urls.json` con las URLs confirmadas (al menos las de 2016-2020 ya verificadas; agregar las que se encuentren de 2021-2026). Formato:

```json
{
  "2016t1": "conflicto_laboral_2016t1.pdf",
  "2020t2": "conflicto_laboral_2020t2.pdf"
}
```

- [ ] **Step 4: Commit**

```bash
git add data/politica/srt_conflictividad_urls.json
git commit -m "docs(politica): manifest de URLs confirmadas de informes trimestrales SRT (conflictividad laboral)"
```

---

### Task 2: Parser del informe trimestral (`_extraer_total_conflictos_srt`)

**Files:**
- Modify: `scripts/politica.py` (agregar función nueva cerca de `_extraer_cifra_cepa`)
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: texto plano extraído de un PDF vía `pdfplumber` (página 3 del informe, la que tiene "Cuadro 1")
- Produces: `politica._extraer_total_conflictos_srt(texto: str) -> int | None`

- [ ] **Step 1: Write the failing tests**

Fixture real, tomado literalmente de la página 3 del informe `conflicto_laboral_2020t2.pdf` (verificado en vivo 2026-07-08):

```python
FIXTURE_SRT_2020T2 = """
Cuadro 1. Indicadores de la conflictividad laboral según ámbito institucional, en cantidad, absolutos, distribución
y variación porcentuales. Segundo trimestre 2019 y 2020
Variación Media II Trim.
Ámbito II Trim. 2020 II Trim. 2019
interanual 2010-2019
Distribución Distribución Distribución
Cantidad Cantidad Absoluta Porcentual Cantidad
porcentual porcentual porcentual
Total 163 212 -49 -23% 330
Conflictos
Estatal 79 48% 132 62% -53 -40% 218 66%
con paro
Privado 87 53% 82 39% 5 6% 117 35%
"""


def test_extraer_total_conflictos_srt_informe_real_2020t2():
    assert politica._extraer_total_conflictos_srt(FIXTURE_SRT_2020T2) == 163


def test_extraer_total_conflictos_srt_sin_cuadro_1_devuelve_none():
    assert politica._extraer_total_conflictos_srt("texto sin la tabla esperada") is None


def test_extraer_total_conflictos_srt_ignora_numeros_de_otras_filas():
    # Asegura que no matchea la fila "Estatal 79 48% 132 62% ..." (formato distinto:
    # tiene "%" pegado al segundo número, no ocurre en la fila "Total").
    fixture_solo_estatal = "Cuadro 1. algo\nEstatal 79 48% 132 62% -53 -40% 218 66%\n"
    assert politica._extraer_total_conflictos_srt(fixture_solo_estatal) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k extraer_total_conflictos_srt -v`
Expected: 3 FAIL con `AttributeError: module 'politica' has no attribute '_extraer_total_conflictos_srt'`

- [ ] **Step 3: Implementar el parser**

Agregar en `scripts/politica.py`, cerca de `_extraer_cifra_cepa`:

```python
_RE_CUADRO1_TOTAL_SRT = re.compile(
    r"Cuadro 1\..*?Total\s+(\d+)\s+\d+\s+-?\d+\s+-?\d+%\s+\d+",
    re.DOTALL,
)


def _extraer_total_conflictos_srt(texto: str) -> int | None:
    """Extrae el total trimestral de "conflictos con paro" del Cuadro 1 de un
    informe de la Secretaría de Trabajo (Dirección de Estudios de Relaciones
    del Trabajo). La fila "Total <actual> <comparación> <var.abs> <var.%>
    <media>" aparece SIEMPRE antes de la fila "Estatal ..." en el texto
    extraído por pdfplumber (el rótulo vertical "Conflictos / con paro" se
    linealiza DESPUÉS de la fila Total por el layout del PDF) -- por eso el
    regex ancla en "Cuadro 1" y toma el primer "Total" que matchea el patrón
    de 5 números (cantidad, cantidad, variación absoluta, variación %,
    media), no cualquier "Total" suelto en el documento."""
    m = _RE_CUADRO1_TOTAL_SRT.search(texto)
    return int(m.group(1)) if m else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k extraer_total_conflictos_srt -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): parser de conflictividad laboral SRT (Cuadro 1, total trimestral de conflictos con paro)"
```

---

### Task 3: Fetch vigente (`fetch_conflictividad_laboral_srt`)

**Files:**
- Modify: `scripts/politica.py`

**Interfaces:**
- Consumes: `politica._extraer_total_conflictos_srt` (Task 2), `data/politica/srt_conflictividad_urls.json` (Task 1)
- Produces: `politica.fetch_conflictividad_laboral_srt() -> dict | None`

- [ ] **Step 1: Write the failing test**

```python
def test_fetch_conflictividad_laboral_srt_usa_el_trimestre_mas_reciente_del_manifest(monkeypatch, tmp_path):
    manifest = tmp_path / "srt_conflictividad_urls.json"
    manifest.write_text(json.dumps({"2019t2": "x.pdf", "2020t2": "conflicto_laboral_2020t2.pdf"}), encoding="utf-8")
    monkeypatch.setattr(politica, "SRT_CONFLICTIVIDAD_MANIFEST", manifest)

    class FakeResponse:
        status_code = 200
        content = b"%PDF-FAKE%"

    def fake_get(url, headers=None, timeout=None):
        assert "conflicto_laboral_2020t2.pdf" in url  # el trimestre MÁS reciente, no el primero
        return FakeResponse()

    def fake_extraer_texto_pdf(contenido_bytes):
        return "Cuadro 1. x\nTotal 163 212 -49 -23% 330\n"

    monkeypatch.setattr(politica.requests, "get", fake_get)
    monkeypatch.setattr(politica, "_texto_pdf", fake_extraer_texto_pdf)

    resultado = politica.fetch_conflictividad_laboral_srt()
    assert resultado["valor"] == 163
    assert resultado["trimestre"] == "2020t2"
    assert resultado["fuente"] == "Dirección de Estudios de Relaciones del Trabajo (Secretaría de Trabajo)"


def test_fetch_conflictividad_laboral_srt_sin_manifest_devuelve_none(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "SRT_CONFLICTIVIDAD_MANIFEST", tmp_path / "no_existe.json")
    assert politica.fetch_conflictividad_laboral_srt() is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k fetch_conflictividad_laboral_srt -v`
Expected: 2 FAIL (`AttributeError`)

- [ ] **Step 3: Implementar**

Agregar cerca de `fetch_cepa_movilizacion` en `scripts/politica.py`:

```python
SRT_CONFLICTIVIDAD_MANIFEST = PROJECT_DIR / "data" / "politica" / "srt_conflictividad_urls.json"
SRT_CONFLICTIVIDAD_BASE = "https://www.argentina.gob.ar/sites/default/files/"


def _texto_pdf(contenido_bytes: bytes) -> str:
    """Extrae todo el texto de un PDF en memoria vía pdfplumber."""
    import io
    import pdfplumber
    with pdfplumber.open(io.BytesIO(contenido_bytes)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def fetch_conflictividad_laboral_srt() -> dict | None:
    """Conflictividad laboral oficial (Secretaría de Trabajo, Ministerio de
    Capital Humano) -- total TRIMESTRAL de "conflictos con paro" (Cuadro 1
    de cada informe). Reemplaza a movilizacion_cepa (CEPA): esta fuente mide
    algo distinto y más angosto que "conflictividad social" amplia --
    específicamente huelgas efectivas -- pero tiene ~40 informes
    trimestrales confirmados desde 2016 (CEPA solo tenía ~4 informes
    irregulares desde fines de 2025) y metodología documentada (monitoreo
    diario de 120+ medios, 10 variables de clasificación).
    Dimensión: conflicto social (Matus)."""
    try:
        manifest_raw = SRT_CONFLICTIVIDAD_MANIFEST.read_text(encoding="utf-8")
    except OSError:
        return None
    manifest = json.loads(manifest_raw)
    if not manifest:
        return None

    trimestre_reciente = max(manifest.keys())
    nombre_archivo = manifest[trimestre_reciente]
    try:
        r = requests.get(SRT_CONFLICTIVIDAD_BASE + nombre_archivo,
                         headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        texto = _texto_pdf(r.content)
        total = _extraer_total_conflictos_srt(texto)
        if total is None:
            raise ValueError(f"No se encontró el Cuadro 1 en {nombre_archivo}")
        return {
            "valor": total,
            "trimestre": trimestre_reciente,
            "unidad": "Conflictos con paro (trimestral)",
            "fuente": "Dirección de Estudios de Relaciones del Trabajo (Secretaría de Trabajo)",
            "fecha_dato": str(date.today()),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("conflictividad_laboral_srt", str(e))
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k fetch_conflictividad_laboral_srt -v`
Expected: 2 PASS

- [ ] **Step 5: Verificación en vivo**

```bash
cd projects/informe_coyuntura && python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
print(politica.fetch_conflictividad_laboral_srt())
"
```
Confirmar que devuelve un dict con `valor` numérico razonable (o `None` con un `[WARN]` si el trimestre más reciente del manifest todavía no está confirmado por Task 1 -- en ese caso, no bloquear, documentarlo en el reporte).

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): fetch vigente de conflictividad_laboral_srt (reemplaza a movilizacion_cepa)"
```

---

### Task 4: Serie histórica con caché persistente

**Files:**
- Modify: `scripts/descargar_series.py`

**Interfaces:**
- Consumes: `politica.fetch_conflictividad_laboral_srt` no se reusa directamente (la serie necesita TODOS los trimestres, no solo el más reciente) -- lee `SRT_CONFLICTIVIDAD_MANIFEST` y `politica._extraer_total_conflictos_srt`/`politica._texto_pdf` directamente.
- Produces: `descargar_series.fetch_conflictividad_laboral_srt_serie() -> list`

- [ ] **Step 1: Write the failing tests**

Reusar el patrón de `test_descargar_series_cohesion.py` (caché persistente por período cerrado, mismo mecanismo que `_serie_cohesion_cacheada` pero por TRIMESTRE, no por año -- todos los trimestres son "cerrados" una vez publicados, ninguno se re-pide nunca, a diferencia de cohesion_bloque_senado donde el año en curso sí se repetía):

```python
def test_conflictividad_srt_serie_cachea_todos_los_trimestres_del_manifest(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"2019t2": "a.pdf", "2020t2": "b.pdf"}), encoding="utf-8")
    monkeypatch.setattr(descargar_series.politica, "SRT_CONFLICTIVIDAD_MANIFEST", manifest)
    monkeypatch.setattr(descargar_series.politica, "SRT_CONFLICTIVIDAD_BASE", "https://x/")
    store = tmp_path / "cache.json"
    monkeypatch.setattr(descargar_series, "SRT_CONFLICTIVIDAD_SERIE_STORE", store)

    llamados = []

    def fake_get(url, headers=None, timeout=None):
        llamados.append(url)
        class R:
            status_code = 200
            content = b"fake"
            def raise_for_status(self): pass
        return R()

    def fake_texto_pdf(contenido):
        return {"https://x/a.pdf": "Cuadro 1. x\nTotal 212 163 49 30% 330\n",
                "https://x/b.pdf": "Cuadro 1. x\nTotal 163 212 -49 -23% 330\n"}[llamados[-1]]

    monkeypatch.setattr(descargar_series.requests, "get", fake_get)
    monkeypatch.setattr(descargar_series.politica, "_texto_pdf", fake_texto_pdf)

    serie = descargar_series.fetch_conflictividad_laboral_srt_serie()

    assert serie == [["2019t2", 212], ["2020t2", 163]]
    assert len(llamados) == 2

    # segunda corrida: nada se vuelve a pedir (todos los trimestres del manifest ya están cacheados)
    llamados.clear()
    serie2 = descargar_series.fetch_conflictividad_laboral_srt_serie()
    assert serie2 == serie
    assert llamados == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_descargar_series_cohesion.py -k conflictividad_srt_serie -v`
Expected: FAIL (`AttributeError`)

- [ ] **Step 3: Implementar**

Agregar en `scripts/descargar_series.py` (cerca de `fetch_cohesion_bloque_senado_serie`):

```python
SRT_CONFLICTIVIDAD_SERIE_STORE = Path(__file__).resolve().parents[1] / "data" / "politica" / "srt_conflictividad_serie.json"


def fetch_conflictividad_laboral_srt_serie() -> list:
    """Serie TRIMESTRAL de conflictividad laboral oficial (Secretaría de
    Trabajo). A diferencia de cohesion_bloque_senado (donde el año en curso
    se re-pide siempre porque puede sumar actas nuevas), acá TODOS los
    trimestres son inmutables una vez publicados -- ninguno se vuelve a
    pedir una vez cacheado, ni siquiera el más reciente (un trimestre
    cerrado no cambia). Lee los nombres de archivo confirmados del manifest
    generado en Task 1 (data/politica/srt_conflictividad_urls.json)."""
    try:
        manifest = json.loads(politica.SRT_CONFLICTIVIDAD_MANIFEST.read_text(encoding="utf-8"))
    except OSError:
        return []

    try:
        cache = json.loads(SRT_CONFLICTIVIDAD_SERIE_STORE.read_text(encoding="utf-8-sig"))
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, json.JSONDecodeError):
        cache = {}

    for trimestre, nombre_archivo in manifest.items():
        if trimestre in cache:
            continue
        try:
            r = requests.get(politica.SRT_CONFLICTIVIDAD_BASE + nombre_archivo,
                             headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            texto = politica._texto_pdf(r.content)
            total = politica._extraer_total_conflictos_srt(texto)
        except Exception as e:
            print(f"  [WARN] conflictividad_srt {trimestre}: {e}")
            continue
        if total is not None:
            cache[trimestre] = total
            SRT_CONFLICTIVIDAD_SERIE_STORE.write_text(
                json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    return [[trimestre, cache[trimestre]] for trimestre in sorted(cache) if trimestre in cache]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_descargar_series_cohesion.py -k conflictividad_srt_serie -v`
Expected: PASS

- [ ] **Step 5: Registrar en POLITICA_DERIVADAS**

Reemplazar la entrada de `movilizacion_cepa` en `POLITICA_DERIVADAS` (buscar `fetch_cepa_movilizacion_serie` en `descargar_series.py`):

```python
    ("conflictividad_laboral_srt", "Conflictos con paro (trimestral)",
     "Secretaría de Trabajo — Dirección de Estudios de Relaciones del Trabajo",
     fetch_conflictividad_laboral_srt_serie),
```

Eliminar la entrada vieja de `movilizacion_cepa` / `fetch_cepa_movilizacion_serie` de la lista (dejar la función `fetch_cepa_movilizacion_serie` y `fetch_cepa_movilizacion` en el código sin uso activo, o eliminarlas -- decisión del implementador, documentar cuál se tomó y por qué).

- [ ] **Step 6: Verificación en vivo + backfill real**

```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py
```

Confirmar que `output/series/politica.csv` tiene múltiples filas `conflictividad_laboral_srt` (idealmente 15-40, según cuántos trimestres confirmó Task 1).

- [ ] **Step 7: Commit**

```bash
git add scripts/descargar_series.py tests/test_descargar_series_cohesion.py
git commit -m "feat(politica): serie histórica de conflictividad_laboral_srt con caché persistente por trimestre"
```

---

### Task 5: Purgar movilizacion_cepa y actualizar bandas/wiring en itcp.py y politica.py

**Files:**
- Modify: `scripts/itcp.py` (BANDAS_ITCP, DIMENSIONES_ITCP)
- Modify: `scripts/politica.py` (INDICADORES_ESPERADOS, main(), colectores)
- Test: `tests/test_itcp.py`

**Interfaces:**
- Consumes: `politica.fetch_conflictividad_laboral_srt` (Task 3)

- [ ] **Step 1: Write the failing test**

En `tests/test_itcp.py`, buscar el test existente que referencia `movilizacion_cepa` en `BANDAS_ITCP` o `DIMENSIONES_ITCP` y agregar (o adaptar) uno equivalente para el nuevo indicador:

```python
def test_bandas_itcp_tiene_conflictividad_laboral_srt_no_movilizacion_cepa():
    assert "conflictividad_laboral_srt" in itcp.BANDAS_ITCP
    assert "movilizacion_cepa" not in itcp.BANDAS_ITCP
    dim_conflicto = itcp.DIMENSIONES_ITCP["conflicto_social"]
    assert "conflictividad_laboral_srt" in dim_conflicto["indicadores"]
    assert "movilizacion_cepa" not in dim_conflicto["indicadores"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_itcp.py -k conflictividad_laboral_srt -v`
Expected: FAIL

- [ ] **Step 3: Actualizar `itcp.py`**

En `BANDAS_ITCP`, reemplazar la entrada de `movilizacion_cepa`:

```python
    "conflictividad_laboral_srt": [
        # Provisional (2026-07-08): anclas informadas por 3 puntos reales
        # citados por la propia Secretaría de Trabajo (Q2-2020=163, Q2-2019=212,
        # media Q2 2010-2019=330) -- recalibrar con cuantiles reales una vez
        # backfilleada la serie completa (Task 4 de este plan). Más conflictos
        # con paro = más tensión (mismo sentido que la banda anterior).
        (0, 60, 100),
        (60, 100, 85),
        (100, 150, 65),
        (150, 250, 40),
        (250, float("inf"), 10),
    ],
```

En `DIMENSIONES_ITCP`, dentro de `conflicto_social`, reemplazar `"movilizacion_cepa"` por `"conflictividad_laboral_srt"` (mismo peso interno, 60%, que tenía `movilizacion_cepa`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_itcp.py -v`
Expected: todos PASS

- [ ] **Step 5: Actualizar `politica.py`**

- En `INDICADORES_ESPERADOS`: reemplazar `"movilizacion_cepa"` por `"conflictividad_laboral_srt"`.
- En `main()`, en la lista de colectores: reemplazar la tupla que llama a `fetch_cepa_movilizacion` por una que llame a `fetch_conflictividad_laboral_srt`.
- Purgar cualquier valor legacy de `movilizacion_cepa` de `output/cache/politica.json` (mismo patrón que la purga de `cohesion_bloque`, commit `3973d00` -- revisar ese commit como referencia si hace falta el mecanismo exacto).

- [ ] **Step 6: Correr la suite completa**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS.

- [ ] **Step 7: Verificación en vivo del ITCP completo**

```bash
cd projects/informe_coyuntura && python scripts/politica.py
```
Confirmar que el ITCP se recalcula sin errores y que `conflictividad_laboral_srt` aparece en el cache con un valor real.

- [ ] **Step 8: Commit**

```bash
git add scripts/itcp.py scripts/politica.py tests/test_itcp.py
git commit -m "feat(politica): reemplaza movilizacion_cepa por conflictividad_laboral_srt en el ITCP (bandas provisionales, purga de legacy)"
```

---

### Task 6: Sync final de `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md`

- [ ] **Step 1: Correr el pipeline completo**

```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py && python scripts/politica.py && python scripts/validacion_externa.py && python scripts/generar_informe.py && python scripts/publicar.py && python scripts/gate_calidad.py && python -m pytest tests/ -q
```

- [ ] **Step 2: Actualizar la sección `movilizacion_cepa` → `conflictividad_laboral_srt`**

Reemplazar la sección `### movilizacion_cepa` (buscar en `docs/cinturon_politica.md`) por una nueva `### conflictividad_laboral_srt` que documente: qué mide (conflictos con paro, trimestral, NO conflictividad social amplia), fuente (Secretaría de Trabajo), valor vigente real (de la corrida del Step 1), tamaño real de la serie backfilleada, y el caveat de la Ley de Bases como quiebre estructural.

Actualizar también la tabla de "Indicadores activos" y la tabla de bandas (`BANDAS_ITCP`) en la sección de estructura del ITCP, marcando `conflictividad_laboral_srt` como **provisional**.

- [ ] **Step 3: Actualizar "Score actual del cinturón"**

Con los valores reales de la corrida del Step 1.

- [ ] **Step 4: Staging cuidadoso y commit**

`scripts/descargar_series.py` sigue teniendo el WIP ajeno de motos sin commitear -- usar `git add -p` si se tocó ese archivo en este plan. Verificar `git diff --cached --stat` antes de cada commit.

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): sincroniza cinturon_politica.md con conflictividad_laboral_srt (reemplazo de movilizacion_cepa)"
```
