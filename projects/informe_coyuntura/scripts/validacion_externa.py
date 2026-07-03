"""validacion_externa.py — Validación de constructo del ITVC y el ITCM (ADR-0019, D6).

Paso 9 del Handbook JRC/OCDE ("links to other variables"): si el índice mide
lo que dice medir, debería co-moverse con variables externas relacionadas que
NO lo componen. Dos estudios:
  * ITVC (condiciones materiales de la vida cotidiana) contra el ICC de UTDT
    (percepción del consumidor) — correlación positiva esperada.
  * ITCM (tensión macroeconómica, reconstrucción mensual desde las series de
    componentes con puntaje interpolado) contra el RIESGO PAÍS (EMBI, puntos
    básicos, ArgentinaDatos) — correlación NEGATIVA esperada: menos tensión
    macro, menos paga la Argentina por su deuda.

Para que la comparación no sea circular (el ICC es un componente del ITVC,
7,5% del peso), la serie del ITVC se recalcula EXCLUYENDO al ICC — la
renormalización estándar del motor absorbe la ausencia.

Cómo se reconstruye la serie mensual del ITVC (dic-2023 → hoy):
- Componentes transformados (itvc_alimentos/tarifas/ipi/isac/endeudamiento):
  ya son índices base-100 en series.json.
- Componentes de rebase directo (brecha, ICC, pluriempleo, carne, motos):
  se rebasea TODA la serie contra su promedio 4T-2023.
- Anuales (informalidad, inseguridad): rebase anual + forward-fill mensual
  (regla del doc: "último dato disponible").
- Cada mes se agrega con itvc.calcular_itvc (misma renormalización que el
  índice publicado); un componente entra con su último dato ≤ mes.

Correlaciones (Pearson): niveles y primeras diferencias, contemporáneas y
con ±1 rezago. Salida: output/validacion_externa.json + resumen legible.

Uso: python scripts/validacion_externa.py
"""
import json
import statistics
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcm
import itvc

RIESGO_PAIS_URL = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"

ROOT = Path(__file__).resolve().parents[1]
SERIES = ROOT / "web" / "src" / "data" / "series.json"
SALIDA = ROOT / "output" / "validacion_externa.json"
BASE_MESES = ("2023-10", "2023-11", "2023-12")

# componente → (clave de serie, invertido, anual)
COMPONENTES = {
    "ipc_alimentos":          ("itvc_alimentos", False, False, True),   # ya base-100
    "peso_tarifas":           ("itvc_tarifas", False, False, True),
    "mortalidad_pymes":       ("itvc_ipi", False, False, True),
    "despacho_cemento":       ("itvc_isac", False, False, True),
    "endeudamiento_familiar": ("itvc_endeudamiento", False, False, True),
    "brecha_salario_cbt":     ("brecha_salario_cbt", False, False, False),
    "icc_utdt":               ("icc_utdt", False, False, False),
    "pluriempleo":            ("pluriempleo", True, False, False),
    "consumo_carne":          ("consumo_carne", False, False, False),
    "patentamiento_motos":    ("patentamiento_motos", False, False, False),
    "informalidad":           ("informalidad", True, True, False),
    "inseguridad":            ("inseguridad", True, True, False),
}


def _mensual(serie: list) -> dict:
    return {p["fecha"][:7]: p["valor"] for p in serie}


def _movil12(vals: dict) -> dict:
    """Acumulado móvil de 12 meses consecutivos (ADR-0024: desestacionaliza
    flujos con calendario fuerte, ej. motos)."""
    yms = sorted(vals)
    out = {}
    for i in range(11, len(yms)):
        win = yms[i - 11:i + 1]
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) == 11:
            out[win[-1]] = sum(vals[k] for k in win) / 12.0
    return out


