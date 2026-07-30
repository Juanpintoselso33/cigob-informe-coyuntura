# -*- coding: utf-8 -*-
"""Tests del panel de validación socioeconómica (ADR-0159), sin red."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcg  # noqa: E402
import itcm  # noqa: E402
import itcp  # noqa: E402
import itvc  # noqa: E402
import panel_validacion as pv  # noqa: E402


def _serie(vals, desde=(2024, 1)):
    y, m = desde
    out = {}
    for v in vals:
        out[f"{y:04d}-{m:02d}"] = float(v)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def test_ninguna_estadistica_del_panel_es_componente_de_un_indice():
    """Si una lo fuera, el índice se estaría validando contra una parte de sí
    mismo — el defecto que obligaba a publicar el artificial «ITVC sin ICC»."""
    componentes = set(itcm.BANDAS_ITCM) | set(itcg.BANDAS_ITCG) | set(itcp.BANDAS_ITCP)
    componentes |= {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    choque = sorted(set(pv.FAMILIA) & componentes)
    assert not choque, f"el panel incluye componentes de algún índice: {choque}"


def test_toda_estadistica_del_panel_tiene_etiqueta_publica():
    faltan = sorted(set(pv.FAMILIA) - set(pv.ETIQUETAS))
    assert not faltan, f"sin etiqueta para el texto público: {faltan}"


def test_las_familias_cubren_los_cuatro_indices():
    assert set(pv.FAMILIA.values()) == {"itvc", "itcg", "itcp", "itcm"}


def test_una_serie_identica_a_su_familia_da_brecha_positiva():
    base = _serie([1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17])
    ruido = _serie([5, 5, 6, 5, 6, 5, 6, 5, 6, 5, 6, 5, 6, 5, 6, 5])
    panel = {"consumo_supermercados": dict(base), "merval_usd": ruido}
    p = pv.perfil("itvc", base, panel)
    assert p["niveles"]["convergente"] == 1.0
    assert p["diferencias"]["brecha"] > 0
    assert p["n_propias"] == 1 and p["n_ajenas"] == 1


def test_la_brecha_negativa_no_se_esconde_en_el_texto():
    """El estándar pide explicar las diferencias, no reportar sólo las que
    confirman. Si el texto omitiera el caso negativo, el tablero publicaría
    validación sólo cuando le da bien."""
    p = {"indice": "itvc", "n_propias": 1, "n_ajenas": 1,
         "niveles": {"convergente": 0.5, "discriminante": 0.4, "brecha": 0.1},
         "diferencias": {"convergente": 0.18, "discriminante": 0.26, "brecha": -0.08}}
    txt = pv.lectura(p)
    # en minúscula: el texto es público y las mayúsculas de énfasis no van
    assert "no se sostiene" in txt
    assert "0,18" in txt and "0,26" in txt


def test_sin_datos_suficientes_no_inventa_perfil():
    corta = _serie([1, 2, 3])
    p = pv.perfil("itvc", corta, {"consumo_supermercados": _serie([1, 2, 3])})
    assert p["perfil"] == []
    assert p["niveles"]["brecha"] is None
    assert pv.lectura(p) == ""


def test_el_texto_publico_usa_coma_decimal_y_menos_tipografico():
    p = {"indice": "itcg", "n_propias": 1, "n_ajenas": 2,
         "niveles": {"convergente": 0.75, "discriminante": 0.44, "brecha": 0.31},
         "diferencias": {"convergente": 0.13, "discriminante": 0.21, "brecha": -0.08}}
    txt = pv.lectura(p)
    assert "0,75" in txt and "0.75" not in txt


def test_el_texto_concuerda_en_numero_cuando_hay_una_sola_propia():
    """«acompaña a las 1 de su propio terreno» es agramatical, y con un panel
    corto el caso n=1 es el normal, no el raro."""
    p = {"indice": "itcg", "n_propias": 1, "n_ajenas": 7,
         "niveles": {"convergente": 0.747, "discriminante": 0.434, "brecha": 0.313},
         "diferencias": {"convergente": 0.119, "discriminante": 0.159, "brecha": -0.04}}
    txt = pv.lectura(p)
    assert "las 1 " not in txt
    assert "la única estadística de su propio terreno" in txt
