import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica
import aviso_slack
from cotejo_manual import revisar_fechas_sancion, avisos

@pytest.mark.parametrize('fecha', [None, '', 'NA', '2026-02-30', '20260910'])
def test_fecha_invalida_llega_al_aviso_con_registro_y_fuente(fecha, capsys):
    revisar_fechas_sancion([{'PROYECTO_ID':'HCDN1', 'SANCION_DEFINITIVA':fecha}], 'https://datos.hcdn.gob.ar')
    log=capsys.readouterr().err
    for parser in (aviso_slack.analizar, aviso_slack.causas):
        mensajes=parser(log+log)
        assert len(mensajes)==1
        assert 'HCDN1' in mensajes[0] and 'https://datos.hcdn.gob.ar' in mensajes[0]
        assert 'no usar fecha de consulta' in mensajes[0]

def test_fechas_validas_no_avisan(capsys):
    revisar_fechas_sancion([{'SANCION_DEFINITIVA':'2026-02-27T00:00:00'}], 'fuente')
    assert avisos(capsys.readouterr().err)==[]

def test_colector_emite_alerta_sin_alterar_datos(monkeypatch, capsys):
    filas=[{'PROYECTO_ID':'1', 'SANCION_DEFINITIVA':'NA'}, {'PROYECTO_ID':'2','SANCION_DEFINITIVA':'2025-02-20'}]
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a, **kw: filas)
    assert politica._leyes_sancionadas_ids() == {'1','2'}
    assert len(avisos(capsys.readouterr().err))==1
    assert filas[0]['SANCION_DEFINITIVA']=='NA'

def test_degradado_envia_alarma_por_transporte_existente(tmp_path,monkeypatch,capsys):
    revisar_fechas_sancion([{'PROYECTO_ID':'HCDN1'}], 'https://datos.hcdn.gob.ar')
    p=tmp_path/'colectores.log';p.write_text(capsys.readouterr().err)
    enviados=[]
    monkeypatch.setattr(aviso_slack,'publicar',lambda cuerpo: enviados.append(cuerpo) or 0)
    monkeypatch.setattr(sys,'argv',['aviso_slack','degradado','--log',str(p),'--url','https://github.com/run/1'])
    assert aviso_slack.main()==0
    assert len(enviados)==1 and 'HCDN1' in enviados[0] and 'https://github.com/run/1' in enviados[0]

def test_log_malformado_no_rompe_y_menciones_no_notifican(capsys):
    assert avisos('[COTEJO_MANUAL] no es json\n[COTEJO_MANUAL] []')==[]
    revisar_fechas_sancion([{'PROYECTO_ID':'<!channel>'}], 'fuente')
    assert '<!channel>' not in avisos(capsys.readouterr().err)[0]

def test_fallo_con_muchas_causas_no_oculta_cotejo(tmp_path,monkeypatch,capsys):
    revisar_fechas_sancion([{'PROYECTO_ID':'HCDN1'}], 'https://datos.hcdn.gob.ar')
    p=tmp_path/'log';p.write_text(capsys.readouterr().err + '\n'.join(f'FAILED tests/test_x.py::test_{n} - error' for n in range(8)))
    enviados=[]
    monkeypatch.setattr(aviso_slack,'publicar',lambda cuerpo: enviados.append(cuerpo) or 0)
    monkeypatch.setattr(sys,'argv',['aviso_slack','fallo','--log',str(p),'--url','https://github.com/run/1'])
    assert aviso_slack.main()==0
    assert 'Cotejo manual' in enviados[0] and 'HCDN1' in enviados[0]


# ── Correcciones documentadas y actas sin fecha ──────────────────────────────
import json
from datetime import date, datetime, timedelta
import cotejo_manual


class Hoy(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 10)


def _correcciones(tmp_path, monkeypatch, correcciones):
    p = tmp_path / 'sanciones.json'
    p.write_text(json.dumps({'revisado_en': '2026-09-10', 'correcciones': correcciones}), encoding='utf-8')
    monkeypatch.setattr(cotejo_manual, 'CORRECCIONES_SANCION', p)


def _actas(tmp_path, monkeypatch, actas):
    p = tmp_path / 'actas.json'
    p.write_text(json.dumps({'revisado_en': '2026-09-10', 'actas': actas}), encoding='utf-8')
    monkeypatch.setattr(cotejo_manual, 'ACTAS_VERIFICADAS', p)


def test_sancion_na_no_entra_al_conteo_y_avisa(tmp_path, monkeypatch, capsys):
    _correcciones(tmp_path, monkeypatch, [])
    monkeypatch.setattr(politica, 'date', Hoy)
    monkeypatch.setattr(politica, '_leyes_sancionadas_complementarias', lambda: [])
    filas = [{'LEY': 1, 'PROYECTO_ID': 'HCDN1', 'SANCION_DEFINITIVA': 'NA'},
             {'LEY': 2, 'SANCION_DEFINITIVA': '2026-02-20T00:00:00'}]
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a, **kw: filas)
    assert politica.fetch_produccion_legislativa() is None
    mensajes = avisos(capsys.readouterr().err)
    assert len(mensajes) == 1
    assert 'HCDN1' in mensajes[0] and 'sanciones_fechas_verificadas' in mensajes[0]


