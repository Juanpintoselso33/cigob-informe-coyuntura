"""procedencia_anclas.py — de dónde sale cada ancla del proyecto (ADR-0103).

La auditoría del cinturón de gestión (jul-2026, punto 3.2) planteó el riesgo de
CIRCULARIDAD: si las bandas se fijan mirando lo que el gobierno ya logró, es más
fácil que el puntaje tienda a ser alto. Pidió "distinguir, en la documentación
pública, qué bandas están ancladas a un criterio normativo externo y cuáles son
convenciones internas de CIGOB".

Este archivo es esa distinción, ejecutable. No elimina el sesgo —con 36 de 42
indicadores sin historia previa a dic-2023, la calibración interna es
irreducible— pero lo vuelve CONTABLE: cuánto del peso de cada índice descansa en
anclas que sólo pueden validarse contra el período que se está midiendo.

LAS CATEGORÍAS, de menor a mayor riesgo:

  externa         Referencia verificable fuera del proyecto y ajena al período
                  medido: un estudio publicado, la práctica histórica de otros
                  gobiernos. Es el estándar al que conviene tender.
  documento       Fijada en el documento de diseño del proyecto ANTES de ver los
                  datos. No es externa, pero tampoco se acomodó al resultado.
  conceptual      Anclada a un valor con significado propio —el cero, la
                  paridad, el 100%— y no a un rango observado.
  historia_larga  Calibrada contra la serie propia del indicador, pero incluyendo
                  períodos anteriores a esta gestión.
  convencion      Calibrada mirando el rango observado desde dic-2023. Es el caso
                  que la auditoría señala: defendible y declarado, pero circular.
  sin_declarar    El código no dice de dónde sale. Peor que una convención: una
                  convención invisible.

CÓMO SE LLENÓ: leyendo, uno por uno, los comentarios de BANDAS_* en itcm.py,
itcg.py e itcp.py. Es una clasificación de CRITERIO y una primera pasada — el
editor debería revisarla, sobre todo los casos marcados `convencion`, que son
los que la auditoría pide vigilar.

Uso: python scripts/procedencia_anclas.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcm
import itcg
import itcp

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "output" / "procedencia_anclas.json"

CATEGORIAS = ("externa", "documento", "conceptual", "historia_larga",
              "convencion", "sin_declarar")

# indicador → (categoría, de dónde sale). El segundo campo es lo que hace
# auditable la clasificación: cualquiera puede ir al comentario y discutirla.
PROCEDENCIA = {
    # ── ITCM ────────────────────────────────────────────────────────────────
    "ipc_total": ("sin_declarar", "el comentario sólo dice la unidad («% mensual»)"),
    "rem_ipc_12m": ("sin_declarar", "el comentario explica la transformación a equivalente mensual, no de dónde salen los cortes"),
    "idm": ("convencion", "«calibrado con la historia 2024-2026»"),
    "presion_dolarizacion": ("documento", "«conserva los cortes institucionales» del documento de diseño"),
    "recaudacion": ("sin_declarar", "el comentario sólo dice la unidad"),
    "saldo_comercial_12m": ("sin_declarar", "el comentario sólo dice la unidad"),
    "reservas_bcra": ("sin_declarar", "el comentario sólo aclara netas vs brutas"),
    "idc": ("conceptual", "anclas en desvíos estándar: +1σ ≈ p84 · −1σ ≈ p16 (ADR-0028)"),
    "emae_ia": ("sin_declarar", "el comentario sólo dice la unidad"),
    "ipi_manufacturero": ("sin_declarar", "hereda las bandas del EMAE a propósito (ADR-0076/0079), que a su vez no declaran origen"),
    "tcrm": ("historia_larga", "historia 1997-2026: p10≈75, p25≈87, mediana≈106 — 29 años, cinco gobiernos"),
    "resultado_primario": ("convencion", "referencias dic-2023 (−12,0%) y el programa estabilizado en +6/+8% (ADR-0072)"),
    "costo_financiamiento_tesoro": ("convencion", "extremos tomados de dic-2023 (−12,2%) y ago-2025 (+33,5%) (ADR-0071)"),
    "iai": ("convencion", "el umbral ±2% del documento «no sobrevive al dato»: se reemplazó por bandas calibradas a 2024-2026"),
    "icip": ("convencion", "banda ensanchada por la volatilidad observada del período"),
    "credito_privado": ("convencion", "«calibradas a la remonetización 2024-2026» (ADR-0022)"),

    # ── ITCG ────────────────────────────────────────────────────────────────
    "cepo_mulc": ("documento", "«brecha sostenida <10-15% = condiciones óptimas de unificación» (doc 260702)"),
    "apertura_comercial": ("documento", "anclas sobre la lineal del documento: 0% → 100 · 15% → 0 (ADR-0021)"),
    "desregulacion_normativa": ("convencion", "la meta de 100 normas = plan completo es convención propia, declarada en ADR-0096"),
    "reduccion_estado": ("convencion", "«calibrado con el dato real»: el recorte observado de ~10-12% define la banda 85"),
    "gasto_funcionamiento": ("convencion", "bandas anchas por el ajuste de 2024, que la propia ficha llama históricamente atípico"),
    "masa_salarial": ("sin_declarar", "el comentario sólo dice la unidad"),
    "reestructuracion_organismos": ("sin_declarar", "el comentario sólo dice la unidad"),
    "fal_modernizacion_laboral": ("conceptual", "cortes sobre los estados que la escala puede tomar, no sobre el rango observado (ADR-0098)"),
    "privatizaciones": ("documento", "etapas 0-4 definidas en el documento de diseño"),
    "rigi_inversiones": ("convencion", "referencia el 22,1% de jun-2026 y la composición del pipeline de ese momento"),
    "concesiones_infraestructura": ("sin_declarar", "el comentario sólo dice la unidad"),
    # asistencia_directa salió del índice por ADR-0100 (clavada en 100,0): su
    # banda sigue existiendo pero ya no pondera, así que no entra acá.
    "protocolo_antipiquetes": ("convencion", "calibrada con la caída observada en CABA en 2024-2025"),
    "libertad_opcion_salud": ("sin_declarar", "el comentario sólo dice la unidad"),
    "litigiosidad_laboral": ("historia_larga", "calibrada sobre 2021-2026, que incluye dos gobiernos (ADR-0023)"),

    # ── ITCP ────────────────────────────────────────────────────────────────
    "votometro_ventaja_lla": ("sin_declarar", "el comentario sólo dice la unidad"),
    "ratio_dnu": ("externa", "ACIJ 2011-2024, cuatro presidencias: 344 DNU / 1.058 leyes ≈ 0,33 (ADR-0058/0059)"),
    "eficacia_legislativa": ("externa", "Directorio Legislativo: 40-50% Macri · 63-67% Alberto Fernández · 75-82% CFK (ADR-0061)"),
    "veto_quorum": ("sin_declarar", "el comentario sólo dice la unidad y la dirección"),
    "desafios_legislativos": ("convencion", "anclas sobre el conteo observado (4 a 13 en 22 meses), leído contra el carácter excepcional del acto (ADR-0089)"),
    "brecha_obra_publica": ("conceptual", "números redondos alrededor del cero, explícitamente NO calibrados contra el rango observado (ADR-0088)"),
    "bloqueo_sostenido": ("externa", "ninguna insistencia exitosa entre 2003 y 2025: ~100% histórico de sostenimiento (ADR-0069)"),
    "iaf_transferencias": ("sin_declarar", "el comentario sólo dice la unidad y la dirección"),
    "alineamiento_senadores_prov": ("convencion", "recalibrada con 29 puntos propios de feb-2024 en adelante (ADR-0038)"),
    "adhesion_reformas_provincial": ("conceptual", "anclas NO tocadas: la adhesión es un evento irreversible y el rango de hoy es un punto de partida, no el rango final (ADR-0044)"),
    "cohesion_bloque": ("convencion", "calibrada contra su propia serie reconstruida desde 2024 (ADR-0042/0048)"),
    "conflictividad_nacional": ("convencion", "calibrada contra los 30 puntos propios de la serie ACLED desde 2024 (ADR-0052)"),
}


def _indicadores_del_indice():
    """{indicador: (sigla, peso_efectivo_nominal)} de los que PUNTÚAN hoy."""
    out = {}
    for mod, sig in ((itcm, "ITCM"), (itcg, "ITCG"), (itcp, "ITCP")):
        dims = getattr(mod, f"DIMENSIONES_{sig}")
        for dim in dims.values():
            peso_dim = dim["peso"]
            for ind, peso_ind in dim["indicadores"].items():
                out[ind] = (sig, peso_dim * peso_ind)
    return out


def informe() -> dict:
    """Cuánto del peso de cada índice descansa en cada tipo de ancla."""
    indicadores = _indicadores_del_indice()
    por_indice = {}
    faltantes = []
    for ind, (sig, peso) in indicadores.items():
        if ind not in PROCEDENCIA:
            faltantes.append(ind)
            continue
        categoria, motivo = PROCEDENCIA[ind]
        bloque = por_indice.setdefault(sig, {"peso_total": 0.0, "categorias": {}, "detalle": []})
        bloque["peso_total"] += peso
        bloque["categorias"][categoria] = bloque["categorias"].get(categoria, 0.0) + peso
        bloque["detalle"].append({"indicador": ind, "categoria": categoria,
                                  "peso": round(peso, 4), "motivo": motivo})

    for sig, bloque in por_indice.items():
        total = bloque["peso_total"] or 1.0
        bloque["share"] = {c: round(p / total, 3) for c, p in bloque["categorias"].items()}
        # el número que la auditoría pide vigilar
        riesgo = sum(p for c, p in bloque["categorias"].items()
                     if c in ("convencion", "sin_declarar"))
        bloque["share_circular"] = round(riesgo / total, 3)
        bloque["detalle"].sort(key=lambda d: (CATEGORIAS.index(d["categoria"]), -d["peso"]))

    return {"por_indice": por_indice, "sin_clasificar": sorted(faltantes)}


def main():
    r = informe()
    if r["sin_clasificar"]:
        print(f"[WARN] indicadores sin procedencia declarada: {r['sin_clasificar']}")
    print("Procedencia de las anclas — cuánto del peso de cada índice es circular\n")
    for sig, b in sorted(r["por_indice"].items()):
        print(f"{sig}  (riesgo de circularidad: {b['share_circular']:.0%} del peso)")
        for cat in CATEGORIAS:
            if cat in b["share"]:
                print(f"    {cat:15s} {b['share'][cat]:5.0%}")
        print()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {SALIDA}")


if __name__ == "__main__":
    main()
