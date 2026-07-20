# -*- coding: utf-8 -*-
"""El perfil de vintages no puede perder componentes en silencio (ADR-0107)."""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import publicar

SNAPSHOT = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "informe.json"


def test_el_rotulo_mensual_se_parsea_en_vez_de_descartarse():
    """El bug que apareció al sumar el ITVC al perfil.

    Tres de sus catorce componentes fechan su dato como «2026-04», que
    `date.fromisoformat` rechaza; el `except ValueError` los descartaba sin
    avisar y la card habría dicho que describe el cinturón cubriendo once.
    """
    assert publicar._fecha_dato_a_date("2026-04") == date(2026, 4, 1)
    assert publicar._fecha_dato_a_date("2026-04-17") == date(2026, 4, 17)
    assert publicar._fecha_dato_a_date("no es una fecha") is None


def test_el_itvc_publica_su_perfil_de_vintages():
    """Es el cinturón con más dispersión de los cuatro: la EPH es trimestral y
    sostiene dos componentes, uno en la dimensión de mayor peso."""
    d = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    vin = d["cinturones"]["vida_cotidiana"]["itvc"].get("vintages")
    assert vin, "el ITVC no publica perfil de vintages"
    assert vin["span_dias"] > 0 and vin["meses_promedio"] > 0


def test_ningun_componente_del_indice_queda_fuera_del_perfil():
    """El guard de fondo: si un componente puntúa, tiene que estar fechado.

    Que la card cubra menos de lo que dice es peor que no tenerla — declara una
    vigencia calculada sobre una parte del índice como si fuera el todo.
    """
    d = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for cint, key in (("vida_cotidiana", "itvc"), ("macro", "itcm"),
                      ("gestion", "itcg"), ("politica", "itcp")):
        bloque = d["cinturones"][cint].get(key) or {}
        if not bloque.get("vintages"):
            continue
        en_indice = {k for k, v in d["cinturones"][cint]["indicadores"].items()
                     if v.get("en_indice") and v.get("peso_efectivo")}
        ilegibles = [k for k in en_indice
                     if publicar._fecha_dato_a_date(
                         d["cinturones"][cint]["indicadores"][k].get("fecha_dato") or "") is None]
        assert not ilegibles, (
            f"{key}: componentes que puntúan y no entran al perfil de vintages "
            f"por fecha ilegible: {ilegibles}"
        )


def test_la_fecha_mensual_no_inventa_un_dia_en_el_texto_publico():
    """Si la fuente sólo conoce el mes, decir «1 de abril» es precisión falsa."""
    d = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    vin = d["cinturones"]["vida_cotidiana"]["itvc"]["vintages"]
    fechas = [r["fecha"] for r in vin["rezagados"]]
    assert fechas, "sin rezagados no se puede verificar el formato"
    for f in fechas:
        assert "-" not in f, f"fecha en formato técnico en texto público: {f}"
