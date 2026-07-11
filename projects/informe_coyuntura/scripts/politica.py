"""
Colector Cinturón Político — CIGOB
Capital político según Carlos Matus: capacidad de gobernar (no popularidad).
Ejecutar desde projects/informe_coyuntura/: python scripts/politica.py

Indicadores:
  votometro_ventaja_lla     — Brecha LLA−PJ en intención de voto (Votómetro CIGOB, auto)
  ratio_dnu                 — DNUs / leyes sancionadas año corriente (InfoLeg, auto)
  conflictividad_nacional   — % var. eventos de protesta y disturbios en TODO el país vs. base
                               2023 (ACLED, 12m completos; ADR-0052 — reemplaza a
                               movilizacion_cepa en la dimensión conflicto_social)
  movilizacion_cepa         — Conflictividad social CEPA 0–100 (scrape centrocepa.com.ar, auto).
                               SEGUIMIENTO INTERNO desde 2026-07-11 (ADR-0052): sin backfill
                               posible (CEPA publica desde fines de 2025) y con fórmula de
                               acumulado YTD no comparable mes a mes — queda como contraste
                               oculto del snapshot
  iaf_transferencias        — Variación real YoY transferencias federales RON (Hacienda, auto)
  eficacia_legislativa      — % proyectos PE aprobados, ventana 12m (datos.hcdn.gob.ar CKAN, auto)
  cohesion_bloque           — % cohesión (Rice) del bloque LLA, COMPUESTO bicameral desde
                               2026-07-10 (ADR-0048): Diputados 65% (scrape votaciones.hcdn.gob.ar)
                               + Senado 35% (scrape senado.gob.ar), renormalizado si falta una cámara
  rotacion_gabinete         — salidas de rango ministerial (JGM + ministros) acumuladas 12m
                               (registro curado data/politica/gabinete_salidas.json + detector
                               de alerta InfoLeg, semiauto — patrón privatizaciones del ITCG).
                               SEGUIMIENTO INTERNO desde 2026-07-10 (ADR-0048): no puntúa
                               y publicar.py lo oculta del snapshot; se sigue relevando
  alineamiento_senadores_prov — % votos de senadores no-LLA alineados con LLA, por provincia
                               (scrape senado.gob.ar, auto — reemplaza a gobernadores_alineamiento,
                               placeholder manual congelado desde 2026-04, ver manuales.json)
  veto_quorum               — % sesiones frustradas por falta de quórum (datos.hcdn.gob.ar CKAN, auto)
  comisiones_caidas         — % proyectos con dictamen que no llegan al recinto (datos.hcdn.gob.ar CKAN, auto)
  adhesion_reformas_provincial — % provincias adheridas al RIGI (MAGyP, auto)
  derrotas_legislativas     — derrotas del Ejecutivo en el recinto, 12m: vetos insistidos +
                               decretos rechazados bajo la ley 26.122 (InfoLeg + actas Senado, auto)
  protestas_caba            — % var. eventos de protesta en CABA vs. base 2023 (ACLED, reutiliza
                               gestion.py). SEGUIMIENTO INTERNO desde 2026-07-10 (ADR-0048): no
                               puntúa y publicar.py lo oculta del snapshot de política (la card
                               de gestión sigue siendo su lectura pública)

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
import unicodedata
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
# Registro versionado de derrotas legislativas (semilla verificada a mano +
# detección incremental de fetch_derrotas_legislativas) — está en el git add
# del cron (data-pipeline.yml): un caché que no se commitea no sobrevive a la
# corrida nocturna (lección 2026-07-09, ver CLAUDE.md).
DERROTAS_EVENTOS_PATH = PROJECT_DIR / "data" / "politica" / "derrotas_legislativas_eventos.json"
GABINETE_SALIDAS_PATH = PROJECT_DIR / "data" / "politica" / "gabinete_salidas.json"
GABINETE_DECRETOS_CACHE_PATH = PROJECT_DIR / "data" / "politica" / "gabinete_decretos_cache.json"
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR.parent / "votometro" / "web" / "votometro.html"  # fallback local

CINTURON              = "politica"
INDICADORES_ESPERADOS = [
    "votometro_ventaja_lla",
    "ratio_dnu",
    "conflictividad_nacional",
    "movilizacion_cepa",
    "iaf_transferencias",
    "cohesion_bloque",
    "rotacion_gabinete",
    "eficacia_legislativa",
    "alineamiento_senadores_prov",
    "adhesion_reformas_provincial",
    "veto_quorum",
    "comisiones_caidas",
    "derrotas_legislativas",
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


def _paced_get(session: requests.Session, base_url: str, path: str, aceptar_404: bool = False, **kwargs):
    """GET con pacing fijo y retry/backoff ante 403 (hasta 3 intentos).
    Generaliza el helper de HCDN para reusar sesión/pacing contra Senado.
    None si se agotan los reintentos o hay un error de red. Con
    `aceptar_404=True` un 404 devuelve la Response (para que el caller pueda
    distinguir "no existe" de un fallo transitorio -- lo necesita el walk de
    actas de Diputados, donde un hueco de id es normal pero un fallo de red
    no debe congelarse como hueco)."""
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
        if r.status_code == 404 and aceptar_404:
            return r
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
    ('premiaría menos marchas'); en política fue indicador del ITCP hasta
    ADR-0048 (revisión editorial: "no pertinente en este cinturón") — sigue
    relevándose como seguimiento interno oculto del snapshot."""
    return gestion.fetch_protestas_caba()


# ── Conflictividad social nacional (ACLED, país entero) ──────────────────────

STALE_CONFLICTIVIDAD_DAYS = 30   # el agregado ACLED es semanal con rezago corto


def fetch_conflictividad_nacional() -> dict | None:
    """
    Conflictividad social nacional (ADR-0052): eventos de protesta y
    disturbios (Protests+Riots, ACLED) en TODO el país, acumulados en 12
    meses completos, expresados como % de variación contra el total 2023
    (la base del mandato). Reemplaza a movilizacion_cepa como el indicador
    puntuante de la dimensión conflicto_social del ITCP.

    "valor" ES la variación % (puntúa directo sobre BANDAS_ITCP, sin el
    caso especial que necesitaba protestas_caba, que exponía el conteo
    crudo). El conteo y la base quedan en el detalle (acum_12m,
    eventos_2023).

    El último mes del archivo se excluye si está parcial (la semana final
    no llega a fin de mes — el corte semanal + rezago de carga de ACLED lo
    dejan incompleto) — mismo criterio que gestion.fetch_protestas_caba.
    La serie usable arranca en dic-2023 (primera ventana 12m íntegramente
    comparable con la base); la cobertura ACLED pre-2020 NO es confiable
    (2019 promedia 102 eventos/mes vs 240 de 2020 — artefacto de expansión
    de cobertura, ver ADR-0052) y no se usa ni para calibrar ni para el
    gráfico público.
    """
    try:
        store = gestion.actualizar_protestas_caba()
        if store is None and gestion.PROTESTAS_STORE_PATH.exists():
            store = json.loads(gestion.PROTESTAS_STORE_PATH.read_text(encoding="utf-8"))
        if not store or "mensual_nacional" not in store:
            raise ValueError("store ACLED sin serie nacional (¿corrida vieja sin ADR-0052?)")
        mensual = store["mensual_nacional"]
        hasta = store.get("_meta", {}).get("hasta_semana", "")
        yms = sorted(mensual)
        if hasta and yms and hasta[:7] == yms[-1]:
            import calendar as _cal
            a, m = int(hasta[:4]), int(hasta[5:7])
            if int(hasta[8:10]) < _cal.monthrange(a, m)[1]:
                yms = yms[:-1]
        if len(yms) < 12:
            raise ValueError("serie ACLED nacional demasiado corta")
        ult12 = sum(mensual[ym] for ym in yms[-12:])
        base_2023 = sum(v for ym, v in mensual.items() if ym.startswith("2023"))
        if not base_2023:
            raise ValueError("store ACLED sin base 2023")
        var = round((ult12 / base_2023 - 1.0) * 100.0, 1)
        return {
            "valor":          var,
            "acum_12m":       ult12,
            "eventos_2023":   base_2023,
            "unidad":         "% vs 2023",
            "fuente":         "ACLED — agregado semanal por provincia (acleddata.com)",
            "fecha_dato":     f"{yms[-1]}-01",
            "desactualizado": bool(hasta) and _days_old(str(hasta)) > STALE_CONFLICTIVIDAD_DAYS,
            "detalle_txt": (f"{ult12} eventos de protesta y disturbios en el país en 12m "
                            f"(hasta {yms[-1]}) vs {base_2023} en todo 2023 "
                            + f"({var:+.1f}%)".replace(".", ",")
                            + " — cuenta marchas, concentraciones y disturbios de ACLED en "
                              "las 24 jurisdicciones; CABA es ~9% del total del país"),
        }
    except Exception as e:
        _warn("conflictividad_nacional", str(e))
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
    OJO: ambas fechas dentro de la MISMA ventana ⇒ el techo alcanzable del %
    está estructuralmente deprimido (un proyecto recién enviado casi nunca
    llegó a sancionarse aún) — las bandas del ITCP están calibradas contra la
    serie real de ESTA métrica, no contra tasas de aprobación de manual
    (ADR-0050).

    Fuente: datos.hcdn.gob.ar CKAN
      - proyectos-parlamentarios: 22b2d52c-7a0e-426b-ac0a-a3326c388ba6
      - movimientos-de-proyectos: 6108ea83-3f12-423c-a136-df1ae9cb2972
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


