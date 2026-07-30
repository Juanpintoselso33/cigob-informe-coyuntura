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


def test_el_factor_solo_se_arma_con_estadisticas_del_terreno_propio():
    """El subconjunto que arma el factor puede ser más chico que la familia
    (ADR-0163), pero nunca puede incluir una estadística ajena: eso convertiría
    el contraste convergente en una mezcla."""
    for indice, claves in pv.FACTOR.items():
        ajenas = [k for k in claves if pv.FAMILIA.get(k) != indice]
        assert not ajenas, f"{indice} arma su factor con estadísticas ajenas: {ajenas}"
        assert len(claves) >= 3, f"{indice}: un factor de menos de tres no se estima"


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


def _panel_consumo(base):
    """Las cuatro estadísticas que arman el factor del ITVC (volúmenes físicos),
    más una del comercio y una ajena, que NO deben entrar al factor."""
    return {"electricidad_residencial": dict(base),
            "gas_residencial": {k: v * 1.4 + 2 for k, v in base.items()},
            "transporte_pasajeros": {k: -v for k, v in base.items()},
            "ventas_naftas": {k: v * 0.8 + 5 for k, v in base.items()},
            "consumo_supermercados": {k: v * 1.1 for k, v in base.items()},
            "merval_usd": _serie([5, 6, 5, 7, 5, 8, 5, 9, 5, 10, 5, 11, 5, 12, 5, 13])}


def test_una_familia_de_tres_o_mas_recibe_su_factor_comun():
    base = _serie([1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17])
    p = pv.perfil("itvc", base, _panel_consumo(base))
    f = p["factor"]
    assert f["n_series"] == 4
    assert set(f["cargas"]) == set(pv.FACTOR["itvc"])
    # el Merval es ajeno y las ventas de comercio no arman el factor (ADR-0163),
    # aunque sí están en la familia del ITVC y se publican en el panel
    assert "merval_usd" not in f["cargas"]
    assert "consumo_supermercados" not in f["cargas"]
    assert any(fila["estadistica"] == "consumo_supermercados" for fila in p["perfil"])


def test_el_factor_deduce_solo_que_una_serie_va_invertida():
    """Lo que antes había que declarar a mano —y era por donde entraba el
    ajuste— lo resuelve la carga: el transporte es el espejo de las otras."""
    base = _serie([1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17])
    f = pv.perfil("itvc", base, _panel_consumo(base))["factor"]
    assert f["cargas"]["transporte_pasajeros"] < 0
    assert f["cargas"]["electricidad_residencial"] > 0
    assert any("signo invertido" in x for x in pv.lectura_factor_detalle({"factor": f}))


def test_una_familia_de_una_sola_estadistica_no_recibe_factor():
    """Con menos de tres no hay factor que estimar, y el ITCG tiene una sola."""
    base = _serie([1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17])
    p = pv.perfil("itcg", base, _panel_consumo(base))
    assert "factor" not in p
    assert pv.lectura_factor(p) == "" and pv.lectura_factor_detalle(p) == []


_GANA = {"factor": {"cargas": {"a": 0.7, "b": 0.5}, "etiquetas": {"a": "una", "b": "otra"},
                    "varianza_explicada": 60.0, "n_series": 3, "n": 30,
                    "r_niveles": 0.523, "r_diferencias": 0.493,
                    "mejor_sola_niveles": 0.493, "mejor_sola_diferencias": 0.42}}
_PIERDE = {"factor": dict(_GANA["factor"], r_niveles=0.211, r_diferencias=0.10,
                          mejor_sola_niveles=0.596, mejor_sola_diferencias=0.246)}
# el caso del ITVC: pierde en niveles y gana en los cambios mes a mes
_GANA_SOLO_DIF = {"factor": dict(_GANA["factor"], r_niveles=0.043, r_diferencias=0.478,
                                 mejor_sola_niveles=0.397, mejor_sola_diferencias=0.409)}


def test_el_detalle_del_factor_dice_si_le_gana_o_no_a_la_mejor_sola():
    assert any("le gana a todas en los dos planos" in x
               for x in pv.lectura_factor_detalle(_GANA))
    txt = " ".join(pv.lectura_factor_detalle(_PIERDE))
    assert "queda por debajo" in txt and "0,596" in txt


