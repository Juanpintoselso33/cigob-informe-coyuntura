"""Cobertura del Monitor según el día de publicación D (días después del fin del mes informado).
Escenario FUENTE: el dato está el día siguiente a que la fuente lo publica (corrida de la noche).
Escenario OBSERVADO: cuándo entró de verdad al Monitor (snapshots de git, jul-oct 2026)."""
import json, datetime as dt, calendar, statistics as st
snap = json.load(open("/Users/juan/dev/trabajo/CIGOB/Analisis CIGOB/projects/informe_coyuntura/web/src/data/informe.json"))
peso = {k: (v.get("peso_efectivo") or 0) / 4 * 100 for c in snap["cinturones"].values() for k, v in c["indicadores"].items() if v.get("en_indice")}
I = json.load(open("indec_series_fechas.json"))
L = json.load(open("llegadas.json"))
def fin(p): y, m = map(int, p.split("-")); return dt.date(y, m, calendar.monthrange(y, m)[1])
def lag(p, f): return (dt.date.fromisoformat(f) - fin(p)).days
# Hacienda (comunicado de resultado fiscal): fechas verificadas en prensa
FISCAL = {"2026-07": "2026-08-18", "2026-08": "2026-09-18", "2026-09": "2026-10-16", "2026-10": "2026-11-16"}
def fuente(k, p):
    """Día (desde fin de M) en que la fuente publica el dato de M. None = no depende de D (continuo o rezagado fijo)."""
    g = lambda s: lag(p, I[s][p]) if p in I[s] else None
    ipc = g("ipc")
    tabla = {
        "ipc_total": ipc, "ipc_alimentos": ipc, "idc": ipc, "credito_privado": ipc, "alquiler_real": ipc,
        "recaudacion": ipc, "actividad_tributaria": ipc,           # ARCA día 2-3, real con el IPC
        "saldo_comercial_12m": g("ica"), "apertura_comercial": g("ica"),
        "resultado_primario": lag(p, FISCAL[p]) if p in FISCAL else 17,
        "gasto_funcionamiento": max(lag(p, FISCAL[p]) if p in FISCAL else 17, ipc or 0),
        "reduccion_estado": g("dotacion"), "ipi_manufacturero": g("ipi"), "iai": g("isac"),
        "emae_ia": g("emae"), "emae_difusion": g("emae"), "consumo_supermercados": g("super"),
        "rem_ipc_12m": 7, "tcrm": 2, "motorizacion_total": 6, "ratio_motos_autos": 6, "desregulacion_normativa": 6,
        "conflictividad_nacional": 12, "pobreza_nowcast": 15, "costo_financiamiento_tesoro": ipc,
        "desequilibrio_monetario": 31, "meta_reservas_fmi": 25, "reservas_bcra": 25,
        "consumo_carne_vacuna": 28, "consumo_carnes_total": 28, "brecha_salario_cbt": 46,
        "mora_familias": 55, "jornadas_individuales_no_trabajadas_12m": 59,
    }
    return tabla.get(k, "x")
MESES = [f"{y}-{m:02d}" for y, m in [(2025, i) for i in range(7, 13)] + [(2026, i) for i in range(1, 11)]]
mensuales = [k for k in peso if fuente(k, "2026-09") != "x"]
fijos = [k for k in peso if k not in mensuales]
print(f"Mensuales que dependen del día: {len(mensuales)} ({sum(peso[k] for k in mensuales):.1f}% del peso). "
      f"Fijos (continuos, en el mes, o trimestrales/anuales): {len(fijos)} ({sum(peso[k] for k in fijos):.1f}%)")
def cobertura(D, p, escenario):
    tot = 0
    for k in mensuales:
        if escenario == "fuente":
            s = fuente(k, p)
            if s is not None and s + 1 <= D: tot += peso[k]
        else:
            ll = [t for fd, t in L.get(k, {}).get("llegadas", []) if fd[:7] == p]
            if ll and (dt.date.fromisoformat(ll[0][:10]) - fin(p)).days <= D: tot += peso[k]
    return tot
tot_m = sum(peso[k] for k in mensuales)
print("\nD = días después de terminar el mes (D=22 → día 22 del mes siguiente; 31+ → mes subsiguiente)")
print(" D | FUENTE: mín-máx % del peso mensual (16 meses) | OBSERVADO jul-oct 2026 mín-máx")
res = {}
for D in list(range(1, 32)) + [35, 40, 45, 50, 56, 60]:
    a = [cobertura(D, p, "fuente") / tot_m * 100 for p in MESES]
    b = [cobertura(D, p, "obs") / tot_m * 100 for p in ["2026-07", "2026-08", "2026-09", "2026-10"]]
    res[D] = (min(a), max(a), min(b), max(b))
    print(f"{D:2} | {min(a):5.1f} – {max(a):5.1f} | {min(b):5.1f} – {max(b):5.1f}")
json.dump(res, open("curva.json", "w"))
print("\nLlegada de la fuente por indicador (mín–máx en los 16 meses, días después del fin del mes):")
for k in sorted(mensuales, key=lambda k: max([x for x in [fuente(k, p) for p in MESES] if x is not None] or [0])):
    xs = [fuente(k, p) for p in MESES]; xs = [x for x in xs if x is not None]
    print(f"  {k:40} {peso[k]:4.2f}%  {min(xs)}–{max(xs)}")
