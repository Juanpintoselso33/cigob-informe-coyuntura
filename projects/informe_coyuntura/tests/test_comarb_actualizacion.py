from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import comarb


def sesion(html, error=False):
    def get(url, **kwargs):
        def raise_for_status():
            if error:
                raise requests.HTTPError('503')
        return SimpleNamespace(text=html, content=b'pdf', raise_for_status=raise_for_status)
    return SimpleNamespace(headers={}, get=get)


def test_no_certifica_catalogo_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(comarb, 'CACHE', tmp_path / 'store.json')
    with pytest.raises(ValueError, match='sin gacetillas'):
        comarb.actualizar(sesion('<html>Servicio temporalmente no disponible</html>'))


def test_rechaza_error_http(tmp_path, monkeypatch):
    monkeypatch.setattr(comarb, 'CACHE', tmp_path / 'store.json')
    with pytest.raises(requests.HTTPError):
        comarb.actualizar(sesion('', error=True))


@pytest.mark.parametrize('desvio,acepta', [(0.0, True), (10.0, False)])
def test_nueva_gacetilla_exige_conciliacion(tmp_path, monkeypatch, desvio, acepta):
    monkeypatch.setattr(comarb, 'CACHE', tmp_path / 'store.json')
    monkeypatch.setattr(comarb.time, 'sleep', lambda _: None)
    monkeypatch.setattr(comarb, '_leer_pdf', lambda _: {
        'total': 100., 'var_ia_publicada': 10., 'desvio_suma_pct': desvio})
    s = sesion('<a href="/2026/Gacetilla_Recaudacion_Mensual_08_Ago_2026.pdf">Agosto</a>')
    if acepta:
        assert comarb.actualizar(s)['gacetillas']['2026-08']['total'] == 100.
    else:
        with pytest.raises(ValueError, match='sin validar'):
            comarb.actualizar(s)
        assert '2026-08' not in comarb._cache_leer()['gacetillas']


def test_gacetilla_que_no_es_de_recaudacion_no_exige_validacion(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(comarb, 'CACHE', tmp_path / 'store.json')
    monkeypatch.setattr(comarb.time, 'sleep', lambda _: None)
    monkeypatch.setattr(comarb, '_leer_pdf', lambda _: {
        'total': 100., 'var_ia_publicada': 10., 'desvio_suma_pct': 0.0})
    s = sesion('<a href="/2026/Gacetilla_Recaudaci%C3%B3n_Mensual_08_Ago_2026.pdf">Agosto</a>'
               '<a href="/2026/Gacetilla_Aniversario_09_Sep_2026.pdf">Aniversario</a>')
    store = comarb.actualizar(s)
    assert set(store['gacetillas']) == {'2026-08'}
    assert 'Aniversario' in capsys.readouterr().out


def test_sin_gacetillas_de_recaudacion_no_certifica(tmp_path, monkeypatch):
    monkeypatch.setattr(comarb, 'CACHE', tmp_path / 'store.json')
    with pytest.raises(ValueError, match='sin gacetillas'):
        comarb.actualizar(sesion('<a href="/2026/Gacetilla_Aniversario_09_Sep_2026.pdf">x</a>'))
