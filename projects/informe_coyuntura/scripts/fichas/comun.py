"""Lo que comparten el generador de fichas, su verificador y su guarda.

Existe por una razón concreta: el formato de los números. `generar.py` imprime
«83,2» y «5,6 %» con una función `coma()` propia, `verificar.py` tenía una copia
con otra firma, y la guarda de `tests/test_fichas_generadas_al_dia.py` habría
sido la tercera. Tres copias del mismo formateador son tres oportunidades de que
el verificador busque un texto que el generador ya no escribe — y un verificador
que no encuentra lo que busca no falla: pasa, porque compara un valor stale
contra un texto que tampoco existe.

Acá viven además los dos mapas que definen el alcance del artefacto: qué
cinturones tienen ficha y cómo se llama el archivo de cada uno.
"""
import re
from pathlib import Path

# scripts/fichas/comun.py → projects/informe_coyuntura/
RAIZ = Path(__file__).resolve().parents[2]
SALIDA_DIR = RAIZ / "output" / "fichas"

COLOR = {"verde": "VERDE", "amarillo": "AMARILLO", "naranja": "NARANJA", "rojo": "ROJO"}
ORDEN_COLOR = ["verde", "amarillo", "naranja", "rojo"]

# Los cuatro cinturones que publican ficha. Son los mismos cuatro del snapshot
# desde ADR-0205; `tests/test_fichas_generadas_al_dia.py` cruza este mapa contra
# `web/src/data/informe.json` para que agregar o retirar un cinturón no deje el
# artefacto a medias en silencio.
CINTURONES = {
    "macro": ("ITCM", "Macroeconomía"),
    "politica": ("ITCP", "Política"),
    "gestion": ("ITCG", "Gestión"),
    "vida_cotidiana": ("ITCIS", "Impacto social"),
}

CLAVES_INDICE = ("itcm", "itcg", "itcp", "itvc")

CADENA = r'"((?:[^"\\]|\\.)*)"'


def ruta_md(cint: str) -> Path:
    return SALIDA_DIR / f"fichas-{cint}.md"


def coma(x, dec=2, recortar=True):
    """Número en formato local. `recortar` saca los decimales que sobran, que
    es lo que se quiere en prosa; en una columna de tabla no, porque deja
    "71" al lado de "67,1" y la columna se lee torcida."""
    if x is None:
        return "—"
    s = f"{float(x):,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    if recortar and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s.replace("-", "−")  # menos tipográfico, no guión


def labels(datos_ts: str | None = None) -> dict:
    """Los rótulos legibles que usa la web, del mapa LABELS de `datos.ts`."""
    if datos_ts is None:
        datos_ts = (RAIZ / "web/src/lib/datos.ts").read_text(encoding="utf-8")
    m = re.search(r"export const LABELS[^{]*\{(.*?)\n\};", datos_ts, re.S)
    return dict(re.findall(r"(\w+):\s*" + CADENA, m.group(1))) if m else {}


def clave_indice(cinturon: dict) -> str | None:
    """Bajo qué clave publica el snapshot el índice de este cinturón, si tiene
    uno."""
    return next((k for k in CLAVES_INDICE if k in cinturon), None)
