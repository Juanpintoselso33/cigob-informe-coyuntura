"""Tests del compuesto tipo de cambio real × términos del intercambio (sin red).

Pinean lo que decidió ADR-0360: las cuatro esquinas y su asimetría, la
posición del tipo de cambio real por sus umbrales institucionales (no por una
ventana), los cortes congelados de los términos del intercambio, y que cada
mes use el último trimestre publicado sin anticipar ninguno.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm                         # noqa: E402
import parametrica                  # noqa: E402
import terminos_intercambio as ti   # noqa: E402

# Términos del intercambio publicados por el INDEC (82.2_ITI_2004_T_27),
# 3T-2023 a 2T-2026, tal como estaban al calibrar (20-oct-2026).
TI_REAL = {
    "2023-07": 136.8618, "2023-10": 140.3978, "2024-01": 138.3890,
    "2024-04": 129.7009, "2024-07": 131.3041, "2024-10": 142.1155,
    "2025-01": 148.1510, "2025-04": 138.1655, "2025-07": 138.0399,
    "2025-10": 140.5937, "2026-01": 148.0972, "2026-04": 145.1401,
}


# ── La matriz ────────────────────────────────────────────────────────────────

def test_las_cuatro_esquinas():
    assert ti.puntaje_matriz(1.0, 1.0) == 85.0   # competitivo, términos altos
    assert ti.puntaje_matriz(1.0, 0.0) == 50.0   # competitivo, términos bajos
    assert ti.puntaje_matriz(0.0, 1.0) == 30.0   # apreciado, términos altos
    assert ti.puntaje_matriz(0.0, 0.0) == 10.0   # apreciado, términos bajos


def test_la_matriz_es_asimetrica_a_proposito():
    """ADR-0360: con el peso competitivo el ajuste ya ocurrió; un peso
    apreciado sostenido por los precios depende de una variable externa. El
    orden de las cruzadas es la decisión, no un número suelto."""
    assert ti.puntaje_matriz(1.0, 0.0) > ti.puntaje_matriz(0.0, 1.0)


def test_las_esquinas_caen_en_el_medio_de_cada_color():
    colores = [parametrica.color_de_puntaje(ti.puntaje_matriz(a, b))
               for a, b in ((1, 1), (1, 0), (0, 1), (0, 0))]
    assert colores == ["verde", "amarillo", "naranja", "rojo"]


def test_el_centro_no_es_un_promedio_de_las_esquinas_cruzadas():
    # bilineal: el centro es el promedio de las CUATRO, no de dos
    assert ti.puntaje_matriz(0.5, 0.5) == pytest.approx((85 + 50 + 30 + 10) / 4)


# ── Posiciones ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tcrm, esperado", [
    (60.0, 0.0), (75.0, 0.0),        # atraso severo satura en 0
    (110.0, 1.0), (130.0, 1.0),      # competitivo satura en 1
    (90.0, (60 - 10) / 90),          # ancla intermedia
])
def test_posicion_del_tcr_sale_de_sus_umbrales_institucionales(tcrm, esperado):
    assert ti.posicion_tcr(tcrm) == pytest.approx(esperado)


def test_el_tcr_vuelve_a_puntuar_con_sus_umbrales():
    """ADR-0375: es tarjeta otra vez, con los umbrales de siempre."""
    assert itcm.BANDAS_ITCM["tcrm"] is ti.BANDAS_TCR
    assert "tcrm" not in itcm.INDICADORES_CONTEXTO
    assert "tcr_terminos_intercambio" in itcm.INDICADORES_CONTEXTO
    assert ti.BANDAS_TCR[0] == (110.0, float("inf"), 100)
    assert ti.BANDAS_TCR[-1] == (float("-inf"), 75.0, 10)


def test_los_cortes_son_los_percentiles_de_la_ventana_y_estan_congelados():
    ventana = sorted(v for q, v in TI_REAL.items() if "2023-10" <= q <= "2026-04")
    assert len(ventana) == 11
    n = len(ventana) - 1

    def pct(p):
        k = p * n
        lo = int(k)
        hi = min(lo + 1, n)
        return ventana[lo] + (ventana[hi] - ventana[lo]) * (k - lo)

    calculados = tuple(round(pct(p), 2) for p in ti.POSICIONES)
    assert calculados == pytest.approx(ti.CORTES_TI, abs=0.01)


def test_posicion_de_los_terminos_satura_fuera_de_los_cortes():
    assert ti.posicion_ti(100.0) == 0.0
    assert ti.posicion_ti(200.0) == 1.0
    assert ti.posicion_ti(ti.CORTES_TI[2]) == pytest.approx(0.5)


# ── Frecuencia ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("mes, trimestre", [
    ("2026-08", "2026-01"),   # el 2T todavía no salió: usa el 1T
    ("2026-09", "2026-04"),   # el 2T entra en septiembre
    ("2026-11", "2026-04"),
    ("2026-12", "2026-04"),   # el 3T entraría en diciembre, pero no está publicado
])
def test_cada_mes_usa_el_ultimo_trimestre_publicado(mes, trimestre):
    assert ti.trimestre_vigente(mes, TI_REAL) == trimestre


def test_no_anticipa_un_trimestre_que_la_fuente_ya_tiene():
    """Que el dato esté hoy en la API no lo vuelve publicado en un mes viejo."""
    assert ti.trimestre_vigente("2026-06", TI_REAL) == "2026-01"
    assert ti.trimestre_vigente("2026-05", TI_REAL) == "2025-10"


def test_etiqueta_trimestre():
    assert ti.etiqueta_trimestre("2026-04") == "2T-2026"
    assert ti.etiqueta_trimestre("2023-10") == "4T-2023"


# ── Serie ────────────────────────────────────────────────────────────────────

def test_la_serie_arranca_en_diciembre_de_2023_y_no_imputa():
    tcrm = {"2023-11": 50.0, "2023-12": 124.88, "2026-09": 85.87}
    serie = ti.construir_serie(tcrm=tcrm, terminos=TI_REAL)
    assert [f["mes"] for f in serie] == ["2023-12", "2026-09"]


def test_septiembre_2026_con_el_dato_real():
    """El valor que publicó la primera corrida (20-oct-2026)."""
    fila = ti.construir_serie(tcrm={"2026-09": 85.87}, terminos=TI_REAL)[0]
    assert fila["trimestre_ti"] == "2T-2026"
    assert fila["celda"] == "apreciado_ti_altos"
    assert fila["puntaje"] == 49.8


def test_la_dimension_cruza_las_dos_tarjetas_con_la_matriz():
    """ADR-0375: el cruce pasó del indicador a la dimensión, con el mismo
    número que el compuesto de ADR-0360."""
    dim = itcm.DIMENSIONES_ITCM["competitividad_externa"]
    assert dim["peso"] == 0.11
    assert dim["indicadores"] == {"tcrm": 0.5, "terminos_intercambio": 0.5}
    assert dim["combinar"] is ti.combinar_dimension
    r = itcm.calcular_itcm({"tcrm": 85.87, "terminos_intercambio": 145.1401})
    d = r["dimensiones"]["competitividad_externa"]
    assert d["indicadores"]["tcrm"]["puntaje_aplicado"] == pytest.approx(49.7, abs=0.05)
    assert d["indicadores"]["terminos_intercambio"]["puntaje_aplicado"] == pytest.approx(85.0, abs=0.05)
    assert d["puntaje"] == 49.8
    fila = ti.construir_serie(tcrm={"2026-09": 85.87}, terminos=TI_REAL)[0]
    assert d["puntaje"] == fila["puntaje"]


@pytest.mark.parametrize("tcrm,terminos", [(70, 125), (80, 139), (98, 141), (105, 146), (120, 150)])
def test_la_dimension_es_la_matriz_y_no_el_promedio(tcrm, terminos):
    d = itcm.calcular_itcm({"tcrm": tcrm, "terminos_intercambio": terminos})["dimensiones"]["competitividad_externa"]
    esperado = ti.puntaje_matriz(ti.posicion_tcr(tcrm), ti.posicion_ti(terminos))
    assert d["puntaje"] == pytest.approx(esperado, abs=0.051)


def test_los_terminos_puntuan_en_la_escala_del_tcr():
    for corte, posicion in zip(ti.CORTES_TI, ti.POSICIONES):
        p = parametrica.puntaje_de(corte, "terminos_intercambio", itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM)
        assert ti.posicion_de_puntaje(p) == pytest.approx(posicion)


def test_con_un_solo_componente_la_dimension_no_se_calcula():
    r = itcm.calcular_itcm({"tcrm": 90.0, "ipc_total": 2.0})
    assert "competitividad_externa" not in r["dimensiones"]


def test_un_mes_con_los_terminos_congelados_no_se_calcula():
    """Codex, 20-oct: la serie histórica aplicaba el rezago de publicación pero
    no el tope, así que publicaba puntos que la card rechaza."""
    viejos = {q: v for q, v in TI_REAL.items() if q <= "2025-10"}
    serie = ti.construir_serie(tcrm={"2026-08": 85.55, "2026-09": 85.87},
                               terminos=viejos)
    # 4T-2025 (empieza en octubre) está a 10 y 11 meses: fuera del tope
    assert serie == []
    assert ti.construir_serie(tcrm={"2026-07": 85.49}, terminos=viejos)


def test_parsear_terminos_descarta_vacios():
    assert ti.parsear_terminos([["2026-04-01", 145.14], ["2026-07-01", None]]) == {
        "2026-04": 145.14}
    with pytest.raises(ValueError):
        ti.parsear_terminos([])
