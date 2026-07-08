# Reemplazo de gobernadores_alineamiento por alineamiento_senadores_prov — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el placeholder manual congelado `gobernadores_alineamiento` (55% desde 2026-04-01, sin fuente automatizable encontrada) por `alineamiento_senadores_prov`: % de votos de senadores NO-LLA que coincide con la posición del bloque LLA, agregado por provincia, promediado entre provincias con al menos 1 senador no-LLA.

**Architecture:** Extiende `_parsear_acta` (ya usada por `fetch_cohesion_bloque`/`fetch_cohesion_bloque_senado`) para extraer también la columna Provincia (celda índice 3, confirmada en vivo idéntica en Diputados y Senado). Nueva función `fetch_alineamiento_senadores_prov` sigue el mismo patrón que `fetch_cohesion_bloque_senado` (misma sesión, mismo descubrimiento de actas, misma ventana de recencia).

**Tech Stack:** Sin dependencias nuevas — reusa `requests`, `BeautifulSoup`, infraestructura ya construida hoy para `cohesion_bloque_senado`.

## Global Constraints

- Spec de diseño: `docs/superpowers/specs/2026-07-08-alineamiento-senadores-provincia-design.md` — leer antes de empezar.
- El indicador mide **voto de senadores**, no postura del gobernador (Poder Ejecutivo) — documentar esto honestamente en `docs/cinturon_politica.md`, no ocultarlo (mismo estándar que `adhesion_reformas_provincial`/RIGI).
- Provincias con 0 senadores no-LLA se EXCLUYEN del promedio (no se cuentan como "100% alineadas" por tautología).
- `gobernadores_alineamiento` NO se borra del código/datos — queda como referencia histórica documentada, se retira solo del peso del ITCP (mismo criterio que dejar `cohesion_bloque` en el código aunque esté bloqueado).
- NO tocar `cohesion_bloque` (Diputados) ni su scraping bloqueado — este plan solo usa la infraestructura de Senado.
- Bandas nuevas quedan **provisional** (mismo mecanismo que el resto de indicadores sin historia aún).

---

### Task 1: Extender `_parsear_acta` con Provincia

**Files:**
- Modify: `scripts/politica.py:1007-1042` (`_parsear_acta`)
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Produces: `_parsear_acta(html) -> list[dict]` ahora con clave `"provincia"` además de `"nombre"`/`"bloque"`/`"voto"`.

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_politica_cohesion.py` (reusar `FIXTURE_ACTA` existente, que ya tiene la estructura real de 6 columnas con Provincia en celda índice 3 — confirmar contra el fixture ya presente en el archivo antes de escribir el test, debe decir "Córdoba"/"Entre Ríos" en sus filas):

```python
def test_parsear_acta_incluye_provincia():
    filas = politica._parsear_acta(FIXTURE_ACTA)
    assert filas[0]["provincia"] == "Córdoba"
    assert filas[1]["provincia"] == "Entre Ríos"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k parsear_acta_incluye_provincia -v`
Expected: FAIL (`KeyError: 'provincia'`)

- [ ] **Step 3: Implementar**

En `scripts/politica.py`, dentro de `_parsear_acta`, agregar la extracción de la celda de provincia (índice 3, mismo índice confirmado en vivo para Diputados y Senado):

```python
        nombre = celdas[1].get_text(strip=True)
        bloque = celdas[2].get_text(strip=True)
        provincia = celdas[3].get_text(strip=True)
        voto = celdas[4].get_text(strip=True).upper()
        if not nombre or not bloque:
            continue
        filas.append({"nombre": nombre, "bloque": bloque, "provincia": provincia, "voto": voto})
