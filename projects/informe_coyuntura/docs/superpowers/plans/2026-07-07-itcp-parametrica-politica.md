# Paramétrica ITCP del cinturón política — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Depende de:** `docs/superpowers/plans/2026-07-07-cohesion-bloque-automatizacion.md` debe estar completo y mergeado antes de empezar (este plan reutiliza `indice_rice`, `es_bloque_lla`, `_parsear_acta`, `_hcdn_votaciones_session` de ese plan).

**Goal:** Reemplazar el promedio simple de política (`calcular_score()`) por una paramétrica ITCP (0-100) con 5 dimensiones de Matus pesadas, espejando `itcm.py`/`itcg.py`/`itvc.py`, sumando 3 indicadores nuevos (`cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba` reutilizado de gestión).

**Architecture:** Un módulo nuevo `scripts/itcp.py` (dimensiones, bandas, `calcular_itcp()`) delega el algoritmo a `scripts/parametrica.py` (ya existente, sin cambios). `scripts/politica.py` gana 2 fetchers nuevos que reusan la infraestructura de scraping del plan anterior, más la reutilización directa del fetcher ACLED que ya existe en `gestion.py`.

**Tech Stack:** Python 3, mismo stack que el plan anterior. `parametrica.py` no se modifica.

## Global Constraints

- Convención de bandas: `(low, high, puntaje)` con low exclusivo, high inclusivo, puntajes canónicos 100/85/65/40/10 (misma convención que `itcg.py`/`itcm.py`, pineada por tests).
- Pesos de dimensión: Poder legislativo 30% · Alianzas territoriales 25% · Cohesión interna 20% · Conflicto social 15% · Imagen y voto 10% (acordados en el spec, no reabrir).
- `cohesion_bloque_senado` es indicador COMPLEMENTARIO — nunca reemplaza a `cohesion_bloque` (Diputados) en ningún cálculo.
- `adhesion_reformas_provincial` se presenta como adhesión fiscal a un régimen puntual (RIGI) — nunca como proxy de `gobernadores_alineamiento` en textos públicos ni en el ADR.
- Todas las bandas nuevas/recalibradas (`cohesion_bloque`, `cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`) se marcan explícitamente como PROVISIONALES en el código (comentario) y en el ADR.

---

### Task 1: Módulo `scripts/itcp.py` — dimensiones, bandas y `calcular_itcp()`

**Files:**
- Create: `scripts/itcp.py`
- Test: `tests/test_itcp.py` (nuevo)