def test_ganar_solo_en_los_cambios_se_declara_y_se_explica_el_nivel():
    """El caso del ITVC: el índice se mueve muy poco en neto, así que compararlo
    en NIVELES contra series con tendencia propia no dice gran cosa. Si el texto
    no lo explicara, un 0,04 se leería como que el índice no mide nada."""
    txt = " ".join(pv.lectura_factor_detalle(_GANA_SOLO_DIF))
    assert "le gana a todas en los cambios mes a mes" in txt
    assert "se movió muy poco" in txt
    linea = pv.lectura_factor(_GANA_SOLO_DIF)
    assert "la prueba exigente" in linea and "más que cualquiera" in linea


def test_el_detalle_declara_que_el_indice_no_entra_al_calculo():
    """Es la propiedad que separa esto de un promedio con signos elegidos a
    mano; si no se dice, el lector no tiene cómo saber que no se acomodó."""
    assert any("no participa del cálculo" in x for x in pv.lectura_factor_detalle(_GANA))


def test_el_detalle_viene_en_parrafos_y_ninguno_es_un_muro():
    parrafos = pv.lectura_factor_detalle(_GANA)
    assert len(parrafos) >= 3
    assert all(len(x) < 420 for x in parrafos), [len(x) for x in parrafos]


def test_la_linea_del_tablero_es_corta_y_dice_el_veredicto():
    """El desarrollo va a la ficha: si volviera al tablero, la conclusión —que
    ya es larga— se vuelve ilegible."""
    for p, esperado in ((_GANA, "en los dos planos"), (_PIERDE, "menos que la mejor")):
        linea = pv.lectura_factor(p)
        assert esperado in linea
        assert len(linea) < 260, linea
        assert len(linea) < len(" ".join(pv.lectura_factor_detalle(p)))


def test_el_texto_publico_no_lleva_marcas_de_markdown():
    """Los dos textos van a campos que se renderizan planos: un ** queda a la
    vista como dos asteriscos."""
    for p in (_GANA, _PIERDE, _GANA_SOLO_DIF):
        for txt in [pv.lectura_factor(p)] + pv.lectura_factor_detalle(p):
            assert "**" not in txt and "__" not in txt


def test_el_texto_concuerda_en_numero_cuando_hay_una_sola_propia():
    """«acompaña a las 1 de su propio terreno» es agramatical, y con un panel
    corto el caso n=1 es el normal, no el raro."""
    p = {"indice": "itcg", "n_propias": 1, "n_ajenas": 7,
         "niveles": {"convergente": 0.747, "discriminante": 0.434, "brecha": 0.313},
         "diferencias": {"convergente": 0.119, "discriminante": 0.159, "brecha": -0.04}}
    txt = pv.lectura(p)
    assert "las 1 " not in txt
    assert "la única estadística de su propio terreno" in txt


def test_el_grafico_muestra_el_plano_sobre_el_que_se_apoya_el_veredicto():
    """Si el veredicto descansa SOLO en los cambios mes a mes, graficar los
    niveles deja una figura que contradice a su propio encabezado. Es el caso
    del ITVC: 0,04 en niveles y 0,48 en cambios."""
    assert pv.plano_del_veredicto(_GANA_SOLO_DIF["factor"]) == "diferencias"


def test_por_defecto_se_grafican_los_niveles():
    """Más legibles, y es el plano habitual: sólo se cambia cuando hace falta."""
    assert pv.plano_del_veredicto(_GANA["factor"]) == "niveles"
    assert pv.plano_del_veredicto(_PIERDE["factor"]) == "niveles"
    assert pv.plano_del_veredicto({}) == "niveles"


def test_el_grafico_del_plano_de_cambios_tiene_un_punto_menos():
    base = _serie([1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17])
    f = pv.perfil("itvc", base, _panel_consumo(base))["factor"]
    assert f["plano"] == "niveles"
    assert f["pares_grafico"] == f["pares"]