# Sentinelas del walk de actas de Diputados: un 404 genuino es un hueco de
# id (tolerable, la numeración puede saltearse) -- un fallo transitorio (red,
# 403 agotado, 5xx) NO es un hueco, y el backfill anual no debe congelar un
# año como "cerrado" si alguna acta falló por esto (quedaría un agujero
# permanente en la serie histórica y en la reconstrucción del ITCP).
_ACTA_NO_EXISTE = object()
_ACTA_FALLO = object()


def _diputados_acta_pdf(session: requests.Session, id_acta: int):
    """GET pausado del PDF de una acta puntual. Devuelve los bytes del PDF,
    `_ACTA_NO_EXISTE` si el servidor respondió 404 (hueco de id genuino), o
    `_ACTA_FALLO` si el request falló de forma transitoria (error de red,
    403 agotado, 5xx) -- los callers que cachean por año necesitan la
    distinción para no congelar un fallo como si fuera un hueco."""
    r = _paced_get(session, HCDN_VOTACIONES_BASE, _DIPUTADOS_ACTA_PDF_PATH.format(id=id_acta),
                   aceptar_404=True)
    if r is None:
        return _ACTA_FALLO
    if r.status_code == 404:
        return _ACTA_NO_EXISTE
    return r.content


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
    un walk repetido nunca vuelva a descargar la misma acta. None si la
    acta no existe (404, hueco de id genuino) o no se pudo extraer la fecha
    del PDF; `_ACTA_FALLO` si la descarga falló de forma transitoria (red,
    403 agotado) -- el backfill anual usa la distinción para no cachear un
    año con agujeros. Ninguno de esos casos se cachea."""
    clave = str(id_acta)
    if clave in cache:
        entrada = cache[clave]
        return {"fecha": datetime.strptime(entrada["fecha"], "%Y-%m-%d"), "rice": entrada["rice"]}
    contenido = _diputados_acta_pdf(session, id_acta)
    if contenido is _ACTA_FALLO:
        return _ACTA_FALLO
    if contenido is _ACTA_NO_EXISTE or contenido is None:
        # None: tolerancia defensiva (el contrato actual de
        # _diputados_acta_pdf ya no lo produce) -- se trata como hueco.
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


# El avance de _diputados_acta_id_maximo tolera huecos de numeración: la
# numeración real de actas NO es contigua — 101 huecos internos en el caché
# 4694..5959, con anchos de hasta 202 ids (4897→5100; luego 72, 35, 34, 33)
# y verificado EN VIVO 2026-07-11 que esos rangos devuelven 404 real, no un
# PDF sin fecha. "Primer 404 = final" perdía toda acta nueva publicada
# después de un hueco. El margen dobla el hueco máximo observado; el costo
# (~450 probeos pacientes al agotar la búsqueda) se paga UNA vez por proceso
# gracias a la memoización de abajo.
_MARGEN_HUECOS_ID = 450
_TOPE_AVANCE_ID = 2000

# Memo por PROCESO del id máximo descubierto: politica.py (card live) y
# descargar_series.py (4 backfills anuales) llaman al descubrimiento varias
# veces por corrida — el máximo no cambia dentro de un mismo proceso, y sin
# memo el probeo terminal de ~450 requests se pagaría por cada llamada. Solo
# se memoiza un resultado exitoso (int): un None (fallo transitorio) debe
# reintentar en la próxima llamada.
_ID_MAXIMO_MEMO: dict = {}

# Persistencia del descubrimiento por DÍA: el cron corre politica.py y
# descargar_series.py como PROCESOS separados en el mismo job, así que el
# memo de proceso no evita pagar dos veces el probeo terminal (~450 requests
# ≈ 2-3 min cada uno) — y el job ya roza su timeout (corridas reales de
# 19m32s/20m2s contra una cota de 20). Solo se persiste un descubrimiento
# EXITOSO y con fecha: al día siguiente se re-descubre (la numeración
# avanza), y un None o una exploración parcial nunca se persisten.
DIPUTADOS_ID_MAXIMO_STORE = Path(__file__).resolve().parents[1] / "data" / "politica" / "id_maximo_diputados.json"


def _hoy_buenos_aires() -> str:
    """Fecha calendario de referencia del proyecto (ART, UTC-3 fijo, sin
    horario de verano) como YYYY-MM-DD. El runner del cron vive en UTC: con
    datetime.now() a secas, un workflow_dispatch entre 00:00 y 02:59 UTC
    (todavía el día ANTERIOR en Argentina) sellaría el store con la fecha
    UTC nueva y el cron de las 03:00 UTC reutilizaría ese máximo sin
    redescubrir (hallazgo de octava pasada de revisión). Fallback a la hora
    local de la máquina si la base de zonas horarias no está disponible
    (Windows sin el paquete tzdata)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _diputados_acta_id_maximo(session: requests.Session, desde_id: int = 5959) -> int | None:
    """Encuentra el id de acta más reciente disponible, caminando desde
    `desde_id` (semilla conocida: 5959 = 24-jun-2026, verificado en vivo
    2026-07-09). Si la semilla ya no existe (quedó vieja), retrocede de a
    50 hasta encontrar un id válido; desde ahí avanza de a uno tolerando
    hasta _MARGEN_HUECOS_ID ids consecutivos sin acta (la numeración real
    tiene huecos, ver arriba) antes de dar por encontrado el máximo.

    None si ni retrocediendo se encuentra un id válido, si CUALQUIER probeo
    falla de forma transitoria (_ACTA_FALLO: con un fallo en el medio no se
    puede saber dónde termina la numeración, y un máximo subestimado haría
    que el walk anual cachee un año sin sus actas de arriba), o si el avance
    supera _TOPE_AVANCE_ID ids nuevos (endpoint patológico que responde 200
    a cualquier id).

    El punto de partida efectivo es el MAYOR entre `desde_id` (semilla
    estática de respaldo) y el id más alto ya presente en el caché por acta:
    así el arranque, el probeo y su tope acompañan el crecimiento real de la
    numeración. Con la semilla fija sola, cada corrida re-descargaba todos
    los ids posteriores a la semilla y, con el paso de las sesiones, el
    flujo normal habría alcanzado el tope y devuelto None para siempre
    (hallazgo de cuarta pasada de revisión).

    Caso extremo documentado: si la numeración avanzara más de
    _TOPE_AVANCE_ID ids sin que ninguna corrida lo registre (colector caído
    por meses), el descubrimiento devolvería None con WARN y haría falta
    subir la semilla estática a mano."""
    if "valor" in _ID_MAXIMO_MEMO:
        return _ID_MAXIMO_MEMO["valor"]
    hoy_str = _hoy_buenos_aires()
    try:
        store = json.loads(DIPUTADOS_ID_MAXIMO_STORE.read_text(encoding="utf-8-sig"))
        if store.get("descubierto") == hoy_str and isinstance(store.get("maximo"), int):
            # Descubrimiento de HOY hecho por otro proceso de la misma
            # corrida (o una corrida manual previa del día): se reusa. Las
            # actas se publican con rezago, así que congelar el máximo por
            # un día calendario no pierde nada en la práctica.
            _ID_MAXIMO_MEMO["valor"] = store["maximo"]
            return store["maximo"]
    except (OSError, json.JSONDecodeError):
        pass
    cache = _cargar_cache_cohesion_diputados()
    ultimo_conocido = max((int(k) for k in cache if str(k).isdigit()), default=0)
    arranques = [max(desde_id, ultimo_conocido)]
    if arranques[0] > desde_id:
        # Respaldo: el máximo cacheado no se valida contra nada, así que una
        # entrada corrupta/manual con un id inverosímilmente alto agotaría el
        # retroceso sin tocar el rango real. En ese caso se reintenta UNA vez
        # desde la semilla estática, en vez de devolver None para siempre
        # (el caché persistente impediría la recuperación automática).
        arranques.append(desde_id)
    actual = 0
    for arranque in arranques:
        actual = arranque
        intentos = 0
        while actual > 0:
            contenido = _diputados_acta_pdf(session, actual)
            if contenido is _ACTA_FALLO:
                return None
            if isinstance(contenido, bytes):
                break
            actual -= 50
            intentos += 1
            if intentos > 200:   # ~10000 ids de margen -- corta un loop patológico
                actual = 0
                break
        if actual > 0:
            break
    if actual <= 0:
        return None

    maximo = actual
    sonda = actual
    huecos_seguidos = 0
    while huecos_seguidos < _MARGEN_HUECOS_ID:
        sonda += 1
        if sonda - actual > _TOPE_AVANCE_ID:
            print(f"  [WARN] _diputados_acta_id_maximo: más de {_TOPE_AVANCE_ID} ids nuevos "
                  f"desde {actual} -- sospechoso, no se determina el máximo")
            return None
        contenido = _diputados_acta_pdf(session, sonda)
        if contenido is _ACTA_FALLO:
            return None
        if isinstance(contenido, bytes):
            maximo = sonda
            huecos_seguidos = 0
        else:
            huecos_seguidos += 1
    _ID_MAXIMO_MEMO["valor"] = maximo
    try:
        DIPUTADOS_ID_MAXIMO_STORE.parent.mkdir(parents=True, exist_ok=True)
        DIPUTADOS_ID_MAXIMO_STORE.write_text(json.dumps(
            {"maximo": maximo, "sondeado_hasta": sonda, "descubierto": hoy_str},
            indent=2), encoding="utf-8")
    except OSError:
        pass   # persistencia best-effort: el memo del proceso igual sirve
    return maximo


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
    de diccionario.

    Si la descarga de ALGUNA acta falla de forma transitoria (_ACTA_FALLO,
    distinto de un hueco de id genuino), devuelve None (detalle incompleto):
    el caller cachea años cerrados como inmutables y un año con agujeros
    contaminaría la serie histórica para siempre. El caché por acta igual
    retiene lo ya descargado, así que la corrida siguiente solo paga las
    actas que faltan."""
    MARGEN_SALIDA = 5
    session = _hcdn_votaciones_session()
    id_maximo = _diputados_acta_id_maximo(session)
    if id_maximo is None:
        return None

    cache = _cargar_cache_cohesion_diputados()
    detalle = []
    fallidas = 0
    fuera_de_anio_seguidas = 0
    id_actual = id_maximo
    while id_actual > 0 and fuera_de_anio_seguidas < MARGEN_SALIDA:
        entrada = _acta_diputados_cacheada(session, id_actual, cache)
        id_actual -= 1
        if entrada is _ACTA_FALLO:
            # fallo transitorio: el acta existe pero no se pudo leer AHORA.
            # No se puede saber de qué año es, así que el resultado completo
            # queda incompleto -- se termina el walk igual (para aprovechar
            # el caché por acta de lo que sí se pudo leer) pero se devuelve
            # None: el caller NO debe congelar este año con un agujero.
            fallidas += 1
            continue
        if entrada is None:
            continue   # hueco de id genuino (404) o sin fecha -- no cuenta como "fuera de año"
        if entrada["fecha"].year > anio:
            continue   # todavía viajando desde HOY hacia el año pedido -- no cuenta como salida
        if entrada["fecha"].year < anio:
            fuera_de_anio_seguidas += 1
            continue
        fuera_de_anio_seguidas = 0
        if entrada["rice"] is not None:
            detalle.append({"fecha": entrada["fecha"].strftime("%Y-%m-%d"), "rice": entrada["rice"]})

    if fallidas:
        print(f"  [WARN] cohesion_bloque_diputados_actas_anio {anio}: "
              f"{fallidas} actas con descarga fallida -- detalle incompleto, no se devuelve")
        return None
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

    # Referencia SIEMPRE a medianoche: el backfill mensual ancla sus ventanas
    # a medianoche del fin de mes, y con la hora del día incluida una acta
    # fechada exactamente `dias_ventana` días atrás quedaba fuera de la card
    # pero dentro de la serie (borde inconsistente entre las dos vistas).
    hoy = datetime.now()
    referencia = (datetime(hoy.year, hoy.month, hoy.day)
                  if anio == hoy.year else datetime(anio, 12, 31))
    limite = referencia - timedelta(days=dias_ventana)

    MARGEN_SALIDA = 5
    cache = _cargar_cache_cohesion_diputados()
    detalle = []
    fuera_de_ventana_seguidas = 0
    id_actual = id_maximo
    while id_actual > 0 and fuera_de_ventana_seguidas < MARGEN_SALIDA:
        entrada = _acta_diputados_cacheada(session, id_actual, cache)
        id_actual -= 1
        if entrada is None or entrada is _ACTA_FALLO:
            # hueco en la numeración, PDF ilegible o fallo transitorio -- el
            # valor live es best-effort (se recalcula entero cada corrida,
            # no se congela), así que acá el fallo solo se saltea.
            continue
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

    # Referencia SIEMPRE a medianoche: el backfill mensual ancla sus ventanas
    # a medianoche del fin de mes, y con la hora del día incluida una acta
    # fechada exactamente `dias_ventana` días atrás quedaba fuera de la card
    # pero dentro de la serie (borde inconsistente entre las dos vistas).
    hoy = datetime.now()
    referencia = (datetime(hoy.year, hoy.month, hoy.day)
                  if anio == hoy.year else datetime(anio, 12, 31))
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
    Senado por cada mes.

    Si el detalle de ALGUNA acta del listado falla, devuelve None (detalle
    incompleto): el caller cachea años cerrados como inmutables y un año
    con agujeros contaminaría la serie histórica para siempre."""
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None
    detalle = []
    fallidas = 0
    for acta in actas:
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
        if r is None:
            # Cada acta viene del listado oficial del año: su detalle DEBE
            # existir, así que esto es un fallo transitorio, no un hueco.
            fallidas += 1
            continue
        filas = _parsear_acta(r.text)
        afirm = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "AFIRMATIVO")
        neg = sum(1 for f in filas if es_bloque_lla(f["bloque"]) and f["voto"] == "NEGATIVO")
        rice = indice_rice(afirm, neg)
        if rice is not None:
            detalle.append({"fecha": acta["fecha"].strftime("%Y-%m-%d"), "rice": rice})
    if fallidas:
        print(f"  [WARN] cohesion_bloque_senado_actas_anio {anio}: "
              f"{fallidas} actas con detalle fallido -- detalle incompleto, no se devuelve")
        return None
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

    # Referencia SIEMPRE a medianoche: el backfill mensual ancla sus ventanas
    # a medianoche del fin de mes, y con la hora del día incluida una acta
    # fechada exactamente `dias_ventana` días atrás quedaba fuera de la card
    # pero dentro de la serie (borde inconsistente entre las dos vistas).
    hoy = datetime.now()
    referencia = (datetime(hoy.year, hoy.month, hoy.day)
                  if anio == hoy.year else datetime(anio, 12, 31))
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
    resto de las series de Senado).

    Si el detalle de ALGUNA acta del listado falla, devuelve None (detalle
    incompleto): el caller cachea años cerrados como inmutables y un año
    con agujeros contaminaría la serie histórica para siempre."""
    session = _hcdn_votaciones_session()
    actas = _descubrir_actas_senado(session, anio)
    if actas is None:
        return None
    detalle = []
    fallidas = 0
    for acta in actas:
        r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
        if r is None:
            # Cada acta viene del listado oficial del año: su detalle DEBE
            # existir, así que esto es un fallo transitorio, no un hueco.
            fallidas += 1
            continue
        filas = _parsear_acta(r.text)
        resultado_acta = _alineamiento_por_provincia(filas)
        if resultado_acta:
            detalle.append({
                "fecha": acta["fecha"].strftime("%Y-%m-%d"),
                "provincias": {p: list(ct) for p, ct in resultado_acta.items()},
            })
    if fallidas:
        print(f"  [WARN] alineamiento_senadores_actas_anio {anio}: "
              f"{fallidas} actas con detalle fallido -- detalle incompleto, no se devuelve")
        return None
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


# ── Derrotas legislativas del Ejecutivo (vetos insistidos + decretos caídos) ──
#
# Indicador de conteo absoluto en ventana móvil de 12 meses (ADR-0046): cuántas
# veces el Congreso le volteó una norma al Ejecutivo en el recinto. Dos familias
# de eventos, las dos únicas derrotas legislativas TERMINALES del régimen:
#   (a) veto insistido: ambas cámaras insisten con 2/3 (art. 83 CN) y la ley se
#       promulga pese al veto — se detecta vía InfoLeg (el proyecto vetado
#       aparece publicado como Ley con fecha POSTERIOR al decreto de veto);
#   (b) decreto rechazado: una cámara rechaza un DNU/decreto delegado bajo la
#       ley 26.122 — se detecta vía las actas del Senado (título con la fórmula
#       estable "en los términos de la ley 26.122"; en esas actas se vota la
#       VALIDEZ del decreto, así que gana NEGATIVO = rechazo, verificado contra
#       los 8 casos reales 2024-2025).
# Cada norma cuenta UNA vez, fechada en el mes de la derrota consumada
# (insistencia de la segunda cámara / primer rechazo en recinto). El estado
# vive en DERROTAS_EVENTOS_PATH (semilla histórica verificada a mano +
# detección incremental); la serie mensual se deriva determinísticamente del
# registro en descargar_series.fetch_derrotas_legislativas_mensual().
#
# Limitación declarada (ficha): la detección automática de decretos mira solo
# el Senado — un rechazo que ocurra primero en Diputados se registra recién
# con el voto del Senado (o a mano en el registro); en los 32 meses de la
# semilla eso habría corrido la fecha de los 5 decretos de ago-2025 apenas
# dos semanas, sin cambiar ningún conteo mensual publicado salvo el de agosto.

_DERROTAS_FRASES_VETO = (
    # Frases EXACTAS (entre comillas dobles: sin comillas InfoLeg hace OR de
    # palabras y devuelve miles de resultados) que cubren las 3 variantes de
    # sumario observadas en los 10 vetos reales dic-2023→jul-2026, con 0
    # falsos positivos y 0 falsos negativos (verificado en vivo 2026-07-09).
    '"observase en su totalidad"',
    '"observa en su totalidad"',
    '"promulgacion parcial"',
)
_RE_VERNORMA = re.compile(r"verNorma\.do\?(?:[^\"']*?&)?id=(\d+)")
_RE_DECRETO_ITEM = re.compile(r"Decreto\s+(\d+)\s*/\s*(\d{4})", re.IGNORECASE)
_RE_PROYECTO_LEY = re.compile(r"\b(2[5-9])\.?(\d{3})\b")
# Número de decreto en el título de un acta del Senado ("… Nº 340/25 …"). El
# prefijo Nº/N° es obligatorio a propósito: sin él matchearía el expediente
# ("PE-44/25-DC") que acompaña al título en el listado.
_RE_DECRETO_TITULO = re.compile(r"N[º°]\s*(\d+)\s*/\s*(\d{2,4})")
_MESES_INFOLEG = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
                  "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
_RE_FECHA_INFOLEG = re.compile(r"(\d{1,2})-([a-z]{3})-(\d{4})", re.IGNORECASE)
_DERROTAS_PAUSA_INFOLEG = 1.5   # segundos entre POSTs a InfoLeg (mismo pacing
                                # probado en vivo sin bloqueo, 2026-07-09)


def _cargar_derrotas_registro() -> dict | None:
    """Registro de eventos (DERROTAS_EVENTOS_PATH) o None si falta/ilegible.
    utf-8-sig: tolera el BOM de editores/PowerShell de Windows (mismo criterio
    que cargar_ajustes)."""
    try:
        registro = json.loads(DERROTAS_EVENTOS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(registro, dict) or "vetos" not in registro or "decretos" not in registro:
        return None
    return registro


def _guardar_derrotas_registro(registro: dict) -> None:
    DERROTAS_EVENTOS_PATH.write_text(
        json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")


def _infoleg_abrir_sesion() -> tuple:
    """(session, action_url) para postear a buscarNormas.do — misma mecánica
    de sesión que fetch_ratio_dnu (GET al home para el jsessionid + action URL
    del formulario)."""
    session = requests.Session()
    r = session.get(INFOLEG_HOME, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    m = re.search(r'action="(/infolegInternet/[^"]+)"', r.text)
    if not m:
        raise ValueError("No se encontró la URL del formulario InfoLeg")
    return session, "https://servicios.infoleg.gob.ar" + m.group(1)


def _infoleg_buscar(session: requests.Session, action_url: str, *, tipo: str,
                    texto: str = "", numero: str = "",
                    desde: date | None = None, hasta: date | None = None) -> str:
    """POST a buscarNormas.do dentro de la sesión y devuelve el HTML del
    listado. Valida que la página sea un resultado real (con conteo
    "Encontradas: N" o el texto de cero resultados) — cualquier otra cosa es
    un fallo de la fuente, no "0 vetos". Pacing fijo antes de cada POST."""
    time.sleep(_DERROTAS_PAUSA_INFOLEG)
    data = {
        "tipoNorma": tipo,
        "numero": numero,
        "anioSancion": "",
        "dependencia": "",
        "diaPubDesde": f"{desde.day:02d}" if desde else "",
        "mesPubDesde": f"{desde.month:02d}" if desde else "",
        "anioPubDesde": str(desde.year) if desde else "",
        "diaPubHasta": f"{hasta.day:02d}" if hasta else "",
        "mesPubHasta": f"{hasta.month:02d}" if hasta else "",
        "anioPubHasta": str(hasta.year) if hasta else "",
        "texto": texto,
    }
    r = session.post(action_url, data=data, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    if "Encontradas" not in r.text and "No se encontraron normas" not in r.text:
        raise ValueError(f"respuesta InfoLeg sin listado (tipo={tipo}, texto={texto!r}, numero={numero!r})")
    return r.text


def _fecha_infoleg(texto: str) -> str | None:
    """'12-sep-2025' (formato del listado InfoLeg) → '2025-09-12'."""
    m = _RE_FECHA_INFOLEG.search(texto)
    if not m:
        return None
    mes = _MESES_INFOLEG.get(m.group(2).lower())
    if not mes:
        return None
    return f"{m.group(3)}-{mes:02d}-{int(m.group(1)):02d}"


def _parsear_listado_infoleg(html: str) -> list[dict]:
    """Filas del listado de resultados de buscarNormas.do:
    [{infoleg_id, norma, fecha_pub, sumario}]. Cada resultado es un <tr> con 3
    <td> (número/dependencia con link a verNorma.do, fecha de publicación,
    descripción); el link "Ver Norma y Textos Resaltados" repite el id en la
    misma fila y se deduplica. Página sin resultados → [] (sin error: la
    validación de que la página es un listado real vive en _infoleg_buscar)."""
    soup = BeautifulSoup(html, "html.parser")
    items, vistos = [], set()
    for fila in soup.select("tr"):
        link = fila.find("a", href=_RE_VERNORMA)
        if link is None:
            continue
        m = _RE_VERNORMA.search(link["href"])
        celdas = fila.find_all("td")
        if not m or len(celdas) < 3:
            continue
        iid = m.group(1)
        if iid in vistos:
            continue
        vistos.add(iid)
        items.append({
            "infoleg_id": iid,
            "norma": re.sub(r"\s+", " ", celdas[0].get_text(" ", strip=True)),
            "fecha_pub": _fecha_infoleg(celdas[1].get_text(" ", strip=True)),
            "sumario": re.sub(r"\s+", " ", celdas[2].get_text(" ", strip=True)),
        })
    return items


def _proyectos_de_sumario(sumario: str) -> list[str]:
    """Números de proyecto de ley del sumario de un decreto de veto,
    normalizados con punto de miles ("27794"/"27.794" → "27.794"). Soporta el
    caso multiproyecto (el decreto 534/2025 vetó tres leyes de una vez)."""
    return sorted({f"{m.group(1)}.{m.group(2)}" for m in _RE_PROYECTO_LEY.finditer(sumario)})


def _derrotas_detectar_vetos(session, action_url, registro: dict) -> None:
    """Detecta decretos de veto (observación total/parcial) nuevos vía las 3
    frases exactas y los agrega al registro con insistencia_completa=null.
    Muta `registro` en memoria; el caller persiste al final si todo salió bien."""
    conocidos = {v["proyecto"] for v in registro["vetos"]}
    for frase in _DERROTAS_FRASES_VETO:
        html = _infoleg_buscar(session, action_url, tipo="2", texto=frase,
                               desde=date(2023, 12, 1), hasta=date.today())
        for item in _parsear_listado_infoleg(html):
            m = _RE_DECRETO_ITEM.search(item["norma"])
            proyectos = _proyectos_de_sumario(item["sumario"])
            if not m or not item["fecha_pub"] or not proyectos:
                continue
            decreto = f"{m.group(1)}/{m.group(2)}"
            es_parcial = "PROMULGACION PARCIAL" in item["sumario"].upper()
            for proyecto in proyectos:
                if proyecto in conocidos:
                    continue
                conocidos.add(proyecto)
                registro["vetos"].append({
                    "proyecto": proyecto,
                    "tema": item["sumario"][:200],
                    "decreto": decreto,
                    "infoleg_id_decreto": int(item["infoleg_id"]),
                    "fecha_veto": item["fecha_pub"],
                    "tipo": "parcial" if es_parcial else "total",
                    "insistencia_completa": None,
                    "fuente_insistencia": None,
                    "detalle": "Detectado automáticamente en InfoLeg.",
                })


def _derrotas_detectar_insistencias(session, action_url, registro: dict) -> None:
    """Verifica si algún veto aún no insistido flipeó: el proyecto vetado
    aparece publicado como Ley en InfoLeg con fecha POSTERIOR al decreto de
    veto (una ley publicada el MISMO día es la promulgación parcial del propio
    decreto, no una insistencia — caso real 27.739). Se re-chequean TODOS los
    vetos sin insistencia, estén o no en ventana: media insistencia pendiente
    (27.790/27.794) no caduca y puede completarse en cualquier momento; el
    evento nuevo se fecharía en el mes del flip, no en el del veto. La fecha
    usada es la de publicación en el B.O. (proxy de la insistencia de la
    segunda cámara: rezago observado 18-19 días, mismo mes en los 3 casos
    reales de 2025 — limitación declarada en la ficha)."""
    for veto in registro["vetos"]:
        if veto.get("insistencia_completa"):
            continue   # inmutable: una insistencia consumada no se des-consuma
        numero = veto["proyecto"].replace(".", "")
        html = _infoleg_buscar(session, action_url, tipo="1", numero=numero)
        for item in _parsear_listado_infoleg(html):
            if item["fecha_pub"] and item["fecha_pub"] > veto["fecha_veto"]:
                veto["insistencia_completa"] = item["fecha_pub"]
                veto["fuente_insistencia"] = ("fecha de publicación en el B.O. de la ley "
                                              "insistida (InfoLeg, detección automática)")
                break


def _actas_senado_26122(session: requests.Session, anio: int):
    """[{id, fecha, titulo}] de las actas del Senado del año cuyo título
    contiene la fórmula estable "en los términos de la ley 26.122" (presente
    en los 8 tratamientos reales de decretos 2024-2025 y ausente en los falsos
    amigos: mociones de orden, el decreto simple 681/25, la reforma de la
    propia ley). Mismo POST/parseo de filas que _descubrir_actas_senado, pero
    conservando el texto de la fila (el título de la votación).
    None si el request falló (distinto de 'sin actas con match' = [])."""
    r = _paced_post(session, SENADO_BASE, "/votaciones/actas",
                    data={"busqueda_actas[anio]": str(anio)})
    if r is None:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    actas, vistos = [], set()
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
        titulo = re.sub(r"\s+", " ", fila.get_text(" ", strip=True))
        # el texto de la fila arrastra la fecha oculta y el bloque "Ver
        # Expedientes ..." del listado — se recorta lo segundo para guardar
        # un título legible (la fecha oculta no molesta al filtro)
        titulo = titulo.split("Ver Expedientes")[0].strip()
        if "26.122" not in titulo:
            continue
        vistos.add(id_acta)
        actas.append({"id": id_acta, "fecha": fecha, "titulo": titulo})
    return actas


def _clave_decreto_de_titulo(titulo: str) -> str | None:
    """'… Decreto … Nº 340/25 …' → '340/2025' (clave normalizada del registro).
    None si el título no trae un número con prefijo Nº/N° (se avisa y se deja
    para revisión manual — no se adivina)."""
    m = _RE_DECRETO_TITULO.search(titulo)
    if not m:
        return None
    numero, anio = m.group(1), m.group(2)
    if len(anio) == 2:
        anio = f"20{anio}"
    return f"{int(numero)}/{anio}"


def _tipo_decreto_de_titulo(titulo: str) -> str:
    t = titulo.lower()
    if "facultades delegadas" in t:
        return "delegado"
    if "necesidad" in t and "urgencia" in t:
        return "DNU"
    return "decreto"


def _derrotas_detectar_decretos(registro: dict) -> None:
    """Detecta tratamientos nuevos de decretos bajo la ley 26.122 en el recinto
    del Senado (año en curso + anterior; las actas ya procesadas quedan en
    actas_senado_vistas y no se re-piden). En estas actas se vota la VALIDEZ
    del decreto: gana NEGATIVO = rechazo (dirección verificada contra los 8
    casos reales 2024-2025; una votación sin votos A/N registrados es un acta
    anulada y se ignora). Decretos anteriores a 2023 (la bicameral a veces
    trata decretos viejos de gestiones anteriores, caso 829/19 en 2024) quedan
    fuera de alcance. Muta `registro`; el caller persiste al final."""
    session = _hcdn_votaciones_session()
    vistos = registro.setdefault("actas_senado_vistas", {})
    hoy = date.today()
    for anio in sorted({hoy.year - 1, hoy.year}):
        actas = _actas_senado_26122(session, anio)
        if actas is None:
            raise ValueError(f"listado de actas del Senado {anio} inaccesible")
        for acta in actas:
            if acta["id"] in vistos:
                continue
            clave = _clave_decreto_de_titulo(acta["titulo"])
            if clave is None:
                # no se marca vista: el aviso se repite cada corrida hasta que
                # alguien resuelva el caso a mano (preferible a perder una
                # derrota en silencio)
                print(f"[WARN] {CINTURON}.derrotas_legislativas: acta {acta['id']} con fórmula "
                      f"26.122 pero sin número de decreto legible — revisar a mano: {acta['titulo'][:140]}")
                continue
            if int(clave.split("/")[1]) < 2023:
                vistos[acta["id"]] = f"{clave}: decreto de gestión anterior — fuera de alcance (dic-2023→)"
                continue
            r = _paced_get(session, SENADO_BASE, f"/votaciones/detalleActa/{acta['id']}")
            if r is None:
                raise ValueError(f"detalleActa {acta['id']} del Senado inaccesible")
            filas = _parsear_acta(r.text)
            afirm = sum(1 for f in filas if f["voto"] == "AFIRMATIVO")
            neg = sum(1 for f in filas if f["voto"] == "NEGATIVO")
            if afirm == 0 and neg == 0:
                vistos[acta["id"]] = f"{clave}: votación sin votos registrados (anulada/rehecha) — sin efecto"
                continue
            if neg > afirm:
                entry = next((d for d in registro["decretos"] if d.get("clave") == clave), None)
                if entry is None:
                    entry = {"clave": clave, "etiqueta": f"Decreto {clave}",
                             "tipo": _tipo_decreto_de_titulo(acta["titulo"]),
                             "tema": acta["titulo"], "publicado_bo": None, "rechazos": [],
                             "estado": "rechazado por el Senado",
                             "detalle": "Detectado automáticamente en las actas del Senado."}
                    registro["decretos"].append(entry)
                fecha = acta["fecha"].strftime("%Y-%m-%d")
                if not any(rz.get("camara") == "Senado" and rz.get("fecha") == fecha
                           for rz in entry["rechazos"]):
                    entry["rechazos"].append({"fecha": fecha, "camara": "Senado",
                                              "acta": acta["id"],
                                              "votos": f"{neg} rechazo - {afirm} validez"})
                vistos[acta["id"]] = f"{clave}: RECHAZO ({neg}-{afirm})"
            else:
                vistos[acta["id"]] = f"{clave}: aprobación/validez ({afirm}-{neg}) — no es derrota"


def _derrotas_eventos(registro: dict) -> list[dict]:
    """Eventos de derrota consumada derivados del registro, cada norma UNA vez:
    [{fecha, tipo: veto_insistido | decreto_rechazado, nombre}] ascendente.
    Veto → fecha de la insistencia completa; decreto → fecha del PRIMER rechazo
    en recinto (el segundo consuma la derogación pero es la misma derrota)."""
    eventos = []
    for v in registro.get("vetos", []):
        if v.get("insistencia_completa"):
            eventos.append({"fecha": v["insistencia_completa"], "tipo": "veto_insistido",
                            "nombre": f"ley {v['proyecto']}"})
    for d in registro.get("decretos", []):
        fechas = [rz["fecha"] for rz in d.get("rechazos", []) if rz.get("fecha")]
        if fechas:
            eventos.append({"fecha": min(fechas), "tipo": "decreto_rechazado",
                            "nombre": d.get("etiqueta") or d.get("clave", "?")})
    return sorted(eventos, key=lambda e: e["fecha"])


def _derrotas_conteo_12m(eventos: list[dict], referencia: date) -> tuple:
    """(total, n_vetos, n_decretos, fecha_ultimo_evento) en la ventana de los
    12 meses calendario que terminan en el mes de `referencia` (inclusive) —
    misma ventana con la que descargar_series deriva la serie mensual, así
    card y serie cuentan igual."""
    meses = referencia.year * 12 + (referencia.month - 1)
    desde = meses - 11
    ym_desde = f"{desde // 12}-{desde % 12 + 1:02d}"
    ym_hasta = f"{referencia.year}-{referencia.month:02d}"
    en_ventana = [e for e in eventos if ym_desde <= e["fecha"][:7] <= ym_hasta]
    n_vetos = sum(1 for e in en_ventana if e["tipo"] == "veto_insistido")
    ultimo = max((e["fecha"] for e in en_ventana), default=None)
    return len(en_ventana), n_vetos, len(en_ventana) - n_vetos, ultimo


def _derrotas_detalle_txt(n_vetos: int, n_decretos: int) -> str:
    """Detalle legible de la card ("valor usado" del modal, vía publicar.py)."""
    if n_vetos == 0 and n_decretos == 0:
        return ("sin derrotas legislativas en los últimos 12 meses "
                "(ni vetos insistidos ni decretos rechazados en el recinto)")
    txt_vetos = (f"{n_vetos} veto{'s' if n_vetos != 1 else ''} "
                 f"insistido{'s' if n_vetos != 1 else ''} por el Congreso")
    txt_decretos = (f"{n_decretos} decreto{'s' if n_decretos != 1 else ''} "
                    f"rechazado{'s' if n_decretos != 1 else ''} en el recinto")
    return f"{txt_vetos} + {txt_decretos} en los últimos 12 meses"


def fetch_derrotas_legislativas() -> dict | None:
    """
    Derrotas legislativas del Ejecutivo en los últimos 12 meses: vetos
    insistidos por ambas cámaras + decretos (DNU/delegados) rechazados por al
    menos una cámara bajo la ley 26.122. Conteo absoluto, cada norma una vez,
    fechada en el mes de la derrota consumada. Menor = mejor.

    Fuentes: InfoLeg (decretos de veto + leyes promulgadas por insistencia,
    misma sesión que fetch_ratio_dnu) y actas de votación del Senado (misma
    mecánica de POST paginado que cohesion_bloque_senado). El estado vive en
    DERROTAS_EVENTOS_PATH; la corrida hace detección INCREMENTAL (≈5 POSTs a
    InfoLeg + 1-2 al Senado por corrida) y solo persiste el registro si las
    tres etapas llegaron a las fuentes — un fallo degrada al caché del
    snapshot anterior (desactualizado=True), sin corromper el registro.
    """
    try:
        registro = _cargar_derrotas_registro()
        if registro is None:
            raise ValueError(f"registro de eventos ausente o ilegible ({DERROTAS_EVENTOS_PATH})")
        session, action_url = _infoleg_abrir_sesion()
        _derrotas_detectar_vetos(session, action_url, registro)
        _derrotas_detectar_insistencias(session, action_url, registro)
        _derrotas_detectar_decretos(registro)
        registro.setdefault("_meta", {})["actualizado"] = str(date.today())
        _guardar_derrotas_registro(registro)

        eventos = _derrotas_eventos(registro)
        total, n_vetos, n_decretos, ultimo = _derrotas_conteo_12m(eventos, date.today())
        return {
            "valor": total,
            "n_vetos_12m": n_vetos,
            "n_decretos_12m": n_decretos,
            "n_eventos_historico": len(eventos),
            "ultimo_evento": ultimo,
            "detalle_txt": _derrotas_detalle_txt(n_vetos, n_decretos),
            "unidad": "Derrotas del Ejecutivo en el recinto, últimos 12 meses (vetos insistidos + decretos rechazados)",
            "fuente": "InfoLeg (vetos e insistencias) + actas de votación del Senado (decretos, ley 26.122) — elaboración CIGOB",
            "fecha_dato": str(date.today()),
            "desactualizado": False,
        }

    except Exception as e:
        _warn("derrotas_legislativas", str(e))
        return None

# ── Rotación del gabinete (registro curado + detector de alerta InfoLeg) ─────
#
# Modelo semiautomático, mismo patrón que privatizaciones (ITCG) y
# adhesion_reformas_provincial: la FUENTE DE VERDAD es un registro curado
# versionado (data/politica/gabinete_salidas.json — cada salida con persona,
# cargo, mes de cese efectivo, decreto BO y clasificación), y un detector
# automático contra InfoLeg AVISA si aparece un decreto de renuncia
# ministerial que el registro no refleja — el detector nunca modifica el
# registro solo (distinguir eyección de pase lateral es una clasificación
# política que ningún regex hace: el Dto. 548/2026 acepta la renuncia de
# Adorni a JGM Y la de Santilli a Interior en el mismo acto, pero solo la
# primera es una salida del gabinete).
#
# El detector es de dos etapas porque el buscador de InfoLeg es OR sobre
# palabras (no frase ni AND: "acéptase la renuncia ministro" devuelve MÁS
# resultados que "renuncia" sola) y trunca la síntesis del listado a ~150
# caracteres, casi siempre antes del cargo. E1: listado mensual con
# texto="renuncia" + tipoNorma=2 (7-20 filas/mes). E2: para las filas cuyo
# resumen truncado arranca con tag de dependencia ministerial y contiene
# RENUNCIA (2-8/mes), detalle verNorma.do (cacheado en disco, patrón
# cohesion_bloque_diputados_actas_cache) y regex final de cargo sobre el
# resumen completo. Probado end-to-end sobre dic-2023→jul-2026: recall 11/11
# salidas reales, cero renuncias no-ministeriales filtradas (jueces,
# fiscales, embajadores y directorios quedan afuera por el tag de
# dependencia; los "ministros plenipotenciarios" del servicio exterior, por
# la exigencia de "MINISTR[OA] DE").

_GABINETE_INFOLEG_PAUSA = 1.6   # seg entre requests al buscador (detector)
_RE_GABINETE_TAG = re.compile(r"^(JEFATURA DE GABINETE DE MINISTROS|MINISTERIO DE[L]? )")
_RE_GABINETE_CARGO = re.compile(
    r"RENUNCIA PRESENTADA POR (?:LA|EL) ([^(]{3,80}?)\s*\(D\.?N\.?I[^)]*\)\s*"
    r"AL CARGO DE (JEFE DE GABINETE DE MINISTROS|JEFA DE GABINETE DE MINISTROS|"
    r"MINISTR[OA] DE[L]? [A-ZÑ ,]{3,70})")
_RE_GABINETE_DECRETO = re.compile(r"Decreto\s+(\d+)\s*/\s*(\d{4})")


def _norm_mayusculas(s: str) -> str:
    """Mayúsculas sin acentos (el HTML de InfoLeg mezcla ambas formas)."""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).upper()


def cargar_gabinete_salidas() -> dict | None:
    """Registro curado de salidas de rango ministerial, o None si falta/roto."""
    try:
        return json.loads(GABINETE_SALIDAS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _indice_mes(ym: str) -> int | None:
    """'YYYY-MM' → meses desde el año 0 (para aritmética de ventanas)."""
    try:
        return int(ym[:4]) * 12 + (int(ym[5:7]) - 1)
    except (ValueError, TypeError):
        return None


def salidas_gabinete_ventana_12m(salidas: list, ym: str) -> list:
    """Salidas del registro cuyo mes de cese efectivo cae en la ventana de 12
    meses calendario que termina en `ym` (YYYY-MM, inclusive) — la métrica
    del indicador. Los movimientos laterales y las reestructuraciones de la
    Ley de Ministerios no están en `salidas` (viven en sus propias claves del
    registro), así que quedan excluidos por construcción."""
    fin = _indice_mes(ym)
    if fin is None:
        return []
    out = []
    for s in salidas:
        idx = _indice_mes(str(s.get("mes", "")))
        if idx is not None and fin - 11 <= idx <= fin:
            out.append(s)
    return out


def _cargar_cache_gabinete_decretos() -> dict:
    try:
        return json.loads(GABINETE_DECRETOS_CACHE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def _guardar_cache_gabinete_decretos(cache: dict) -> None:
    GABINETE_DECRETOS_CACHE_PATH.write_text(
        json.dumps(cache, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _gabinete_sesion_infoleg():
    """(session, action_url) contra el buscador de InfoLeg — misma mecánica
    que fetch_ratio_dnu / gestion._infoleg_post (GET home → form action)."""
    session = requests.Session()
    r_home = session.get(INFOLEG_HOME, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r_home.raise_for_status()
    action_m = re.search(r'action="(/infolegInternet/[^"]+)"', r_home.text)
    if not action_m:
        raise ValueError("No se encontró la URL del formulario InfoLeg")
    time.sleep(_GABINETE_INFOLEG_PAUSA)
    return session, "https://servicios.infoleg.gob.ar" + action_m.group(1)


def _gabinete_parsear_filas(html: str) -> list:
    """Filas del listado de resultados de InfoLeg → [{id, decreto, descripcion}].
    La síntesis viene truncada a ~150 caracteres — solo sirve para el
    prefiltro de E2, nunca para clasificar."""
    filas = []
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", html, re.S):
        m_id = re.search(r"verNorma\.do\?id=(\d+)", tr)
        if not m_id:
            continue
        celdas = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        limpio = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in celdas]
        titulo = limpio[0] if limpio else ""
        m_dec = _RE_GABINETE_DECRETO.search(titulo)
        filas.append({
            "id": m_id.group(1),
            "decreto": f"Decreto {m_dec.group(1)}/{m_dec.group(2)}" if m_dec else titulo[:40],
            "descripcion": limpio[-1] if len(limpio) >= 2 else "",
        })
    return filas


def _gabinete_listado_mes(session, action_url: str, anio: int, mes: int,
                           max_paginas: int = 4) -> list:
    """E1 del detector: decretos publicados en el mes con 'renuncia' en el
    texto (paginado con desplazamiento=AP, como el buscador real)."""
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    data = {
        "tipoNorma": "2", "numero": "", "anioSancion": "", "dependencia": "",
        "diaPubDesde": "01", "mesPubDesde": f"{mes:02d}", "anioPubDesde": str(anio),
        "diaPubHasta": str(ultimo_dia), "mesPubHasta": f"{mes:02d}", "anioPubHasta": str(anio),
        "texto": "renuncia",
    }
    r = session.post(action_url, data=data, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    time.sleep(_GABINETE_INFOLEG_PAUSA)
    if re.search(r"No se encontraron normas", r.text, re.IGNORECASE):
        return []
    m = re.search(r"Encontradas?[:\s]+(\d+)", r.text, re.IGNORECASE)
    total = int(m.group(1)) if m else None
    filas = _gabinete_parsear_filas(r.text)
    pagina = 2
    while total and len(filas) < total and pagina <= max_paginas:
        rp = session.post(action_url, data={"desplazamiento": "AP", "irAPagina": str(pagina)},
                          headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        rp.raise_for_status()
        time.sleep(_GABINETE_INFOLEG_PAUSA)
        nuevas = _gabinete_parsear_filas(rp.text)
        if not nuevas:
            break
        filas.extend(nuevas)
        pagina += 1
    return filas


def _gabinete_resumen_norma(session, norma_id: str, cache: dict) -> str:
    """E2 del detector: el campo Resumen COMPLETO de verNorma.do (el listado
    lo trunca antes del cargo). Cacheado en disco de inmediato — una norma
    publicada no cambia, y el caché evita repagar los GET en cada corrida
    (mismo criterio que la caché permanente por acta de Diputados)."""
    if norma_id in cache:
        return cache[norma_id]
    r = session.get(f"https://servicios.infoleg.gob.ar/infolegInternet/verNorma.do?id={norma_id}",
                    headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    time.sleep(_GABINETE_INFOLEG_PAUSA)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))
    m = re.search(r"Resumen:\s*(.*?)(?:Texto completo de la norma|Esta norma|$)", txt)
    resumen = _norm_mayusculas(m.group(1).strip()) if m else ""
    cache[norma_id] = resumen
    _guardar_cache_gabinete_decretos(cache)
    return resumen


def _detectar_salidas_gabinete_infoleg(meses_atras: int = 1) -> list | None:
    """Detector de alerta: renuncias a cargos de rango ministerial publicadas
    en el BO en el mes corriente y los `meses_atras` previos (el decreto puede
    llegar hasta ~40 días después del hecho político — caso Ferraro). Devuelve
    [{decreto, persona, cargo, mes_bo}] dedupeado (un mismo decreto puede
    repetir el párrafo de una renuncia en su resumen), o None si InfoLeg no
    respondió — el indicador NO depende de esto para publicar (el registro
    curado manda), solo para avisar."""
    try:
        session, action_url = _gabinete_sesion_infoleg()
    except Exception:
        return None
    hoy = date.today()
    meses = []
    anio, mes = hoy.year, hoy.month
    for _ in range(meses_atras + 1):
        meses.append((anio, mes))
        anio, mes = (anio - 1, 12) if mes == 1 else (anio, mes - 1)

    cache = _cargar_cache_gabinete_decretos()
    detecciones, vistos = [], set()
    for anio, mes in meses:
        try:
            filas = _gabinete_listado_mes(session, action_url, anio, mes)
        except Exception:
            return None   # listado caído: sin señal confiable, mejor no "detectar nada"
        for fila in filas:
            desc = _norm_mayusculas(fila["descripcion"])
            if not _RE_GABINETE_TAG.search(desc) or "RENUNCIA" not in desc:
                continue
            try:
                resumen = _gabinete_resumen_norma(session, fila["id"], cache)
            except Exception:
                continue   # un detalle caído no invalida el resto del barrido
            for m_c in _RE_GABINETE_CARGO.finditer(resumen):
                clave = (fila["decreto"], m_c.group(1).strip(), m_c.group(2).strip())
                if clave in vistos:
                    continue
                vistos.add(clave)
                detecciones.append({
                    "decreto": fila["decreto"],
                    "persona": m_c.group(1).strip().title(),
                    "cargo": m_c.group(2).strip(),
                    "mes_bo": f"{anio}-{mes:02d}",
                })
    return detecciones


def _gabinete_discrepancias(registro: dict, detecciones: list) -> list:
    """Detecciones cuyo decreto NO está citado en el registro curado (ni como
    salida ni como movimiento lateral): son las que exigen curaduría. Se
    compara por número de decreto (no por persona) para que una re-salida de
    una persona ya registrada también dispare la alerta."""
    texto_registro = json.dumps(registro, ensure_ascii=False)
    decretos_registrados = {f"Decreto {n}/{a}" for n, a
                            in _RE_GABINETE_DECRETO.findall(texto_registro)}
    return [d for d in detecciones if d["decreto"] not in decretos_registrados]


def fetch_rotacion_gabinete() -> dict | None:
    """Salidas de rango ministerial (jefe de Gabinete + ministros) acumuladas
    en la ventana móvil de 12 meses que termina en el mes corriente, desde el
    registro curado (menor = mejor). Cuenta salidas políticas Y estructurales
    (ceses por banca electoral) sin distinguir — la composición se publica
    como transparencia y los casos extremos se administran con el override
    del analista (ajustes_itcp.json). No cuenta pases laterales dentro del
    gabinete ni reestructuraciones de la Ley de Ministerios.

    fecha_dato = fecha del chequeo (hoy): el registro no "vence" por falta de
    eventos — el no-evento es dato (0 salidas ese mes) — y el guard real de
    frescura es el detector InfoLeg, que avisa si aparece un decreto de
    renuncia ministerial no registrado. La última salida queda en
    `ultima_salida` para la lectura fina."""
    registro = cargar_gabinete_salidas()
    if registro is None or not isinstance(registro.get("salidas"), list):
        _warn("rotacion_gabinete", f"registro curado ausente o ilegible ({GABINETE_SALIDAS_PATH.name})")
        return None

    ym = date.today().strftime("%Y-%m")
    en_ventana = salidas_gabinete_ventana_12m(registro["salidas"], ym)
    politicas = [s for s in en_ventana if s.get("clasificacion") == "salida_politica"]
    estructurales = [s for s in en_ventana if s.get("clasificacion") == "salida_estructural_electoral"]
    ultima = max(registro["salidas"], key=lambda s: str(s.get("mes", "")), default=None)

    if en_ventana:
        lista = ", ".join(f"{s['persona']} ({s['mes']})"
                          for s in sorted(en_ventana, key=lambda s: str(s.get("mes", ""))))
        detalle = (f"{len(en_ventana)} salidas en 12 meses = {len(politicas)} políticas · "
                   f"{len(estructurales)} por bancas electorales — {lista}")
    else:
        detalle = "0 salidas de rango ministerial en los últimos 12 meses"

    resultado = {
        "valor": len(en_ventana),
        "unidad": "salidas de rango ministerial (acum. 12 meses)",
        "fuente": "Decretos de designación y renuncia — Boletín Oficial (registro curado CIGOB)",
        "fecha_dato": str(date.today()),
        "desactualizado": False,
        "salidas_politicas": len(politicas),
        "salidas_estructurales": len(estructurales),
        "ultima_salida": (f"{ultima['persona']} — {ultima['cargo']} ({ultima['mes']})"
                          if ultima else None),
        "detalle_txt": detalle,
    }

    # Detector de alerta (no bloquea: si InfoLeg falla, el registro manda)
    try:
        detecciones = _detectar_salidas_gabinete_infoleg()
    except Exception as e:
        print(f"[WARN] {CINTURON}.rotacion_gabinete: detector InfoLeg falló ({e}) — "
              "se publica igual desde el registro curado")
        detecciones = None
    if detecciones is not None:
        discrepancias = _gabinete_discrepancias(registro, detecciones)
        for d in discrepancias:
            print(f"[ALERTA] {CINTURON}.rotacion_gabinete: {d['decreto']} (BO {d['mes_bo']}) "
                  f"acepta la renuncia de {d['persona']} al cargo de {d['cargo']} y NO figura "
                  f"en el registro curado — revisar data/politica/gabinete_salidas.json")
        if discrepancias:
            resultado["detector_decretos_sin_registrar"] = [
                f"{d['decreto']} — {d['persona']} ({d['cargo']})" for d in discrepancias]

    return resultado


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


# Pesos por cámara del compuesto bicameral de cohesión (ADR-0048): el mismo
# ratio interno 65/35 ≈ 45/25 que las dos cámaras tenían como indicadores
# separados dentro de la dimensión (ADR-0036/0047). Renormaliza si una cámara
# no tiene dato — mismo criterio que la paramétrica ante faltantes.
COHESION_PESOS_CAMARAS = {"diputados": 0.65, "senado": 0.35}


def componer_cohesion_bloque(dip: dict | None, sen: dict | None) -> dict | None:
    """Card compuesta bicameral de cohesión del bloque LLA (ADR-0048,
    revisión editorial CIGOB 2026-07-10): un solo indicador en lugar de las
    dos cards por cámara. Rice de Diputados 65% + Rice del Senado 35%,
    renormalizado sobre las cámaras con dato. Los componentes por cámara
    quedan en la card (mismo patrón que el Fondo de Cese en gestión) y son
    la fuente del carry-forward por cámara de la próxima corrida
    (_anterior_camara los lee de vuelta)."""
    camaras = {"diputados": dip, "senado": sen}
    con_dato = {c: e for c, e in camaras.items()
                if e is not None and e.get("valor") is not None}
    if not con_dato:
        return None
    peso_total = sum(COHESION_PESOS_CAMARAS[c] for c in con_dato)
    valor = round(sum(e["valor"] * COHESION_PESOS_CAMARAS[c]
                      for c, e in con_dato.items()) / peso_total, 1)
    fechas = [e["fecha_dato"] for e in con_dato.values() if e.get("fecha_dato")]
    return {
        "valor": valor,
        "unidad": ("% cohesión (índice de Rice bicameral: Diputados 65% + Senado 35%, "
                   "promedio actas divididas últimos 90 días)"),
        "fuente": "Votaciones nominales de Diputados y Senado — elaboración CIGOB (scraping directo)",
        "fecha_dato": max(fechas) if fechas else None,
        "n_actas": sum(e.get("n_actas") or 0 for e in con_dato.values()),
        # desactualizado solo si TODAS las cámaras que aportan están
        # desactualizadas: con una cámara fresca el compuesto tiene
        # información nueva (la composición por cámara queda visible abajo).
        "desactualizado": all(e.get("desactualizado") for e in con_dato.values()),
        "componentes": {
            c: {k: e.get(k) for k in ("valor", "fecha_dato", "n_actas",
                                       "corrida_exitosa_en", "desactualizado")}
            for c, e in camaras.items() if e is not None
        },
    }


def _anterior_camara(indicadores_anteriores: dict, camara: str) -> dict | None:
    """Último dato conocido de una cámara para el carry-forward del compuesto.
    Forma nueva: dentro de "componentes" de la card compuesta. Formas de
    migración (cache anterior a ADR-0048): cohesion_bloque era la card de
    Diputados sola y cohesion_bloque_senado la del Senado."""
    comp = indicadores_anteriores.get("cohesion_bloque")
    if comp is not None and isinstance(comp.get("componentes"), dict):
        return comp["componentes"].get(camara)
    if camara == "diputados":
        return comp
    return indicadores_anteriores.get("cohesion_bloque_senado")


def _entrada_camara(resultado: dict | None, anterior: dict | None) -> tuple:
    """(entrada, corrida_ok) por cámara para el compuesto — las MISMAS tres
    ramas que tenían las dos cards separadas: corrida con votos nuevos /
    corrida exitosa sin votos en la ventana (receso: se reusa el último valor
    sin marcarlo desactualizado) / sin corrida (cache, con el chequeo de
    staleness de _cohesion_desactualizada). corrida_ok = la corrida de HOY
    llegó al sitio (insumo del conteo de frescura del colector)."""
    if resultado is not None and resultado.get("valor") is not None:
        return resultado, True
    if resultado is not None and anterior is not None:
        return ({**anterior, "desactualizado": False,
                 "corrida_exitosa_en": resultado["corrida_exitosa_en"]}, True)
    if anterior is not None:
        return ({**anterior,
                 "desactualizado": _cohesion_desactualizada(anterior, resultado)}, False)
    return None, resultado is not None


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
    patrón que gestion.anotar_indicadores para el ITCG). Desde ADR-0048 el
    ITCP tiene contexto declarado (itcp.INDICADORES_CONTEXTO:
    rotacion_gabinete y protestas_caba — se publican, no puntúan); sus bandas
    siguen en itcp.BANDAS_ITCP como referencia histórica, por eso el
    override explícito después del fallback (mismo esquema que macro/ITCM)."""
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
            if nombre in itcp.INDICADORES_CONTEXTO:
                ind["en_indice"] = False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    cache_anterior         = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})

    frescos: dict = {}
    frescos_count = 0

    colectores = [
        ("votometro_ventaja_lla",         fetch_votometro),
        ("ratio_dnu",                     fetch_ratio_dnu),
        ("conflictividad_nacional",       fetch_conflictividad_nacional),
        ("movilizacion_cepa",             fetch_cepa_movilizacion),
        ("iaf_transferencias",            fetch_iaf_transferencias),
        ("eficacia_legislativa",          fetch_eficacia_legislativa),
        ("veto_quorum",                   fetch_veto_quorum),
        ("comisiones_caidas",             fetch_comisiones_caidas),
        ("adhesion_reformas_provincial",  fetch_adhesion_reformas_provincial),
        ("derrotas_legislativas",         fetch_derrotas_legislativas),
        ("rotacion_gabinete",             fetch_rotacion_gabinete),
        ("protestas_caba",                fetch_protestas_caba),
    ]

    for nombre, fetcher in colectores:
        resultado = fetcher()
        if _resultado_utilizable(nombre, resultado):
            frescos[nombre] = resultado
            frescos_count += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    # Compuesto bicameral de cohesión (ADR-0048): una sola card desde las dos
    # corridas por cámara. Cada cámara conserva sus tres ramas de fallback
    # (fresco / receso / cache) vía _entrada_camara; el compuesto cuenta como
    # fresco solo si AMBAS corridas llegaron a su sitio — con una sola cámara
    # fresca el valor sale igual (renormalizado) pero el exit code del
    # colector reporta frescura mixta, como cuando eran dos cards.
    resultado_cohesion = fetch_cohesion_bloque()
    anterior_dip = _anterior_camara(indicadores_anteriores, "diputados")
    if anterior_dip is not None and _es_cohesion_legado(anterior_dip):
        # Cache heredado del viejo placeholder manual (78, "% votos alineados
        # con la posición oficial") — NO es un dato de Rice genuino, tratarlo
        # como ausente para no corromper el ITCP con un valor de significado
        # distinto (hallazgo de revisión externa).
        anterior_dip = None
    entrada_dip, dip_ok = _entrada_camara(resultado_cohesion, anterior_dip)

    resultado_cohesion_senado = fetch_cohesion_bloque_senado()
    anterior_sen = _anterior_camara(indicadores_anteriores, "senado")
    entrada_sen, sen_ok = _entrada_camara(resultado_cohesion_senado, anterior_sen)

    compuesto_cohesion = componer_cohesion_bloque(entrada_dip, entrada_sen)
    if compuesto_cohesion is not None:
        frescos["cohesion_bloque"] = compuesto_cohesion
        if dip_ok and sen_ok:
            frescos_count += 1

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
