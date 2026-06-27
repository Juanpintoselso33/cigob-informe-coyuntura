"""
Colector Cinturón Macro — CIGOB
Patrón estándar: URLs → fetch → score → cache → exit codes
Ejecutar desde projects/informe_coyuntura/: python scripts/macro.py
"""
import sys
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

# ── URL Constants (NFR6: URLs al inicio del script) ───────────────────────────
INDEC_SERIES_BASE   = "https://apis.datos.gob.ar/series/api/series/"
BCRA_VARIABLES_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"

# INDEC — series IDs verificados en datos.gob.ar
INDEC_IPC_ID         = "148.3_INIVELNAL_DICI_M_26"     # IPC total nacional mensual
INDEC_EMAE_IA_ID     = "143.3_ICE_SERVIA_2004_A_25"    # EMAE variación i.a. mensual (base 2004)
INDEC_SALDO_COM_ID   = "164.3_SOTALTAL_0_0_8"          # Saldo comercial total mensual (M USD) — FALLBACK, ~14 meses de rezago
INDEC_EXPO_ICA_ID    = "74.3_IET_0_M_16"               # ICA exportaciones totales mensual (M USD)
INDEC_IMPO_ICA_ID    = "74.3_IIT_0_M_25"               # ICA importaciones totales mensual (M USD)
INDEC_RECAUDACION_ID = "172.3_TL_RECAION_M_0_0_17"     # Recaudación total mensual (M ARS)
INDEC_TCRM_ID        = "116.3_TCRMA_0_M_36"            # Tipo de Cambio Real Multilateral (base 2010=100)

# BCRA — variable IDs verificados en api.bcra.gob.ar v4.0
BCRA_RESERVAS_ID    = 1    # Reservas internacionales BRUTAS (millones USD)
BCRA_BADLAR_ID      = 7    # BADLAR bancos privados (% anual) — contexto + insumo del IdC
BCRA_REM_IPC_ID     = 29   # REM: mediana expectativas IPC próximos 12 meses (% anual)
BCRA_PRESTAMOS_ID   = 26   # Préstamos sector privado (millones ARS) — contexto
BCRA_BASE_MON_ID    = 15   # Base monetaria (millones ARS)
BCRA_TC_MAYOR_ID    = 5    # Tipo de cambio mayorista de referencia (ARS/USD)
BCRA_DEP_PRIV_ID    = 100  # Depósitos del sector privado no financiero (incluye cedros) — insumo IdC
BCRA_PREST_PRIV_ID  = 117  # Préstamos otorgados al sector privado — insumo IdC

HTTP_TIMEOUT = 30
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}

logging.basicConfig(level=logging.WARNING, format="%(message)s")