**Interfaces:**
- Consumes: `parametrica.calcular_indice`, `parametrica.banda_interpretacion`, `parametrica.tension_de_indice`, `parametrica.cargar_ajustes`, `parametrica.texto_bandas` (todos ya existen en `scripts/parametrica.py`, sin cambios)
- Produces: `itcp.calcular_itcp(valores: dict, ajustes: dict | None = None) -> dict | None`, `itcp.banda_interpretacion(itcp: float) -> str`, `itcp.tension_de_itcp(itcp: float) -> float`, `itcp.cargar_ajustes(path, periodo) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_itcp.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcp


def test_banda_votometro_extremos():
    # (15,inf,100)·(5,15,85)·(-5,5,65)·(-15,-5,40)·(-inf,-15,10)
    assert itcp.puntaje_banda(20.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 100
    assert itcp.puntaje_banda(15.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 100
    assert itcp.puntaje_banda(14.9, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 85
    assert itcp.puntaje_banda(-20.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 10


def test_banda_low_exclusivo_high_inclusivo():
    bandas = itcp.BANDAS_ITCP["ratio_dnu"]  # (-inf,0.3,100)·(0.3,0.7,85)·...
    assert itcp.puntaje_banda(0.3, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(0.30001, bandas) == 85  # low exclusivo del siguiente tramo


def test_calcular_itcp_pondera_dimensiones():
    valores = {
        "votometro_ventaja_lla": 15.0,       # imagen_voto, puntaje 100
        "ratio_dnu": 0.2,                    # poder_legislativo, puntaje 100
        "eficacia_legislativa": 60.0,        # poder_legislativo, puntaje 100
        "veto_quorum": 2.0,                  # poder_legislativo, puntaje 100
        "comisiones_caidas": 10.0,           # poder_legislativo, puntaje 100
        "iaf_transferencias": 12.0,          # alianzas_territoriales, puntaje 100
        "gobernadores_alineamiento": 70.0,   # alianzas_territoriales, puntaje 100
        "adhesion_reformas_provincial": 90.0, # alianzas_territoriales, puntaje 100
        "cohesion_bloque": 95.0,             # cohesion_interna, puntaje 100
        "cohesion_bloque_senado": 95.0,      # cohesion_interna, puntaje 100
        "movilizacion_cepa": 5.0,            # conflicto_social, puntaje 100
        "protestas_caba": 5.0,               # conflicto_social, puntaje 100
    }
    resultado = itcp.calcular_itcp(valores)
    assert resultado is not None
    assert resultado["valor"] == 100.0
    assert resultado["banda"] == "aflojado"


def test_calcular_itcp_renormaliza_ante_faltantes():
    # Solo imagen_voto disponible -> esa dimensión sola determina el índice
    resultado = itcp.calcular_itcp({"votometro_ventaja_lla": 15.0})
    assert resultado is not None
    assert resultado["valor"] == 100.0


def test_calcular_itcp_sin_datos_devuelve_none():
    assert itcp.calcular_itcp({}) is None


def test_calcular_itcp_aplica_ajustes_con_vencimiento(tmp_path):
    ajustes_path = tmp_path / "ajustes_itcp.json"
    ajustes_path.write_text(
        '{"cohesion_bloque": {"puntaje": 50, "justificacion": "test", "vigente_hasta": "2099-12"}}',
        encoding="utf-8",
    )
    ajustes = itcp.cargar_ajustes(ajustes_path, "2026-07")
    resultado = itcp.calcular_itcp({"cohesion_bloque": 95.0}, ajustes)
    assert resultado["dimensiones"]["cohesion_interna"]["indicadores"]["cohesion_bloque"]["puntaje_aplicado"] == 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/test_itcp.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'itcp'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/itcp.py
"""ITCP — Índice de Tensión del Cinturón Político (capital político según
Matus: capacidad de gobernar, NO popularidad).

ITCP = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor)), escala
0-100 donde 100 = mínima tensión (máximo capital político). Tensión 0-10 del
informe = (100 − ITCP) / 10 (motor común en parametrica.py).

A diferencia de ITCM/ITCG/ITVC, NO hay un documento CIGOB que fije los pesos
de las 5 dimensiones (imagen y voto, poder legislativo, alianzas
territoriales, cohesión interna del oficialismo, conflicto social) — ya
descriptas en docs/cinturon_politica.md pero nunca pesadas. Los pesos acá son
una decisión editorial explícita (ver ADR-0035): "imagen y voto" pesa
deliberadamente MENOS que las demás porque el propio marco del proyecto
distingue capital político de popularidad.

Bandas de cohesion_bloque, cohesion_bloque_senado, adhesion_reformas_provincial
y protestas_caba son PROVISIONALES (sin serie histórica propia todavía) — ver
ADR-0035, a recalibrar cuando el backfill esté corriendo.
"""
import parametrica

INF = float("inf")

BANDAS_ITCP = {
    "votometro_ventaja_lla": [           # pp gap LLA-PJ, mayor = mejor
        (15.0, INF, 100), (5.0, 15.0, 85), (-5.0, 5.0, 65), (-15.0, -5.0, 40), (-INF, -15.0, 10),
    ],
    "ratio_dnu": [                        # DNUs / leyes, menor = mejor
        (-INF, 0.3, 100), (0.3, 0.7, 85), (0.7, 1.2, 65), (1.2, 2.0, 40), (2.0, INF, 10),
    ],
    "eficacia_legislativa": [             # % proyectos PE aprobados, mayor = mejor
        (55.0, INF, 100), (35.0, 55.0, 85), (15.0, 35.0, 65), (5.0, 15.0, 40), (-INF, 5.0, 10),
    ],
    "veto_quorum": [                      # % sesiones fracasadas, menor = mejor
        (-INF, 5.0, 100), (5.0, 10.0, 85), (10.0, 20.0, 65), (20.0, 30.0, 40), (30.0, INF, 10),
    ],
    "comisiones_caidas": [                # % varados (20-30% es "normal" según el doc), menor = mejor
        (-INF, 30.0, 100), (30.0, 50.0, 85), (50.0, 70.0, 65), (70.0, 85.0, 40), (85.0, INF, 10),
    ],
    "iaf_transferencias": [               # % var real YoY transferencias federales, mayor = mejor
        (10.0, INF, 100), (0.0, 10.0, 85), (-10.0, 0.0, 65), (-20.0, -10.0, 40), (-INF, -20.0, 10),
    ],
    "gobernadores_alineamiento": [        # % gobernadores alineados, mayor = mejor (manual)
        (65.0, INF, 100), (45.0, 65.0, 85), (25.0, 45.0, 65), (10.0, 25.0, 40), (-INF, 10.0, 10),
    ],
    "adhesion_reformas_provincial": [     # % provincias adheridas RIGI, mayor = mejor — PROVISIONAL
        (80.0, INF, 100), (60.0, 80.0, 85), (40.0, 60.0, 65), (20.0, 40.0, 40), (-INF, 20.0, 10),
    ],
    "cohesion_bloque": [                  # índice de Rice %, mayor = mejor — PROVISIONAL
        (90.0, INF, 100), (75.0, 90.0, 85), (60.0, 75.0, 65), (40.0, 60.0, 40), (-INF, 40.0, 10),
    ],
    "cohesion_bloque_senado": [           # mismo constructo que cohesion_bloque — PROVISIONAL
        (90.0, INF, 100), (75.0, 90.0, 85), (60.0, 75.0, 65), (40.0, 60.0, 40), (-INF, 40.0, 10),
    ],
    "movilizacion_cepa": [                # índice 0-100, menor = mejor
        (-INF, 20.0, 100), (20.0, 40.0, 85), (40.0, 60.0, 65), (60.0, 80.0, 40), (80.0, INF, 10),
    ],
    "protestas_caba": [                   # nivel 0-100 (mismo tratamiento que CEPA) — PROVISIONAL
        (-INF, 20.0, 100), (20.0, 40.0, 85), (40.0, 60.0, 65), (60.0, 80.0, 40), (80.0, INF, 10),
    ],
}

DIMENSIONES_ITCP = {
    "poder_legislativo": {
        "nombre": "Poder legislativo",
        "peso": 0.30,
        "indicadores": {"ratio_dnu": 0.25, "eficacia_legislativa": 0.30,
                        "veto_quorum": 0.20, "comisiones_caidas": 0.25},
    },
    "alianzas_territoriales": {
        "nombre": "Alianzas territoriales",
        "peso": 0.25,
        "indicadores": {"iaf_transferencias": 0.40, "gobernadores_alineamiento": 0.30,
                        "adhesion_reformas_provincial": 0.30},
    },
    "cohesion_interna": {
        "nombre": "Cohesión interna del oficialismo",
        "peso": 0.20,
        "indicadores": {"cohesion_bloque": 0.65, "cohesion_bloque_senado": 0.35},
    },
    "conflicto_social": {
        "nombre": "Conflicto social",
        "peso": 0.15,
        "indicadores": {"movilizacion_cepa": 0.60, "protestas_caba": 0.40},
    },
    "imagen_voto": {
        "nombre": "Imagen y voto",
        "peso": 0.10,
        "indicadores": {"votometro_ventaja_lla": 1.0},
    },
}

BANDAS_INTERPRETACION = [
    (-INF, 20.0, "severamente_apretado"),
    (20.0, 40.0, "apretado"),
    (40.0, 60.0, "moderadamente_apretado"),
    (60.0, 80.0, "moderadamente_aflojado"),
    (80.0, INF, "aflojado"),
]

INTERPRETACION_LEGIBLE = {
    "severamente_apretado":   "Severamente apretado",
    "apretado":               "Apretado",
    "moderadamente_apretado": "Moderadamente apretado",
    "moderadamente_aflojado": "Moderadamente aflojado",
    "aflojado":               "Aflojado",
}


def puntaje_banda(valor: float, bandas: list) -> int:
    return parametrica.puntaje_banda(valor, bandas)


def banda_interpretacion(itcp: float) -> str:
    return parametrica.banda_interpretacion(itcp, BANDAS_INTERPRETACION)


def tension_de_itcp(itcp: float) -> float:
    return parametrica.tension_de_indice(itcp)


def texto_bandas(indicador: str) -> str:
    return parametrica.texto_bandas(BANDAS_ITCP[indicador])


def cargar_ajustes(path, periodo: str) -> dict:
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itcp(valores: dict, ajustes: dict | None = None) -> dict | None:
    """Calcula el ITCP a partir de {indicador: valor} (None se ignora)."""
    return parametrica.calcular_indice(
        valores, ajustes, BANDAS_ITCP, DIMENSIONES_ITCP,
        BANDAS_INTERPRETACION, INTERPRETACION_LEGIBLE)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/test_itcp.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/itcp.py tests/test_itcp.py
git commit -m "feat(politica): módulo itcp.py — paramétrica de 5 dimensiones"
```

