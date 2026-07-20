"""
Monitor Cinturón Vida Cotidiana — CIGOB
Colecta todos los indicadores automatizables y guarda en data/.

Uso:
    python main.py              # Corre todos los collectors
    python main.py --check      # Solo muestra estado de fuentes manuales
    python main.py --search IPC # Busca series en catálogo INDEC
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

DATA_DIR = Path(__file__).parent / "data"


def guardar(resultados: dict) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = DATA_DIR / f"vida_cotidiana_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Guardado en: %s", path)
    return path


def imprimir_resumen(resultados: dict) -> None:
    print("\n" + "=" * 60)
    print("  MONITOR VIDA COTIDIANA — CIGOB")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    for fuente, datos in resultados.items():
        if fuente == "metadata" or not datos:
            continue
        print(f"\n  [{fuente.upper()}]")
        for indicador, vals in datos.items():
            if not isinstance(vals, dict):
                continue
            valor = vals.get("valor")
            fecha = vals.get("fecha", "")
            var = vals.get("variacion_mensual_pct")
            # Fallbacks para estructuras no estandar
            if valor is None:
                for alt in ("anio", "total_hechos", "interes_relativo", "datasets_disponibles", "size_mb"):
                    if alt in vals:
                        valor = vals[alt]
                        break
            var_str = f" ({var:+.2f}% m/m)" if var is not None else ""
            print(f"    {indicador}: {valor}{var_str} [{fecha}]")

    print("\n" + "=" * 60 + "\n")


def run_all() -> dict:
    from collectors.indec_series import fetch_indec
    from collectors.bcra import fetch_bcra
    from collectors.utdt_icc import fetch_icc
    from collectors.cafam import fetch_cafam
    from collectors.ciccra import fetch_ciccra
    from collectors.snic import fetch_snic
    from collectors.salud import fetch_salud
    from collectors.trends import fetch_trends
    from collectors.utdt_nowcast_pobreza import fetch_nowcast_pobreza

    logger.info("Iniciando recolección — 8 fuentes...")

    fuentes_automatizadas = [
        "indec_series (IPC, CBT, salarios, empleo, RIPTE, ISAC, EMAE, IPI, faena, acero)",
        "bcra (creditos privados, tarjeta, personales, hipotecarios, BADLAR)",
        "utdt_icc (Indice de Confianza del Consumidor)",
        "cafam (patentamiento motos por provincia)",
        "ciccra (consumo carne vacuna per capita — PDF mensual)",
        "snic (estadisticas criminales nacionales + CABA)",
        "salud (datasets DEIS/SNVS via datos.salud.gob.ar CKAN)",
        "trends (interes Google: inflacion, precios, inseguridad, trabajo)",
    ]

    resultados = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "fuentes_automatizadas": fuentes_automatizadas,
        },
        "indec":  fetch_indec(),
        "bcra":   fetch_bcra(),
        "utdt":   fetch_icc(),
        "pobreza": fetch_nowcast_pobreza(),
        "cafam":  fetch_cafam(),
        "ciccra": fetch_ciccra(),
        "snic":   fetch_snic(),
        "salud":  fetch_salud(),
        "trends": fetch_trends(),
    }

    imprimir_resumen(resultados)
    path = guardar(resultados)
    print(f"Datos guardados: {path}\n")
    return resultados


def main():
    parser = argparse.ArgumentParser(description="Monitor Vida Cotidiana CIGOB")
    parser.add_argument("--check", action="store_true", help="Muestra estado de fuentes manuales")
    parser.add_argument("--search", type=str, help="Busca una serie en el catálogo INDEC")
    args = parser.parse_args()

    if args.check:
        from collectors.manual import get_estado_fuentes
        get_estado_fuentes()
        return

    if args.search:
        from collectors.indec_series import search_serie
        resultados = search_serie(args.search, limit=10)
        print(f"\nSeries encontradas para '{args.search}':\n")
        for s in resultados:
            print(f"  ID: {s['id']}")
            print(f"     {s['description']} [{s['frequency']}]\n")
        return

    run_all()


if __name__ == "__main__":
    main()
