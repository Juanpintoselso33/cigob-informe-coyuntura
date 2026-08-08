"""Capa de semáforo: color por tensión y umbrales en unidad propia (ADR-0181, ADR-0182)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import parametrica


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
