"""
descargar_series.py — Descarga series históricas por cinturón a CSV
Salida: output/series/macro.csv | politica.csv | vida_cotidiana.csv | gestion.csv
Columnas: fecha, indicador, valor, fuente
"""
import sys
import csv
import io
import json
import re
import calendar
import requests
import urllib3
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import macro     # reutiliza el parser SDDS y las constantes del balance (reservas netas)
import gestion   # reutiliza el lector del sheet oficial del RIGI + fechas del BO
import politica  # reutiliza la reconstrucción histórica del Votómetro

sys.stdout.reconfigure(encoding="utf-8")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_DIR = Path("output/series")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HTTP_TIMEOUT = 20
HTTP_HEADERS = {"User-Agent": "CIGOB-InformeCoyuntura/1.0"}
INDEC_BASE   = "https://apis.datos.gob.ar/series/api/series/"
BCRA_BASE    = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"


def fetch_indec(series_id: str, limit: int = 48) -> list:
    r = requests.get(INDEC_BASE, params={"ids": series_id, "format": "json",
                     "limit": limit, "sort": "desc"},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return [[row[0], row[1]] for row in r.json()["data"] if row[1] is not None]


def fetch_indec_var_mensual(series_id: str, limit: int = 48) -> list:
    """Serie histórica de la variación m/m % de una serie INDEC de índices:
    (idx_t / idx_{t-1} − 1)×100. Misma fórmula que indec_series._var_mensual, para
    todo el histórico. Devuelve [[YYYY-MM-DD, var_pct]] ascendente."""
    data = sorted(fetch_indec(series_id, limit), key=lambda x: x[0])
    return [[f1, round((v1 / v0 - 1) * 100, 2)]
            for (f0, v0), (f1, v1) in zip(data, data[1:]) if v0]


def fetch_indec_x100(series_id: str, limit: int = 40) -> list:
    """Serie INDEC multiplicada por 100 (tasas EPH que la API devuelve en proporción,
    p. ej. 0,368 → 36,8 %). Misma transformación que la card. [[fecha, %]] ascendente."""
    return [[f, round(v * 100, 1)]
            for f, v in sorted(fetch_indec(series_id, limit), key=lambda x: x[0])]


def fetch_bcra(var_id: int, dias: int = 540) -> list:
    desde = (datetime.today() - timedelta(days=dias)).strftime("%Y-%m-%d")
    r = requests.get(f"{BCRA_BASE}/{var_id}", params={"desde": desde},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    detalle = r.json()["results"][0]["detalle"]
    return sorted([[d["fecha"], d["valor"]] for d in detalle],
                  key=lambda x: x[0], reverse=True)


def write_csv(nombre: str, rows: list):
    path = OUTPUT_DIR / f"{nombre}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["fecha", "indicador", "valor", "unidad", "fuente"])
        writer.writerows(rows)
    print(f"[OK] {path}  ({len(rows)} filas)")


def fetch_saldo_ica(limit: int = 48) -> list:
    """Saldo comercial mensual derivado de las series ICA (expo − impo).
    La serie de saldo directa (164.3_SOTALTAL_0_0_8) corre con ~14 meses de
    rezago; las ICA están frescas a ~2 meses (mismo criterio que macro.py)."""
    expo = fetch_indec("74.3_IET_0_M_16", limit)
    impo_por_fecha = dict(fetch_indec("74.3_IIT_0_M_25", limit))
    return [[fecha, round(valor - impo_por_fecha[fecha], 1)]
            for fecha, valor in expo if fecha in impo_por_fecha]


def _tesoro_por_mes() -> dict:
    """Mapa {YYYY-MM: dep. Tesoro en USD (M)} del Balance Consolidado del BCRA,
    para componer la serie histórica de reservas netas."""
    import xlrd
    r = requests.get(macro.BCRA_BALANCE_URL, headers=HTTP_HEADERS, timeout=60, verify=False)
    sh = xlrd.open_workbook(file_contents=r.content).sheet_by_name("B.C.R.A.")
    out = {}
    for row in range(27, sh.nrows):
        ym = sh.cell_value(row, 0)
        dep = sh.cell_value(row, macro.BAL_COL_DEP_GOB_ME)
        tc  = sh.cell_value(row, macro.BAL_COL_TC)
        if all(isinstance(x, (int, float)) for x in (ym, dep, tc)) and tc > 0:
            anio = int(ym); mes = round((ym - anio) * 100)
            if 1 <= mes <= 12:
                out[f"{anio}-{mes:02d}"] = dep / tc / 1000.0
    return out


def fetch_reservas_netas_serie(meses: int = 18) -> list:
    """Serie mensual de reservas NETAS "a secas" = SDDS estricto + dep. Tesoro +
    Bopreal 12m (la misma fórmula que el indicador en macro.py), parseando las
    últimas `meses` planillas SDDS. Salta los meses sin planilla parseable."""
    tesoro = _tesoro_por_mes()
    out = []
    y, m = datetime.today().year, datetime.today().month
    for _ in range(meses):
        nombre = f"temp{m:02d}{y % 100:02d}"
        try:
            r = requests.get(macro.SDDS_URL_BASE.format(nombre), headers=HTTP_HEADERS,
                             timeout=60, verify=False)
            if r.status_code == 200 and len(r.content) > 50000:
                s = macro._parse_sdds_content(r.content)
                if s and s["fecha"]:
                    _, mm, yy = s["fecha"].split("/")
                    ym = f"20{yy}-{mm}"
                    netas = s["netas"] + tesoro.get(ym, 0.0) + abs(s["bopreal_12m"])
                    out.append([f"20{yy}-{mm}-01", round(netas, 0)])
        except Exception:
            pass
        m -= 1
        if m == 0: m = 12; y -= 1
    return out


def fetch_tcrm_serie(meses: int = 18) -> list:
    """Serie mensual del ITCRM oficial del BCRA (base 17-dic-2015=100), de la
    planilla ITCRMSerie.xlsx. Reemplaza la serie INDEC 116.3_TCRMA, discontinuada
    en dic-2024. Devuelve los últimos `meses` como [[YYYY-MM-01, valor]]."""
    serie = macro.fetch_itcrm_serie()  # [(YYYY-MM-01, valor)] ascendente
    return [[ym, val] for ym, val in serie[-meses:]]


def fetch_idm_serie(meses: int = 18) -> list:
    """Serie mensual del Índice de Desequilibrio Monetario (brecha i.a. real entre
    M3 y M2 privado), con la misma fórmula que el indicador en macro.py. Devuelve
    los últimos `meses` como [[YYYY-MM-01, gap_pp]]."""
    serie = macro._idm_serie_mensual(meses_hist=meses + 4)  # [(YYYY-MM, gap, m3, m2)] asc.
    return [[f"{ym}-01", gap] for ym, gap, _m3, _m2 in serie[-meses:]]


def fetch_idc_serie(meses: int = 18) -> list:
    """Serie mensual del Índice de Capacidad Prestable, con la misma fórmula que el
    indicador en macro.py (_idc_componentes) sobre stocks de fin de mes. Devuelve
    los últimos `meses` como [[YYYY-MM-01, idc]]."""
    serie = macro._idc_serie_mensual(meses_hist=meses + 2)  # [(YYYY-MM, idc)] asc.
    return [[f"{ym}-01", idc] for ym, idc in serie[-meses:]]


def fetch_iai_serie(meses: int = 18) -> list:
    """Serie histórica del IAI (inversión física: ISAC + BK importados, 65/35),
    con la misma fórmula que macro.py. [[YYYY-MM-01, valor]]."""
    return [[f"{ym}-01", v] for ym, v in macro._iai_serie_mensual(meses=meses)]


def fetch_icip_serie(meses: int = 18) -> list:
    """Serie histórica del ICIP (inversión digital: servicios tech + productividad),
    con la misma fórmula que macro.py. [[YYYY-MM-01, valor]]."""
    return [[f"{ym}-01", v] for ym, v in macro._icip_serie_mensual(meses=meses)]


def descargar(cinturon: str, indec_series: list, bcra_vars: list, derivadas: list = ()):
    rows = []

    for nombre, unidad, fuente, fetch_fn in derivadas:
        try:
            data = fetch_fn()
            for fecha, valor in data:
                rows.append([fecha, nombre, valor, unidad, fuente])
            print(f"  [OK] {nombre}: {len(data)} puntos  ({data[-1][0]} → {data[0][0]})")
        except Exception as e:
            print(f"  [ERR] {nombre}: {e}")

    for sid, nombre, unidad, fuente in indec_series:
        try:
            data = fetch_indec(sid)
            for fecha, valor in data:
                rows.append([fecha, nombre, valor, unidad, fuente])
            print(f"  [OK] {nombre}: {len(data)} puntos  ({data[-1][0]} → {data[0][0]})")
        except Exception as e:
            print(f"  [ERR] {nombre}: {e}")

    for var_id, nombre, unidad, fuente in bcra_vars:
        try:
            data = fetch_bcra(var_id)
            for fecha, valor in data:
                rows.append([fecha, nombre, valor, unidad, fuente])
            print(f"  [OK] {nombre}: {len(data)} puntos  ({data[-1][0]} → {data[0][0]})")
        except Exception as e:
            print(f"  [ERR] {nombre}: {e}")

    rows.sort(key=lambda x: (x[1], x[0]), reverse=True)
    write_csv(cinturon, rows)


# ── Definición de series por cinturón ─────────────────────────────────────────

MACRO_INDEC = [
    ("148.3_INIVELNAL_DICI_M_26",  "ipc_total",       "% mensual",          "INDEC/datos.gob.ar"),
    ("143.3_ICE_SERVIA_2004_A_25", "emae_ia",         "% i.a.",             "INDEC/datos.gob.ar"),
    ("172.3_TL_RECAION_M_0_0_17",  "recaudacion",     "M ARS",              "INDEC/datos.gob.ar"),
]
MACRO_DERIVADAS = [
    ("saldo_comercial", "M USD", "INDEC/datos.gob.ar (ICA expo−impo)", fetch_saldo_ica),
    ("reservas_bcra", "M USD netas", "BCRA Planilla SDDS + Balance (a secas)", fetch_reservas_netas_serie),
    ("tcrm", "índice (base dic-2015)", "BCRA ITCRM", fetch_tcrm_serie),
    ("idm", "pp (brecha i.a. real)", "BCRA (M3/M2 privado) + IPC INDEC", fetch_idm_serie),
    ("idc", "índice (~1,0)", "BCRA (BADLAR/depósitos/préstamos) + IPC INDEC", fetch_idc_serie),
    ("iai", "% i.a. ponderado", "INDEC (ISAC + bienes de capital importados)", fetch_iai_serie),
    ("icip", "% i.a. ponderado", "INDEC (servicios informática + productividad)", fetch_icip_serie),
]
MACRO_BCRA = [
    (7,  "badlar",             "% anual",  "BCRA"),
    (29, "rem_ipc_12m",        "% anual",  "BCRA"),
    (26, "prestamos_privados", "M ARS",    "BCRA"),
    (15, "base_monetaria",     "M ARS",    "BCRA"),
    (5,  "tc_mayorista",       "ARS/USD",  "BCRA"),
]

POLITICA_INDEC = []
# Cinturón político: sin series INDEC, pero el Votómetro reconstruye su histórico.


def fetch_votometro_serie() -> list:
    """Serie histórica de la brecha LLA−PJ del Votómetro (reconstruida desde
    encuestasRaw). [[YYYY-MM-01, gap]]."""
    return [[f"{ym}-01", g] for ym, g in politica.votometro_serie_mensual()]


def fetch_iaf_serie() -> list:
    """Serie ANUAL de la variación real i.a. de transferencias federales totales
    (RON Hacienda), deflactada por el IPC dic-dic oficial de INDEC — misma fórmula
    que el indicador. Confiable desde 2017 (base del índice IPC). [[YYYY-12-01, %]]."""
    import csv
    import io
    r = requests.get(politica.RON_CSV_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    rd = csv.reader(io.StringIO(r.text), delimiter=";")
    next(rd)
    tot = {}
    for row in rd:
        if len(row) < 5:
            continue
        try:
            tot[int(row[0])] = tot.get(int(row[0]), 0.0) + float(row[4].replace(",", "."))
        except ValueError:
            continue
    ipc = politica._ipc_dicdic_indec()
    out = []
    for y in sorted(tot):
        if y - 1 in tot and tot[y - 1] and y in ipc:
            var_nom = tot[y] / tot[y - 1] - 1.0
            var_real = (1.0 + var_nom) / (1.0 + ipc[y]) - 1.0
            out.append([f"{y}-12-01", round(var_real * 100.0, 1)])
    return out


def fetch_ratio_dnu_serie() -> list:
    """Serie ANUAL del ratio DNUs/leyes (InfoLeg), misma fórmula que el indicador:
    DNUs (tipoNorma=2 + 'necesidad y urgencia') / leyes (tipoNorma=1) por año.
    [[YYYY-01-01, ratio]]."""
    s = requests.Session()
    rh = s.get(politica.INFOLEG_HOME, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    rh.raise_for_status()
    m = re.search(r'action="(/infolegInternet/[^"]+)"', rh.text)
    if not m:
        raise ValueError("InfoLeg: no se encontró el form action")
    au = "https://servicios.infoleg.gob.ar" + m.group(1)
    out = []
    for y in range(2020, date.today().year + 1):
        leyes = politica._infoleg_session_count(s, au, "1", y)
        if not leyes:
            continue
        dnus = politica._infoleg_session_count(s, au, "2", y, texto="necesidad y urgencia")
        out.append([f"{y}-01-01", round(dnus / leyes, 3)])
    return out


POLITICA_DERIVADAS = [
    ("votometro_ventaja_lla", "pp (brecha LLA−PJ)", "Votómetro CIGOB", fetch_votometro_serie),
    ("iaf_transferencias", "% i.a. real", "RON Hacienda + IPC INDEC (dic-dic)", fetch_iaf_serie),
    ("ratio_dnu", "DNUs por ley", "InfoLeg (conteo anual)", fetch_ratio_dnu_serie),
]

VIDA_INDEC = [
    ("148.3_INIVELNAL_DICI_M_26", "ipc_total",    "indice base dic-2016=100", "INDEC/datos.gob.ar"),
    ("42.3_EPH_PUNTUATAL_0_M_30", "desocupacion", "%",                        "INDEC/datos.gob.ar"),
]
# Derivadas: la variación m/m % de cada serie INDEC de índices (misma métrica que
# muestra la card del indicador), reconstruida para todo el histórico disponible.
VIDA_DERIVADAS = [
    ("ipc_alimentos",    "% m/m",           "INDEC serie 146.3", lambda: fetch_indec_var_mensual("146.3_IALIMENNAL_DICI_M_45")),
    ("peso_tarifas",     "% m/m regulados", "INDEC serie 148.3", lambda: fetch_indec_var_mensual("148.3_IREGULANAL_DICI_M_22")),
    ("mortalidad_pymes", "% m/m (IPI)",     "INDEC serie 453.1", lambda: fetch_indec_var_mensual("453.1_SERIE_ORIGNAL_0_0_14_46")),
]
def fetch_icc_serie(meses: int = 60) -> list:
    """Serie histórica del ICC UTDT: parsea TODAS las filas del XLS oficial (col 0 fecha,
    col 1 índice), no solo la última como el indicador. Reusa el scraper del colector de
    vida. Devuelve los últimos `meses` como [[YYYY-MM-01, icc]] ascendente."""
    import xlrd
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana" / "collectors"))
    from utdt_icc import _get_latest_xls_fname
    from config import UTDT_ICC_DOWNLOAD_BASE
    r = requests.get(UTDT_ICC_DOWNLOAD_BASE + _get_latest_xls_fname(),
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    wb = xlrd.open_workbook(file_contents=r.content)
    ws = wb.sheets()[0]
    out = []
    for i in range(ws.nrows):
        fc, vc = ws.cell(i, 0), ws.cell(i, 1)
        if fc.ctype == xlrd.XL_CELL_DATE and vc.ctype == xlrd.XL_CELL_NUMBER:
            t = xlrd.xldate_as_tuple(fc.value, wb.datemode)
            out.append([f"{t[0]}-{t[1]:02d}-01", round(vc.value, 1)])
    return out[-meses:]


VIDA_DERIVADAS.append(
    ("icc_utdt", "índice", "UTDT (ICC, serie XLS)", fetch_icc_serie)
)


def fetch_sentimiento_serie() -> list:
    """Serie SEMANAL del sentimiento digital (promedio del interés Trends de las 4
    keywords) en la MISMA ventana 'today 3-m' que usa el indicador live, así la
    normalización 0-100 coincide y no hay re-anclado ni cambio de score. Google Trends
    no tiene escala absoluta: una ventana más larga re-normaliza el valor, por eso la
    serie se acota a 3 meses. [[YYYY-MM-DD, interés]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana" / "collectors"))
    import trends as _t
    from config import TRENDS_KEYWORDS, TRENDS_GEO
    _t._patch_urllib3()
    from pytrends.request import TrendReq
    pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 30), retries=2, backoff_factor=0.5)
    pt.build_payload(TRENDS_KEYWORDS, cat=0, timeframe="today 3-m", geo=TRENDS_GEO)
    df = pt.interest_over_time()
    if df is None or df.empty:
        raise ValueError("Trends devolvió vacío (rate limit)")
    cols = [k for k in TRENDS_KEYWORDS if k in df.columns]
    return [[d.strftime("%Y-%m-%d"), round(float(row[cols].mean()), 1)]
            for d, row in df.iterrows()]


VIDA_DERIVADAS.append(
    ("sentimiento_digital", "interés 0–100", "Google Trends (ventana 3m)", fetch_sentimiento_serie)
)


def fetch_endeudamiento_serie() -> list:
    """Serie del stock nominal de crédito de consumo (personales 114 + tarjeta 115, BCRA)
    en billones de pesos — mismo valor que el headline del indicador (la variación real
    i.a. que puntúa se muestra aparte en el box de score). [[YYYY-MM-01, billones]]."""
    def mensual(vid):
        out = {}
        for f, v in sorted(fetch_bcra(vid, dias=1300)):
            out[f[:7]] = v
        return out
    per, tar = mensual(114), mensual(115)
    return [[f"{ym}-01", round((per[ym] + tar[ym]) / 1e6, 2)]
            for ym in sorted(per) if ym in tar]


VIDA_DERIVADAS.append(
    ("endeudamiento_familiar", "billones de pesos (consumo)", "BCRA API v4.0 (personales + tarjeta)", fetch_endeudamiento_serie)
)

VIDA_DERIVADAS += [
    ("informalidad", "%", "INDEC EPH (52.1, anual)", lambda: fetch_indec_x100("52.1_ASDJ_0_0_37")),
    ("pluriempleo", "%", "INDEC EPH (47.2, trimestral)", lambda: fetch_indec_x100("47.2_ECTSDT_0_T_47")),
]


# ── Series ITVC-B100 (vida cotidiana, doc 260702 — ADR-0018) ──────────────────
# Componentes del ITVC que requieren TRANSFORMACIÓN (nivel relativo al salario,
# nivel desestacionalizado rebaseado, deuda real): se emiten como series YA
# rebaseadas a 100 = promedio 4T-2023 (oct-nov-dic), la línea base del doc.
# La base se calcula DINÁMICAMENTE de la misma serie (nunca hardcodeada).

ITVC_RIPTE_ID      = "158.1_REPTE_0_0_5"                # RIPTE mensual ($)
ITVC_IPI_DESEST_ID = "453.1_SERIE_DESEADA_0_0_24_58"    # IPI nivel desestacionalizado
ITVC_ISAC_DESEST_ID = "33.2_ISAC_SIN_EDAD_0_M_23_56"    # ISAC nivel desestacionalizado
ITVC_BASE_MESES = ("2023-10", "2023-11", "2023-12")


def _nivel_mensual(sid: str, limit: int = 60) -> dict:
    """{YYYY-MM: valor} de una serie mensual de datos.gob.ar (vía fetch_indec)."""
    return {f[:7]: v for f, v in fetch_indec(sid, limit=limit)}


def _base_t423(serie: dict) -> float:
    """Promedio del 4T-2023 de {YYYY-MM: valor}; exige los tres meses."""
    faltan = [m for m in ITVC_BASE_MESES if m not in serie]
    if faltan:
        raise ValueError(f"base 4T-2023 incompleta (faltan {faltan})")
    return sum(serie[m] for m in ITVC_BASE_MESES) / 3.0


def _itvc_rebase(serie: dict, invertido: bool = False) -> list:
    """Serie {ym: valor} → [[YYYY-MM-01, índice]] con 100 = promedio 4T-2023.
    invertido=True para métricas 'más alto = peor' (I = base/valor)."""
    base = _base_t423(serie)
    out = []
    for ym in sorted(serie):
        if ym < "2023-10" or not serie[ym]:
            continue
        indice = (base / serie[ym] if invertido else serie[ym] / base) * 100.0
        out.append([f"{ym}-01", round(indice, 1)])
    return out


def _itvc_relativo_salario(sid_precio: str) -> list:
    """Componente de precios del ITVC: nivel del índice de precios RELATIVO al
    salario (RIPTE), rebaseado. I(t) = (P_base/P_t) × (RIPTE_t/RIPTE_base) × 100:
    >100 = los precios subieron MENOS que los salarios desde el 4T-2023."""
    precio = _nivel_mensual(sid_precio)
    ripte  = _nivel_mensual(ITVC_RIPTE_ID)
    p_base, r_base = _base_t423(precio), _base_t423(ripte)
    out = []
    for ym in sorted(set(precio) & set(ripte)):
        if ym < "2023-10" or not precio[ym] or not ripte[ym]:
            continue
        indice = (p_base / precio[ym]) * (ripte[ym] / r_base) * 100.0
        out.append([f"{ym}-01", round(indice, 1)])
    return out


def fetch_itvc_alimentos() -> list:
    """I_IA: poder de compra de alimentos del salario (IPC Alimentos nivel vs
    RIPTE), 100 = 4T-2023."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import INDEC_SERIES
    return _itvc_relativo_salario(INDEC_SERIES["ipc_alimentos"])


def fetch_itvc_tarifas() -> list:
    """I_PT: peso de los servicios regulados en el salario (IPC Regulados nivel
    vs RIPTE), 100 = 4T-2023."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import INDEC_SERIES
    return _itvc_relativo_salario(INDEC_SERIES["ipc_regulados"])


def fetch_itvc_ipi() -> list:
    """I_IPI: nivel del IPI manufacturero DESESTACIONALIZADO, 100 = 4T-2023."""
    return _itvc_rebase(_nivel_mensual(ITVC_IPI_DESEST_ID))


def fetch_itvc_isac() -> list:
    """I_ISC: nivel del ISAC DESESTACIONALIZADO, 100 = 4T-2023 (la serie
    original tiene un desplome estacional en dic-23 que contaminaría la base)."""
    return _itvc_rebase(_nivel_mensual(ITVC_ISAC_DESEST_ID))


BCRA_INF_BANCOS_ANEXO = ("https://www.bcra.gob.ar/archivos/Pdfs/"
                         "PublicacionesEstadisticas/informes/InfBanc_Anexo.xlsx")


def _anexo_bancos_familias() -> tuple:
    """(deuda_consumo {ym: saldo M$}, mora {ym: % ponderado}) del corte FAMILIAS
    del anexo del Informe sobre Bancos (hoja 'Calidad de Cartera (por líneas)',
    personales + tarjetas: saldos e irregularidad, mensual 2010→). El layout se
    detecta por etiquetas (no por número de fila): cada bloque tiene una fila de
    fechas seguida de filas etiquetadas; el bloque de ratios tiene valores <100
    y el de saldos, millones."""
    import openpyxl
    r = requests.get(BCRA_INF_BANCOS_ANEXO, headers=HTTP_HEADERS,
                     timeout=HTTP_TIMEOUT * 3, verify=False)
    r.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    hoja = next(s for s in wb.sheetnames if "por l" in s.lower())   # "(por líneas)"
    filas = list(wb[hoja].iter_rows(values_only=True))

    def _es_fecha(c):
        return hasattr(c, "year") and hasattr(c, "month")

    # Anclado en el título de sección: "2. Familias - Total" → los DOS bloques
    # de fechas siguientes son el ratio de irregularidad y el saldo (en ese
    # orden, cada uno con filas etiquetadas Personales / Tarjetas de crédito).
    inicio = next(i for i, f in enumerate(filas)
                  if str((f or [""])[0] or "").strip().lower().startswith("2. familias"))
    bloques = []
    i = inicio + 1
    while i < len(filas) and len(bloques) < 2:
        f = filas[i]
        if sum(1 for c in f if _es_fecha(c)) > 50:
            fechas = {j: f"{c.year}-{c.month:02d}" for j, c in enumerate(f) if _es_fecha(c)}
            etiquetas = {}
            for k in range(i + 1, min(i + 10, len(filas))):
                lbl = str(filas[k][0] or "").strip().lower()
                if not lbl or lbl.startswith("fuente"):
                    if lbl.startswith("fuente"):
                        break
                    continue
                etiquetas[lbl] = filas[k]
            bloques.append((fechas, etiquetas))
        i += 1
    if len(bloques) < 2:
        raise ValueError("anexo Informe sobre Bancos: bloques de familias no encontrados")
    ratios, saldos = bloques

    def _serie(bloque, contiene):
        fechas, etiquetas = bloque
        lbl = next(l for l in etiquetas if contiene in l)
        out = {}
        for j, ym in fechas.items():
            try:
                v = float(etiquetas[lbl][j])
            except (TypeError, ValueError, IndexError):
                continue
            out[ym] = v
        return out

    s_per, s_tar = _serie(saldos, "personales"), _serie(saldos, "tarjeta")
    r_per, r_tar = _serie(ratios, "personales"), _serie(ratios, "tarjeta")
    deuda, mora = {}, {}
    for ym in sorted(set(s_per) & set(s_tar) & set(r_per) & set(r_tar)):
        total = s_per[ym] + s_tar[ym]
        if total > 0:
            deuda[ym] = total
            mora[ym] = (r_per[ym] * s_per[ym] + r_tar[ym] * s_tar[ym]) / total
    return deuda, mora


def fetch_itvc_endeudamiento() -> list:
    """I_EC del doc 260702: crédito de consumo de FAMILIAS (personales +
    tarjetas, anexo del Informe sobre Bancos — mismo corte para saldo y mora)
    en términos REALES, corregido por la tasa de irregularidad:

        I_EC(t) = 100 × (Deuda_real_t / Deuda_real_4T23) × (Mora_4T23 / Mora_t)

    Deuda creciendo con mora estable = mejora de acceso al crédito; deuda
    creciendo con mora disparada = sobreendeudamiento por necesidad (cae)."""
    deuda, mora = _anexo_bancos_familias()
    ipc = _nivel_mensual("148.3_INIVELNAL_DICI_M_26", limit=220)
    real = {ym: deuda[ym] / ipc[ym] for ym in sorted(set(deuda) & set(ipc))}
    base_real, base_mora = _base_t423(real), _base_t423(mora)
    out = []
    for ym in sorted(real):
        if ym < "2023-10" or ym not in mora or not mora[ym]:
            continue
        indice = 100.0 * (real[ym] / base_real) * (base_mora / mora[ym])
        out.append([f"{ym}-01", round(indice, 1)])
    return out


def fetch_inseguridad_serie() -> list:
    """Serie ANUAL de hechos delictivos del SNIC (total país), con el MISMO
    criterio de suma que el colector (todas las filas del CSV: padres +
    subcategorías — consistente con el valor del indicador y la baseline del
    ITVC). El CSV oficial se revisa retroactivamente. [[YYYY-12-01, hechos]]."""
    import csv as _csv
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import SNIC_CSV
    r = requests.get(SNIC_CSV, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
    r.raise_for_status()
    texto = r.content.decode("utf-8", errors="replace")
    sep = ";" if ";" in texto.split("\n", 1)[0] else ","   # el CSV cambió a ';' en 2026
    por_anio = {}
    for row in _csv.DictReader(io.StringIO(texto), delimiter=sep):
        anio = (row.get("anio") or row.get("year") or row.get("Anio") or "").strip()
        if not anio.isdigit():
            continue
        try:
            hechos = int(float(row.get("cantidad_hechos") or row.get("hechos")
                                or row.get("cantidad") or 0))
        except ValueError:
            continue
        por_anio[anio] = por_anio.get(anio, 0) + hechos
    return [[f"{a}-12-01", por_anio[a]] for a in sorted(por_anio)
            if int(a) >= 2014 and por_anio[a] > 0]


CARNE_SERIE_STORE = Path(__file__).resolve().parents[1] / "data" / "vida" / "carne_serie.json"


def fetch_carne_serie() -> list:
    """Serie MENSUAL del consumo de carne per cápita (promedio móvil 12m,
    CICCRA) desde oct-2023 (línea base del ITVC). Los PDFs mensuales se bajan
    una sola vez y quedan cacheados por mes en data/vida/carne_serie.json
    (~33 PDFs solo la primera corrida). Los informes de 2023 usan sufijo 'b'
    (separata económica); 2024→ van sin sufijo. [[YYYY-MM-01, kg/hab/año]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana" / "collectors"))
    from ciccra import _url_pdf, _extraer_per_capita
    try:
        cache = json.loads(CARNE_SERIE_STORE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        cache = {}
    hoy = date.today()
    fin = hoy.replace(day=1) - timedelta(days=1)          # dato hasta ~2 meses atrás
    fin = fin.replace(day=1) - timedelta(days=1)
    y, m = 2023, 10
    while (y, m) <= (fin.year, fin.month):
        ym = f"{y}-{m:02d}"
        if ym not in cache:
            url = _url_pdf(y, m)
            valor = None
            for u in (url, url.replace(f"-{y}-", f"b-{y}-", 1)):
                try:
                    r = requests.get(u, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
                    if r.status_code == 200 and r.content[:4] == b"%PDF":
                        valor = _extraer_per_capita(r.content)
                        if valor is not None:
                            break
                except requests.RequestException:
                    continue
            # None también se cachea (mes sin informe parseable: no reintentar
            # cada corrida; borrar la clave del store para forzar reintento).
            cache[ym] = valor
            CARNE_SERIE_STORE.write_text(
                json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
        m += 1
        if m > 12:
            m = 1; y += 1
    return [[f"{ym}-01", v] for ym, v in sorted(cache.items()) if v]


def fetch_motos_serie() -> list:
    """Serie mensual de patentamientos de motovehículos vía la API de CAFAM
    (la misma fuente del colector; expone meses históricos — verificado
    jul-2026). Desde oct-2023 (la línea base del ITVC) hasta el último mes
    calendario completo. [[YYYY-MM-01, unidades]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import CAFAM_API
    hoy = date.today()
    fin = (hoy.replace(day=1) - timedelta(days=1))     # último mes completo
    out = []
    y, m = 2023, 10
    while (y, m) <= (fin.year, fin.month):
        try:
            r = requests.get(CAFAM_API, params={"month_start": m, "month_end": m,
                                                "year": y, "type": "TODOS"},
                             headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            total = sum(p["count"] for p in r.json().get("provinces", []))
            if total > 0:
                out.append([f"{y}-{m:02d}-01", total])
        except Exception as e:
            print(f"  [WARN] motos serie {y}-{m:02d}: {e}")
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


# Componentes transformados del ITVC-B100 (100 = promedio 4T-2023, ADR-0018)
VIDA_DERIVADAS += [
    ("itvc_alimentos", "índice (100 = 4T-2023)", "INDEC IPC Alimentos + RIPTE (elab. CIGOB)", fetch_itvc_alimentos),
    ("itvc_tarifas", "índice (100 = 4T-2023)", "INDEC IPC Regulados + RIPTE (elab. CIGOB)", fetch_itvc_tarifas),
    ("itvc_ipi", "índice (100 = 4T-2023)", "INDEC IPI desestacionalizado", fetch_itvc_ipi),
    ("itvc_isac", "índice (100 = 4T-2023)", "INDEC ISAC desestacionalizado", fetch_itvc_isac),
    ("itvc_endeudamiento", "índice real (100 = 4T-2023)", "BCRA Informe sobre Bancos (familias) + IPC INDEC", fetch_itvc_endeudamiento),
    ("patentamiento_motos", "unidades/mes", "CAFAM API (histórico mensual)", fetch_motos_serie),
    ("inseguridad", "hechos/año (total país)", "SNIC (CSV oficial, suma anual)", fetch_inseguridad_serie),
    ("consumo_carne", "kg/hab/año (PM 12m)", "CICCRA (informes mensuales, caché local)", fetch_carne_serie),
    # La MISMA métrica que muestra la card del indicador (ISAC nivel s.e.);
    # antes el modal caía por alias a isac_construccion (insumo cemento 33.4).
    ("despacho_cemento", "índice ISAC (desest.)", "INDEC ISAC (33.2, s.e.)",
     lambda: [[f, round(v, 2)] for f, v in sorted(fetch_indec(ITVC_ISAC_DESEST_ID, limit=60))]),
]


def fetch_brecha_serie() -> list:
    """Serie de la brecha salario/CBT = RIPTE / Canasta Básica Total, ALINEADA por mes
    (mismo mes en ambas series; el indicador live toma el último de cada una, que a veces
    son meses distintos). Cuántas canastas cubre el salario imponible promedio.
    [[YYYY-MM-01, canastas]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import RIPTE_CSV, INDEC_SERIES
    r = requests.get(RIPTE_CSV, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    ripte = {}
    for line in r.text.strip().split("\n"):
        p = line.split(",")
        if len(p) >= 2 and p[0][:4].isdigit():
            ripte[p[0][:7]] = float(p[1])
    cbt = {f[:7]: v for f, v in fetch_indec(INDEC_SERIES["cbt"], limit=60)}
    comun = sorted(set(ripte) & set(cbt))
    return [[f"{ym}-01", round(ripte[ym] / cbt[ym], 2)] for ym in comun if cbt[ym]]


VIDA_DERIVADAS.append(
    ("brecha_salario_cbt", "canastas (RIPTE/CBT)", "INDEC (RIPTE + Canasta Básica Total)", fetch_brecha_serie)
)

GESTION_INDEC = [
    ("149.1_SOR_PUBICO_OCTU_0_14",   "indice_salarios_publico", "indice base oct-2016=100", "INDEC/datos.gob.ar"),
    ("33.4_ISAC_CEMENAND_0_0_21_24", "isac_construccion",       "indice base 2004=100",     "INDEC/datos.gob.ar"),
]


def fetch_rigi_serie() -> list:
    """Serie histórica del RIGI: inversión aprobada ACUMULADA (US$ M) por mes,
    reconstruida con la fecha de sanción (BO) de cada proyecto aprobado. La
    plataforma oficial solo publica la foto actual; esto arma la evolución."""
    proy = gestion.rigi_proyectos_aprobados()   # [(fecha_iso, nombre, inv)] ordenado
    cum, por_mes = 0.0, {}
    for fecha, _nombre, inv in proy:
        cum += inv
        por_mes[fecha[:7]] = round(cum)         # acumulado al último proyecto del mes
    return [[f"{ym}-01", v] for ym, v in sorted(por_mes.items())]


def fetch_infoleg_serie(texto: str) -> list:
    """Serie mensual del conteo ACUMULADO de normas InfoLeg que contienen `texto`,
    desde dic-2023 hasta el fin de cada mes (mismo conteo que el indicador, evaluado
    a cada corte). [[YYYY-MM-01, count]]."""
    out = []
    y, mo = 2023, 12
    today = date.today()
    while (y, mo) <= (today.year, today.month):
        last = min(date(y, mo, calendar.monthrange(y, mo)[1]), today)
        try:
            c = gestion._infoleg_post(
                texto=texto, tipo_norma="",
                fecha_desde=("01", "12", "2023"),
                fecha_hasta=(last.strftime("%d"), last.strftime("%m"), last.strftime("%Y")),
            )
            out.append([f"{y}-{mo:02d}-01", c])
        except Exception:
            pass
        mo += 1
        if mo > 12:
            mo = 1; y += 1
    return out


def fetch_reduccion_serie() -> list:
    """Serie de la variación % de la dotación APN vs dic-2023 (misma fórmula y
    fuente que el indicador: XLSX mensual del INDEC). [[YYYY-MM-01, var%]]."""
    serie = gestion.dotacion_apn_series()          # {YYYY-MM: dotación}
    base = serie["2023-12"]
    return [[f"{ym}-01", round((v - base) / base * 100, 2)]
            for ym, v in sorted(serie.items()) if ym >= "2023-12"]


def fetch_tdps_serie() -> list:
    """Serie mensual del TDPS (% del devengado pagado directo a personas,
    partida 5.1.4, sobre el total del inciso 5) del programa de ingreso social
    vigente en cada momento: Potenciar Trabajo (2023, jur. 85 prog. 38) y sus
    sucesores Volver al Trabajo + Acompañamiento Social (2024–). API
    Presupuesto Abierto; sin token devuelve [] (la serie queda en el último
    snapshot). Meses de transición con devengado ínfimo se omiten."""
    token = gestion._pa_token()
    if not token:
        return []
    cols = ["impacto_presupuestario_mes", "inciso_id", "principal_id",
            "parcial_id", "credito_devengado"]
    por_mes: dict = {}
    for anio in range(2023, date.today().year + 1):
        if anio == 2023:
            bloques = [[{"column": "jurisdiccion_id", "operator": "equal", "value": "85"},
                        {"column": "programa_id", "operator": "equal", "value": "38"}]]
        else:
            bloques = [[{"column": "actividad_desc", "operator": "like", "value": f"%{a}%"}]
                       for a in gestion.TDPS_ACTIVIDADES]
        for filtros in bloques:
            try:
                rows = gestion._pa_credito(token, anio, filtros, columns=cols)
            except Exception as e:
                print(f"  [WARN] tdps serie {anio}: {e}")
                continue
            for r in rows:
                try:
                    if int(r.get("inciso_id") or 0) != 5:
                        continue
                    ym = f"{anio}-{int(r.get('impacto_presupuestario_mes') or 0):02d}"
                    dev = float(r.get("credito_devengado") or 0)
                except (TypeError, ValueError):
                    continue
                d = por_mes.setdefault(ym, {"directo": 0.0, "total": 0.0})
                d["total"] += dev
                if int(r.get("principal_id") or 0) == 1 and int(r.get("parcial_id") or 0) == 4:
                    d["directo"] += dev
    return [[f"{ym}-01", round(100.0 * d["directo"] / d["total"], 1)]
            for ym, d in sorted(por_mes.items()) if d["total"] > 1000.0]


def _serie_var_real_vs_2023(nominal_ids: list) -> list:
    """Serie mensual de la variación % REAL vs el MISMO MES de 2023 (misma
    fórmula que el indicador: deflactada por IPC, mismo mes evita el sesgo
    del aguinaldo) para la suma de una o más series nominales de datos.gob.ar.
    [[YYYY-MM-01, var%]] desde 2024-01."""
    nominal: dict = {}
    for sid in nominal_ids:
        for ym, v in gestion._indec_nivel_mensual(sid, limit=48).items():
            nominal[ym] = nominal.get(ym, 0.0) + v
    ipc = gestion._indec_nivel_mensual(gestion.IPC_ID, limit=48)
    out = []
    for ym in sorted(nominal):
        if ym < "2024-01":
            continue
        base = f"2023-{ym[5:7]}"
        if base not in nominal or base not in ipc or ym not in ipc:
            continue
        real_t = nominal[ym] / ipc[ym]
        real_b = nominal[base] / ipc[base]
        out.append([f"{ym}-01", round((real_t / real_b - 1.0) * 100.0, 2)])
    return out


def fetch_opcion_salud_serie() -> list:
    """Serie mensual del % de usuarios de prepagas con aportes derivados
    directo (misma fórmula que el indicador): RNAS 90xxxx / total RNEMP, por
    año desde 2024 (los XLSX de la SSS existen por año, URL estable; usa
    gestion._sss_tabla, que no depende de la fila de totales — falta en los
    archivos de algunos años). El denominador RNEMP se arrastra al último mes
    disponible (cambia lento y su archivo tiene más rezago que el RNAS)."""
    import openpyxl
    derivados, usuarios = {}, {}
    for anio in range(2024, date.today().year + 1):
        for url_tpl, destino, solo_prepagas in (
                (gestion.SSS_RNAS_URL, derivados, True),
                (gestion.SSS_RNEMP_URL, usuarios, False)):
            try:
                wb = openpyxl.load_workbook(io.BytesIO(
                    gestion._http_get_resiliente(url_tpl.format(anio=anio))), data_only=True)
                ws = wb[wb.sheetnames[0]]
                cols, entidades = gestion._sss_tabla(ws)
                for col, mm in sorted(cols.items()):
                    total_mes, _ = gestion._sss_suma_mes(entidades, col)
                    if total_mes > 0:
                        suma, _ = gestion._sss_suma_mes(entidades, col, solo_prepagas=solo_prepagas)
                        destino[f"{anio}-{mm}"] = suma
            except Exception as e:
                registro = "RNAS" if url_tpl is gestion.SSS_RNAS_URL else "RNEMP"
                print(f"  [WARN] opcion salud serie {registro} {anio}: {e}")
    # Denominador: se arrastra el último RNEMP conocido; para los meses previos
    # al primer archivo mensual (el RNEMP 2024 agrupa por cuatrimestres y se
    # saltea) se usa el primero disponible — el canal era ínfimo en 2024.
    out, ult_u = [], None
    primera_u = usuarios[min(usuarios)] if usuarios else None
    for ym in sorted(derivados):
        if usuarios.get(ym):
            ult_u = usuarios[ym]
        denom = ult_u or primera_u
        if denom:
            out.append([f"{ym}-01", round(100.0 * derivados[ym] / denom, 1)])
    return out


def fetch_protestas_serie() -> list:
    """Serie mensual de eventos de protesta en CABA desde el store que llena
    gestion.actualizar_protestas_caba() (evita re-bajar los ~8 MB de ACLED:
    el colector corre antes en el pipeline). [[YYYY-MM-01, eventos]]."""
    import json as _json
    if not gestion.PROTESTAS_STORE_PATH.exists():
        return []
    store = _json.loads(gestion.PROTESTAS_STORE_PATH.read_text(encoding="utf-8"))
    return [[f"{ym}-01", v] for ym, v in sorted(store.get("mensual", {}).items())]


ARGENTINADATOS_CCL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"


def fetch_brecha_serie() -> list:
    """Serie mensual de la brecha CCL/mayorista (misma métrica que cepo_mulc):
    promedio mensual del CCL histórico de ArgentinaDatos (el proyecto hermano
    de dolarapi, la MISMA familia de fuente que usa el colector vivo) sobre el
    promedio mensual del A3500 oficial (BCRA var. 5). Desde dic-2023. El
    último punto es el promedio del mes corriente parcial (el live es el spot
    del día — difieren de forma inmaterial)."""
    hoy = date.today()
    r = requests.get(ARGENTINADATOS_CCL,
                     headers={"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"},
                     timeout=120)
    r.raise_for_status()
    ccl: dict = {}
    for fila in r.json():
        fecha = str(fila.get("fecha", ""))
        try:
            v = float(fila.get("venta") or 0)
        except (TypeError, ValueError):
            continue
        if fecha >= "2023-12" and v > 0:
            ccl.setdefault(fecha[:7], []).append(v)
    dias = (hoy - date(2023, 11, 25)).days
    a3500 = gestion._tc_mayorista_promedio_por_mes(dias=dias)   # {ym: promedio}
    out = []
    for ym in sorted(set(ccl) & set(a3500)):
        prom_ccl = sum(ccl[ym]) / len(ccl[ym])
        if a3500[ym] > 0:
            out.append([f"{ym}-01", round((prom_ccl / a3500[ym] - 1.0) * 100.0, 2)])
    return out


def fetch_litigiosidad_serie() -> list:
    """Serie mensual de la variación % de los juicios SRT (acumulado 12 meses
    vs los 12 previos, misma fórmula que el indicador). [[YYYY-MM-01, var%]]."""
    import io as _io, openpyxl
    content = gestion._http_get_resiliente(gestion.SRT_JUICIOS_URL)
    wb = openpyxl.load_workbook(_io.BytesIO(content), data_only=True)
    hoja = next(s for s in wb.sheetnames if "TOTAL" in s.upper())
    filas = list(wb[hoja].iter_rows(values_only=True))
    meses_es = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
                "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
    patron = re.compile(r"^([A-Za-z]{3})-(\d{4})$")
    header = next(f for f in filas
                  if sum(1 for c in f if isinstance(c, str) and patron.match(c.strip())) > 20)
    fila_total = next(f for f in filas
                      if isinstance(f[0], str) and f[0].lower().startswith("total de juicios"))
    serie = {}
    for h, v in zip(header, fila_total):
        m = patron.match(h.strip()) if isinstance(h, str) else None
        if m and m.group(1).lower() in meses_es:
            try:
                serie[f"{m.group(2)}-{meses_es[m.group(1).lower()]:02d}"] = float(v)
            except (TypeError, ValueError):
                continue
    yms = sorted(serie)
    out = []
    for i in range(23, len(yms)):
        ult12 = sum(serie[y] for y in yms[i - 11:i + 1])
        prev12 = sum(serie[y] for y in yms[i - 23:i - 11])
        if prev12:
            out.append([f"{yms[i]}-01", round((ult12 / prev12 - 1.0) * 100.0, 1)])
    return out[-60:]   # últimos 5 años (la serie arranca en 2010)


def fetch_ilce_serie() -> list:
    """Serie mensual del ILCE (apertura_comercial) desde dic-2023, con la misma
    fórmula del colector: (0,4·B_camb + 0,4·A_efec)/0,8. B_camb sale de la
    brecha CCL/mayorista mensual (fetch_brecha_serie); A_efec de la alícuota
    efectiva (recaudación DEX+DIM en USD por el A3500 promedio, sobre el
    intercambio expo+impo del ICA). El live usa la brecha SPOT del día y la
    serie el promedio del mes — divergen de forma inmaterial. [[YYYY-MM-01, índice]]."""
    brecha = {f[:7]: v for f, v in fetch_brecha_serie()}
    dex  = gestion._indec_nivel_mensual(gestion.DEX_ID, limit=48)
    dim  = gestion._indec_nivel_mensual(gestion.DIM_ID, limit=48)
    expo = gestion._indec_nivel_mensual(gestion.EXPO_ICA_ID, limit=48)
    impo = gestion._indec_nivel_mensual(gestion.IMPO_ICA_ID, limit=48)
    dias = (date.today() - date(2023, 11, 25)).days
    tc   = gestion._tc_mayorista_promedio_por_mes(dias=dias)
    out = []
    for ym in sorted(set(brecha) & set(dex) & set(dim) & set(expo) & set(impo) & set(tc)):
        if ym < "2023-12" or expo[ym] + impo[ym] <= 0 or tc[ym] <= 0:
            continue
        b_camb = 100.0 / (1.0 + max(-0.99, brecha[ym] / 100.0))
        alicuota = 100.0 * ((dex[ym] + dim[ym]) / tc[ym]) / (expo[ym] + impo[ym])
        a_efec = 100.0 * max(0.0, 1.0 - alicuota / gestion.ALICUOTA_CIERRE_PCT)
        out.append([f"{ym}-01", round((0.40 * b_camb + 0.40 * a_efec) / 0.80, 1)])
    return out


CONCESIONES_FECHAS_STORE = Path(__file__).resolve().parents[1] / "data" / "gestion" / "concesiones_fechas.json"


def fetch_concesiones_serie() -> list:
    """Serie mensual del % de km adjudicados de la RFC, reconstruida como
    función ESCALONADA por hitos fechados (las adjudicaciones son actos
    administrativos puntuales): cada etapa suma sus km desde su mes de
    adjudicación. El store concesiones_fechas.json trae las fechas oficiales
    verificadas (Etapa I: RESOL-2025-80-ST ene-2026 · II-A: Res. 706/2026
    may-2026) y se auto-actualiza cuando CONTRAT.AR muestra una etapa nueva
    en ADJUDICADO (mes corriente) — mismo patrón que rigi_fechas.
    Antes de la primera adjudicación el avance es 0. [[YYYY-MM-01, %]]."""
    store = json.loads(CONCESIONES_FECHAS_STORE.read_text(encoding="utf-8-sig"))
    etapas = store["etapas"]
    try:
        km = gestion._rfc_km_por_etapa()
        store["km_totales"] = round(sum(km.values()))
        hoy_ym = date.today().strftime("%Y-%m")
        for proceso, nombre, estado in gestion._contratar_procesos_rfc():
            etapa = gestion._etapa_de_proceso(nombre)
            if etapa and "ADJUDICADO" in estado.upper() and etapa in km:
                if etapa not in etapas:
                    etapas[etapa] = {"fecha": hoy_ym, "km": km[etapa],
                                     "fuente": f"CONTRAT.AR {proceso} (detectado {hoy_ym})"}
                else:
                    etapas[etapa]["km"] = km[etapa]
        CONCESIONES_FECHAS_STORE.write_text(
            json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  [WARN] concesiones serie: CONTRAT.AR/RFC no disponible ({e}); se usa el store")
    km_total = store.get("km_totales") or 0
    if not km_total:
        return []
    out = []
    y, m = 2023, 12
    hoy = date.today()
    while (y, m) <= (hoy.year, hoy.month):
        ym = f"{y}-{m:02d}"
        adj = sum(e["km"] for e in etapas.values() if e["fecha"] <= ym)
        out.append([f"{ym}-01", round(100.0 * adj / km_total, 1)])
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


def fetch_fal_serie() -> list:
    """Serie mensual del índice FAL (fondo de cese laboral): 0 desde dic-2023
    hasta jun-2026 — el cero histórico es un DATO DURO, no un faltante: el
    decreto 847/2024 recién reglamentó el instrumento en sep-2024 y el registro
    CNV (RG 1071/2025) nunca tuvo altas —, y desde jul-2026 la medición vigente
    (cobertura CCT estimada + adopción financiera) acumulada en el histórico,
    con el valor live como último punto (ADR-0012). [[YYYY-MM-01, índice]]."""
    hist_path = Path(__file__).resolve().parents[1] / "data" / "historico" / "indicadores.json"
    try:
        hist = json.loads(hist_path.read_text(encoding="utf-8-sig")).get(
            "fal_modernizacion_laboral", {})
    except (OSError, json.JSONDecodeError):
        hist = {}
    live = gestion.fetch_fal_modernizacion_laboral()
    hoy_ym = date.today().strftime("%Y-%m")
    if live and live.get("valor") is not None:
        hist[hoy_ym] = float(live["valor"])
    out = []
    y, m = 2023, 12
    while (y, m) <= (int(hoy_ym[:4]), int(hoy_ym[5:])):
        ym = f"{y}-{m:02d}"
        out.append([f"{ym}-01", hist[ym] if ym in hist else 0.0])
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


GESTION_DERIVADAS = [
    ("apertura_comercial", "Índice 0–100 (ILCE)", "ARCA + INDEC ICA + BCRA + CCL (elab. CIGOB)", fetch_ilce_serie),
    ("concesiones_infraestructura", "% km adjudicados RFC", "CONTRAT.AR + RFC (hitos fechados)", fetch_concesiones_serie),
    ("fal_modernizacion_laboral", "Índice 0–100 (FAL)", "CNV + MTEySS (histórico: 0 hasta jul-2026)", fetch_fal_serie),
    ("rigi_inversiones", "US$ M aprobados (acum.)", "Min. Economía RIGI + BO (fechas de sanción)", fetch_rigi_serie),
    ("desregulacion_normativa", "Normas (conteo acum.)", "InfoLeg ('deroga' desde dic-2023)", lambda: fetch_infoleg_serie("deroga")),
    ("reestructuracion_organismos", "Normas (conteo acum.)", "InfoLeg ('disolucion' desde dic-2023)", lambda: fetch_infoleg_serie("disolucion")),
    ("reduccion_estado", "% vs dic-2023", "INDEC (dotación APN mensual)", fetch_reduccion_serie),
    ("asistencia_directa", "% TDPS (directo a personas / transferencias)", "API Presupuesto Abierto (SIDIF)", fetch_tdps_serie),
    ("gasto_funcionamiento", "% real vs mismo mes 2023", "Sec. Hacienda IMIG + IPC INDEC",
     lambda: _serie_var_real_vs_2023([gestion.FUNC_SALARIOS_ID, gestion.FUNC_OTROS_ID])),
    ("masa_salarial", "% real vs mismo mes 2023", "Sec. Hacienda AIF + IPC INDEC",
     lambda: _serie_var_real_vs_2023([gestion.REMUNERACIONES_ID])),
    ("libertad_opcion_salud", "% usuarios de prepagas con derivación directa", "SSS — RNAS/RNEMP", fetch_opcion_salud_serie),
    ("litigiosidad_laboral", "% i.a. juicios SRT (12m vs 12m)", "SRT — serie de litigiosidad", fetch_litigiosidad_serie),
    ("cepo_mulc", "% brecha CCL/mayorista (prom. mensual)", "ArgentinaDatos (CCL) + BCRA (A3500)", fetch_brecha_serie),
    ("protestas_caba", "eventos de protesta/mes (CABA)", "ACLED — agregado semanal (acleddata.com)", fetch_protestas_serie),
]


if __name__ == "__main__":
    print("=== MACRO ===")
    descargar("macro", MACRO_INDEC, MACRO_BCRA, MACRO_DERIVADAS)

    print("\n=== POLÍTICA ===")
    descargar("politica", POLITICA_INDEC, [], POLITICA_DERIVADAS)

    print("\n=== VIDA COTIDIANA ===")
    descargar("vida_cotidiana", VIDA_INDEC, [], VIDA_DERIVADAS)

    print("\n=== GESTIÓN ===")
    descargar("gestion", GESTION_INDEC, [], GESTION_DERIVADAS)

    print(f"\nCSVs en {OUTPUT_DIR.resolve()}")
