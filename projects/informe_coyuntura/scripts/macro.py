"""
Colector Cinturón Macro — CIGOB
Patrón estándar: URLs → fetch → score → cache → exit codes
Ejecutar desde projects/informe_coyuntura/: python scripts/macro.py
"""
import sys
import re
import json
import requests
import urllib3
import logging
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import itcm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_PATH  = PROJECT_DIR / "output" / "cache" / "macro.json"
PATENTAMIENTOS_PATH = PROJECT_DIR / "data" / "macro" / "patentamientos_comerciales.json"

# ── URL Constants (NFR6: URLs al inicio del script) ───────────────────────────
INDEC_SERIES_BASE   = "https://apis.datos.gob.ar/series/api/series/"
BCRA_VARIABLES_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
# ITCRM oficial del BCRA (base 17-dic-2015=100). Reemplaza la serie de INDEC
# 116.3_TCRMA, discontinuada en dic-2024. La planilla trae prom. mensuales.
BCRA_ITCRM_URL      = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/ITCRMSerie.xlsx"
ITCRM_SHEET_MENSUAL = "ITCRM y bilaterales prom. mens."

# INDEC — series IDs verificados en datos.gob.ar
INDEC_IPC_ID         = "148.3_INIVELNAL_DICI_M_26"     # IPC total nacional mensual
INDEC_EMAE_IA_ID     = "143.3_ICE_SERVIA_2004_A_25"    # EMAE variación i.a. mensual (base 2004)
INDEC_SALDO_COM_ID   = "164.3_SOTALTAL_0_0_8"          # Saldo comercial total mensual (M USD) — FALLBACK, ~14 meses de rezago
INDEC_EXPO_ICA_ID    = "74.3_IET_0_M_16"               # ICA exportaciones totales mensual (M USD)
INDEC_IMPO_ICA_ID    = "74.3_IIT_0_M_25"               # ICA importaciones totales mensual (M USD)
INDEC_RECAUDACION_ID = "172.3_TL_RECAION_M_0_0_17"     # Recaudación total mensual (M ARS)
INDEC_TCRM_ID        = "116.3_TCRMA_0_M_36"            # Tipo de Cambio Real Multilateral (base 2010=100)

# Capítulo Inversión — IAI (físico/tradicional) e ICIP (digital/intangible)
INDEC_ISAC_NIVEL_ID  = "33.2_ISAC_NIVELRAL_0_M_18_63"  # ISAC nivel general (índice 2004=100) → i.a.
INDEC_BK_IMPO_ID     = "74.3_IIBCA_0_M_32"             # Importación de bienes de capital (M USD) → i.a.
INDEC_SVC_INFO_ID    = "185.1_PAGO_SERVIICA_0_M_38"    # Pagos al exterior de servicios de informática (M USD) → i.a.
INDEC_IPI_NIVEL_ID   = "453.1_SERIE_ORIGNAL_0_0_14_46" # IPI manufacturero nivel general (índice 2004=100)
INDEC_EMPLEO_EIL_ID  = "50.3_ICS_0_M_12"               # Índice de empleo total (EIL) — denominador de productividad

# DNRPA — patentamientos comerciales (no hay histórico: se ACUMULA mes a mes).
DNRPA_CKAN_PACKAGE   = "https://datos.jus.gob.ar/api/3/action/package_show"
DNRPA_INSCRIP_AUTOS  = "37c9ad39-f092-44be-9b7f-1201b3c4b7a8"  # dataset "Inscripciones iniciales de autos"
# Tipos de vehículo (automotor_tipo_descripcion) considerados comerciales
# (livianos + pesados), proxy de inversión en logística y transporte.
PATENTAMIENTOS_COMERCIALES_KEYS = ("CAMION", "PICK", "UTILITARIO", "FURGON", "CHASIS", "TRACTOR DE CARRETERA")

# BCRA — variable IDs verificados en api.bcra.gob.ar v4.0
BCRA_RESERVAS_ID    = 1    # Reservas internacionales BRUTAS (millones USD)
BCRA_BADLAR_ID      = 7    # BADLAR bancos privados (% anual) — contexto + insumo del IdC
BCRA_REM_IPC_ID     = 29   # REM: mediana expectativas IPC próximos 12 meses (% anual)
BCRA_PRESTAMOS_ID   = 26   # Préstamos sector privado (millones ARS) — contexto
BCRA_BASE_MON_ID    = 15   # Base monetaria (millones ARS)
BCRA_TC_MAYOR_ID    = 5    # Tipo de cambio mayorista de referencia (ARS/USD)
BCRA_DEP_PRIV_ID    = 100  # Depósitos del sector privado no financiero (incluye cedros) — insumo IdC + M3 priv.
BCRA_PREST_PRIV_ID  = 117  # Préstamos otorgados al sector privado — insumo IdC
BCRA_CIRCULANTE_ID  = 17   # Billetes y monedas en poder del público — insumo M3 privado (IDM)
BCRA_M2_PRIV_ID     = 197  # M2 transaccional del sector privado — demanda de dinero (IDM)

HTTP_TIMEOUT = 30
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}

logging.basicConfig(level=logging.WARNING, format="%(message)s")

CINTURON = "macro"
INDICADORES_ESPERADOS = [
    "ipc_total", "reservas_bcra", "idc", "badlar",
    "emae_ia", "saldo_comercial_12m", "recaudacion", "tcrm",
    "rem_ipc_12m", "idm", "iai", "icip", "credito_privado",
    "prestamos_privados", "base_monetaria", "tc_mayorista",
]


def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _warn(indicador: str, err: Exception) -> None:
    print(f"[WARN] {CINTURON}.{indicador}: {err}. Usando cache.")


