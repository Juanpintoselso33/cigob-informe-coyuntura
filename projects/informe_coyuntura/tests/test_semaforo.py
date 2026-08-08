"""Capa de semáforo: color por tensión y umbrales en unidad propia (ADR-0181, ADR-0182)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import parametrica
import itcg
import itcm
import itcp

ESCALA_ITCG = parametrica.Escala(
    itcg.BANDAS_ITCG,
    getattr(itcg, "ANCLAS_ITCG", None),
    getattr(itcg, "TRANSFORMACIONES_ITCG", None),
)
ESCALA_ITCM = parametrica.Escala(
    itcm.BANDAS_ITCM,
    getattr(itcm, "ANCLAS_ITCM", None),
    getattr(itcm, "TRANSFORMACIONES_ITCM", None),
)
ESCALA_ITCP = parametrica.Escala(
    itcp.BANDAS_ITCP,
    getattr(itcp, "ANCLAS_ITCP", None),
    getattr(itcp, "TRANSFORMACIONES_ITCP", None),
)
ESCALAS = {"ITCG": ESCALA_ITCG, "ITCM": ESCALA_ITCM, "ITCP": ESCALA_ITCP}


def _tramos(indicador, escala, color):
    return [t for t in parametrica.umbrales_en_unidad(indicador, escala)
            if t["color"] == color]


class TestColorDeTension:
    def test_los_cuatro_colores(self):
        assert parametrica.color_de_tension(0.0) == "verde"
        assert parametrica.color_de_tension(5.0) == "amarillo"
        assert parametrica.color_de_tension(7.0) == "naranja"
        assert parametrica.color_de_tension(9.5) == "rojo"

    def test_los_bordes_son_inclusivos_hacia_el_mejor_color(self):
        # low exclusivo / high inclusivo, la convención del motor
        assert parametrica.color_de_tension(4.0) == "verde"
        assert parametrica.color_de_tension(4.01) == "amarillo"
        assert parametrica.color_de_tension(6.0) == "amarillo"
        assert parametrica.color_de_tension(6.01) == "naranja"
        assert parametrica.color_de_tension(8.0) == "naranja"
        assert parametrica.color_de_tension(8.01) == "rojo"

    def test_puntaje_0_100_usa_los_bordes_de_las_bandas_de_interpretacion(self):
        assert parametrica.color_de_puntaje(60.0) == "verde"
        assert parametrica.color_de_puntaje(40.0) == "amarillo"
        assert parametrica.color_de_puntaje(20.0) == "naranja"
        assert parametrica.color_de_puntaje(19.9) == "rojo"

    def test_no_usa_la_tension_redondeada(self):
        # 59,9 da tensión 4,01; redondeada a un decimal es 4,0 y daría verde.
        # Es el error que rompe el borde, y este test es el que lo ataja.
        assert parametrica.color_de_puntaje(59.9) == "amarillo"

    def test_base100_despeja_su_propia_formula_de_tension(self):
        # tensión = 5 − (índice − 100) × 0,2  →  t≤4 ⟺ i≥105, t≤6 ⟺ i≥95, t≤8 ⟺ i≥85
        assert parametrica.color_de_indice_base100(105.0) == "verde"
        assert parametrica.color_de_indice_base100(104.9) == "amarillo"
        assert parametrica.color_de_indice_base100(95.0) == "amarillo"
        assert parametrica.color_de_indice_base100(94.9) == "naranja"
        assert parametrica.color_de_indice_base100(85.0) == "naranja"
        assert parametrica.color_de_indice_base100(84.9) == "rojo"


class TestUmbralesEnUnidad:
    def test_indicador_creciente_apertura_comercial(self):
        # apertura: menor alícuota = mejor. Verde es un "≤".
        verde = _tramos("apertura_comercial", ESCALA_ITCG, "verde")
        assert len(verde) == 1
        assert verde[0]["desde"] is None
        assert verde[0]["hasta"] == pytest.approx(6.0, abs=0.01)

    def test_indicador_decreciente_desregulacion(self):
        # desregulación: más artículos = mejor. Verde es un "≥".
        verde = _tramos("desregulacion_normativa", ESCALA_ITCG, "verde")
        assert len(verde) == 1
        assert verde[0]["desde"] == pytest.approx(11000.0, abs=1.0)
        assert verde[0]["hasta"] is None

    def test_reversibilidad_en_las_57_tablas(self):
        # El test que detecta un error de interpolación inversa sin pinear
        # ningún valor: puntuar el umbral tiene que devolver ALGUNO de los
        # cortes reales (60/40/20) — no necesariamente el "propio" del color
        # que lo reporta. Un tramo interior (amarillo, naranja) linda con DOS
        # colores distintos y por lo tanto toca DOS cortes distintos, uno en
        # "desde" y otro en "hasta" (p.ej. amarillo en cepo_mulc: desde=14
        # puntúa 60 —el corte de verde, su vecino mejor— y hasta=20 puntúa 40
        # —el suyo propio—). Atarle a cada tramo un único corte por su color y
        # exigírselo a sus DOS bordes falla en las 57/57 tablas por
        # construcción (no por un bug de interpolación): color_de_tension es
        # inclusivo hacia el color mejor (pineado por TestColorDeTension), así
        # que el borde "de entrada" de un tramo interior siempre puntúa el
        # corte del vecino mejor, nunca el propio.
        cortes = (60.0, 40.0, 20.0)
        revisados = 0
        for sigla, escala in ESCALAS.items():
            for indicador in escala.bandas:
                tramos = parametrica.umbrales_en_unidad(indicador, escala)
                assert tramos, f"{sigla}/{indicador} sin umbrales"
                for tramo in tramos:
                    for borde in (tramo["desde"], tramo["hasta"]):
                        if borde is None:
                            continue
                        p = escala.puntaje(borde, indicador)
                        assert any(p == pytest.approx(c, abs=0.2) for c in cortes), (
                            f"{sigla}/{indicador}: puntaje({borde}) = {p}, "
                            f"no coincide con ningún corte de {cortes}")
                        revisados += 1
        assert revisados > 100

    def test_no_monotono_costo_financiamiento_tesoro(self):
        # Anclas (−5,20) (−2,5,55) (3,100) (9,75) (16,45) (20,15): óptimo en el
        # medio. Verde es un INTERVALO CERRADO y los partidos en dos son
        # amarillo y naranja. Por izquierda nunca hay rojo: el puntaje satura
        # en 20 y se queda en naranja.
        tramos = parametrica.umbrales_en_unidad("costo_financiamiento_tesoro", ESCALA_ITCM)
        verde = [t for t in tramos if t["color"] == "verde"]
        assert len(verde) == 1
        assert verde[0]["desde"] == pytest.approx(-1.89, abs=0.02)
        assert verde[0]["hasta"] == pytest.approx(12.52, abs=0.02)
        assert len([t for t in tramos if t["color"] == "amarillo"]) == 2
        assert len([t for t in tramos if t["color"] == "naranja"]) == 2
        assert len([t for t in tramos if t["color"] == "rojo"]) == 1

    def test_transformacion_devuelve_unidad_cruda(self):
        # rem_ipc_12m se publica como expectativa ANUAL y se puntúa por su
        # equivalente MENSUAL. El umbral tiene que salir en anual, que es lo
        # que muestra la card.
        tramos = parametrica.umbrales_en_unidad("rem_ipc_12m", ESCALA_ITCM)
        bordes = [b for t in tramos for b in (t["desde"], t["hasta"]) if b is not None]
        assert max(bordes) > 5.0, f"parecen equivalentes mensuales, no anuales: {bordes}"

    def test_transformacion_creciente_no_dispara_la_guarda_de_orden(self):
        # rem_ipc_12m es la única transformación declarada hoy y es creciente
        # (más REM anual → más equivalente mensual): el camino soportado.
        # Cubre la rama sana de la guarda que hace ValueError ante una
        # inversa decreciente (ninguna existe todavía, así que esa rama no
        # tiene un test propio — queda documentada en el comentario del código).
        tramos = parametrica.umbrales_en_unidad("rem_ipc_12m", ESCALA_ITCM)
        for tramo in tramos:
            if tramo["desde"] is not None and tramo["hasta"] is not None:
                assert tramo["desde"] <= tramo["hasta"], tramo

    def test_sin_bandas_devuelve_none(self):
        assert parametrica.umbrales_en_unidad("no_existe", ESCALA_ITCG) is None

    def test_sin_tramos_duplicados(self):
        # Cuando un corte cae en un ancla exacta, dos segmentos lo reportan.
        for escala in ESCALAS.values():
            for indicador in escala.bandas:
                tramos = parametrica.umbrales_en_unidad(indicador, escala)
                vistos = [(t["color"], t["desde"], t["hasta"]) for t in tramos]
                assert len(vistos) == len(set(vistos)), f"{indicador}: tramos repetidos"
