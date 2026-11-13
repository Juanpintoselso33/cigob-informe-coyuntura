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
    # Medio para arriba, como la web (Intl.NumberFormat): con el formato de
    # Python un peso de 11,25 % salía 11,2 en la ficha y 11,3 en la tarjeta.
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
    s = f"{q:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    if recortar and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s.replace("-", "−")  # menos tipográfico, no guión


# ── Cortes del semáforo, en las tres escalas que muestran las fichas ─────────
# Salen de `semaforo_cortes` del snapshot (parametrica.CORTES_SEMAFORO), no se
# escriben acá: hasta el 13-nov-2026 las fichas tenían 4/6/8, 60/40/20 y
# 105/95/85 a mano y siguieron diciéndolos después de ADR-0427 (2,5/5/7,5).
# Las fórmulas son las publicadas: puntaje = 100 − 10 × tensión; índice
# base 100 = 100 − (tensión − 5) × 5.

def topes_de_tension(cortes: list) -> list:
    """Los tres cortes finitos de `semaforo_cortes`, de menor a mayor tensión."""
    return [float(c["hasta"]) for c in cortes if c.get("hasta") is not None]


def puntaje_de_tension(t: float) -> float:
    return 100.0 - 10.0 * float(t)


def indice_base100_de_tension(t: float) -> float:
    return 100.0 - (float(t) - 5.0) * 5.0


def tramos_en_escala(cortes: list, a_escala) -> list:
    """[(texto, color)] de mejor a peor en una escala donde más es mejor:
    «75 o más», «de 50 a 75», «de 25 a 50», «menos de 25». El borde va del
    lado del color mejor (`tension <= tope`): 75 es verde, 50 amarillo."""
    colores = [c["color"] for c in cortes]
    v = [a_escala(t) for t in topes_de_tension(cortes)]
    n = lambda x: coma(x, 1)
    out = [(f"{n(v[0])} o más", colores[0])]
    out += [(f"de {n(v[i + 1])} a {n(v[i])}", colores[i + 1]) for i in range(len(v) - 1)]
    out.append((f"menos de {n(v[-1])}", colores[-1]))
    return out


def umbrales_base100(cortes: list) -> tuple:
    """((112,5, "verde"), (100, "amarillo"), (87,5, "naranja")): desde qué
    índice base 100 rige cada color; debajo del último, el color siguiente."""
    return tuple((indice_base100_de_tension(t), c["color"])
                 for t, c in zip(topes_de_tension(cortes), cortes))


def tramos_de_tension(cortes: list) -> list:
    """«hasta 2,5», «más de 2,5 y hasta 5», …, «más de 7,5»."""
    t = [coma(x, 1) for x in topes_de_tension(cortes)]
    return ([f"hasta {t[0]}"]
            + [f"más de {t[i]} y hasta {t[i + 1]}" for i in range(len(t) - 1)]
            + [f"más de {t[-1]}"])


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