```

(Reemplaza el bloque equivalente ya existente — solo agrega la línea de `provincia` y la clave en el dict final.)

- [ ] **Step 4: Run test to verify it passes, y correr toda la suite (este cambio es aditivo pero toca una función muy reusada)**

Run: `cd projects/informe_coyuntura && python -m pytest tests/ -v`
Expected: todos PASS (los tests existentes de `fetch_cohesion_bloque`/`fetch_cohesion_bloque_senado` no deberían romperse — no leen `"provincia"`, y los que hacen `==` contra un dict completo de fila individual deben revisarse: si alguno compara `filas == [{"nombre":..., "bloque":..., "voto":...}]` sin la clave nueva, VA A FALLAR — en ese caso, actualizar esos tests para incluir `"provincia"` en el dict esperado, tomando el valor real del fixture correspondiente).

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): _parsear_acta extrae también la columna Provincia (base para alineamiento_senadores_prov)"
```

---

### Task 2: `fetch_alineamiento_senadores_prov`

**Files:**
- Modify: `scripts/politica.py` (cerca de `fetch_cohesion_bloque_senado`)
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: `_descubrir_actas_senado`, `_paced_get`, `_parsear_acta` (con provincia, Task 1), `es_bloque_lla`
- Produces: `politica.fetch_alineamiento_senadores_prov(anio: int | None = None, dias_ventana: int = 90) -> dict | None`

- [ ] **Step 1: Write the failing tests**

```python
FIXTURE_ACTA_ALINEAMIENTO = """
<table id="myTable">
<tbody>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador uno">SENADOR UNO</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador dos">SENADOR DOS</td>
  <td data-order="la libertad avanza">La Libertad Avanza</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador tres">SENADOR TRES</td>
  <td data-order="union civica radical">Union Civica Radical</td>
  <td data-order="caba">CABA</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador cuatro">SENADOR CUATRO</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-success">AFIRMATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador cinco">SENADOR CINCO</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
<tr>
  <td><div><a><img></a></div></td>
  <td data-order="senador seis">SENADOR SEIS</td>
  <td data-order="union por la patria">Union Por La Patria</td>
  <td data-order="cordoba">Córdoba</td>
  <td><center><span class="label label-danger">NEGATIVO</span></center></td>
  <td></td>
</tr>
</tbody>
</table>
"""


def test_alineamiento_de_una_acta_agrupa_por_provincia_excluyendo_full_lla():
    # Posición LLA en esta acta: 2 senadores LLA de CABA, ambos AFIRMATIVO -> posición = AFIRMATIVO.
    # CABA tiene 1 senador no-LLA (UCR, AFIRMATIVO) -> coincide -> CABA: 1/1 = 100%.
    # Córdoba tiene 3 senadores no-LLA (PJ): AFIRMATIVO, NEGATIVO, NEGATIVO -> 1/3 coincide -> 33.3%.
    # (CABA no se excluye del todo -- tiene 1 senador no-LLA real, solo se ignora el voto de los 2 LLA)
    filas = politica._parsear_acta(FIXTURE_ACTA_ALINEAMIENTO)
    resultado = politica._alineamiento_por_provincia(filas)
    assert resultado == {"CABA": (1, 1), "Córdoba": (1, 3)}  # (coincidencias, total) por provincia


def test_alineamiento_por_provincia_provincia_100pct_lla_no_aparece():
    fixture_solo_lla = FIXTURE_ACTA_ALINEAMIENTO.replace(
        'data-order="union civica radical">Union Civica Radical',
        'data-order="la libertad avanza">La Libertad Avanza',
    )
    filas = politica._parsear_acta(fixture_solo_lla)
    resultado = politica._alineamiento_por_provincia(filas)
    assert "CABA" not in resultado  # los 3 senadores de CABA son LLA -- sin señal, se excluye
    assert resultado == {"Córdoba": (1, 3)}


def test_fetch_alineamiento_senadores_prov_promedia_provincias(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: session)
    monkeypatch.setattr(politica, "_descubrir_actas_senado",
                         lambda s, anio: [{"id": "1", "fecha": datetime(2026, 6, 1)}])
    monkeypatch.setattr(politica, "_paced_get",
                         lambda s, base, path: MagicMock(status_code=200, text=FIXTURE_ACTA_ALINEAMIENTO))

    resultado = politica.fetch_alineamiento_senadores_prov(anio=2026, dias_ventana=366)

    # CABA=100%, Córdoba=33.33...% -> promedio = 66.67%
    assert resultado["valor"] == 66.7
    assert resultado["n_provincias"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k "alineamiento" -v`