def _rebase(vals: dict, invertido: bool, anual: bool) -> dict:
    """Serie {ym: valor} → {ym: índice base-100 vs 4T-2023}."""
    if anual:
        # base = valor del año 2023; el índice anual se asigna al mes de enero
        # del dato y el forward-fill mensual lo propaga
        base = next((v for ym, v in sorted(vals.items()) if ym[:4] == "2023"), None)
        if not base:
            return {}
        return {ym: round((base / v if invertido else v / base) * 100.0, 1)
                for ym, v in vals.items() if v}
    base_vals = [vals[m] for m in BASE_MESES if vals.get(m)]
    if not base_vals:
        return {}
    base = sum(base_vals) / len(base_vals)
    return {ym: round((base / v if invertido else v / base) * 100.0, 1)
            for ym, v in vals.items() if v and ym >= "2023-10"}


def _meses(desde: str, hasta: str) -> list:
    out, (y, m) = [], (int(desde[:4]), int(desde[5:7]))
    while f"{y}-{m:02d}" <= hasta:
        out.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def construir_series_itvc() -> tuple:
    """(serie ITVC completa, serie ITVC sin ICC, serie ICC) mensuales."""
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    indices_por_comp = {}
    for comp, (skey, invertido, anual, ya_rebaseada) in COMPONENTES.items():
        vals = _mensual(series.get(skey) or [])
        if comp == "patentamiento_motos":
            vals = _movil12(vals)          # ADR-0024: estacionalidad fuerte
        indices_por_comp[comp] = (vals if ya_rebaseada
                                  else _rebase(vals, invertido, anual))
    ult = max(max(v) for v in indices_por_comp.values() if v)
    itvc_full, itvc_sin_icc = {}, {}
    for ym in _meses("2023-12", ult):
        punto = {}
        for comp, vals in indices_por_comp.items():
            previos = [k for k in vals if k <= ym]
            if previos:
                punto[comp] = vals[max(previos)]     # último dato disponible (doc IV.2.1)
        r = itvc.calcular_itvc(punto)
        if r:
            itvc_full[ym] = r["valor"]
        r2 = itvc.calcular_itvc({k: v for k, v in punto.items() if k != "icc_utdt"})
        if r2:
            itvc_sin_icc[ym] = r2["valor"]
    icc = _mensual(series.get("icc_utdt") or [])
    return itvc_full, itvc_sin_icc, icc


def construir_serie_itcm() -> dict:
    """Serie mensual del ITCM reconstruida desde las series de componentes
    (mismo motor, puntaje interpolado, sin overrides del analista): 10 de los
    12 componentes tienen serie; IAI/ICIP faltan y el motor renormaliza.
    Reservas netas solo desde jun-2024 (límite de fuente documentado)."""
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    m = lambda k: _mensual(series.get(k) or [])
    ipc_nivel = m("ipc_total")            # NIVEL del índice → m/m por cociente
    rem = m("rem_ipc_12m")                # % anual → equivalente mensual
    saldo = m("saldo_comercial")          # M USD mensual → suma móvil 12m
    directos = {k: m(k) for k in ("idm", "recaudacion", "reservas_bcra", "idc",
                                  "credito_privado", "emae_ia", "tcrm")}

    def saldo_12m(ym):
        yms = sorted(saldo)
        if ym not in yms or yms.index(ym) < 11:
            return None
        win = yms[yms.index(ym) - 11:yms.index(ym) + 1]
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        return sum(saldo[k] for k in win) if (af * 12 + mf) - (a0 * 12 + m0) == 11 else None

    out = {}
    ult = max(ipc_nivel)
    for ym in _meses("2023-12", ult):
        prev = sorted(k for k in ipc_nivel if k < ym)
        valores = {
            "ipc_total": ((ipc_nivel[ym] / ipc_nivel[prev[-1]] - 1) * 100
                          if ym in ipc_nivel and prev else None),
            "rem_ipc_12m": (itcm.rem_mensual_equivalente(rem[ym])
                            if ym in rem else None),
            "saldo_comercial_12m": saldo_12m(ym),
            **{k: v.get(ym) for k, v in directos.items()},
        }
        r = itcm.calcular_itcm(valores)
        if r:
            out[ym] = r["valor"]
    return out


