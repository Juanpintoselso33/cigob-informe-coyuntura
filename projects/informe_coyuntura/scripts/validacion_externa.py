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
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcg
import itcm
import itcp
import itvc
import publicar

RIESGO_PAIS_URL = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"
MERVAL_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EMERV"
CCL_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"
EPU_LATAM_URL = ("https://www.bde.es/f/webbe/SES/AnalisisEconomico/AnalisisEconomico/"
                 "America_latina/Publicaciones/EPU_LATAM.xlsx")

ROOT = Path(__file__).resolve().parents[1]
SERIES = ROOT / "web" / "src" / "data" / "series.json"
SALIDA = ROOT / "output" / "validacion_externa.json"
BASE_MESES = ("2023-10", "2023-11", "2023-12")

# componente → (clave de serie, invertido, anual)
COMPONENTES = {
    "ipc_alimentos":          ("itvc_alimentos", False, False, True),   # ya base-100 (ADR-0033: relativo al IPC)
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
    "inseguridad":            ("inseguridad", True, False, False),      # IVI mensual (ADR-0032)
    "sentimiento_digital":    ("sentimiento_digital", True, False, False),  # ADR-0034
}
# Bases DECLARADAS distintas del 4T-2023 (misma regla que publicar):
BASES_PROPIAS = {"inseguridad": ("2024-01",)}   # IVI reanudado ene-2024 (ADR-0032)
ITVC_TECHO = 140.0                              # winsorización asimétrica (ADR-0033)


def _mensual(serie: list) -> dict:
    return {p["fecha"][:7]: p["valor"] for p in serie}


def _cargar_series_itcm() -> dict:
    """Combina el snapshot publicado con los CSV locales recién descargados.

    La validación corre antes que publicar.py: los CSV deben prevalecer para que
    una serie nueva o actualizada entre en la reconstrucción sin perder puntos
    históricos que todavía solo existan en el snapshot acumulado.
    """
    acumuladas = json.loads(SERIES.read_text(encoding="utf-8"))
    for clave, puntos_frescos in publicar.build_series().items():
        por_fecha = {p["fecha"]: p for p in acumuladas.get(clave) or []}
        por_fecha.update({p["fecha"]: p for p in puntos_frescos})
        acumuladas[clave] = [por_fecha[fecha] for fecha in sorted(por_fecha)]
    return acumuladas


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


