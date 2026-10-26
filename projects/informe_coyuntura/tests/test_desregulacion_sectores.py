# -*- coding: utf-8 -*-
"""Desregulación: la clasificación por sector del Ministerio (ADR-0363).

Complementa el conteo de artículos, que no distingue la importancia de cada
norma (auditoría de oct-2026, observación #7). No puntúa: se publica sólo si
los sectores suman el total de normas del mismo informe.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import gestion

FIXTURE = Path(__file__).parent / "fixtures" / "desregulacion_sectores_ago2026.json"


def _fx():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_lee_los_once_sectores_del_informe_de_agosto_2026():
    fx = _fx()
    s = gestion._desreg_sectores_de_bloques(fx["bloques"], fx["normas"])
    assert len(s) == 11
    assert s["Agroindustria"] == 125
    assert s["Finanzas y Mercado de Capitales"] == 120     # sin el «Finanzas» pegado
    assert s["Sector Inmobiliario"] == 16
    assert sum(s.values()) == 770
    assert list(s.values()) == sorted(s.values(), reverse=True)


def test_si_no_suma_el_total_no_se_publica():
    fx = _fx()
    assert gestion._desreg_sectores_de_bloques(fx["bloques"], 771) == {}
    # una cifra mal leída tampoco pasa
    bloques = [list(b) for b in fx["bloques"]]
    i = next(k for k, b in enumerate(bloques) if b[4].strip() == "125")
    bloques[i][4] = "152\n"
    assert gestion._desreg_sectores_de_bloques(bloques, 770) == {}


def test_sin_tabla_o_sin_total_no_inventa():
    fx = _fx()
    sin_titulo = [b for b in fx["bloques"] if "por sector" not in b[4]]
    assert gestion._desreg_sectores_de_bloques(sin_titulo, 770) == {}
    assert gestion._desreg_sectores_de_bloques(fx["bloques"], None) == {}
