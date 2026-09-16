"""Genera una vista autónoma dentro del experimento, fuera de web/ y CI."""
import copy
import json
from pathlib import Path
from motor import calcular

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def construir():
    registro = json.loads((ROOT / "docs/producto/piloto-compromisos-2026-09-10.json").read_text())
    fuentes = {s["id"]: s["url"] for s in registro["fuentes"]}
    real = [{"id": "PE-159-2025", "nombre": "Modernización laboral", "peso": 1,
             "prioridad_desde": "2025-12-11", "verificado_hasta": "2026-09-08",
             "fuente_prioridad": fuentes["pen_comunicado_122"],
             "eventos": [
                 {"fecha": "2025-12-11", "estado": "presentado", "fuente": fuentes["pen_comunicado_122"]},
                 {"fecha": "2026-02-27", "estado": "sancionado", "fuente": fuentes["ley_27802_ficha"]}]}]
    sint = []
    for n, estado in enumerate(["sancionado", "sancionado", "media_sancion", "retirado"]):
        sint.append({"id": f"sim-{n}", "nombre": f"Iniciativa ficticia {n+1}", "peso": 1,
                     "prioridad_desde": "2026-01-01", "verificado_hasta": "2026-09-08",
                     "fuente_prioridad": "Escenario simulado",
                     "eventos": [{"fecha": "2026-02-01", "estado": estado, "fuente": "Escenario simulado"}]})
    incompleto = copy.deepcopy(sint)
    incompleto[0]["verificado_hasta"] = "2026-08-01"
    incompleto[0]["eventos"][0]["estado"] = "presentado"
    sesgo = copy.deepcopy(sint[:2])
    ponderado = copy.deepcopy(sint); ponderado[0]["peso"] = 3
    casos = [
        ("real", "Reforma documentada", "Una iniciativa seleccionada para probar el vínculo. Cartera incompleta: no representa toda la agenda.", real),
        ("base", "Simulación: cartera completa", "Cuatro iniciativas ficticias; dos sancionadas, una con media sanción y una retirada. Igual peso.", sint),
        ("faltantes", "Simulación: falta una verificación", "Falta el documento de sanción de una iniciativa y su último estado no está actualizado. Permanece en el denominador.", incompleto),
        ("seleccion", "Simulación: seleccionar sólo éxitos", "Se omiten las dos iniciativas sin sanción. El porcentaje sube por selección, no por un nuevo logro.", sesgo),
        ("pesos", "Simulación: cambiar un peso", "Una sancionada pesa tres y las otras uno. Es sensibilidad ilustrativa, no una ponderación adoptada.", ponderado),
    ]
    fechas = ["2025-12-10", "2026-02-26", "2026-02-27", "2026-09-08", "2026-09-10"]
    resultados = [{"id": id, "nombre": nombre, "nota": nota, "simulado": id != "real",
                   "cortes": [calcular(cartera, dia) for dia in fechas]} for id, nombre, nota, cartera in casos]
    paquete = {"fechas": fechas, "casos": resultados, "snapshot": registro["snapshot"],
               "baseline": {"corte": "2026-09-08", "porcentaje": 14.3,
                            "descripcion": "2 de 14 proyectos ingresados entre 8-sep-2024 y 8-sep-2025. La reforma del piloto queda fuera."}}
    target = HERE / "vista"; target.mkdir(exist_ok=True)
    (target / "resultados.json").write_text(json.dumps(paquete, ensure_ascii=False, indent=2) + "\n")
    (target / "index.html").write_text((HERE / "plantilla.html").read_text())
    print(f"Vista generada: {target}/index.html; {len(casos)*len(fechas)} escenarios/cortes")


if __name__ == "__main__":
    construir()