---

### Task 2: `fetch_cohesion_bloque_senado()`

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: `_hcdn_votaciones_session`, `_parsear_acta`, `es_bloque_lla`, `indice_rice` (del plan anterior)
- Produces: `politica._paced_get(session, base_url, path, **kwargs)` (generaliza `_hcdn_votaciones_get`), `politica._descubrir_actas_senado(session, anio) -> list[dict] | None`, `politica.fetch_cohesion_bloque_senado(anio=None, dias_ventana=90) -> dict | None`

- [ ] **Step 1: Write the failing tests**

```python
FIXTURE_LISTADO_SENADO = """
<table>
<tr>
  <td><span style="display:none">20260211</span> 11/02/2026</td>
  <td>Modernización Laboral. Título I.
    <a href="/votaciones/detalleActa/2623">Ver</a>
  </td>
</tr>
</table>
"""


def test_paced_get_reusa_logica_de_pacing(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._paced_get(session, "https://www.senado.gob.ar", "/votaciones/actas")
    assert r.status_code == 200
    session.get.assert_called_with("https://www.senado.gob.ar/votaciones/actas", timeout=politica.HTTP_TIMEOUT)


def test_hcdn_votaciones_get_sigue_funcionando_via_paced_get(monkeypatch):
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200)
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    r = politica._hcdn_votaciones_get(session, "/votaciones/actas")
    assert r.status_code == 200
    session.get.assert_called_with(f"{politica.HCDN_VOTACIONES_BASE}/votaciones/actas", timeout=politica.HTTP_TIMEOUT)


def test_descubrir_actas_senado_extrae_id_y_fecha():
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200, text=FIXTURE_LISTADO_SENADO)
    actas = politica._descubrir_actas_senado(session, 2026)
    assert actas == [{"id": "2623", "fecha": datetime(2026, 2, 11)}]


def test_fetch_cohesion_bloque_senado_es_complementario(monkeypatch):
    hoy = datetime.now()
    actas = [{"id": "2623", "fecha": hoy - timedelta(days=5)}]
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: MagicMock())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, a: actas)
    monkeypatch.setattr(politica, "_paced_get", lambda s, base, path: MagicMock(text="<html></html>"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda html: [
        {"nombre": "X", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
        {"nombre": "Y", "bloque": "LA LIBERTAD AVANZA", "voto": "AFIRMATIVO"},
    ])
    resultado = politica.fetch_cohesion_bloque_senado()
    assert resultado["valor"] == 100.0
    assert "Senado" in resultado["fuente"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k "paced_get or senado"`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write the implementation**

