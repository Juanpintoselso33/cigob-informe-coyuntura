# -*- coding: utf-8 -*-
"""Entrega 4: ningún nombre interpreta más de lo que observan sus insumos.

Los cuatro casos de esta entrega no tenían mal la aritmética ni el universo: le
ponían al número un nombre que sus insumos no sostienen.

- `idm` se llamaba «Exceso de pesos sobre la demanda» y compara dos AGREGADOS
  monetarios. Estimar una demanda de dinero pide variables, forma funcional y
  validación; nada de eso hay.
- `desequilibrio_monetario` afirmaba medir dinero «fuera del sistema». Su
  componente B es la compra neta de divisas, y el BCRA estimó que cerca del 80%
  de esas compras quedó depositado localmente.
- `icip` se llamaba «Capitalización». Los pagos transfronterizos por informática
  y nube son consumo intermedio en cuentas nacionales.
- `judicializacion` decía medir la judicialización de la agenda del Ejecutivo
  sobre un corpus que no identifica causas contra el Ejecutivo.

Estos tests no verifican prosa linda: verifican que **las afirmaciones que la
auditoría marcó como no sostenidas no puedan volver**. Es la única clase de
regresión posible acá — no hay un número que se mueva.
"""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import itcm
import itcp
import publicar

WEB = RAIZ / "web" / "src" / "lib"
CAPA_PUBLICA = {
    "datos.ts": (WEB / "datos.ts").read_text(encoding="utf-8"),
    "descripciones.ts": (WEB / "descripciones.ts").read_text(encoding="utf-8"),
    "fichas.ts": (WEB / "fichas.ts").read_text(encoding="utf-8"),
    "formulas.ts": (WEB / "formulas.ts").read_text(encoding="utf-8"),
}
CODIGO = {p.name: p.read_text(encoding="utf-8")
          for p in (RAIZ / "scripts").rglob("*.py")}


def _sin_afirmacion(frase, textos, excepciones=()):
    """Dónde aparece `frase` afirmando algo, saltando las líneas que la citan
    para decir que NO es cierta."""
    hallazgos = []
    for nombre, texto in textos.items():
        for linea in texto.splitlines():
            if frase.lower() not in linea.lower():
                continue
            if any(e.lower() in linea.lower() for e in excepciones):
                continue
            hallazgos.append(f"{nombre}: {linea.strip()[:110]}")
    return hallazgos


# Una línea que NIEGA la afirmación no es la afirmación. La lista es explícita a
# propósito: un heurístico más listo (buscar "no" cerca) daría falsos negativos
# justo en las líneas que hay que vigilar.
NIEGA = ("no mide", "no identifica", "no es", "no son", "no lo sostiene",
         "se llamaba", "decía", "hasta agosto", "dos actos distintos",
         "quedó depositado", "consumo intermedio", "ya no puntúa",
         "salió del índice", "estimar una", "es un agregado", "son agregados",
         # citar el ADR de esta entrega marca una línea explicativa
         "adr-0252", "adr-0253", "adr-0254", "adr-0255")


# ── 17 · «fuera del sistema» (ADR-0252) ─────────────────────────────────────

