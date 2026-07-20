"""out_of_sample.py — ¿la banda sigue discriminando fuera del período que midió?

Complemento de ADR-0103. Aquél clasifica de dónde sale cada ancla; éste pone a
prueba las que resultaron circulares.

LA PREGUNTA. Una banda calibrada mirando el rango 2024-2026 puede describir muy
bien ese rango y no significar nada fuera de él. Si es así, aplicada a los años
anteriores debería mostrar una firma característica: los puntajes se APLASTAN
contra el techo o el piso, porque el régimen anterior cae entero de un lado de
las anclas. Una banda que mide algo real, en cambio, sigue separando meses
buenos de malos en cualquier período.

POR QUÉ POR INDICADOR Y NO POR ÍNDICE. Lo natural sería reconstruir cada índice
para gobiernos anteriores y comparar. No se puede: sólo el 31% del peso del
ITCM, el 24% del ITCP y el 4% del ITCG tiene serie anterior a dic-2023.
Reconstruir "el ITCM de Macri" con un tercio de sus indicadores daría un número
con apariencia de dato y sin contenido. La unidad honesta acá es el indicador.

EL CONTROL. `brecha_obra_publica` es el control positivo del test: tiene 100
meses de serie y ADR-0088 declara explícitamente que sus anclas NO se
calibraron contra el rango observado, sino alrededor del cero. Si el método
sirve, esa banda tiene que discriminar en ambas ventanas. Si el control falla,
lo que está mal es el test y no la banda.

Uso: python scripts/out_of_sample.py
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcm
import itcg
import itcp
import parametrica
import procedencia_anclas as pa
from validacion_externa import _serie_indicador

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "output" / "out_of_sample.json"

CORTE = "2023-12"      # asunción de Milei: todo lo anterior es fuera de muestra
MIN_PUNTOS = 12        # menos de un año fuera de muestra no permite concluir nada
CERCA_DEL_EXTREMO = 2.0   # a cuántos puntos del tope/piso se considera saturado

ESCALAS = {
    "ITCM": parametrica.Escala(itcm.BANDAS_ITCM, getattr(itcm, "ANCLAS_ITCM", None),
                               getattr(itcm, "TRANSFORMACIONES_ITCM", None)),
    "ITCG": parametrica.Escala(itcg.BANDAS_ITCG, getattr(itcg, "ANCLAS_ITCG", None),
                               getattr(itcg, "TRANSFORMACIONES_ITCG", None)),
    "ITCP": parametrica.Escala(itcp.BANDAS_ITCP, getattr(itcp, "ANCLAS_ITCP", None),
                               getattr(itcp, "TRANSFORMACIONES_ITCP", None)),
}


def _extremos(escala, indicador):
    """(piso, techo) de puntaje alcanzables por este indicador.

    No se asume 10/100: cada banda define los suyos y saturar significa llegar
    al extremo PROPIO, no a un número fijo."""
    if indicador in escala.anclas:
        ps = [float(p) for _, p in escala.anclas[indicador]]
    else:
        ps = [float(b[2]) for b in escala.bandas[indicador]]
    return min(ps), max(ps)


def _resumen(puntajes, crudos, piso, techo):
    """Distribución de puntajes de una ventana, CON el rango crudo al lado.

    El crudo no es decorativo: es lo único que permite distinguir una banda que
    no alcanza el período de un período que fue de verdad extremo. Sin él, la
    tabla invita a la conclusión equivocada.
    """
    if not puntajes:
        return None
    sat = sum(1 for p in puntajes
              if p <= piso + CERCA_DEL_EXTREMO or p >= techo - CERCA_DEL_EXTREMO)
    return {
        "n": len(puntajes),
        "media": round(statistics.fmean(puntajes), 1),
        "desvio": round(statistics.pstdev(puntajes), 1) if len(puntajes) > 1 else 0.0,
        "saturado": round(sat / len(puntajes), 3),
        "crudo_min": round(min(crudos), 2),
        "crudo_max": round(max(crudos), 2),
        "crudo_media": round(statistics.fmean(crudos), 2),
    }


def _señal(fuera, dentro):
    """Marca los casos a MIRAR. No dictamina circularidad — no puede.

    La primera versión de este archivo devolvía un veredicto "circular" cuando
    el puntaje se aplastaba fuera de muestra y discriminaba dentro. Es un test
    equivocado, y se vio al contrastarlo con los valores crudos: marcó
    `ipc_total`, `litigiosidad_laboral` y `emae_ia`, y en los tres la saturación
    era REAL. La inflación mensual promedio anterior a dic-2023 fue de 6,4%
    (~112% anual) y la litigiosidad crecía al 39% anual: puntuar cerca del piso
    ahí es la banda funcionando, no fallando.

    El defecto es de fondo, no de umbral. Una banda circular y un cambio de
    régimen genuino producen la MISMA firma en la distribución de puntajes, y
    separarlos exige mirar si la realidad subyacente fue de verdad extrema —
    que es justamente lo que ADR-0045 obliga a chequear antes de recalibrar.

    Así que esto marca candidatos y adjunta el rango crudo de cada ventana, que
    es lo que permite decidir. La decisión es de quien lee.
    """
    asimetrica = fuera["saturado"] >= 0.6 and dentro["saturado"] < 0.3
    plana = fuera["desvio"] < 5 and dentro["desvio"] >= 10
    if asimetrica or plana:
        return "mirar", ("se aplasta fuera del período que la calibró — "
                         "comparar los rangos crudos: ¿el período anterior fue "
                         "realmente extremo, o la banda no lo alcanza?")
    return "sin señal", "discrimina en ambas ventanas"


def analizar():
    reg = json.load(open(RAIZ / "output" / "procedencia_anclas.json", encoding="utf-8"))
    cat = {d["indicador"]: d["categoria"]
           for b in reg["por_indice"].values() for d in b["detalle"]}
    indice_de = {d["indicador"]: sig
                 for sig, b in reg["por_indice"].items() for d in b["detalle"]}

    filas, descartados = [], []
    for ind, sig in sorted(indice_de.items()):
        escala = ESCALAS[sig]
        if not escala.puntuable(ind):
            continue
        serie = _serie_indicador(ind)
        fuera_v = [v for ym, v in serie.items() if ym < CORTE]
        dentro_v = [v for ym, v in serie.items() if ym >= CORTE]
        if len(fuera_v) < MIN_PUNTOS:
            descartados.append({"indicador": ind, "n_fuera": len(fuera_v),
                                "motivo": "sin ventana fuera de muestra utilizable"})
            continue

        piso, techo = _extremos(escala, ind)
        fuera = _resumen([escala.puntaje(v, ind) for v in fuera_v], fuera_v, piso, techo)
        dentro = _resumen([escala.puntaje(v, ind) for v in dentro_v], dentro_v, piso, techo)
        if not dentro:
            continue
        señal, motivo = _señal(fuera, dentro)
        filas.append({"indicador": ind, "indice": sig,
                      "procedencia": cat.get(ind, "?"),
                      "fuera_de_muestra": fuera, "dentro_de_muestra": dentro,
                      "señal": señal, "lectura": motivo})

    filas.sort(key=lambda f: (f["señal"] != "mirar", f["indicador"]))
    return {"corte": CORTE, "evaluados": filas, "no_evaluables": descartados}


def main():
    r = analizar()
    print(f"Out-of-sample: puntajes anteriores a {r['corte']} con las bandas de hoy\n")
    print(f"{'indicador':24s} {'fuera: pje/sat (crudo medio)':32s} "
          f"{'dentro: pje/sat (crudo medio)':32s} señal")
    print("-" * 108)
    for f in r["evaluados"]:
        fu, de = f["fuera_de_muestra"], f["dentro_de_muestra"]
        izq = f"{fu['media']:5.1f}/{fu['saturado']:4.0%} ({fu['crudo_media']:8.2f})"
        der = f"{de['media']:5.1f}/{de['saturado']:4.0%} ({de['crudo_media']:8.2f})"
        print(f"{f['indicador']:24s} {izq:32s} {der:32s} {f['señal']}")
    if r["no_evaluables"]:
        print(f"\nSin ventana previa utilizable ({len(r['no_evaluables'])}): "
              + ", ".join(d["indicador"] for d in r["no_evaluables"]))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
