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


def _meses_desde_asuncion() -> int:
    """Meses entre dic-2023 (asunción del gobierno) y hoy: la ventana por
    defecto de las series macro (regla de backfill ADR-0012 — toda serie debe
    cubrir el mandato completo, no una ventana fija que envejece)."""
    hoy = date.today()
    return (hoy.year - 2023) * 12 + hoy.month - 11


def fetch_bcra(var_id: int, dias: int = 960) -> list:
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


def fetch_saldo_12m_serie(limit: int = 60) -> list:
    """Saldo comercial ACUMULADO MÓVIL de 12 meses — la métrica del titular
    del indicador (barrido 5/12: la serie mensual bajo un titular acumulado
    confundía la lectura). La mensual sigue publicándose como saldo_comercial,
    insumo de la validación externa del ITCM. [[YYYY-MM-01, M USD]]."""
    mensual = dict(sorted(fetch_saldo_ica(limit)))
    fechas = list(mensual)
    out = []
    for i in range(11, len(fechas)):
        win = fechas[i - 11:i + 1]
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) == 11:      # ventana sin huecos
            out.append([fechas[i], round(sum(mensual[f] for f in win), 1)])
    return out


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


def fetch_reservas_netas_serie(meses: int | None = None) -> list:
    """Serie mensual de reservas NETAS "a secas" = SDDS estricto + dep. Tesoro +
    Bopreal 12m (la misma fórmula que el indicador en macro.py), parseando las
    últimas `meses` planillas SDDS (por defecto, desde dic-2023). LÍMITE DE LA
    FUENTE: el BCRA borra las planillas viejas (404 antes de jun-2024) y no
    están en Wayback (verificado jul-2026) → la serie arranca en jun-2024;
    los meses sin planilla parseable se saltean."""
    meses = meses or _meses_desde_asuncion()
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


def fetch_tcrm_serie(meses: int | None = None) -> list:
    """Serie mensual del ITCRM oficial del BCRA (base 17-dic-2015=100), de la
    planilla ITCRMSerie.xlsx. Reemplaza la serie INDEC 116.3_TCRMA, discontinuada
    en dic-2024. Devuelve los últimos `meses` como [[YYYY-MM-01, valor]]."""
    meses = meses or _meses_desde_asuncion()
    serie = macro.fetch_itcrm_serie()  # [(YYYY-MM-01, valor)] ascendente
    return [[ym, val] for ym, val in serie[-meses:]]


def fetch_idm_serie(meses: int | None = None) -> list:
    """Serie mensual del Índice de Desequilibrio Monetario (brecha i.a. real entre
    M3 y M2 privado), con la misma fórmula que el indicador en macro.py. Devuelve
    los últimos `meses` como [[YYYY-MM-01, gap_pp]]."""
    meses = meses or _meses_desde_asuncion()
    serie = macro._idm_serie_mensual(meses_hist=meses + 4)  # [(YYYY-MM, gap, m3, m2)] asc.
    return [[f"{ym}-01", gap] for ym, gap, _m3, _m2 in serie[-meses:]]


def fetch_idc_serie(meses: int | None = None) -> list:
    """Serie mensual del Índice de Capacidad Prestable, con la misma fórmula que el
    indicador en macro.py (_idc_componentes) sobre stocks de fin de mes. Devuelve
    los últimos `meses` como [[YYYY-MM-01, idc]]."""
    meses = meses or _meses_desde_asuncion()
    serie = macro._idc_serie_mensual(meses_hist=meses + 2)  # [(YYYY-MM, idc)] asc.
    return [[f"{ym}-01", idc] for ym, idc in serie[-meses:]]


def fetch_iai_serie(meses: int | None = None) -> list:
    """Serie histórica del IAI (inversión física: ISAC + BK importados, 65/35),
    con la misma fórmula que macro.py. [[YYYY-MM-01, valor]]."""
    meses = meses or _meses_desde_asuncion()
    return [[f"{ym}-01", v] for ym, v in macro._iai_serie_mensual(meses=meses)]


def fetch_icip_serie(meses: int | None = None) -> list:
    """Serie histórica del ICIP (inversión digital: servicios tech + productividad),
    con la misma fórmula que macro.py. [[YYYY-MM-01, valor]]."""
    meses = meses or _meses_desde_asuncion()
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

# Las tres series INDEC de macro se publican TRANSFORMADAS a la métrica del
# titular (barrido macro 04-jul-2026: la bajada cruda mostraba el NIVEL del
# IPC bajo un titular en % m/m, el EMAE en fracción y la recaudación nominal
# bajo un titular real — mismatch valor/serie en el modal).
MACRO_INDEC = []

IPC_NIVEL_ID = "148.3_INIVELNAL_DICI_M_26"


def fetch_ipc_mm_serie() -> list:
    """Inflación mensual (% m/m) derivada del nivel del IPC nacional — la
    métrica del titular. La curva de desinflación completa. [[YYYY-MM-01, %]]."""
    niveles = dict(sorted(fetch_indec(IPC_NIVEL_ID, limit=60)))
    fechas = list(niveles)
    return [[fechas[i], round((niveles[fechas[i]] / niveles[fechas[i - 1]] - 1) * 100, 2)]
            for i in range(1, len(fechas))]


def fetch_emae_ia_serie() -> list:
    """EMAE variación i.a. en % (la serie INDEC viene en fracción). [[YYYY-MM-01, %]]."""
    return [[f, round(v * 100, 2)] for f, v in sorted(fetch_indec("143.3_ICE_SERVIA_2004_A_25", limit=60))]


def fetch_recaudacion_real_serie() -> list:
    """Recaudación total: variación i.a. REAL en PROMEDIO MÓVIL 3 MESES — la
    métrica del titular (ADR-0029: el interanual de un mes suelto hereda el
    calendario tributario). [[YYYY-MM-01, %]]."""
    nominal = {f[:7]: v for f, v in fetch_indec("172.3_TL_RECAION_M_0_0_17", limit=72)}
    ipc = {f[:7]: v for f, v in fetch_indec(IPC_NIVEL_ID, limit=72)}
    real = {}
    for ym in sorted(nominal):
        prev = f"{int(ym[:4]) - 1}{ym[4:]}"
        if prev in nominal and ym in ipc and prev in ipc:
            real[ym] = ((nominal[ym] / nominal[prev]) * (ipc[prev] / ipc[ym]) - 1) * 100
    yms = sorted(real)
    return [[f"{yms[i]}-01", round(sum(real[y] for y in yms[i - 2:i + 1]) / 3, 2)]
            for i in range(2, len(yms))]