def _indec_serie(series_id: str, limit: int = 2) -> list:
    params = {"ids": series_id, "format": "json", "limit": limit, "sort": "desc"}
    r = requests.get(INDEC_SERIES_BASE, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["data"]


def _bcra_detalle(var_id: int, dias: int = 60) -> list:
    """Devuelve el detalle diario del BCRA para los últimos `dias` días, ordenado desc."""
    desde = (datetime.today() - timedelta(days=dias)).strftime("%Y-%m-%d")
    url   = f"{BCRA_VARIABLES_BASE}/{var_id}"
    r = requests.get(url, params={"desde": desde},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    detalle = r.json()["results"][0]["detalle"]
    return sorted(detalle, key=lambda x: x["fecha"], reverse=True)


def _bcra_ultimo(var_id: int) -> dict:
    detalle = _bcra_detalle(var_id, dias=45)
    ultimo  = detalle[0]
    return {"valor": ultimo["valor"], "fecha": ultimo["fecha"]}


def _bcra_par(var_id: int) -> dict:
    """Par (valor actual, valor de hace ~30 días) de una serie BCRA, para los
    ratios mensuales del IdC. Devuelve {actual, anterior, fecha}."""
    detalle = _bcra_detalle(var_id, dias=70)
    ultimo  = detalle[0]
    fecha_u = date.fromisoformat(ultimo["fecha"])
    anterior = next((d for d in detalle
                     if (fecha_u - date.fromisoformat(d["fecha"])).days >= 28), None)
    if anterior is None:
        raise ValueError(f"BCRA var {var_id}: sin datos de hace 30+ días")
    return {"actual": float(ultimo["valor"]), "anterior": float(anterior["valor"]),
            "fecha": ultimo["fecha"]}


def _ipc_mensual() -> float:
    """Última variación m/m del IPC (%), insumo del IdC (BADLAR real)."""
    data = _indec_serie(INDEC_IPC_ID, limit=2)
    return (data[0][1] / data[1][1] - 1) * 100


def _indec_yoy(series_id: str) -> dict:
    """Variación interanual (%) de una serie mensual INDEC: último mes vs el
    mismo mes del año anterior (13 puntos atrás). {var_ia, fecha}."""
    data = _indec_serie(series_id, limit=13)
    actual, hace_12m = data[0][1], data[12][1]
    return {"var_ia": (actual / hace_12m - 1) * 100, "fecha": data[0][0]}


def _bcra_variacion_m(var_id: int) -> dict:
    """Variación % mensual: último valor vs valor de hace ~30 días."""
    detalle = _bcra_detalle(var_id, dias=60)
    ultimo  = detalle[0]
    fecha_u = date.fromisoformat(ultimo["fecha"])
    # Buscar el registro más cercano a 30 días atrás
    hace_30 = None
    for d in detalle:
        fecha_d = date.fromisoformat(d["fecha"])
        if (fecha_u - fecha_d).days >= 28:
            hace_30 = d
            break
    if hace_30 is None:
        raise ValueError(f"BCRA var {var_id}: sin datos de hace 30+ días")
    var_m = (float(ultimo["valor"]) / float(hace_30["valor"]) - 1) * 100
    return {"var_m": round(var_m, 2), "fecha": ultimo["fecha"]}


def _bcra_fin_de_mes(var_id: int, meses: int) -> dict:
    """{YYYY-MM: último valor del mes} de una serie BCRA, sobre los últimos
    `meses` meses. Insumo del IDM (agregados monetarios de fin de mes)."""
    desde = (date.today() - timedelta(days=int(meses * 31) + 10)).isoformat()
    url   = f"{BCRA_VARIABLES_BASE}/{var_id}"
    r = requests.get(url, params={"desde": desde, "limit": 3000},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    detalle = r.json()["results"][0]["detalle"]
    por_mes = {}
    for d in sorted(detalle, key=lambda x: x["fecha"]):
        por_mes[d["fecha"][:7]] = float(d["valor"])   # se queda con el último día del mes
    return por_mes


def _ipc_indice_mensual(limit: int = 40) -> dict:
    """{YYYY-MM: índice IPC nivel} para deflactar los agregados del IDM."""
    data = _indec_serie(INDEC_IPC_ID, limit=limit)
    return {row[0][:7]: row[1] for row in data if row[1] is not None}


def _indec_nivel_mensual(series_id: str, limit: int = 40) -> dict:
    """{YYYY-MM: valor} de una serie INDEC mensual de nivel."""
    return {row[0][:7]: row[1] for row in _indec_serie(series_id, limit=limit) if row[1] is not None}


def _indec_ratio_yoy(num_id: str, den_id: str) -> dict:
    """Variación i.a. del COCIENTE de dos series INDEC mensuales (último mes
    común vs 12 meses antes). Insumo de la productividad del ICIP (IPI/empleo)."""
    num = _indec_nivel_mensual(num_id, limit=20)
    den = _indec_nivel_mensual(den_id, limit=20)
    comunes = sorted(set(num) & set(den))
    if not comunes:
        raise ValueError("ratio i.a.: sin meses comunes")
    ym = comunes[-1]
    prev = _ym_shift(ym, -12)
    if prev not in num or prev not in den:
        raise ValueError("ratio i.a.: sin 12 meses previos")
    r_t = num[ym] / den[ym]
    r_p = num[prev] / den[prev]
    return {"var_ia": (r_t / r_p - 1) * 100, "fecha": ym}


def _ym_shift(ym: str, meses: int) -> str:
    """Desplaza un 'YYYY-MM' en `meses` (puede ser negativo)."""
    total = int(ym[:4]) * 12 + (int(ym[5:7]) - 1) + meses
    return f"{total // 12}-{total % 12 + 1:02d}"


def _idm_serie_mensual(meses_hist: int = 24) -> list:
    """Serie mensual del Índice de Desequilibrio Monetario (IDM).

    Brecha entre el crecimiento interanual REAL de la oferta amplia de pesos del
    sector privado (M3 privado = circulante en poder del público + depósitos
    privados, var. 17 + 100) y el de la demanda transaccional (M2 privado, var.
    197), ambos deflactados por el IPC. Versión real-real interanual: corrige el
    sesgo inflacionario y la estacionalidad del aguinaldo de la propuesta original
    (m/m nominal-real). Positivo = la masa amplia corre por encima de la demanda
    real → excedente de pesos que presiona la brecha cambiaria.

    Devuelve [(YYYY-MM, gap_pp, m3_real_ia, m2_real_ia)] ascendente.
    """
    n = meses_hist + 14
    circ = _bcra_fin_de_mes(BCRA_CIRCULANTE_ID, n)
    dep  = _bcra_fin_de_mes(BCRA_DEP_PRIV_ID, n)
    m2   = _bcra_fin_de_mes(BCRA_M2_PRIV_ID, n)
    ipc  = _ipc_indice_mensual(meses_hist + 16)
    comunes = set(circ) & set(dep) & set(m2) & set(ipc)
    out = []
    for ym in sorted(comunes):
        prev = _ym_shift(ym, -12)
        if prev not in comunes:
            continue
        m3, m3p = circ[ym] + dep[ym], circ[prev] + dep[prev]
        m3_real_ia = ((m3 / ipc[ym]) / (m3p / ipc[prev]) - 1) * 100
        m2_real_ia = ((m2[ym] / ipc[ym]) / (m2[prev] / ipc[prev]) - 1) * 100
        out.append((ym, round(m3_real_ia - m2_real_ia, 2),
                    round(m3_real_ia, 2), round(m2_real_ia, 2)))
    return out


# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch_ipc() -> dict | None:
    try:
        data = _indec_serie(INDEC_IPC_ID, limit=2)
        actual, anterior = data[0][1], data[1][1]
        var = (actual / anterior - 1) * 100 if anterior else None
        return {
            "valor": round(var, 2) if var is not None else None,
            "unidad": "% mensual",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("ipc_total", e)
        return None


# Reservas netas "a secas" — el número que mira el mercado (Machado/Ieral),
# calculado 100% de datos oficiales, sin una sola constante:
#   netas = SDDS estricto + depósitos del Tesoro + Bopreal a 12m
# donde:
#   • SDDS estricto = Activos de reserva (I.A) − drenajes a corto plazo en ME
#     (Sección II) de la Planilla SDDS/NEDD del BCRA (oficial, mensual, USD).
#   • depósitos del Tesoro = "Dep. del gobierno en ME" del Balance Consolidado del BCRA.
#   • Bopreal a 12m = bucket de vencimiento "3m-1año" de la Sección II.1 del SDDS.
#   El SDDS descuenta Tesoro y Bopreal como pasivos, pero el mercado los suma de
#   vuelta porque no son pasivos del BCRA para defender el TC ("a secas"). Verificado
#   empíricamente: la fórmula reproduce la banda del mercado en mar/abr/may-2026 (el
#   bucket 3m-1año saltó de ~130 a ~2.670 en abril, justo cuando el Bopreal Serie 1B
#   entró a la ventana de 12 meses). Todo automático, ningún componente a mano.
SDDS_URL_BASE = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/{}.pdf"
BCRA_BALANCE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/balbcrhis.xls"
BAL_COL_RESERVAS   = 7   # "Oro y divisas (neto)" — para ubicar la última fila con dato
BAL_COL_DEP_GOB_ME = 29  # "Depósitos del gobierno nacional en moneda extranjera" (Tesoro)
BAL_COL_TC         = 42  # "Tipo de cambio de valuación 1 u$s ="
RESERVAS_PASIVOS_PATH = PROJECT_DIR / "data" / "macro" / "reservas_netas_pasivos.json"


def _num_es(s: str) -> float:
    """Número en formato es-AR ('-22.197,23') → float."""
    return float(s.replace(".", "").replace(",", "."))


def _tesoro_deposits_usd() -> float:
    """Depósitos del Tesoro en USD en el BCRA (M USD), del Balance Consolidado
    oficial (balbcrhis.xls): col 'Dep. del gobierno en ME' / TC / 1000 (el balance
    está en miles de pesos). Es el término que el mercado suma de vuelta al neto
    estricto para las 'netas de libre disponibilidad'."""
    import xlrd  # ya en requirements (1.2.0)
    r = requests.get(BCRA_BALANCE_URL, headers=HTTP_HEADERS, timeout=60, verify=False)
    r.raise_for_status()
    sh = xlrd.open_workbook(file_contents=r.content).sheet_by_name("B.C.R.A.")
    fila = next(row for row in range(sh.nrows - 1, 26, -1)
                if isinstance(sh.cell_value(row, BAL_COL_RESERVAS), (int, float))
                and sh.cell_value(row, BAL_COL_RESERVAS))
    tc  = float(sh.cell_value(fila, BAL_COL_TC))
    dep = float(sh.cell_value(fila, BAL_COL_DEP_GOB_ME))
    if tc <= 0:
        raise ValueError("balance BCRA: TC inválido")
    return dep / tc / 1000.0


def _parse_sdds_content(content: bytes) -> dict | None:
    """Parsea el PDF de UNA planilla SDDS → componentes de reservas netas, o None
    si no matchea. Reutilizable (lo usa también descargar_series.py para la serie
    histórica). netas estricto = I.A Activos de reserva + Sección II (drenajes,
    ya negativos: II.1 préstamos/dep + II.2 forwards/swaps + II.3 repos). El bucket
    "3m-1año" de II.1 es el Bopreal a 12m."""
    import io
    import pdfplumber  # ya en requirements; import perezoso → si falta, cae al fallback
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        txt = "\n".join((p.extract_text() or "") for p in pdf.pages[:2])
    ia  = re.search(r"A\.\s*Activos de reserva oficiales\s+([\d.]+,\d{2})", txt)
    ii1 = re.search(r"Pr[ée]stamos en moneda extranjera,\s*valores,?\s*y\s*dep[óo]sitos"
                    r"\s*\d*\s+(-?[\d.]+,\d{2})"
                    r"(?:\s+(-?[\d.]+,\d{2})\s+(-?[\d.]+,\d{2})\s+(-?[\d.]+,\d{2}))?", txt)
    ii2 = re.search(r"swaps de monedas\)\s*\d*\s*\n\s*(-?[\d.]+,\d{2})", txt)
    ii3 = re.search(r"3\.\s*Otros \(especificar\)\s+(-?[\d.]+,\d{2})", txt)
    if not all([ia, ii1, ii2, ii3]):
        return None
    brutas = _num_es(ia.group(1))
    p_dep, swaps, repos = _num_es(ii1.group(1)), _num_es(ii2.group(1)), _num_es(ii3.group(1))
    bopreal = _num_es(ii1.group(4)) if ii1.group(4) else 0.0
    mf = re.search(r"final del per[ií]odo\)\s*(\d{2}/\d{2}/\d{2})", txt)
    return {"netas": brutas + p_dep + swaps + repos, "brutas": brutas,
            "prestamos_dep": p_dep, "swaps": swaps, "repos": repos,
            "bopreal_12m": bopreal, "fecha": mf.group(1) if mf else None}


def _reservas_netas_sdds() -> dict:
    """Reservas netas de la última Planilla SDDS del BCRA (temp{MM}{YY}.pdf). Prueba
    las planillas de los últimos meses (se publican ~22 días tras el cierre) y usa la
    primera parseable. 100% oficial, sin ajustes ni constantes."""
    hoy = date.today(); y, m = hoy.year, hoy.month
    for _ in range(4):
        nombre = f"temp{m:02d}{y % 100:02d}"
        try:
            r = requests.get(SDDS_URL_BASE.format(nombre), headers=HTTP_HEADERS,
                             timeout=60, verify=False)
            if r.status_code == 200 and len(r.content) > 50000:
                s = _parse_sdds_content(r.content)
                if s:
                    return {**s, "planilla": nombre, "fecha": s["fecha"] or nombre}
        except Exception:
            pass
        m -= 1
        if m == 0: m = 12; y -= 1
    raise ValueError("SDDS: ninguna planilla reciente parseable")


def fetch_reservas_netas() -> dict | None:
    """Reservas NETAS de libre disponibilidad (el número del mercado), calculadas
    100% de datos oficiales, sin constantes:
        netas = SDDS estricto (planilla SDDS del BCRA) + depósitos del Tesoro (balance).
    Validación: brutas SDDS vs API ±15%; si el PDF SDDS no parsea → FALLBACK
    (brutas API − drenajes Sección II del último SDDS del config) + Tesoro. El término
    del Tesoro tiene su propio try: si el balance no baja, se omite (degradación elegante).
    Nunca queda mal en silencio."""
    try:
        tesoro = _tesoro_deposits_usd()
    except Exception as e:
        _warn("reservas_bcra (Tesoro, se omite)", e)
        tesoro = 0.0

    try:
        s = _reservas_netas_sdds()
        brutas_api = float(_bcra_ultimo(BCRA_RESERVAS_ID)["valor"])
        if abs(s["brutas"] - brutas_api) / brutas_api > 0.15:
            raise ValueError(f"brutas SDDS {s['brutas']:.0f} vs API {brutas_api:.0f} divergen >15%")
        # "a secas" = estricto, sumando de vuelta lo que el mercado no computa como
        # pasivo del BCRA: depósitos del Tesoro + Bopreal a 12m (bucket 3m-1año de II.1).
        bopreal = abs(s.get("bopreal_12m", 0.0))
        netas = s["netas"] + tesoro + bopreal
        if not -40000 < netas < 40000:
            raise ValueError(f"netas fuera de rango plausible: {netas:.0f}")
        return {
            "valor": round(netas, 0),
            "unidad": "Millones de USD",
            "fuente": "BCRA — Planilla SDDS y Balance Consolidado",
            # la planilla trae dd/mm/yy; a ISO como el resto de las fichas
            "fecha_dato": datetime.strptime(s["fecha"], "%d/%m/%y").date().isoformat(),
            "netas_sdds_estricto": round(s["netas"], 0),
            "depositos_tesoro": round(tesoro, 0),
            "bopreal_12m": round(bopreal, 0),
            "reservas_brutas": round(s["brutas"], 0),
            "drenaje_prestamos_dep": round(s["prestamos_dep"], 0),
            "drenaje_swaps": round(s["swaps"], 0),
            "drenaje_repos": round(s["repos"], 0),
            "metodo": "sdds+tesoro+bopreal",
            "desactualizado": False,
        }
    except Exception as e:
        _warn("reservas_bcra (SDDS, cae a config)", e)

    try:  # FALLBACK: brutas API − drenajes Sección II del último SDDS (config) + Tesoro
        brutas = float(_bcra_ultimo(BCRA_RESERVAS_ID)["valor"])
        fecha  = _bcra_ultimo(BCRA_RESERVAS_ID)["fecha"]
        with open(RESERVAS_PASIVOS_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        estricto = brutas - float(cfg["drenajes_seccion_ii"])
        return {
            "valor": round(estricto + tesoro, 0),
            "unidad": "Millones de USD",
            "fuente": "BCRA — Planilla SDDS y Balance Consolidado",
            "fecha_dato": fecha,
            "netas_sdds_estricto": round(estricto, 0),
            "depositos_tesoro": round(tesoro, 0),
            "reservas_brutas": round(brutas, 0),
            "drenajes_actualizado": cfg.get("actualizado"),
            "metodo": "config_fallback",
            "desactualizado": False,
        }
    except Exception as e:
        _warn("reservas_bcra", e)
        return None


def fetch_badlar() -> dict | None:
    try:
        ultimo = _bcra_ultimo(BCRA_BADLAR_ID)
        return {
            "valor": round(float(ultimo["valor"]), 2),
            "unidad": "% anual",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_BADLAR_ID}",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("badlar", e)
        return None


def _idc_componentes(badlar_nivel: float, ipc_m: float,
                     dep_t: float, dep_p: float, pre_t: float, pre_p: float) -> tuple:
    """Componentes del IdC para un par de meses consecutivos (t vs t-1).
    Devuelve (precio, volumen, asignacion, idc). Única fuente de la fórmula:
    la usan tanto el indicador en vivo (fetch_idc) como la serie histórica.
      • badlar_nivel: BADLAR (% anual) del mes t.
      • ipc_m:        inflación % mensual del mes t.
      • dep/pre:      depósitos y préstamos privados (stock) en t y t-1."""
    tem    = ((1.0 + badlar_nivel / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0
    precio = 1.0 + (tem - ipc_m) / 100.0
    volumen = (dep_t / dep_p) / (1.0 + ipc_m / 100.0)
    r_t = pre_t / dep_t
    r_p = pre_p / dep_p
    asignacion = (1.0 - r_t) / (1.0 - r_p)
    idc = itcm.indice_capacidad_prestable(precio, volumen, asignacion)
    return precio, volumen, asignacion, idc


def _idc_serie_mensual(meses_hist: int = 18) -> list:
    """Serie histórica mensual del IdC, con la misma fórmula que el indicador en
    vivo (_idc_componentes) pero sobre stocks de fin de mes. Cada punto compara el
    mes con el anterior. Devuelve [(YYYY-MM, idc)] ascendente."""
    n = meses_hist + 3
    badlar = _bcra_fin_de_mes(BCRA_BADLAR_ID, n)
    dep    = _bcra_fin_de_mes(BCRA_DEP_PRIV_ID, n)
    pre    = _bcra_fin_de_mes(BCRA_PREST_PRIV_ID, n)
    ipc    = _ipc_indice_mensual(meses_hist + 5)
    comunes = set(badlar) & set(dep) & set(pre) & set(ipc)
    out = []
    for ym in sorted(comunes):
        prev = _ym_shift(ym, -1)
        if prev not in comunes:
            continue
        ipc_m = (ipc[ym] / ipc[prev] - 1) * 100
        *_, idc = _idc_componentes(badlar[ym], ipc_m, dep[ym], dep[prev], pre[ym], pre[prev])
        out.append((ym, round(idc, 4)))
    return out


def fetch_idc() -> dict | None:
    """Índice de Capacidad Prestable (doc "260626 aportes"). Reemplaza a la tasa
    en la dimensión de financiamiento. Tres componentes mensuales (~1,0):
      • Precio:     1 + tasa REAL mensual de la BADLAR (TEM − IPC m/m).
      • Volumen:    ratio mensual de depósitos privados deflactados por IPC.
      • Asignación: ratio mensual de holgura prestable (1−R_t)/(1−R_{t-1}),
                    R = préstamos/depósitos del sector privado.
    Índice >1,02 = expansión (verde); 0,98-1,02 = neutro (amarillo); <0,98 = rojo."""
    try:
        ipc_m  = _ipc_mensual()
        badlar = float(_bcra_ultimo(BCRA_BADLAR_ID)["valor"])
        dep = _bcra_par(BCRA_DEP_PRIV_ID)
        pre = _bcra_par(BCRA_PREST_PRIV_ID)
        precio, volumen, asignacion, idc = _idc_componentes(
            badlar, ipc_m, dep["actual"], dep["anterior"], pre["actual"], pre["anterior"])
        i_real = (precio - 1.0) * 100.0
        semaforo = "verde" if idc > 1.02 else "amarillo" if idc >= 0.98 else "rojo"
        return {
            "valor": round(idc, 4),
            "unidad": "Índice (~1,0)",
            "fuente": ("BCRA — BADLAR (var. 7), depósitos privados (var. 100) y "
                       "préstamos privados (var. 117) + IPC INDEC"),
            "fecha_dato": dep["fecha"],
            "componentes": {
                "precio": round(precio, 4),
                "volumen": round(volumen, 4),
                "asignacion": round(asignacion, 4),
            },
            "badlar_real_mensual": round(i_real, 2),
            "semaforo": semaforo,
            "desactualizado": False,
        }
    except Exception as e:
        _warn("idc", e)
        return None


def fetch_emae_ia() -> dict | None:
    try:
        data = _indec_serie(INDEC_EMAE_IA_ID, limit=2)
        val  = data[0][1]  # ya es variación i.a. en decimal (0.0187 = 1.87%)
        return {
            "valor": round(float(val) * 100, 2),
            "unidad": "% i.a.",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("emae_ia", e)
        return None


def fetch_saldo_comercial_12m() -> dict | None:
    """Saldo 12m = expo − impo de las series ICA (74.3, frescas a ~2 meses),
    con la composición que necesita la regla automática del ITCM (¿el superávit
    viene de exportar más o de importar menos?). La serie de saldo directa
    (164.3) tiene ~14 meses de rezago y queda solo como fallback."""
    try:
        expo = _indec_serie(INDEC_EXPO_ICA_ID, limit=26)
        impo = _indec_serie(INDEC_IMPO_ICA_ID, limit=26)
        # Alinear por fecha: usar solo los meses presentes en ambas series.
        impo_por_fecha = {f: v for f, v in impo if v is not None}
        comunes = [(f, v, impo_por_fecha[f]) for f, v in expo
                   if v is not None and f in impo_por_fecha]
        if len(comunes) < 24:
            raise ValueError(f"ICA: solo {len(comunes)} meses comunes expo/impo (se necesitan 24)")
        ex  = [e for _, e, _ in comunes]
        im  = [i for _, _, i in comunes]
        expo_12, expo_prev = sum(ex[:12]), sum(ex[12:24])
        impo_12, impo_prev = sum(im[:12]), sum(im[12:24])
        return {
            "valor": round(expo_12 - impo_12, 0),
            "unidad": "Millones de USD (acum. 12 meses)",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": comunes[0][0],
            "desactualizado": False,
            "expo_12m": round(expo_12, 0),
            "impo_12m": round(impo_12, 0),
            "expo_var_ia": round((expo_12 / expo_prev - 1) * 100, 1),
            "impo_var_ia": round((impo_12 / impo_prev - 1) * 100, 1),
            "expo_delta_12m": round(expo_12 - expo_prev, 0),
            "impo_delta_12m": round(impo_12 - impo_prev, 0),
        }
    except Exception as e:
        _warn("saldo_comercial_12m (ICA)", e)
    try:
        data   = _indec_serie(INDEC_SALDO_COM_ID, limit=13)
        meses  = [row[1] for row in data[:12] if row[1] is not None]
        total  = sum(meses)
        return {
            "valor": round(total, 0),
            "unidad": "Millones de USD (acum. 12 meses)",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("saldo_comercial_12m", e)
        return None


def fetch_recaudacion() -> dict | None:
    """Variación INTERANUAL REAL de la recaudación: la variación nominal i.a.
    deflactada por el IPC del mismo período (doc "260626 aportes"). Aísla la
    recuperación genuina de los ingresos del efecto inflacionario."""
    try:
        rec = _indec_yoy(INDEC_RECAUDACION_ID)   # nominal i.a.
        ipc = _indec_yoy(INDEC_IPC_ID)           # IPC i.a. (mismo período)
        var_real = ((1.0 + rec["var_ia"] / 100.0) / (1.0 + ipc["var_ia"] / 100.0) - 1.0) * 100.0
        return {
            "valor": round(var_real, 2),
            "unidad": "% i.a. real",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": rec["fecha"],
            "var_ia_nominal": round(rec["var_ia"], 2),
            "ipc_ia": round(ipc["var_ia"], 2),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("recaudacion", e)
        return None


def fetch_itcrm_serie() -> list:
    """Serie mensual del ITCRM oficial del BCRA (base 17-dic-2015=100), de la
    planilla ITCRMSerie.xlsx (hoja de promedios mensuales). Devuelve
    [(YYYY-MM-01, valor)] ordenado ascendente. 100% de dato oficial."""
    import io, openpyxl
    r = requests.get(BCRA_ITCRM_URL, headers=HTTP_HEADERS, timeout=60, verify=False)
    r.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    ws = wb[ITCRM_SHEET_MENSUAL]
    serie = []
    for fecha, itcrm, *_ in ws.iter_rows(min_row=3, values_only=True):
        if fecha is None or not isinstance(itcrm, (int, float)):
            continue  # saltea encabezados y notas al pie
        ym = fecha.date().isoformat() if hasattr(fecha, "date") else str(fecha)[:10]
        serie.append((ym, round(float(itcrm), 2)))
    if not serie:
        raise ValueError("ITCRM: sin datos numéricos en la planilla del BCRA")
    return serie


def fetch_tcrm() -> dict | None:
    try:  # BCRA ITCRM oficial (vigente, base 17-dic-2015=100)
        ym, val = fetch_itcrm_serie()[-1]
        return {
            "valor": val,
            "unidad": "Índice (base dic-2015=100)",
            "fuente": "BCRA — Índice de Tipo de Cambio Real Multilateral (ITCRM)",
            "fecha_dato": ym,
            "desactualizado": False,
        }
    except Exception as e:
        _warn("tcrm (ITCRM BCRA, cae a INDEC discontinuada)", e)
    try:  # FALLBACK: serie INDEC 116.3_TCRMA — discontinuada en dic-2024
        data = _indec_serie(INDEC_TCRM_ID, limit=2)
        return {
            "valor": round(float(data[0][1]), 2),
            "unidad": "Índice (base 2010=100)",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": data[0][0],
            "desactualizado": True,
        }
    except Exception as e:
        _warn("tcrm", e)
        return None


def fetch_rem_ipc_12m() -> dict | None:
    try:
        ultimo = _bcra_ultimo(BCRA_REM_IPC_ID)
        return {
            "valor": round(float(ultimo["valor"]), 1),
            "unidad": "% anual esperado",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_REM_IPC_ID}",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("rem_ipc_12m", e)
        return None


def fetch_idm() -> dict | None:
    """Índice de Desequilibrio Monetario (IDM): brecha i.a. real entre la oferta
    amplia de pesos privados (M3 privado) y la demanda transaccional (M2 privado).
    Positivo = excedente de pesos sobre la demanda → presión sobre la brecha;
    negativo = remonetización genuina traccionada por la demanda real. Ver
    _idm_serie_mensual para la metodología (real-real interanual)."""
    try:
        serie = _idm_serie_mensual()
        if not serie:
            raise ValueError("sin meses con interanual disponible")
        ym, gap, m3_real_ia, m2_real_ia = serie[-1]
        return {
            "valor": gap,
            "unidad": "pp (brecha i.a. real)",
            "fuente": ("BCRA (M3 privado = circulante var. 17 + depósitos privados var. 100; "
                       "M2 privado transaccional var. 197) + IPC INDEC"),
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
            "m3_real_ia": m3_real_ia,
            "m2_real_ia": m2_real_ia,
        }
    except Exception as e:
        _warn("idm", e)
        return None


# ── Capítulo Inversión: IAI (físico) e ICIP (digital) ─────────────────────────

# Pesos del IAI. DNRPA no expone histórico de patentamientos comerciales, así que
# arrancan en None y se ACUMULAN mes a mes (data/macro/patentamientos_comerciales.json);
# hasta tener 13 meses (primer interanual), el IAI usa solo ISAC + BK renormalizados.
IAI_PESOS_CON_PAT = {"isac": 0.55, "bk_importados": 0.30, "patentamientos_comerciales": 0.15}
IAI_PESOS_SIN_PAT = {"isac": 0.65, "bk_importados": 0.35}
ICIP_PESOS = {"servicios_tech": 0.57, "productividad": 0.43}


def _cargar_patentamientos() -> dict:
    if PATENTAMIENTOS_PATH.exists():
        return json.loads(PATENTAMIENTOS_PATH.read_text(encoding="utf-8"))
    return {}


def actualizar_patentamientos_comerciales() -> dict:
    """Descarga el CSV de inscripciones iniciales de la DNRPA (solo expone el mes
    corriente) y UPSERTA el conteo de patentamientos comerciales del mes completo
    en el store JSON. Es la única vía de construir la serie: la fuente no publica
    histórico a nivel registro. Devuelve el store actualizado."""
    store = _cargar_patentamientos()
    try:
        meta = requests.get(DNRPA_CKAN_PACKAGE, params={"id": DNRPA_INSCRIP_AUTOS},
                            headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False).json()["result"]
        url = next(x["url"] for x in meta["resources"] if x.get("format", "").upper() == "CSV")
        import csv as _csv, io as _io, collections as _col
        txt = requests.get(url, headers=HTTP_HEADERS, timeout=90, verify=False)
        txt.encoding = "utf-8"
        rows = list(_csv.reader(_io.StringIO(txt.text)))
        hdr = rows[0]
        ti = hdr.index("automotor_tipo_descripcion")
        fi = hdr.index("fecha_inscripcion_inicial")
        por_mes = _col.Counter()
        for r in rows[1:]:
            if len(r) <= max(ti, fi) or not r[fi]:
                continue
            if any(k in r[ti].upper() for k in PATENTAMIENTOS_COMERCIALES_KEYS):
                por_mes[r[fi][:7]] += 1
        if por_mes:
            ym, cnt = por_mes.most_common(1)[0]   # mes COMPLETO = el dominante del archivo
            store[ym] = cnt
            PATENTAMIENTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
            PATENTAMIENTOS_PATH.write_text(
                json.dumps(store, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    except Exception as e:
        _warn("patentamientos_comerciales (acumulación DNRPA)", e)
    return store


def _patentamientos_ia() -> dict | None:
    """Variación i.a. de los patentamientos comerciales SI ya hay 13 meses
    acumulados con el mismo mes del año anterior; si no, None (el IAI lo omite)."""
    store = _cargar_patentamientos()
    meses = sorted(store)
    if len(meses) < 13:
        return None
    ym = meses[-1]
    prev = _ym_shift(ym, -12)
    if prev not in store or not store[prev]:
        return None
    return {"var_ia": (store[ym] / store[prev] - 1) * 100, "fecha": ym,
            "meses_acumulados": len(meses)}


def fetch_iai() -> dict | None:
    """IAI — Índice Anticipador de Inversión (físico/tradicional). Promedio
    ponderado de variaciones i.a.: ISAC construcción + bienes de capital
    importados (+ patentamientos comerciales cuando haya histórico acumulado).
    Mayor = inversión expandiéndose. Bandas en itcm.BANDAS_ITCM['iai']."""
    try:
        isac = _indec_yoy(INDEC_ISAC_NIVEL_ID)["var_ia"]
        bk   = _indec_yoy(INDEC_BK_IMPO_ID)
        pat  = _patentamientos_ia()
        componentes = {"isac": round(isac, 1), "bk_importados": round(bk["var_ia"], 1)}
        if pat is not None:
            w = IAI_PESOS_CON_PAT
            componentes["patentamientos_comerciales"] = round(pat["var_ia"], 1)
            valor = w["isac"]*isac + w["bk_importados"]*bk["var_ia"] + w["patentamientos_comerciales"]*pat["var_ia"]
            nota = f"ISAC 55% · BK importados 30% · patentamientos comerciales 15% ({pat['meses_acumulados']} meses)"
        else:
            w = IAI_PESOS_SIN_PAT
            valor = w["isac"]*isac + w["bk_importados"]*bk["var_ia"]
            nota = "ISAC 65% · BK importados 35% (patentamientos comerciales: acumulando histórico DNRPA)"
        return {
            "valor": round(valor, 2),
            "unidad": "% i.a. ponderado",
            "fuente": "INDEC — ISAC (construcción) + ICA (bienes de capital importados)",
            "fecha_dato": bk["fecha"],
            "desactualizado": False,
            "componentes": componentes,
            "pesos_nota": nota,
        }
    except Exception as e:
        _warn("iai", e)
        return None


def fetch_icip() -> dict | None:
    """ICIP — Índice de Capitalización Inteligente y Productividad (digital/
    intangible). Promedio ponderado de variaciones i.a.: pagos al exterior de
    servicios de informática (software/cloud/IA) + productividad laboral
    (IPI/empleo). Mayor = la economía se digitaliza más rápido. Banda 'icip'."""
    try:
        svc  = _indec_yoy(INDEC_SVC_INFO_ID)
        prod = _indec_ratio_yoy(INDEC_IPI_NIVEL_ID, INDEC_EMPLEO_EIL_ID)
        valor = ICIP_PESOS["servicios_tech"]*svc["var_ia"] + ICIP_PESOS["productividad"]*prod["var_ia"]
        return {
            "valor": round(valor, 2),
            "unidad": "% i.a. ponderado",
            "fuente": "INDEC — servicios de informática (balanza) + IPI/empleo (productividad)",
            "fecha_dato": svc["fecha"],
            "desactualizado": False,
            "componentes": {
                "servicios_tech": round(svc["var_ia"], 1),
                "productividad": round(prod["var_ia"], 1),
            },
            "pesos_nota": "Servicios tech 57% · productividad (IPI/empleo) 43%",
        }
    except Exception as e:
        _warn("icip", e)
        return None


def _iai_serie_mensual(meses: int = 24) -> list:
    """Serie histórica del IAI (sin patentamientos: solo ISAC + BK, 65/35).
    Devuelve [(YYYY-MM, valor)] ascendente."""
    isac = _indec_nivel_mensual(INDEC_ISAC_NIVEL_ID, limit=meses + 16)
    bk   = _indec_nivel_mensual(INDEC_BK_IMPO_ID, limit=meses + 16)
    comunes = set(isac) & set(bk)
    out = []
    for ym in sorted(comunes):
        p = _ym_shift(ym, -12)
        if p in comunes and isac[p] and bk[p]:
            si = (isac[ym] / isac[p] - 1) * 100
            bi = (bk[ym] / bk[p] - 1) * 100
            out.append((ym, round(0.65 * si + 0.35 * bi, 2)))
    return out[-meses:]


def _icip_serie_mensual(meses: int = 24) -> list:
    """Serie histórica del ICIP (servicios tech + productividad IPI/empleo).
    Devuelve [(YYYY-MM, valor)] ascendente."""
    svc = _indec_nivel_mensual(INDEC_SVC_INFO_ID, limit=meses + 16)
    ipi = _indec_nivel_mensual(INDEC_IPI_NIVEL_ID, limit=meses + 16)
    emp = _indec_nivel_mensual(INDEC_EMPLEO_EIL_ID, limit=meses + 16)
    prod = {ym: ipi[ym] / emp[ym] for ym in set(ipi) & set(emp)}
    comunes = set(svc) & set(prod)
    out = []
    for ym in sorted(comunes):
        p = _ym_shift(ym, -12)
        if p in svc and p in prod and svc[p] and prod[p]:
            sv = (svc[ym] / svc[p] - 1) * 100
            pr = (prod[ym] / prod[p] - 1) * 100
            out.append((ym, round(0.57 * sv + 0.43 * pr, 2)))
    return out[-meses:]


def fetch_prestamos_privados() -> dict | None:
    try:
        result = _bcra_variacion_m(BCRA_PRESTAMOS_ID)
        return {
            "valor": result["var_m"],
            "unidad": "% mensual nominal",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_PRESTAMOS_ID}",
            "fecha_dato": result["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("prestamos_privados", e)
        return None


def fetch_credito_privado() -> dict | None:
    """Variación interanual REAL de los préstamos al sector privado (BCRA
    var. 26), deflactada por el IPC (INDEC). ADR-0022: mide el crédito
    REALIZADO — información distinta de la capacidad prestable del IdC (que
    usa tasas y ratios) — y es la única señal no redundante de los viejos
    indicadores de contexto (badlar/préstamos/base/TC quedan ocultos: son
    insumos de IdC, IDM y TCRM)."""
    try:
        detalle = _bcra_detalle(BCRA_PRESTAMOS_ID, dias=400)   # desc
        ultimo = detalle[0]
        objetivo = datetime.fromisoformat(ultimo["fecha"]) - timedelta(days=365)
        base = min(detalle, key=lambda d: abs(
            (datetime.fromisoformat(d["fecha"]) - objetivo).days))
        if abs((datetime.fromisoformat(base["fecha"]) - objetivo).days) > 12:
            raise ValueError("sin dato de préstamos ~365 días atrás")
        nominal = float(ultimo["valor"]) / float(base["valor"]) - 1.0
        ipc = _indec_yoy(INDEC_IPC_ID)["var_ia"] / 100.0
        real = ((1.0 + nominal) / (1.0 + ipc) - 1.0) * 100.0
        return {
            "valor": round(real, 1),
            "unidad": "% i.a. real",
            "fuente": "BCRA (préstamos al sector privado, var. 26) + IPC INDEC",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
            "nominal_ia": round(nominal * 100.0, 1),
            "detalle_txt": (f"nominal {str(round(nominal * 100.0, 1)).replace('.', ',')}% i.a. "
                            f"deflactado por IPC i.a. — crédito realizado, no capacidad (IdC)"),
        }
    except Exception as e:
        _warn("credito_privado", e)
        return None


def fetch_base_monetaria() -> dict | None:
    try:
        result = _bcra_variacion_m(BCRA_BASE_MON_ID)
        return {
            "valor": result["var_m"],
            "unidad": "% mensual nominal",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_BASE_MON_ID}",
            "fecha_dato": result["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("base_monetaria", e)
        return None


def fetch_tc_mayorista() -> dict | None:
    try:
        result = _bcra_variacion_m(BCRA_TC_MAYOR_ID)
        return {
            "valor": result["var_m"],
            "unidad": "% mensual",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_TC_MAYOR_ID}",
            "fecha_dato": result["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("tc_mayorista", e)
        return None


# ── Scoring (ITCM — Paramétrica CIGOB mayo 2026) ──────────────────────────────

AJUSTES_PATH = PROJECT_DIR / "data" / "macro" / "ajustes_itcm.json"


def calcular_itcm_cinturon(indicadores: dict) -> dict | None:
    """ITCM 0-100 (ver scripts/itcm.py) sobre los indicadores del índice.
    Ajustes: primero la regla automática del saldo comercial (composición
    expo/impo), luego los overrides manuales del analista vigentes para el
    mes corriente (data/macro/ajustes_itcm.json), que pisan lo automático.

    El REM se puntúa por su EQUIVALENTE MENSUAL (raíz 12), no por el nivel
    anual, para bandearlo con la misma escala mensual del IPC."""
    ajustes = {}
    auto_saldo = itcm.ajuste_automatico_saldo(indicadores.get("saldo_comercial_12m", {}))
    if auto_saldo:
        ajustes["saldo_comercial_12m"] = auto_saldo
    periodo = datetime.now().strftime("%Y-%m")
    ajustes.update(itcm.cargar_ajustes(AJUSTES_PATH, periodo))
    valores = {nombre: indicadores.get(nombre, {}).get("valor")
               for nombre in itcm.BANDAS_ITCM}
    rem = valores.get("rem_ipc_12m")
    valores["rem_ipc_12m"] = itcm.rem_mensual_equivalente(rem) if rem is not None else None
    return itcm.calcular_itcm(valores, ajustes)


def anotar_indicadores(indicadores: dict, resultado: dict | None) -> None:
    """Marca cada indicador con su rol en el ITCM: los del índice llevan
    puntaje, dimensión y peso efectivo; el resto queda como contexto."""
    por_indicador = {}
    if resultado:
        for dkey, dim in resultado["dimensiones"].items():
            for ikey, info in dim["indicadores"].items():
                por_indicador[ikey] = {
                    "en_indice": True,
                    "dimension": dkey,
                    "puntaje_itcm": info["puntaje_aplicado"],
                    "puntaje_banda": info["puntaje_banda"],
                    "peso_efectivo": info["peso_efectivo"],
                }
    for nombre, ind in indicadores.items():
        if nombre in por_indicador:
            ind.update(por_indicador[nombre])
        else:
            ind["en_indice"] = nombre in itcm.BANDAS_ITCM  # del índice pero sin dato
            if nombre in itcm.INDICADORES_CONTEXTO:
                ind["en_indice"] = False


def calcular_score(indicadores: dict) -> float:
    """Tensión 0-10 del cinturón, derivada del ITCM: (100 − ITCM) / 10.
    Sin ningún indicador del índice disponible, devuelve 5.0 (neutro)."""
    resultado = calcular_itcm_cinturon(indicadores)
    return itcm.tension_de_itcm(resultado["valor"]) if resultado else 5.0


def anotar_rem_mensual(indicadores: dict) -> None:
    """Expone en el indicador REM el equivalente mensual con que se lo puntúa
    (transparencia: el valor mostrado es el nivel anual, pero la banda usa el
    equivalente mensual, comparable al IPC)."""
    rem = indicadores.get("rem_ipc_12m")
    if not rem or rem.get("valor") is None:
        return
    mensual = itcm.rem_mensual_equivalente(rem["valor"])
    rem["equivalente_mensual"] = round(mensual, 2)
    rem["nota_scoring"] = (
        f"Puntuado por su equivalente mensual (raíz 12): {round(mensual, 2)}% "
        f"mensual, en la misma escala que el IPC."
    )


def main() -> None:
    cache_anterior         = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})

    # Acumular el mes corriente de patentamientos comerciales (DNRPA no expone
    # histórico): cada corrida upserta un mes en el store que alimenta al IAI.
    actualizar_patentamientos_comerciales()

    frescos: dict = {}
    frescos_count = 0

    for nombre, fetcher in [
        ("ipc_total",          fetch_ipc),
        ("reservas_bcra",      fetch_reservas_netas),
        ("idc",                fetch_idc),
        ("badlar",             fetch_badlar),
        ("emae_ia",            fetch_emae_ia),
        ("saldo_comercial_12m", fetch_saldo_comercial_12m),
        ("recaudacion",        fetch_recaudacion),
        ("tcrm",               fetch_tcrm),
        ("rem_ipc_12m",        fetch_rem_ipc_12m),
        ("idm",                fetch_idm),
        ("iai",                fetch_iai),
        ("icip",               fetch_icip),
        ("credito_privado",    fetch_credito_privado),
        ("prestamos_privados", fetch_prestamos_privados),
        ("base_monetaria",     fetch_base_monetaria),
        ("tc_mayorista",       fetch_tc_mayorista),
    ]:
        resultado = fetcher()
        if resultado is not None and resultado.get("valor") is not None:
            frescos[nombre] = resultado
            frescos_count  += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    resultado = calcular_itcm_cinturon(frescos)
    anotar_indicadores(frescos, resultado)
    anotar_rem_mensual(frescos)
    score   = itcm.tension_de_itcm(resultado["valor"]) if resultado else 5.0
    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "itcm":         resultado,
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
