"""Omisiones del catálogo, fechas y fallos de lectura de leyes originales."""
import json
from datetime import date
import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica
import descargar_series


class Hoy(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 8)


@pytest.fixture
def fuentes(monkeypatch, tmp_path):
    leyes = {
        'SANTA FE': {'fecha': '2025-01-01', 'fuente': 'https://test/sf',
                     'comprobar_textos': ['Ley 14386', '93.- Adhiérese', 'vigencia el 1 de enero de 2025']},
        'CABA': {'fecha': '2026-05-28', 'fuente': 'https://test/caba',
                 'comprobar_textos': ['LEY 6949', 'Ciudad Autónoma de Buenos Aires adhiere']},
    }
    p=tmp_path/'complementarias.json';p.write_text(json.dumps(leyes))
    monkeypatch.setattr(politica, 'ADHESION_COMPLEMENTARIAS_PATH', p)
    monkeypatch.setattr(politica, 'date', Hoy)
    monkeypatch.setattr(descargar_series, 'date', Hoy)
    contenidos={
        politica.MAGYP_RIGI_URL: '<table><tr><td>CATAMARCA</td><td>Ley</td></tr></table>',
        'https://test/sf': '<p>Ley 14386</p><p>93.- Adhiérese</p><p>vigencia el 1 de enero de 2025</p>',
        'https://test/caba': '<h2>LEY 6949</h2><p>Ciudad Autónoma de Buenos Aires\n adhiere</p>',
    }
    def get(url, **kw):
        return Mock(status_code=200, text=contenidos[url], raise_for_status=lambda: None)
    monkeypatch.setattr(politica.requests, 'get', get)
    return contenidos,p


def test_omite_catalogo_pero_leyes_entran_y_se_deduplican(fuentes):
    contenidos,_=fuentes
    r=politica.fetch_adhesion_reformas_provincial()
    assert r['valor']==12.5
    assert r['jurisdicciones']==['CABA','CATAMARCA','SANTA FE']
    contenidos[politica.MAGYP_RIGI_URL]+='<table><tr><td>CIUDAD AUTÓNOMA DE BUENOS AIRES</td><td>Ley 6949</td></tr><tr><td>SANTA FE</td><td>Ley 14386</td></tr></table>'
    assert politica.fetch_adhesion_reformas_provincial()['n_provincias']==3


@pytest.mark.parametrize('url', ['https://test/sf','https://test/caba'])
def test_html_200_sin_ley_no_publica_conteo_parcial(fuentes,url):
    fuentes[0][url]='<html>Servicio temporalmente no disponible</html>'
    assert politica.fetch_adhesion_reformas_provincial() is None
    assert descargar_series.fetch_adhesion_reformas_provincial_serie()==[]


def test_error_red_complementaria_no_es_baja(fuentes,monkeypatch):
    original=politica.requests.get
    def get(url,**kw):
        if url=='https://test/sf':raise politica.requests.RequestException('sin conexión')
        return original(url,**kw)
    monkeypatch.setattr(politica.requests,'get',get)
    assert politica.fetch_adhesion_reformas_provincial() is None


def test_fechas_historicas_no_anticipan_la_adhesion(fuentes,monkeypatch,tmp_path):
    p=tmp_path/'base.json';p.write_text(json.dumps({'CATAMARCA':{'fecha':'2024-09-27'}}))
    monkeypatch.setattr(descargar_series,'ADHESION_REFORMAS_FECHAS_PATH',p)
    serie=dict(descargar_series.fetch_adhesion_reformas_provincial_serie())
    assert serie['2024-12-31']==4.2  # Santa Fe no rige hasta el 1 de enero.
    assert serie['2025-01-31']==8.3
    assert serie['2026-04-30']==8.3
    assert serie['2026-05-31']==12.5
    assert serie['2026-08-31']==politica.fetch_adhesion_reformas_provincial()['valor']


def test_no_cuenta_adhesion_futura(fuentes):
    _,p=fuentes;d=json.loads(p.read_text());d['CABA']['fecha']='2027-01-01';p.write_text(json.dumps(d))
    assert politica._rigi_complementarias_verificadas()=={'SANTA FE'}
