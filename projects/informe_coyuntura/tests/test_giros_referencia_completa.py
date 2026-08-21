# -*- coding: utf-8 -*-
"""La referencia de un análisis de puntos de giro entra ENTERA (ADR-0226).

EL PROBLEMA, y por qué no se ve solo. `puntos_de_giro` estima el ciclo como
desviación de una media móvil centrada. En el borde de una serie esa media se
calcula con una ventana incompleta, así que la tendencia queda torcida y
aparecen extremos locales que la serie no tiene. ADR-0158 ya lo había
documentado hacia adentro —una serie monótona devolvía giros de amplitud casi
cero— y le puso amplitud mínima y la marca de provisorio.

Lo que faltaba es la otra mitad: si la SERIE DE REFERENCIA se recorta para
hacerla coincidir con la ventana del índice, el corte crea un borde nuevo en
medio de datos que existen, y ahí se fabrican giros que después se aparean con
los del índice. La concordancia sale distinta y nadie se entera.

MEDIDO CON DATOS REALES, y es lo que motivó este test: contrastando el ITCG
contra el gasto en subsidios, la serie recortada en dic-2023 daba una
concordancia de 0,815 con tres giros de la referencia dentro de la ventana; con
doce meses más de historia, 0,519; con la serie entera, 0,593 y UN solo giro
adentro. Dos de los tres giros eran del corte.
"""
import json
import math
import random
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import puntos_de_giro as pg  # noqa: E402


def _meses(desde, n):
    y, m = int(desde[:4]), int(desde[5:7])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def _series():
    """Referencia larga sin ciclo propio (caída que se ameseta) + un índice
    corto. El ruido es determinista: sin nada de ruido no hay extremos locales
    de ningún lado y el ejercicio no mide nada."""
    rnd = random.Random(7)
    ref = {m: 100.0 - 55.0 * (1 - math.exp(-i / 45.0)) + rnd.uniform(-1.2, 1.2)
           for i, m in enumerate(_meses("2018-01", 102))}
    idx = {m: 20.0 + 60.0 * (i / 30.0) + rnd.uniform(-1.5, 1.5)
           for i, m in enumerate(_meses("2023-12", 31))}
    return idx, ref


def _giros_dentro(analisis, idx):
    return [g["mes"] for g in analisis["giros_referencia"]
            if min(idx) <= g["mes"] <= max(idx)]


def test_recortar_la_referencia_fabrica_giros_en_el_borde():
    idx, ref = _series()
    completa = pg.analisis(idx, ref)
    recortada = pg.analisis(idx, {m: v for m, v in ref.items() if m >= min(idx)})
    dentro_c = _giros_dentro(completa, idx)
    dentro_r = _giros_dentro(recortada, idx)
    # los giros del ÍNDICE no cambian: lo único que se movió es la referencia
    assert [g["mes"] for g in completa["giros"]] == [g["mes"] for g in recortada["giros"]]
    # y la referencia recortada inventa giros dentro de la misma ventana
    assert len(dentro_r) > len(dentro_c), (dentro_c, dentro_r)
    assert set(dentro_c) < set(dentro_r)


def test_la_concordancia_se_mueve_al_recortar():
    """Corolario que hace al número publicable o no: la misma comparación, con
    la misma ventana de solape, da distinto según cuánta historia se le dejó a
    la referencia. Si el resultado depende de eso, el recorte es una decisión
    metodológica y no un detalle de preparación de datos."""
    idx, ref = _series()
    completa = pg.analisis(idx, ref)
    recortada = pg.analisis(idx, {m: v for m, v in ref.items() if m >= min(idx)})
    assert completa["n_meses"] == recortada["n_meses"]
    assert completa["concordancia"] != recortada["concordancia"]


def test_la_referencia_del_itcm_llega_de_antes_que_el_indice():
    """La única concordancia que el informe publica hoy es la del ITCM contra
    el Índice Líder. Su referencia trae historia previa —no está recortada— y
    esto lo fija: si alguien la recortara a la ventana del índice para
    «alinearlas», el número publicado cambiaría sin que nada más avisara."""
    salida = RAIZ / "output" / "validacion_externa.json"
    if not salida.exists():
        pytest.skip("sin output/validacion_externa.json")
    d = json.loads(salida.read_text(encoding="utf-8"))
    itcm = d.get("serie_itcm") or {}
    # La ventana que ENTRÓ al cálculo, no la serie que se descargó: son cosas
    # distintas apenas alguien filtre entre una y otra, y ése es justamente el
    # cambio que hay que poder ver.
    ventana = (d.get("giros_itcm") or {}).get("referencia_ventana") or {}
    if not ventana or not itcm:
        pytest.skip("la corrida no trae el ITCM y la ventana de su referencia")
    ini_ref, ini_idx = ventana["desde"], min(itcm)
    assert ini_ref < ini_idx, (ini_ref, ini_idx)
    # al menos una ventana entera de media móvil antes del arranque del índice,
    # que es lo que hace falta para que el primer mes comparado no se calcule
    # contra un borde
    previos = (int(ini_idx[:4]) * 12 + int(ini_idx[5:7])) - (int(ini_ref[:4]) * 12 + int(ini_ref[5:7]))
    assert previos >= 13, f"sólo {previos} meses de historia previa"