Reemplazar el cuerpo de `_hcdn_votaciones_get` (Tarea 3 del plan anterior) para
que delegue en una función generalizada, y agregar el fetcher de Senado:

```python
SENADO_BASE = "https://www.senado.gob.ar"


def _paced_get(session: requests.Session, base_url: str, path: str, **kwargs):
    """GET con pacing fijo y retry/backoff ante 403 (hasta 3 intentos).
    Generaliza el helper de HCDN para reusar sesión/pacing contra Senado."""
    url = f"{base_url}{path}"
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


def _hcdn_votaciones_get(session: requests.Session, path: str, **kwargs):
    return _paced_get(session, HCDN_VOTACIONES_BASE, path, **kwargs)


_RE_DETALLE_ACTA_SENADO = re.compile(r"/votaciones/detalleActa/(\d+)")


def _descubrir_actas_senado(session: requests.Session, anio: int):
    """GET a /votaciones/actas (listado con fecha en <span style="display:none">
    YYYYMMDD</span> y link <a href="/votaciones/detalleActa/{id}">) ->
    [{id, fecha}] del año dado. Estructura confirmada en vivo (Senado, HTML
    server-side, sin headless browser). parser="html.parser": lxml no está en
    requirements.txt (Tarea 4 del plan de cohesion_bloque). Reusa
    _RE_DISPLAY_NONE (mismo plan, Tarea 4) en vez de un match exacto de
    "display:none" — la Tarea 4 confirmó que el HTML real de HCDN usa
    "display: none" CON espacio; dado que Senado es la misma familia de sitios
    de gobierno, no asumir que acá sí seŕa sin espacio sin verificarlo en vivo
    (ver Step de verificación más abajo)."""
    r = _paced_get(session, SENADO_BASE, "/votaciones/actas")
    if r is None:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    actas = []
    vistos = set()
    for fila in soup.select("tr"):
        link = fila.find("a", href=_RE_DETALLE_ACTA_SENADO)
        span_fecha = fila.find("span", style=lambda s: s and _RE_DISPLAY_NONE.search(s))
        if link is None or span_fecha is None:
            continue
        m = _RE_DETALLE_ACTA_SENADO.search(link["href"])
        if not m:
            continue
        id_acta = m.group(1)
        try:
            fecha = datetime.strptime(span_fecha.get_text(strip=True), "%Y%m%d")
        except ValueError:
            continue
        if fecha.year != anio or id_acta in vistos:
            continue
        vistos.add(id_acta)
        actas.append({"id": id_acta, "fecha": fecha})
    return actas


def fetch_cohesion_bloque_senado(anio: int | None = None, dias_ventana: int = 90) -> dict | None:
    """Cohesión del bloque LLA en el Senado — mismo índice de Rice que
    fetch_cohesion_bloque, indicador COMPLEMENTARIO (otra cámara, otra
    composición de bloque): nunca reemplaza al de Diputados."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None

    limite = datetime.now() - timedelta(days=dias_ventana)
    indices = []
    fecha_max = None
    for acta in actas:
        if acta["fecha"] < limite:
            continue
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
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
        "unidad": "% cohesión (índice de Rice, Senado), promedio actas divididas últimos 90 días",
        "fuente": "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
        "fecha_dato": fecha_max.strftime("%Y-%m-%d") if fecha_max else None,
        "n_actas": len(indices),
        "corrida_exitosa_en": datetime.now().strftime("%Y-%m-%d"),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v`
Expected: todos los tests (plan anterior + esta tarea) pasan

- [ ] **Step 4b: Verificación en vivo (obligatoria antes de continuar)**

