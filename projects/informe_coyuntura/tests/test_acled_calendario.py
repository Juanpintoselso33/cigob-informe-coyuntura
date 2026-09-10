from datetime import date
from pathlib import Path
import json,sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import acled_calendario as a
import politica,gestion,descargar_series


def store(semana='2026-08-29'):
    datos={f'{y}-{m:02d}':100 for y in range(2023,2027) for m in range(1,13)
           if f'{y}-{m:02d}' <= '2026-08'}
    return {'_meta':{'hasta_semana':semana,'actualizado':'2026-09-01'},
            'mensual_nacional':datos,'mensual':datos.copy()}


def test_sabado_es_inicio_y_agosto_esta_cubierto_hasta_el_viernes():
    r=a.serie_12m(store(), 'mensual_nacional',date(2026,9,8))
    assert r['cobertura_hasta']=='2026-09-04'
    assert r['puntos'][-1]=={'fecha':'2026-08-01','acum_12m':1200,'variacion':0.0}


def test_la_semana_anterior_todavia_no_cierra_agosto():
    r=a.serie_12m(store('2026-08-22'),'mensual_nacional',date(2026,9,8))
    assert r['puntos'][-1]['fecha']=='2026-07-01'


@pytest.mark.parametrize('defecto',['dia','futura','base','hueco','negativo','nan','fraccion'])
def test_rechaza_cortes_y_calendarios_que_no_acreditan_una_ventana(defecto):
    s=store()
    if defecto=='dia':s['_meta']['hasta_semana']='2026-08-30'
    if defecto=='futura':s['_meta']['hasta_semana']='2026-09-05'
    if defecto=='base':del s['mensual_nacional']['2023-01']
    if defecto=='hueco':del s['mensual_nacional']['2025-03']
    if defecto=='negativo':s['mensual_nacional']['2025-03']=-1
    if defecto=='nan':s['mensual_nacional']['2025-03']=float('nan')
    if defecto=='fraccion':s['mensual_nacional']['2025-03']=1.5
    with pytest.raises(ValueError):a.serie_12m(s,'mensual_nacional',date(2026,9,8))


@pytest.mark.parametrize('descarga_ok',[True,False])
def test_tarjeta_e_historia_comparten_corte_y_cache(monkeypatch,tmp_path,descarga_ok):
    s=store();p=tmp_path/'acled.json';p.write_text(json.dumps(s))
    monkeypatch.setattr(gestion,'PROTESTAS_STORE_PATH',p)
    monkeypatch.setattr(gestion,'actualizar_protestas_caba',lambda:s if descarga_ok else None)
    card=politica.fetch_conflictividad_nacional()
    serie=descargar_series.fetch_conflictividad_nacional_mensual()
    assert [card['fecha_dato'],card['valor']]==serie[-1]
    assert card['fecha_dato']=='2026-08-01'
    assert card['obtenido_en']=='2026-09-01'
    if not descarga_ok:assert card['desactualizado'] is True
    caba=gestion.fetch_protestas_caba()
    assert caba['fecha_dato']=='2026-08-01'
    assert caba['valor']==1200
    assert descargar_series.fetch_protestas_serie()[-1]==['2026-08-01',100]


def test_main_no_renueva_el_sello_de_la_copia_local(monkeypatch):
    for nombre in dir(politica):
        if nombre.startswith('fetch_'):monkeypatch.setattr(politica,nombre,lambda *a,**kw:None)
    for nombre in ('detectar_novedades_judiciales','detectar_novedades_empresarias'):
        monkeypatch.setattr(politica,nombre,lambda:{})
    monkeypatch.setattr(politica,'fetch_conflictividad_nacional',lambda:{
        'valor':-24.1,'desactualizado':True,'obtenido_en':'2026-09-01'})
    monkeypatch.setattr(politica,'load_cache',lambda:{'indicadores':{}})
    guardados=[];monkeypatch.setattr(politica,'save_cache',guardados.append)
    with pytest.raises(SystemExit) as salida:politica.main()
    assert salida.value.code==2
    assert guardados[0]['indicadores']['conflictividad_nacional']['obtenido_en']=='2026-09-01'