CINTURON = "macro"
INDICADORES_ESPERADOS = [
    "ipc_total", "reservas_bcra", "idc", "badlar",
    "emae_ia", "saldo_comercial_12m", "recaudacion", "tcrm",
    "rem_ipc_12m", "prestamos_privados", "base_monetaria", "tc_mayorista",
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


RESERVAS_PASIVOS_PATH = PROJECT_DIR / "data" / "macro" / "reservas_netas_pasivos.json"
RESERVAS_PASIVOS_COMPONENTES = ["encajes_usd", "swap_china", "prestamos_ooii", "repos_12m"]


def fetch_reservas_netas() -> dict | None:
    """Reservas NETAS según la metodología Machado/OPEN, calculadas con datos
    oficiales: brutas (BCRA, automáticas) menos los pasivos en moneda extranjera
    (encajes de depósitos USD privados, swap China, préstamos a OOII y repos a
    ≤12m). Los pasivos —que se mueven lento— se leen de un config sembrado con
    el desglose oficial del balance del BCRA; las brutas se actualizan solas.
    Así el número es propio (lo calculamos nosotros, no lo scrapeamos)."""
    try:
        brutas = float(_bcra_ultimo(BCRA_RESERVAS_ID)["valor"])
        fecha  = _bcra_ultimo(BCRA_RESERVAS_ID)["fecha"]
        with open(RESERVAS_PASIVOS_PATH, encoding="utf-8") as f:
            pasivos = json.load(f)
        total_pasivos = sum(float(pasivos[k]) for k in RESERVAS_PASIVOS_COMPONENTES)
        netas = brutas - total_pasivos
        return {
            "valor": round(netas, 0),
            "unidad": "mill USD (netas)",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_RESERVAS_ID} − pasivos BCRA (metodología Machado/OPEN)",
            "fecha_dato": fecha,
            "reservas_brutas": round(brutas, 0),
            "pasivos": {k: float(pasivos[k]) for k in RESERVAS_PASIVOS_COMPONENTES},
            "pasivos_total": round(total_pasivos, 0),
            "pasivos_actualizado": pasivos.get("actualizado"),
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


def fetch_idc() -> dict | None:
    """Índice de Capacidad Prestable (doc "260626 aportes"). Reemplaza a la tasa
    en la dimensión de financiamiento. Tres componentes mensuales (~1,0):
      • Precio:     1 + tasa REAL mensual de la BADLAR (TEM − IPC m/m).
      • Volumen:    ratio mensual de depósitos privados deflactados por IPC.
      • Asignación: ratio mensual de holgura prestable (1−R_t)/(1−R_{t-1}),
                    R = préstamos/depósitos del sector privado.
    Índice >1,02 = expansión (verde); 0,98-1,02 = neutro (amarillo); <0,98 = rojo."""
    try:
        ipc_m   = _ipc_mensual()
        badlar  = float(_bcra_ultimo(BCRA_BADLAR_ID)["valor"])
        tem     = ((1.0 + badlar / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0
        i_real  = tem - ipc_m
        precio  = 1.0 + i_real / 100.0

        dep = _bcra_par(BCRA_DEP_PRIV_ID)
        volumen = (dep["actual"] / dep["anterior"]) / (1.0 + ipc_m / 100.0)

        pre = _bcra_par(BCRA_PREST_PRIV_ID)
        r_t = pre["actual"]   / dep["actual"]
        r_p = pre["anterior"] / dep["anterior"]
        asignacion = (1.0 - r_t) / (1.0 - r_p)

        idc = itcm.indice_capacidad_prestable(precio, volumen, asignacion)
        semaforo = "verde" if idc > 1.02 else "amarillo" if idc >= 0.98 else "rojo"
        return {
            "valor": round(idc, 4),
            "unidad": "índice (~1,0)",
            "fuente": (f"{BCRA_VARIABLES_BASE}/{BCRA_BADLAR_ID},{BCRA_DEP_PRIV_ID},"
                       f"{BCRA_PREST_PRIV_ID} + IPC INDEC"),
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
            "unidad": "mill USD acumulado 12m",
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
            "unidad": "mill USD acumulado 12m",
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


def fetch_tcrm() -> dict | None:
    try:
        data = _indec_serie(INDEC_TCRM_ID, limit=2)
        val  = data[0][1]
        return {
            "valor": round(float(val), 2),
            "unidad": "índice base 2010=100",
            "fuente": INDEC_SERIES_BASE,
            "fecha_dato": data[0][0],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("tcrm", e)
        return None


def fetch_rem_ipc_12m() -> dict | None:
    try:
        ultimo = _bcra_ultimo(BCRA_REM_IPC_ID)
        return {
            "valor": round(float(ultimo["valor"]), 1),
            "unidad": "% anual esperado (mediana REM)",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_REM_IPC_ID}",
            "fecha_dato": ultimo["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("rem_ipc_12m", e)
        return None


def fetch_prestamos_privados() -> dict | None:
    try:
        result = _bcra_variacion_m(BCRA_PRESTAMOS_ID)
        return {
            "valor": result["var_m"],
            "unidad": "% var mensual nominal",
            "fuente": f"{BCRA_VARIABLES_BASE}/{BCRA_PRESTAMOS_ID}",
            "fecha_dato": result["fecha"],
            "desactualizado": False,
        }
    except Exception as e:
        _warn("prestamos_privados", e)
        return None


def fetch_base_monetaria() -> dict | None:
    try:
        result = _bcra_variacion_m(BCRA_BASE_MON_ID)
        return {
            "valor": result["var_m"],
            "unidad": "% var mensual nominal",
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
            "unidad": "% var mensual",
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
