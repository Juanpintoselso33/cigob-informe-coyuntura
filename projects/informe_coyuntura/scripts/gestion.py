"""
Colector Cinturón Gestión — CIGOB
Mide cumplimiento de reformas del Estado y compromisos de la APN (dic-2023–).
Score 0-10: mayor = mayor brecha compromisos/ejecución (tensión gerencial).

Indicadores AUTO (6):
  cepo_mulc               — brecha CCL/mayorista (dolarapi.com)
  reduccion_estado        — variación empleo sector público vs Q4-2023 (datos.gob.ar INDEC)
  apertura_comercial      — variación i.a. importaciones totales (datos.gob.ar INDEC)
  desregulacion_normativa — count normas "deroga" vía InfoLeg (sesión POST)
  reestructuracion_organismos — count normas "disolucion" vía InfoLeg (sesión POST)
  rigi_inversiones        — count Resoluciones tipo=3 texto="VPU" vía InfoLeg (sesión POST)

Indicadores BLOQUEADOS (caen a manuales.json):
  libertad_opcion_salud — SSS usa fingerprinting back-end; retorna "No se reportan datos" incluso con Playwright
  privatizaciones       — contar normas ≠ privatización completada; sin proxy confiable

Indicadores manual (manuales.json):
  concesiones_infraestructura, asistencia_directa,
  fal_modernizacion_laboral, protocolo_antipiquetes
"""
import re
import sys
import json
import requests
import logging
from datetime import datetime, date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
PROJECT_DIR   = SCRIPT_DIR.parent
CACHE_PATH    = PROJECT_DIR / "output" / "cache" / "gestion.json"
MANUALES_PATH = PROJECT_DIR / "data" / "gestion" / "manuales.json"

# ── URLs ──────────────────────────────────────────────────────────────────────
DOLARAPI_URL        = "https://dolarapi.com/v1/dolares"
INDEC_SERIES_BASE   = "https://apis.datos.gob.ar/series/api/series/"
INFOLEG_HOME        = "https://servicios.infoleg.gob.ar/infolegInternet/"
SSS_OPCIONES_URL    = "https://www.sssalud.gob.ar/index.php"
RIGI_PORTAL_URL     = "https://www.argentina.gob.ar/economia/industria/rigi"
BO_API_URL          = "https://www.boletinoficial.gob.ar/norma/detallePrimera"

# datos.gob.ar series IDs
EMPLEO_PUBLICO_ID = "324.1_TOTAL_SECTAJO__36"  # sector público puestos trabajo (trimestral)
IMPORTACIONES_ID  = "163.3_MTALTAL_0_0_7"       # importaciones totales (mensual, M USD)

HTTP_TIMEOUT = 60
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}

logging.basicConfig(level=logging.WARNING, format="%(message)s")

