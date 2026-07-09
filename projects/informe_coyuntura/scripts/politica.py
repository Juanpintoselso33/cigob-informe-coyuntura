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
  cohesion_bloque           — % cohesión (Rice) del bloque LLA en Diputados (scrape votaciones.hcdn.gob.ar, auto)
  cohesion_bloque_senado    — % cohesión (Rice) del bloque LLA en Senado (scrape senado.gob.ar, auto)
  alineamiento_senadores_prov — % votos de senadores no-LLA alineados con LLA, por provincia
                               (scrape senado.gob.ar, auto — reemplaza a gobernadores_alineamiento,
                               placeholder manual congelado desde 2026-04, ver manuales.json)
  veto_quorum               — % sesiones frustradas por falta de quórum (datos.hcdn.gob.ar CKAN, auto)
  comisiones_caidas         — % proyectos con dictamen que no llegan al recinto (datos.hcdn.gob.ar CKAN, auto)
  adhesion_reformas_provincial — % provincias adheridas al RIGI (MAGyP, auto)
  protestas_caba            — % var. eventos de protesta en CABA vs. base 2023 (ACLED, reutiliza gestion.py)

Nota: ICG UTDT removido (mide confianza ciudadana, no capacidad de gobernar con actores
políticos). Reemplazado por ratio_dnu según framework Luis Babino / reunión 12-may-2026.
IAF (Índice de Armonía Federal): iaf_transferencias captura cumplimiento fiscal federal
(Babino: Agregados de Poder). alineamiento_senadores_prov captura la dimensión territorial
(reemplaza a gobernadores_alineamiento, ver docstring de fetch_alineamiento_senadores_prov).
veto_quorum y comisiones_caidas capturan la eficacia legislativa de la oposición y el
bloqueo en comisiones — candidatos a fusionarse en índice compuesto legislativo.
"""
import sys
import io
import json
import re
import math
import calendar
import logging
import time
import requests
import urllib3
import pdfplumber
import gestion  # reutiliza el fetcher ACLED ya construido para protestas_caba (ADR-0017)
import itcp
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR     = Path(__file__).parent
PROJECT_DIR    = SCRIPT_DIR.parent
CACHE_PATH     = PROJECT_DIR / "output" / "cache" / "politica.json"
MANUALES_PATH  = PROJECT_DIR / "data" / "politica" / "manuales.json"
AJUSTES_ITCP_PATH = PROJECT_DIR / "data" / "politica" / "ajustes_itcp.json"
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR.parent / "votometro" / "web" / "votometro.html"  # fallback local

CINTURON              = "politica"
INDICADORES_ESPERADOS = [
    "votometro_ventaja_lla",
    "ratio_dnu",
    "movilizacion_cepa",
    "iaf_transferencias",
    "cohesion_bloque",
    "cohesion_bloque_senado",
    "eficacia_legislativa",
    "alineamiento_senadores_prov",
    "adhesion_reformas_provincial",
    "veto_quorum",
    "comisiones_caidas",
    "protestas_caba",
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

# HCDN Votaciones — votaciones.hcdn.gob.ar (portal de votaciones nominales)
HCDN_VOTACIONES_BASE = "https://votaciones.hcdn.gob.ar"
_HCDN_VOTACIONES_DELAY = 0.3  # segundos entre requests — evita el WAF F5 BIG-IP
                              # (confirmado: Como_voto corre a diario con este patrón)

# Senado — senado.gob.ar (portal de votaciones nominales, sitio distinto de HCDN)
SENADO_BASE = "https://www.senado.gob.ar"

# MAGyP — tabla de provincias adheridas al RIGI (Título VII, Ley 27.742)
MAGYP_RIGI_URL = "https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php"

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


# ── HCDN Votaciones session helpers ──────────────────────────────────────────────

def _hcdn_votaciones_session() -> requests.Session:
    """Sesión persistente con headers estables. El WAF del sitio devuelve 403
    ante ráfagas o headers que varían entre requests — reusar la misma sesión
    y no variar el UA es lo que lo evita."""
    s = requests.Session()
    s.headers.update(HTTP_HEADERS)
    return s


def _paced_get(session: requests.Session, base_url: str, path: str, **kwargs):
    """GET con pacing fijo y retry/backoff ante 403 (hasta 3 intentos).
    Generaliza el helper de HCDN para reusar sesión/pacing contra Senado.
    None si se agotan los reintentos o hay un error de red."""
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


def _hcdn_votaciones_get(session: requests.Session, path: str, **kwargs):
    return _paced_get(session, HCDN_VOTACIONES_BASE, path, **kwargs)


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
    el informe vigente. Reconoce dos patrones textuales, mutuamente
    excluyentes, cada uno con su propia escala de normalización:

      - "X casos por mes" / "promedio de X casos mensuales" -> TASA mensual
        (rama "m_mes", escala 0-CEPA_MAX_CASOS_MES).
      - "al menos N conflictos" / "se registraron N conflictos" -> CONTEO
        acumulado (rama "m_tot", escala 0-CEPA_MAX_CONFLICTOS_TOT).

    El dict devuelto incluye "rama": "m_mes" o "m_tot" para que el llamador
    pueda distinguir de forma explícita qué patrón matcheó (en vez de
    inspeccionar el string "metrica"). Devuelve None si el HTML no matchea
    ninguno de los dos patrones.

    Esta función NO sabe nada sobre qué informes deben excluirse de una
    serie histórica ni por qué -- eso es responsabilidad de cada llamador.
    En particular, un informe puede citar una cifra bajo un ancla temporal
    distinta a la del indicador vigente (p.ej. acumulado "desde enero 2024"
    en vez de "desde inicios del año en curso") y aun así matchear (rama
    m_mes o m_tot) si el patrón textual está presente en algún lugar del
    HTML -- ver docstring de fetch_cepa_movilizacion_serie() en
    descargar_series.py para el filtro real que excluye lecturas no
    comparables de la serie."""
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
                "cifra_cruda": cifra, "metrica": f"{cifra} casos/mes", "rama": "m_mes"}
    if m_tot:
        cifra = float(m_tot.group(1))
        return {"valor": round(min(100.0, (cifra / CEPA_MAX_CONFLICTOS_TOT) * 100.0), 1),
                "cifra_cruda": cifra, "metrica": f"{cifra} conflictos acumulados", "rama": "m_tot"}
    return None


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
        if cifra_info["rama"] != "m_tot":
            # Hallazgo de revisión final (2026-07-08): el informe más reciente
            # puede matchear la rama m_mes (tasa mensual, escala 0-80) en vez de
            # m_tot (conteo acumulado "desde inicios del año", escala 0-200) --
            # ver fetch_cepa_movilizacion_serie() para el caso real (informe
            # 748). Si eso pasara acá, BANDAS_ITCP["movilizacion_cepa"] (0-200)
            # puntuaría mal una tasa mensual. Se trata igual que "sin patrón":
            # degrada a cache en vez de publicar un valor en la escala
            # equivocada.
            raise ValueError(
                f"informe más reciente ({informe_url}) es rama={cifra_info['rama']!r}, "
                "no comparable con la escala m_tot ya publicada"
            )

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


