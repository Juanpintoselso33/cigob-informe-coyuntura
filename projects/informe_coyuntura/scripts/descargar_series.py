"""
descargar_series.py — Descarga series históricas por cinturón a CSV
Salida: output/series/macro.csv | politica.csv | vida_cotidiana.csv | gestion.csv
Columnas: fecha, indicador, valor, fuente
"""
import sys
import csv
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
    """Serie de la variación % del empleo público vs el baseline (último trimestre
    ≤ 2024-01-01), misma fórmula que el indicador. Trimestral. [[YYYY-MM-DD, var%]]."""
    data = sorted(fetch_indec(gestion.EMPLEO_PUBLICO_ID, limit=40), key=lambda x: x[0])
    base = [(f, v) for f, v in data if f <= "2024-01-01"]
    if not base:
        return []
    bdate, bval = base[-1][0], float(base[-1][1])
    return [[f, round((float(v) - bval) / bval * 100, 2)] for f, v in data if f >= bdate]


def fetch_apertura_serie() -> list:
    """Serie de la variación i.a. de importaciones totales (misma fórmula que el
    indicador). Mensual. [[YYYY-MM-DD, var_ia]]."""
    data = sorted(fetch_indec(gestion.IMPORTACIONES_ID, limit=48), key=lambda x: x[0])
    return [[data[i][0], round((data[i][1] / data[i - 12][1] - 1) * 100, 2)]
            for i in range(12, len(data)) if data[i - 12][1]]


GESTION_DERIVADAS = [
    ("rigi_inversiones", "US$ M aprobados (acum.)", "Min. Economía RIGI + BO (fechas de sanción)", fetch_rigi_serie),
    ("desregulacion_normativa", "Normas (conteo acum.)", "InfoLeg ('deroga' desde dic-2023)", lambda: fetch_infoleg_serie("deroga")),
    ("reestructuracion_organismos", "Normas (conteo acum.)", "InfoLeg ('disolucion' desde dic-2023)", lambda: fetch_infoleg_serie("disolucion")),
    ("reduccion_estado", "% vs Q1-2024", "INDEC/datos.gob.ar (empleo público)", fetch_reduccion_serie),
    ("apertura_comercial", "% interanual", "INDEC/datos.gob.ar (importaciones)", fetch_apertura_serie),
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