Expected: FAIL (`AttributeError`)

- [ ] **Step 3: Implementar**

Agregar en `scripts/politica.py`, después de `fetch_cohesion_bloque_senado`:

```python
def _alineamiento_por_provincia(filas: list[dict]) -> dict:
    """Dada la lista de filas de UNA acta (nombre/bloque/provincia/voto),
    devuelve {provincia: (coincidencias, total)} solo para las provincias que
    tienen AL MENOS 1 senador no-LLA en esa acta. La posición del oficialismo
    en esa acta es el voto mayoritario de los senadores del bloque LLA
    (cualquier provincia); si LLA no tiene votos claros (empate o sin
    senadores LLA presentes) esa acta no aporta señal, se devuelve {}."""
    afirm_lla = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "AFIRMATIVO")
    neg_lla = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "NEGATIVO")
    if afirm_lla == neg_lla:
        return {}
    posicion_lla = "AFIRMATIVO" if afirm_lla > neg_lla else "NEGATIVO"

    resultado = {}
    for f in filas:
        if es_bloque_lla(f["bloque"]) or f["voto"] not in ("AFIRMATIVO", "NEGATIVO"):
            continue
        coincide, total = resultado.get(f["provincia"], (0, 0))
        resultado[f["provincia"]] = (coincide + (1 if f["voto"] == posicion_lla else 0), total + 1)
    return resultado


def fetch_alineamiento_senadores_prov(anio: int | None = None, dias_ventana: int = 90) -> dict | None:
    """% de votos de senadores NO-LLA que coincide con la posición del
    bloque LLA en el Senado, agregado por provincia y promediado entre
    provincias con al menos 1 senador no-LLA (las 100% LLA se excluyen --
    su "alineamiento" con LLA es tautológico, no aporta señal).

    Reemplaza a gobernadores_alineamiento (placeholder manual congelado
    desde 2026-04, sin fuente automatizable encontrada tras 2 rondas de
    investigación). CAVEAT HONESTO: mide comportamiento de voto de
    SENADORES, no la postura pública del gobernador (Poder Ejecutivo
    provincial) -- un senador no depende del gobernador de turno. Es la
    mejor señal automatizable disponible hoy (2026-07-08), no una medición
    directa -- mismo tipo de proxy que adhesion_reformas_provincial/RIGI.

    Misma ventana/ancla que fetch_cohesion_bloque_senado (hoy para año en
    curso, 31-dic para backfill)."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None

    referencia = datetime.now() if anio == datetime.now().year else datetime(anio, 12, 31)
    limite = referencia - timedelta(days=dias_ventana)
    acumulado = {}
    fecha_max = None
    for acta in actas:
        if acta["fecha"] < limite:
            continue
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
        if r is None:
            continue
        filas = _parsear_acta(r.text)
        for provincia, (coincide, total) in _alineamiento_por_provincia(filas).items():
            c0, t0 = acumulado.get(provincia, (0, 0))
            acumulado[provincia] = (c0 + coincide, t0 + total)
        if acumulado:
            fecha_max = acta["fecha"] if fecha_max is None else max(fecha_max, acta["fecha"])

    if not acumulado:
        return {
            "valor": None,
            "unidad": "% votos de senadores no-LLA alineados con LLA, por provincia",
            "fuente": "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
            "fecha_dato": None,
            "n_provincias": 0,
            "corrida_exitosa_en": datetime.now().strftime("%Y-%m-%d"),
            "desactualizado": False,
        }

    ratios_por_provincia = [c / t for c, t in acumulado.values() if t > 0]
    valor = round(100 * sum(ratios_por_provincia) / len(ratios_por_provincia), 1)
    return {
        "valor": valor,
        "unidad": "% votos de senadores no-LLA alineados con LLA, por provincia",
        "fuente": "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
        "fecha_dato": fecha_max.strftime("%Y-%m-%d") if fecha_max else None,
        "n_provincias": len(acumulado),
        "corrida_exitosa_en": datetime.now().strftime("%Y-%m-%d"),
        "desactualizado": False,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_politica_cohesion.py -k "alineamiento" -v`