# ── Protestas CABA (ACLED) — reutilizado de gestión ──────────────────────────

def fetch_protestas_caba() -> dict | None:
    """Reutiliza el fetcher ACLED ya construido en gestion.py (ADR-0017) para
    eventos de protesta en CABA. En gestión es CONTEXTO y no puntúa
    ('premiaría menos marchas'); en política SÍ puntúa como condición
    objetiva de gobernabilidad (nivel de conflicto social, Matus) — no como
    juicio sobre la legitimidad de protestar."""
    return gestion.fetch_protestas_caba()


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


def _es_media_sancion(movimiento: str) -> bool:
    """True si el movimiento es EXPLÍCITAMENTE una media sanción ('TEXTO DE
    LA MEDIA SANCION' y variantes) — aprobación de UNA cámara, no ley.
    Auditoría 2026-07-09: el q='SANCION' del CKAN también matchea esas filas
    (54 en el dataset) y las contaba como aprobación. Ningún número publicado
    llegó a estar mal (los únicos proyectos con SOLO media sanción son de
    legislaturas viejas, 2011), pero una media sanción futura de un proyecto
    recién enviado habría creado un 'aprobado' fantasma en eficacia_legislativa.
    Nota: el caso inverso (un 'CONSIDERACION Y SANCION' pelado de la cámara
    de ORIGEN también es solo media sanción) no se puede distinguir con las
    etiquetas del dataset — la Ley de Bases figura con esa misma etiqueta en
    su sanción DEFINITIVA (27-jun-2024) — así que solo se filtra lo
    inequívoco. comisiones_caidas NO usa este filtro a propósito: ahí la
    media sanción debe contar como 'avanzó' (mide varados en comisión, no
    leyes)."""
    return "MEDIA SANCION" in movimiento.upper()


