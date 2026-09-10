"""Cobertura mensual, moneda y tasas directas en resultados de Finanzas."""
import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import colocaciones_complementarias as cc


def html(tasa='29,75%', monto='$ 6.085.000', precio='$ 1.217,00'):
    # Fila del resultado oficial 27-ago; otra tabla CER deliberadamente tiene TIREA.
    return f'''<p>27 de agosto de 2026. Montos expresados en millones.</p>
    <table><tr><th>Instrumentos a Tasa Fija</th><th>Valor Efectivo Adjudicado (*)</th><th>Precio/TEM de corte</th><th>TIREA</th></tr>
    <tr><td>LETRA CAPITALIZABLE EN PESOS (S30N6 - reapertura)</td><td>{monto}</td><td>{precio}</td><td>{tasa}</td></tr></table>
    <table><tr><th>Instrumentos ajustados por CER</th><th>Valor Efectivo Adjudicado</th><th>TIREA</th></tr>
    <tr><td>CER</td><td>$ 834.350</td><td>6,25%</td></tr></table>'''


def registro():
    return {'resultado':'resultado','llamado':'llamado','fecha':'2026-08-27',
            'liquidacion':'2026-08-31','filas_fijas':1}


def test_tasa_publicada_y_monto_sin_mezclar_cer():
    filas=cc.parsear_resultado(html(),registro())
    assert len(filas)==1
    assert filas[0]['tirea']==29.75
    assert filas[0]['valor_efectivo']==6085000
    assert filas[0]['precio_corte']==1217


def test_precio_tem_no_se_confunde_con_precio_de_corte():
    fila=cc.parsear_resultado(html('30,60%','$ 2.379.233','2,25% (**)'),registro())[0]
    assert fila['precio_corte'] is None
    assert fila['tem_corte']==2.25


@pytest.mark.parametrize('cambio',[{'filas_fijas':2},{'fecha':'2026-08-12'}])
def test_rechaza_cambios_de_cobertura_o_fecha(cambio):
    with pytest.raises(ValueError):cc.parsear_resultado(html(),{**registro(),**cambio})


def test_no_incorpora_medio_mes_y_no_muta_serie(tmp_path):
    p=tmp_path/'fuentes.json'
    r=registro();r2={**r,'resultado':'falla'}
    p.write_text(json.dumps({'meses':{'2026-08':{'cobertura_verificada':True,'licitaciones':[r,r2]}}}))
    def get(url,**kw):
        if url=='falla':raise ValueError('fuente caída')
        t='La liquidación se efectuará el 31 de agosto de 2026.' if url=='llamado' else html()
        return SimpleNamespace(text=t,raise_for_status=lambda:None)
    serie={'2026-07':(.26,10,1,[])}
    with pytest.raises(ValueError):cc.completar(serie,manifiesto=p,get=get,hoy=date(2026,9,8))
    assert list(serie)==['2026-07']


def test_mes_cerrado_y_peso_efectivo(tmp_path):
    p=tmp_path/'fuentes.json';r=registro()
    p.write_text(json.dumps({'meses':{'2026-08':{'cobertura_verificada':True,'licitaciones':[r]}}}))
    def get(url,**kw):
        return SimpleNamespace(text=('Liquidación el 31 de agosto de 2026.' if url=='llamado' else html()),raise_for_status=lambda:None)
    assert cc.completar({},manifiesto=p,get=get,hoy=date(2026,8,31))=={}
    out=cc.completar({},manifiesto=p,get=get,hoy=date(2026,9,8))
    assert out['2026-08'][0]==pytest.approx(.2975)
    assert out['2026-08'][1:3]==(6085000,1)


def test_planilla_que_ya_cubre_el_mes_no_se_duplica(tmp_path):
    p=tmp_path/'fuentes.json'
    p.write_text(json.dumps({'meses':{'2026-08':{}}}))
    serie={'2026-08':(.3,100,2,[])}
    assert cc.completar(serie,manifiesto=p,get=lambda *a,**k:pytest.fail('No debe descargar'),hoy=date(2026,9,8))==serie


def test_cache_de_dos_anios_no_impide_pedir_cuatro(monkeypatch):
    import macro
    monkeypatch.setattr(macro,'_COLOC_MEMO',{2:{'2026-07':(.26,1,1,[])}})
    monkeypatch.setattr(macro,'_colocaciones_urls',lambda:{})
    # Debe intentar recuperar la ventana pedida, nunca devolver la corta.
    with pytest.raises(ValueError,match='planillas'):
        macro._tirea_mensual(anios=4)
    assert '2026-07' in macro._tirea_mensual(anios=2)