Expected: todos PASS

- [ ] **Step 5: Verificación en vivo**

```bash
cd projects/informe_coyuntura && python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
print(politica.fetch_alineamiento_senadores_prov(dias_ventana=90))
"
```
Anotar el resultado real en el reporte (valor, n_provincias, fecha_dato). Si `n_provincias` es sospechosamente bajo (ej. 0 o 1), investigar antes de continuar -- no es necesariamente un bug (puede ser receso legislativo o pocas actas divididas recientes), pero documentarlo.

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): fetch_alineamiento_senadores_prov -- reemplaza gobernadores_alineamiento con proxy de voto de senadores por provincia"
```

---

### Task 3: Serie histórica con caché persistente

**Files:**
- Modify: `scripts/descargar_series.py`

**Interfaces:**
- Produces: `descargar_series.fetch_alineamiento_senadores_prov_serie() -> list`

- [ ] **Step 1: Write the failing test**

Mismo patrón que `test_fetch_cohesion_bloque_senado_serie_usa_el_store_de_senado` en `tests/test_descargar_series_cohesion.py` (año cerrado se cachea, año en curso siempre se re-pide):

```python
def test_fetch_alineamiento_senadores_prov_serie_usa_su_propio_store(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "ALINEAMIENTO_SENADORES_STORE", tmp_path / "alineamiento.json")
    monkeypatch.setattr(descargar_series.politica, "fetch_alineamiento_senadores_prov",
                         lambda anio, dias_ventana: {"valor": 66.7})
    serie = descargar_series.fetch_alineamiento_senadores_prov_serie(anio_inicio=2026)
    assert serie == [["2026-01-01", 66.7]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_descargar_series_cohesion.py -k alineamiento_senadores_prov_serie -v`
Expected: FAIL

- [ ] **Step 3: Implementar**

Reusar `_serie_cohesion_cacheada` (ya genérica, agregada hoy en el plan de `cohesion_bloque_senado`) en vez de duplicar la lógica de caché:

```python
ALINEAMIENTO_SENADORES_STORE = Path(__file__).resolve().parents[1] / "data" / "politica" / "alineamiento_senadores_serie.json"


def fetch_alineamiento_senadores_prov_serie(anio_inicio: int = 2023) -> list:
    """Serie ANUAL de alineamiento_senadores_prov (reemplaza a
    gobernadores_alineamiento). Caché persistente por año, ver
    _serie_cohesion_cacheada."""
    return _serie_cohesion_cacheada(ALINEAMIENTO_SENADORES_STORE, politica.fetch_alineamiento_senadores_prov,
                                     anio_inicio, "alineamiento_senadores_prov")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_descargar_series_cohesion.py -v`
Expected: todos PASS

- [ ] **Step 5: Registrar en POLITICA_DERIVADAS**

Agregar en `descargar_series.py`:

```python
    ("alineamiento_senadores_prov", "% votos de senadores no-LLA alineados con LLA",
     "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
     fetch_alineamiento_senadores_prov_serie),
```

- [ ] **Step 6: Verificación en vivo + backfill real**

```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py
```
Confirmar filas `alineamiento_senadores_prov` en `output/series/politica.csv`.

- [ ] **Step 7: Commit**

```bash
git add scripts/descargar_series.py tests/test_descargar_series_cohesion.py
git commit -m "feat(politica): serie histórica de alineamiento_senadores_prov con caché persistente por año"
```

---

### Task 4: Wiring en itcp.py y politica.py

**Files:**
- Modify: `scripts/itcp.py` (BANDAS_ITCP, DIMENSIONES_ITCP)
- Modify: `scripts/politica.py` (INDICADORES_ESPERADOS, main())
- Test: `tests/test_itcp.py`

- [ ] **Step 1: Write the failing test**

```python
def test_bandas_itcp_tiene_alineamiento_senadores_prov_no_gobernadores_alineamiento():
    assert "alineamiento_senadores_prov" in itcp.BANDAS_ITCP
    dim = itcp.DIMENSIONES_ITCP["alianzas_territoriales"]
    assert "alineamiento_senadores_prov" in dim["indicadores"]
    assert "gobernadores_alineamiento" not in dim["indicadores"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_itcp.py -k alineamiento_senadores_prov -v`

- [ ] **Step 3: Actualizar `itcp.py`**

En `BANDAS_ITCP`, agregar (marcada provisional, mismo criterio que el resto de bandas sin historia aún):

```python
    "alineamiento_senadores_prov": [
        # Provisional (2026-07-08, sin historia real todavía): mismas
        # anclas que gobernadores_alineamiento (mismo tipo de escala 0-100%
        # de alineamiento) hasta recalibrar con datos reales backfilleados.
        (0, 10, 10),
        (10, 25, 40),
        (25, 45, 65),
        (45, 65, 85),
        (65, 100, 100),
    ],
```

En `DIMENSIONES_ITCP["alianzas_territoriales"]["indicadores"]`, reemplazar `"gobernadores_alineamiento"` por `"alineamiento_senadores_prov"` (mismo peso interno, 30%).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/informe_coyuntura && python -m pytest tests/test_itcp.py -v`

- [ ] **Step 5: Actualizar `politica.py`**

- En `INDICADORES_ESPERADOS`: reemplazar `"gobernadores_alineamiento"` por `"alineamiento_senadores_prov"`.
- En `main()`, agregar `fetch_alineamiento_senadores_prov` a la lista de colectores (reemplazando la lectura manual de `gobernadores_alineamiento` desde `manuales.json` para efectos del ITCP -- pero SIN borrar la lectura de `manuales.json` en sí, que puede seguir existiendo como dato de referencia/contexto histórico si el código actual la expone en otro lado; revisar el código real de `main()` antes de decidir si hace falta tocar la lectura de manuales.json o si alcanza con no usar más ese valor para el ITCP).

- [ ] **Step 6: Correr la suite completa + verificación en vivo del ITCP**

```bash
cd projects/informe_coyuntura && python -m pytest tests/ -v && python scripts/politica.py
```

- [ ] **Step 7: Commit**

```bash
git add scripts/itcp.py scripts/politica.py tests/test_itcp.py
git commit -m "feat(politica): reemplaza gobernadores_alineamiento por alineamiento_senadores_prov en el ITCP"
```

---

### Task 5: Sync final de `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md`

- [ ] **Step 1: Correr el pipeline completo**

```bash
cd projects/informe_coyuntura && python scripts/descargar_series.py && python scripts/politica.py && python scripts/validacion_externa.py && python scripts/generar_informe.py && python scripts/publicar.py && python scripts/gate_calidad.py && python -m pytest tests/ -q
```

- [ ] **Step 2: Reemplazar la sección de `gobernadores_alineamiento` por `alineamiento_senadores_prov`**

Documentar qué mide (voto de senadores no-LLA vs. posición LLA, por provincia), el caveat honesto (no mide postura del gobernador), valor vigente real (de la corrida del Step 1), y agregar una nota breve indicando que `gobernadores_alineamiento` (55%, congelado desde abril) queda documentado como intento manual descartado, ya no pondera en el ITCP.

- [ ] **Step 3: Actualizar "Score actual del cinturón" y la tabla de bandas**

Con los valores reales de la corrida del Step 1. Marcar `alineamiento_senadores_prov` como **provisional** en la tabla de bandas.

- [ ] **Step 4: Staging cuidadoso y commit**

`scripts/descargar_series.py` sigue teniendo el WIP ajeno de motos sin commitear -- usar `git add -p` si se tocó ese archivo. Verificar `git diff --cached --stat` antes de cada commit.

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): sincroniza cinturon_politica.md con alineamiento_senadores_prov (reemplazo de gobernadores_alineamiento)"
```
