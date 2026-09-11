import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ica
import macro


def test_catalogo_ordena_por_fecha_y_resuelve_relativos():
    html = '<a href="../../ftp/cuadros/economia/ica_cuadros_20_12_25.xls">anterior</a><a href="/ftp/cuadros/economia/ica_cuadros_20_01_26.xls">nuevo</a>'
    assert ica.enlaces(html)[0] == 'https://www.indec.gob.ar/ftp/cuadros/economia/ica_cuadros_20_01_26.xls'


def test_parser_omite_futuros_y_no_toma_acumulados(monkeypatch):
    rows = [['Cuadro 1. Intercambio comercial argentino'],
            ['Período', '', 'Exportaciones', '', 'Importaciones', ''],
            ['', '', '2026e', '2025*', '2026*', '2025*'],
            ['', 'Total anual', '///', 12000, '///', 11000]]
    for m in ica.MESES:
        actual = ica.MESES[m] <= 7
        rows.append(['', m.title(), 8853.859 if actual else '', 7000.,
                     6738.676 if actual else '', 6000.])
    hoja = SimpleNamespace(nrows=len(rows), cell_value=lambda r,c:rows[r][c],row_values=lambda r:rows[r])
    monkeypatch.setattr(ica.xlrd,'open_workbook',lambda **kw:SimpleNamespace(sheets=lambda:[hoja]))
    puntos=ica.parsear(b'')
    assert len(puntos)==19
    assert max(puntos)=='2026-07-01'
    assert puntos['2026-07-01']==[8853.859,6738.676]


def test_fallo_del_catalogo_no_borra_julio_del_store(tmp_path, monkeypatch):
    store=tmp_path/'ica.json'
    store.write_text(json.dumps({'url':'https://www.indec.gob.ar/cuadro.xls', 'consultado':'2026-08-20T12:00:00-03:00',
        'mensual':{'2026-07-01':[8853.859,6738.676]}}))
    monkeypatch.setattr(ica,'STORE',store)
    def fallo(*a,**kw):raise requests.ConnectionError('fuente no disponible')
    monkeypatch.setattr(ica.requests,'get',fallo)
    r=ica.completar([['2026-06-01',9111.8]],[['2026-06-01',6876.6]])
    assert r['puntos'][0][0]=='2026-07-01'
    assert r['advertencia'] and not r['consulta_oficial_exitosa']
    assert r['obtenido_en']=='2026-08-20T12:00:00-03:00'


def test_macro_no_resella_el_cuadro_cacheado_ni_lo_cuenta_como_fresco(monkeypatch):
    for nombre in dir(macro):
        if nombre.startswith('fetch_'):
            monkeypatch.setattr(macro,nombre,lambda:None)
    fecha='2026-08-20T12:00:00-03:00'
    monkeypatch.setattr(macro,'fetch_saldo_comercial_12m',lambda:{
        'valor':23731.,'fecha_dato':'2026-07-01','desactualizado':True,'obtenido_en':fecha})
    monkeypatch.setattr(macro,'actualizar_patentamientos_comerciales',lambda:None)
    monkeypatch.setattr(macro,'load_cache',lambda:{'indicadores':{}})
    guardado={}
    monkeypatch.setattr(macro,'save_cache',lambda p:guardado.update(p))
    with pytest.raises(SystemExit) as fin:
        macro.main()
    assert fin.value.code==2
    assert guardado['indicadores']['saldo_comercial_12m']['obtenido_en']==fecha


def test_pipeline_persiste_el_cuadro_entre_runners():
    root=Path(__file__).resolve().parents[3]
    workflow=(root/'.github/workflows/data-pipeline.yml').read_text()
    commit=workflow[workflow.index('git add '):]
    assert 'projects/informe_coyuntura/data/macro/ica_mensual.json' in commit


def test_ventana_no_compensa_un_mes_ausente_con_uno_mas_viejo():
    with pytest.raises(ValueError,match='consecutivos'):
        ica.ventana([['2026-07-01',1,1],['2026-05-01',1,1]],2)


def test_tarjeta_acumula_doce_y_compara_con_los_doce_anteriores(monkeypatch):
    puntos=[]
    for n in range(24):
        mes=2026*12+6-n
        puntos.append([f'{mes//12}-{mes%12+1:02}-01',100.25 if n<12 else 90.,80.125 if n<12 else 85.])
    monkeypatch.setattr(macro,'_ica_mensual',lambda:{'puntos':puntos,'url':'https://www.indec.gob.ar/cuadro.xls',
        'advertencia':None,'consulta_oficial_exitosa':True})
    c=macro.fetch_saldo_comercial_12m()
    assert c['valor']==round(12*(100.25-80.125),0)
    assert c['fecha_dato']=='2026-07-01'
    assert c['expo_delta_12m']==123
    assert c['impo_delta_12m']==-58


def test_fallo_del_catalogo_no_adelanta_la_fecha_con_la_api(tmp_path, monkeypatch):
    store = tmp_path / 'ica.json'
    store.write_text(json.dumps({'url': 'u', 'consultado': '2026-08-20T12:00:00-03:00',
                                 'mensual': {'2026-07-01': [8853.859, 6738.676]}}))
    monkeypatch.setattr(ica, 'STORE', store)
    def fallo(*a, **kw): raise requests.ConnectionError('fuente no disponible')
    monkeypatch.setattr(ica.requests, 'get', fallo)
    r = ica.completar([['2026-08-01', 9000.], ['2026-06-01', 9111.8]],
                      [['2026-08-01', 6000.], ['2026-06-01', 6876.6]])
    assert not r['consulta_oficial_exitosa']
    assert [p[0] for p in r['puntos']] == ['2026-07-01', '2026-06-01']


def test_planilla_recortada_conserva_el_cuadro_validado(tmp_path, monkeypatch):
    store = tmp_path / 'ica.json'
    store.write_text(json.dumps({'url': 'u', 'consultado': '2026-08-20T12:00:00-03:00',
                                 'mensual': {'2026-07-01': [8853.859, 6738.676]}}))
    monkeypatch.setattr(ica, 'STORE', store)
    monkeypatch.setattr(ica.requests, 'get', lambda *a, **kw: SimpleNamespace(
        text='<a href="/ftp/cuadros/economia/ica_cuadros_20_08_26.xls">x</a>', content=b'',
        raise_for_status=lambda: None))
    def recortada(contenido): raise IndexError('list index out of range')
    monkeypatch.setattr(ica, 'parsear', recortada)
    r = ica.completar([], [])
    assert r['puntos'][0][0] == '2026-07-01' and r['advertencia'] and not r['consulta_oficial_exitosa']
    assert json.loads(store.read_text())['mensual'] == {'2026-07-01': [8853.859, 6738.676]}


def test_parser_exige_anios_coherentes_en_importaciones(monkeypatch):
    rows = [['Cuadro 1. Intercambio comercial argentino'],
            ['Período', '', 'Exportaciones', '', 'Importaciones', ''],
            ['', '', '2026e', '2025*', '2025*', '2026*']]
    for m in ica.MESES:
        rows.append(['', m.title(), 1., 1., 1., 1.])
    hoja = SimpleNamespace(nrows=len(rows), cell_value=lambda r, c: rows[r][c], row_values=lambda r: rows[r])
    monkeypatch.setattr(ica.xlrd, 'open_workbook', lambda **kw: SimpleNamespace(sheets=lambda: [hoja]))
    with pytest.raises(ValueError, match='importaciones'):
        ica.parsear(b'')
