"""
Colector INDEC via API datos.gob.ar/series
Sin autenticacion. Todos los IDs verificados al 2026-05-10.
"""
import logging
import requests

import sys as _sys
from pathlib import Path as _Path
if str(_Path(__file__).resolve().parents[2]) not in _sys.path:
    _sys.path.append(str(_Path(__file__).resolve().parents[2]))  # scripts/: datos_gob
import datos_gob  # noqa: E402

from config import DATOS_GOB_BASE, DATOS_GOB_SEARCH, INDEC_SERIES, RIPTE_CSV, HTTP_HEADERS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _get_serie(series_id: str, limit: int = 2) -> list:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import indec_actividad
    if series_id in indec_actividad.SERIES:
        return indec_actividad.filas(series_id, limit)
    params = {"ids": series_id, "format": "json", "limit": limit, "sort": "desc"}
    r = datos_gob.get(DATOS_GOB_BASE, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["data"]


def _ultimo(series_id: str) -> dict:
    data = _get_serie(series_id, limit=1)
    return {"valor": data[0][1], "fecha": data[0][0]}


def variacion_empleo_contra_2023(filas: list) -> dict:
    """Filas [[fecha, tasa en proporción]] (cualquier orden) → diferencia, en
    puntos porcentuales, entre la tasa de empleo del último trimestre y la del
    MISMO trimestre de 2023, antes del mandato (ADR-0383, decisión de Juan del
    27-oct-2026). Se compara la misma estación porque la EPH no viene
    desestacionalizada; si falta ese trimestre de 2023, falla en voz alta."""
    por_fecha = {f: v for f, v in filas if v is not None}
    if not por_fecha:
        raise ValueError("sin datos de tasa de empleo")
    ultima = max(por_fecha)
    base = f"2023{ultima[4:]}"
    if base not in por_fecha:
        raise ValueError(f"falta el trimestre {base} para comparar contra 2023")
    tasa, tasa_base = por_fecha[ultima] * 100, por_fecha[base] * 100
    return {"valor": round(round(tasa, 1) - round(tasa_base, 1), 1), "fecha": ultima,
            "tasa": round(tasa, 1), "tasa_2023": round(tasa_base, 1)}


def _var_mensual(series_id: str) -> dict:
    data = _get_serie(series_id, limit=2)
    actual, anterior = data[0][1], data[1][1]
    var = (actual / anterior - 1) * 100 if anterior else None
    resultado = {"valor": actual, "variacion_mensual_pct": var, "fecha": data[0][0]}
    import indec_actividad
    if series_id in indec_actividad.SERIES:
        fuente = indec_actividad.niveles(indec_actividad.SERIES[series_id][0])
        resultado.update({k: fuente[k] for k in ("fuente_url", "obtenido_en")})
    return resultado


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
    for key in ["ipc_total", "ipc_alimentos", "ipc_vivienda", "ipc_regulados",
                "ipc_alquiler_gba"]:
        try:
            if key == 'ipc_alquiler_gba':
                from .ipc_alquiler import tarjeta
                results[key] = tarjeta()
            else:
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
    # OJO: esta lista es una WHITELIST. Agregar una serie a INDEC_SERIES en
    # config.py NO alcanza para que el colector la emita — hay que sumar la
    # clave acá. (Costó una corrida en falso al incorporar empleo_registrado:
    # la card salía sin valor y el gate fallaba con G1, lejos de la causa.)
    for key in ["desocupacion", "empleo", "subocupacion_demandante",
                "empleo_registrado"]:
        try:
            results[key] = _ultimo(INDEC_SERIES[key])
            logger.info("%s OK: %s", key, results[key]["valor"])
        except Exception as e:
            logger.error("%s FAIL: %s", key, e)

    # Ocupación EPH (ADR-0383): diferencia de la tasa de empleo, en puntos
    # porcentuales, contra el MISMO trimestre de 2023 (antes del mandato);
    # la EPH no viene desestacionalizada. 20 trimestres alcanzan hasta 2028.
    try:
        results["ocupacion_eph"] = variacion_empleo_contra_2023(
            _get_serie(INDEC_SERIES["empleo"], limit=20))
        logger.info("ocupacion_eph OK: %s", results["ocupacion_eph"])
    except Exception as e:
        logger.error("ocupacion_eph FAIL: %s", e)

    # Informalidad SIN aportes propios (ADR-0413): asalariados sin descuento
    # jubilatorio que tampoco se pagan sus aportes por su cuenta. No sale de la
    # API de series sino de las planillas del INDEC (ver informalidad_eph.py).
    try:
        import informalidad_eph
        results["informalidad_trimestral"] = informalidad_eph.ultimo()
        logger.info("informalidad sin aportes propios OK: %s", results["informalidad_trimestral"])
    except Exception as e:
        logger.error("informalidad sin aportes propios FAIL: %s", e)

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