La Tarea 4 del plan de `cohesion_bloque` confirmó que HCDN usa
`"display: none"` (CON espacio) en el sitio de Diputados, no `"display:none"`
— y que el sitio devuelve 403 desde este tipo de entorno (bloqueo a nivel IP,
no resuelto con pacing/retry/UA). Antes de confiar esta tarea a producción,
repetir el mismo intento contra `senado.gob.ar` (probablemente NO esté detrás
del mismo bloqueo — es un host distinto — pero no asumirlo):

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
s = politica._hcdn_votaciones_session()
actas = politica._descubrir_actas_senado(s, 2026)
print(actas[:3] if actas else actas)
"
```

Si responde con datos reales, confirmar que el espaciado de `display:none`
coincide con el fixture (ajustar si difiere, igual que la Tarea 4). Si devuelve
`None`/403, documentarlo como el mismo tipo de bloqueo ya conocido (no bloquea
esta tarea — el guard de frescura de la Tarea 7 del plan anterior ya cubre
este caso) y seguir con el Step 5.

- [ ] **Step 5: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): cohesion_bloque_senado como indicador complementario"
```

---

### Task 3: `fetch_adhesion_reformas_provincial()`

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Produces: `politica.fetch_adhesion_reformas_provincial() -> dict | None`

- [ ] **Step 1: Write the failing tests**

```python
FIXTURE_TABLA_RIGI = """
<table>
<tr><td>CATAMARCA</td><td><a href="/ley_dgr_catamarca">Ley DGR Catamarca 5.863</a></td></tr>
<tr><td>CHUBUT</td><td><a href="/ley_dgr_chubut">Ley DGR Chubut 123</a></td></tr>
</table>
"""


def test_fetch_adhesion_reformas_provincial_cuenta_provincias(monkeypatch):
    monkeypatch.setattr(politica.requests, "get",
        lambda *a, **kw: MagicMock(status_code=200, text=FIXTURE_TABLA_RIGI))
    resultado = politica.fetch_adhesion_reformas_provincial()
    assert resultado["n_provincias"] == 2
    assert resultado["valor"] == round(2 / 24 * 100, 1)


def test_fetch_adhesion_reformas_provincial_request_fallido(monkeypatch):
    monkeypatch.setattr(politica.requests, "get",
        lambda *a, **kw: MagicMock(status_code=500, text=""))
    assert politica.fetch_adhesion_reformas_provincial() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k adhesion_reformas`
Expected: FAIL con `AttributeError`

- [ ] **Step 3: Write the implementation**

```python
MAGYP_RIGI_URL = "https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php"


def fetch_adhesion_reformas_provincial() -> dict | None:
    """% de provincias (sobre 24) adheridas formalmente al RIGI (Título VII,
    Ley 27.742) — tabla MAGyP. Mide adhesión FISCAL a un régimen puntual, NO
    alineamiento político general — no reemplaza a gobernadores_alineamiento.
    parser="html.parser" (stdlib, lxml no está en requirements.txt — ver
    Tarea 4 del plan de cohesion_bloque): el sitio fuente tiene un <tr> vacío
    malformado que con html.parser produce una fila SANTA CRUZ duplicada
    (confirmado en vivo en la investigación previa) — no requiere lxml para
    resolverlo, `provincias` ya es un `set()` más abajo, así que agregar el
    mismo nombre dos veces es un no-op y el conteo final no se infla."""
    try:
        r = requests.get(MAGYP_RIGI_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    provincias = set()
    for fila in soup.select("table tr"):
        celdas = fila.find_all("td")
        if len(celdas) < 2:
            continue
        provincia = celdas[0].get_text(strip=True)
        if provincia:
            provincias.add(provincia.upper())
    if not provincias:
        return None
    return {
        "valor": round(len(provincias) / 24.0 * 100.0, 1),
        "unidad": "% de provincias (sobre 24) adheridas al RIGI",
        "fuente": "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
        "fecha_dato": datetime.now().strftime("%Y-%m-%d"),
        "n_provincias": len(provincias),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k adhesion_reformas`
Expected: 2 passed

- [ ] **Step 5: Verificación en vivo**

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
import politica
print(politica.fetch_adhesion_reformas_provincial())
"
```
Expected: dict con `n_provincias` cercano a 16 (dato observado en la
investigación previa) — si la tabla cambió de estructura, ajustar los
selectores antes de continuar.

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): adhesion_reformas_provincial (RIGI) como indicador nuevo"
```

---

### Task 4: Reutilizar `protestas_caba` de gestión

**Files:**
- Modify: `scripts/politica.py`
- Test: `tests/test_politica_cohesion.py`

**Interfaces:**
- Consumes: fetcher de ACLED ya existente en `scripts/gestion.py` (ADR-0017) — **el nombre exacto de la función no está confirmado en este plan; el primer step de esta tarea es encontrarlo**.

- [ ] **Step 1: Encontrar el fetcher existente**

```bash
cd "projects/informe_coyuntura" && grep -n "def fetch.*acled\|def fetch.*protesta\|protestas_caba" scripts/gestion.py
```

Anotar el nombre exacto de la función y su firma (probablemente algo como
`fetch_protestas_caba()` o `fetch_acled_protestas()`, devolviendo el mismo
formato `{"valor": ..., "fuente": ..., "fecha_dato": ...}` que los demás
indicadores del proyecto).

- [ ] **Step 2: Write the failing test**

Ajustar el nombre `fetch_protestas_caba_gestion` en el test de abajo por el
nombre real encontrado en el Step 1:

```python
def test_politica_reutiliza_fetcher_de_gestion(monkeypatch):
    import gestion
    monkeypatch.setattr(gestion, "fetch_protestas_caba_gestion",  # <- ajustar nombre real
                         lambda: {"valor": 12.0, "fecha_dato": "2026-07-07"})
    resultado = politica.fetch_protestas_caba()
    assert resultado["valor"] == 12.0
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k protestas_caba`
Expected: FAIL con `AttributeError` (no existe `politica.fetch_protestas_caba`
todavía)

- [ ] **Step 4: Write the implementation**

En `scripts/politica.py`, agregar el import de `gestion` (mismo directorio,
`import gestion` alcanza dado que ambos scripts viven en `scripts/`) y:

```python
import gestion  # reutiliza el fetcher ACLED ya construido para protestas_caba (ADR-0017)


def fetch_protestas_caba() -> dict | None:
    """Reutiliza el fetcher ACLED de gestion.py. En gestión no puntúa
    ('premiaría menos marchas', ADR-0017); en política SÍ puntúa como
    condición objetiva de gobernabilidad (nivel de conflicto social), no
    como juicio sobre la legitimidad de protestar."""
    return gestion.fetch_protestas_caba_gestion()  # <- ajustar al nombre real (Step 1)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_politica_cohesion.py -v -k protestas_caba`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py tests/test_politica_cohesion.py
git commit -m "feat(politica): reutiliza protestas_caba de gestión como indicador de conflicto social"
```

---

### Task 5: Wiring de `itcp.calcular_itcp()` en `main()`

**Files:**
- Modify: `scripts/politica.py`

- [ ] **Step 1: Agregar los 3 fetchers nuevos a `colectores`**

```python
    colectores = [
        ("votometro_ventaja_lla",         fetch_votometro),
        ("ratio_dnu",                     fetch_ratio_dnu),
        ("movilizacion_cepa",             fetch_cepa_movilizacion),
        ("iaf_transferencias",            fetch_iaf_transferencias),
        ("eficacia_legislativa",          fetch_eficacia_legislativa),
        ("gobernadores_alineamiento",     lambda: fetch_manual("gobernadores_alineamiento")),
        ("veto_quorum",                   fetch_veto_quorum),
        ("comisiones_caidas",             fetch_comisiones_caidas),
        ("adhesion_reformas_provincial",  fetch_adhesion_reformas_provincial),
        ("protestas_caba",                fetch_protestas_caba),
    ]
```

`cohesion_bloque` y `cohesion_bloque_senado` se manejan aparte (no en la lista
`colectores` genérica), igual que en el plan anterior. En `main()`, el bloque
especial que el plan anterior agregó para `cohesion_bloque` (después del `for
nombre, fetcher in colectores:` loop, antes de `score = ...`) queda así, con
`cohesion_bloque_senado` repitiendo la misma lógica:

```python
    resultado_cohesion = fetch_cohesion_bloque()
    anterior_cohesion = indicadores_anteriores.get("cohesion_bloque")
    if resultado_cohesion is not None and resultado_cohesion.get("valor") is not None:
        frescos["cohesion_bloque"] = resultado_cohesion
        frescos_count += 1
    elif resultado_cohesion is not None and anterior_cohesion is not None:
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

    resultado_cohesion_senado = fetch_cohesion_bloque_senado()
    anterior_cohesion_senado = indicadores_anteriores.get("cohesion_bloque_senado")
    if resultado_cohesion_senado is not None and resultado_cohesion_senado.get("valor") is not None:
        frescos["cohesion_bloque_senado"] = resultado_cohesion_senado
        frescos_count += 1
    elif resultado_cohesion_senado is not None and anterior_cohesion_senado is not None:
        frescos["cohesion_bloque_senado"] = {
            **anterior_cohesion_senado,
            "desactualizado": False,
            "corrida_exitosa_en": resultado_cohesion_senado["corrida_exitosa_en"],
        }
        frescos_count += 1
    elif anterior_cohesion_senado is not None:
        frescos["cohesion_bloque_senado"] = {
            **anterior_cohesion_senado,
            "desactualizado": _cohesion_desactualizada(anterior_cohesion_senado, resultado_cohesion_senado),
        }
```

- [ ] **Step 2: Actualizar `INDICADORES_ESPERADOS`**

```python
INDICADORES_ESPERADOS = [
    "votometro_ventaja_lla",
    "ratio_dnu",
    "movilizacion_cepa",
    "iaf_transferencias",
    "cohesion_bloque",
    "cohesion_bloque_senado",
    "eficacia_legislativa",
    "gobernadores_alineamiento",
    "adhesion_reformas_provincial",
    "veto_quorum",
    "comisiones_caidas",
    "protestas_caba",
]
```

- [ ] **Step 3: Reemplazar `calcular_score()` por `itcp.calcular_itcp()`**

Agregar `import itcp` al tope de `politica.py`. En `main()`, reemplazar:

```python
    score   = calcular_score(frescos)
