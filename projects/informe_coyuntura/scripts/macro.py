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
from statistics import fmean, pstdev

sys.path.insert(0, str(Path(__file__).parent))
import comarb
import desequilibrio_monetario
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
# Secretaría de Finanzas — planillas anuales con TODAS las colocaciones de deuda
# (hojas Letras/Bonos). Los nombres de archivo cambian en cada actualización, así
# que se resuelven leyendo los enlaces de esta página (ver _colocaciones_urls).
FINANZAS_COLOCACIONES_URL = "https://www.argentina.gob.ar/economia/finanzas/deudapublica/colocacionesdedeuda"

# INDEC — series IDs verificados en datos.gob.ar
INDEC_IPC_ID         = "148.3_INIVELNAL_DICI_M_26"     # IPC total nacional mensual
INDEC_EMAE_IA_ID     = "143.3_ICE_SERVIA_2004_A_25"    # EMAE variación i.a. mensual (base 2004)
INDEC_IPI_ID         = "453.1_SERIE_ORIGNAL_0_0_14_46"  # IPI manufacturero nivel general, serie original
INDEC_SALDO_COM_ID   = "164.3_SOTALTAL_0_0_8"          # Saldo comercial total mensual (M USD) — FALLBACK, ~14 meses de rezago
INDEC_EXPO_ICA_ID    = "74.3_IET_0_M_16"               # ICA exportaciones totales mensual (M USD)
INDEC_IMPO_ICA_ID    = "74.3_IIT_0_M_25"               # ICA importaciones totales mensual (M USD)
# Recaudación DGI mensual (M ARS): impuestos INTERNOS —IVA doméstico, Ganancias,
# créditos y débitos, internos—, sin aduana ni seguridad social (ADR-0127).
# Reemplaza a la recaudación TOTAL (172.3_TL_RECAION_M_0_0_17, que sigue abajo
# como referencia) porque el indicador mide la base imponible y la actividad
# (ADR-0072), y el total mezcla eso con la decisión política sobre el comercio
# exterior: en 2026 la aduana cae 15-37% real por el recorte de retenciones
# mientras la base doméstica está plana. La descomposición cierra exacta:
# DGI + DGA + Seguridad Social = total.
INDEC_RECAUDACION_ID = "172.3_SOTAL_DDGI_M_0_0_12"     # Recaudación DGI mensual (M ARS)
INDEC_RECAUDACION_TOTAL_ID = "172.3_TL_RECAION_M_0_0_17"  # total — contexto de la card
INDEC_RECAUDACION_DGA_ID   = "172.3_SOTAL_DDGA_M_0_0_12"  # aduana — contexto de la card
# IMIG (Informe Mensual de Ingresos y Gastos, Sec. de Hacienda): resultado
# PRIMARIO del Sector Público Nacional, mensual en millones de pesos.
HACIENDA_RESULTADO_PRIMARIO_ID = "452.3_RESULTADO_RIO_0_M_18_54"
INDEC_TCRM_ID        = "116.3_TCRMA_0_M_36"            # Tipo de Cambio Real Multilateral (base 2010=100)

# EMAE — apertura sectorial, base 2004 (dataset "Estimador Mensual de Actividad
# Económica (EMAE). Apertura Sectorial"). Son los 15 SECTORES de actividad; el
# dataset trae una 16ª serie, "Subsidios netos" (11.3_IF_2004_M_25), que NO se
# incluye porque es un componente de la agregación (impuestos netos de
# subsidios), no una actividad económica. Publican el mismo mes que el EMAE
# agregado, así que la difusión no agrega rezago (ADR-0124).
INDEC_EMAE_SECTORES = {
    "11.3_ISOM_2004_M_39":  "Agricultura, ganadería, caza y silvicultura",
    "11.3_VIPAA_2004_M_5":  "Pesca",
    "11.3_ISD_2004_M_26":   "Explotación de minas y canteras",
    "11.3_VMASD_2004_M_23": "Industria manufacturera",
    "11.3_ITC_2004_M_21":   "Electricidad, gas y agua",
    "11.3_VMATC_2004_M_12": "Construcción",
    "11.3_AGCS_2004_M_41":  "Comercio mayorista, minorista y reparaciones",
    "11.3_P_2004_M_20":     "Hoteles y restaurantes",
    "11.3_EMC_2004_M_25":   "Transporte, almacenamiento y comunicaciones",
    "11.3_IM_2004_M_25":    "Intermediación financiera",
    "11.3_SEGA_2004_M_48":  "Inmobiliarias, empresariales y alquiler",
    "11.3_C_2004_M_60":     "Administración pública, defensa y seguridad social",
    "11.3_CMMR_2004_M_10":  "Enseñanza",
    "11.3_HR_2004_M_24":    "Servicios sociales (salud)",
    "11.3_TAC_2004_M_60":   "Servicios comunitarios",
}

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
# ADR-0251: la variable 26 es `MEyML` — pesos Y moneda extranjera valuada en
# pesos. El titular usa la 117 (`ML`, sólo pesos): con la 26, una devaluación
# revaluaba la cartera en dólares y el indicador lo publicaba como crecimiento
# real del crédito. Las otras dos se publican como desglose, no como titular.
BCRA_PRESTAMOS_ID     = 117  # Préstamos al sector privado EN PESOS (millones ARS)
BCRA_PRESTAMOS_USD_ID = 125  # ...en moneda extranjera, en millones de USD
BCRA_PRESTAMOS_ME_ID  = 126  # ...esa misma cartera valuada en pesos
BCRA_PRESTAMOS_TOT_ID = 26   # pesos + moneda extranjera valuada en pesos
BCRA_BASE_MON_ID    = 15   # Base monetaria (millones ARS)
BCRA_TC_MAYOR_ID    = 5    # Tipo de cambio mayorista de referencia (ARS/USD)
BCRA_DEP_PRIV_ID        = 100  # Depósitos privados en pesos — insumo IdC e IDM
BCRA_PREST_PRIV_ID      = 117  # Préstamos otorgados al sector privado — insumo IdC
BCRA_CIRCULANTE_ID      = 17   # Billetes y monedas en poder del público — insumo M3 privado (IDM)
BCRA_M2_PRIV_ID         = 197  # M2 transaccional del sector privado (agregado, NO una demanda estimada — ADR-0254)
DESEQUILIBRIO_MAX_REZAGO_MESES = 2   # Mercado de Cambios publica con hasta dos meses de rezago

HTTP_TIMEOUT = 30
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}

logging.basicConfig(level=logging.WARNING, format="%(message)s")

