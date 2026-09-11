from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publicar


def test_desglose_expone_fecha_y_cache_de_cada_camara():
    texto = publicar._politica_input_txt('cohesion_bloque', {
        'valor': 100., 'componentes': {
            'diputados': {'valor': 100., 'fecha_dato': '2026-06-24', 'n_actas': 13,
                          'desactualizado': True},
            'senado': {'valor': 100., 'fecha_dato': '2026-08-27', 'n_actas': 16,
                       'desactualizado': False}}})
    assert '2026-06-24 · dato conservado en caché' in texto
    assert '2026-08-27' in texto
    assert texto.count('conservado en caché') == 1
    assert 'peso 65%' in texto and 'peso 35%' in texto


def test_una_camara_explica_renormalizacion():
    texto = publicar._politica_input_txt('cohesion_bloque', {
        'valor': 99., 'componentes': {'senado': {'valor': 99., 'n_actas': 2}}})
    assert 'peso 35%' not in texto
    assert 'peso se renormaliza al 100%' in texto
    assert 'última acta sin fecha' in texto
