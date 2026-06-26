"""
descargar_series.py — Descarga series históricas por cinturón a CSV
Salida: output/series/macro.csv | politica.csv | vida_cotidiana.csv | gestion.csv
Columnas: fecha, indicador, valor, fuente
"""
import sys
import csv
import requests
import urllib3
from datetime import datetime, timedelta
from pathlib import Path

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


def fetch_spread_intermediacion(dias: int = 540) -> list:
    """Spread de intermediación derivado: tasa activa (adelantos en cta. cte.,
    var 13) − pasiva (depósitos a 30 días, var 12), muestreado a fin de mes."""
    ade = {f: float(v) for f, v in fetch_bcra(13, dias)}
    dep = {f: float(v) for f, v in fetch_bcra(12, dias)}
    por_mes = {}
    for f in sorted(ade.keys() & dep.keys()):   # asc → conserva el último día de cada mes
        por_mes[f[:7]] = f
    return [[por_mes[m], round(ade[por_mes[m]] - dep[por_mes[m]], 2)]
            for m in sorted(por_mes, reverse=True)]


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
    ("116.3_TCRMA_0_M_36",         "tcrm",            "indice base 2010=100","INDEC/datos.gob.ar"),
]
MACRO_DERIVADAS = [
    ("saldo_comercial", "M USD", "INDEC/datos.gob.ar (ICA expo−impo)", fetch_saldo_ica),
    ("spread_intermediacion", "pts", "BCRA (adelantos − depósitos)", fetch_spread_intermediacion),
]
MACRO_BCRA = [
    (1,  "reservas_bcra",      "M USD",    "BCRA"),
    (7,  "badlar",             "% anual",  "BCRA"),
    (29, "rem_ipc_12m",        "% anual",  "BCRA"),
    (26, "prestamos_privados", "M ARS",    "BCRA"),
    (15, "base_monetaria",     "M ARS",    "BCRA"),
    (5,  "tc_mayorista",       "ARS/USD",  "BCRA"),
]

POLITICA_INDEC = []
# Cinturón político usa Votómetro HTML (parser en politica.py) + manuales.json
# No hay series INDEC descargables para estos indicadores

VIDA_INDEC = [
    ("148.3_INIVELNAL_DICI_M_26", "ipc_total",    "indice base dic-2016=100", "INDEC/datos.gob.ar"),
    ("42.3_EPH_PUNTUATAL_0_M_30", "desocupacion", "%",                        "INDEC/datos.gob.ar"),
]
# icc_utdt: sin API de series — solo disponible vía scraping XLS UTDT

GESTION_INDEC = [
    ("149.1_SOR_PUBICO_OCTU_0_14",   "indice_salarios_publico", "indice base oct-2016=100", "INDEC/datos.gob.ar"),
    ("33.4_ISAC_CEMENAND_0_0_21_24", "isac_construccion",       "indice base 2004=100",     "INDEC/datos.gob.ar"),
]


if __name__ == "__main__":
    print("=== MACRO ===")
    descargar("macro", MACRO_INDEC, MACRO_BCRA, MACRO_DERIVADAS)

    print("\n=== POLÍTICA ===")
    print("  [SKIP] cinturón político — indicadores manuales + Votómetro HTML, sin series INDEC")
    descargar("politica", POLITICA_INDEC, [])

    print("\n=== VIDA COTIDIANA ===")
    print("  [SKIP] icc_utdt — sin API, requiere scraping XLS UTDT")
    descargar("vida_cotidiana", VIDA_INDEC, [])

    print("\n=== GESTIÓN ===")
    descargar("gestion", GESTION_INDEC, [])

    print(f"\nCSVs en {OUTPUT_DIR.resolve()}")
