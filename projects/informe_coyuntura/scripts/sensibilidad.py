"""sensibilidad.py — Análisis de sensibilidad y robustez de las paramétricas (ADR-0019).

Implementa el paso 7 del Handbook JRC/OCDE ("uncertainty and sensitivity
analysis") para ITCM, ITCG e ITVC, sobre los puntajes PUBLICADOS en el
snapshot (web/src/data/informe.json) — no re-descarga nada.

Tres experimentos por índice (semilla fija: corridas reproducibles):

1. PESOS (Monte Carlo, N=2000): cada peso de dimensión y de indicador se
   multiplica por U(0,8; 1,2) y se renormaliza. Mide cuánto del valor depende
   de la ponderación exacta elegida en el doc.
2. INSUMOS (solo ITCM/ITCG, N=2000): cada valor de entrada se perturba ±5%
   DEL ANCHO ENTRE SUS ANCLAS (aditivo, scale-free — ADR-0031) y se re-puntúa
   por la escala interpolada o sus anclas explícitas — mide la sensibilidad al error de
   medición de las fuentes. (Reemplaza al viejo experimento de "salto de
   banda"; el ruido multiplicativo previo subestimaba los indicadores con
   signo o centrados en cero.)
   Los componentes con override del analista no se perturban. El ITVC recibe
   su ruido de insumos vía el rebase continuo (sólo pesos acá).
3. LEAVE-ONE-OUT: el índice recalculado excluyendo cada indicador (con la
   renormalización estándar ante faltantes). Identifica componentes dominantes.

Salida: output/sensibilidad.json + resumen legible por consola, con el rango
de robustez p05-p95 y su traducción a tensión.

Uso: python scripts/sensibilidad.py [N_draws]
"""
import json
import math
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import parametrica
import itcm
import itcg
import itvc as itvc_mod
import itcp

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web" / "src" / "data" / "informe.json"
SALIDA = ROOT / "output" / "sensibilidad.json"

N_DRAWS = 2000              # override por CLI en main() — no parsear argv al importar
SEMILLA = 20260703          # fija: el análisis es reproducible corrida a corrida
RUIDO_PESO = 0.20           # pesos × U(1−r, 1+r)
RUIDO_INSUMO = 0.05         # valores de entrada × U(1−r, 1+r), re-puntuados por interpolación

# ── Error COMPARTIDO del deflactor (ADR-0078) ────────────────────────────────
# El IPC no es un insumo más: deflacta a varios indicadores a la vez, así que su
# error no se cancela en el promedio como sí lo hace el ruido idiosincrático de
# cada fuente. Sortear un error independiente por indicador —lo que hacía este
# módulo— subestima el rango de robustez.
#
# El signo importa y no es el mismo para todos. Si el IPC está SOBREESTIMADO:
#   ipc_total        +1  la inflación medida es esa, y puntúa peor
#   recaudacion      −1  deflactar de más hunde la variación real
#   credito_privado  −1  ídem
#   idc              −1  la BADLAR real queda más baja
#   idm               0  compara M3 real contra M2 real: el deflactor se cancela
# Por eso `idm` NO figura acá pese a usar el IPC: su construcción lo inmuniza.
EXPOSICION_DEFLACTOR_ITCM = {
    "ipc_total": +1.0,
    "recaudacion": -1.0,
    "credito_privado": -1.0,
    "idc": -1.0,
}
# Qué fracción del error de un indicador deflactado viene del deflactor y no de
# su propia fuente. 0 = el modelo viejo (todo idiosincrático); 1 = todo el error
# es del deflactor. Se adopta 0,5 —mitad y mitad— porque una variación real se
# construye con dos series de precisión comparable, la nominal y el deflactor.
FRAC_ERROR_DEFLACTOR = 0.5

INDICES = {
    "itcm": {"cinturon": "macro", "bandas": itcm.BANDAS_ITCM,
             "anclas": itcm.ANCLAS_ITCM,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itcg": {"cinturon": "gestion", "bandas": itcg.BANDAS_ITCG,
             "tension": lambda v: round((100 - v) / 10, 1)},
    "itvc": {"cinturon": "vida_cotidiana", "bandas": None,   # continuo
             "tension": lambda v: round(min(10.0, max(0.0, 5 - (v - 100) * 0.2)), 1)},
    "itcp": {"cinturon": "politica", "bandas": itcp.BANDAS_ITCP,
             "tension": lambda v: round((100 - v) / 10, 1)},
}


def _estructura(bloque: dict) -> dict:
    """{dkey: {peso, ind: {ikey: {peso, puntaje, banda, valor}}}} desde el
    bloque publicado (valor = insumo crudo, para el experimento de insumos)."""
    return {
        dk: {
            "peso": d["peso"],
            "ind": {ik: {"peso": i["peso"], "puntaje": i["puntaje_aplicado"],
                         "banda": i.get("puntaje_banda"), "valor": i.get("valor")}
                    for ik, i in d["indicadores"].items()},
        }
        for dk, d in bloque["dimensiones"].items()
    }