def fetch_riesgo_pais_mensual() -> dict:
    """Promedio mensual del riesgo país (EMBI, pb) desde ArgentinaDatos."""
    r = requests.get(RIESGO_PAIS_URL, timeout=30)
    r.raise_for_status()
    por_mes = {}
    for p in r.json():
        if p.get("valor") and p["fecha"] >= "2023-11":
            por_mes.setdefault(p["fecha"][:7], []).append(float(p["valor"]))
    return {ym: round(sum(v) / len(v), 0) for ym, v in por_mes.items()}


def _pearson(a: dict, b: dict) -> tuple:
    comunes = sorted(set(a) & set(b))
    if len(comunes) < 6:
        return None, len(comunes)
    return round(statistics.correlation([a[m] for m in comunes],
                                        [b[m] for m in comunes]), 3), len(comunes)


def _difs(s: dict) -> dict:
    yms = sorted(s)
    return {yms[i]: round(s[yms[i]] - s[yms[i - 1]], 2) for i in range(1, len(yms))}


def _lag(s: dict, k: int) -> dict:
    """Serie corrida k meses hacia adelante (k>0: s adelanta al comparador)."""
    yms = sorted(s)
    return {yms[i + k]: s[yms[i]] for i in range(len(yms) - k)} if k > 0 else s


def main():
    itvc_full, itvc_sin, icc = construir_series_itvc()
    resultados = {"_meta": {"adr": "0019 Decisión 6",
                            "nota": "ITVC sin ICC para evitar circularidad (el ICC pesa 7,5% del ITVC)"}}
    print(f"serie ITVC reconstruida: {len(itvc_full)} meses "
          f"({min(itvc_full)} → {max(itvc_full)}) · último: {itvc_full[max(itvc_full)]}")
    resultados["serie_itvc"] = itvc_full
    resultados["serie_itvc_sin_icc"] = itvc_sin

    pares = {
        "niveles (ITVC sin ICC vs ICC)": (itvc_sin, icc),
        "niveles (ITVC completo vs ICC — con circularidad 7,5%)": (itvc_full, icc),
        "primeras diferencias (sin ICC)": (_difs(itvc_sin), _difs(icc)),
        "ITVC sin ICC adelantado 1 mes vs ICC": (_lag(itvc_sin, 1), icc),
        "ICC adelantado 1 mes vs ITVC sin ICC": (itvc_sin, _lag(icc, 1)),
    }
    resultados["correlaciones"] = {}
    print("\ncorrelaciones (Pearson):")
    for nombre, (a, b) in pares.items():
        r, n = _pearson(a, b)
        resultados["correlaciones"][nombre] = {"r": r, "n": n}
        print(f"  {nombre}: r = {r}  (n = {n})")

    # ── ITCM vs riesgo país (correlación negativa esperada) ────────────────
    serie_itcm = construir_serie_itcm()
    print(f"\nserie ITCM reconstruida: {len(serie_itcm)} meses "
          f"({min(serie_itcm)} → {max(serie_itcm)}) · último: {serie_itcm[max(serie_itcm)]}")
    resultados["serie_itcm"] = serie_itcm
    try:
        riesgo = fetch_riesgo_pais_mensual()
        resultados["riesgo_pais_mensual"] = riesgo
        pares_m = {
            "niveles (ITCM vs riesgo país)": (serie_itcm, riesgo),
            "primeras diferencias (ITCM vs riesgo)": (_difs(serie_itcm), _difs(riesgo)),
            "ITCM adelantado 1 mes vs riesgo": (_lag(serie_itcm, 1), riesgo),
            "riesgo adelantado 1 mes vs ITCM": (serie_itcm, _lag(riesgo, 1)),
        }
        resultados["correlaciones_itcm"] = {}
        print("correlaciones ITCM (Pearson, negativa = válida):")
        for nombre, (a, b) in pares_m.items():
            r, n = _pearson(a, b)
            resultados["correlaciones_itcm"][nombre] = {"r": r, "n": n}
            print(f"  {nombre}: r = {r}  (n = {n})")
    except Exception as e:
        print(f"[WARN] riesgo país no disponible: {e}")

    SALIDA.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
