import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica


def meses():
    return [(f'2025-{m:02}', 100) for m in range(1, 13)] + [('2026-01', 100)]


def test_ventana_calendario_cruza_anio_y_preserva_fracciones():
    serie = meses()
    serie[-1] = ('2026-01', 100.5)
    assert politica._jornadas_acumuladas_12m(serie) == [
        ['2025-12-01', 1200], ['2026-01-01', 1200.5]]


@pytest.mark.parametrize('alteracion', ['hueco', 'duplicado', 'negativo', 'nan', 'bool'])
def test_rechaza_doce_filas_que_no_forman_doce_meses_validos(alteracion):
    serie = meses()
    if alteracion == 'hueco':
        del serie[5]
    elif alteracion == 'duplicado':
        serie[5] = serie[4]
    else:
        serie[5] = (serie[5][0], {'negativo': -1, 'nan': float('nan'), 'bool': True}[alteracion])
    with pytest.raises(ValueError):
        politica._jornadas_acumuladas_12m(serie)