```

por:

```python
    ajustes = itcp.cargar_ajustes(PROJECT_DIR / "data" / "politica" / "ajustes_itcp.json",
                                   datetime.now().strftime("%Y-%m"))
    valores = {k: v["valor"] for k, v in frescos.items() if v.get("valor") is not None}
    resultado_itcp = itcp.calcular_itcp(valores, ajustes)
    score = itcp.tension_de_itcp(resultado_itcp["valor"]) if resultado_itcp else 5.0
```

Y en el `payload` que se guarda en cache, agregar el detalle del índice:

```python
    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "itcp":         resultado_itcp,
        "indicadores":  frescos,
    }
```

`calcular_score()` queda en el archivo sin usar — eliminarla en este paso (ya
no tiene caller; dejar código muerto violaría YAGNI).

- [ ] **Step 4: Correr los tests**

Run: `cd "projects/informe_coyuntura" && python -m pytest tests/ -v`
Expected: todos pasan.

- [ ] **Step 5: Prueba manual end-to-end**

Run: `python scripts/politica.py`
Expected: exit 0 o 1, `output/cache/politica.json` tiene una clave `itcp` con
`valor`, `banda`, `dimensiones` (5 claves: `poder_legislativo`,
`alianzas_territoriales`, `cohesion_interna`, `conflicto_social`, `imagen_voto`).

- [ ] **Step 6: Commit**

```bash
git add scripts/politica.py
git commit -m "feat(politica): reemplaza calcular_score() por la paramétrica ITCP"
```

---

### Task 6: `data/politica/ajustes_itcp.json` (nuevo, vacío)

**Files:**
- Create: `data/politica/ajustes_itcp.json`

- [ ] **Step 1: Crear el archivo**

```json
{}
```

- [ ] **Step 2: Commit**

```bash
git add data/politica/ajustes_itcp.json
git commit -m "feat(politica): archivo de overrides del analista para ITCP"
```

---

### Task 7: Backfill de las series nuevas

**Files:**
- Modify: `scripts/descargar_series.py`

- [ ] **Step 1: Confirmar si `protestas_caba` ya tiene serie histórica**

```bash
grep -n "protestas_caba" scripts/descargar_series.py
```

Si ya existe (reutilizada de gestión), no duplicar — solo confirmar que
`POLITICA_DERIVADAS` también la referencia para el cinturón política.

- [ ] **Step 2: Agregar series para `cohesion_bloque_senado` y `adhesion_reformas_provincial`**

```python
def fetch_cohesion_bloque_senado_serie(anio_inicio: int = 2023) -> dict:
    """Backfill de cohesion_bloque_senado, mismo patrón que cohesion_bloque_serie."""
    serie = {}
    for anio in range(anio_inicio, datetime.now().year + 1):
        resultado = politica.fetch_cohesion_bloque_senado(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            serie[str(anio)] = resultado["valor"]
    return serie


def fetch_adhesion_reformas_provincial_serie() -> dict:
    """adhesion_reformas_provincial es un STOCK (adhesión es un evento único
    e irreversible por provincia, no una serie mensual suave) — un solo punto
    con el valor actual, no backfill año por año (no hay forma de reconstruir
    cuándo adhirió cada provincia sin una fuente con fecha de adhesión)."""
    resultado = politica.fetch_adhesion_reformas_provincial()
    if not resultado:
        return {}
    return {str(datetime.now().year): resultado["valor"]}
```

Registrar ambas en `POLITICA_DERIVADAS` junto a `fetch_cohesion_bloque_serie`
(Tarea 10 del plan anterior).

- [ ] **Step 3: Correr el backfill**

Run: `python scripts/descargar_series.py`
Expected: exit 0, series nuevas presentes en el archivo de históricos de política.

- [ ] **Step 4: Commit**

```bash
git add scripts/descargar_series.py data/politica/
git commit -m "feat(politica): backfill de cohesion_bloque_senado y adhesion_reformas_provincial"
```

---

### Task 8: ADR-0035

**Files:**
- Create: `docs/adr/0035-itcp-parametrica-politica.md`

- [ ] **Step 1: Escribir el ADR**

Seguir el formato de ADR-0013 (tabla Estado/Fecha/Ámbito, Contexto, Decisión,
Operacionalizaciones, Opciones descartadas, Consecuencias). Contenido mínimo
a incluir (ya redactado en el spec, `docs/superpowers/specs/2026-07-07-itcp-cinturon-politica-design.md` — usar como fuente):

- Contexto: cinturón política se puntuaba con promedio simple; 5 dimensiones
  ya descriptas en `docs/cinturon_politica.md` pero nunca pesadas.
- Decisión: pesos 30/25/20/15/10, sin doc CIGOB de respaldo (a diferencia de
  ITCM/ITCG/ITVC) — decisión editorial explícita justificada en el propio
  marco del proyecto ("capacidad de gobernar, NO popularidad").
- `cohesion_bloque` redefinido de "% alineado con posición oficial" a "índice
  de Rice" (cohesión interna) — la posición oficial no es un dato disponible.
- 3 indicadores nuevos y su alcance honesto: `cohesion_bloque_senado`
  (complementario, no reemplaza a Diputados), `adhesion_reformas_provincial`
  (adhesión fiscal puntual, no proxy de `gobernadores_alineamiento`),
  `protestas_caba` (reutilizado de gestión, lectura distinta: condición de
  gobernabilidad, no juicio sobre legitimidad de protestar).
- Bandas provisionales a recalibrar: las 4 nuevas/recalibradas.
- Opciones descartadas: compactar `poder_legislativo` en un compuesto (sin
  doc que lo exija, se mantiene plano); usar Senado o Presupuesto Abierto
  como proxy directo de `gobernadores_alineamiento` (construct-invalid,
  documentado en `manuales.json._meta`).

- [ ] **Step 2: Commit**

```bash
git add docs/adr/0035-itcp-parametrica-politica.md
git commit -m "docs(adr): ADR-0035 — paramétrica ITCP del cinturón política"
```

---

### Task 9: Reescribir `docs/cinturon_politica.md`

**Files:**
- Modify: `docs/cinturon_politica.md`

- [ ] **Step 1: Reescribir siguiendo el formato de `docs/cinturon_gestion.md`**

Leer primero `docs/cinturon_gestion.md` completo como plantilla de formato
(tabla de dimensiones y pesos, detalle por indicador, sección de ejecución,
notas de mantenimiento). Reemplazar en `docs/cinturon_politica.md`:
- La sección "Encuadre" para incluir la tabla de pesos de dimensión.
- Cada entrada de indicador para reflejar el estado real post-implementación
  (`cohesion_bloque` ya no es "carga manual", agregar `cohesion_bloque_senado`,
  `adhesion_reformas_provincial`, `protestas_caba`).
- El score actual del cinturón (correr `python scripts/politica.py` primero
  para tener el valor real de ITCP a citar).

- [ ] **Step 2: Commit**

```bash
git add docs/cinturon_politica.md
git commit -m "docs(politica): reescribe cinturon_politica.md reflejando la paramétrica ITCP"
```

---

### Task 10: Fichas metodológicas en la web

**Files:**
- Modify: `web/src/lib/fichas.ts`

- [ ] **Step 1: Leer las fichas existentes de `cohesion_bloque` y `gobernadores_alineamiento`**

```bash
grep -n "cohesion_bloque\|gobernadores_alineamiento" web/src/lib/fichas.ts
```

Usar la ficha existente de `cohesion_bloque` como plantilla de formato (misma
interfaz TS que las 55 fichas ya publicadas — sin números de ADR en el texto
público, per convención vigente).

- [ ] **Step 2: Actualizar la ficha de `cohesion_bloque`**

Actualizar el texto de metodología para reflejar el índice de Rice (dejar de
decir "% alineado con la posición oficial"; explicar en lenguaje llano qué es
cohesión de bloque y cómo se calcula, sin jerga de "índice de Rice" si el
estándar de las fichas es explicar en términos llanos — seguir el mismo
registro que usan las fichas de ITCM/ITCG ya publicadas).

- [ ] **Step 3: Agregar 3 fichas nuevas**

`cohesion_bloque_senado`, `adhesion_reformas_provincial`, `protestas_caba`
(esta última puede reusar/adaptar texto de la ficha ya existente en gestión
si la hay, ajustando la lectura: en política mide condición de gobernabilidad,
no premia/castiga la protesta).

- [ ] **Step 4: Verificar que el sitio renderiza sin errores**

```bash
cd web && npm run build
```
Expected: build exitoso, sin errores de TypeScript.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/fichas.ts
git commit -m "feat(web): fichas metodológicas para ITCP — cohesion_bloque actualizada + 3 nuevas"
```

---

## Self-Review

**Cobertura del spec:** Tarea 1 cubre dimensiones/bandas/`calcular_itcp()`.
Tareas 2-4 cubren los 3 indicadores nuevos. Tarea 5 cubre el reemplazo de
`calcular_score()`. Tareas 6-7 cubren `ajustes_itcp.json` y el backfill.
Tareas 8-10 cubren ADR, doc del cinturón y fichas web. Todo lo comprometido en
la sección "Sub-proyecto 2" del spec tiene tarea.

**Placeholders:** el nombre exacto del fetcher ACLED en `gestion.py` (Tarea 4)
y la estructura exacta de `fichas.ts` (Tarea 10) no estaban confirmados en el
spec — ambas tareas empiezan con un `grep`/lectura concreta para resolverlo
antes de escribir código, no con una instrucción vaga.

**Consistencia de tipos:** `DIMENSIONES_ITCP` en Tarea 1 usa exactamente las
mismas 12 claves de indicador que se fetchean en Tareas 2-5 y que se backfillean
en Tarea 7 (`cohesion_bloque`, `cohesion_bloque_senado`,
`adhesion_reformas_provincial`, `protestas_caba` + los 8 ya existentes).
`_paced_get` introducido en Tarea 2 es consumido tanto por
`_hcdn_votaciones_get` (retrocompatibilidad con el plan anterior) como por
`_descubrir_actas_senado`/`fetch_cohesion_bloque_senado`.
