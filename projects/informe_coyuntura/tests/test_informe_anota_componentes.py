"""El recálculo del índice actualiza también los aportes de sus tarjetas."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import generar_informe


@pytest.mark.parametrize('cinturon,clave,indicador,valor', [
    ('macro', 'itcm', 'costo_financiamiento_tesoro', 7.25),
    ('gestion', 'itcg', 'cepo_mulc', 5.35),
    ('politica', 'itcp', 'ratio_dnu', 2.19),
])
def test_recalculo_reemplaza_aporte_obsoleto(cinturon, clave, indicador, valor):
    datos = {indicador: {'valor': valor, 'en_indice': False,
                        f'puntaje_{clave}': -999, 'peso_efectivo': -1}}
    _, resultado = generar_informe._recalcular_indice(cinturon, datos, 0)
    assert resultado is not None
    tarjeta = datos[indicador]
    assert tarjeta['en_indice'] is True
    assert tarjeta['peso_efectivo'] == 1
    assert tarjeta[f'puntaje_{clave}'] == resultado['valor']