def test_no_se_afirma_que_el_dinero_esta_fuera_del_sistema():
    """La compra neta de divisas no dice adónde fue el dinero."""
    malos = _sin_afirmacion("fuera del sistema", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    assert not malos, "vuelve la afirmación de que el dinero sale del sistema:\n  " + "\n  ".join(malos)


def test_las_celdas_de_la_matriz_describen_la_combinacion_no_el_destino():
    """Las cuatro esquinas nombran qué se observó, no dónde terminó la plata."""
    txt = publicar._macro_input_txt("desequilibrio_monetario", {
        "valor": 77.5, "componente_a": 49.96, "componente_b": 6545.1,
        "celda": "naranja_rojo"})
    assert "presión compradora" in txt
    assert "fuga" not in txt.lower()
    for celda, esperado in (("verde", "poca compra"),
                            ("amarillo", "sin presión compradora"),
                            ("rojo", "presión compradora alta")):
        t = publicar._macro_input_txt("desequilibrio_monetario", {
            "valor": 1.0, "componente_a": 1.0, "componente_b": 1.0, "celda": celda})
        assert esperado in t, celda


def test_el_rotulo_publico_no_promete_dolarizacion_fuera_del_sistema():
    assert 'desequilibrio_monetario: "Dolarización dentro y fuera del sistema"' \
        not in CAPA_PUBLICA["datos.ts"]
    assert "presión compradora" in CAPA_PUBLICA["datos.ts"]


# ── 18 · «capitalización» (ADR-0253) ────────────────────────────────────────

def test_el_icip_no_se_llama_capitalizacion():
    malos = _sin_afirmacion("capitalización inteligente", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    malos += _sin_afirmacion("capitalización digital", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    assert not malos, "vuelve el lenguaje de capitalización:\n  " + "\n  ".join(malos)


def test_el_rotulo_del_icip_habla_de_pagos_no_de_inversion():
    m = re.search(r'\bicip: "([^"]*)"', CAPA_PUBLICA["datos.ts"])
    assert m
    assert "Pagos" in m.group(1)
    assert "Capitalización" not in m.group(1)


def test_la_ficha_declara_que_son_consumo_intermedio():
    """Es la razón por la que no puede llamarse capitalización, y tiene que
    estar dicha donde alguien la vaya a leer."""
    assert "consumo intermedio" in CAPA_PUBLICA["descripciones.ts"]


# ── 16 · «exceso sobre la demanda» (ADR-0254) ───────────────────────────────

def test_el_idm_no_promete_una_demanda_de_dinero():
    malos = _sin_afirmacion("demanda de dinero", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    malos += _sin_afirmacion("exceso de pesos", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    malos += _sin_afirmacion("excedente de pesos", {**CAPA_PUBLICA, **CODIGO}, NIEGA)
    assert not malos, "vuelve el lenguaje de demanda de dinero:\n  " + "\n  ".join(malos)


def test_el_rotulo_del_idm_nombra_los_dos_agregados():
    m = re.search(r'\bidm: "([^"]*)"', CAPA_PUBLICA["datos.ts"])
    assert m
    assert "M3" in m.group(1) and "M2" in m.group(1)
    assert "demanda" not in m.group(1).lower()


def test_la_formula_del_idm_no_cambio():
    """El rediseño de nombre no toca el cálculo: la banda es la misma, así que
    la serie histórica sigue siendo comparable."""
    assert "idm" in itcm.BANDAS_ITCM
    assert itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]["indicadores"]["idm"] == 0.2


# ── 19 · judicialización fuera del score (ADR-0255) ─────────────────────────

def test_judicializacion_no_puntua():
    assert "judicializacion" in itcp.INDICADORES_SUSPENDIDOS
    r = itcp.calcular_itcp({k: 50.0 for k in itcp.BANDAS_ITCP})
    presentes = {i for d in r["dimensiones"].values() for i in d["indicadores"]}
    assert "judicializacion" not in presentes
    assert "judicializacion" in publicar.POLITICA_OCULTOS


def test_su_peso_lo_absorben_los_otros_tres_del_poder_judicial():
    tabla = itcp.DIMENSIONES_ITCP["poder_judicial"]["indicadores"]
    assert "judicializacion" in tabla, "el peso de diseño no se borra (ADR-0245)"
    r = itcp.calcular_itcp({k: 50.0 for k in itcp.BANDAS_ITCP})
    d = r["dimensiones"]["poder_judicial"]
    vivos = {k: p for k, p in tabla.items() if k != "judicializacion"}
    resto = sum(vivos.values())
    for k, info in d["indicadores"].items():
        assert abs(info["peso_efectivo"] / d["peso_efectivo"] - vivos[k] / resto) < 1e-3


def test_su_rotulo_ya_no_dice_que_mide_la_agenda_del_ejecutivo():
    """El corpus de SAIJ no identifica causas contra el PEN: una cautelar entre
    privados cuenta igual."""
    m = re.search(r'\bjudicializacion: "([^"]*)"', CAPA_PUBLICA["datos.ts"])
    assert m
    assert "agenda" not in m.group(1).lower()
    assert "SAIJ" in m.group(1) or "sumarios" in m.group(1)


def test_la_condicion_de_reingreso_pide_causas_contra_el_ejecutivo():
    meta = itcp.INDICADORES_SUSPENDIDOS["judicializacion"]
    cond = meta["condicion_reingreso"].lower()
    assert "ejecutivo" in cond
    assert "expediente" in cond or "caso" in cond
    assert meta["adr"] == "0255"
