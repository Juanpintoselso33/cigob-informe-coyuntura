"""ADR-0396: la lectura en palabras sale del mismo valor crudo que el color,
los rótulos de base dicen contra qué se ancla cada índice, y las tablas de
colores con tramo abierto funcionan en cualquier escala de unidades."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itcm, itcp, itvc, parametrica, publicar  # noqa: E402


def _tarjeta_politica(puntaje):
    c = {"indicadores": {"ratio_dnu": {"en_indice": True, "puntaje_itcp": puntaje,
                                       "valor": 1.094, "peso_efectivo": 0.02}}}
    publicar._scoring_indice(c, "itcp", itcp, "contexto", lambda k, i: "")
    return c["indicadores"]["ratio_dnu"]


def test_lectura_y_color_coinciden_en_el_borde():
    # puntaje 59,95 → tensión cruda 4,005: amarillo. Redondeada (4,0) leería verde.
    ind = _tarjeta_politica(59.95)
    color = parametrica.color_de_puntaje(59.95)
    assert color == "amarillo"
    assert round((100 - 59.95) / 10, 1) == 4.0          # el redondeado engaña
    assert f"está en {color} (" in ind["aporte_lectura"], ind["aporte_lectura"]
    assert "verde" not in ind["aporte_lectura"]


def test_lectura_y_color_coinciden_en_un_barrido():
    for p in [x / 10 for x in range(160, 960, 7)] + [59.95, 39.95, 19.95, 60.05]:
        lectura = _tarjeta_politica(p)["aporte_lectura"]
        assert f"está en {parametrica.color_de_puntaje(p)} (" in lectura, (p, lectura)


def test_rotulos_de_base_de_vida_cotidiana():
    """Corre el bloque de vida sobre el snapshot (en memoria, sin escribir)."""
    import copy
    import json
    web = Path(__file__).resolve().parents[1] / "web/src/data"
    snap = json.loads((web / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((web / "series.json").read_text(encoding="utf-8"))
    c = copy.deepcopy(snap["cinturones"]["vida_cotidiana"])
    publicar._scoring_vida_itvc(c, series)
    f = {k: (v.get("aporte_formula") or "") for k, v in c["indicadores"].items()}
    for k in ("tasa_homicidios", "tasa_robos"):
        assert "frente a la mediana de la serie 2000-2025" in f[k], f[k]
        assert "igual que la mediana histórica" in f[k] and "4º trimestre de 2023" not in f[k], f[k]
    assert "frente al 2º semestre de 2023" in f["pobreza_nowcast"], f["pobreza_nowcast"]
    # ADR-0393: la victimización usa el default (promedio del 4º trimestre de 2023)
    assert "frente a 4º trimestre de 2023" in f["inseguridad"] and "ene-2024" not in f["inseguridad"]


def test_tabla_de_colores_con_tramo_abierto_en_millones_incluye_el_rojo():
    escala = parametrica.Escala(
        {"x": [(float("-inf"), 4_000_000.0, 100), (4_000_000.0, 5_900_000.0, 85),
               (5_900_000.0, 7_600_000.0, 65), (7_600_000.0, 9_100_000.0, 40),
               (9_100_000.0, float("inf"), 10)]}, None, None)
    tabla = parametrica.umbrales_en_unidad("x", escala)
    assert [t["color"] for t in tabla] == ["verde", "amarillo", "naranja", "rojo"], tabla
    assert tabla[-1]["hasta"] is None and tabla[-1]["desde"] is not None


def test_tabla_de_colores_es_invariante_a_la_escala():
    base = [(float("-inf"), 4.0, 100), (4.0, 5.9, 85), (5.9, 7.6, 65),
            (7.6, 9.1, 40), (9.1, float("inf"), 10)]
    colores = None
    for k in (1e-3, 1.0, 1e3, 1e6, 1e9):
        bandas = [(a * k, b * k, p) for a, b, p in base]
        t = parametrica.umbrales_en_unidad("x", parametrica.Escala({"x": bandas}, None, None))
        c = [x["color"] for x in t]
        assert colores is None or c == colores, (k, c)
        colores = c


def test_por_que_con_miles_y_sin_ceros_sobrantes():
    tramos = [{"color": "verde", "desde": None, "hasta": 7_070_000.0},
              {"color": "amarillo", "desde": 7_070_000.0, "hasta": None}]
    s = publicar._semaforo_de("verde", 1.0, tramos, "jornadas", 4820775)
    assert s["por_que"] == ("4.820.775 jornadas está en Verde, a 2.249.225 del límite con "
                            "Amarillo (7.070.000)."), s["por_que"]


def test_cortes_se_redondean_a_la_precision_del_indicador():
    tramos = [{"color": "verde", "desde": 141.1178, "hasta": None},
              {"color": "amarillo", "desde": None, "hasta": 141.1178}]
    s = publicar._semaforo_de("verde", 1.0, tramos, "pts", 145.14)
    assert s["umbrales"][0]["desde"] == 141.12
    assert "141,12" in s["por_que"] and "141,1178" not in s["por_que"]