def fetch_eficacia_legislativa() -> dict | None:
    """
    % proyectos ejecutivos aprobados en los últimos 12 meses.
    Identificación PE: EXP_DIPUTADOS o EXP_SENADO con patrón NNNN-PE-AAAA.
    Aprobación: aparición del PROYECTO_ID en movimientos-de-proyectos con
    MOVIMIENTO~'SANCION', excluyendo medias sanciones explícitas
    (_es_media_sancion).
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
            and not _es_media_sancion(str(r.get("MOVIMIENTO", "")))
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


# Bloque propio de LLA en Diputados/Senado. Excluye DELIBERADAMENTE aliados
# ambiguos (ej. "Fuerzas del Cielo - Espacio Liberal F.C.E.") que no son el
# bloque propio — sumarlos infla artificialmente la cohesión medida.
BLOQUES_LLA = {"la libertad avanza", "libertad avanza"}


def es_bloque_lla(nombre_bloque: str) -> bool:
    return nombre_bloque.strip().lower() in BLOQUES_LLA


_RE_REDIRECT_ACTA = re.compile(r"redirectActa\((\d+),\s*(\d+),\s*'([^']*)'\)")
_RE_DISPLAY_NONE   = re.compile(r"display\s*:\s*none")  # el sitio real usa "display: none" (con
                                                          # espacio) — confirmado vía snapshot de
                                                          # Wayback Machine (ene-2026) del listado
                                                          # real de votaciones.hcdn.gob.ar; el
                                                          # substring "display:none" sin espacio
                                                          # (supuesto inicial del fixture) no
                                                          # matchea contra la marca real.

def _descubrir_actas(session: requests.Session, anio: int):
    """POST a /votaciones/search por año -> [{id, slug, fecha}] de cada acta
    nominal encontrada. Cada fila del listado trae la fecha en un
    <span style="display: none">YYYYMMDD</span> y el link de detalle en un
    onclick=redirectActa(id, ?, 'slug') — se emparejan por fila (no por regex
    global sobre toda la página) para no desalinear fecha/acta.
    Nota: en el sitio real (confirmado vía snapshot archivado) el 3er argumento
    de redirectActa (slug) viene SIEMPRE vacío ('') — no es un bug de parseo,
    es el dato real; no asumir slugs legibles aguas abajo.
    None si el request en sí falló (distinto de 'sin actas ese año' = [])."""
    try:
        r = session.post(f"{HCDN_VOTACIONES_BASE}/votaciones/search",
                          data={"anoSearch": str(anio)}, timeout=HTTP_TIMEOUT)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    actas = []
    vistos = set()
    for fila in soup.select("tr"):
        m = _RE_REDIRECT_ACTA.search(str(fila))
        span_fecha = fila.find("span", style=lambda s: s and _RE_DISPLAY_NONE.search(s))
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


# DORMIDO desde 2026-07-09 (ADR-0040): _descubrir_actas/_url_acta/_parsear_acta
# construían el listado vía la SPA de votaciones.hcdn.gob.ar, bloqueada por
# anti-bot (ADR-0037) -- fetch_cohesion_bloque ya no los llama, usa el
# endpoint PDF directo (_descubrir_actas_diputados_pdf y compañía, más abajo).
# Se conservan sin borrar (mismo criterio que las bandas de
# gobernadores_alineamiento): si el endpoint PDF alguna vez deja de andar,
# es la referencia de qué ya se probó del lado de la SPA.
def _url_acta(acta: dict) -> str:
    """Construye la URL de detalle de una acta. En producción el slug viene
    VACÍO en el 100% de las filas observadas (Tarea 4, HTML real archivado
    2026-01-15) — con slug vacío la URL real es /votacion/{id} (confirmado
    contra un snapshot real de Wayback Machine, id 5840, status 200), NO
    /votacion//{id}. Se soporta igual el caso con slug por si la fuente
    cambia en el futuro."""
    if acta.get("slug"):
        return f"/votacion/{acta['slug']}/{acta['id']}"
    return f"/votacion/{acta['id']}"


def _parsear_acta(html: str) -> list[dict]:
    """Parsea el HTML de una acta de votación nominal de Diputados ->
    [{nombre, bloque, provincia, voto}]. Ignora filas sin las columnas esperadas.

    Estructura REAL confirmada (Tarea 5, snapshot real de Wayback Machine
    2026-01-15, acta id 5840, tabla #myTable con 257 filas = las 257 bancas
    de la Cámara): cada fila tiene 6 <td> — foto (índice 0, sin texto),
    DIPUTADO/nombre (1), BLOQUE (2), PROVINCIA (3), "¿CÓMO VOTÓ?"/voto (4,
    anidado en un <span class="label ..."> dentro de <center>, no como texto
    directo del <td>), "¿QUÉ DIJO?" (5). La fila de <thead> tiene solo <th>
    (0 <td>) y queda afuera sola por el chequeo de longitud.

    Esto reemplaza la suposición original de 3 columnas
    (`<td>nombre</td><td class="ocultar">bloque</td><td>voto</td>`) que
    JAMÁS fue observada en vivo para Diputados (era inferencia por analogía
    con Senado, donde sí se había confirmado esa estructura de 3 columnas, y
    con el scraper de terceros Como_voto) — el HTML real de Diputados no
    tiene ninguna clase "ocultar" (0 ocurrencias en la página real).
    get_text(strip=True) extrae igual el voto aunque esté anidado en <span>.

    parser="html.parser" (stdlib): lxml NO está en requirements.txt y
    rompería en CI (confirmado en la Tarea 4; mismo parser que ya usa
    fetch_cepa_movilizacion)."""
    soup = BeautifulSoup(html, "html.parser")
    filas = []
    for tr in soup.select("table tr"):
        celdas = tr.find_all("td")
        if len(celdas) < 5:
            continue
        nombre = celdas[1].get_text(strip=True)
        bloque = celdas[2].get_text(strip=True)
        provincia = celdas[3].get_text(strip=True)
        voto = celdas[4].get_text(strip=True).upper()
        if not nombre or not bloque:
            continue
        filas.append({"nombre": nombre, "bloque": bloque, "provincia": provincia, "voto": voto})
    return filas


# ── Diputados vía PDF directo (desbloquea ADR-0037, ver ADR-0040) ────────────
#
# votaciones.hcdn.gob.ar/pdf/acta/{id} sirve el PDF de cada acta SIN pasar
# por la SPA bloqueada -- verificado en vivo 2026-07-09: HTTP 200 directo,
# sin JS, sin anti-bot. El id es un contador GLOBAL secuencial (no por
# período): actas consecutivas de una misma sesión tienen ids consecutivos
# (confirmado: 5955-5959 son 5 votaciones de la sesión del 24-jun-2026); no
# hay listado público de ids↔fecha, así que el rango se descubre caminando
# el propio endpoint.
_DIPUTADOS_ACTA_PDF_PATH = "/pdf/acta/{id}"
_DIPUTADOS_VOTOS_VALIDOS = {"AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE"}
_DIPUTADOS_UMBRAL_COLUMNA = 15.0   # puntos pdfplumber: separa columnas (~50-120pt) de palabras dentro de una columna (~2pt)


def _parsear_acta_diputados_pdf(contenido: bytes) -> list[dict]:
    """Parsea el PDF de una acta de votación nominal de Diputados (endpoint
    directo) -> [{nombre, bloque, provincia, voto}].

    El PDF no tiene una tabla con bordes que pdfplumber pueda detectar como
    tal (extract_tables() solo encuentra el bloque de metadata/encabezado,
    no la lista de votantes) -- se agrupan palabras por fila (mismo `top`,
    redondeado a 1 decimal) y se cortan en columnas nuevas donde el hueco
    horizontal entre palabras supera _DIPUTADOS_UMBRAL_COLUMNA (~2pt dentro
    de una columna -- "GUILLERMO CESAR", "Union Civica Radical" -- vs.
    50-120pt entre columnas, confirmado en vivo contra el acta 5959).

    El título decorativo ("Honorable Cámara...") y la fila de encabezados de
    columna vienen con cada CARÁCTER duplicado (fuente en negrita simulada
    del generador de PDF) -- no se intenta arreglar eso, esas filas no
    forman 4 columnas limpias y quedan afuera solas. La línea de metadata
    repetida en cada página ("Acta Nº... Fecha:... Hora:...") SÍ arma 4
    columnas por casualidad -- se filtra exigiendo que la última columna sea
    un voto válido (_DIPUTADOS_VOTOS_VALIDOS), no por posición de página."""
    filas = []
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina in pdf.pages:
            por_fila = {}
            for palabra in pagina.extract_words():
                clave = round(palabra["top"], 1)
                por_fila.setdefault(clave, []).append(palabra)
            for _, palabras in sorted(por_fila.items()):
                palabras.sort(key=lambda p: p["x0"])
                columnas, actual = [], [palabras[0]["text"]]
                for anterior, palabra in zip(palabras, palabras[1:]):
                    if palabra["x0"] - anterior["x1"] > _DIPUTADOS_UMBRAL_COLUMNA:
                        columnas.append(" ".join(actual))
                        actual = [palabra["text"]]
                    else:
                        actual.append(palabra["text"])
                columnas.append(" ".join(actual))
                if len(columnas) != 4:
                    continue
                nombre, bloque, provincia, voto = columnas
                voto = voto.upper()
                if voto not in _DIPUTADOS_VOTOS_VALIDOS:
                    continue
                filas.append({"nombre": nombre, "bloque": bloque, "provincia": provincia, "voto": voto})
    return filas


def _diputados_acta_fecha(contenido: bytes) -> datetime | None:
    """Extrae la fecha ('Fecha: DD/MM/YYYY') del encabezado de metadata del
    PDF de una acta -- esa línea extrae limpia (sin duplicado de carácter),
    a diferencia del título decorativo."""
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        texto = pdf.pages[0].extract_text() or ""
    m = re.search(r"Fecha:\s*(\d{2}/\d{2}/\d{4})", texto)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%d/%m/%Y")
    except ValueError:
        return None


def _diputados_acta_pdf(session: requests.Session, id_acta: int):
    """GET pausado del PDF de una acta puntual. None si no existe (404) o
    el request falló -- _paced_get ya distingue eso de un 403 (reintenta) y
    de un error de red (None)."""
    r = _paced_get(session, HCDN_VOTACIONES_BASE, _DIPUTADOS_ACTA_PDF_PATH.format(id=id_acta))
    return r.content if r is not None else None


# Caché PERMANENTE por acta (id -> {fecha, rice}): a diferencia de los
# stores "por año" de Senado/alineamiento (donde el año en curso se
# re-pide siempre porque pueden aparecer actas nuevas), acá el caché es a
# nivel de ACTA INDIVIDUAL -- una vez publicada, un acta nunca cambia de
# fecha ni de resultado, así que cachearla para siempre es seguro y barato.
# Sin este caché, cada corrida (live O backfill) volvía a descargar y
# parsear el mismo PDF de siempre -- hallazgo real 2026-07-09: sin caché,
# el backfill anual completo (4 años) tardó ~35 minutos extra en el
# pipeline; con caché, cada acta se descarga una sola vez en la vida del
# proyecto, sea cual sea cuántas veces se llame a fetch_cohesion_bloque o
# fetch_cohesion_bloque_diputados_actas_anio después.
DIPUTADOS_COHESION_CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "politica" / "cohesion_bloque_diputados_actas_cache.json"


def _cargar_cache_cohesion_diputados() -> dict:
    try:
        return json.loads(DIPUTADOS_COHESION_CACHE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def _guardar_cache_cohesion_diputados(cache: dict) -> None:
    DIPUTADOS_COHESION_CACHE_PATH.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _acta_diputados_cacheada(session: requests.Session, id_acta: int, cache: dict) -> dict | None:
    """{"fecha": datetime, "rice": float | None} de una acta, mirando
    primero `cache` (dict mutable id-str -> {"fecha": "YYYY-MM-DD", "rice":
    float | None}) antes de pedir red. Si no está cacheada, descarga+parsea
    y la agrega a `cache`, persistiendo a disco DE INMEDIATO (no al final
    del walk que la llama) -- un backfill completo camina cientos de ids a
    ~0,3s/request (varios minutos reales), y si se corta a mitad de camino
    (timeout de CI, corrida manual interrumpida) el trabajo ya hecho no
    puede perderse: la próxima corrida debe retomar desde donde quedó, no
    desde cero. Se cachea SIEMPRE que se pudo leer la fecha, con rice=None
    cuando el bloque LLA no aporta señal (empate o sin presentes), para que
    un walk repetido nunca vuelva a descargar la misma acta. None solo si
    la acta no existe (404, puede ser transitorio) o no se pudo extraer la
    fecha del PDF -- ninguno de esos dos casos se cachea."""
    clave = str(id_acta)
    if clave in cache:
        entrada = cache[clave]
        return {"fecha": datetime.strptime(entrada["fecha"], "%Y-%m-%d"), "rice": entrada["rice"]}
    contenido = _diputados_acta_pdf(session, id_acta)
    if contenido is None:
        return None
    fecha = _diputados_acta_fecha(contenido)
    if fecha is None:
        return None
    filas = _parsear_acta_diputados_pdf(contenido)
    afirm = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "AFIRMATIVO")
    neg = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "NEGATIVO")
    rice = indice_rice(afirm, neg)
    cache[clave] = {"fecha": fecha.strftime("%Y-%m-%d"), "rice": rice}
    _guardar_cache_cohesion_diputados(cache)
    return {"fecha": fecha, "rice": rice}


def _diputados_acta_id_maximo(session: requests.Session, desde_id: int = 5959) -> int | None:
    """Encuentra el id de acta más reciente disponible, caminando desde
    `desde_id` (semilla conocida: 5959 = 24-jun-2026, verificado en vivo
    2026-07-09). Si la semilla ya no existe (quedó vieja), retrocede de a
    50 hasta encontrar un id válido; desde ahí avanza de a uno hasta el
    primer 404. None solo si ni retrocediendo se encuentra ningún id válido
    (fallo real del endpoint, no "sin sesiones nuevas")."""
    actual = desde_id
    intentos = 0
    while actual > 0 and _diputados_acta_pdf(session, actual) is None:
        actual -= 50
        intentos += 1
        if intentos > 200:   # ~10000 ids de margen -- corta un loop patológico
            return None
    if actual <= 0:
        return None
    while _diputados_acta_pdf(session, actual + 1) is not None:
        actual += 1
    return actual


def fetch_cohesion_bloque_diputados_actas_anio(anio: int) -> list | None:
    """Detalle CRUDO de cohesión por acta de Diputados de TODO el año dado
    (sin recortar por ventana de días), vía el endpoint PDF directo --
    mismo shape que fetch_cohesion_bloque_senado_actas_anio (Senado):
    [{"fecha": "YYYY-MM-DD", "rice": float}, ...], una fila por acta con
    señal (votos del bloque LLA, no empatados). Existe para el backfill
    mensual (descargar_series.py) con el mismo patrón que Senado.

    A diferencia de Senado (que tiene un listado liviano por año), acá no
    hay forma de pedir "solo este año" -- camina hacia atrás desde el id
    más reciente HOY, así que llamar esta función para 2023..2026 en
    cualquier orden vuelve a caminar por los años ya vistos en llamadas
    anteriores. Eso es barato gracias a _acta_diputados_cacheada (caché
    PERMANENTE por acta, ver ahí) -- cada acta se descarga una sola vez,
    las siguientes veces que el walk la vuelve a pisar es solo un lookup
    de diccionario."""
    MARGEN_SALIDA = 5
    session = _hcdn_votaciones_session()
    id_maximo = _diputados_acta_id_maximo(session)
    if id_maximo is None:
        return None

    cache = _cargar_cache_cohesion_diputados()
    detalle = []
    fuera_de_anio_seguidas = 0
    id_actual = id_maximo
    while id_actual > 0 and fuera_de_anio_seguidas < MARGEN_SALIDA:
        entrada = _acta_diputados_cacheada(session, id_actual, cache)
        id_actual -= 1
        if entrada is None:
            continue   # acta inexistente o sin señal -- no cuenta como "fuera de año"
        if entrada["fecha"].year > anio:
            continue   # todavía viajando desde HOY hacia el año pedido -- no cuenta como salida
        if entrada["fecha"].year < anio:
            fuera_de_anio_seguidas += 1
            continue
        fuera_de_anio_seguidas = 0
        if entrada["rice"] is not None:
            detalle.append({"fecha": entrada["fecha"].strftime("%Y-%m-%d"), "rice": entrada["rice"]})

    return detalle


def fetch_cohesion_bloque(anio: int | None = None, dias_ventana: int = 90) -> dict | None:
    """Cohesión del bloque LLA en Diputados: índice de Rice promedio sobre
    las actas nominales divididas de los últimos `dias_ventana` días.

    Desde 2026-07-09 (ADR-0040) usa el endpoint PDF directo
    (votaciones.hcdn.gob.ar/pdf/acta/{id}), NO la SPA bloqueada por
    anti-bot (ADR-0037) que usaban _descubrir_actas/_url_acta/_parsear_acta
    (dormidas más arriba). No hay listado id↔fecha para este endpoint, así
    que camina hacia atrás desde el id más reciente descargando cada acta
    -- se corta a los MARGEN_SALIDA actas seguidas fuera de la ventana en
    vez de solo por fecha de la última, para tolerar algún id fuera de
    orden sin perder actas más viejas que sí caen en la ventana.

    `anio`/`dias_ventana=366` para backfill de un año pasado usan
    fetch_cohesion_bloque_diputados_actas_anio + descargar_series (mismo
    patrón que cohesion_bloque_senado) -- ESTA función solo sirve bien el
    caso live (año en curso, ventana de 90 días); para años pasados
    `_diputados_acta_id_maximo` seguiría ancladando al id de HOY, no al de
    fin de `anio`, así que no se soporta acá.

    Desde 2026-07-09 usa la caché permanente por acta
    (_acta_diputados_cacheada) en vez de descargar cada acta sin registro:
    en una corrida repetida (cron nocturno incluido) solo las actas nuevas
    desde la última corrida pagan una descarga real.

    Devuelve None SOLO si no se pudo determinar el id más reciente (el
    endpoint en sí falló) — 'sin votos en la ventana' (receso legislativo)
    es un resultado válido con valor=None pero corrida_exitosa_en seteado."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    id_maximo = _diputados_acta_id_maximo(session)
    if id_maximo is None:
        return None

    referencia = datetime.now() if anio == datetime.now().year else datetime(anio, 12, 31)
    limite = referencia - timedelta(days=dias_ventana)

    MARGEN_SALIDA = 5
    cache = _cargar_cache_cohesion_diputados()
    detalle = []
    fuera_de_ventana_seguidas = 0
    id_actual = id_maximo
    while id_actual > 0 and fuera_de_ventana_seguidas < MARGEN_SALIDA:
        entrada = _acta_diputados_cacheada(session, id_actual, cache)
        id_actual -= 1
        if entrada is None:
            continue   # hueco en la numeración o PDF ilegible -- no cuenta como "fuera de ventana"
        if entrada["fecha"] > referencia:
            continue
        if entrada["fecha"] < limite:
            fuera_de_ventana_seguidas += 1
            continue
        fuera_de_ventana_seguidas = 0
        if entrada["rice"] is not None:
            detalle.append((entrada["fecha"], entrada["rice"]))

    fecha_max = max((f for f, _ in detalle), default=None)
    return {
        "valor": round(sum(r for _, r in detalle) / len(detalle), 1) if detalle else None,
        "unidad": "% cohesión (índice de Rice), promedio actas divididas últimos 90 días",
        "fuente": "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
        "fecha_dato": fecha_max.strftime("%Y-%m-%d") if fecha_max else None,
        "n_actas": len(detalle),
        "corrida_exitosa_en": datetime.now().strftime("%Y-%m-%d"),
        "desactualizado": False,
    }


