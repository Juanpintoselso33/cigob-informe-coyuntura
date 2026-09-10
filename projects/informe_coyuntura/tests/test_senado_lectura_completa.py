"""No publicar una muestra sesgada cuando falta un acta de la ventana."""
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica


class Corte(datetime):
    @classmethod
    def now(cls):
        return cls(2026, 9, 8, 19)


@pytest.fixture(params=['fetch_cohesion_bloque_senado', 'fetch_alineamiento_senadores_prov'])
def colector(request, monkeypatch):
    monkeypatch.setattr(politica, 'datetime', Corte)
    monkeypatch.setattr(politica, '_hcdn_votaciones_session', lambda: object())
    return getattr(politica, request.param)


def filas_validas():
    return [
        {'nombre': 'A', 'bloque': 'LA LIBERTAD AVANZA', 'provincia': 'Córdoba', 'voto': 'AFIRMATIVO'},
        {'nombre': 'B', 'bloque': 'OTRO', 'provincia': 'Córdoba', 'voto': 'AFIRMATIVO'},
    ]


@pytest.mark.parametrize('fallo', ['red', 'html_sin_votos'])
def test_un_acta_fallida_no_publica_el_promedio_del_resto(colector, monkeypatch, fallo):
    monkeypatch.setattr(politica, '_descubrir_actas_senado', lambda *_: [
        {'id': '1', 'fecha': datetime(2026, 8, 27)},
        {'id': '2', 'fecha': datetime(2026, 8, 28)},
    ])
    def leer(_session, _base, path):
        if path.endswith('/1'):
            return SimpleNamespace(text='votos')
        return None if fallo == 'red' else SimpleNamespace(text='portal sin acta')
    monkeypatch.setattr(politica, '_paced_get', leer)
    monkeypatch.setattr(politica, '_parsear_acta', lambda text: filas_validas() if text == 'votos' else [])
    assert colector() is None


def test_solo_lee_actas_del_intervalo_hasta_el_corte(colector, monkeypatch):
    monkeypatch.setattr(politica, '_descubrir_actas_senado', lambda *_: [
        {'id': 'vieja', 'fecha': datetime(2026, 1, 1)},
        {'id': 'hoy', 'fecha': datetime(2026, 9, 8)},
        {'id': 'futura', 'fecha': datetime(2026, 9, 9)},
    ])
    llamadas = []
    def leer(_session, _base, path):
        llamadas.append(path)
        return SimpleNamespace(text='votos')
    monkeypatch.setattr(politica, '_paced_get', leer)
    monkeypatch.setattr(politica, '_parsear_acta', lambda _: filas_validas())
    resultado = colector()
    assert resultado['valor'] == 100
    assert resultado['fecha_dato'] == '2026-09-08'
    assert llamadas == ['/votaciones/detalleActa/hoy']


@pytest.mark.parametrize('nombre', ['fetch_cohesion_bloque_senado_actas_anio', 'fetch_alineamiento_senadores_actas_anio'])
def test_historia_no_cachea_como_completo_un_anio_con_html_sin_votos(monkeypatch, nombre):
    monkeypatch.setattr(politica, '_hcdn_votaciones_session', lambda: object())
    monkeypatch.setattr(politica, '_descubrir_actas_senado', lambda *_: [
        {'id': '1', 'fecha': datetime(2025, 8, 27)},
        {'id': '2', 'fecha': datetime(2025, 8, 28)},
    ])
    monkeypatch.setattr(politica, '_paced_get', lambda _s, _b, path: SimpleNamespace(text=path))
    monkeypatch.setattr(politica, '_parsear_acta', lambda text: filas_validas() if text.endswith('/1') else [])
    assert getattr(politica, nombre)(2025) is None
