from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion
import ica
import descargar_series


def preparar(monkeypatch, vigente=True):
    series = {
        gestion.DEX_ID: {'2026-06': 100., '2026-07': 200., '2026-08': 300.},
        gestion.DIM_ID: {'2026-06': 50., '2026-07': 80., '2026-08': 90.},
        gestion.EXPO_ICA_ID: {'2026-06': 100.},
        gestion.IMPO_ICA_ID: {'2026-06': 50.},
    }
    monkeypatch.setattr(gestion, '_indec_nivel_mensual', lambda id, **kw: series[id])
    monkeypatch.setattr(gestion, '_tc_mayorista_promedio_por_mes',
                        lambda **kw: {'2026-06': 10., '2026-07': 20., '2026-08': 20.})
    monkeypatch.setattr(ica, 'completar', lambda ex, im: {
        'puntos': [['2026-07-01', 100., 100.], ['2026-06-01', 100., 50.]],
        'consulta_oficial_exitosa': vigente, 'url': 'https://www.indec.gob.ar/cuadro.xls',
        'obtenido_en': '2026-09-07T10:00:00-03:00',
        'advertencia': None if vigente else 'fuente no disponible'})


def test_completa_julio_sin_mezclar_recaudacion_agosto(monkeypatch):
    preparar(monkeypatch)
    card = gestion.fetch_apertura_comercial()
    assert card['fecha_dato'] == '2026-07-01'
    assert card['valor'] == 7.0  # (200 + 80) / 20 / (100 + 100) * 100
    assert descargar_series.fetch_alicuota_serie()[-1] == ['2026-07-01', card['valor']]
    assert card['desactualizado'] is False


def test_fallo_original_conserva_periodo_y_declara_cache(monkeypatch):
    preparar(monkeypatch, vigente=False)
    card = gestion.fetch_apertura_comercial()
    assert card['fecha_dato'] == '2026-07-01'
    assert card['desactualizado'] is True
    assert card['advertencia_fuente'] == 'fuente no disponible'
    assert gestion._sellar(card)['obtenido_en'] == '2026-09-07T10:00:00-03:00'


def test_sin_tipo_cambio_comun_no_inventa_cero(monkeypatch):
    preparar(monkeypatch)
    monkeypatch.setattr(gestion, '_tc_mayorista_promedio_por_mes', lambda **kw: {})
    assert gestion.fetch_apertura_comercial() is None
    assert descargar_series.fetch_alicuota_serie() == []
