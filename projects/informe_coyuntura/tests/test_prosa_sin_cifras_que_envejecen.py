# -*- coding: utf-8 -*-
"""La prosa de fichas, descripciones y fórmulas no copia cifras que envejecen.

EL PROBLEMA. La página de cada ficha (`pages/metodologia/[id].astro`) ya lee del
snapshot, en cada build, el valor del indicador, su puntaje y sus pesos. Cuando
la prosa además los escribe a mano —«pesa 8,5 % del índice», «el último dato es
46,75 kg», «superávit de trece mil millones»—, esa copia queda vieja la próxima
vez que cambia el dato o el peso, y nada falla. La auditoría del 28-oct-2026
encontró decenas: pesos de antes de ADR-0368, cifras de mayo en dotación, la
cuenta corriente de hace dos trimestres. `test_fichas_pesos.py` cruzaba sólo la
forma canónica «N% interno · M% del ÍNDICE»; cualquier otra redacción pasaba.

LA REGLA (pedido de Juan, 28-oct-2026: «no debería haber cifras que queden
desactualizadas, es una invitación a que pase esto»):

1. Ningún peso en la prosa. La página ya lo muestra.
2. Ninguna cifra que sea un valor del propio indicador (el de hoy o uno de su
   serie) sin decir de qué fecha es. Un hecho fechado («en 2024 cayó 85 %») no
   envejece; un dato sin fecha, sí.

Quedan afuera, a propósito: el changelog (`cambios`), las tablas de anclas
(`bandas`, `puntos`, renglones con «→», que cruza `test_fichas_bandas.py`
contra el motor), las fórmulas LaTeX y la `fuente` (ids de series, números de
ley). Si una frase necesita de verdad una cifra así, se suma a `ACEPTADAS` con
el motivo, como en `test_texto_publico_no_caduca.py`.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LIB = RAIZ / "web" / "src" / "lib"
ARCHIVOS = ("fichas.ts", "descripciones.ts", "formulas.ts")
CAMPOS_EXCLUIDOS = {"cambios", "bandas", "puntos", "anclas", "latex", "fuente"}

CADENA = re.compile(r'"((?:[^"\\]|\\.){12,}?)"')
PESO = re.compile(
    r"\bpesa(?:ba|n)?\s+(?:un\s+|el\s+)?\d[\d,.]*\s?%"
    r"|\d[\d,.]*\s?%\s+(?:del\s+(?:índice|indice|total|cinturón|ITVC|ITCIS|ITCP|ITCG|ITCM)"
    r"|interno|de\s+la\s+dimensión)",
    re.I)
NUMERO = re.compile(r"(?<![\w.,])[−-]?\d{1,3}(?:\.\d{3})*,\d+")
FECHADA = re.compile(
    r"\b(?:19|20)\d{2}\b|semestre|trimestre|\b(?:ene|feb|mar|abr|may|jun|jul|ago|sep|"
    r"set|oct|nov|dic)[a-z]*\.?\b", re.I)

# (archivo, clave, campo): motivo. Vacío es el estado deseado.
ACEPTADAS: dict = {
    ("fichas.ts", "tasa_homicidios", "incidenciaTexto"):
        "el 4,32 es la tasa de 2023 que explica por qué ADR-0327 corrigió el ancla "
        "(«anclaba contra el propio 2023»): es un hecho fechado, no el dato vigente",
}


def _valores_del_indicador() -> dict:
    informe = json.loads((RAIZ / "web/src/data/informe.json").read_text(encoding="utf-8-sig"))
    series = json.loads((RAIZ / "web/src/data/series.json").read_text(encoding="utf-8-sig"))
    out = {}
    for cin in informe["cinturones"].values():
        for k, v in (cin.get("indicadores") or {}).items():
            xs = set()
            s = series.get(k)
            for p in s if isinstance(s, list) else []:
                if isinstance(p, dict) and isinstance(p.get("valor"), (int, float)):
                    xs.add(round(p["valor"], 2))
            if isinstance(v.get("valor"), (int, float)):
                xs.add(round(v["valor"], 2))
            out[k] = xs
    return out


def _cadenas():
    """(archivo, clave, campo, texto) de toda cadena de prosa fuera de los
    campos excluidos."""
    for nombre in ARCHIVOS:
        clave = campo = None
        for linea in (LIB / nombre).read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^  (\w+): \{", linea)
            if m:
                clave, campo = m.group(1), None
            m = re.match(r"^\s{4}(\w+):", linea)
            if m:
                campo = m.group(1)
            if campo in CAMPOS_EXCLUIDOS or "→" in linea:
                continue
            for texto in CADENA.findall(linea):
                yield nombre, clave, campo, texto


def _a_float(n: str) -> float:
    return float(n.replace("−", "-").replace(".", "").replace(",", "."))


def test_la_prosa_no_escribe_pesos():
    malos = [f"{a} · {k} · {c}: «{m.group(0)}»"
             for a, k, c, t in _cadenas()
             for m in PESO.finditer(t)
             if (a, k, c) not in ACEPTADAS]
    assert not malos, (
        "la prosa escribe pesos a mano y van a quedar viejos con el próximo "
        "cambio de composición; la página de la ficha ya los lee del snapshot. "
        "Sacalos (remití a la tabla de composición) o justificá en ACEPTADAS:\n  "
        + "\n  ".join(malos))


def test_la_prosa_no_copia_valores_del_dato_sin_fecha():
    valores = _valores_del_indicador()
    malos = []
    for a, k, c, t in _cadenas():
        if k not in valores or (a, k, c) in ACEPTADAS:
            continue
        for frase in re.split(r"(?<=[.;:])\s", t):
            if FECHADA.search(frase):
                continue
            for n in NUMERO.findall(frase):
                if round(_a_float(n), 2) in valores[k]:
                    malos.append(f"{a} · {k} · {c}: «{n}» en «{frase[:100]}»")
    assert not malos, (
        "la prosa copia un valor del propio indicador sin decir de cuándo es: "
        "queda viejo con el próximo dato. Sacalo (la página muestra el valor "
        "vigente), fechalo, o justificá en ACEPTADAS:\n  " + "\n  ".join(malos))