CINTURON = "gestion"
INDICADORES_ESPERADOS = [
    "cepo_mulc",
    "privatizaciones",
    "concesiones_infraestructura",
    "reduccion_estado",
    "reestructuracion_organismos",
    "rigi_inversiones",
    "desregulacion_normativa",
    "apertura_comercial",
    "asistencia_directa",
    "fal_modernizacion_laboral",
    "libertad_opcion_salud",
    "protocolo_antipiquetes",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_manuales() -> dict:
    if not MANUALES_PATH.exists():
        return {}
    with open(MANUALES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _warn(ind: str, err: Exception) -> None:
    print(f"[WARN] {CINTURON}.{ind}: {err}. Usando fallback.")


def _infoleg_post(texto: str, tipo_norma: str, fecha_desde: tuple, fecha_hasta: tuple) -> int:
    """
    Sesión POST en InfoLeg con reintento automático (2 intentos).
    Retorna el conteo de normas encontradas.
    fecha_desde / fecha_hasta: (dia, mes, anio) como strings.
    """
    last_err = None
    for attempt in range(2):
        try:
            session = requests.Session()
            r_home = session.get(INFOLEG_HOME, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r_home.raise_for_status()

            action_m = re.search(r'action="(/infolegInternet/[^"]+)"', r_home.text)
            if not action_m:
                raise ValueError("No se encontró form action URL en InfoLeg home")
            action_url = "https://servicios.infoleg.gob.ar" + action_m.group(1)

            post_data = {
                "tipoNorma":    tipo_norma,
                "numero":       "",
                "anioSancion":  "",
                "dependencia":  "",
                "diaPubDesde":  fecha_desde[0],
                "mesPubDesde":  fecha_desde[1],
                "anioPubDesde": fecha_desde[2],
                "diaPubHasta":  fecha_hasta[0],
                "mesPubHasta":  fecha_hasta[1],
                "anioPubHasta": fecha_hasta[2],
                "texto":        texto,
            }
            r = session.post(action_url, data=post_data, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
            r.raise_for_status()

            m = re.search(r"Encontradas?[:\s]+(\d+)", r.text, re.IGNORECASE)
            if not m:
                raise ValueError("Conteo no encontrado en respuesta InfoLeg")
            return int(m.group(1))
        except Exception as e:
            last_err = e
            if attempt == 0:
                print(f"[RETRY] infoleg texto='{texto}': {e}. Reintentando...")
    raise last_err


def _avance_to_tension(avance_pct: float) -> float:
    """avance_pct (0–100) → tension score (0–10). Más reforma ejecutada = menos tensión."""
    return round(10.0 * (1.0 - float(avance_pct) / 100.0), 1)


def _manual_entry(nombre: str, manuales: dict, cache_anterior: dict) -> dict | None:
    """Devuelve entrada desde manuales.json o cache anterior como último recurso."""
    m = manuales.get(nombre, {})
    if m and m.get("avance_pct") is not None:
        return {
            "valor":          m.get("valor"),
            "avance_pct":     float(m["avance_pct"]),
            "unidad":         m.get("unidad", ""),
            "fuente":         m.get("fuente", "manual"),
            "fecha_dato":     m.get("fecha_dato", ""),
            "desactualizado": m.get("estado") in ("estimado", "placeholder"),
        }
    prev = cache_anterior.get("indicadores", {}).get(nombre, {})
    if prev and prev.get("avance_pct") is not None:
        return {**prev, "desactualizado": True}
    return None


def _indec_serie(series_id: str, limit: int = 16) -> list:
    params = {"ids": series_id, "format": "json", "limit": limit, "sort": "desc"}
    r = requests.get(INDEC_SERIES_BASE, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["data"]


# ── Colectores AUTO ───────────────────────────────────────────────────────────

def fetch_cepo_mulc() -> dict | None:
    """
    Brecha CCL/mayorista como proxy del cepo corporativo (giro de dividendos, capitales).
    El mayorista (referencia A3500 del BCRA) es la tasa correcta para medir la brecha
    cambiaria: el "oficial" minorista ya incluye el spread del banco y subestima la brecha.
    Blue≈0% porque el cepo minorista se levantó (abr-2025); el CCL mide la restricción
    que persiste para empresas: repatriación de utilidades, acceso al MULC para capital.
    brecha 0% → avance 100%; brecha 20% → avance 0%.
    """
    try:
        r = requests.get(DOLARAPI_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        dolares = {d["casa"]: d for d in r.json()}
        ccl       = dolares.get("contadoconliqui", {}).get("venta")
        mayorista = dolares.get("mayorista",       {}).get("venta")
        if not ccl or not mayorista:
            raise ValueError("CCL o mayorista no encontrado en respuesta")
        brecha = round((float(ccl) - float(mayorista)) / float(mayorista) * 100.0, 2)
        # 0% → avance 100%; 20% → avance 0%
        avance = round(max(0.0, min(100.0, 100.0 - brecha * 5.0)), 1)
        return {
            "valor":          brecha,
            "avance_pct":     avance,
            "unidad":         "% de brecha",
            "fuente":         DOLARAPI_URL,
            "fecha_dato":     date.today().isoformat(),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("cepo_mulc", e)
        return None


def fetch_reduccion_estado() -> dict | None:
    """
    Variación del empleo público vs baseline Q4-2023 (series datos.gob.ar).
    Reducción de empleo → avance de reforma (meta de referencia: -30% = avance 100%).
    """
    try:
        data = _indec_serie(EMPLEO_PUBLICO_ID, limit=16)
        if not data or len(data) < 8:
            raise ValueError("datos insuficientes para calcular baseline")

        current_val  = float(data[0][1])
        current_date = data[0][0]

        # Buscar el punto más cercano a 2023-10-01 (Q4-2023) como baseline
        baseline_val  = None
        baseline_date = None
        for fecha, valor in data:
            if fecha <= "2024-01-01":  # primer trimestre que llega a o antes de Q4-2023
                baseline_val  = float(valor)
                baseline_date = fecha
                break
        if baseline_val is None:
            baseline_val  = float(data[-1][1])
            baseline_date = data[-1][0]

        var_pct = round((current_val - baseline_val) / baseline_val * 100.0, 2)
        # -30% → avance 100% | 0% → avance 0% | >0% → avance 0%
        avance  = round(max(0.0, min(100.0, -var_pct * 100.0 / 30.0)), 1)

        return {
            "valor":          var_pct,
            "avance_pct":     avance,
            "unidad":         f"% de variación (vs {baseline_date})",
            "fuente":         INDEC_SERIES_BASE,
            "fecha_dato":     current_date,
            "desactualizado": False,
        }
    except Exception as e:
        _warn("reduccion_estado", e)
        return None


def fetch_apertura_comercial() -> dict | None:
    """
    Variación interanual de importaciones totales INDEC como proxy de apertura comercial.
    +30% i.a. → avance 100% | flat → avance 50% | -30% i.a. → avance 0%.
    """
    try:
        data = _indec_serie(IMPORTACIONES_ID, limit=14)
        if not data or len(data) < 13:
            raise ValueError("datos insuficientes para calcular variación i.a.")

        current_val  = float(data[0][1])
        current_date = data[0][0]
        anio_ant_val = float(data[12][1])  # mismo mes del año anterior

        if not anio_ant_val:
            raise ValueError("valor año anterior es cero")

        var_ia = round((current_val / anio_ant_val - 1.0) * 100.0, 2)
        # +30% → 100%, 0% → 50%, -30% → 0%
        avance = round(max(0.0, min(100.0, var_ia * 5.0 / 3.0 + 50.0)), 1)

        return {
            "valor":          var_ia,
            "avance_pct":     avance,
            "unidad":         "% interanual",
            "fuente":         INDEC_SERIES_BASE,
            "fecha_dato":     current_date,
            "desactualizado": False,
        }
    except Exception as e:
        _warn("apertura_comercial", e)
        return None


# ── Colectores SCRAPE (best-effort) ──────────────────────────────────────────

def fetch_desregulacion_normativa() -> dict | None:
    """
    Cuenta normas publicadas desde dic-2023 que contienen "deroga" (InfoLeg sesión POST).
    100 normas derogantes = avance 100%; escala lineal.
    """
    try:
        today = date.today()
        count = _infoleg_post(
            texto="deroga", tipo_norma="",
            fecha_desde=("01", "12", "2023"),
            fecha_hasta=(today.strftime("%d"), today.strftime("%m"), today.strftime("%Y")),
        )
        avance = round(min(100.0, float(count)), 1)
        return {
            "valor":          count,
            "avance_pct":     avance,
            "unidad":         "Normas (conteo)",
            "fuente":         INFOLEG_HOME,
            "fecha_dato":     today.isoformat(),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("desregulacion_normativa", e)
        return None


def fetch_libertad_opcion_salud() -> dict | None:
    """
    Opciones de cambio captadas acumuladas desde dic-2023 (SSS).
    Requiere obtener total acumulado y restar el stock previo a dic-2023.
    """
    try:
        r = requests.get(
            SSS_OPCIONES_URL,
            params={"page": "opciones", "cat": "institucion"},
            headers=HTTP_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        # SSS muestra tabla con total de opciones por año/mes; buscar el número más prominente
        match = re.search(r"(\d[\d\.,]{4,})\s*(opciones|traspasos)", r.text, re.I)
        if not match:
            # Intentar otro patrón
            match = re.search(r"Total[^:]*:\s*(\d[\d\.,]+)", r.text, re.I)
        if not match:
            return None
        total_str = match.group(1).replace(".", "").replace(",", "")
        total = int(total_str)
        # El dato acumulado desde 1998 es ~histórico. Sin serie temporal no podemos calcular avance.
        # Fallback: usar avance de manuales hasta tener serie post-dic-2023.
        return None
    except Exception as e:
        _warn("libertad_opcion_salud", e)
        return None


def fetch_rigi_inversiones() -> dict | None:
    """
    Cuenta Resoluciones (tipo=3) RIGI vía InfoLeg sesión POST, usando texto="VPU"
    (Vehículo de Proyecto Único — término técnico exclusivo del RIGI, Ley 27.742).
    Desde 01/07/2024 (entrada en vigencia RIGI). Calibración: 28 normas ≈ 28% avance
    (validado contra dato manual may-2026: 16 proyectos = USD 27.210M aprobados = 28.7%).
    """
    try:
        today = date.today()
        count = _infoleg_post(
            texto="VPU", tipo_norma="3",
            fecha_desde=("01", "07", "2024"),
            fecha_hasta=(today.strftime("%d"), today.strftime("%m"), today.strftime("%Y")),
        )
        avance = round(min(100.0, float(count)), 1)
        return {
            "valor":          count,
            "avance_pct":     avance,
            "unidad":         "Resoluciones (conteo)",
            "fuente":         INFOLEG_HOME,
            "fecha_dato":     today.isoformat(),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("rigi_inversiones", e)
        return None


def fetch_privatizaciones() -> dict | None:
    """
    Conteo de publicaciones del Boletín Oficial relacionadas con privatizaciones.
    Proxy: decretos/resoluciones con 'privatizacion' o 'transferencia de acciones'.
    """
    try:
        # BO API: secciones del día (no acumulado) — difícil de agregar sin base histórica
        # Retorna None hasta implementar conteo acumulado
        return None
    except Exception as e:
        _warn("privatizaciones", e)
        return None


def fetch_reestructuracion_organismos() -> dict | None:
    """
    Cuenta normas con "disolucion" desde dic-2023 via InfoLeg sesión POST.
    DNU 70/23 no aparece en búsqueda de texto libre (no indexado); los 18 documentos
    capturados son acciones de disolución/fusión POSTERIORES al megadecreto.
    Calibración: 18 actos = avance 40% (validado con estimación manual); 45 = 100%.
    """
    try:
        today = date.today()
        count = _infoleg_post(
            texto="disolucion", tipo_norma="",
            fecha_desde=("01", "12", "2023"),
            fecha_hasta=(today.strftime("%d"), today.strftime("%m"), today.strftime("%Y")),
        )
        avance = round(min(100.0, count * 100.0 / 45.0), 1)
        return {
            "valor":          count,
            "avance_pct":     avance,
            "unidad":         "Normas (conteo)",
            "fuente":         INFOLEG_HOME,
            "fecha_dato":     today.isoformat(),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("reestructuracion_organismos", e)
        return None


# ── Score ─────────────────────────────────────────────────────────────────────

def calcular_score(indicadores: dict) -> float:
    """Score 0–10: promedio de tensiones por indicador (avance → tensión)."""
    tensions = [
        _avance_to_tension(ind["avance_pct"])
        for ind in indicadores.values()
        if ind is not None and ind.get("avance_pct") is not None
    ]
    return round(sum(tensions) / len(tensions), 1) if tensions else 5.0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    cache_anterior = load_cache()
    manuales       = load_manuales()

    auto_fetchers: dict = {
        "cepo_mulc":                    fetch_cepo_mulc,
        "reduccion_estado":             fetch_reduccion_estado,
        "apertura_comercial":           fetch_apertura_comercial,
        "desregulacion_normativa":      fetch_desregulacion_normativa,
        "reestructuracion_organismos":  fetch_reestructuracion_organismos,
        "rigi_inversiones":             fetch_rigi_inversiones,
    }

    indicadores: dict = {}
    frescos_auto = 0

    for nombre in INDICADORES_ESPERADOS:
        resultado = None

        if nombre in auto_fetchers:
            resultado = auto_fetchers[nombre]()

        if resultado is not None and resultado.get("avance_pct") is not None:
            indicadores[nombre] = resultado
            frescos_auto += 1
        else:
            fallback = _manual_entry(nombre, manuales, cache_anterior)
            indicadores[nombre] = fallback or {
                "valor":          None,
                "avance_pct":     None,
                "unidad":         "",
                "fuente":         "pendiente",
                "fecha_dato":     "",
                "desactualizado": True,
            }

    score   = calcular_score(indicadores)
    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "indicadores":  indicadores,
    }

    save_cache(payload)

    total = len(INDICADORES_ESPERADOS)
    total_auto = len(auto_fetchers)
    con_datos = sum(1 for v in indicadores.values() if v and v.get("avance_pct") is not None)
    print(f"[OK] {CINTURON}: score={score} auto_frescos={frescos_auto}/{total_auto} con_datos={con_datos}/{total}")

    if frescos_auto == total_auto:
        sys.exit(0)
    elif frescos_auto > 0:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