def _rebase(vals: dict, invertido: bool, anual: bool, base_meses: tuple = None) -> dict:
    """Serie {ym: valor} → {ym: índice base-100 vs 4T-2023 (o base declarada)}."""
    if anual:
        # base = valor del año 2023; el índice anual se asigna al mes de enero
        # del dato y el forward-fill mensual lo propaga
        base = next((v for ym, v in sorted(vals.items()) if ym[:4] == "2023"), None)
        if not base:
            return {}
        return {ym: round((base / v if invertido else v / base) * 100.0, 1)
                for ym, v in vals.items() if v}
    base_vals = [vals[m] for m in (base_meses or BASE_MESES) if vals.get(m)]
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
        idx = (vals if ya_rebaseada
               else _rebase(vals, invertido, anual, BASES_PROPIAS.get(comp)))
        # winsorización asimétrica del ADR-0033: mismo techo que publicar
        indices_por_comp[comp] = {ym: min(v, ITVC_TECHO) for ym, v in idx.items()}
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
    (mismo motor, puntaje interpolado, sin overrides del analista): 11 de los
    13 componentes tienen serie; IAI/ICIP faltan y el motor renormaliza.
    Reservas netas solo desde jun-2024 (límite de fuente documentado)."""
    series = _cargar_series_itcm()
    m = lambda k: _mensual(series.get(k) or [])
    ipc_mm = m("ipc_total")               # ya publicada en % m/m (04-jul-2026)
    rem = m("rem_ipc_12m")                # % anual → equivalente mensual
    saldo = m("saldo_comercial")          # M USD mensual → suma móvil 12m
    directos = {k: m(k) for k in ("idm", "presion_dolarizacion", "recaudacion",
                                  "reservas_bcra", "idc", "credito_privado",
                                  "emae_ia", "tcrm")}

    def saldo_12m(ym):
        yms = sorted(saldo)
        if ym not in yms or yms.index(ym) < 11:
            return None
        win = yms[yms.index(ym) - 11:yms.index(ym) + 1]
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        return sum(saldo[k] for k in win) if (af * 12 + mf) - (a0 * 12 + m0) == 11 else None

    out = {}
    ult = max(ipc_mm)
    for ym in _meses("2023-12", ult):
        valores = {
            "ipc_total": ipc_mm.get(ym),
            "rem_ipc_12m": (itcm.rem_mensual_equivalente(rem[ym])
                            if ym in rem else None),
            "saldo_comercial_12m": saldo_12m(ym),
            **{k: v.get(ym) for k, v in directos.items()},
        }
        r = itcm.calcular_itcm(valores)
        if r:
            out[ym] = r["valor"]
    return out


ITCG_SERIES = [
    "cepo_mulc", "apertura_comercial", "desregulacion_normativa",
    "reduccion_estado", "gasto_funcionamiento", "masa_salarial",
    "reestructuracion_organismos", "fal_modernizacion_laboral",
    "litigiosidad_laboral", "privatizaciones", "rigi_inversiones",
    "concesiones_infraestructura", "asistencia_directa",
    "protocolo_antipiquetes", "libertad_opcion_salud",
]


def construir_serie_itcg() -> dict:
    """Serie mensual del ITCG reconstruida desde las series de componentes
    (mismo motor, puntaje interpolado, sin overrides del analista): 14 de los
    15 componentes tienen serie con historia; el protocolo antipiquetes recién
    acumula y el motor renormaliza."""
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    valores_por_comp = {k: _mensual(series.get(k) or []) for k in ITCG_SERIES}
    ult = max(max(v) for v in valores_por_comp.values() if v)
    out = {}
    for ym in _meses("2023-12", ult):
        r = itcg.calcular_itcg({k: v.get(ym) for k, v in valores_por_comp.items()})
        if r:
            out[ym] = r["valor"]
    return out


# Composición post ADR-0052 (2026-07-11): conflictividad_nacional (ACLED
# país, serie real de 30 meses) reemplaza a movilizacion_cepa (2 puntos,
# acumulado YTD) en la dimensión conflicto_social — la reconstrucción gana
# una pata mensual completa desde dic-2023. Antes, post ADR-0048
# (2026-07-10): cohesion_bloque ya es la serie del COMPUESTO bicameral
# 65/35 (una sola clave); cohesion_bloque_senado, rotacion_gabinete,
# protestas_caba y ahora movilizacion_cepa están fuera del índice — no
# entran a la reconstrucción aunque sus series sigan existiendo como
# contexto.
ITCP_SERIES = [
    "votometro_ventaja_lla", "ratio_dnu", "eficacia_legislativa", "veto_quorum",
    "derrotas_legislativas", "iaf_transferencias",
    "alineamiento_senadores_prov", "adhesion_reformas_provincial",
    "cohesion_bloque", "conflictividad_nacional",
    "bloqueo_sostenido",   # ADR-0069 (2026-07-16): tasa de normas desafiadas
    # en pie, 12m — serie desde mar-2024 (primer desafío votado: DNU 70/2023
    # en el Senado); antes el motor renormaliza, igual que con veto_quorum.
    # comisiones_caidas salió del índice (ADR-0064) — su serie sigue
    # existiendo como seguimiento interno pero no entra a la reconstrucción
]

# MÁSCARA DE ERA para eficacia_legislativa en la reconstrucción (ADR-0070,
# 2026-07-16): la cohorte madura del indicador (expedientes PE publicados
# 12-24 meses antes del mes evaluado) recién es 100% de la gestión actual
# cuando t−730d ≥ 10-dic-2023, o sea desde DIC-2025. Antes de eso el
# indicador mide la cartera de la gestión ANTERIOR muriendo con el cambio de
# congreso (todo 2024: expedientes 2022-2023 de Fernández; el 74→26 de
# puntaje reconstruido en 2024 era ese artefacto, no capital de esta
# gestión). El criterio es A PRIORI —composición de la cohorte, la misma
# doctrina que excluye dic-2023 de toda la reconstrucción (ver docstring de
# construir_serie_itcp)— y NO una calibración contra el benchmark: los meses
# de cohorte mixta (dic-2024→nov-2025) también se excluyen porque siguen
# ponderados mayormente por expedientes pre-gestión. Solo afecta la serie
# reconstruida de validación; la card publicada no se toca (hoy su cohorte
# ya es 100% de esta gestión).
EFICACIA_COHORTE_100PCT_MILEI_DESDE = "2025-12"


def construir_serie_itcp() -> dict:
    """Serie mensual del ITCP reconstruida desde las series de componentes
    (mismo motor, puntaje interpolado, sin overrides del analista) — bastante
    más ruidosa que la de ITCM/ITCG porque la cobertura histórica real de
    política es dispareja:
    - Con historia mensual sólida desde dic-2023: votometro_ventaja_lla,
      eficacia_legislativa, (desde 2026-07-09, ADR-0046)
      derrotas_legislativas —cuya serie completa se deriva del registro
      versionado de eventos— y (desde 2026-07-15, ADR-0058) ratio_dnu, que
      pasó de un punto por año calendario a ventana móvil de 365 días
      recalculada al fin de cada mes.
    - veto_quorum llega por período legislativo (pocos puntos, no un valor
      por mes) e iaf_transferencias es un dato anual (dic-dic): solo
      "prenden" en los meses exactos en que hay dato — el resto del tiempo el
      motor renormaliza sin ellos, igual que ITCM/ITCG con sus faltantes.
    - Desde 2026-07-09 la cobertura mejoró de verdad: cohesion_bloque
      (desde ADR-0048 la serie del compuesto bicameral 65/35, construida
      sobre las dos series por cámara de ADR-0039/0041) y
      alineamiento_senadores_prov (ADR-0038) tienen ~29-31 puntos mensuales
      reales, y adhesion_reformas_provincial 24 (fechas investigadas a mano,
      ADR-0044) — las dimensiones "alianzas territoriales" y "cohesión
      interna" ya no quedan renormalizadas sobre casi nada.
    - protestas_caba y rotacion_gabinete NO entran (contexto desde
      ADR-0048); la transformación var_vs_2023 que protestas necesitaba
      se fue con ellos.

    PISO DE COBERTURA (2026-07-09): los meses donde las dimensiones con
    algún dato suman menos del 60% del peso del índice se EXCLUYEN de la
    serie. Hallazgo real de la auditoría de hoy: el mes en curso (parcial)
    quedaba reconstruido solo con "poder legislativo" e "imagen y voto"
    (40% del peso, renormalizado al 100%) y daba un valor artefacto que
    saltaba decenas de puntos según qué serie tuviera o no un punto en ese
    mes (55,0 en la corrida anterior, 26,4 en la de hoy, para el MISMO
    mes) — sin par EPU todavía no contaminaba la correlación, pero lo iba
    a hacer apenas EPU publicara ese mes. El piso solo recorta esos meses
    de cola parcial: toda la historia 2024-01→jun-2026 tiene cobertura
    ≥75% y no se toca.

    ARRANQUE EN 2024-01 (2026-07-09, revisión conceptual de la celda
    ITCP×riesgo de la matriz): dic-2023 se excluye de la reconstrucción.
    No por cobertura (pasaba el piso) sino por composición degenerada: los
    componentes de ventana anual que "prenden" ese mes describen el año
    2023 COMPLETO de la gestión anterior — iaf_transferencias dic-dic 2023
    (transferencias de todo 2023 vs 2022; cuando se decidió también pesaba
    protestas_caba, hoy fuera del índice). El punto resultante era un salto
    de composición, no de política, y metía ruido justo en el arranque de
    todas las correlaciones.

    MÁSCARA DE ERA PARA EFICACIA (2026-07-16, ADR-0070): la misma doctrina,
    aplicada por componente — eficacia_legislativa se excluye de la
    reconstrucción hasta nov-2025 inclusive porque su cohorte madura
    (12-24m) recién es 100% de esta gestión desde dic-2025 (ver la
    constante EFICACIA_COHORTE_100PCT_MILEI_DESDE arriba). Y desde ADR-0069
    entra bloqueo_sostenido (tasa de normas desafiadas en pie), que le da a
    la dimensión "poder legislativo" una pata que sí mide 2024: los vetos
    sostenidos de sep/oct-2024 y la supervivencia del DNU 70."""
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    m = lambda k: _mensual(series.get(k) or [])
    directos = {k: m(k) for k in ITCP_SERIES}
    ult = max(max(v) for v in directos.values() if v)
    # tope: el último mes CALENDARIO COMPLETO. El mes en curso (parcial)
    # reconstruye con la cobertura justa y sin par EPU — recortarlo no
    # pierde nada (el artefacto original entró vía rotacion_gabinete, que ya
    # no puntúa, pero el criterio del mes completo sigue valiendo solo).
    hoy = datetime.now(timezone.utc)
    ult_completo = f"{hoy.year - 1}-12" if hoy.month == 1 else f"{hoy.year}-{hoy.month - 1:02d}"
    ult = min(ult, ult_completo)
    out = {}
    for ym in _meses("2024-01", ult):
        valores = {k: v.get(ym) for k, v in directos.items()}
        if ym < EFICACIA_COHORTE_100PCT_MILEI_DESDE:
            valores["eficacia_legislativa"] = None   # máscara de era (ADR-0070)
        r = itcp.calcular_itcp(valores)
        if not r:
            continue
        cobertura = sum(d["peso"] for d in r["dimensiones"].values())
        if cobertura < 0.6:
            print(f"  [i] serie ITCP: {ym} excluido por cobertura insuficiente "
                  f"({cobertura:.0%} del peso del índice con datos)")
            continue
        out[ym] = r["valor"]
    return out


def fetch_merval_usd_mensual() -> dict:
    """{YYYY-MM: Merval en USD} — cierre mensual del índice Merval (Yahoo
    Finance, ^MERV) sobre el CCL promedio del mes (ArgentinaDatos). Es el par
    convergente PROPIO del ITCG (ADR-0031): el mercado de acciones pricea la
    transformación estructural — reformas ejecutadas, empresas que valen más.
    El riesgo país queda como par exclusivo del ITCM."""
    r = requests.get(MERVAL_YAHOO_URL, params={"range": "3y", "interval": "1mo"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    cierres = {datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m"): c
               for t, c in zip(res["timestamp"],
                               res["indicators"]["quote"][0]["close"]) if c}
    r2 = requests.get(CCL_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r2.raise_for_status()
    por_mes = {}
    for d in r2.json():
        if d.get("venta"):
            por_mes.setdefault(d["fecha"][:7], []).append(float(d["venta"]))
    ccl = {ym: sum(v) / len(v) for ym, v in por_mes.items()}
    return {ym: round(cierres[ym] / ccl[ym], 1) for ym in sorted(cierres)
            if ym in ccl and ym >= "2023-11"}


def fetch_riesgo_pais_mensual() -> dict:
    """Promedio mensual del riesgo país (EMBI, pb) desde ArgentinaDatos."""
    r = requests.get(RIESGO_PAIS_URL, timeout=30)
    r.raise_for_status()
    por_mes = {}
    for p in r.json():
        if p.get("valor") and p["fecha"] >= "2023-11":
            por_mes.setdefault(p["fecha"][:7], []).append(float(p["valor"]))
    return {ym: round(sum(v) / len(v), 0) for ym, v in por_mes.items()}


def fetch_epu_argentina_mensual() -> dict:
    """Promedio mensual del EPU (Economic Policy Uncertainty) de Argentina,
    columna EPU_ARG_local (basado en diarios locales) de la hoja data_LATAM
    del dataset EPU_LATAM del Banco de España + SECMCA (misma familia
    metodológica de minería de texto que Baker/Bloom/Davis, no un precio de
    mercado): es el par externo del ITCP. Correlación NEGATIVA esperada — más
    capital político (menos tensión del cinturón), menos incertidumbre de
    política percibida en la prensa."""
    import io as _io
    import openpyxl
    r = requests.get(EPU_LATAM_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    wb = openpyxl.load_workbook(_io.BytesIO(r.content), data_only=True)
    ws = wb["data_LATAM"]
    filas = ws.iter_rows(values_only=True)
    encabezado = next(filas)
    col = encabezado.index("EPU_ARG_local")
    out = {}
    for fila in filas:
        fecha, valor = fila[0], fila[col]
        if fecha and valor is not None:
            out[fecha.strftime("%Y-%m")] = round(float(valor), 1)
    return out


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

    # ── ITCG vs ICG UTDT (confianza en el gobierno; positiva esperada) ─────
    serie_itcg = construir_serie_itcg()
    print(f"\nserie ITCG reconstruida: {len(serie_itcg)} meses "
          f"({min(serie_itcg)} → {max(serie_itcg)}) · último: {serie_itcg[max(serie_itcg)]}")
    resultados["serie_itcg"] = serie_itcg
    series_json = json.loads(SERIES.read_text(encoding="utf-8"))
    icg = _mensual(series_json.get("icg_utdt") or [])
    riesgo = resultados.get("riesgo_pais_mensual") or {}
    pares_g = {}
    try:
        merval = fetch_merval_usd_mensual()
        resultados["merval_usd_mensual"] = merval
        # Convergente PROPIO del ITCG (ADR-0031): el equity pricea la
        # transformación estructural (positiva esperada)
        pares_g.update({
            "niveles (ITCG vs Merval USD)": (serie_itcg, merval),
            "primeras diferencias (ITCG vs Merval USD)": (_difs(serie_itcg), _difs(merval)),
        })
    except Exception as e:
        print(f"[WARN] Merval USD no disponible: {e}")
    if riesgo:
        # Referencia cruzada (el par propio del ITCM)
        pares_g.update({
            "niveles (ITCG vs riesgo país)": (serie_itcg, riesgo),
            "primeras diferencias (ITCG vs riesgo)": (_difs(serie_itcg), _difs(riesgo)),
        })
    if icg:
        # Discriminante: el ITCG mide ejecución ACUMULATIVA, no popularidad —
        # la divergencia con el ciclo de confianza política es esperable.
        pares_g.update({
            "niveles (ITCG vs ICG)": (serie_itcg, icg),
            "primeras diferencias (ITCG vs ICG)": (_difs(serie_itcg), _difs(icg)),
        })
    if pares_g:
        resultados["correlaciones_itcg"] = {}
        print("correlaciones ITCG (Pearson):")
        for nombre, (a, b) in pares_g.items():
            r, n = _pearson(a, b)
            resultados["correlaciones_itcg"][nombre] = {"r": r, "n": n}
            print(f"  {nombre}: r = {r}  (n = {n})")

    # ── ITCP vs EPU Argentina (incertidumbre de política; negativa esperada) ──
    serie_itcp = construir_serie_itcp()
    print(f"\nserie ITCP reconstruida: {len(serie_itcp)} meses "
          f"({min(serie_itcp)} → {max(serie_itcp)}) · último: {serie_itcp[max(serie_itcp)]}")
    resultados["serie_itcp"] = serie_itcp
    try:
        epu = fetch_epu_argentina_mensual()
        resultados["epu_argentina_mensual"] = epu
        pares_p = {
            "niveles (ITCP vs EPU Argentina)": (serie_itcp, epu),
            "primeras diferencias (ITCP vs EPU)": (_difs(serie_itcp), _difs(epu)),
            "ITCP adelantado 1 mes vs EPU": (_lag(serie_itcp, 1), epu),
            "EPU adelantado 1 mes vs ITCP": (serie_itcp, _lag(epu, 1)),
        }
        resultados["correlaciones_itcp"] = {}
        print("correlaciones ITCP (Pearson, negativa = válida):")
        for nombre, (a, b) in pares_p.items():
            r, n = _pearson(a, b)
            resultados["correlaciones_itcp"][nombre] = {"r": r, "n": n}
            print(f"  {nombre}: r = {r}  (n = {n})")
    except Exception as e:
        print(f"[WARN] EPU Argentina no disponible: {e}")

    SALIDA.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