_RE_DETALLE_ACTA_SENADO = re.compile(r"/votaciones/detalleActa/(\d+)")


def _descubrir_actas_senado(session: requests.Session, anio: int):
    """POST a /votaciones/actas (listado con fecha en <span style="display:none">
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
    composición de bloque): nunca reemplaza al de Diputados.

    La ventana de recencia se ancla a HOY para el año en curso, y al 31 de
    diciembre de `anio` para años pasados (backfill) — mismo fix aplicado en
    fetch_cohesion_bloque (Tarea 6, cross-fix del plan de Diputados): anclar
    siempre a datetime.now() hacía el backfill de años pasados estructuralmente
    imposible (hallazgo de revisión de esta tarea, mismo bug reintroducido por
    el brief)."""
    anio = anio or datetime.now().year
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None

    referencia = datetime.now() if anio == datetime.now().year else datetime(anio, 12, 31)
    limite = referencia - timedelta(days=dias_ventana)
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
        "desactualizado": False,
    }


def fetch_cohesion_bloque_senado_actas_anio(anio: int) -> list | None:
    """Detalle CRUDO de cohesión por acta de TODO el año dado (sin recortar
    por ventana de días): [{"fecha": "YYYY-MM-DD", "rice": float}, ...], una
    fila por acta con señal (votos AFIRMATIVO/NEGATIVO del bloque LLA, no
    empatados). Mismo criterio que fetch_alineamiento_senadores_actas_anio:
    factorizada de fetch_cohesion_bloque_senado sin modificarla (el valor
    live sigue pidiendo solo las actas dentro de su ventana de 90 días) --
    existe para el backfill mensual (descargar_series.fetch_cohesion_bloque_senado_mensual),
    que necesita derivar múltiples ventanas de 90 días sin re-scrapear el
    Senado por cada mes."""
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None
    detalle = []
    for acta in actas:
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
        if r is None:
            continue
        filas = _parsear_acta(r.text)
        afirm = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "AFIRMATIVO")
        neg = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "NEGATIVO")
        rice = indice_rice(afirm, neg)
        if rice is not None:
            detalle.append({"fecha": acta["fecha"].strftime("%Y-%m-%d"), "rice": rice})
    return detalle


