"""
Generador del Informe de Coyuntura — CIGOB
Lee los 5 caches de colectores y produce:
  output/informe.json  — schema v1.0.0 para dev externo
  output/informe.md    — markdown con frontmatter YAML para Drive y reunión

Ejecutar desde projects/informe_coyuntura/: python scripts/generar_informe.py
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

from config import (PESOS_CINTURONES, UMBRALES, BARBARISMO_MAP, fase_mandato,
                    MANDATO_INICIO, estado_de_score, es_tensionado)
# Reutilizan el motor de scoring vigente para recalcular ITCM/ITCG/ITCP desde
# los valores crudos ya persistidos en el caché (sin red) — ver
# _INDICES_PARAMETRICOS más abajo y el ADR que documenta este cambio.
import macro, gestion, politica, itcm, itcg, itcp

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_DIR   = PROJECT_DIR / "output" / "cache"
OUTPUT_DIR  = PROJECT_DIR / "output"

CINTURONES_ESPERADOS = ["macro", "politica", "vida_cotidiana", "gestion"]

SCHEMA_VERSION = "1.2.0"

# Cinturones con índice paramétrico 0-100 (ITCM/ITCG/ITCP): el colector deja
# los VALORES CRUDOS en cache["indicadores"] y, además, el resultado de
# calcular_itc*() que computó AL MOMENTO DEL FETCH. Ese segundo campo queda
# obsoleto si el motor de scoring (itcm.py/itcg.py/itcp.py: bandas, pesos,
# ajustes) cambia sin volver a correr el colector — generar_informe.py antes
# lo copiaba verbatim. Ahora se recalcula acá, con el código VIGENTE, a
# partir de los valores crudos ya persistidos (sin pegarle a ninguna fuente
# externa): mismo patrón que ya usa ITVC en publicar.py (_itvc_indices +
# itvc.calcular_itvc, siempre fresco desde las series persistidas).
_INDICES_PARAMETRICOS = {
    "macro":    ("itcm", macro.calcular_itcm_cinturon,    itcm.tension_de_itcm),
    "gestion":  ("itcg", gestion.calcular_itcg_cinturon,  itcg.tension_de_itcg),
    "politica": ("itcp", politica.calcular_itcp_cinturon, itcp.tension_de_itcp),
}


def _recalcular_indice(nombre: str, indicadores: dict, score_cache: float) -> tuple[float, dict | None]:
    """(score, resultado) recalculados con el código vigente, o el score
    cacheado sin bloque de índice si `nombre` no tiene paramétrica (vida
    cotidiana, espíritu de época) o si no hay ningún valor utilizable."""
    if nombre not in _INDICES_PARAMETRICOS:
        return score_cache, None
    _, calcular, tension_de = _INDICES_PARAMETRICOS[nombre]
    resultado = calcular(indicadores)
    if resultado is None:
        return score_cache, None
    return tension_de(resultado["valor"]), resultado


# La definición vive en config.estado_de_score: es la misma que usa publicar y
# la misma con la que se cuenta la alerta.
_estado = estado_de_score


def load_caches() -> dict[str, dict]:
    caches = {}
    for cinturon in CINTURONES_ESPERADOS:
        path = CACHE_DIR / f"{cinturon}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                caches[cinturon] = json.load(f)
        else:
            print(f"[WARN] generar_informe: cache {cinturon}.json no encontrado. Cinturón ausente.")
    return caches


def calcular_score_global(cinturones_data: dict) -> float:
    """Score global ponderado según PESOS_CINTURONES en config.py."""
    peso_total = 0.0
    score_sum  = 0.0
    for nombre, data in cinturones_data.items():
        peso = PESOS_CINTURONES.get(nombre, 0.0)
        score_sum  += data["score"] * peso
        peso_total += peso
    return round(score_sum / peso_total, 1) if peso_total else 5.0


def detectar_barbarismo(cinturones_data: dict) -> tuple[str | None, bool]:
    """
    Retorna (barbarismo_activo, alerta_multicinturon).
    Regla matusiana: nunca apretar 3 cinturones a la vez.
    barbarismo_activo = cinturón con score más alto que supera umbral de tensión.
    alerta_multicinturon = True si 2+ cinturones están "tensionados", con el
    MISMO criterio que `_estado` — no uno propio: cuando acá decía
    `score >= EN_TENSION_MAX + 1` había una zona muerta entre 6 y 7 (ADR-0195).
    """
    tensionados = [
        (nombre, data["score"])
        for nombre, data in cinturones_data.items()
        if es_tensionado(data["score"])
    ]
    en_tension_o_mas = [
        (nombre, data["score"])
        for nombre, data in cinturones_data.items()
        if data["score"] > UMBRALES["ESTABLE_MAX"]
    ]

    alerta_multicinturon = len(tensionados) >= 2

    if not en_tension_o_mas:
        return None, alerta_multicinturon

    dominante = max(en_tension_o_mas, key=lambda x: x[1])[0]
    barbarismo = BARBARISMO_MAP.get(dominante)
    return barbarismo, alerta_multicinturon


def construir_informe(caches: dict) -> dict:
    """Construye el payload JSON v1.0.0 a partir de los caches."""
    # `.astimezone()` y no `.now()` a secas: este sello es la CLAVE DE CORRIDA
    # del archivo histórico en BigQuery, y un timestamp sin offset lo lee como
    # UTC. En la CI eso salía bien de casualidad (el runner corre en UTC); una
    # corrida manual desde una máquina en ART quedaba 3 horas adelantada. Ver
    # ADR-0203, que mide el daño: 3 de 11 corridas archivadas.
    #
    # `.astimezone()` sella con el offset de la máquina —`-03:00` acá, `+00:00`
    # en el runner— sin hardcodear zona. El reloj de pared no cambia, así que
    # los consumidores que cortan el string (`[:10]`, `[:19]`, `.slice(0,10)`)
    # siguen viendo exactamente lo mismo.
    now = datetime.now().astimezone()
    period = now.strftime("%Y-%m")

    cinturones_data: dict = {}
    flags: list = []

    for nombre in CINTURONES_ESPERADOS:
        if nombre not in caches:
            flags.append(f"cache_ausente:{nombre}")
            continue

        cache = caches[nombre]
        indicadores = cache.get("indicadores", {})
        score, resultado_indice = _recalcular_indice(nombre, indicadores, cache.get("score", 5.0))

        # Detectar indicadores desactualizados
        desactualizados = [
            ind for ind, vals in indicadores.items()
            if vals.get("desactualizado", False)
        ]
        if desactualizados:
            flags.append(f"desactualizado:{nombre}:{','.join(desactualizados)}")

        cinturones_data[nombre] = {
            "score":              score,
            "estado":             _estado(score),
            "barbarismo_riesgo":  BARBARISMO_MAP.get(nombre),
            "indicadores":        indicadores,
            "alerta":             None,
        }
        if resultado_indice:
            clave = _INDICES_PARAMETRICOS[nombre][0]
            cinturones_data[nombre][clave] = resultado_indice

    barbarismo_activo, alerta_multicinturon = detectar_barbarismo(cinturones_data)

    if alerta_multicinturon:
        for nombre in cinturones_data:
            if cinturones_data[nombre]["score"] >= UMBRALES["EN_TENSION_MAX"] + 1:
                cinturones_data[nombre]["alerta"] = "multicinturon"

    score_global = calcular_score_global(cinturones_data)

    return {
        "schema_version":       SCHEMA_VERSION,
        "generated_at":         now.isoformat(),
        "period":               period,
        "score_global":         score_global,
        "ponderacion": {
            "fase":           fase_mandato(),
            "mandato_inicio": MANDATO_INICIO.isoformat(),
            "pesos":          PESOS_CINTURONES,
        },
        "cinturones":           cinturones_data,
        "barbarismo_activo":    barbarismo_activo,
        "alerta_multicinturon": alerta_multicinturon,
        "flags":                flags,
    }


def escribir_json(informe: dict) -> None:
    path = OUTPUT_DIR / "informe.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2, default=str)
    print(f"[OK] informe.json → {path}")


def _emoji_estado(estado: str) -> str:
    return {"estable": "🟢", "en_tension": "🟡", "tensionado": "🔴"}.get(estado, "⚪")


def escribir_md(informe: dict) -> None:
    """Genera informe.md con frontmatter YAML y sección por cinturón."""
    path = OUTPUT_DIR / "informe.md"
    period     = informe["period"]
    generated  = informe["generated_at"][:19].replace("T", " ")
    score_g    = informe["score_global"]
    barbarismo = informe["barbarismo_activo"] or "ninguno"
    alerta     = informe["alerta_multicinturon"]
    flags      = informe["flags"]

    lines: list[str] = []

    # Frontmatter YAML
    lines.append("---")
    lines.append(f"periodo: \"{period}\"")
    lines.append(f"generado: \"{generated}\"")
    lines.append(f"score_global: {score_g}")
    lines.append(f"barbarismo_activo: \"{barbarismo}\"")
    lines.append(f"alerta_multicinturon: {str(alerta).lower()}")
    lines.append(f"schema_version: \"{SCHEMA_VERSION}\"")
    lines.append("---")
    lines.append("")

    lines.append(f"# Informe de Coyuntura — {period}")
    lines.append("")
    lines.append(f"**Score global:** {score_g}/10  |  **Riesgo dominante:** {barbarismo}")

    if alerta:
        lines.append("")
        lines.append("> **ALERTA MATUSIANA:** Dos o más cinturones tensionados simultáneamente.")
        lines.append("> Riesgo de decisión desequilibrada. No apretar tres cinturones a la vez.")

    lines.append("")
    lines.append("## Cinturones")
    lines.append("")

    for nombre, data in informe["cinturones"].items():
        estado   = data["estado"]
        score    = data["score"]
        barb     = data["barbarismo_riesgo"] or "—"
        emoji    = _emoji_estado(estado)
        lines.append(f"### {emoji} {nombre.replace('_', ' ').title()} — score {score}/10 ({estado})")
        lines.append(f"*Riesgo de barbarismo: {barb}*")
        lines.append("")
        lines.append("| Indicador | Valor | Unidad | Fecha | Estado |")
        lines.append("|---|---|---|---|---|")
        for ind, vals in data["indicadores"].items():
            valor       = vals.get("valor", "N/A")
            unidad      = vals.get("unidad", "")
            fecha       = vals.get("fecha_dato", "")
            desact      = "⚠ cache" if vals.get("desactualizado") else "fresco"
            valor_extra = vals.get("valor_brecha_vs_ipc")
            valor_str   = str(valor)
            if valor_extra is not None:
                valor_str += f" (brecha {valor_extra:+.2f}pp)"
            lines.append(f"| {ind} | {valor_str} | {unidad} | {fecha} | {desact} |")
        lines.append("")

    if flags:
        lines.append("## Advertencias")
        lines.append("")
        for flag in flags:
            lines.append(f"- `{flag}`")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generado por CIGOB — {generated} — schema {SCHEMA_VERSION}*")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] informe.md   → {path}")


def main() -> None:
    caches  = load_caches()
    if not caches:
        print("[ERROR] Sin caches disponibles. Correr primero los colectores.")
        sys.exit(2)

    informe = construir_informe(caches)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    escribir_json(informe)
    escribir_md(informe)

    total = len(CINTURONES_ESPERADOS)
    found = len(caches)
    score = informe["score_global"]
    barb  = informe["barbarismo_activo"] or "ninguno"
    alrt  = informe["alerta_multicinturon"]
    print(f"[OK] informe: score_global={score} cinturones={found}/{total} barbarismo={barb} alerta={alrt}")

    sys.exit(0 if found == total else 1)


if __name__ == "__main__":
    main()
