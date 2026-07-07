"""
Colector Cinturón Político — CIGOB
Capital político según Carlos Matus: capacidad de gobernar (no popularidad).
Ejecutar desde projects/informe_coyuntura/: python scripts/politica.py

Indicadores:
  votometro_ventaja_lla     — Brecha LLA−PJ en intención de voto (Votómetro CIGOB, auto)
  ratio_dnu                 — DNUs / leyes sancionadas año corriente (InfoLeg, auto)
  movilizacion_cepa         — Conflictividad social CEPA 0–100 (scrape centrocepa.com.ar, auto)
  iaf_transferencias        — Variación real YoY transferencias federales RON (Hacienda, auto)
  eficacia_legislativa      — % proyectos PE aprobados, ventana 12m (datos.hcdn.gob.ar CKAN, auto)
  cohesion_bloque           — % cohesión del bloque LLA en Diputados (manual — votaciones CKAN congeladas en 2019)
  gobernadores_alineamiento — % gobernadores alineados con política nacional (manual — sin fuente estructurada)
  veto_quorum               — % sesiones frustradas por falta de quórum (datos.hcdn.gob.ar CKAN, auto)
  comisiones_caidas         — % proyectos con dictamen que no llegan al recinto (datos.hcdn.gob.ar CKAN, auto)

Nota: ICG UTDT removido (mide confianza ciudadana, no capacidad de gobernar con actores
políticos). Reemplazado por ratio_dnu según framework Luis Babino / reunión 12-may-2026.
IAF (Índice de Armonía Federal): iaf_transferencias captura cumplimiento fiscal federal
(Babino: Agregados de Poder). gobernadores_alineamiento captura la dimensión territorial.
veto_quorum y comisiones_caidas capturan la eficacia legislativa de la oposición y el
bloqueo en comisiones — candidatos a fusionarse en índice compuesto legislativo.
"""
import sys
import json
import re
import math
import calendar
import logging
import requests
import urllib3
from datetime import datetime, date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR     = Path(__file__).parent
PROJECT_DIR    = SCRIPT_DIR.parent
CACHE_PATH     = PROJECT_DIR / "output" / "cache" / "politica.json"
MANUALES_PATH  = PROJECT_DIR / "data" / "politica" / "manuales.json"
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR.parent / "votometro" / "web" / "votometro.html"  # fallback local

CINTURON              = "politica"
INDICADORES_ESPERADOS = [
    "votometro_ventaja_lla",
    "ratio_dnu",
    "movilizacion_cepa",
    "iaf_transferencias",
    "cohesion_bloque",
    "eficacia_legislativa",
    "gobernadores_alineamiento",
    "veto_quorum",
    "comisiones_caidas",
]

STALE_MANUAL_DAYS    = 45
STALE_VOTOMETRO_DAYS = 60
STALE_DNU_DAYS       = 30
STALE_IAF_DAYS       = 365  # dato anual — válido todo el año

HTTP_TIMEOUT = 20
HTTP_HEADERS = {"User-Agent": "CIGOB-InformeCoyuntura/1.0"}

CEPA_INFORMES_URL       = "https://centrocepa.com.ar/documentos/informes"
CEPA_MAX_CASOS_MES      = 80.0
CEPA_MAX_CONFLICTOS_TOT = 200.0

# InfoLeg — leyes y DNUs
# tipoNorma: 1=Ley, 2=Decreto. DNUs se identifican con texto="necesidad y urgencia"
INFOLEG_HOME    = "https://servicios.infoleg.gob.ar/infolegInternet/"
INFOLEG_BUSCAR  = "https://servicios.infoleg.gob.ar/infolegInternet/buscarNormas.do"

# Hacienda RON — transferencias federales históricas (serie anual 2003–año_actual)
RON_CSV_URL = "https://www.argentina.gob.ar/sites/default/files/serie_ron_2003_2025.csv"