def _agregar_cohesion_ventana(detalle: list[dict], referencia: datetime, dias_ventana: int) -> dict | None:
    """Agrega el detalle crudo por acta (fetch_cohesion_bloque_senado_actas_anio,
    de uno o más años) dentro de la ventana [referencia − dias_ventana,
    referencia] y devuelve {valor, fecha_dato, n_actas}, o None si ninguna
    acta cae en la ventana. Misma fórmula que fetch_cohesion_bloque_senado
    (promedio simple del índice de Rice entre las actas con señal) --
    factorizada acá para que el backfill mensual pueda recalcularla para
    cada fin de mes sin duplicar la matemática ni volver a pedir red."""
    limite = referencia - timedelta(days=dias_ventana)
    indices = []
    fecha_max = None
    for fila in detalle:
        fecha = datetime.strptime(fila["fecha"], "%Y-%m-%d")
        if fecha < limite or fecha > referencia:
            continue
        indices.append(fila["rice"])
        fecha_max = fecha if fecha_max is None else max(fecha_max, fecha)
    if not indices:
        return None
    return {
        "valor": round(sum(indices) / len(indices), 1),
        "fecha_dato": fecha_max.strftime("%Y-%m-%d"),
        "n_actas": len(indices),
    }


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
        resultado_acta = _alineamiento_por_provincia(filas)
        for provincia, (coincide, total) in resultado_acta.items():
            c0, t0 = acumulado.get(provincia, (0, 0))
            acumulado[provincia] = (c0 + coincide, t0 + total)
        if resultado_acta:
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


