import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion

def respuesta(monkeypatch, ccl=1588.7, fecha='2026-09-08T01:00:00Z'):
    filas=[dict(casa='contadoconliqui',venta=ccl,fechaActualizacion=fecha),
           dict(casa='mayorista',venta=1508,fechaActualizacion='2026-09-08T10:50:00Z')]
    monkeypatch.setattr(gestion.requests,'get',lambda *a,**k:SimpleNamespace(raise_for_status=lambda:None,json=lambda:filas))

def test_fecha_de_la_pata_mas_antigua_en_argentina(monkeypatch):
    respuesta(monkeypatch)
    r=gestion.fetch_cepo_mulc()
    assert r['fecha_dato']=='2026-09-07'
    assert r['valor']==5.35
    assert r['cotizaciones']['ccl']['actualizado_en']=='2026-09-07T22:00:00-03:00'

@pytest.mark.parametrize('fecha',['', 'malformada', '2026-09-08T10:00:00'])
def test_fecha_no_verificable_no_se_reemplaza_por_hoy(monkeypatch,fecha):
    respuesta(monkeypatch,fecha=fecha)
    assert gestion.fetch_cepo_mulc() is None

@pytest.mark.parametrize('valor',[float('nan'),float('inf'),-1,0])
def test_precio_invalido_no_produce_brecha(monkeypatch,valor):
    respuesta(monkeypatch,ccl=valor)
    assert gestion.fetch_cepo_mulc() is None
