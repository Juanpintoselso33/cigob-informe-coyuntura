"""
Colector Cinturón Espíritu de Época — CIGOB
Marco: "Marco Conceptual del Informe de Coyuntura" (CIGOB, mayo 2026), que
amplía los cinturones de Matus con la sintonía emocional del gobierno con
los sentimientos colectivos (política de las emociones, redes sociales).

v1 PROVISIONAL — único indicador PUNTUABLE (ADR-0049):
  - indice_intencion_migratoria ← data/vida/intencion_migratoria_serie.json (Google
    Trends, ADR-0035; store mensual compartido con descargar_series.py, gateado
    por frescura — no se re-fetchea si el store ya tiene el mes en curso)

Los tres proxies iniciales del cinturón se siguen relevando y cacheando como
seguimiento interno, pero NO puntúan ni se publican en el tablero
(publicar.ESPIRITU_OCULTOS, mismo criterio que ADR-0022/0048) — son lecturas
duplicadas de cards que ya viven en otros cinturones:
  - icc_utdt                    ← último scripts/vida_cotidiana/data/vida_cotidiana_*.json
  - sentimiento_digital         ← ídem (Google Trends; busca hacia atrás si vino null)
  - clima_electoral             ← output/cache/politica.json (votometro_ventaja_lla)

`apatia_electoral` (voto en blanco/nulo + ausentismo) queda pendiente: el
Votómetro aún no publica blanco/nulo por encuesta.

Ejecutar desde projects/informe_coyuntura/: python scripts/espiritu_epoca.py
(después de vida_cotidiana/main.py y politica.py, de cuyos outputs lee).
"""
import sys
import glob
import json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_PATH  = PROJECT_DIR / "output" / "cache" / "espiritu_epoca.json"
VIDA_GLOB   = str(SCRIPT_DIR / "vida_cotidiana" / "data" / "vida_cotidiana_*.json")
POLITICA_CACHE = PROJECT_DIR / "output" / "cache" / "politica.json"

CINTURON = "espiritu_epoca"
INDICADORES_ESPERADOS = [
    "icc_utdt", "sentimiento_digital", "clima_electoral", "indice_intencion_migratoria",
]
INTENCION_MIGRATORIA_STORE = PROJECT_DIR / "data" / "vida" / "intencion_migratoria_serie.json"


def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _warn(indicador: str, msg) -> None:
    print(f"[WARN] {CINTURON}.{indicador}: {msg}. Usando cache.")


def _vida_files_desc() -> list[str]:
    return sorted(glob.glob(VIDA_GLOB), reverse=True)


def fetch_icc_utdt() -> dict | None:
    """Confianza del consumidor (UTDT) desde el último JSON de vida cotidiana."""
    try:
        files = _vida_files_desc()
        raw = json.loads(Path(files[0]).read_text(encoding="utf-8"))
        icc = raw["utdt"]["icc_utdt"]
        return {
            "valor": round(float(icc["valor"]), 1),
            "unidad": "índice",
            "fuente": "UTDT — Índice de Confianza del Consumidor",
            "fecha_dato": icc.get("fecha"),
            "desactualizado": False,
        }
    except Exception as e:
        _warn("icc_utdt", e)
        return None


def fetch_sentimiento_digital() -> dict | None:
    """Interés en términos de malestar (Google Trends, promedio 0-100). El
    colector de vida suele caer por rate-limit: buscar hacia atrás el último
    archivo con dato y marcar desactualizado si no es el más reciente."""
    try:
        files = _vida_files_desc()
        for i, path in enumerate(files):
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            interes = (raw.get("trends", {})
                          .get("sentimiento_digital", {})
                          .get("interes_relativo"))
            if interes:
                fecha = raw.get("metadata", {}).get("timestamp", "")[:10]
                return {
                    "valor": round(sum(interes.values()) / len(interes), 1),
                    "unidad": "interés 0–100",
                    "fuente": "Google Trends (inflación, precios, inseguridad, trabajo)",
                    "fecha_dato": fecha,
                    "desactualizado": i > 0,
                }
        raise ValueError("ningún vida_cotidiana_*.json tiene interes_relativo")
    except Exception as e:
        _warn("sentimiento_digital", e)
        return None


def fetch_clima_electoral() -> dict | None:
    """Ventaja LLA−PJ del Votómetro (proxy de adhesión al oficialismo), leída
    del cache del cinturón Política (ya ponderada por calidad y recencia)."""
    try:
        pol = json.loads(POLITICA_CACHE.read_text(encoding="utf-8"))
        vot = pol["indicadores"]["votometro_ventaja_lla"]
        return {
            "valor": vot["valor"],
            "unidad": "pp (LLA − PJ)",
            "fuente": "Votómetro CIGOB",
            "fecha_dato": vot.get("fecha_dato"),
            "desactualizado": bool(vot.get("desactualizado", False)),
        }
    except Exception as e:
        _warn("clima_electoral", e)
        return None