def fetch_alineamiento_senadores_actas_anio(anio: int) -> list | None:
    """Detalle CRUDO de alineamiento por acta de TODO el año dado (sin
    recortar por ventana de días): [{"fecha": "YYYY-MM-DD", "provincias":
    {provincia: [coincide, total]}}, ...], una fila por acta CON señal (las
    actas donde el bloque LLA queda empatado no aportan fila).

    A diferencia de fetch_alineamiento_senadores_prov (que recorta por
    dias_ventana ANTES de pedir el detalle de cada acta, para no gastar
    requests de más en la corrida diaria), acá se pide el año COMPLETO de
    una sola pasada. Existe para el backfill mensual
    (descargar_series.fetch_alineamiento_senadores_prov_mensual): con el
    detalle crudo cacheado por año se pueden derivar múltiples ventanas de
    90 días (una por fin de mes) sin volver a scrapear el Senado por cada
    mes — sólo tiene sentido llamarla para años YA cerrados (o, para el año
    en curso, sabiendo que se re-pide entera en cada corrida, igual que el
    resto de las series de Senado)."""
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None
    detalle = []
    for acta in actas:
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
        if r is None:
            continue
        filas = _parsear_acta(r.text)
        resultado_acta = _alineamiento_por_provincia(filas)
        if resultado_acta:
            detalle.append({
                "fecha": acta["fecha"].strftime("%Y-%m-%d"),
                "provincias": {p: list(ct) for p, ct in resultado_acta.items()},
            })
    return detalle