def _agregar(dims: dict) -> float:
    """Promedio ponderado con renormalización ante faltantes (la misma
    agregación de parametrica.calcular_indice / itvc.calcular_itvc)."""
    total, wsum = 0.0, 0.0
    for d in dims.values():
        if not d["ind"]:
            continue
        pw = sum(i["peso"] for i in d["ind"].values())
        dscore = sum(i["puntaje"] * i["peso"] for i in d["ind"].values()) / pw
        total += dscore * d["peso"]
        wsum += d["peso"]
    return total / wsum if wsum else 0.0


def _perturbar(dims: dict, rng: random.Random, *, pesos: bool,
               bandas: dict | None, anclas: dict | None = None,
               exposicion: dict | None = None) -> float:
    anclas = anclas or {}
    exposicion = exposicion or {}
    # Un ÚNICO error de deflactor por corrida, compartido por todos los
    # indicadores que lo heredan (ADR-0078). Es lo que hace que sus errores no
    # se cancelen entre sí en la agregación.
    shock_deflactor = rng.uniform(-RUIDO_INSUMO, RUIDO_INSUMO)
    d2 = {dk: {"peso": d["peso"], "ind": {ik: dict(i) for ik, i in d["ind"].items()}}
          for dk, d in dims.items()}
    for d in d2.values():
        if pesos:
            d["peso"] *= rng.uniform(1 - RUIDO_PESO, 1 + RUIDO_PESO)
        for ik, i in d["ind"].items():
            if pesos:
                i["peso"] *= rng.uniform(1 - RUIDO_PESO, 1 + RUIDO_PESO)
            puntuable = (bandas and ik in bandas) or ik in anclas
            if puntuable and i.get("valor") is not None \
                    and i.get("banda") == i["puntaje"]:   # con override no se perturba
                # Ruido ADITIVO: ±RUIDO_INSUMO del ancho entre anclas finitas
                # (scale-free, ADR-0031). El multiplicativo original subestimaba
                # la incertidumbre de los indicadores con signo o centrados en
                # cero (IdC en σ, IDM en pp): ±5% de un valor cercano a 0 no
                # perturba nada.
                if ik in anclas:
                    ancs = [float(x) for x, _ in anclas[ik]]
                else:
                    inf_ = float("inf")
                    ancs = [
                        a for banda in bandas[ik] for a in banda[:2]
                        if abs(a) != inf_
                    ]
                span = (max(ancs) - min(ancs)) if ancs else abs(float(i["valor"])) or 1.0
                idio = rng.uniform(-RUIDO_INSUMO, RUIDO_INSUMO)
                exp = exposicion.get(ik, 0.0)
                if exp:
                    # Mezcla que preserva la varianza total del ruido: la parte
                    # compartida reemplaza a la idiosincrática, no se le suma.
                    f = FRAC_ERROR_DEFLACTOR
                    ruido = math.sqrt(f) * exp * shock_deflactor + math.sqrt(1 - f) * idio
                else:
                    ruido = idio
                v = float(i["valor"]) + ruido * span
                if ik in anclas:
                    i["puntaje"] = parametrica.puntaje_desde_anclas(v, anclas[ik])
                else:
                    i["puntaje"] = parametrica.puntaje_interpolado(v, bandas[ik])
    return _agregar(d2)


def _resumen(muestras: list) -> dict:
    qs = statistics.quantiles(muestras, n=20)          # 5% … 95%
    return {"media": round(statistics.fmean(muestras), 1),
            "p05": round(qs[0], 1), "p95": round(qs[-1], 1),
            "desvio": round(statistics.pstdev(muestras), 2)}


def analizar_bloque(bloque: dict, bandas: dict | None, tension_fn,
                    n_draws: int = N_DRAWS,
                    anclas: dict | None = None) -> dict:
    """Análisis completo de un bloque de índice publicado (dimensiones con
    puntajes): experimentos de pesos/bandas/combinado + leave-one-out.
    Función PURA sobre el bloque — la usa este script y también publicar.py
    para adjuntar el rango de robustez al snapshot (ADR-0019, Decisión 1)."""
    dims = _estructura(bloque)
    base = _agregar(dims)
    rng = random.Random(SEMILLA)

    exp = {"pesos": [], "combinado": []}
    if bandas:
        exp["insumos"] = []
    for _ in range(n_draws):
        exp["pesos"].append(_perturbar(dims, rng, pesos=True, bandas=None))
        if bandas:
            exp["insumos"].append(_perturbar(
                dims, rng, pesos=False, bandas=bandas, anclas=anclas
            ))
        exp["combinado"].append(_perturbar(
            dims, rng, pesos=True, bandas=bandas, anclas=anclas
        ))

    loo = {}
    for dk, d in dims.items():
        for ik in d["ind"]:
            d2 = {k: {"peso": v["peso"], "ind": {i: dict(x) for i, x in v["ind"].items()}}
                  for k, v in dims.items()}
            del d2[dk]["ind"][ik]
            loo[ik] = round(_agregar(d2), 1)

    t = tension_fn
    comb = _resumen(exp["combinado"])
    return {
        "valor_publicado": bloque["valor"],
        "valor_recomputado": round(base, 1),
        "experimentos": {k: _resumen(v) for k, v in exp.items()},
        "leave_one_out": dict(sorted(loo.items(), key=lambda kv: abs(kv[1] - base),
                                     reverse=True)),
        "tension": {"base": t(base),
                    "rango_combinado": [t(comb["p95"]), t(comb["p05"])]},
    }


