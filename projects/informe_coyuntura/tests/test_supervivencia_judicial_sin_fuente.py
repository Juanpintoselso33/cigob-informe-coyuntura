"""ADR-0230: no hay fuente para la supervivencia JUDICIAL de las normas.

Lo que se protege acá no es un indicador —no existe— sino un **resultado
negativo** y la razón de que lo sea. El riesgo concreto tiene nombre y está
medido: el campo `estado` de SAIJ existe, es gratis, tiene vocabulario cerrado
y devuelve el DNU 70/2023 como «Vigente, de alcance general» dos años y medio
después de que la Justicia frenara su Título IV. Es exactamente la clase de
error que ADR-0218 dejó escrito —un indicador que no mide lo que su nombre
dice— y ningún gate del proyecto compara un nombre con su fuente.

De ahí las cinco guardas: que el relevamiento sea legible, que ninguna fuente
quede declarada apta sin que alguien escriba el ADR que revierte éste, que no
se cablee a ningún índice, que no aparezca un indicador con nombre de
supervivencia judicial, y que las cifras del ADR salgan del relevamiento.
"""
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RELEVAMIENTO = RAIZ / "data" / "politica" / "supervivencia_judicial_fuentes.json"
ADR = RAIZ / "docs" / "adr" / "0230-nadie-publica-si-un-decreto-sigue-rigiendo.md"
INDICES = ("itcm.py", "itcp.py", "itcg.py", "itvc.py")

VEREDICTOS = {"no_sirve", "parcial", "sirve"}


@pytest.fixture(scope="module")
def relevamiento() -> dict:
    return json.loads(RELEVAMIENTO.read_text(encoding="utf-8"))


# ── 1 · El relevamiento se puede leer y está completo ───────────────────────
def test_el_relevamiento_es_legible_y_declara_sus_fuentes(relevamiento):
    fuentes = relevamiento["fuentes"]
    assert len(fuentes) >= 6, "el relevamiento recorrió seis fuentes; no se recortan"
    for nombre, f in fuentes.items():
        assert f.get("veredicto") in VEREDICTOS, (
            f"{nombre}: veredicto {f.get('veredicto')!r} fuera del vocabulario "
            f"{sorted(VEREDICTOS)}")


# ── 2 · Ninguna fuente quedó declarada apta ─────────────────────────────────
def test_ninguna_fuente_relevada_quedo_declarada_apta(relevamiento):
    """El disparador. Si alguien encuentra la fuente que falta y pone `sirve`,
    este test cae — y esa caída es el pedido de escribir el ADR que revierte
    ADR-0230, en vez de cambiar el veredicto en silencio y que el tablero
    empiece a publicar un indicador que nadie discutió."""
    aptas = sorted(n for n, f in relevamiento["fuentes"].items()
                   if f.get("veredicto") == "sirve")
    assert not aptas, (
        f"{aptas} quedaron declaradas aptas y ADR-0230 dice que ninguna lo es. "
        "Si de verdad apareció la fuente, escribí el ADR que supersede a 0230 "
        "en vez de dar vuelta el veredicto acá.")
    assert relevamiento["_meta"]["veredicto"] == "NINGUNA FUENTE SIRVE"


# ── 3 · El relevamiento no alimenta ningún índice ───────────────────────────
def test_el_relevamiento_no_alimenta_ningun_indice():
    """Misma guarda que ADR-0141 le puso al detector de la CSJN: es un mapa de
    fuentes, no una serie. Nada de esto puede terminar puntuando."""
    for indice in INDICES:
        texto = (RAIZ / "scripts" / indice).read_text(encoding="utf-8")
        assert "supervivencia_judicial_fuentes" not in texto, (
            f"{indice} referencia el relevamiento de ADR-0230, que no es una serie")


# ── 4 · Nadie cableó el campo `estado` como si fuera judicial ───────────────
# Los nombres que un indicador así llevaría. No pretende ser exhaustivo: cubre
# las formas con las que alguien lo bautizaría al retomar el ADR.
_NOMBRES_PROHIBIDOS = re.compile(
    r"supervivencia_judicial|normas_caidas|caida_judicial|"
    r"veto_constitucionalidad|inconstitucionalidad_normas|cautelares_normas",
    re.I)


def test_ningun_indice_declara_un_indicador_de_supervivencia_judicial():
    """El error que ADR-0230 previene no es abstracto: el campo `estado` de SAIJ
    está poblado, es gratis y contesta «Vigente» para una norma frenada. Un
    indicador con este nombre encima de esa fuente pasaría todos los gates."""
    encontrados = []
    for indice in INDICES:
        texto = (RAIZ / "scripts" / indice).read_text(encoding="utf-8")
        # sólo el código, no los comentarios: el ADR se cita en prosa
        codigo = "\n".join(l.split("#")[0] for l in texto.splitlines())
        for m in _NOMBRES_PROHIBIDOS.finditer(codigo):
            encontrados.append(f"{indice}: {m.group(0)}")
    assert not encontrados, (
        "apareció un indicador con nombre de supervivencia judicial: "
        + ", ".join(encontrados) +
        ". ADR-0230 midió que ninguna fuente lo sostiene; si cambió, superseder "
        "el ADR primero.")


# ── 5 · Las cifras del ADR salen del relevamiento ───────────────────────────
# Cada fila es (ruta dentro del JSON, valor medido, cómo se escribe en el ADR).
# No se listan todas: sólo las que sostienen la decisión, que son las que no
# pueden derivar sin que el ADR cambie de conclusión.
_CIFRAS = [
    (("universo_que_habria_que_cubrir", "normas_del_pen_en_el_dataset_abierto_desde_2023_12_10"),
     2914, "2.914"),
    (("universo_que_habria_que_cubrir", "dnu_en_la_misma_ventana"), 113, "**113 DNU**"),
    (("fuentes", "infoleg_dataset_abierto", "observaciones_no_vacias"), 200, "200 tienen"),
    (("fuentes", "infoleg_dataset_abierto", "observaciones_que_mencionan_algo_judicial"), 0, None),
    (("fuentes", "saij_legislacion", "cobertura_del_propio_campo", "con_el_campo_vacio"),
     8015, "8.015"),
    (("fuentes", "saij_jurisprudencia", "cobertura_por_norma", "dnu_con_al_menos_un_documento"),
     10, "10 DNU (8,8%)"),
    (("fuentes", "chequeado_eldiarioar_fopea", "filas"), 161, "161 filas"),
]


def _hondo(d: dict, ruta: tuple):
    for k in ruta:
        d = d[k]
    return d


def test_las_cifras_del_adr_salen_del_relevamiento(relevamiento):
    """El ADR y el relevamiento son dos archivos y pueden derivar. Cada cifra
    que sostiene la decisión tiene que estar en los dos, con el mismo valor."""
    problemas = []
    texto = ADR.read_text(encoding="utf-8")
    for ruta, esperado, como_se_escribe in _CIFRAS:
        medido = _hondo(relevamiento, ruta)
        if medido != esperado:
            problemas.append(f"{'/'.join(ruta)}: el relevamiento dice {medido}, "
                             f"el ADR se escribió con {esperado}")
        elif como_se_escribe and como_se_escribe not in texto:
            problemas.append(f"{'/'.join(ruta)}: el ADR ya no dice «{como_se_escribe}»")
    assert not problemas, (
        "el ADR y el relevamiento dejaron de decir lo mismo:\n  "
        + "\n  ".join(problemas))