def _agregar_alineamiento_ventana(detalle: list[dict], referencia: datetime, dias_ventana: int) -> dict | None:
    """Agrega el detalle crudo por acta (fetch_alineamiento_senadores_actas_anio,
    de uno o más años) dentro de la ventana [referencia − dias_ventana,
    referencia] y devuelve {valor, fecha_dato, n_provincias}, o None si
    ninguna acta cae en la ventana. Misma fórmula que
    fetch_alineamiento_senadores_prov (promedio simple entre provincias con
    señal) — factorizada acá para que el backfill mensual pueda recalcularla
    para cada fin de mes sin duplicar la matemática ni volver a pedir red."""
    limite = referencia - timedelta(days=dias_ventana)
    acumulado = {}
    fecha_max = None
    for fila in detalle:
        fecha = datetime.strptime(fila["fecha"], "%Y-%m-%d")
        if fecha < limite or fecha > referencia:
            continue
        for provincia, (coincide, total) in fila["provincias"].items():
            c0, t0 = acumulado.get(provincia, (0, 0))
            acumulado[provincia] = (c0 + coincide, t0 + total)
        fecha_max = fecha if fecha_max is None else max(fecha_max, fecha)
    if not acumulado:
        return None
    ratios_por_provincia = [c / t for c, t in acumulado.values() if t > 0]
    return {
        "valor": round(100 * sum(ratios_por_provincia) / len(ratios_por_provincia), 1),
        "fecha_dato": fecha_max.strftime("%Y-%m-%d"),
        "n_provincias": len(acumulado),
    }


# ── MAGyP — adhesión provincial al RIGI ──────────────────────────────────────

def _provincias_adheridas_rigi() -> set[str] | None:
    """{NOMBRE_PROVINCIA en mayúsculas, ...} de la tabla MAGyP de provincias
    adheridas al RIGI (Título VII, Ley 27.742), o None si el fetch falló.
    parser="html.parser" (stdlib, lxml no está en requirements.txt — ver
    Tarea 4 del plan de cohesion_bloque): el sitio fuente tiene un <tr> vacío
    malformado que con html.parser produce una fila SANTA CRUZ duplicada
    (confirmado en vivo en la investigación previa) — no requiere lxml para
    resolverlo, el resultado ya es un `set()`, así que agregar el mismo
    nombre dos veces es un no-op y el conteo final no se infla. Factorizada
    de fetch_adhesion_reformas_provincial (que solo necesita el conteo) para
    que descargar_series.fetch_adhesion_reformas_provincial_serie pueda
    cruzar los NOMBRES contra las fechas de adhesión investigadas a mano
    (data/politica/adhesion_reformas_provincial_fechas.json, ADR-0044)."""
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
    return provincias or None


def fetch_adhesion_reformas_provincial() -> dict | None:
    """% de provincias (sobre 24) adheridas formalmente al RIGI (Título VII,
    Ley 27.742) — tabla MAGyP. Mide adhesión FISCAL a un régimen puntual, NO
    alineamiento político general — no reemplaza a gobernadores_alineamiento."""
    provincias = _provincias_adheridas_rigi()
    if not provincias:
        return None
    return {
        "valor": round(len(provincias) / 24.0 * 100.0, 1),
        "unidad": "% de jurisdicciones (sobre 24) adheridas al RIGI",
        "fuente": "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
        "fecha_dato": datetime.now().strftime("%Y-%m-%d"),
        "n_provincias": len(provincias),
        "desactualizado": False,
    }


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


def _es_cohesion_legado(anterior: dict) -> bool:
    """True si `anterior` (el cache previo de cohesion_bloque) tiene la forma
    VIEJA del placeholder manual (pre-scraper) — {"valor": 78, "estado":
    "placeholder", "unidad": "% votos en línea con la posición oficial del
    bloque LLA", ...} — en vez de la forma NUEVA que devuelve
    fetch_cohesion_bloque (índice de Rice real).

    El discriminador es la AUSENCIA de "n_actas": es una clave que solo la
    corrida del scraper nuevo pone (junto con "corrida_exitosa_en"); el
    placeholder manual nunca la tuvo. Ambas formas son números 0-100 con
    significados totalmente distintos (78 = "% de diputados alineados con la
    posición oficial" vs. índice de Rice real) — sin este chequeo, un cache
    viejo se arrastraría para siempre como si fuera un dato de Rice genuino
    (hallazgo de revisión externa, ver commit)."""
    return "n_actas" not in anterior


def _valor_itcp(nombre: str, entry: dict):
    """Valor a puntuar en el ITCP para un indicador ya fresco/cacheado.

    protestas_caba es la ÚNICA excepción: puntúa sobre "var_vs_2023" (% de
    variación de eventos ACLED en CABA contra la base 2023), NO sobre "valor"
    (el conteo crudo de eventos acumulado 12 meses, que gestion.fetch_protestas_caba
    devuelve y que puede estar en cientos — ver docstring de itcp.BANDAS_ITCP).
    Cualquier otro indicador puntúa directo sobre su propio "valor"."""
    if nombre == "protestas_caba":
        return entry.get("var_vs_2023")
    return entry.get("valor")


