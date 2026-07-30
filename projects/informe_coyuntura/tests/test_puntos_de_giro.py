# -*- coding: utf-8 -*-
"""Tests del detector de puntos de giro (ADR-0158), sin red.

El bug que motivó la mitad de estos tests: la primera versión aplicaba la
alternancia UNA vez y después el filtro de duración mínima, que la volvía a
romper. Producía secuencias valle-valle y pico-pico-pico, y con ellas un
«adelanto medio» calculado sobre giros que no eran giros. Por eso `alternan()`
es parte de la interfaz y se afirma en cada caso.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import puntos_de_giro as pg


def _serie(valores, desde=(2024, 1)):
    y, m = desde
    out = {}
    for v in valores:
        out[f"{y:04d}-{m:02d}"] = float(v)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def test_un_ciclo_limpio_da_un_valle_y_un_pico():
    # baja, sube, baja: valle y pico, con fases largas
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    c = pg.ciclo(_serie(vals), ventana=5)
    g = pg.giros(c, fase_min=5)
    assert pg.alternan(g), g
    assert [t for _, t, _ in g] == ["valle", "pico"], g


def test_la_alternancia_se_mantiene_despues_del_filtro_de_fase():
    """EL BUG. Una serie con un pico chiquito muy cerca de otro: al descartarlo
    por fase corta, la versión vieja dejaba dos valles seguidos."""
    vals = [10, 6, 2, 6, 10, 9, 10, 6, 2, 6, 10, 14, 10, 6, 2]
    c = pg.ciclo(_serie(vals), ventana=5)
    g = pg.giros(c, fase_min=5)
    assert pg.alternan(g), f"quedaron giros consecutivos del mismo tipo: {g}"


def test_ninguna_fase_dura_menos_que_el_minimo():
    vals = [5, 3, 5, 3, 5, 3, 5, 9, 1, 9, 1, 9, 1, 5, 5, 5, 1, 9, 1, 9]
    c = pg.ciclo(_serie(vals), ventana=5)
    g = pg.giros(c, fase_min=5)
    assert pg.alternan(g), g
    for i in range(len(g) - 1):
        assert pg._ord(g[i + 1][0]) - pg._ord(g[i][0]) >= 5, g


def test_serie_monotona_no_tiene_giros():
    c = pg.ciclo(_serie(list(range(20))), ventana=5)
    assert pg.giros(c) == []


def test_concordancia_de_una_serie_consigo_misma_es_uno():
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    c = pg.ciclo(_serie(vals), ventana=5)
    g = pg.giros(c, fase_min=5)
    f = pg.fases(c, g)
    assert pg.concordancia(f, f) == (1.0, len(f))


def test_concordancia_de_fases_opuestas_es_cero():
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    c = pg.ciclo(_serie(vals), ventana=5)
    f = pg.fases(c, pg.giros(c, fase_min=5))
    opuesta = {m: -v for m, v in f.items()}
    assert pg.concordancia(f, opuesta)[0] == 0.0


def test_el_apareo_detecta_el_adelanto():
    """B es A corrida dos meses hacia adelante: A se adelanta 2."""
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    a = _serie(vals)
    b = _serie([10, 10] + vals)          # dos meses de retraso
    ca, cb = pg.ciclo(a, 5), pg.ciclo(b, 5)
    pares = pg.aparear(pg.giros(ca, 5), pg.giros(cb, 5))
    desfases = [d for _, _, fb, d in pares if fb is not None]
    assert desfases, pares
    assert all(d > 0 for d in desfases), f"A debería adelantarse: {pares}"


def test_sin_par_se_declara_en_vez_de_omitirse():
    """Un giro sin contraparte no puede desaparecer del conteo: si se omitiera,
    el desfase medio se calcularía sobre los que calzan y siempre daría bien."""
    a = _serie([10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0])
    b = _serie([1] * 18)                  # sin ciclo: no hay giros
    r = pg.analisis(a, b, ventana=5, fase_min=5)
    assert r["apareados"] == 0
    assert r["sin_par"] == len(r["giros"]) > 0
    assert r["desfase_medio"] is None


def test_una_serie_igual_a_la_referencia_no_tiene_señales_falsas():
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    s = _serie(vals)
    r = pg.señales(s, s)
    assert r["falsas"] == 0 and r["perdidos"] == 0


def test_una_serie_sin_ciclo_pierde_los_giros_de_la_referencia():
    ref = _serie([10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0])
    plana = _serie(list(range(18)))          # monótona: sin giros propios
    r = pg.señales(plana, ref)
    assert r["falsas"] == 0, "una serie sin giros no puede dar señales falsas"
    assert r["perdidos"] == r["n_giros_ref"] > 0


def test_los_giros_fuera_del_solape_no_cuentan_como_perdidos():
    """Un giro de la referencia en meses donde el indicador ni existe no es un
    giro perdido: sería castigar al indicador por no haber nacido."""
    vals = [10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0]
    ref = _serie(vals + vals)                       # 36 meses, dos ciclos
    corta = {m: v for m, v in _serie(vals).items()}  # sólo los primeros 18
    r = pg.señales(corta, ref)
    assert r["n_giros_ref"] <= 3, r


def test_el_compuesto_se_compara_contra_cada_componente():
    ref = _serie([10, 8, 6, 4, 2, 0, 2, 4, 6, 8, 10, 12, 10, 8, 6, 4, 2, 0,
                  2, 4, 6, 8, 10, 12])
    comp = dict(ref)                                  # compuesto perfecto
    componentes = {"bueno": dict(ref),
                   "ruidoso": _serie([5, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9,
                                      1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9])}
    r = pg.compuesto_vs_componentes(comp, componentes, ref, min_meses=12)
    assert r["evaluables"] == 2
    assert r["compuesto"]["total"] == 0
    assert r["mejores"] == 0, "nada puede ser mejor que cero errores"