def _contexto_duro_componente_b() -> dict:
    """Último valor de cada una de las 6 fuentes de datos duros de migración
    real (ADR-0035, Componente B) -- cruce de validación del Componente A,
    NUNCA puntúa. Si falla entero, devuelve {} (Componente A sigue solo,
    igual que antes de que existiera el Componente B)."""
    try:
        import descargar_series as _ds
        store = _ds.fetch_componente_b_store()
    except Exception as e:
        _warn("indice_intencion_migratoria.contexto_duro", e)
        return {}
    contexto = {}
    for clave, serie in store.items():
        if clave == "_meta" or not isinstance(serie, dict):
            continue
        puntos = serie.get("mensual") or serie.get("anual") or {}
        if puntos:
            ultimo_periodo = sorted(puntos.keys())[-1]
            contexto[clave] = {"periodo": ultimo_periodo, "valor": puntos[ultimo_periodo]}
    return contexto


def fetch_indice_intencion_migratoria() -> dict | None:
    """Intención expresada de emigrar (Google Trends, ADR-0035) — único proxy
    puntuable de las 5 tandas del Componente A. Store mensual COMPARTIDO con
    descargar_series.py: se actualiza a lo sumo una vez por mes (el que corra
    primero esa noche hace el fetch real si hace falta; el otro reutiliza el
    store ya fresco). El mes en curso siempre queda excluido (incompleto)."""
    try:
        sys.path.insert(0, str(SCRIPT_DIR / "vida_cotidiana"))
        sys.path.insert(0, str(SCRIPT_DIR / "vida_cotidiana" / "collectors"))
        import trends as _trends

        store = _trends.fetch_intencion_migratoria_store(INTENCION_MIGRATORIA_STORE)
        mensual = store.get("mensual", {})
        if not mensual:
            raise ValueError("store de intencion_migratoria sin datos mensuales")

        ultimo_mes = sorted(mensual.keys())[-1]
        actualizado = store.get("_meta", {}).get("actualizado", "")
        mes_actual = datetime.today().strftime("%Y-%m")
        return {
            "valor": mensual[ultimo_mes],
            "unidad": "interés 0–100 (canasta mensual)",
            "fuente": "Google Trends (canasta intención migratoria, ventana fija 2021→)",
            "fecha_dato": f"{ultimo_mes}-01",
            "desactualizado": actualizado[:7] != mes_actual,
            "contexto_duro": _contexto_duro_componente_b(),
        }
    except Exception as e:
        _warn("indice_intencion_migratoria", e)
        return None


# ── Scoring ───────────────────────────────────────────────────────────────────

def _clamp10(x: float) -> float:
    return round(max(0.0, min(10.0, x)), 1)


def calcular_score(indicadores: dict) -> float:
    """
    Score 0-10: mayor = mayor desconexión con el humor social.
    Único puntuable (ADR-0049; v1 provisional, sin paramétrica CIGOB aún):

    indice_intencion_migratoria (interés 0-100): 0 → 0 | 50 → 5 | 100 → 10

    Los otros 3 proxies del cache (icc_utdt, sentimiento_digital,
    clima_electoral) son seguimiento interno: no entran al score.
    Sin dato de intención migratoria → 5.0 neutral.
    """
    intencion_migratoria = indicadores.get("indice_intencion_migratoria", {}).get("valor")
    if intencion_migratoria is not None:
        return _clamp10(float(intencion_migratoria) / 10.0)
    return 5.0


def main() -> None:
    cache_anterior         = load_cache()
    indicadores_anteriores = cache_anterior.get("indicadores", {})

    frescos: dict = {}
    frescos_count = 0

    for nombre, fetcher in [
        ("icc_utdt",                    fetch_icc_utdt),
        ("sentimiento_digital",         fetch_sentimiento_digital),
        ("clima_electoral",             fetch_clima_electoral),
        ("indice_intencion_migratoria", fetch_indice_intencion_migratoria),
    ]:
        resultado = fetcher()
        if resultado is not None and resultado.get("valor") is not None:
            frescos[nombre] = resultado
            frescos_count  += 1
        elif nombre in indicadores_anteriores:
            frescos[nombre] = {**indicadores_anteriores[nombre], "desactualizado": True}

    score   = calcular_score(frescos)
    payload = {
        "cinturon":     CINTURON,
        "generated_at": datetime.now().isoformat(),
        "score":        score,
        "indicadores":  frescos,
    }

    if frescos:
        save_cache(payload)
        total = len(INDICADORES_ESPERADOS)
        print(f"[OK] {CINTURON}: score={score} frescos={frescos_count}/{total}")

    if frescos_count == len(INDICADORES_ESPERADOS):
        sys.exit(0)
    elif frescos_count > 0:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