def _resultado_utilizable(nombre: str, resultado: dict | None) -> bool:
    """True si el resultado de un fetcher tiene el valor que efectivamente se
    usa en el ITCP para `nombre` (vía _valor_itcp), no solo un "valor" crudo
    presente. Cierra un borde latente (auditoría 2026-07-08): protestas_caba
    puntúa sobre var_vs_2023; si var_vs_2023 fuera None con "valor" presente
    (base_2023 == 0), el indicador se contaría como fresco sin aportar
    realmente al índice. Para el resto de los indicadores es equivalente a
    `resultado.get("valor") is not None` (_valor_itcp devuelve "valor" directo)."""
    return resultado is not None and _valor_itcp(nombre, resultado) is not None


def _anotar_indicadores_itcp(indicadores: dict, resultado: dict | None) -> None:
    """Marca cada indicador con su rol en el ITCP: los del índice llevan
    puntaje, dimensión y peso efectivo; el resto queda como contexto (mismo
    patrón que gestion.anotar_indicadores para el ITCG). A diferencia del
    ITCG, el ITCP no tiene indicadores de contexto declarados todavía (los 12
    de itcp.BANDAS_ITCP puntúan todos) — `en_indice` cae a False solo si el
    indicador no está ni en el resultado ni en la tabla de bandas."""
    por_indicador = {}
    if resultado:
        for dkey, dim in resultado["dimensiones"].items():
            for ikey, info in dim["indicadores"].items():
                por_indicador[ikey] = {
                    "en_indice": True,
                    "dimension": dkey,
                    "puntaje_itcp": info["puntaje_aplicado"],
                    "puntaje_banda": info["puntaje_banda"],
                    "peso_efectivo": info["peso_efectivo"],
                }
    for nombre, ind in indicadores.items():
        if nombre in por_indicador:
            ind.update(por_indicador[nombre])
        else:
            ind["en_indice"] = nombre in itcp.BANDAS_ITCP  # del índice pero sin dato


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    cache_anterior         = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})

    frescos: dict = {}
    frescos_count = 0

    colectores = [
        ("votometro_ventaja_lla",         fetch_votometro),
        ("ratio_dnu",                     fetch_ratio_dnu),
        ("movilizacion_cepa",             fetch_cepa_movilizacion),
        ("iaf_transferencias",            fetch_iaf_transferencias),
        ("eficacia_legislativa",          fetch_eficacia_legislativa),
        ("veto_quorum",                   fetch_veto_quorum),
        ("comisiones_caidas",             fetch_comisiones_caidas),
        ("adhesion_reformas_provincial",  fetch_adhesion_reformas_provincial),
        ("protestas_caba",                fetch_protestas_caba),
    ]

    for nombre, fetcher in colectores:
        resultado = fetcher()
        if _resultado_utilizable(nombre, resultado):
            frescos[nombre] = resultado
            frescos_count += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    resultado_cohesion = fetch_cohesion_bloque()
    anterior_cohesion = indicadores_anteriores.get("cohesion_bloque")
    if anterior_cohesion is not None and _es_cohesion_legado(anterior_cohesion):
        # Cache heredado del viejo placeholder manual (78, "% votos alineados
        # con la posición oficial") — NO es un dato de Rice genuino, tratarlo
        # como ausente para no corromper el ITCP con un valor de significado
        # distinto (hallazgo de revisión externa).
        anterior_cohesion = None
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

    # alineamiento_senadores_prov comparte el mismo contrato de retorno que
    # cohesion_bloque_senado (misma sesión/descubrimiento de actas de Senado):
    # dict con "valor": None (no None a secas) cuando la corrida llegó al
    # sitio pero no hubo actas divididas en la ventana de recencia (receso
    # legislativo normal). Mismo bloque dedicado que cohesion_bloque_senado
    # en vez de la lista plana de colectores, para no marcar "desactualizado"
    # solo por ausencia de votos nuevos (reutiliza _cohesion_desactualizada,
    # que es un chequeo de staleness genérico, no específico de cohesión).
    resultado_alineamiento = fetch_alineamiento_senadores_prov()
    anterior_alineamiento = indicadores_anteriores.get("alineamiento_senadores_prov")
    if resultado_alineamiento is not None and resultado_alineamiento.get("valor") is not None:
        frescos["alineamiento_senadores_prov"] = resultado_alineamiento
        frescos_count += 1
    elif resultado_alineamiento is not None and anterior_alineamiento is not None:
        frescos["alineamiento_senadores_prov"] = {
            **anterior_alineamiento,
            "desactualizado": False,
            "corrida_exitosa_en": resultado_alineamiento["corrida_exitosa_en"],
        }
        frescos_count += 1
    elif anterior_alineamiento is not None:
        frescos["alineamiento_senadores_prov"] = {
            **anterior_alineamiento,
            "desactualizado": _cohesion_desactualizada(anterior_alineamiento, resultado_alineamiento),
        }

    ajustes = itcp.cargar_ajustes(AJUSTES_ITCP_PATH, datetime.now().strftime("%Y-%m"))
    valores = {}
    for nombre, entry in frescos.items():
        valor = _valor_itcp(nombre, entry)
        if valor is not None:
            valores[nombre] = valor
    resultado_itcp = itcp.calcular_itcp(valores, ajustes)
    score = itcp.tension_de_itcp(resultado_itcp["valor"]) if resultado_itcp else 5.0
    _anotar_indicadores_itcp(frescos, resultado_itcp)

    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "itcp":         resultado_itcp,
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
