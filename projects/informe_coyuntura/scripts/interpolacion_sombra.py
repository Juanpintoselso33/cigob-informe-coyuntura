"""interpolacion_sombra.py — Estudio sombra: bandas vs interpolación (ADR-0019, Decisión 3).

Recalcula el ITCM y el ITCG con puntaje CONTINUO — interpolación lineal entre
los anclajes de las bandas del doc (piecewise linear) — en paralelo al método
vigente por bandas, y mide la diferencia. Es el insumo para proponer (o no)
el cambio de método a CIGOB. NO toca el índice publicado.

Anclajes: cada banda finita ancla su puntaje en su PUNTO MEDIO; las bandas
abiertas (±inf) anclan en su borde finito. Fuera del rango de anclajes el
puntaje queda plano (el de la banda extrema) — sin extrapolación. Los
overrides del analista se respetan igual que en producción.

Uso: python scripts/interpolacion_sombra.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcm
import itcg

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web" / "src" / "data" / "informe.json"
SALIDA = ROOT / "output" / "interpolacion_sombra.json"
INF = float("inf")


def _anclas(bandas: list) -> list:
    """[(valor, puntaje)] ordenado: punto medio de las bandas finitas, borde
    finito de las abiertas."""
    out = []
    for lo, hi, p in bandas:
        if lo == -INF and hi == INF:
            continue
        if lo == -INF:
            out.append((float(hi), float(p)))
        elif hi == INF:
            out.append((float(lo), float(p)))
        else:
            out.append(((float(lo) + float(hi)) / 2.0, float(p)))
    return sorted(out)


def puntaje_interpolado(valor: float, bandas: list) -> float:
    """Puntaje continuo: lineal entre anclajes, plano en los extremos."""
    a = _anclas(bandas)
    if valor <= a[0][0]:
        return a[0][1]
    if valor >= a[-1][0]:
        return a[-1][1]
    for (x0, p0), (x1, p1) in zip(a, a[1:]):
        if x0 <= valor <= x1:
            if x1 == x0:
                return p1
            return p0 + (p1 - p0) * (valor - x0) / (x1 - x0)
    return a[-1][1]


def recalcular(bloque: dict, bandas_mod: dict) -> tuple:
    """(índice interpolado, {dim: puntaje}, [detalle por indicador]) con la
    misma agregación/renormalización que producción."""
    dims_out, detalles = {}, []
    total, wsum = 0.0, 0.0
    for dkey, dim in bloque["dimensiones"].items():
        acc, pw = 0.0, 0.0
        for ikey, info in dim["indicadores"].items():
            if info["puntaje_aplicado"] != info["puntaje_banda"]:
                p_int = float(info["puntaje_aplicado"])      # override del analista: se respeta
            elif info.get("valor") is not None and ikey in bandas_mod:
                p_int = puntaje_interpolado(float(info["valor"]), bandas_mod[ikey])
            else:
                p_int = float(info["puntaje_aplicado"])
            detalles.append({
                "dimension": dkey, "indicador": ikey,
                "valor": info.get("valor"),
                "banda": info["puntaje_banda"],
                "interpolado": round(p_int, 1),
                "delta": round(p_int - info["puntaje_aplicado"], 1),
            })
            acc += p_int * info["peso"]
            pw += info["peso"]
        dscore = acc / pw
        dims_out[dkey] = round(dscore, 1)
        total += dscore * dim["peso"]
        wsum += dim["peso"]
    return round(total / wsum, 1), dims_out, detalles


def main():
    informe = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    salida = {"_meta": {"adr": "0019 Decisión 3", "metodo": "anclaje en punto medio de banda, lineal entre anclajes, plano en extremos"}}
    for nombre, ck, mod in (("itcm", "macro", itcm), ("itcg", "gestion", itcg)):
        bloque = informe["cinturones"][ck].get(nombre)
        if not bloque:
            continue
        bandas = getattr(mod, f"BANDAS_{nombre.upper()}")
        interp, dims, detalles = recalcular(bloque, bandas)
        banda_val = bloque["valor"]
        salida[nombre] = {
            "indice_bandas": banda_val,
            "indice_interpolado": interp,
            "delta": round(interp - banda_val, 1),
            "tension_bandas": round((100 - banda_val) / 10, 1),
            "tension_interpolada": round((100 - interp) / 10, 1),
            "dimensiones_interpoladas": dims,
            "detalle": sorted(detalles, key=lambda d: -abs(d["delta"])),
        }
        print(f"\n== {nombre.upper()} — bandas {banda_val} vs interpolado {interp} "
              f"(Δ {round(interp - banda_val, 1):+}) · tensión "
              f"{round((100 - banda_val) / 10, 1)} vs {round((100 - interp) / 10, 1)} ==")
        print("  mayores diferencias por indicador (banda → interpolado):")
        for d in salida[nombre]["detalle"][:6]:
            print(f"    {d['indicador']}: valor {d['valor']} · {d['banda']} → "
                  f"{d['interpolado']}  (Δ {d['delta']:+})")
    SALIDA.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
