"""
Colector INDEC via API datos.gob.ar/series
Sin autenticacion. Todos los IDs verificados al 2026-05-10.
"""
import logging
import requests

from config import DATOS_GOB_BASE, DATOS_GOB_SEARCH, INDEC_SERIES, RIPTE_CSV, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _get_serie(series_id: str, limit: int = 2) -> list:
    params = {"ids": series_id, "format": "json", "limit": limit, "sort": "desc"}
    r = requests.get(DATOS_GOB_BASE, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["data"]


def _ultimo(series_id: str) -> dict:
    data = _get_serie(series_id, limit=1)
    return {"valor": data[0][1], "fecha": data[0][0]}


def _var_mensual(series_id: str) -> dict:
    data = _get_serie(series_id, limit=2)
    actual, anterior = data[0][1], data[1][1]
    var = (actual / anterior - 1) * 100 if anterior else None
    return {"valor": actual, "variacion_mensual_pct": var, "fecha": data[0][0]}


def search_serie(query: str, limit: int = 10) -> list[dict]:
    r = requests.get(DATOS_GOB_SEARCH, params={"q": query, "limit": limit},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return [{"id": s["field"]["id"], "description": s["field"].get("description",""),
             "frequency": s["field"].get("frequency",""), "end": s["field"].get("time_index_end","")}
            for s in r.json().get("data", [])]


def _get_ripte() -> dict:
    """RIPTE via CSV directo. Mensual desde jul-1994."""
    hist = _get_ripte_hist()
    ult = max(hist)
    return {"valor": hist[ult], "fecha": f"{ult}-01"}


def _get_ripte_hist() -> dict:
    """{YYYY-MM: RIPTE en pesos} — la serie completa del CSV oficial, para
    alinear la brecha salario/CBT por MES COMÚN (ADR-0030)."""
    r = requests.get(RIPTE_CSV, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    hist = {}
    for line in r.text.strip().split("\n"):
        p = line.split(",")
        if len(p) >= 2 and p[0][:4].isdigit():
            try:
                hist[p[0][:7]] = float(p[1])
            except ValueError:
                continue
    if not hist:
        raise ValueError("RIPTE CSV vacio")
    return hist


def fetch_indec() -> dict:
    results = {}

    # ── Precios ──────────────────────────────────────────────────────────────
    for key in ["ipc_total", "ipc_alimentos", "ipc_vivienda", "ipc_regulados"]:
        try:
            results[key] = _var_mensual(INDEC_SERIES[key])
            logger.info("%s OK: %s", key, results[key]["fecha"])
        except Exception as e:
            logger.error("%s FAIL: %s", key, e)

    # ── Canasta Basica Total ─────────────────────────────────────────────────
    for key in ["cbt", "cba"]:
        try:
            results[key] = _var_mensual(INDEC_SERIES[key])
            logger.info("%s OK: $%s", key, results[key]["valor"])
        except Exception as e:
            logger.error("%s FAIL: %s", key, e)

    # ── RIPTE + Brecha salario vs CBT (MES COMÚN, ADR-0030) ──────────────────
    # El RIPTE corre ~1 mes detrás de la CBT: dividir el último de cada uno
    # mezclaba meses (salario de abril / canasta de mayo) y subestimaba la
    # brecha en desinflación. Se alinea al último mes que ambos tienen y la
    # CBT más fresca queda declarada como provisoria.
    try:
        ripte_hist = _get_ripte_hist()
        ult_r = max(ripte_hist)
        results["ripte"] = {"valor": ripte_hist[ult_r], "fecha": f"{ult_r}-01"}
        cbt_hist = {f[:7]: v for f, v in _get_serie(INDEC_SERIES["cbt"], limit=8)}
        comunes = sorted(set(ripte_hist) & set(cbt_hist))
        if comunes:
            ym = comunes[-1]
            brecha = ripte_hist[ym] / cbt_hist[ym]
            nota = (f"RIPTE / CBT del mismo mes ({ym}): canastas cubiertas por "
                    f"el salario imponible promedio")
            ult_c = max(cbt_hist)
            if ult_c > ym:
                nota += (f" — CBT de {ult_c} ya publicada (${cbt_hist[ult_c]:,.0f}): "
                         f"esa brecha queda provisoria hasta que salga el RIPTE")
            results["brecha_salario_cbt"] = {
                "valor": brecha,
                "ripte_pesos": ripte_hist[ym],
                "cbt_pesos": cbt_hist[ym],
                "canastas_que_cubre": brecha,
                "fecha": f"{ym}-01",
                "nota": nota,
            }
            logger.info("Brecha sal/CBT OK (mes comun %s): %.2f canastas", ym, brecha)
    except Exception as e:
        logger.error("RIPTE FAIL: %s", e)

    # ── Salarios ─────────────────────────────────────────────────────────────
    try:
        results["isalarios_total"] = _var_mensual(INDEC_SERIES["isalarios_total"])
    except Exception as e:
        logger.error("isalarios FAIL: %s", e)

    # ── Salario real (deflactado por IPC) ────────────────────────────────────
    if "ipc_total" in results and "isalarios_total" in results:
        sal = results["isalarios_total"]["valor"]
        ipc = results["ipc_total"]["valor"]
        results["salario_real_indice"] = {
            "valor": sal / ipc * 100,
            "fecha": results["isalarios_total"]["fecha"],
            "nota": "Salario nominal / IPC * 100",
        }

    # ── Empleo y mercado laboral ──────────────────────────────────────────────
    for key in ["desocupacion", "empleo", "subocupacion_demandante"]:
        try:
            results[key] = _ultimo(INDEC_SERIES[key])
            logger.info("%s OK: %s", key, results[key]["valor"])
        except Exception as e:
            logger.error("%s FAIL: %s", key, e)

    # Informalidad (anual)
    try:
        results["informalidad_anual"] = _ultimo(INDEC_SERIES["informalidad_anual"])
        logger.info("informalidad OK: %s%%", results["informalidad_anual"]["valor"])
    except Exception as e:
        logger.error("informalidad FAIL: %s", e)

    # ── Actividad / Industria ─────────────────────────────────────────────────
    for key in ["isac", "emae", "ipi"]:
        try:
            results[key] = _var_mensual(INDEC_SERIES[key])
        except Exception as e:
            logger.error("%s FAIL: %s", key, e)

    # ── Faena vacuna (proxy consumo carne) ───────────────────────────────────
    try:
        results["faena_vacuna"] = _var_mensual(INDEC_SERIES["faena_vacuna"])
        logger.info("faena_vacuna OK")
    except Exception as e:
        logger.error("faena_vacuna FAIL: %s", e)

    # ── Acero crudo (hierro/construccion) ────────────────────────────────────
    try:
        results["acero_crudo"] = _var_mensual(INDEC_SERIES["acero_crudo"])
        logger.info("acero_crudo OK")
    except Exception as e:
        logger.error("acero_crudo FAIL: %s", e)

    return results