CINTURON = "macro"
INDICADORES_ESPERADOS = [
    "ipc_total", "reservas_bcra", "idc", "badlar",
    "emae_ia", "emae_difusion", "ipi_manufacturero", "saldo_comercial_12m",
    "recaudacion", "tcrm",
    "rem_ipc_12m", "idm", "desequilibrio_monetario", "iai", "icip",
    "credito_privado", "prestamos_privados", "base_monetaria", "tc_mayorista",
    "costo_financiamiento_tesoro", "resultado_primario",
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


def _purgar_indicadores_obsoletos(indicadores: dict) -> None:
    indicadores.pop("dolarizacion_depositos", None)
    # Reemplazado por desequilibrio_monetario (ADR-0192): medía la misma fuga
    # cambiaria, desde la misma planilla del BCRA.
    indicadores.pop("presion_dolarizacion", None)


def _warn(indicador: str, err: Exception) -> None:
    print(f"[WARN] {CINTURON}.{indicador}: {err}. Usando cache.")


def _sellar(resultado: dict) -> dict:
    """Sella el momento en que este valor se obtuvo de la fuente en vivo (ADR-0191).

    Se aplica SOLO a resultados frescos. El carry-forward hace
    `{**anterior, "desactualizado": True}`, asi que arrastra el sello viejo
    intacto: es esa fecha que deja de moverse la que mide hace cuanto que la
    fuente no contesta. `fecha_dato` no sirve para eso — en las series anuales
    no se mueve aunque el fetch ande perfecto.
    """
    return {**resultado, "obtenido_en": datetime.now().isoformat(timespec="seconds")}


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
    """Serie mensual de la brecha de crecimiento real M3–M2 privados (IDM).

    Brecha entre el crecimiento interanual REAL del M3 privado (circulante en
    poder del público + depósitos privados, var. 17 + 100) y el del M2 privado
    transaccional (var. 197), ambos deflactados por el IPC. Los dos son
    agregados monetarios; la brecha no es oferta menos demanda (ADR-0254).

    Versión real-real interanual: corrige el sesgo inflacionario y la
    estacionalidad del aguinaldo de la propuesta original (m/m nominal-real).
    Positivo = el agregado amplio crece más rápido que el transaccional, o sea
    que los pesos se van a plazo y a instrumentos remunerados en vez de quedarse
    en transacciones.

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


def _desequilibrio_monetario_serie_mensual(
    meses_hist: int = 36,
) -> list[dict]:
    """Serie común del desequilibrio monetario para el titular y el backfill."""
    return desequilibrio_monetario.obtener_serie(
        meses_hist=meses_hist,
        fetch_bcra_fin_mes=_bcra_fin_de_mes,
    )


# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch_ipc() -> dict | None:
    try:
        data = _indec_serie(INDEC_IPC_ID, limit=2)
        actual, anterior = data[0][1], data[1][1]
        var = (actual / anterior - 1) * 100 if anterior else None
        return {
            "valor": round(var, 2) if var is not None else None,
            "unidad": "% mensual",
            "fuente": "INDEC — IPC nacional (vía datos.gob.ar)",
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


def _mes_balance(sh, row: int) -> tuple[int, int] | None:
    """Año y mes de una fila del balance BCRA: la columna 0 codifica el período
    como AAAA.MM (ej. 2026.05 = mayo de 2026); None si la celda no es numérica."""
    valor = sh.cell_value(row, 0)
    if not isinstance(valor, (int, float)):
        return None
    anio = int(valor)
    return anio, round((valor - anio) * 100)


def _tesoro_deposits_usd(mes: str | None = None) -> float:
    """Depósitos del Tesoro en USD en el BCRA (M USD), del Balance Consolidado
    oficial (balbcrhis.xls): col 'Dep. del gobierno en ME' / TC / 1000 (el balance
    está en miles de pesos). Si se indica ``YYYY-MM``, usa el último balance de ese
    mes para mantener la misma fecha de corte que la planilla SDDS."""
    import xlrd  # ya en requirements (1.2.0)
    r = requests.get(BCRA_BALANCE_URL, headers=HTTP_HEADERS, timeout=60, verify=False)
    r.raise_for_status()
    sh = xlrd.open_workbook(file_contents=r.content).sheet_by_name("B.C.R.A.")
    filas = [
        row for row in range(27, sh.nrows)
        if isinstance(sh.cell_value(row, BAL_COL_RESERVAS), (int, float))
        and sh.cell_value(row, BAL_COL_RESERVAS)
    ]
    if mes:
        anio_objetivo, mes_objetivo = map(int, mes.split("-"))
        filas = [
            row for row in filas
            if _mes_balance(sh, row) == (anio_objetivo, mes_objetivo)
        ]
    if not filas:
        raise ValueError(f"balance BCRA: sin fila válida para {mes or 'último dato'}")
    fila = filas[-1]
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
    Ambos componentes usan el mismo mes de cierre. Validación: brutas SDDS vs API
    ±15%; si el PDF SDDS no parsea → FALLBACK (brutas API − drenajes Sección II
    del último SDDS del config) + Tesoro. Si el balance no aporta el mismo mes de
    cierre, el indicador falla y el colector conserva el último cache como desactualizado.
    Nunca se publica una reserva neta parcial como dato fresco."""
    try:
        s = _reservas_netas_sdds()
        fecha_sdds = datetime.strptime(s["fecha"], "%d/%m/%y")
        try:
            tesoro = _tesoro_deposits_usd(fecha_sdds.strftime("%Y-%m"))
        except Exception as e:
            _warn("reservas_bcra (Tesoro del mes SDDS)", e)
            return None
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
            "fecha_dato": fecha_sdds.date().isoformat(),
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
        ultimo = _bcra_ultimo(BCRA_RESERVAS_ID)
        brutas = float(ultimo["valor"])
        fecha = ultimo["fecha"]
        with open(RESERVAS_PASIVOS_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        if str(cfg.get("actualizado", ""))[:7] != fecha[:7]:
            raise ValueError(
                "fallback de reservas: drenajes y reservas brutas "
                "corresponden a meses distintos"
            )
        tesoro = _tesoro_deposits_usd(fecha[:7])
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
            "fuente": "BCRA — BADLAR bancos privados (API monetarias)",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("badlar", e)
        return None


IDC_MESES_HIST = 120        # ventana de descarga: ~10 años (la muestra usable
                            # arranca 13 meses después del inicio de las fuentes)
IDC_MIN_MESES = 60          # mínimo de historia para que los z-scores signifiquen algo
_IDC_BASE_MEMO: dict = {}   # memo por corrida: indicador y serie comparten la
                            # misma descarga (3 series BCRA de ~2.500 filas c/u)


def _idc_base_mensual(meses_hist: int = IDC_MESES_HIST) -> dict:
    """Los tres NIVELES mensuales del IdC rediseñado (ADR-0028) sobre toda la
    historia disponible: {YYYY-MM: (tasa_real_pp, dep_real_ia_pct, holgura_pct)}.
      • tasa_real:   TEM de la BADLAR de fin de mes − IPC m/m del mes (pp).
      • dep_real_ia: depósitos privados fin de mes, variación i.a. REAL (%) —
                     la interanual absorbe la estacionalidad (aguinaldos, cosecha).
      • holgura:     (1 − préstamos/depósitos) × 100 de fin de mes (%). Es un
                     NIVEL acotado: no explota cuando R→1 (ese era el defecto
                     del ratio mensual del diseño original).
    El primer mes usable queda 12 meses después del inicio común de las fuentes
    (IPC nacional dic-2016 → muestra desde 2018)."""
    if meses_hist in _IDC_BASE_MEMO:
        return _IDC_BASE_MEMO[meses_hist]
    badlar = _bcra_fin_de_mes(BCRA_BADLAR_ID, meses_hist)
    dep    = _bcra_fin_de_mes(BCRA_DEP_PRIV_ID, meses_hist)
    pre    = _bcra_fin_de_mes(BCRA_PREST_PRIV_ID, meses_hist)
    ipc    = _ipc_indice_mensual(meses_hist + 6)
    out = {}
    for ym in sorted(set(badlar) & set(dep) & set(pre) & set(ipc)):
        prev1, prev12 = _ym_shift(ym, -1), _ym_shift(ym, -12)
        if prev1 not in ipc or prev12 not in dep or prev12 not in ipc:
            continue
        tem = ((1.0 + badlar[ym] / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0
        ipc_m = (ipc[ym] / ipc[prev1] - 1.0) * 100.0
        dep_real = ((dep[ym] / dep[prev12]) / (ipc[ym] / ipc[prev12]) - 1.0) * 100.0
        holgura = (1.0 - pre[ym] / dep[ym]) * 100.0
        out[ym] = (tem - ipc_m, dep_real, holgura)
    _IDC_BASE_MEMO[meses_hist] = out
    return out


def _idc_z_series(base: dict) -> dict:
    """{YYYY-MM: (z_precio, z_volumen, z_asignacion, idc)}: cada nivel
    estandarizado contra TODA la muestra (media 0, desvío 1 — ventana expansiva,
    recalculada en cada corrida) y combinado 30/40/30 (itcm.IDC_PESOS).
    z = 0 es el mes histórico típico; +1 σ ≈ percentil 84."""
    if len(base) < IDC_MIN_MESES:
        raise ValueError(f"IdC: historia insuficiente para z-scores ({len(base)} meses)")
    stats = [(fmean(c), pstdev(c)) for c in zip(*base.values())]
    if any(sd == 0 for _, sd in stats):
        raise ValueError("IdC: desvío nulo en un componente")
    out = {}
    for ym, niveles in base.items():
        z = [round((v - mu) / sd, 2) for v, (mu, sd) in zip(niveles, stats)]
        out[ym] = (*z, round(itcm.indice_capacidad_prestable(*z), 2))
    return out


def _idc_serie_mensual(meses_hist: int = 18) -> list:
    """Serie mensual del IdC (z compuesto, ADR-0028): últimos `meses_hist`
    puntos de la serie estandarizada sobre toda la historia. [(YYYY-MM, σ)] asc."""
    zs = _idc_z_series(_idc_base_mensual())
    return [(ym, z[3]) for ym, z in sorted(zs.items())][-meses_hist:]


def fetch_idc() -> dict | None:
    """Índice de Capacidad Prestable REDISEÑADO (ADR-0028, supersede la forma
    del doc "260626 aportes" — conserva sus tres conceptos). Tres NIVELES
    mensuales, cada uno estandarizado contra su propia historia (z-score,
    muestra 2018→hoy) y combinados 30/40/30:
      • precio:     tasa real mensual de la BADLAR (TEM − IPC m/m), en nivel.
      • volumen:    depósitos privados, variación i.a. real.
      • asignación: holgura prestable 1 − préstamos/depósitos, en nivel.
    Se publica en desvíos estándar (σ): 0 = mes histórico típico. Semáforo:
    > +0,5 σ expansión (verde) · ±0,5 σ neutro (amarillo) · < −0,5 σ (rojo).
    El mes publicado es el último con IPC cerrado (sin nowcast del deflactor)."""
    try:
        base = _idc_base_mensual()
        zs = _idc_z_series(base)
        ym = max(zs)
        zp, zv, za, z = zs[ym]
        tasa_real, dep_real, holgura = base[ym]
        # Nombre de campo `banda_idc`, no `semaforo`: este es un semáforo de 3
        # colores propio del IDC (por z-score, ajeno al motor paramétrico),
        # y colisionaba de nombre con el semáforo de 4 colores que publica
        # publicar.py._semaforos sobre CADA indicador (ADR-0181). Antes de
        # este rename, publicar.py leía este campo para armar
        # aporte_input_txt del propio idc ANTES de que _semaforos lo
        # pisara — funcionaba por orden de ejecución, no por diseño.
        banda_idc = "verde" if z > 0.5 else "amarillo" if z >= -0.5 else "rojo"
        return {
            "valor": z,
            "unidad": "σ vs. su historia",
            "fuente": ("BCRA — BADLAR (var. 7), depósitos privados (var. 100) y "
                       "préstamos privados (var. 117) + IPC INDEC"),
            "fecha_dato": f"{ym}-01",
            "componentes": {"precio": zp, "volumen": zv, "asignacion": za},
            "niveles": {"tasa_real_pp": round(tasa_real, 2),
                        "dep_real_ia_pct": round(dep_real, 1),
                        "holgura_pct": round(holgura, 1)},
            "ventana": f"{min(zs)} → {max(zs)} ({len(zs)} meses)",
            "badlar_real_mensual": round(tasa_real, 2),
            "banda_idc": banda_idc,
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
            "fuente": "INDEC — EMAE (vía datos.gob.ar)",
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("emae_ia", e)
        return None


def _emae_sectores_niveles(limit: int = 300) -> dict:
    """{id_serie: {YYYY-MM: nivel}} de los 15 sectores del EMAE.

    UNA sola llamada con los 15 ids (la API los acepta separados por coma): 15
    requests sueltos serían 15 golpes a datos.gob.ar por corrida.

    El orden de las columnas se lee del `meta` de la respuesta, NO del orden en
    que se pidieron. Hoy la API los devuelve alineados, pero nada del contrato
    lo garantiza, y un desalineo silencioso asignaría la variación de un sector
    a otro sin que ningún gate lo note.
    """
    ids = list(INDEC_EMAE_SECTORES)
    params = {"ids": ",".join(ids), "format": "json", "limit": limit, "sort": "desc"}
    r = requests.get(INDEC_SERIES_BASE, params=params,
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    payload = r.json()

    columnas = [m["field"]["id"] for m in payload["meta"] if "field" in m]
    if sorted(columnas) != sorted(ids):
        raise ValueError(
            f"la API devolvió {len(columnas)} series y se pidieron {len(ids)}")

    niveles = {sid: {} for sid in columnas}
    for fila in payload["data"]:
        ym = fila[0][:7]
        for sid, val in zip(columnas, fila[1:]):
            if val is not None:
                niveles[sid][ym] = float(val)
    return niveles


def _emae_difusion_por_mes(limit: int = 300) -> tuple[dict, dict]:
    """Difusión sectorial del EMAE, mes a mes.

    Devuelve ({YYYY-MM: % de sectores creciendo i.a.},
              {YYYY-MM: {nombre_sector: % i.a.}}).

    La comparación es INTERANUAL y por CALENDARIO (mismo mes del año anterior),
    no por posición en la lista: las series son originales, sin desestacionalizar,
    así que el interanual es la única variación que no arrastra estacionalidad.
    Un mes sólo se emite si los 15 sectores tienen dato — una difusión calculada
    sobre 12 sectores no es comparable con una calculada sobre 15.
    """
    niveles = _emae_sectores_niveles(limit=limit)
    meses = sorted(set().union(*(set(s) for s in niveles.values())))

    difusion, detalle = {}, {}
    for ym in meses:
        previo = f"{int(ym[:4]) - 1}{ym[4:]}"
        variaciones = {}
        for sid, serie in niveles.items():
            if ym in serie and previo in serie and serie[previo]:
                variaciones[INDEC_EMAE_SECTORES[sid]] = round(
                    (serie[ym] / serie[previo] - 1) * 100, 2)
        if len(variaciones) != len(INDEC_EMAE_SECTORES):
            continue
        crecen = sum(1 for v in variaciones.values() if v > 0)
        difusion[ym] = round(crecen / len(variaciones) * 100, 2)
        detalle[ym] = variaciones
    return difusion, detalle


def fetch_emae_difusion() -> dict | None:
    """% de los 15 sectores del EMAE que crecen interanualmente (ADR-0124).

    Responde lo que el agregado no puede: si el crecimiento es generalizado o
    está concentrado en pocos sectores. En may-2026 el EMAE marca +0,2% i.a.
    —prácticamente nada— mientras 8 de 15 sectores crecen, traccionados por
    minas y canteras (+15,7%) y energía (+8,0%), con la industria en −5,6% y
    el comercio en −4,3%.
    """
    try:
        difusion, detalle = _emae_difusion_por_mes(limit=30)
        ym = max(difusion)
        variaciones = detalle[ym]
        crecen = sorted((v, n) for n, v in variaciones.items() if v > 0)
        caen = sorted((v, n) for n, v in variaciones.items() if v <= 0)
        return {
            "valor": difusion[ym],
            "unidad": "% de sectores en crecimiento i.a.",
            "fuente": "INDEC — EMAE apertura sectorial (vía datos.gob.ar)",
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
            "sectores_totales": len(variaciones),
            "sectores_crecen": len(crecen),
            "sectores_por_variacion": [
                {"sector": n, "var_ia": v} for v, n in sorted(
                    ((v, n) for n, v in variaciones.items()), reverse=True)
            ],
            "detalle_txt": (
                f"{len(crecen)} de {len(variaciones)} sectores crecen"
                + (f" · lidera {crecen[-1][1]} ({str(crecen[-1][0]).replace('.', ',')}%)"
                   if crecen else "")
                + (f" · el que más cae es {caen[0][1]} "
                   f"({str(caen[0][0]).replace('.', ',')}%)" if caen else "")),
        }
    except Exception as e:
        _warn("emae_difusion", e)
        return None


def _ipi_ia_por_mes() -> dict:
    """{YYYY-MM: variación i.a. suavizada a 3 meses} del IPI manufacturero.

    Se suaviza a propósito: la variación i.a. del IPI original salta ±9 pp de un
    mes al siguiente (feriados móviles, días hábiles, paradas de planta), un
    ruido que no dice nada sobre el estado de la industria. El promedio de tres
    meses baja el desvío de los cambios mensuales de 6,2 a 2,5 pp sin agregar
    rezago apreciable — la serie sigue siendo interanual, sólo deja de vibrar.

    La ventana se arma por CALENDARIO, no por posición en la lista: si el INDEC
    saltea un mes, ese promedio no se emite en vez de mezclar tres
    observaciones que abarcan cuatro meses o más. Por la misma razón los dos
    primeros meses de la serie histórica quedan afuera: no tienen tres meses
    completos detrás y promediarlos sobre una ventana parcial daba un valor
    calculado con menos datos que el resto, sin nada que lo señalara. Ambas
    cosas las detectó una auditoría de código (18-jul-2026).
    """
    filas = _indec_serie(INDEC_IPI_ID, limit=5000)
    idx = {f[:7]: v for f, v in filas if v}

    def _mes_menos(ym: str, n: int) -> str:
        total = int(ym[:4]) * 12 + (int(ym[5:7]) - 1) - n
        return f"{total // 12}-{total % 12 + 1:02d}"

    ia = {ym: (val / idx[_mes_menos(ym, 12)] - 1) * 100
          for ym, val in idx.items() if idx.get(_mes_menos(ym, 12))}

    suavizada = {}
    for ym in sorted(ia):
        ventana = [ia.get(_mes_menos(ym, k)) for k in (0, 1, 2)]
        if all(v is not None for v in ventana):     # ventana completa o nada
            suavizada[ym] = round(sum(ventana) / 3, 2)
    return suavizada


def fetch_ipi_manufacturero() -> dict | None:
    """Segunda señal de actividad junto al EMAE (ADR-0076): producción
    industrial manufacturera, variación i.a. suavizada a tres meses.

    Publica un mes ANTES que el EMAE, así que además de dejar de colgar la
    dimensión de un único dato, acorta el rezago con el que se lee actividad."""
    try:
        serie = _ipi_ia_por_mes()
        ym = max(serie)
        return {
            "valor": serie[ym],
            "unidad": "% i.a. (promedio 3 meses)",
            "fuente": "INDEC — IPI manufacturero, nivel general (vía datos.gob.ar)",
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
        }
    except Exception as e:
        _warn("ipi_manufacturero", e)
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
            "fuente": "INDEC — ICA, intercambio comercial (vía datos.gob.ar)",
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
            "fuente": "INDEC — ICA, intercambio comercial (vía datos.gob.ar)",
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("saldo_comercial_12m", e)
        return None


def _real_ia_pm3(nom: dict, ipc: dict) -> dict:
    """{YYYY-MM: % i.a. real} de una serie nominal deflactada por IPC."""
    out = {}
    for ym in sorted(nom):
        prev = _ym_shift(ym, -12)
        if ym in ipc and prev in nom and prev in ipc and nom[prev] and ipc[prev]:
            out[ym] = ((nom[ym] / nom[prev]) / (ipc[ym] / ipc[prev]) - 1.0) * 100.0
    return out


def fetch_recaudacion() -> dict | None:
    """Base imponible REAL desestacionalizada: 100 = promedio del 4T-2023.

    Suma la recaudación de impuestos INTERNOS de la Nación —IVA doméstico,
    Ganancias, créditos y débitos, no el total (ADR-0127)— y la de los sistemas
    de la Comisión Arbitral, que es el Impuesto sobre los Ingresos Brutos de los
    contribuyentes de Convenio Multilateral más los regímenes de retención
    provinciales. El indicador no mide viabilidad fiscal sino la base imponible y
    la actividad (ADR-0072): dejar la aduana afuera evita confundir eso con la
    decisión política sobre el comercio exterior, y sumar lo provincial cubre una
    porción de la base que la serie nacional no ve.

    Hasta el 29-jul-2026 la métrica era la variación interanual real con promedio
    móvil de 3 meses (ADR-0029). Se cambia porque teniendo el dato MENSUAL la
    interanual desperdicia resolución y arrastra la base de hace un año: con el
    dato de junio de 2026 informaba +3,3% —«creciendo», contra un 2025 deprimido—
    mientras el nivel real dice 88,2, es decir 11,8% POR DEBAJO de la transición.
    Las dos son ciertas y la segunda es la que importa para un índice de tensión.

    El valor es el ÚLTIMO PUNTO de la misma serie que publica
    `descargar_series.fetch_recaudacion_real_serie`, calculada por
    `comarb.base_imponible_real_sa` — una sola implementación, así que card y
    serie no pueden divergir (G3 por construcción, como `apoyo_empresario`)."""
    try:
        nom = {r[0][:7]: r[1] for r in _indec_serie(INDEC_RECAUDACION_ID,
                                                    limit=comarb.LIMITE_MESES)
               if r[1] is not None}
        ipc = {r[0][:7]: r[1] for r in _indec_serie(INDEC_IPC_ID,
                                                    limit=comarb.LIMITE_MESES)
               if r[1] is not None}
        serie = comarb.base_imponible_real_sa(nom, ipc)
        if not serie:
            raise ValueError("recaudación: sin ventana suficiente para desestacionalizar")
        ultimo = max(serie)
        valor = serie[ultimo]

        prov = comarb.niveles_cacheados()
        aporte_prov = (100 * prov[ultimo] / (nom[ultimo] + prov[ultimo])
                       if ultimo in prov and ultimo in nom else None)
        # Texto público: coma decimal es-AR, igual que el resto del informe.
        cm = lambda x: f"{x:.1f}".replace(".", ",")
        previos = sorted(serie)[-4:-1]
        detalle = (f"La base imponible real está en {cm(valor)} sobre una base de 100 "
                   f"en el cuarto trimestre de 2023, es decir "
                   + (f"{cm(100 - valor)}% por debajo" if valor < 100
                      else f"{cm(valor - 100)}% por encima") + ". "
                   + "Meses previos: "
                   + " · ".join(f"{ym}: {cm(serie[ym])}" for ym in previos) + ".")
        if aporte_prov is not None:
            detalle += (f" Los impuestos provinciales del Convenio Multilateral aportan "
                        f"{cm(aporte_prov)}% de la base medida.")
        return {
            "valor": valor,
            "unidad": "índice (100 = 4T-2023)",
            "fuente": "Sec. Hacienda — recaudación DGI (vía datos.gob.ar) + "
                      "Comisión Arbitral del Convenio Multilateral",
            "fecha_dato": f"{ultimo}-01",
            "aporte_provincial_pct": None if aporte_prov is None else round(aporte_prov, 1),
            "detalle_txt": detalle,
            "desactualizado": False,
        }
    except Exception as e:
        _warn("recaudacion", e)
        return None


# ── Resultado primario del SPN (ADR-0072) ─────────────────────────────────────
# La dimensión se llama "viabilidad fiscal" pero su componente principal medía
# INGRESOS, no resultado: un gobierno puede sostener superávit con recaudación
# cayendo (bajando el gasto, o bajando impuestos a propósito) y el índice leía
# deterioro donde el programa registra cumplimiento. Este indicador mide el
# resultado.

def _superavit_sobre_recaudacion_12m() -> dict:
    """{YYYY-MM: resultado primario acumulado 12m / recaudación acumulada 12m, %}.

    Dos decisiones de método:
    - **Acumulado 12 meses**: el resultado primario mensual es brutalmente
      estacional (diciembre da déficit todos los años por aguinaldo y cierre;
      enero, superávit alto). Puntuar el mes suelto marcaría colapso fiscal cada
      diciembre.
    - **Normalizado por recaudación, no por PIB ni por IPC**: no hay PIB nominal
      mensual publicado, y deflactar por IPC sumaría un eslabón más a la cadena
      del deflactor (ya toca recaudación, crédito, IDM e IdC). El cociente contra
      la recaudación es adimensional y se lee solo: de cada peso que recauda el
      Estado, cuánto le sobra después de gastar, antes de intereses."""
    prim = {r[0][:7]: r[1] for r in _indec_serie(HACIENDA_RESULTADO_PRIMARIO_ID, limit=90)
            if r[1] is not None}
    # TOTAL explícito, no la constante del indicador de recaudación: acá el
    # denominador es "de cada peso que recauda el Estado", que incluye aduana y
    # seguridad social. Cuando ADR-0127 apuntó `recaudacion` a la DGI, esta
    # línea compartía la constante y el resultado primario habría pasado a
    # medirse contra una base 40% más chica sin que nada avisara.
    rec = {r[0][:7]: r[1] for r in _indec_serie(INDEC_RECAUDACION_TOTAL_ID, limit=90)
           if r[1] is not None}
    out = {}
    for ym in sorted(set(prim) & set(rec)):
        ventana = [_ym_shift(ym, -k) for k in range(11, -1, -1)]
        if not all(m in prim and m in rec for m in ventana):
            continue                       # ventana incompleta: no se imputa
        suma_rec = sum(rec[m] for m in ventana)
        if suma_rec <= 0:
            continue
        out[ym] = sum(prim[m] for m in ventana) / suma_rec * 100.0
    return out


def fetch_resultado_primario() -> dict | None:
    """Superávit (o déficit) primario del Sector Público Nacional acumulado 12
    meses, medido como porcentaje de la recaudación del mismo período."""
    try:
        serie = _superavit_sobre_recaudacion_12m()
        if not serie:
            raise ValueError("sin ventanas de 12 meses completas")
        ym = max(serie)
        valor = serie[ym]
        signo = "superávit" if valor >= 0 else "déficit"
        return {
            "valor": round(valor, 2),
            "unidad": "% de la recaudación (acum. 12 meses)",
            "fuente": "Sec. de Hacienda — IMIG (resultado primario) + recaudación (vía datos.gob.ar)",
            "fecha_dato": f"{ym}-01",
            "detalle_txt": (
                f"{ym}: {signo} primario de {abs(valor):.1f}% de la recaudación "
                f"acumulada de doce meses"
            ),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("resultado_primario", e)
        return None


# ── Costo real del financiamiento del Tesoro (ADR-0071) ───────────────────────
# Qué tasa REAL paga el Tesoro para colocar deuda en pesos en el mercado local.
# Es el precio del financiamiento soberano, que la dimensión no medía: reservas,
# IdC y crédito miden cantidad y condiciones de fondeo, no cuánto cuesta
# refinanciarse. El riesgo país queda FUERA del índice a propósito (es el
# validador externo del ITCM y su fuente no es oficial); esta serie mide la
# curva en pesos, que es donde el Tesoro efectivamente se financia hoy.

_COLOC_MEMO: dict = {}            # memo por corrida: las planillas pesan ~0,4 MB

_RE_TEM_CAP = re.compile(r"capitalizable\s*([\d,\.]+)\s*%")
_RE_FECHA_ARCH = re.compile(r"(\d{1,2})[-_](\d{1,2})[-_](\d{2,4})")


def _norm_txt(s) -> str:
    """Minúsculas sin acentos ni espacios repetidos (los encabezados de la
    planilla cambian de un año a otro: 'Cupón' vs 'Cupón/Ajuste de capital')."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _colocaciones_urls() -> dict:
    """{año: url} de las planillas de colocaciones de Finanzas. El nombre de
    archivo NO es estable (cambia en cada actualización), así que se resuelve
    leyendo los enlaces de la página. Si un año tiene varias versiones, gana la
    de fecha más reciente en el nombre."""
    r = requests.get(FINANZAS_COLOCACIONES_URL, timeout=40,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    mejores: dict = {}
    for href in re.findall(r'href="([^"]+\.xlsx?)"', r.text):
        nombre = href.rsplit("/", 1)[-1]
        m = _RE_FECHA_ARCH.search(nombre)
        if not m:
            continue
        d, mth, y = (int(x) for x in m.groups())
        if y < 100:
            y += 2000
        if not (2000 <= y <= 2100 and 1 <= mth <= 12 and 1 <= d <= 31):
            continue
        clave = (y, mth, d)
        if y not in mejores or clave > mejores[y][0]:
            url = href if href.startswith("http") else f"https://www.argentina.gob.ar{href}"
            mejores[y] = (clave, url)
    return {y: u for y, (_, u) in mejores.items()}


def _tem_capitalizable(cup: str) -> float | None:
    """TEM del cupón de una LECAP/BONCAP a tasa fija en pesos, o None.

    Sólo la tasa fija: `capitalizable "TAMAR TEM"` no trae número y queda
    afuera, igual que CER, dólar linked y cupón variable."""
    m = _RE_TEM_CAP.search(_norm_txt(cup))
    return float(m.group(1).replace(",", ".")) / 100.0 if m else None


# Un "mes" en la convención de Finanzas es 365/12 días, no 30, y el año es de
# 365 días, no de 360. Se determinó ajustando las dos bases contra las TIREA de
# corte publicadas en trece reaperturas (jul-2025 → ago-2026): con 365/12 y 365
# el error cuadrático medio es 0,09 pp; con 30 y 360 —la convención que se había
# supuesto— es 1,08 pp, y el desvío crece cuanto más corto es el plazo
# remanente. Ver ADR-0258.
_MES_DIAS = 365.0 / 12.0


def _tirea_de_fila(cup: str, emi, ven, col, precio: float) -> float | None:
    """TIREA (tasa efectiva ANUAL) **de corte** de una colocación en pesos.

    Es el rendimiento al que el Tesoro efectivamente colocó, que es lo que el
    indicador quiere medir: se descuenta el flujo del instrumento contra el
    precio de corte de ESA licitación.

        payoff = 1000 · (1 + TEM)^(días de vida / (365/12))     # capitalizable
        payoff = 1000                                           # a descuento
        TIREA  = (payoff / precio)^(365 / días al vencimiento) − 1

    **En una emisión nueva colocada a la par la fórmula devuelve exactamente
    `(1+TEM)^12 − 1`**, que es la TIREA que publica la Secretaría: con
    `precio = 1000` y `días al vencimiento = días de vida`, los exponentes se
    cancelan. Por eso no hay dos caminos ni hay que detectar la reapertura —
    hay una sola cuenta que en el caso a la par coincide con el dato publicado.

    Lo que había antes anualizaba el cupón (`(1+TEM)^12 − 1`) para TODA fila,
    también para las reaperturas. En una reapertura el cupón fija el flujo pero
    el precio determina el rendimiento, así que eso publicaba la tasa
    contractual del instrumento en vez del costo de la colocación. En la
    reapertura de la S30N6 del 15-jul-2026 (precio de corte $1.194) informaba
    31,37% donde la Secretaría publicó **25,59%**, y el indicador salía 5,80%
    real en vez de 4,13% (ADR-0258). No era un caso de borde: sobre las 177
    colocaciones a tasa fija en pesos desde 2023, 118 se colocaron fuera de la
    par, y ahí el cupón se desvía de la tasa de corte entre −30,5 y +29,2 pp.

    La convención de días no se supuso: mes de 365/12 días y año de 365 se
    ajustaron contra catorce TIREA de corte publicadas por la Secretaría
    (0,41 pp de error cuadrático medio; con mes de 30 y año de 360, 1,08 pp y
    creciendo cuanto más corto es el plazo remanente).

    ADR-0238 había elegido leer el cupón porque la reconstrucción de entonces
    estaba rota —capitalizaba por meses de calendario enteros— y dejó la
    reapertura anotada como limitación declarada. Esto la cierra.
    """
    tem = _tem_capitalizable(cup)
    norm = _norm_txt(cup)
    if tem is not None:
        dias_vida = (ven - emi).days
        if dias_vida <= 0:
            return None
        payoff = 1000.0 * (1.0 + tem) ** (dias_vida / _MES_DIAS)
    elif "a descuento" in norm or "cupon cero" in norm:
        payoff = 1000.0                  # LEDE/LETE: sin TEM, paga 1.000
    else:
        return None                      # CER, dólar linked, TAMAR: no comparable
    dias = (ven - col).days
    if dias <= 0 or precio <= 0:
        return None
    tirea = (payoff / precio) ** (365.0 / dias) - 1.0
    return tirea if 0.0 < tirea < 8.0 else None      # descarta filas corruptas


def _tirea_contractual(cup: str) -> float | None:
    """Tasa del CUPÓN anualizada, `(1+TEM)^12 − 1`. NO alimenta el indicador:
    existe como control y para que el inventario pueda mostrar las dos.

    Es la tasa que el instrumento paga por contrato desde su emisión, no la que
    el Tesoro pagó en esta licitación. Las dos coinciden —exactamente— cuando
    la colocación es una emisión nueva a la par, y ése es el invariante que
    prueba `test_a_la_par_la_tasa_de_corte_es_el_cupon_anualizado`. Cuando se
    separan, la que describe el costo de fondeo del mes es la de corte.
    """
    tem = _tem_capitalizable(cup)
    return (1.0 + tem) ** 12 - 1.0 if tem is not None else None


def _entrada_inventario(instrumento: str, cup: str, emi, col,
                        precio: float, ve: float, tirea: float) -> dict:
    """Una fila del inventario de colocaciones que viaja con la card.

    Lleva la tasa de corte **y** la contractual porque son distintas justo
    cuando importa: en una reapertura fuera de la par. Publicar el promedio sin
    esa distinción es lo que dejó pasar 31,37% en la S30N6 sin que nadie
    pudiera revisarlo (ADR-0258)."""
    contractual = _tirea_contractual(cup)
    return {
        "instrumento": instrumento,
        "tirea": round(tirea * 100.0, 2),
        "valor_efectivo": round(ve, 3),
        "colocacion": col.strftime("%Y-%m-%d"),
        "precio_corte": round(precio, 2),
        "reapertura": emi != col,
        "tirea_contractual": (None if contractual is None
                              else round(contractual * 100.0, 2)),
    }


def _tirea_mensual(anios: int = 2) -> dict:
    """{YYYY-MM: (tirea_ponderada, monto_adjudicado, n_colocaciones, inventario)}
    a partir de las planillas de Finanzas. Se pondera por valor efectivo
    adjudicado: una licitación chica no debe mover el promedio como una grande.

    La tasa de cada fila es la **TIREA de corte** —el rendimiento que fija el
    precio de esa licitación—, no la tasa contractual del instrumento: ver
    `_tirea_de_fila` y ADR-0258.

    El inventario —instrumento, TIREA de corte, tasa contractual, precio de
    corte y monto de cada colocación— viaja con el promedio para que la card
    pueda decir de qué salió el número. Una tasa promedio sin las colocaciones
    que la forman no es auditable: fue justamente lo que dejó pasar 32,17%
    durante meses, y después 31,37% en una reapertura."""
    if _COLOC_MEMO:
        return _COLOC_MEMO
    import io, openpyxl
    from collections import defaultdict
    urls = _colocaciones_urls()
    if not urls:
        raise ValueError("no se encontraron planillas de colocaciones")
    acc: dict = defaultdict(lambda: [0.0, 0.0, 0, []])
    for y in sorted(urls)[-anios:]:
        r = requests.get(urls[y], timeout=90, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
        for hoja in ("Letras", "Bonos"):
            if hoja not in wb.sheetnames:
                continue
            filas = list(wb[hoja].iter_rows(values_only=True))
            hdr, cols = None, {}
            for i, fila in enumerate(filas[:12]):
                celdas = {j: _norm_txt(c) for j, c in enumerate(fila) if c is not None}
                if not any("nombre del instrumento" in v for v in celdas.values()):
                    continue
                for j, v in celdas.items():
                    if "fecha de emis" in v:            cols["emi"] = j
                    elif v.startswith("vencimiento"):   cols["ven"] = j
                    elif v.startswith("cup"):           cols["cup"] = j
                    elif "moneda de origen" in v:       cols["mon"] = j
                    elif "fecha colocacion" in v:       cols["col"] = j
                    elif "valor efectivo" in v:         cols["ve"]  = j
                    elif "precio de emision" in v:      cols["pre"] = j
                hdr = i
                break
            if hdr is None or not {"emi", "ven", "cup", "mon", "col", "ve", "pre"} <= cols.keys():
                continue
            for fila in filas[hdr + 1:]:
                if not fila or fila[0] is None:
                    continue
                get = lambda k: fila[cols[k]] if cols[k] < len(fila) else None
                if get("mon") != "ARP" or not isinstance(get("cup"), str):
                    continue
                emi, ven, col = get("emi"), get("ven"), get("col")
                if not all(isinstance(x, datetime) for x in (emi, ven, col)):
                    continue
                try:
                    precio, ve = float(get("pre")), float(get("ve"))
                except (TypeError, ValueError):
                    continue
                if ve <= 0:
                    continue
                tirea = _tirea_de_fila(get("cup"), emi, ven, col, precio)
                if tirea is None:
                    continue
                a = acc[col.strftime("%Y-%m")]
                a[0] += tirea * ve
                a[1] += ve
                a[2] += 1
                a[3].append(_entrada_inventario(
                    str(fila[0]).strip(), get("cup"), emi, col, precio, ve, tirea))
    _COLOC_MEMO.update({ym: (s / w, w, n, inv)
                        for ym, (s, w, n, inv) in acc.items() if w > 0})
    return _COLOC_MEMO


def _rem_12m_por_mes(dias: int = 1200) -> dict:
    """{YYYY-MM: inflación esperada 12m %} del REM (BCRA)."""
    out = {}
    for punto in _bcra_detalle(BCRA_REM_IPC_ID, dias=dias):
        f = punto.get("fecha")
        v = punto.get("valor")
        if f and v is not None:
            out[str(f)[:7]] = float(v)
    return out


def fetch_costo_financiamiento_tesoro() -> dict | None:
    """Tasa REAL ex-ante que paga el Tesoro por colocar deuda en pesos: la TIREA
    **de corte** promedio ponderada de las colocaciones del mes, deflactada por
    la inflación esperada a 12 meses del REM. De corte, no contractual: en una
    reapertura el rendimiento lo fija el precio, no el cupón (ADR-0258). Se publica en TIREA (tasa efectiva anual), no
    en TNA: a tasas altas divergen mucho (dic-2023 fue 105% TNA = 169% TIREA).

    Es una variable de U INVERTIDA: la tasa real muy negativa es represión
    financiera (el Tesoro coloca licuando al ahorrista, dic-2023) y la muy alta
    es bola de nieve (la deuda crece más rápido que la economía, ago-2025). El
    óptimo está en positivo moderado."""
    try:
        tirea = _tirea_mensual()
        rem = _rem_12m_por_mes()
        comunes = sorted(ym for ym in tirea if ym in rem)
        if not comunes:
            raise ValueError("sin meses con colocaciones y REM simultáneos")
        ym = comunes[-1]
        t, monto, n, inventario = tirea[ym]
        esperada = rem[ym]
        real = ((1.0 + t) / (1.0 + esperada / 100.0) - 1.0) * 100.0
        return {
            "valor": round(real, 2),
            "unidad": "% real anual (TIREA vs. inflación esperada REM)",
            "fuente": "Sec. de Finanzas — colocaciones de deuda + BCRA (REM)",
            "fecha_dato": f"{ym}-01",
            "tirea_nominal": round(t * 100.0, 2),
            "inflacion_esperada": round(esperada, 1),
            "colocaciones": n,
            "inventario_colocaciones": inventario,
            "detalle_txt": (
                f"{ym}: TIREA de corte {t * 100:.1f}% en {n} colocación/es a tasa fija en pesos "
                f"contra inflación esperada {esperada:.1f}% → {real:+.1f}% real"
            ),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("costo_financiamiento_tesoro", e)
        return None


_ITCRM_FILAS_MEMO: list = []      # memo por corrida: ITCRM y bilaterales salen
                                  # de la MISMA planilla (una sola descarga)


def _itcrm_filas() -> list:
    """Filas (fecha_iso, ITCRM, Brasil, EEUU, China) de la planilla oficial
    ITCRMSerie.xlsx (hoja de promedios mensuales). Columnas de la hoja:
    Período · ITCRM · Brasil · Canadá · Chile · EEUU · México · Uruguay ·
    China · India — se toman los tres bilaterales más relevantes."""
    if _ITCRM_FILAS_MEMO:
        return _ITCRM_FILAS_MEMO
    import io, openpyxl
    r = requests.get(BCRA_ITCRM_URL, headers=HTTP_HEADERS, timeout=60, verify=False)
    r.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    ws = wb[ITCRM_SHEET_MENSUAL]
    for fila in ws.iter_rows(min_row=3, values_only=True):
        fecha, itcrm = fila[0], fila[1]
        if fecha is None or not isinstance(itcrm, (int, float)):
            continue  # saltea encabezados y notas al pie
        ym = fecha.date().isoformat() if hasattr(fecha, "date") else str(fecha)[:10]
        _ITCRM_FILAS_MEMO.append(
            (ym, round(float(itcrm), 2),
             round(float(fila[2]), 2) if isinstance(fila[2], (int, float)) else None,   # Brasil
             round(float(fila[5]), 2) if isinstance(fila[5], (int, float)) else None,   # EEUU
             round(float(fila[8]), 2) if isinstance(fila[8], (int, float)) else None))  # China
    if not _ITCRM_FILAS_MEMO:
        raise ValueError("ITCRM: sin datos numéricos en la planilla del BCRA")
    return _ITCRM_FILAS_MEMO


def fetch_itcrm_serie() -> list:
    """Serie mensual del ITCRM oficial (base 17-dic-2015=100).
    [(YYYY-MM-DD, valor)] ascendente. 100% de dato oficial."""
    return [(f[0], f[1]) for f in _itcrm_filas()]


def fetch_itcrm_bilateral(pais: str) -> list:
    """Serie mensual del ITCR BILATERAL oficial ('brasil' | 'eeuu' | 'china'),
    para el gráfico comparado del modal (así lo presenta el propio BCRA)."""
    idx = {"brasil": 2, "eeuu": 3, "china": 4}[pais]
    return [(f[0], f[idx]) for f in _itcrm_filas() if f[idx] is not None]


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
            "fuente": "INDEC — TCRM, serie discontinuada (vía datos.gob.ar)",
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
            "fuente": "BCRA — REM, expectativas de inflación (API monetarias)",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("rem_ipc_12m", e)
        return None


def fetch_idm() -> dict | None:
    """Brecha de crecimiento real M3–M2 privados, en puntos porcentuales.

    Es la diferencia entre cuánto crece en términos reales el M3 privado y
    cuánto crece el M2 privado transaccional, ambos interanuales. Positivo = el
    agregado amplio crece más rápido que el transaccional: los pesos se están
    yendo a plazo y a instrumentos remunerados en vez de quedarse en
    transacciones. Negativo = lo contrario.

    **No mide un exceso sobre la demanda de dinero** (ADR-0254). Hasta ago-2026
    se llamaba «Índice de Desequilibrio Monetario» y se leía como oferta menos
    demanda estimada; M2 es un agregado monetario, no una función de demanda.
    Estimar una demanda de dinero requiere elegir variables, forma funcional y
    validación, y nada de eso está acá. Lo que sí observa —dos agregados y su
    velocidad relativa— sigue siendo informativo, y así se llama ahora.

    Ver _idm_serie_mensual para la metodología (real-real interanual)."""
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


def _rezago_mensual(mes: str, hoy: date | None = None) -> int:
    """Meses calendario entre ``mes`` (YYYY-MM) y la fecha de referencia."""
    hoy = hoy or date.today()
    anio, numero_mes = map(int, mes.split("-"))
    return (hoy.year - anio) * 12 + hoy.month - numero_mes


def fetch_desequilibrio_monetario() -> dict | None:
    """Confianza en el peso: dolarización DENTRO del sistema x fuga FUERA de él."""
    try:
        serie = _desequilibrio_monetario_serie_mensual()
        if not serie:
            raise ValueError("sin meses con insumos completos")
        fila = serie[-1]
        rezago = _rezago_mensual(fila["mes"])
        if not 0 <= rezago <= DESEQUILIBRIO_MAX_REZAGO_MESES:
            raise ValueError(
                f'último mes {fila["mes"]} fuera del rezago admisible '
                f"(0-{DESEQUILIBRIO_MAX_REZAGO_MESES} meses)"
            )
        return {
            "valor": fila["tension"],
            "unidad": "pts de tensión (0-100)",
            "fuente": (
                "BCRA (M2 transaccional privado, circulante, depósitos privados "
                "en pesos y en dólares, y Mercado de Cambios)"
            ),
            "fecha_dato": f'{fila["mes"]}-01',
            "desactualizado": False,
            "puntaje_itcm": fila["puntaje_itcm"],
            # Los dos componentes y su posición en la matriz: los consume el
            # detalle de la card y la ficha metodológica.
            "componente_a": fila["componente_a"],
            "componente_b": fila["componente_b"],
            "posicion_a": fila["posicion_a"],
            "posicion_b": fila["posicion_b"],
            "celda": fila["celda"],
        }
    except Exception as e:
        _warn("desequilibrio_monetario", e)
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
        # ÚLTIMO MES COMÚN de ambos componentes (barrido 10/12): el ISAC corre
        # ~1 mes detrás del ICA — mezclar meses etiquetaba abril+mayo como
        # "mayo" y el titular difería del último punto de la serie. El
        # componente más fresco queda como provisorio en el detalle.
        isac_m = _indec_nivel_mensual(INDEC_ISAC_NIVEL_ID, limit=16)
        bk_m   = _indec_nivel_mensual(INDEC_BK_IMPO_ID, limit=16)
        comunes = [ym for ym in sorted(set(isac_m) & set(bk_m))
                   if _ym_shift(ym, -12) in isac_m and _ym_shift(ym, -12) in bk_m]
        if not comunes:
            raise ValueError("IAI: sin mes común con interanual disponible")
        ym = comunes[-1]
        isac = (isac_m[ym] / isac_m[_ym_shift(ym, -12)] - 1) * 100
        bk_ia = (bk_m[ym] / bk_m[_ym_shift(ym, -12)] - 1) * 100
        pat  = _patentamientos_ia()
        componentes = {"isac": round(isac, 1), "bk_importados": round(bk_ia, 1)}
        if pat is not None:
            w = IAI_PESOS_CON_PAT
            componentes["patentamientos_comerciales"] = round(pat["var_ia"], 1)
            valor = w["isac"]*isac + w["bk_importados"]*bk_ia + w["patentamientos_comerciales"]*pat["var_ia"]
            nota = f"ISAC 55% · BK importados 30% · patentamientos comerciales 15% ({pat['meses_acumulados']} meses)"
        else:
            w = IAI_PESOS_SIN_PAT
            valor = w["isac"]*isac + w["bk_importados"]*bk_ia
            nota = "ISAC 65% · BK importados 35% (patentamientos comerciales: acumulando histórico DNRPA)"
        # componente con dato más nuevo que el mes común → contexto provisorio
        fresco = ""
        ult_bk = max(bk_m)
        if ult_bk > ym and _ym_shift(ult_bk, -12) in bk_m:
            bk_prov = (bk_m[ult_bk] / bk_m[_ym_shift(ult_bk, -12)] - 1) * 100
            fresco = f" — BK {ult_bk} (provisorio, no puntúa): {bk_prov:+.1f}%"
        return {
            "valor": round(valor, 2),
            "unidad": "% i.a. ponderado",
            "fuente": "INDEC — ISAC (construcción) + ICA (bienes de capital importados)",
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
            "componentes": componentes,
            "pesos_nota": nota,
            "detalle_txt": (f"{round(valor, 1):+} % i.a. = ISAC {componentes['isac']:+}% · "
                            f"BK importados {componentes['bk_importados']:+}% "
                            f"(mes común: {ym}){fresco}"),
        }
    except Exception as e:
        _warn("iai", e)
        return None


def fetch_icip() -> dict | None:
    """ICIP — Pagos de servicios digitales y productividad. Promedio ponderado
    de variaciones i.a.: pagos al exterior de servicios de informática
    (software/cloud/IA) + productividad laboral (IPI/empleo). Mayor = la
    economía paga más por servicios digitales y/o produce más por ocupado.
    Banda 'icip'.

    **No es capitalización** (ADR-0253). Se llamaba «Índice de Capitalización
    Inteligente y Productividad» y el insumo principal no lo sostiene: en
    cuentas nacionales, los pagos transfronterizos por informática y nube son
    **consumo intermedio**, no formación bruta de capital. Pagar la licencia de
    la nube todos los meses no capitaliza a nadie. Medir inversión digital de
    verdad pide software, bases de datos y equipos TIC según cuentas nacionales;
    eso es un indicador nuevo, no un rótulo distinto sobre este."""
    try:
        # ÚLTIMO MES COMÚN de los TRES insumos (ADR-0030, mismo criterio de
        # borde irregular que IAI/recaudación/IdC): sin esto, el día que la
        # balanza de servicios publique antes que el IPI/EIL el titular
        # mezclaría meses. El insumo más fresco queda provisorio en el detalle.
        svc_m = _indec_nivel_mensual(INDEC_SVC_INFO_ID, limit=16)
        ipi_m = _indec_nivel_mensual(INDEC_IPI_NIVEL_ID, limit=16)
        eil_m = _indec_nivel_mensual(INDEC_EMPLEO_EIL_ID, limit=16)
        comunes = [ym for ym in sorted(set(svc_m) & set(ipi_m) & set(eil_m))
                   if all(_ym_shift(ym, -12) in s for s in (svc_m, ipi_m, eil_m))]
        if not comunes:
            raise ValueError("ICIP: sin mes común con interanual disponible")
        ym = comunes[-1]
        p = _ym_shift(ym, -12)
        svc_ia  = (svc_m[ym] / svc_m[p] - 1) * 100
        prod_ia = ((ipi_m[ym] / eil_m[ym]) / (ipi_m[p] / eil_m[p]) - 1) * 100
        valor = ICIP_PESOS["servicios_tech"]*svc_ia + ICIP_PESOS["productividad"]*prod_ia
        fresco = ""
        ult_svc = max(svc_m)
        if ult_svc > ym and _ym_shift(ult_svc, -12) in svc_m:
            svc_prov = (svc_m[ult_svc] / svc_m[_ym_shift(ult_svc, -12)] - 1) * 100
            fresco = f" — servicios tech {ult_svc} (provisorio, no puntúa): {svc_prov:+.1f}%"
        return {
            "valor": round(valor, 2),
            "unidad": "% i.a. ponderado",
            "fuente": "INDEC — servicios de informática (balanza) + IPI/empleo (productividad)",
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
            "componentes": {
                "servicios_tech": round(svc_ia, 1),
                "productividad": round(prod_ia, 1),
            },
            "pesos_nota": "Servicios tech 57% · productividad (IPI/empleo) 43%",
            "detalle_txt": (f"{round(valor, 1):+} % i.a. = servicios tech {round(svc_ia, 1):+}% · "
                            f"productividad {round(prod_ia, 1):+}% (mes común: {ym}){fresco}"),
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
            "fuente": "BCRA — préstamos al sector privado (API monetarias)",
            "fecha_dato": result["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("prestamos_privados", e)
        return None


def fetch_credito_privado() -> dict | None:
    """Variación interanual REAL de los préstamos al sector privado **en
    pesos** (BCRA var. 117), deflactada por el IPC (INDEC). ADR-0022: mide el
    crédito REALIZADO — información distinta de la capacidad prestable del IdC
    (que usa tasas y ratios) — y es la única señal no redundante de los viejos
    indicadores de contexto (badlar/préstamos/base/TC quedan ocultos: son
    insumos de IdC, IDM y TCRM).

    **Por qué en pesos y no el total** (ADR-0251): hasta ago-2026 el titular
    usaba la variable 26, que el BCRA declara `MEyML` — pesos y moneda
    extranjera **valuada en pesos**. Con esa serie, una devaluación revalúa la
    cartera en dólares sin que se preste un peso más, y el indicador lo publica
    como crecimiento real del crédito. En julio de 2026 eso daba +2,6% real
    cuando el crédito en pesos caía 1,5%: la cartera en dólares crecía 17,1%
    real medida en pesos y arrastraba el titular.

    El crédito en moneda extranjera no se descarta: se publica en el desglose,
    en dólares y en su valuación en pesos, que es donde se puede leer sin que
    se mezcle con el efecto cambiario."""
    try:
        # ÚLTIMO MES CON IPC CERRADO (ADR-0030): el titular anterior usaba el
        # préstamo diario al día deflactado con el IPC i.a. de dos meses atrás
        # (la peor deriva de la familia) y difería del último punto de la
        # serie. El dato diario fresco queda provisorio en el detalle.
        fin_mes = _bcra_fin_de_mes(BCRA_PRESTAMOS_ID, 16)
        ipc = _ipc_indice_mensual(20)
        comunes = [ym for ym in sorted(set(fin_mes) & set(ipc))
                   if _ym_shift(ym, -12) in fin_mes and _ym_shift(ym, -12) in ipc]
        if not comunes:
            raise ValueError("crédito privado: sin mes común con interanual disponible")
        ym = comunes[-1]
        p = _ym_shift(ym, -12)
        nominal = fin_mes[ym] / fin_mes[p] - 1.0
        deflactor = ipc[ym] / ipc[p]
        real = ((1.0 + nominal) / deflactor - 1.0) * 100.0
        coma = lambda x: str(round(x, 1)).replace(".", ",")

        # Desglose: la cartera en moneda extranjera, en su propia unidad y en
        # pesos, más el total. Van como contexto DENTRO de la card, no como
        # cards propias (ADR-0153: si no puntúa, no es card).
        desglose = {}
        try:
            usd = _bcra_fin_de_mes(BCRA_PRESTAMOS_USD_ID, 16)
            me = _bcra_fin_de_mes(BCRA_PRESTAMOS_ME_ID, 16)
            tot = _bcra_fin_de_mes(BCRA_PRESTAMOS_TOT_ID, 16)
            if ym in usd and p in usd:
                desglose["usd_ia"] = round((usd[ym] / usd[p] - 1.0) * 100.0, 1)
                desglose["usd_saldo_mm"] = round(usd[ym])
            if ym in me and p in me:
                desglose["me_en_pesos_ia_real"] = round(
                    ((me[ym] / me[p]) / deflactor - 1.0) * 100.0, 1)
            if ym in tot and p in tot:
                desglose["total_ia_real"] = round(
                    ((tot[ym] / tot[p]) / deflactor - 1.0) * 100.0, 1)
        except Exception as e:                            # noqa: BLE001
            _warn("credito_privado (desglose)", e)

        fresco = ""
        detalle = _bcra_detalle(BCRA_PRESTAMOS_ID, dias=400)   # desc
        ultimo = detalle[0]
        if ultimo["fecha"][:7] > ym:
            objetivo = datetime.fromisoformat(ultimo["fecha"]) - timedelta(days=365)
            base = min(detalle, key=lambda d: abs(
                (datetime.fromisoformat(d["fecha"]) - objetivo).days))
            if abs((datetime.fromisoformat(base["fecha"]) - objetivo).days) <= 12:
                nom_f = float(ultimo["valor"]) / float(base["valor"]) - 1.0
                real_f = ((1.0 + nom_f) / deflactor - 1.0) * 100.0
                fresco = (f" — al {ultimo['fecha']} (provisorio, no puntúa): "
                          f"{coma(real_f)}% real con deflactor de {ym}")
        contexto = ""
        if desglose.get("me_en_pesos_ia_real") is not None:
            contexto = (f" · aparte, la cartera en moneda extranjera "
                        f"{coma(desglose['me_en_pesos_ia_real'])}% real medida en pesos"
                        + (f" y {coma(desglose['usd_ia'])}% en dólares"
                           if desglose.get("usd_ia") is not None else "")
                        + (f"; los dos universos juntos, "
                           f"{coma(desglose['total_ia_real'])}% real"
                           if desglose.get("total_ia_real") is not None else ""))
        return {
            "valor": round(real, 1),
            "unidad": "% i.a. real (crédito en pesos)",
            "fuente": "BCRA (préstamos al sector privado en pesos, var. 117) + IPC INDEC",
            "fecha_dato": f"{ym}-01",
            "desactualizado": False,
            "nominal_ia": round(nominal * 100.0, 1),
            "moneda": "pesos",
            **desglose,
            "detalle_txt": (f"nominal {coma(nominal * 100.0)}% i.a. deflactado por IPC, "
                            f"sólo crédito EN PESOS — crédito realizado, no capacidad "
                            f"(IdC) (mes común: {ym}){contexto}{fresco}"),
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
            "fuente": "BCRA — base monetaria (API monetarias)",
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
            "fuente": "BCRA — TC mayorista A3500 (API monetarias)",
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
    expo/impo, ADR-0056), luego los overrides manuales del analista vigentes
    para el mes corriente (data/macro/ajustes_itcm.json), que pisan lo
    automático. No hay regla automática para el TCRM: se probó una y se
    descartó por doble conteo con la dimensión monetaria (ADR-0073, rechazado).

    El REM se puntúa por su EQUIVALENTE MENSUAL (raíz 12) y no por el nivel
    anual, pero de eso se encarga el motor: la transformación está declarada
    junto a las bandas (TRANSFORMACIONES_ITCM, ADR-0082) y acá se pasan los
    valores crudos."""
    ajustes = {}
    auto_saldo = itcm.ajuste_automatico_saldo(indicadores.get("saldo_comercial_12m", {}))
    if auto_saldo:
        ajustes["saldo_comercial_12m"] = auto_saldo
    periodo = datetime.now().strftime("%Y-%m")
    ajustes.update(itcm.cargar_ajustes(AJUSTES_PATH, periodo))
    valores = {nombre: indicadores.get(nombre, {}).get("valor")
               for nombre in itcm.BANDAS_ITCM}
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
    cache_anterior = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})
    _purgar_indicadores_obsoletos(indicadores_anteriores)

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
        ("emae_difusion",      fetch_emae_difusion),
        ("ipi_manufacturero",  fetch_ipi_manufacturero),
        ("saldo_comercial_12m", fetch_saldo_comercial_12m),
        ("recaudacion",        fetch_recaudacion),
        ("tcrm",               fetch_tcrm),
        ("rem_ipc_12m",        fetch_rem_ipc_12m),
        ("idm",                fetch_idm),
        ("desequilibrio_monetario", fetch_desequilibrio_monetario),
        ("iai",                fetch_iai),
        ("icip",               fetch_icip),
        ("credito_privado",    fetch_credito_privado),
        ("costo_financiamiento_tesoro", fetch_costo_financiamiento_tesoro),
        ("resultado_primario",  fetch_resultado_primario),
        ("prestamos_privados", fetch_prestamos_privados),
        ("base_monetaria",     fetch_base_monetaria),
        ("tc_mayorista",       fetch_tc_mayorista),
    ]:
        resultado = fetcher()
        if resultado is not None and resultado.get("valor") is not None:
            frescos[nombre] = _sellar(resultado)
            frescos_count  += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    _purgar_indicadores_obsoletos(frescos)
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
