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


def _seguro(fn, nombre):
    """Corre un colector y devuelve None si falla, en vez de tumbar la corrida.

    El resto de las fuentes de este cinturón no tienen por qué caerse porque
    una cambió de formato: el pipeline ya sabe publicar con lo que hay y marcar
    lo que falta (exit code 1 = mixto fresco/cache)."""
    try:
        return fn()
    except Exception as e:
        logger.error("colector %s falló: %s", nombre, e)
        return None


def run_all() -> dict:
    from collectors.indec_series import fetch_indec
    from collectors.bcra import fetch_bcra
    from collectors.utdt_icc import fetch_icc
    from collectors.cafam import fetch_cafam
    from collectors.dnrpa_autos import fetch_patentamiento_autos
    from collectors.ciccra import fetch_ciccra
    from collectors.consumo_carnes import fetch_consumo_carnes
    from collectors.srt_empleadores import fetch_empleadores_pyme
    from collectors.trabajo_independiente import fetch_trabajo_independiente

    def _empleadores_sin_serie():
        """La card sólo necesita el último mes. La serie completa (359
        puntos) la baja `descargar_series.py` del mismo colector, así que
        guardarla acá la duplicaría en un archivo versionado."""
        d = fetch_empleadores_pyme()
        return {k: v for k, v in d.items() if not k.startswith('serie_')}

    def _independiente_sin_serie():
        d = fetch_trabajo_independiente()
        return {k: v for k, v in d.items() if k != 'serie'}

    def _autos_sin_serie():
        """Mismo criterio que los dos de arriba: la card sólo necesita el
        último mes y la serie completa la baja `descargar_series.py` del
        mismo colector."""
        d = fetch_patentamiento_autos()
        return {k: v for k, v in d.items() if k != 'serie'}
    from collectors.snic import fetch_snic
    from collectors.salud import fetch_salud
    from collectors.trends import fetch_trends
    from collectors.utdt_nowcast_pobreza import fetch_nowcast_pobreza

    logger.info("Iniciando recolección — 12 fuentes...")

    fuentes_automatizadas = [
        "indec_series (IPC, CBT, salarios, empleo, RIPTE, ISAC, EMAE, IPI, faena, acero)",
        "bcra (creditos privados, tarjeta, personales, hipotecarios, BADLAR)",
        "utdt_icc (Indice de Confianza del Consumidor)",
        "cafam (patentamiento motos por provincia)",
        "dnrpa (patentamiento autos: inscripciones iniciales por jurisdiccion)",
        "ciccra (consumo carne vacuna per capita — PDF mensual)",
        "consumo_carnes (total vacuna+aviar+porcina per capita — tablero SAGYP)",
        "srt (empleadores con cobertura de ART por tamano de nomina)",
        "sipa (autonomos y monotributo sobre el empleo registrado)",
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
        # El espejo de las motos (ADR-0223). Falla suave: el recurso del
        # catálogo de la DNRPA se descubre por nombre y el colector levanta
        # excepción ante cualquier cambio de forma — que reviente no puede
        # tumbar al resto del cinturón.
        "dnrpa_autos": _seguro(_autos_sin_serie, "dnrpa_autos"),
        "ciccra": fetch_ciccra(),
        # Componentes B y C de la ficha de proteína animal: sin el total, una
        # caída de la vacuna se lee como empobrecimiento cuando puede ser
        # sustitución hacia pollo o cerdo. Falla suave: si el PDF de SAGYP
        # cambia de forma, el parser levanta y este colector queda en None
        # sin tumbar al resto del cinturón.
        "consumo_carnes": _seguro(fetch_consumo_carnes, "consumo_carnes"),
        # Cierre neto de PyMEs (ADR-0218): cuando una PyME cierra o despide a
        # toda su nomina, el contrato con la ART se rescinde casi en el acto.
        # Falla suave como el de carnes: el XLSX de la SRT es pesado y su
        # formato puede cambiar; que se caiga no puede tumbar al cinturon.
        "empleadores_pyme": _seguro(_empleadores_sin_serie, "empleadores_pyme"),
        # La contracara del cierre de PyMEs (ADR-0219): si las empresas que
        # cierran reaparecen como gente facturando por su cuenta, es
        # reconfiguracion; si no reaparecen, es destruccion.
        "trabajo_independiente": _seguro(_independiente_sin_serie, "trabajo_independiente"),
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