def fetch_credito_privado_serie() -> list:
    """Serie mensual de la variación i.a. REAL de los préstamos al sector
    privado (BCRA var. 26 fin de mes, deflactada por el IPC nivel) — la misma
    métrica del indicador credito_privado (ADR-0022). [[YYYY-MM-01, %]]."""
    fin_mes = {}
    for f, v in sorted(fetch_bcra(26, dias=1350)):
        fin_mes[f[:7]] = v
    ipc = {f[:7]: v for f, v in fetch_indec("148.3_INIVELNAL_DICI_M_26", limit=60)}
    out = []
    for ym in sorted(fin_mes):
        if ym < "2023-12":
            continue
        prev = f"{int(ym[:4]) - 1}{ym[4:]}"
        if prev in fin_mes and ym in ipc and prev in ipc and fin_mes[prev] and ipc[prev]:
            nominal = fin_mes[ym] / fin_mes[prev] - 1.0
            infl = ipc[ym] / ipc[prev] - 1.0
            out.append([f"{ym}-01", round(((1 + nominal) / (1 + infl) - 1) * 100.0, 1)])
    return out


MACRO_DERIVADAS = [
    ("ipc_total", "% mensual", "INDEC (derivado del nivel del IPC)", fetch_ipc_mm_serie),
    ("emae_ia", "% i.a.", "INDEC/datos.gob.ar", fetch_emae_ia_serie),
    ("recaudacion", "% i.a. real", "INDEC (recaudación) + IPC (deflactor)", fetch_recaudacion_real_serie),
    ("credito_privado", "% i.a. real", "BCRA (préstamos privados) + IPC INDEC", fetch_credito_privado_serie),
    ("saldo_comercial", "M USD", "INDEC/datos.gob.ar (ICA expo−impo)", fetch_saldo_ica),
    ("saldo_comercial_12m", "M USD (acum. 12 meses)", "INDEC — ICA (vía datos.gob.ar)", fetch_saldo_12m_serie),
    ("reservas_bcra", "M USD netas", "BCRA Planilla SDDS + Balance (a secas)", fetch_reservas_netas_serie),
    ("tcrm", "índice (base dic-2015)", "BCRA ITCRM", fetch_tcrm_serie),
    # bilaterales oficiales de la misma planilla (descarga memoizada): el
    # gráfico comparado del modal del TCRM, como lo presenta el propio BCRA
    ("tcrm_bilateral_brasil", "índice (base dic-2015)", "BCRA ITCRM",
     lambda: [[f, v] for f, v in macro.fetch_itcrm_bilateral("brasil")][-32:]),
    ("tcrm_bilateral_eeuu", "índice (base dic-2015)", "BCRA ITCRM",
     lambda: [[f, v] for f, v in macro.fetch_itcrm_bilateral("eeuu")][-32:]),
    ("idm", "pp (brecha i.a. real)", "BCRA (M3/M2 privado) + IPC INDEC", fetch_idm_serie),
    ("idc", "σ vs. su historia", "BCRA (BADLAR/depósitos/préstamos) + IPC INDEC", fetch_idc_serie),
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


def _hcdn_ventanas_12m() -> list:
    """[(YYYY-MM, cutoff_iso, fin_iso)] con ventana móvil de 365 días al fin de
    cada mes, desde dic-2023 hasta hoy."""
    out = []
    y, m = 2023, 12
    hoy = date.today()
    while (y, m) <= (hoy.year, hoy.month):
        fin = min(date(y, m, calendar.monthrange(y, m)[1]), hoy)
        out.append((f"{y}-{m:02d}", (fin - timedelta(days=365)).isoformat(), fin.isoformat()))
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


def fetch_eficacia_serie() -> list:
    """Serie mensual del % de proyectos PE aprobados en ventana móvil de 12
    meses (misma fórmula que el indicador): las fechas vienen POR REGISTRO en
    el CKAN de HCDN (PUBLICACION_FECHA / FECHA), así que una sola descarga
    completa permite computar todas las ventanas localmente. [[YYYY-MM-01, %]]."""
    raw_pe = politica._hcdn_paginate(politica.HCDN_PROYECTOS_RID, q="-PE-")
    pe = [(r["PROYECTO_ID"], str(r.get("PUBLICACION_FECHA", ""))[:10]) for r in raw_pe
          if r.get("PROYECTO_ID")
          and (politica._RE_PE_EXP.search(r.get("EXP_DIPUTADOS", "") or "")
               or politica._RE_PE_EXP.search(r.get("EXP_SENADO", "") or ""))]
    raw_san = politica._hcdn_paginate(politica.HCDN_MOVIMIENTOS_RID, q="SANCION")
    san = [(str(r.get("PROYECTO_ID", "")), str(r.get("FECHA", ""))[:10]) for r in raw_san
           if r.get("PROYECTO_ID")]
    out = []
    for ym, cutoff, fin in _hcdn_ventanas_12m():
        pe_ids = {pid for pid, f in pe if cutoff <= f <= fin}
        san_ids = {pid for pid, f in san if cutoff <= f <= fin}
        if pe_ids:
            out.append([f"{ym}-01", round(len(pe_ids & san_ids) / len(pe_ids) * 100.0, 1)])
    return out


def fetch_veto_quorum_serie() -> list:
    """Serie ANUAL del % de sesiones de Diputados fracasadas por período
    legislativo (período = 144 + (año − 2026); mismo criterio que el
    indicador). [[YYYY-01-01, %]]."""
    out = []
    for y in range(2024, date.today().year + 1):
        periodo = f"HCDN{144 + (y - 2026)}"
        try:
            recs = [r for r in politica._hcdn_paginate(politica.HCDN_SESIONES_RID, q=str(y))
                    if str(r.get("PERIODO_ID", "")).startswith(periodo)
                    and str(r.get("SESION_CAMARA", "")).upper() == "DIPUTADOS"]
        except Exception as e:
            print(f"  [WARN] veto_quorum serie {y}: {e}")
            continue
        if recs:
            frac = sum(1 for r in recs if "fracasada" in str(r.get("REUNION_TIPO", "")).lower())
            out.append([f"{y}-01-01", round(frac / len(recs) * 100.0, 1)])
    return out


def fetch_comisiones_serie() -> list:
    """Serie mensual del % de proyectos con dictamen (Orden del Día) SIN
    sanción, ventana móvil de 12 meses — misma fórmula que el indicador.
    [[YYYY-MM-01, %]]."""
    dictamenes = []
    for y in range(2023, date.today().year + 1):
        try:
            dictamenes += politica._hcdn_paginate(politica.HCDN_DICTAMENES_RID, q=str(y))
        except Exception as e:
            print(f"  [WARN] comisiones serie dictámenes {y}: {e}")
    od = [(str(r["EXPEDIENTE"]).strip(), str(r.get("FECHA", ""))[:10]) for r in dictamenes
          if r.get("EXPEDIENTE") and "orden" in str(r.get("TIPO", "")).lower()]
    raw_san = politica._hcdn_paginate(politica.HCDN_MOVIMIENTOS_RID, q="SANCION")
    san = [(str(r.get("PROYECTO_ID", "")).strip(), str(r.get("FECHA", ""))[:10])
           for r in raw_san if r.get("PROYECTO_ID")]
    out = []
    for ym, cutoff, fin in _hcdn_ventanas_12m():
        od_ids = {e for e, f in od if cutoff <= f <= fin}
        san_ids = {p for p, f in san if cutoff <= f <= fin}
        if od_ids:
            pct = round((len(od_ids) - len(od_ids & san_ids)) / len(od_ids) * 100.0, 1)
            out.append([f"{ym}-01", pct])
    return out


def fetch_cohesion_bloque_serie(anio_inicio: int = 2023) -> list:
    """Serie ANUAL de cohesión del bloque LLA en Diputados (índice de Rice
    promedio): un punto por año desde `anio_inicio`, con dias_ventana=366
    para cubrir TODAS las actas divididas del año sin depender de la fecha de
    corrida — mismo criterio que el indicador cohesion_bloque (Tarea 6).
    [[YYYY-01-01, % cohesión]]."""
    out = []
    for anio in range(anio_inicio, date.today().year + 1):
        resultado = politica.fetch_cohesion_bloque(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            out.append([f"{anio}-01-01", resultado["valor"]])
    return out


def fetch_cohesion_bloque_senado_serie(anio_inicio: int = 2023) -> list:
    """Serie ANUAL de cohesión del bloque LLA en el Senado (índice de Rice
    promedio): mismo patrón que fetch_cohesion_bloque_serie (Diputados) —
    un punto por año desde `anio_inicio`, con dias_ventana=366 para cubrir
    TODAS las actas divididas del año sin depender de la fecha de corrida.
    Indicador COMPLEMENTARIO (otra cámara), no reemplaza a cohesion_bloque.
    [[YYYY-01-01, % cohesión]]."""
    out = []
    for anio in range(anio_inicio, date.today().year + 1):
        resultado = politica.fetch_cohesion_bloque_senado(anio=anio, dias_ventana=366)
        if resultado and resultado.get("valor") is not None:
            out.append([f"{anio}-01-01", resultado["valor"]])
    return out


def fetch_adhesion_reformas_provincial_serie() -> list:
    """adhesion_reformas_provincial es un STOCK: la adhesión al RIGI es un
    evento único e irreversible por provincia, no una magnitud que fluctúe
    mes a mes — un solo punto con el valor actual, no un backfill año por
    año (no hay fuente con la fecha en la que cada provincia adhirió, así
    que no hay forma de reconstruir el pasado). Confirmado en vivo
    (2026-07-08): la tabla de MAGyP solo tiene 2 columnas (provincia, link a
    la ley), sin fecha de adhesión; el sitio que sí podría tenerla
    (trivia.consejo.org.ar, donde apuntan los links de ley) devuelve
    "Request Rejected" ante fetch directo — mismo patrón de WAF categórico
    que HCDN Diputados (ADR-0037), no reintentar sin una vía nueva.
    [[YYYY-01-01, % provincias]]."""
    resultado = politica.fetch_adhesion_reformas_provincial()
    if not resultado or resultado.get("valor") is None:
        return []
    return [[f"{date.today().year}-01-01", resultado["valor"]]]


def fetch_cepa_movilizacion_serie(max_paginas: int = 40) -> list:
    """Backfill histórico de movilizacion_cepa: escanea hasta `max_paginas`
    páginas de centrocepa.com.ar/documentos/informes (10 informes por
    página) buscando TODOS los links con "conflictividad"/"conflictos-laborales"
    en la URL -- no solo el más reciente, a diferencia de
    politica.fetch_cepa_movilizacion(). Verificado en vivo (2026-07-08): con
    40 páginas se cubren de sobra los ~4 informes de este tipo publicados
    hasta la fecha (CEPA recién empezó a publicarlos a fines de 2025 -- no
    hay nada más atrás que buscar). Reusa politica._extraer_cifra_cepa /
    politica._fecha_informe_cepa, pero NO se limita a saltear los informes
    donde _extraer_cifra_cepa devuelve None (ausencia de cualquier patrón
    conocido) -- también filtra por el campo "rama" que esa función expone
    (hallazgo en vivo 2026-07-08): el informe 748 ("2 años de Milei") acumula
    desde ene-2024, sin la frase-gatillo "desde inicios del año en curso" que
    usa el indicador vigente, PERO su cuerpo también trae una oración con un
    promedio mensual ("promediando 24 casos por mes") que sí matchea la rama
    m_mes de _extraer_cifra_cepa (rama anterior a esta tarea, no se modifica
    acá) -- por lo tanto NO devuelve None, devuelve {"rama": "m_mes", ...}.
    Esa cifra es una TASA mensual sobre una ventana ene24-sep25, mientras que
    el indicador vigente (rama m_tot, "acumulados desde inicios del año en
    curso") es un CONTEO acumulado -- dos escalas incompatibles
    (CEPA_MAX_CASOS_MES=80 vs. CEPA_MAX_CONFLICTOS_TOT=200) que no deben
    mezclarse en la misma serie. Por eso acá, a diferencia de
    fetch_cepa_movilizacion() (que no discrimina entre ramas porque solo ve
    UN informe a la vez y ese informe siempre viene de m_tot en la
    práctica), se descartan explícitamente las lecturas rama="m_mes": solo
    se conservan lecturas rama="m_tot" ("conflictos acumulados"), homogéneas
    con el valor vigente publicado hoy (50.5 = 101/200*100, informe 809).
    [[YYYY-MM-DD, índice 0-100]]."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[WARN] movilizacion_cepa_serie: beautifulsoup4 no disponible")
        return []

    links = []
    for page in range(max_paginas):
        page_url = politica.CEPA_INFORMES_URL if page == 0 else f"{politica.CEPA_INFORMES_URL}?start={page * 10}"
        try:
            r = requests.get(page_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
        except requests.RequestException:
            break
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href_lower = a["href"].lower()
            if any(kw in href_lower for kw in ("conflictividad", "conflictos-laborales")):
                links.append(a["href"])

    out = []
    vistos = set()
    for href in links:
        if href in vistos:
            continue
        vistos.add(href)
        informe_url = ("https://centrocepa.com.ar" + href) if href.startswith("/") else href
        try:
            r2 = requests.get(informe_url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r2.raise_for_status()
        except requests.RequestException as e:
            print(f"[WARN] movilizacion_cepa_serie: {informe_url}: {e}")
            continue
        cifra_info = politica._extraer_cifra_cepa(r2.text)
        if cifra_info is None or cifra_info["rama"] != "m_tot":
            continue   # sin match, o tasa mensual (m_mes) -- no comparable con el conteo acumulado, ver docstring de _extraer_cifra_cepa
        fecha = politica._fecha_informe_cepa(r2.text)
        out.append([fecha, cifra_info["valor"]])

    out.sort(key=lambda x: x[0])
    return out


POLITICA_DERIVADAS = [
    ("votometro_ventaja_lla", "pp (brecha LLA−PJ)", "Votómetro CIGOB", fetch_votometro_serie),
    ("iaf_transferencias", "% i.a. real", "RON Hacienda + IPC INDEC (dic-dic)", fetch_iaf_serie),
    ("ratio_dnu", "DNUs por ley", "InfoLeg (conteo anual)", fetch_ratio_dnu_serie),
    ("eficacia_legislativa", "% proyectos PE aprobados (12m móviles)", "datos.hcdn.gob.ar CKAN", fetch_eficacia_serie),
    ("veto_quorum", "% sesiones fracasadas (por período)", "datos.hcdn.gob.ar CKAN", fetch_veto_quorum_serie),
    ("comisiones_caidas", "% con dictamen sin sanción (12m móviles)", "datos.hcdn.gob.ar CKAN", fetch_comisiones_serie),
    ("cohesion_bloque", "% cohesión (índice de Rice, anual)",
     "Votaciones nominales Cámara de Diputados — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_serie),
    ("cohesion_bloque_senado", "% cohesión (índice de Rice, Senado, anual)",
     "Votaciones nominales Senado — elaboración CIGOB (scraping directo)",
     fetch_cohesion_bloque_senado_serie),
    ("adhesion_reformas_provincial", "% de provincias (sobre 24) adheridas al RIGI",
     "Tabla de provincias adheridas — Ministerio de Agricultura, Ganadería y Pesca",
     fetch_adhesion_reformas_provincial_serie),
    ("movilizacion_cepa", "Índice de conflictividad social (0-100)",
     "Centro CEPA — informes de conflictividad (elaboración CIGOB)",
     fetch_cepa_movilizacion_serie),
    # protestas_caba NO se registra acá: ya está en GESTION_DERIVADAS
    # (fetch_protestas_serie) y build_series() en publicar.py fusiona TODOS
    # los CSV de output/series/ en un único dict keyed por indicador — la
    # clave "protestas_caba" ya queda disponible para el ITCP de política sin
    # duplicar la descarga (~8 MB de ACLED) ni la lógica de scraping.
]

VIDA_INDEC = [
    # NIVEL del IPC bajo clave propia: es un INSUMO (deflactor del crédito de
    # consumo en publicar), no la serie de la card ipc_total (que publica el
    # % m/m desde macro) — con la misma clave, la fusión de CSVs las mezclaba.
    ("148.3_INIVELNAL_DICI_M_26", "ipc_nivel",    "indice base dic-2016=100", "INDEC/datos.gob.ar"),
    ("42.3_EPH_PUNTUATAL_0_M_30", "desocupacion", "%",                        "INDEC/datos.gob.ar"),
]
# Derivadas: la variación m/m % de cada serie INDEC de índices (misma métrica que
# muestra la card del indicador), reconstruida para todo el histórico disponible.
VIDA_DERIVADAS = [
    ("ipc_alimentos",    "% m/m",           "INDEC serie 146.3", lambda: fetch_indec_var_mensual("146.3_IALIMENNAL_DICI_M_45")),
    ("peso_tarifas",     "% m/m regulados", "INDEC serie 148.3", lambda: fetch_indec_var_mensual("148.3_IREGULANAL_DICI_M_22")),
    ("mortalidad_pymes", "% m/m (IPI desest.)", "INDEC — IPI desestacionalizado",
     lambda: fetch_indec_var_mensual(ITVC_IPI_DESEST_ID)),
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


SENTIMIENTO_SERIE_STORE = Path(__file__).resolve().parents[1] / "data" / "vida" / "sentimiento_serie.json"


def fetch_sentimiento_serie() -> list:
    """Serie MENSUAL del sentimiento digital (ADR-0034): canasta de las 4
    keywords en VENTANA FIJA 2021→hoy con resolución mensual nativa de Trends.
    La escala de Trends es relativa a la ventana consultada, pero el COCIENTE
    entre dos meses de la MISMA consulta es invariante a la renormalización —
    eso vuelve puntuable el B100 vs 4T-2023 (verificado: 3 corridas idénticas,
    amplitud 0,0; r = +0,76 contra el IPC m/m). El mes en curso se descarta
    (incompleto). Store persistente con REEMPLAZO TOTAL en cada descarga sana:
    valores de corridas distintas no se mezclan (escalas distintas).
    [[YYYY-MM-01, interés]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana" / "collectors"))
    import trends as _t
    from config import TRENDS_KEYWORDS, TRENDS_GEO
    store = json.loads(SENTIMIENTO_SERIE_STORE.read_text(encoding="utf-8-sig")) \
        if SENTIMIENTO_SERIE_STORE.exists() else {"_meta": {}, "mensual": {}}
    try:
        _t._patch_urllib3()
        from pytrends.request import TrendReq
        pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 40), retries=2, backoff_factor=1)
        hoy = datetime.today()
        pt.build_payload(TRENDS_KEYWORDS, cat=0,
                         timeframe=f"2021-01-01 {hoy.strftime('%Y-%m-%d')}", geo=TRENDS_GEO)
        df = pt.interest_over_time()
        if df is None or df.empty:
            raise ValueError("Trends devolvió vacío (rate limit)")
        cols = [k for k in TRENDS_KEYWORDS if k in df.columns]
        canasta = df[cols].mean(axis=1)
        mensual = {}
        for d, v in canasta.groupby(canasta.index.strftime("%Y-%m")).mean().items():
            if v > 0 and d < hoy.strftime("%Y-%m"):        # mes en curso: fuera
                mensual[d] = round(float(v), 1)
        if len(mensual) >= 36:                              # descarga sana → REEMPLAZO total
            store["mensual"] = mensual
            store["_meta"] = {"fuente": "Google Trends (canasta mensual, ventana fija 2021→)",
                              "actualizado": datetime.today().strftime("%Y-%m-%d"),
                              "nota": ("ADR-0034: escala relativa a la ventana — el store se "
                                       "reemplaza entero en cada corrida sana; corridas "
                                       "distintas no se mezclan.")}
            SENTIMIENTO_SERIE_STORE.write_text(
                json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  [WARN] sentimiento: Trends no disponible ({str(e)[:60]}); serie del store "
              f"(al {store['_meta'].get('actualizado')})")
    return [[f"{ym}-01", v] for ym, v in sorted(store["mensual"].items())]


VIDA_DERIVADAS.append(
    ("sentimiento_digital", "interés 0–100 (canasta mensual)",
     "Google Trends (ventana fija 2021→, ADR-0034)", fetch_sentimiento_serie)
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
    ("informalidad", "%", "INDEC EPH (52.2, trimestral)", lambda: fetch_indec_x100("52.2_ASDJ_0_0_37")),
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
    """I_IA REDISEÑADO (ADR-0033): encarecimiento RELATIVO de la comida —
    IPC alimentos contra el IPC general, rebaseado a 4T-2023. >100 = la comida
    sube MENOS que el resto de los precios (alivia la canasta de los hogares
    de menores ingresos); <100 = la comida encarece por encima del promedio.
    La versión anterior (IPC alimentos vs RIPTE) correlacionaba r=0,985 con la
    brecha salario/CBT: un tercio del ITVC contaba dos veces el mismo ratio
    salario/comida. Esta métrica es la pregunta de PRECIOS pura, independiente
    del salario. [[YYYY-MM-01, índice]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import INDEC_SERIES
    alim = _nivel_mensual(INDEC_SERIES["ipc_alimentos"])
    gen = _nivel_mensual("148.3_INIVELNAL_DICI_M_26")
    a_base, g_base = _base_t423(alim), _base_t423(gen)
    out = []
    for ym in sorted(set(alim) & set(gen)):
        if ym < "2023-10" or not alim[ym] or not gen[ym]:
            continue
        indice = (a_base / alim[ym]) * (gen[ym] / g_base) * 100.0
        out.append([f"{ym}-01", round(indice, 1)])
    return out


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


IVI_SERIE_STORE = Path(__file__).resolve().parents[1] / "data" / "vida" / "ivi_serie.json"
IVI_ARCHIVO_URL = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=23763"
IVI_ULTIMO_URL = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=2156"
IVI_MESES = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
             "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "SETIEMBRE": 9, "OCTUBRE": 10,
             "NOVIEMBRE": 11, "DICIEMBRE": 12}


def _ivi_parse_pdf(content: bytes) -> tuple | None:
    """(YYYY-MM, ivi_pct) desde la primera página del informe mensual del
    LICIP: encabezado 'MES AÑO' + 'XX.X % de los hogares'. Patrón verificado
    en informes de 2020, 2025 y 2026."""
    import io as _io
    from pypdf import PdfReader
    t = " ".join(PdfReader(_io.BytesIO(content)).pages[0].extract_text().split())
    m = re.search(r"([A-ZÑ]+)\s+(20\d\d)", t)
    v = re.search(r"(\d{1,2}[.,]\d)\s*%\s*de los hogares", t)
    if not (m and v and m.group(1).upper() in IVI_MESES):
        return None
    ym = f"{m.group(2)}-{IVI_MESES[m.group(1).upper()]:02d}"
    return ym, float(v.group(1).replace(",", "."))


def fetch_ivi_serie() -> list:
    """IVI — Índice de Victimización del LICIP (UTDT): % de hogares de 40
    centros urbanos que sufrieron al menos un delito en los últimos 12 meses
    (denunciado o no — captura la cifra negra), encuesta MENSUAL (ADR-0032:
    reemplaza al SNIC anual como métrica del ITVC; el SNIC queda de contraste).
    La ventana de 12 meses de la pregunta desestacionaliza por construcción.
    STORE persistente: cada corrida descubre los PDFs del archivo + el último
    informe, parsea solo los no procesados y acumula. [[YYYY-MM-01, %]]."""
    store = json.loads(IVI_SERIE_STORE.read_text(encoding="utf-8-sig")) \
        if IVI_SERIE_STORE.exists() else {"_meta": {}, "procesados": [], "mensual": {}}
    try:
        urls = set()
        for pagina in (IVI_ARCHIVO_URL, IVI_ULTIMO_URL):
            r = requests.get(pagina, headers=HTTP_HEADERS, timeout=60)
            r.raise_for_status()
            urls |= set(re.findall(r'https://www\.utdt\.edu/download\.php\?fname=[^"&]+\.pdf', r.text))
        nuevos = sorted(urls - set(store["procesados"]))
        for url in nuevos:
            try:
                rp = requests.get(url, headers=HTTP_HEADERS, timeout=90)
                rp.raise_for_status()
                parsed = _ivi_parse_pdf(rp.content)
                if parsed:
                    ym, v = parsed
                    store["mensual"][ym] = v
                store["procesados"].append(url)
            except Exception as e:
                print(f"  [WARN] IVI: PDF no procesado ({url[-30:]}): {str(e)[:50]}")
        if nuevos:
            store["_meta"] = {"fuente": "UTDT — LICIP, Índice de Victimización (informes mensuales PDF)",
                              "actualizado": datetime.today().strftime("%Y-%m-%d"),
                              "nota": ("Encuesta mensual, 40 centros urbanos, ventana 12 meses. "
                                       "PDFs con URL por hash: se descubren desde el listado y "
                                       "se procesan una sola vez (ADR-0032).")}
            IVI_SERIE_STORE.write_text(
                json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  [OK] IVI: {len(nuevos)} PDFs nuevos procesados "
                  f"(serie: {len(store['mensual'])} meses)")
    except Exception as e:
        print(f"  [WARN] IVI: listado UTDT no disponible ({str(e)[:60]}); serie del store")
    return [[f"{ym}-01", v] for ym, v in sorted(store["mensual"].items())]


SNIC_SERIE_STORE = Path(__file__).resolve().parents[1] / "data" / "vida" / "snic_serie.json"


def fetch_inseguridad_serie() -> list:
    """Serie ANUAL de hechos delictivos del SNIC (total país), con el MISMO
    criterio de suma que el colector — VALIDADO contra los totales oficiales
    (2016: 1,59M · 2023: 2,4M · dinámica 2025 = informe 01-jun-2026). Con
    STORE PERSISTENTE (barrido vida 10/13): cloud-snic sufre caídas de días
    enteros; si el host responde se refresca el store, si no, la serie sale
    del store — la web nunca se queda sin serie (antes, el apagón hacía que
    el fallback del histórico inyectara totales anuales con fechas de
    corrida). El CSV oficial se revisa retroactivamente: cada refresco pisa
    la serie completa. [[YYYY-12-01, hechos]]."""
    import csv as _csv
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import SNIC_CSV
    store = json.loads(SNIC_SERIE_STORE.read_text(encoding="utf-8-sig"))
    try:
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
        por_anio = {a: v for a, v in por_anio.items() if int(a) >= 2014 and v > 0}
        if len(por_anio) >= 8:                       # descarga sana → refrescar store
            store["anual"] = {a: por_anio[a] for a in sorted(por_anio)}
            store["_meta"]["actualizado"] = datetime.today().strftime("%Y-%m-%d")
            SNIC_SERIE_STORE.write_text(
                json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  [WARN] inseguridad: cloud-snic caído ({str(e)[:60]}); serie del store "
              f"(al {store['_meta'].get('actualizado')})")
    return [[f"{a}-12-01", v] for a, v in sorted(store["anual"].items())]


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
    # El informe del MES PASADO (M−1) sale en los primeros días del mes
    # corriente y la card (fetch_ciccra) lo levanta apenas existe: la serie
    # también debe intentarlo, pero SIN persistir None (el None permanente es
    # la razón por la que el bucle principal corta en M−2) — si el PDF todavía
    # no salió, se reintenta en la corrida siguiente. Sin esto, el titular
    # avanza un mes antes que la serie y el gate G3 corta el pipeline.
    ult = hoy.replace(day=1) - timedelta(days=1)
    ym_ult = f"{ult.year}-{ult.month:02d}"
    if cache.get(ym_ult) is None:
        url = _url_pdf(ult.year, ult.month)
        for u in (url, url.replace(f"-{ult.year}-", f"b-{ult.year}-", 1)):
            try:
                r = requests.get(u, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
                if r.status_code == 200 and r.content[:4] == b"%PDF":
                    valor = _extraer_per_capita(r.content)
                    if valor is not None:
                        cache[ym_ult] = valor
                        CARNE_SERIE_STORE.write_text(
                            json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
                        break
            except requests.RequestException:
                continue
    return [[f"{ym}-01", v] for ym, v in sorted(cache.items()) if v]


def fetch_motos_serie() -> list:
    """Serie mensual de patentamientos de motovehículos vía la API de CAFAM
    (la misma fuente del colector; expone meses históricos — verificado
    jul-2026). Desde nov-2022: 11 meses antes de la línea base del ITVC para
    que el rebase por acumulado móvil de 12 meses (ADR-0024, motos tienen
    estacionalidad fuerte: enero ≈ 2× junio) tenga ventanas completas en el
    4T-2023. [[YYYY-MM-01, unidades]]."""
    sys.path.insert(0, str(Path(__file__).parent / "vida_cotidiana"))
    from config import CAFAM_API
    hoy = date.today()
    fin = (hoy.replace(day=1) - timedelta(days=1))     # último mes completo
    out = []
    y, m = 2022, 11
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
    # inseguridad = IVI mensual (ADR-0032); el SNIC anual sigue como serie de
    # contraste bajo clave propia (sin card: alimenta la ficha y validaciones)
    ("inseguridad", "% de hogares víctimas (12 meses)", "UTDT — IVI (LICIP)", fetch_ivi_serie),
    ("inseguridad_snic", "hechos/año (total país)", "SNIC (CSV oficial, suma anual)", fetch_inseguridad_serie),
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
    # Antes del primer proyecto aprobado la inversión RIGI era 0 (el régimen
    # se reglamentó en ago-2024): la serie arranca en dic-2023 con ceros.
    y, m = 2023, 12
    primero = min(por_mes) if por_mes else None
    while primero and f"{y}-{m:02d}" < primero:
        por_mes[f"{y}-{m:02d}"] = 0
        m += 1
        if m > 12:
            m = 1; y += 1
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
    # dic-2023: el canal de derivación directa nace con el DNU 70/23 (dic-2023);
    # antes del primer XLSX (ene-2024) los derivados eran 0.
    if out and out[0][0] == "2024-01-01":
        out.insert(0, ["2023-12-01", 0.0])
    return out


def fetch_protestas_serie() -> list:
    """Serie mensual de eventos de protesta en CABA desde el store que llena
    gestion.actualizar_protestas_caba() (evita re-bajar los ~8 MB de ACLED:
    el colector corre antes en el pipeline). El último mes se EXCLUYE si el
    archivo ACLED no llega a fin de mes (misma regla que el indicador: un mes
    parcial dibujaría un derrumbe falso al final de la curva).
    [[YYYY-MM-01, eventos]]."""
    import json as _json
    if not gestion.PROTESTAS_STORE_PATH.exists():
        return []
    store = _json.loads(gestion.PROTESTAS_STORE_PATH.read_text(encoding="utf-8"))
    mensual = store.get("mensual", {})
    hasta = store.get("_meta", {}).get("hasta_semana", "")
    yms = sorted(mensual)
    if hasta and yms and hasta[:7] == yms[-1]:
        a, m = int(hasta[:4]), int(hasta[5:7])
        if int(hasta[8:10]) < calendar.monthrange(a, m)[1]:
            yms = yms[:-1]
    return [[f"{ym}-01", mensual[ym]] for ym in yms]


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


def fetch_alicuota_serie() -> list:
    """Serie mensual de la ALÍCUOTA EFECTIVA del comercio exterior
    (apertura_comercial desde el ADR-0021: la brecha salió del compuesto):
    recaudación DEX+DIM en USD por el A3500 promedio del mes, sobre el
    intercambio expo+impo del ICA. Desde dic-2023. [[YYYY-MM-01, %]]."""
    dex  = gestion._indec_nivel_mensual(gestion.DEX_ID, limit=48)
    dim  = gestion._indec_nivel_mensual(gestion.DIM_ID, limit=48)
    expo = gestion._indec_nivel_mensual(gestion.EXPO_ICA_ID, limit=48)
    impo = gestion._indec_nivel_mensual(gestion.IMPO_ICA_ID, limit=48)
    dias = (date.today() - date(2023, 11, 25)).days
    tc   = gestion._tc_mayorista_promedio_por_mes(dias=dias)
    out = []
    for ym in sorted(set(dex) & set(dim) & set(expo) & set(impo) & set(tc)):
        if ym < "2023-12" or expo[ym] + impo[ym] <= 0 or tc[ym] <= 0:
            continue
        alicuota = 100.0 * ((dex[ym] + dim[ym]) / tc[ym]) / (expo[ym] + impo[ym])
        out.append([f"{ym}-01", round(alicuota, 2)])
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


PRIVATIZACIONES_FECHAS_STORE = (Path(__file__).resolve().parents[1] / "data" / "gestion"
                                / "privatizaciones_fechas.json")


def fetch_privatizaciones_serie() -> list:
    """Serie mensual del avance de privatizaciones (promedio de etapas/4 × 100,
    la MISMA fórmula del indicador) reconstruida con las transiciones de etapa
    FECHADAS por norma del BO (privatizaciones_fechas.json, verificadas
    jul-2026). El mes corriente usa las etapas del store vivo
    (privatizaciones.json) y avisa si no reconcilia con las transiciones —
    señal de que falta fechar un hito nuevo. [[YYYY-MM-01, %]]."""
    fechas = json.loads(PRIVATIZACIONES_FECHAS_STORE.read_text(encoding="utf-8-sig"))["empresas"]
    live_path = Path(__file__).resolve().parents[1] / "data" / "gestion" / "privatizaciones.json"
    live = json.loads(live_path.read_text(encoding="utf-8-sig"))["empresas"]

    def etapa_en(emp: str, ym: str) -> float:
        vigente = 0.0
        for t in fechas.get(emp, []):
            if t["fecha"] <= ym:
                vigente = float(t["etapa"])
        return vigente

    empresas = sorted(live)
    hoy_ym = date.today().strftime("%Y-%m")
    for emp in empresas:
        if abs(etapa_en(emp, hoy_ym) - float(live[emp]["etapa"])) > 0.01:
            print(f"  [WARN] privatizaciones serie: {emp} etapa live "
                  f"{live[emp]['etapa']} != fechada {etapa_en(emp, hoy_ym)} — "
                  f"agregar la transición a privatizaciones_fechas.json")
    out = []
    y, m = 2023, 12
    while (y, m) <= (int(hoy_ym[:4]), int(hoy_ym[5:])):
        ym = f"{y}-{m:02d}"
        if ym == hoy_ym:
            etapas = [float(live[e]["etapa"]) for e in empresas]
        else:
            etapas = [etapa_en(e, ym) for e in empresas]
        out.append([f"{ym}-01", round(sum(etapas) / len(etapas) / 4.0 * 100.0, 1)])
        m += 1
        if m > 12:
            m = 1; y += 1
    return out


def fetch_fal_serie() -> list:
    """Serie mensual del índice FAL reconstruida desde el BOLETÍN OFICIAL
    (jul-2026): menciones acumuladas de "fondo de cese laboral" hasta el fin
    de cada mes → cobertura (420 = plena, calibración del colector) → índice
    con adopción financiera = 0 (el registro CNV nunca tuvo altas — dato
    duro). Una consulta BO por mes (~30; el endpoint tolera batch sin
    throttling, verificado 03-jul-2026). Fallback al histórico acumulado si
    el BO no responde. [[YYYY-MM-01, índice]]."""
    try:
        out = []
        hoy = date.today()
        fin = hoy.replace(day=1) - timedelta(days=1)      # último mes completo
        y, m = 2023, 12
        while (y, m) <= (fin.year, fin.month):
            ult_dia = calendar.monthrange(y, m)[1]
            n = gestion._bo_conteo(gestion.FAL_BO_TEXTO,
                                   hasta=f"{ult_dia:02d}/{m:02d}/{y}")
            cobertura = min(100.0, n * 100.0 / gestion.FAL_BO_MENCIONES_PLENO)
            indice = round((0.40 * cobertura) / 0.70, 1)   # financiera = 0 histórico
            out.append([f"{y}-{m:02d}-01", indice])
            m += 1
            if m > 12:
                m, y = 1, y + 1
        if len(out) >= 12:
            return out
    except Exception as e:
        print(f"  [WARN] fal serie BO (fallback histórico): {e}")
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


UTDT_ICG_LISTADO = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=28756"
UTDT_ICG_REFERER = "https://www.utdt.edu/ver_contenido.php?id_contenido=1351&id_item_menu=2970"


def fetch_icg_serie() -> list:
    """Serie mensual del ICG UTDT (Índice de Confianza en el Gobierno, 0-5) —
    insumo de la validación externa del ITCG (no es indicador del cinturón).
    El XLS oficial viene TRANSPUESTO (fechas en columnas): en cada hoja se
    busca la fila de fechas y la fila rotulada ICG. El listado de descargas
    exige Referer (sin él devuelve vacío). [[YYYY-MM-01, índice]]."""
    import xlrd
    h = dict(HTTP_HEADERS, Referer=UTDT_ICG_REFERER)
    r = requests.get(UTDT_ICG_LISTADO, headers=h, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    m = re.search(r"download\.php\?fname=([^\"'\s>]+\.xls)\b", r.text, re.IGNORECASE)
    if not m:
        raise ValueError("listado ICG sin XLS (¿cambió la página o falta Referer?)")
    r = requests.get(f"https://www.utdt.edu/download.php?fname={m.group(1)}",
                     headers=h, timeout=60, verify=False)
    r.raise_for_status()
    wb = xlrd.open_workbook(file_contents=r.content)
    out = {}
    for ws in wb.sheets():
        fila_fechas = next((i for i in range(ws.nrows)
                            if sum(1 for j in range(ws.ncols)
                                   if ws.cell(i, j).ctype == xlrd.XL_CELL_DATE) >= 5), None)
        if fila_fechas is None:
            continue
        fila_icg = next((i for i in range(fila_fechas + 1, min(fila_fechas + 4, ws.nrows))
                         if "icg" in str(ws.cell(i, 1).value).lower()
                         or "icg" in str(ws.cell(i, 0).value).lower()), fila_fechas + 1)
        for j in range(ws.ncols):
            fc, vc = ws.cell(fila_fechas, j), ws.cell(fila_icg, j)
            if fc.ctype == xlrd.XL_CELL_DATE and vc.ctype == xlrd.XL_CELL_NUMBER:
                t = xlrd.xldate_as_tuple(fc.value, wb.datemode)
                out[f"{t[0]}-{t[1]:02d}-01"] = round(float(vc.value), 3)
    return sorted([f, v] for f, v in out.items())


def fetch_protocolo_serie() -> list:
    """Serie del IRPC (reducción de cortes CABA vs 2023) por escalones ANUALES
    de los anclajes públicos de Diagnóstico Político (ADR-0025): cada año
    cerrado aporta su IRPC y el valor se arrastra mes a mes hasta el siguiente
    (regla del último dato disponible). [[YYYY-MM-01, %]]."""
    dp = json.loads((Path(__file__).resolve().parents[1] / "data" / "gestion" /
                     "dp_piquetes.json").read_text(encoding="utf-8-sig"))
    caba = {int(k): int(v) for k, v in dp["caba"].items()}
    base = caba[2023]
    hoy = date.today()
    fin = hoy.replace(day=1) - timedelta(days=1)
    out = []
    y, m = 2024, 1
    while (y, m) <= (fin.year, fin.month):
        anio_dato = y if y in caba else max(a for a in caba if 2023 < a <= y)
        irpc = round((1.0 - caba[anio_dato] / base) * 100.0, 1)
        out.append([f"{y}-{m:02d}-01", irpc])
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


GESTION_DERIVADAS = [
    ("protocolo_antipiquetes", "% reducción de cortes CABA vs 2023 (IRPC, anual)",
     "Diagnóstico Político (monitoreos públicos)", fetch_protocolo_serie),
    ("icg_utdt", "índice 0-5 (confianza en el gobierno)", "UTDT (ICG, serie XLS)", fetch_icg_serie),
    ("apertura_comercial", "% alícuota efectiva del comercio exterior", "ARCA (DEX+DIM) + INDEC ICA + BCRA A3500", fetch_alicuota_serie),
    ("concesiones_infraestructura", "% km adjudicados RFC", "CONTRAT.AR + RFC (hitos fechados)", fetch_concesiones_serie),
    ("privatizaciones", "% avance (etapas 0-4, cartera Ley Bases)", "BO — hitos fechados (elab. CIGOB)", fetch_privatizaciones_serie),
    ("fal_modernizacion_laboral", "Índice 0–100 (FAL)", "Boletín Oficial (menciones) + CNV (registro FCI)", fetch_fal_serie),
    ("rigi_inversiones", "US$ M aprobados (acum.)", "Min. Economía RIGI + BO (fechas de sanción)", fetch_rigi_serie),
    ("desregulacion_normativa", "Normas (conteo acum.)", "InfoLeg ('deroga' desde dic-2023)", lambda: fetch_infoleg_serie("deroga")),
    # A % calibrado (45 actos = plan completo, misma escala que el titular):
    # a diferencia de desregulación (100 normas = 100%), acá conteo ≠ %.
    ("reestructuracion_organismos", "% de avance (proxy InfoLeg, 45 actos = 100%)",
     "InfoLeg ('disolucion' desde dic-2023)",
     lambda: [[f, round(min(100.0, v / 45.0 * 100.0), 1)] for f, v in fetch_infoleg_serie("disolucion")]),
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