def test_correccion_documentada_entra_al_conteo_sin_aviso(tmp_path, monkeypatch, capsys):
    _correcciones(tmp_path, monkeypatch, [{'PROYECTO_ID': 'hcdn1', 'SANCION_DEFINITIVA': '2026-02-20',
                                           'fuente': 'https://www.boletinoficial.gob.ar/detalle/x'}])
    monkeypatch.setattr(politica, 'date', Hoy)
    monkeypatch.setattr(politica, '_leyes_sancionadas_complementarias', lambda: [])
    filas = [{'LEY': 1, 'PROYECTO_ID': 'HCDN1', 'SANCION_DEFINITIVA': 'NA'},
             {'LEY': 2, 'PROYECTO_ID': 'HCDN2', 'SANCION_DEFINITIVA': '2026-03-05T00:00:00'}]
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a, **kw: filas)
    serie = politica.produccion_legislativa_serie()
    assert serie['2026-08'] == 2
    assert politica._leyes_sancionadas_ids('2026-02-28') == {'HCDN1'}
    assert avisos(capsys.readouterr().err) == []
    assert filas[0]['SANCION_DEFINITIVA'] == 'NA'


def test_fecha_valida_del_catalogo_no_se_reescribe(tmp_path, monkeypatch):
    _correcciones(tmp_path, monkeypatch, [{'LEY': '27700', 'SANCION_DEFINITIVA': '2026-01-01', 'fuente': 'x'}])
    filas = cotejo_manual.aplicar_correcciones_sancion(
        [{'LEY': 27700, 'SANCION_DEFINITIVA': '2026-02-20T00:00:00'}])
    assert filas[0]['SANCION_DEFINITIVA'] == '2026-02-20T00:00:00'


@pytest.mark.parametrize('mala', [
    [{'PROYECTO_ID': 'HCDN1', 'SANCION_DEFINITIVA': '2026-02-20'}],
    [{'PROYECTO_ID': 'HCDN1', 'SANCION_DEFINITIVA': '20/02/2026', 'fuente': 'x'}],
    [{'SANCION_DEFINITIVA': '2026-02-20', 'fuente': 'x'}],
])
def test_una_correccion_sin_fuente_o_sin_fecha_canonica_no_se_acepta(tmp_path, monkeypatch, mala):
    _correcciones(tmp_path, monkeypatch, mala)
    with pytest.raises(ValueError):
        cotejo_manual.aplicar_correcciones_sancion([{'SANCION_DEFINITIVA': 'NA'}])


def test_acta_sin_fecha_avisa_y_no_acredita(tmp_path, monkeypatch, capsys):
    _actas(tmp_path, monkeypatch, {})
    monkeypatch.setattr(politica, '_diputados_acta_pdf', lambda s, id: b'pdf')
    monkeypatch.setattr(politica, '_diputados_acta_fecha', lambda c: None)
    monkeypatch.setattr(politica, '_guardar_cache_cohesion_diputados', lambda c: None)
    cache = {}
    assert politica._acta_diputados_cacheada(object(), 6001, cache) is politica._ACTA_FALLO
    assert cache == {}
    mensajes = avisos(capsys.readouterr().err)
    assert len(mensajes) == 1
    assert 'acta 6001' in mensajes[0] and '/pdf/acta/6001' in mensajes[0]


def test_acta_con_fecha_documentada_se_acredita_sin_aviso(tmp_path, monkeypatch, capsys):
    _actas(tmp_path, monkeypatch, {'6001': {'fecha': '2026-06-24',
                                            'fuente': 'https://votaciones.hcdn.gob.ar/votacion/6001'}})
    monkeypatch.setattr(politica, '_diputados_acta_pdf', lambda s, id: b'pdf')
    monkeypatch.setattr(politica, '_diputados_acta_fecha', lambda c: None)
    monkeypatch.setattr(politica, '_parsear_acta_diputados_pdf', lambda c: [
        {'nombre': 'X', 'bloque': 'LA LIBERTAD AVANZA', 'voto': 'AFIRMATIVO'},
        {'nombre': 'Y', 'bloque': 'LA LIBERTAD AVANZA', 'voto': 'NEGATIVO'}])
    guardado = {}
    monkeypatch.setattr(politica, '_guardar_cache_cohesion_diputados', lambda c: guardado.update(c))
    cache = {}
    entrada = politica._acta_diputados_cacheada(object(), 6001, cache)
    assert entrada['fecha'] == datetime(2026, 6, 24)
    assert guardado['6001']['fecha'] == '2026-06-24'
    assert avisos(capsys.readouterr().err) == []


# ── Conciliación judicial: avisa antes de que G2b corte la publicación ───────
@pytest.mark.parametrize('dias_atras, avisa', [(3, False), (10, True), (20, True)])
def test_conciliacion_judicial_avisa_antes_de_vencer(monkeypatch, capsys, dias_atras, avisa):
    corte = (date.today() - timedelta(days=dias_atras)).isoformat()
    meta = {'total_cargos': 955, 'vacantes_padron': 345, 'fecha_padron': '2026-06-05',
            'composicion': {'Titular': 500, 'Subrogante': 100, 'Sin subrogante designado': 10},
            'fecha_corte': corte, 'cargos_con_juez': 705, 'ancla_corregida': 609,
            'correcciones_padron': 1, 'designaciones': 100, 'renuncias': 3, 'otras_bajas': 1,
            'limites': ['límite documentado']}
    monkeypatch.setattr(politica, 'cobertura_judicial_serie', lambda: ({'2026-08': 73.82}, meta))
    card = politica.fetch_cobertura_judicial()
    assert card['valor'] == 73.82 and card['obtenido_en'] == corte
    mensajes = avisos(capsys.readouterr().err)
    assert bool(mensajes) is avisa
    if avisa:
        assert corte in mensajes[0] and 'revisado_hasta' in mensajes[0]
        assert ('venció' if dias_atras > 14 else 'vence en') in mensajes[0]