def robustez_compacta(bloque: dict, bandas: dict | None, tension_fn,
                      n_draws: int = 1000, n_bins: int = 36,
                      anclas: dict | None = None,
                      exposicion: dict | None = None) -> dict:
    """Versión compacta para el snapshot publicado: rango p05-p95 del
    experimento combinado + su traducción a tensión + el componente dominante
    (mayor |Δ| del leave-one-out) + el HISTOGRAMA de la simulación (n_bins
    bins entre el mínimo y el máximo de los draws) para el gráfico de
    distribución de la web."""
    dims = _estructura(bloque)
    rng = random.Random(SEMILLA)
    draws = [
        _perturbar(dims, rng, pesos=True, bandas=bandas, anclas=anclas,
                   exposicion=exposicion)
        for _ in range(n_draws)
    ]
    qs = statistics.quantiles(draws, n=20)
    p05, p95 = round(qs[0], 1), round(qs[-1], 1)

    lo, hi = min(draws), max(draws)
    hist = [0] * n_bins
    if hi > lo:
        for v in draws:
            hist[min(n_bins - 1, int((v - lo) / (hi - lo) * n_bins))] += 1

    base = _agregar(dims)
    loo = {}
    for dk, d in dims.items():
        for ik in d["ind"]:
            d2 = {k: {"peso": v["peso"], "ind": {i: dict(x) for i, x in v["ind"].items()}}
                  for k, v in dims.items()}
            del d2[dk]["ind"][ik]
            loo[ik] = round(_agregar(d2), 1)
    dominante = max(loo.items(), key=lambda kv: abs(kv[1] - base), default=None)

    return {
        "p05": p05,
        "p95": p95,
        "tension_rango": [tension_fn(p95), tension_fn(p05)],
        "dominante": ({"indicador": dominante[0],
                       "indice_sin": dominante[1]} if dominante else None),
        "n_draws": n_draws,
        "hist": hist,
        "hist_min": round(lo, 2),
        "hist_max": round(hi, 2),
        # OJO: este texto se publica (lo valida el gate G6). Sin siglas de ADR
        # ni jerga interna.
        "metodo": ("pesos ±20% + insumos ±5% del rango entre anclas, re-puntuados por "
                   "interpolación (Monte Carlo). El error del índice de precios se sortea "
                   "una sola vez por corrida y se propaga a los indicadores que lo usan "
                   "como deflactor, en lugar de suponer que cada uno se equivoca por su "
                   "cuenta."),
    }


def analizar(nombre: str, bloque: dict, cfg: dict) -> dict:
    resultado = analizar_bloque(
        bloque, cfg["bandas"], cfg["tension"],
        anclas=cfg.get("anclas"),
    )
    base = resultado["valor_recomputado"]
    t = cfg["tension"]

    comb = resultado["experimentos"]["combinado"]
    print(f"\n== {nombre.upper()} — publicado {bloque['valor']} "
          f"(recomputado {round(base, 1)}) ==")
    for k, r in resultado["experimentos"].items():
        print(f"  {k:10s}: media {r['media']}  ·  p05-p95 [{r['p05']} – {r['p95']}]"
              f"  ·  σ {r['desvio']}")
    print(f"  → robustez: {nombre.upper()} {round(base, 1)} "
          f"[{comb['p05']} – {comb['p95']}]  ·  tensión {t(base)} "
          f"[{t(comb['p95'])} – {t(comb['p05'])}]")
    top = list(resultado["leave_one_out"].items())[:4]
    print("  componentes dominantes (índice sin el componente):")
    for ik, v in top:
        print(f"    - sin {ik}: {v}  (Δ {round(v - base, 1):+})")
    return resultado


def main():
    global N_DRAWS
    if len(sys.argv) > 1:
        N_DRAWS = int(sys.argv[1])
    informe = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    salida = {"_meta": {"n_draws": N_DRAWS, "semilla": SEMILLA,
                        "ruido_peso": RUIDO_PESO, "ruido_insumo": RUIDO_INSUMO,
                        "snapshot": informe.get("generado", ""), "adr": "0019"}}
    for nombre, cfg in INDICES.items():
        bloque = informe["cinturones"][cfg["cinturon"]].get(nombre)
        if not bloque:
            print(f"[WARN] {nombre}: sin bloque en el snapshot")
            continue
        salida[nombre] = analizar(nombre, bloque, cfg)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
