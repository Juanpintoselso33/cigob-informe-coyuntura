"""Un benchmark rezagado no recorta la trayectoria propia del monitor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publicar


def test_historia_sigue_hasta_agosto_aunque_panel_termine_en_mayo(monkeypatch):
    monkeypatch.setattr(publicar, '_cargar_validacion', lambda: {
        'serie_itvc': {'2026-05': 94.1, '2026-08': 94.2},
        'series_dimensiones': {},
    })
    bloque = {'dimensiones': {'ingresos': {}}, 'validacion': {'pares': [['2026-05', 94.1, 1.]]}}
    publicar._series_dimensiones(bloque, 'itvc', base100=True)
    assert bloque['serie_mensual'] == [['2026-05', 94.1], ['2026-08', 94.2]]
    assert bloque['validacion']['pares'] == [['2026-05', 94.1, 1.]]
