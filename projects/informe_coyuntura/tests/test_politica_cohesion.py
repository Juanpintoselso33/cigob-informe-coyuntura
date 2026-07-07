import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica


def test_indice_rice_unanime_afirmativo():
    assert politica.indice_rice(93, 0) == 100.0


def test_indice_rice_dividido_parejo():
    assert politica.indice_rice(50, 50) == 0.0


def test_indice_rice_mayoria_parcial():
    # 93 a favor, 1 en contra -> |93-1|/94*100 = 97.87
    assert politica.indice_rice(93, 1) == 97.87


def test_indice_rice_sin_votos():
    assert politica.indice_rice(0, 0) is None


def test_es_bloque_lla_variantes():
    assert politica.es_bloque_lla("LA LIBERTAD AVANZA")
    assert politica.es_bloque_lla("Libertad Avanza")
    assert politica.es_bloque_lla("  la libertad avanza  ")


def test_es_bloque_lla_excluye_aliados_y_otros():
    assert not politica.es_bloque_lla("Fuerzas del Cielo - Espacio Liberal F.C.E.")
    assert not politica.es_bloque_lla("PRO")
    assert not politica.es_bloque_lla("Unión por la Patria")
    assert not politica.es_bloque_lla("")