# HCDN CKAN — datos.hcdn.gob.ar (open data portal de la Cámara de Diputados)
HCDN_CKAN            = "https://datos.hcdn.gob.ar/api/3/action/datastore_search"
HCDN_PROYECTOS_RID   = "22b2d52c-7a0e-426b-ac0a-a3326c388ba6"   # proyectos-parlamentarios
HCDN_MOVIMIENTOS_RID = "6108ea83-3f12-423c-a136-df1ae9cb2972"   # movimientos-de-proyectos
HCDN_SESIONES_RID    = "4ac70a51-a82d-428b-966a-0a203dd0a7e3"   # sesiones plenarias
HCDN_DICTAMENES_RID  = "59595a93-5a5e-4ba6-a3db-c1044e2f949e"   # dictámenes de comisión
_RE_PE_EXP           = re.compile(r"\d+-PE-\d{4}")

# IPC interanual diciembre (INDEC). Actualizar en enero de cada año.
# 2024: 117.06% acumulado anual. 2025: 38.3% acumulado anual (estimado previo a cierre).
IPC_ANUAL = {2024: 1.1706, 2025: 0.383}   # fallback dic-dic si la API INDEC falla

INDEC_SERIES_URL = "https://apis.datos.gob.ar/series/api/series/"
INDEC_IPC_INDICE = "148.3_INIVELNAL_DICI_M_26"   # IPC nivel general, índice (base dic-2016=100)


