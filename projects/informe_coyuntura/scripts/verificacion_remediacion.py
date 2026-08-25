# -*- coding: utf-8 -*-
"""Controles obligatorios de la remediación (Entrega 5 del handoff 25-ago-2026).

No reemplaza a `gate_calidad.py` ni a la suite: verifica lo que ninguno de los
dos mira, que es si el snapshot nuevo **es consistente con las decisiones que se
tomaron**. Cada control responde una pregunta que el handoff hace explícita:

    python scripts/verificacion_remediacion.py docs/auditoria_indicadores/linea_base_260825.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcg  # noqa: E402
import itcm  # noqa: E402
import itcp  # noqa: E402
import itvc  # noqa: E402
import publicar  # noqa: E402

PARAMETRICA = {"macro": ("itcm", itcm), "politica": ("itcp", itcp),
               "vida_cotidiana": ("itvc", itvc), "gestion": ("itcg", itcg)}
OCULTOS = {"macro": publicar.MACRO_OCULTOS, "politica": publicar.POLITICA_OCULTOS,
           "vida_cotidiana": publicar.VIDA_OCULTOS, "gestion": publicar.GESTION_OCULTOS}

# Lo que cada entrega decidió, para poder verificarlo contra el snapshot y no
# contra la memoria de quien lo revisa.
SUSPENDIDOS = {
    "apoyo_empresario": "0246", "reestructuracion_organismos": "0247",
    "sentimiento_digital": "0248", "judicializacion": "0255",
}
# Un indicador cuya auditoría verificó un MES concreto no se controla contra la
# card —que avanza con el calendario— sino contra ese punto de la serie. Mezclar
# «corregí el dato» con «llegó un mes nuevo» es justamente lo que el handoff
# pide reportar por separado: el costo del financiamiento pasó de 8,07% a 4,93%
# en junio (la corrección) y la corrida trajo julio en 5,80% (la actualización).
VALORES_EN_SERIE = {            # indicador: (mes, valor, tolerancia, ADR)
    "costo_financiamiento_tesoro": ("2026-06", 4.92, 0.05, "0238"),
}

VALORES_ESPERADOS = {           # indicador: (valor, tolerancia, ADR)
    "iaf_transferencias": (1.6, 0.15, "0239"),
    "ratio_dnu": (1.48, 0.06, "0241"),
    # ±0,15 y no más: CABA marcaba 39,87 contra 40,23 del nacional, y una
    # tolerancia de 0,35 no distinguiría una columna de la otra (ADR-0242).
    "icc_utdt": (40.2, 0.15, "0242"),
    "concesiones_infraestructura": (100.0, 0.6, "0244"),
    "credito_privado": (-1.5, 0.8, "0251"),
}
IDS_MUERTOS = ("pluriempleo",)
UNIDADES_ESPERADAS = {
    "consumo_supermercados": "2017",
    "subocupacion_demandante": "PEA",
    "trabajo_independiente": "sin monotributo social",
    "credito_privado": "pesos",
    "ratio_dnu": "publicados",
}


def _cargar(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def verificar(snap: dict, base: dict) -> tuple[list, list]:
    fallas, avisos = [], []
    inds = {}
    for cint, bloque in snap["cinturones"].items():
        for k, v in bloque["indicadores"].items():
            inds[k] = {**v, "_cinturon": cint}

    # 1 · ningún suspendido aporta al índice, y ninguno se muestra
    for ind, adr in SUSPENDIDOS.items():
        if ind in inds:
            fallas.append(f"[suspendido] `{ind}` (ADR-{adr}) sigue publicándose como card")
        cint = next((c for c, o in OCULTOS.items() if ind in o), None)
        if cint is None:
            fallas.append(f"[suspendido] `{ind}` no está en la lista de ocultos de ningún cinturón")

    # 2 · los pesos suman 1 por dimensión y por cinturón
    for cint, (clave, _mod) in PARAMETRICA.items():
        par = snap["cinturones"][cint].get(clave) or {}
        dims = par.get("dimensiones") or {}
        if not dims:
            fallas.append(f"[pesos] {cint}: el snapshot no trae dimensiones")
            continue
        total = 0.0
        for dk, d in dims.items():
            interno = sum(i["peso_efectivo"] for i in d["indicadores"].values())
            if abs(interno - d["peso_efectivo"]) > 0.002:
                fallas.append(f"[pesos] {cint}/{dk}: los indicadores suman "
                              f"{interno:.4f} y la dimensión pesa {d['peso_efectivo']:.4f}")
            total += d["peso_efectivo"]
            for ik in d["indicadores"]:
                if ik in SUSPENDIDOS:
                    fallas.append(f"[suspendido] `{ik}` tiene peso efectivo en {cint}/{dk}")
        if abs(total - 1.0) > 0.002:
            fallas.append(f"[pesos] {cint}: los pesos efectivos suman {total:.4f}, no 1")

    # 3 · los valores que la auditoría verificó
    for ind, (esperado, tol, adr) in VALORES_ESPERADOS.items():
        if ind not in inds:
            fallas.append(f"[valor] `{ind}` (ADR-{adr}) no está en el snapshot")
            continue
        v = inds[ind].get("valor")
        if v is None:
            fallas.append(f"[valor] `{ind}` publicó None")
        elif abs(v - esperado) > tol:
            fallas.append(f"[valor] `{ind}` = {v}; ADR-{adr} verificó {esperado} (±{tol})")

    # 3b · los meses que la auditoría verificó, leídos de la SERIE
    series_path = RAIZ / "web" / "src" / "data" / "series.json"
    series = json.loads(series_path.read_text(encoding="utf-8")) if series_path.exists() else {}
    for ind, (mes, esperado, tol, adr) in VALORES_EN_SERIE.items():
        puntos = {str(p.get("fecha"))[:7]: p.get("valor")
                  for p in (series.get(ind) or [])}
        if mes not in puntos:
            fallas.append(f"[serie] `{ind}` no tiene el punto {mes} que verificó ADR-{adr}")
            continue
        v = puntos[mes]
        if v is None or abs(v - esperado) > tol:
            fallas.append(f"[serie] `{ind}` en {mes} = {v}; ADR-{adr} verificó {esperado}")
        card_mes = str(inds.get(ind, {}).get("fecha_dato") or "")[:7]
        if card_mes and card_mes > mes:
            avisos.append(f"[actualización] `{ind}`: la auditoría verificó {mes} "
                          f"({esperado}) y la card publica {card_mes} "
                          f"({inds[ind].get('valor')}) — es dato nuevo, no una corrección")

    # 4 · identificadores dados de baja
    crudo = json.dumps(snap, ensure_ascii=False)
    for muerto in IDS_MUERTOS:
        if f'"{muerto}"' in crudo:
            fallas.append(f"[id] reapareció el identificador dado de baja `{muerto}`")

    # 5 · unidades que se corrigieron
    for ind, marca in UNIDADES_ESPERADAS.items():
        if ind not in inds:
            continue
        u = (inds[ind].get("unidad") or "") + " " + (inds[ind].get("fuente") or "")
        if marca.lower() not in u.lower():
            fallas.append(f"[unidad] `{ind}` no declara «{marca}»: {inds[ind].get('unidad')!r}")

    # 6 · toda card con valor tiene fecha, y toda card del índice tiene puntaje
    for k, v in inds.items():
        if v.get("valor") is not None and not v.get("fecha_dato"):
            fallas.append(f"[frescura] `{k}` publica valor sin fecha_dato")
        if v.get("en_indice") and v.get("valor") is not None:
            if v.get("puntaje_banda") is None and v.get("indice_itvc") is None:
                avisos.append(f"[puntaje] `{k}` integra el índice y no trae puntaje")

    # 7 · comparación de los 69, no sólo de los intervenidos. Los dos lados se
    # reportan: con cuatro suspensiones y un renombre, mirar sólo las bajas
    # dejaría fuera al indicador que cambió de nombre.
    ib = base["indicadores"]
    salieron = sorted(set(ib) - set(inds))
    entraron = sorted(set(inds) - set(ib))
    if salieron:
        avisos.append(f"[perímetro] salieron ({len(salieron)}): {', '.join(salieron)}")
    if entraron:
        avisos.append(f"[perímetro] entraron ({len(entraron)}): {', '.join(entraron)}")
    avisos.append(f"[perímetro] {len(ib)} indicadores antes → {len(inds)} después")
    return fallas, avisos


def tabla(snap: dict, base: dict) -> list[str]:
    ib, out = base["indicadores"], []
    inds = {k: {**v, "_c": c} for c, b in snap["cinturones"].items()
            for k, v in b["indicadores"].items()}
    out.append("| indicador | cinturón | antes | después | banda antes | banda después |")
    out.append("|---|---|---:|---:|---:|---:|")
    movidos = 0
    for k in sorted(set(ib) | set(inds)):
        a, d = ib.get(k), inds.get(k)
        va = a["valor"] if a else None
        vd = d["valor"] if d else None
        ba = a["puntaje_banda"] if a else None
        bd = d.get("puntaje_banda") if d else None
        if va == vd and ba == bd:
            continue
        movidos += 1
        f = lambda x: "—" if x is None else (f"{x:g}" if isinstance(x, float) else str(x))
        out.append(f"| `{k}` | {(d or a).get('_c') or (a or {}).get('cinturon')} | "
                   f"{f(va)} | {f(vd)} | {f(ba)} | {f(bd)} |")
    out.append("")
    out.append(f"Se movieron {movidos} de {len(set(ib) | set(inds))} indicadores.")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("base", type=Path)
    p.add_argument("--snapshot", type=Path,
                   default=RAIZ / "web" / "src" / "data" / "informe.json")
    p.add_argument("--tabla", action="store_true")
    a = p.parse_args(argv)

    snap, base = _cargar(a.snapshot), _cargar(a.base)
    fallas, avisos = verificar(snap, base)

    if a.tabla:
        print("\n".join(tabla(snap, base)))
        print()

    for x in avisos:
        print(f"  AVISO  {x}")
    if fallas:
        print(f"\n[FALLA] {len(fallas)} controles no pasaron:")
        for x in fallas:
            print(f"  - {x}")
        return 1
    print(f"\n[OK] los controles de la remediación pasan "
          f"(score global {base['score_global']} → {snap.get('score_global')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