def _ipc_dicdic_indec() -> dict:
    """IPC dic-dic por año derivado de la serie ÍNDICE oficial de INDEC (sin hardcodear):
    {año: variación dic(año)/dic(año−1) − 1}. Confiable desde 2017 (base dic-2016=100)."""
    r = requests.get(INDEC_SERIES_URL,
                     params={"ids": INDEC_IPC_INDICE, "format": "json", "limit": 200, "sort": "desc"},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    dic = {}
    for fecha, val in r.json()["data"]:
        if val is not None and str(fecha)[5:7] == "12":
            dic[int(str(fecha)[:4])] = val
    return {y: dic[y] / dic[y - 1] - 1 for y in dic if y - 1 in dic}

logging.basicConfig(level=logging.WARNING, format="%(message)s")


# ── Cache helpers ─────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _warn(indicador: str, msg: str) -> None:
    print(f"[WARN] {CINTURON}.{indicador}: {msg}. Usando cache.")


def _days_old(fecha_str: str) -> int:
    try:
        fecha = date.fromisoformat(str(fecha_str)[:10])
        return (date.today() - fecha).days
    except Exception:
        return 999


# ── Votómetro parser ──────────────────────────────────────────────────────────

def _cargar_votometro_html() -> str:
    """HTML del Votómetro LIVE (cigob.github.io/Votometro, embebido en cigob.org).
    Cae al archivo local si la URL falla o no trae encuestasRaw."""
    try:
        r = requests.get(VOTOMETRO_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        if "encuestasRaw" in r.text:
            return r.text
        raise ValueError("encuestasRaw ausente en la respuesta del Votómetro live")
    except Exception as e:
        if VOTOMETRO_HTML.exists():
            _warn("votometro (URL live falló, uso archivo local)", str(e))
            return VOTOMETRO_HTML.read_text(encoding="utf-8")
        raise


def fetch_votometro() -> dict | None:
    """
    Parsea encuestasRaw del Votómetro CIGOB y calcula la brecha ponderada LLA−PJ.

    Filtros:
    - tipo='espacio' (porcentajes de espacio político, no candidatos individuales)
    - últimos STALE_VOTOMETRO_DAYS días desde la encuesta más reciente

    Peso = exp(−0.015 × días) × calidad_mult  donde A=3, B=2, C=1
    """
    try:
        html = _cargar_votometro_html()

        m = re.search(r"const\s+encuestasRaw\s*=\s*\[(.*?)\];", html, re.DOTALL)
        if not m:
            raise ValueError("No se encontró encuestasRaw en el HTML")

        raw_block = m.group(1)

        entries = []
        for obj in re.finditer(r"\{([^}]+)\}", raw_block):
            fields = {}
            for kv in re.finditer(r"(\w+)\s*:\s*'([^']*)'|(\w+)\s*:\s*([\d.]+)", obj.group(1)):
                if kv.group(1):
                    fields[kv.group(1)] = kv.group(2)
                else:
                    fields[kv.group(3)] = float(kv.group(4))
            if fields:
                entries.append(fields)

        espacios = [e for e in entries if str(e.get("tipo", "")).strip() == "espacio"]
        if not espacios:
            raise ValueError("Sin encuestas tipo='espacio' en Votómetro")

        fechas = []
        for e in espacios:
            try:
                fechas.append(date.fromisoformat(str(e["fecha"])[:10]))
            except Exception:
                pass
        if not fechas:
            raise ValueError("Sin fechas válidas en encuestas espacio")
        fecha_max = max(fechas)

        cutoff = (fecha_max - timedelta(days=STALE_VOTOMETRO_DAYS)).isoformat()
        recientes = [e for e in espacios if str(e.get("fecha", "")) >= cutoff]
        if not recientes:
            raise ValueError("Sin encuestas espacio recientes en ventana de tiempo")

        CALIDAD_MULT = {"A": 3.0, "B": 2.0, "C": 1.0}
        LAMBDA = 0.015

        suma_peso = 0.0
        suma_lla  = 0.0
        suma_pj   = 0.0

        for e in recientes:
            try:
                fecha_enc = date.fromisoformat(str(e["fecha"])[:10])
                dias = (date.today() - fecha_enc).days
                wT = math.exp(-LAMBDA * dias)
                cal = str(e.get("calidad", "B")).strip().upper()
                wC = CALIDAD_MULT.get(cal, 2.0)
                w  = wT * wC

                lla = float(e.get("LLA", 0))
                pj  = float(e.get("PJ", 0))

                suma_peso += w
                suma_lla  += w * lla
                suma_pj   += w * pj
            except Exception:
                continue

        if suma_peso == 0:
            raise ValueError("Suma de pesos = 0")

        lla_pond = round(suma_lla / suma_peso, 1)
        pj_pond  = round(suma_pj / suma_peso, 1)
        gap      = round(lla_pond - pj_pond, 1)

        return {
            "valor": gap,
            "lla_ponderado": lla_pond,
            "pj_ponderado": pj_pond,
            "n_encuestas": len(recientes),
            "unidad": "Puntos porcentuales",
            "fuente": "Votómetro CIGOB",
            "fecha_dato": str(fecha_max),
            "desactualizado": _days_old(str(fecha_max)) > STALE_VOTOMETRO_DAYS,
        }

    except Exception as e:
        _warn("votometro_ventaja_lla", str(e))
        return None


def votometro_serie_mensual() -> list:
    """Serie histórica mensual de la brecha LLA−PJ del Votómetro, reconstruida desde
    encuestasRaw (que trae todos los sondeos desde dic-2023). Para cada mes se aplica
    la MISMA ponderación que fetch_votometro (recencia exp(−0,015·días) × calidad,
    ventana de STALE_VOTOMETRO_DAYS anclada en el último sondeo del mes), evaluada al
    cierre del mes. Devuelve [(YYYY-MM, gap)] ascendente."""
    html = _cargar_votometro_html()
    m = re.search(r"const\s+encuestasRaw\s*=\s*\[(.*?)\];", html, re.DOTALL)
    if not m:
        raise ValueError("No se encontró encuestasRaw en el HTML")
    esp = []
    for obj in re.finditer(r"\{([^}]+)\}", m.group(1)):
        f = {}
        for kv in re.finditer(r"(\w+)\s*:\s*'([^']*)'|(\w+)\s*:\s*([\d.]+)", obj.group(1)):
            f[kv.group(1) or kv.group(3)] = kv.group(2) if kv.group(1) else float(kv.group(4))
        if f and str(f.get("tipo", "")).strip() == "espacio" and f.get("fecha"):
            esp.append(f)
    fechas = sorted(date.fromisoformat(str(e["fecha"])[:10]) for e in esp)
    if not fechas:
        raise ValueError("Sin encuestas tipo='espacio'")
    CAL = {"A": 3.0, "B": 2.0, "C": 1.0}; LAMBDA = 0.015

    def gap_al(asof: date):
        fmax = max((f for f in fechas if f <= asof), default=None)
        if not fmax:
            return None
        cutoff = fmax.toordinal() - STALE_VOTOMETRO_DAYS
        sw = sl = sp = 0.0
        for e in esp:
            fe = date.fromisoformat(str(e["fecha"])[:10])
            if fe > asof or fe.toordinal() < cutoff:
                continue
            w = math.exp(-LAMBDA * (asof - fe).days) * CAL.get(str(e.get("calidad", "B")).strip().upper(), 2.0)
            sw += w; sl += w * float(e.get("LLA", 0)); sp += w * float(e.get("PJ", 0))
        return round((sl - sp) / sw, 1) if sw else None

    out = []
    y, mo = fechas[0].year, fechas[0].month
    while (y, mo) <= (date.today().year, date.today().month):
        asof = min(date(y, mo, calendar.monthrange(y, mo)[1]), date.today())
        g = gap_al(asof)
        if g is not None:
            out.append((f"{y}-{mo:02d}", g))
        mo += 1
        if mo > 12:
            mo = 1; y += 1
    return out


# ── Ratio DNU ─────────────────────────────────────────────────────────────────

def _infoleg_session_count(session: requests.Session, action_url: str,
                            tipo: str, year: int, texto: str = "") -> int:
    """
    POST a InfoLeg buscarNormas.do dentro de una sesión activa.
    tipo: "1"=Ley, "2"=Decreto. DNUs se identifican con texto="necesidad y urgencia".
    """
    hasta = date.today().strftime("%d/%m/%Y") if year == date.today().year else f"31/12/{year}"
    post_data = {
        "tipoNorma": tipo,
        "numero": "",
        "anioSancion": "",
        "dependencia": "",
        "diaPubDesde": "01",
        "mesPubDesde": "01",
        "anioPubDesde": str(year),
        "diaPubHasta": hasta[:2],
        "mesPubHasta": hasta[3:5],
        "anioPubHasta": hasta[6:],
        "texto": texto,
    }
    r = session.post(action_url, data=post_data, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()

    m = re.search(r"Encontradas?[:\s]+(\d+)", r.text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    raise ValueError(f"Conteo no encontrado en InfoLeg (tipo={tipo}, texto={texto!r})")


def fetch_ratio_dnu() -> dict | None:
    """
    Ratio DNU = count(DNUs) / count(leyes sancionadas) — año corriente.
    Mayor ratio = mayor dependencia del decreto → debilidad legislativa y exposición judicial.
    Dimensión: capacidad legislativa del Ejecutivo (Luis Babino: Agregados de Poder).

    Fuente: servicios.infoleg.gob.ar
    - Leyes: tipoNorma=1 (Ley)
    - DNUs: tipoNorma=2 (Decreto) + texto="necesidad y urgencia"
    Requiere GET previo para obtener jsessionid del formulario.

    Score: ratio 0→0, 1.0→5, 2.0+→10  (formula: ratio × 5)
    Referencia 2026 (may): ~22 DNUs / 7 leyes = 3.14 → score 10 (tensionado)
    """
    try:
        year = date.today().year

        session = requests.Session()
        r_home = session.get(INFOLEG_HOME, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r_home.raise_for_status()

        action_m = re.search(r'action="(/infolegInternet/[^"]+)"', r_home.text)
        if not action_m:
            raise ValueError("No se encontró la URL del formulario InfoLeg")
        action_url = "https://servicios.infoleg.gob.ar" + action_m.group(1)

        leyes = _infoleg_session_count(session, action_url, "1", year)
        if leyes == 0:
            raise ValueError("0 leyes — posible fallo en búsqueda InfoLeg (tipoNorma=1)")

        dnus = _infoleg_session_count(session, action_url, "2", year, texto="necesidad y urgencia")

        ratio = round(dnus / leyes, 3)

        return {
            "valor": ratio,
            "dnu_count": dnus,
            "leyes_count": leyes,
            "periodo": str(year),
            "unidad": "DNUs por ley",
            "fuente": INFOLEG_HOME,
            "fecha_dato": str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("ratio_dnu", str(e))
        return None


# ── CEPA conflictividad ───────────────────────────────────────────────────────

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


# ── IAF — Índice de Armonía Federal (transferencias) ─────────────────────────

def fetch_iaf_transferencias() -> dict | None:
    """
    Variación real YoY de transferencias federales totales (RON Hacienda).
    Dimensión: armonía fiscal federal (Luis Babino: Agregados de Poder — IAF).

    Fuente: CSV anual Hacienda — columnas: ano;provincia;impuesto;regimen;monto
    Decimal en monto: coma (ej. 2787,1198 → 2787.1198).
    Se suman todos los montos del año de referencia (año_actual − 1) y año anterior.
    Deflactor: IPC_ANUAL[año_ref] (variación dic-dic INDEC).

    Score: +10% real growth→0, 0%→2.5, −10%→5, −20%→7.5, −30%+→10
    formula: min(10, max(0, (0.10 − var_real) × 25))
    """
    import csv
    import io
    try:
        year_ref = date.today().year - 1   # último año completo
        year_ant = date.today().year - 2   # año anterior para comparar

        r = requests.get(RON_CSV_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()

        reader = csv.reader(io.StringIO(r.text), delimiter=";")
        next(reader)  # saltar header

        tot: dict[int, float] = {year_ref: 0.0, year_ant: 0.0}
        for row in reader:
            if len(row) < 5:
                continue
            try:
                yr = int(row[0])
            except ValueError:
                continue
            if yr not in tot:
                continue
            try:
                tot[yr] += float(row[4].replace(",", "."))
            except ValueError:
                continue

        if tot[year_ref] == 0 or tot[year_ant] == 0:
            raise ValueError(f"Sin datos para {year_ref} o {year_ant} en RON CSV")

        var_nominal = (tot[year_ref] / tot[year_ant]) - 1.0
        ipc = None
        try:
            ipc = _ipc_dicdic_indec().get(year_ref)   # oficial INDEC, sin hardcodear
        except Exception as e:
            _warn("iaf_transferencias (IPC INDEC, uso fallback)", str(e))
        if ipc is None:
            ipc = IPC_ANUAL.get(year_ref)              # fallback al dic-dic hardcodeado
        if ipc is None:
            raise ValueError(
                f"IPC no disponible para {year_ref} (ni INDEC ni IPC_ANUAL)"
            )
        var_real = (1.0 + var_nominal) / (1.0 + ipc) - 1.0
        score_val = round(min(10.0, max(0.0, (0.10 - var_real) * 25.0)), 2)

        return {
            "valor": round(var_real * 100.0, 1),
            "var_nominal_pct": round(var_nominal * 100.0, 1),
            "total_ref_mm": round(tot[year_ref] / 1e6, 0),
            "total_ant_mm": round(tot[year_ant] / 1e6, 0),
            "periodo": f"{year_ref} vs {year_ant}",
            "ipc_aplicado_pct": round(ipc * 100.0, 1),
            "unidad": "% interanual real",
            "fuente": RON_CSV_URL,
            "fecha_dato": str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("iaf_transferencias", str(e))
        return None


# ── HCDN CKAN — eficacia legislativa ─────────────────────────────────────────

def _hcdn_paginate(resource_id: str, *, q: str = "") -> list[dict]:
    """Fetch all records from a CKAN datastore resource, handling pagination."""
    records: list[dict] = []
    offset = 0
    while True:
        params: dict = {"resource_id": resource_id, "limit": 500, "offset": offset}
        if q:
            params["q"] = q
        r = requests.get(HCDN_CKAN, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        result = r.json().get("result")
        if not result:
            raise ValueError(f"CKAN sin result para resource_id={resource_id[:8]}…")
        batch = result.get("records", [])
        records.extend(batch)
        if len(batch) < 500:
            break
        offset += 500
    return records


def fetch_eficacia_legislativa() -> dict | None:
    """
    % proyectos ejecutivos aprobados en los últimos 12 meses.
    Identificación PE: EXP_DIPUTADOS o EXP_SENADO con patrón NNNN-PE-AAAA.
    Aprobación: aparición del PROYECTO_ID en movimientos-de-proyectos con MOVIMIENTO~'SANCION'.
    Ventana: PUBLICACION_FECHA (proyectos) y FECHA (movimientos) >= hoy − 365 días.

    Fuente: datos.hcdn.gob.ar CKAN
      - proyectos-parlamentarios: 22b2d52c-7a0e-426b-ac0a-a3326c388ba6
      - movimientos-de-proyectos: 6108ea83-3f12-423c-a136-df1ae9cb2972

    Score: 70%→0, 35%→5, 0%→10  (formula: (70 − valor) / 7)
    """
    try:
        cutoff = (date.today() - timedelta(days=365)).isoformat()[:10]

        raw_pe = _hcdn_paginate(HCDN_PROYECTOS_RID, q="-PE-")
        pe_recientes: set[str] = {
            r["PROYECTO_ID"]
            for r in raw_pe
            if str(r.get("PUBLICACION_FECHA", ""))[:10] >= cutoff
            and (
                _RE_PE_EXP.search(r.get("EXP_DIPUTADOS", "") or "")
                or _RE_PE_EXP.search(r.get("EXP_SENADO", "") or "")
            )
        }
        if not pe_recientes:
            raise ValueError("Sin proyectos PE en los últimos 12 meses")

        raw_san = _hcdn_paginate(HCDN_MOVIMIENTOS_RID, q="SANCION")
        sancionados: set[str] = {
            r["PROYECTO_ID"]
            for r in raw_san
            if str(r.get("FECHA", ""))[:10] >= cutoff
        }

        aprobados = pe_recientes & sancionados
        total     = len(pe_recientes)
        count     = len(aprobados)
        pct       = round(count / total * 100.0, 1) if total else 0.0

        return {
            "valor":        pct,
            "aprobados_n":  count,
            "enviados_n":   total,
            "ventana_dias": 365,
            "unidad":       "% de proyectos",
            "fuente":       "datos.hcdn.gob.ar — proyectos-parlamentarios + movimientos-de-proyectos",
            "fecha_dato":   str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("eficacia_legislativa", str(e))
        return None


# ── HCDN CKAN — veto por quórum ──────────────────────────────────────────────

def fetch_veto_quorum() -> dict | None:
    """
    % sesiones plenarias (Diputados) frustradas por falta de quórum en el período corriente.
    Detección: REUNION_TIPO contiene "Fracasada" en dataset de sesiones HCDN.
    Período corriente: PERIODO_ID con prefijo HCDN{periodo_num} (144 = 2026).
    Fórmula período: 144 + (año_actual − 2026).

    Nota: sesiones que nunca abren ("desactivadas") NO aparecen en HCDN — solo
    sesiones formalmente iniciadas y luego fracasadas por quórum son registradas.

    Fuente: datos.hcdn.gob.ar CKAN — sesiones (4ac70a51-...)
    Score: 0%→0, 15%→5, 30%+→10  (formula: valor / 3)
    """
    try:
        periodo_num    = 144 + (date.today().year - 2026)
        periodo_prefix = f"HCDN{periodo_num}"

        # CKAN q= doesn't substring-match tokens like "HCDN144R02" → fetch by year, filter Python-side
        year = date.today().year
        raw_year = _hcdn_paginate(HCDN_SESIONES_RID, q=str(year))
        periodo_recs = [
            r for r in raw_year
            if str(r.get("PERIODO_ID", "")).startswith(periodo_prefix)
            and str(r.get("SESION_CAMARA", "")).upper() == "DIPUTADOS"
        ]

        fracasadas_n = sum(
            1 for r in periodo_recs
            if "fracasada" in str(r.get("REUNION_TIPO", "")).lower()
        )
        total_n = len(periodo_recs)

        pct = round(fracasadas_n / total_n * 100.0, 1) if total_n > 0 else 0.0

        return {
            "valor":        pct,
            "fracasadas_n": fracasadas_n,
            "total_n":      total_n,
            "periodo_id":   periodo_prefix,
            "unidad":       "% de sesiones",
            "fuente":       f"datos.hcdn.gob.ar CKAN — sesiones — período {periodo_num}",
            "fecha_dato":   str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("veto_quorum", str(e))
        return None


# ── HCDN CKAN — comisiones caídas ─────────────────────────────────────────────

def fetch_comisiones_caidas() -> dict | None:
    """
    % proyectos con dictamen 'Orden del Día' en los últimos 12 meses que no fueron sancionados.
    Identifica proyectos con dictamen listo para el recinto (OD) pero sin SANCION en movimientos.

    Si dictámenes incluye PROYECTO_ID → join directo a movimientos.
    Si solo incluye EXPEDIENTE → map a PROYECTO_ID vía proyectos-parlamentarios.

    Fuente: datos.hcdn.gob.ar CKAN
      - dictámenes:           59595a93-5a5e-4ba6-a3db-c1044e2f949e
      - movimientos-de-proyectos: 6108ea83-3f12-423c-a136-df1ae9cb2972
      - proyectos-parlamentarios: 22b2d52c-7a0e-426b-ac0a-a3326c388ba6 (si hace falta join)

    Score: 20%→0, 40%→5, 60%+→10  (formula: (valor − 20) / 4)
    """
    try:
        year   = date.today().year
        cutoff = (date.today() - timedelta(days=365)).isoformat()[:10]

        # Dictámenes: dos pasadas para cubrir la ventana de 12 meses
        raw_cur  = _hcdn_paginate(HCDN_DICTAMENES_RID, q=str(year))
        raw_prev = _hcdn_paginate(HCDN_DICTAMENES_RID, q=str(year - 1))
        all_dict = raw_cur + raw_prev

        # Python-side: FECHA >= cutoff AND TIPO contiene "orden" (Orden del Día)
        od_records = [
            r for r in all_dict
            if str(r.get("FECHA", ""))[:10] >= cutoff
            and "orden" in str(r.get("TIPO", "")).lower()
        ]

        if not od_records:
            muestra = list(all_dict[0].keys()) if all_dict else []
            raise ValueError(
                f"Sin dictámenes 'Orden del Día' en ventana 12m "
                f"({len(all_dict)} registros totales, campos: {muestra})"
            )

        # dictámenes.EXPEDIENTE = HCDN project ID (same format as movimientos.PROYECTO_ID)
        od_ids: set[str] = {
            str(r["EXPEDIENTE"]).strip()
            for r in od_records if r.get("EXPEDIENTE")
        }

        if not od_ids:
            raise ValueError("Sin EXPEDIENTE válidos en dictámenes OD")

        # Sancionados en la ventana
        raw_san = _hcdn_paginate(HCDN_MOVIMIENTOS_RID, q="SANCION")
        sancionados: set[str] = {
            str(r["PROYECTO_ID"]).strip()
            for r in raw_san
            if str(r.get("FECHA", ""))[:10] >= cutoff and r.get("PROYECTO_ID")
        }

        aprobados_n = len(od_ids & sancionados)
        total_n     = len(od_ids)
        caidas_n    = total_n - aprobados_n
        pct         = round(caidas_n / total_n * 100.0, 1) if total_n else 0.0

        return {
            "valor":        pct,
            "dictamen_n":   total_n,
            "aprobados_n":  aprobados_n,
            "caidas_n":     caidas_n,
            "ventana_dias": 365,
            "unidad":       "% de proyectos",
            "fuente":       "datos.hcdn.gob.ar — dictámenes + movimientos-de-proyectos",
            "fecha_dato":   str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("comisiones_caidas", str(e))
        return None


# ── Colectores manuales ───────────────────────────────────────────────────────

def load_manuales() -> dict:
    if not MANUALES_PATH.exists():
        return {}
    with open(MANUALES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data


def fetch_manual(nombre: str, stale_days: int = STALE_MANUAL_DAYS) -> dict | None:
    manuales = load_manuales()
    entry = manuales.get(nombre)
    if entry is None:
        _warn(nombre, f"No encontrado en {MANUALES_PATH}")
        return None
    if entry.get("valor") is None:
        _warn(nombre, "valor = null en manuales.json")
        return None

    dias = _days_old(str(entry.get("fecha_dato", "")))
    return {
        **entry,
        "desactualizado": dias > stale_days,
    }


# ── Score ─────────────────────────────────────────────────────────────────────

def indice_rice(afirmativos: int, negativos: int) -> float | None:
    """Índice de Rice de cohesión (0-100): |afirm-neg|/(afirm+neg) * 100.
    Ausentes/abstenciones ya excluidos por el caller (no forman parte de la
    votación dividida). None si no hubo votos afirmativos ni negativos del
    bloque en esa acta (no aporta información de cohesión)."""
    total = afirmativos + negativos
    if total == 0:
        return None
    return round(abs(afirmativos - negativos) / total * 100.0, 2)


def calcular_score(indicadores: dict) -> float:
    """
    Score 0–10: mayor = mayor tensión en capital político.
    Cada dimensión de Matus pesa igual (1/N disponibles).

    votometro_ventaja_lla (gap LLA−PJ en pp):
        +15pp→0, 0→5, −15pp→10
    ratio_dnu (DNUs / leyes, año corriente):
        0→0, 1.0→5, 2.0+→10
    movilizacion_cepa (índice 0–100):
        0→0, 50→5, 100→10
    iaf_transferencias (% variación real YoY):
        +10%→0, 0%→2.5, −10%→5, −20%→7.5, −30%+→10
    eficacia_legislativa (% 0–100):
        70%→0, 35%→5, 0%→10
    cohesion_bloque (% 0–100):
        95%→0, 60%→5, 25%→10
    gobernadores_alineamiento (% 0–100):
        80%→0, 40%→5, 0%→10
    veto_quorum (% sesiones frustradas por quórum):
        0%→0, 15%→5, 30%+→10
    comisiones_caidas (% proyectos con dictamen que no llegan al recinto):
        20%→0, 40%→5, 60%+→10
    """
    scores = []

    vot = indicadores.get("votometro_ventaja_lla", {}).get("valor")
    if vot is not None:
        scores.append(min(10.0, max(0.0, 5.0 - float(vot) / 3.0)))

    dnu = indicadores.get("ratio_dnu", {}).get("valor")
    if dnu is not None:
        scores.append(min(10.0, max(0.0, float(dnu) * 5.0)))

    cepa = indicadores.get("movilizacion_cepa", {}).get("valor")
    if cepa is not None:
        scores.append(min(10.0, max(0.0, float(cepa) / 10.0)))

    iaf = indicadores.get("iaf_transferencias", {}).get("valor")
    if iaf is not None:
        var_real = float(iaf) / 100.0
        scores.append(min(10.0, max(0.0, (0.10 - var_real) * 25.0)))

    efic = indicadores.get("eficacia_legislativa", {}).get("valor")
    if efic is not None:
        scores.append(min(10.0, max(0.0, (70.0 - float(efic)) / 7.0)))

    coh = indicadores.get("cohesion_bloque", {}).get("valor")
    if coh is not None:
        scores.append(min(10.0, max(0.0, (95.0 - float(coh)) / 7.0)))

    gob = indicadores.get("gobernadores_alineamiento", {}).get("valor")
    if gob is not None:
        scores.append(min(10.0, max(0.0, (80.0 - float(gob)) / 8.0)))

    veto = indicadores.get("veto_quorum", {}).get("valor")
    if veto is not None:
        scores.append(min(10.0, max(0.0, float(veto) / 3.0)))

    com = indicadores.get("comisiones_caidas", {}).get("valor")
    if com is not None:
        scores.append(min(10.0, max(0.0, (float(com) - 20.0) / 4.0)))

    return round(sum(scores) / len(scores), 1) if scores else 5.0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    cache_anterior         = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})

    frescos: dict = {}
    frescos_count = 0

    colectores = [
        ("votometro_ventaja_lla",       fetch_votometro),
        ("ratio_dnu",                   fetch_ratio_dnu),
        ("movilizacion_cepa",           fetch_cepa_movilizacion),
        ("iaf_transferencias",          fetch_iaf_transferencias),
        ("eficacia_legislativa",        fetch_eficacia_legislativa),
        ("cohesion_bloque",             lambda: fetch_manual("cohesion_bloque")),
        ("gobernadores_alineamiento",   lambda: fetch_manual("gobernadores_alineamiento")),
        ("veto_quorum",                 fetch_veto_quorum),
        ("comisiones_caidas",           fetch_comisiones_caidas),
    ]

    for nombre, fetcher in colectores:
        resultado = fetcher()
        if resultado is not None and resultado.get("valor") is not None:
            frescos[nombre] = resultado
            frescos_count += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    score   = calcular_score(frescos)
    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "indicadores":  frescos,
    }

    if frescos:
        save_cache(payload)
        total = len(INDICADORES_ESPERADOS)
        print(f"[OK] {CINTURON}: score={score} frescos={frescos_count}/{total}")

    if frescos_count == len(INDICADORES_ESPERADOS):
        sys.exit(0)
    elif frescos_count > 0:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
