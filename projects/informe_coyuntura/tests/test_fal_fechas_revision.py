import json
from datetime import date
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import gestion


class Hoy(date):
    dia=8
    @classmethod
    def today(cls):return cls(2026,9,cls.dia)


@pytest.fixture
def registro(tmp_path,monkeypatch):
    data=json.loads(gestion.FAL_HITOS_PATH.read_text())
    p=tmp_path/'hitos.json';p.write_text(json.dumps(data))
    monkeypatch.setattr(gestion,'FAL_HITOS_PATH',p)
    monkeypatch.setattr(gestion,'date',Hoy)
    monkeypatch.setattr(Hoy,'dia',8)
    monkeypatch.setattr(gestion,'_cnv_registro_fci',lambda:[{'Text':'OTRO FONDO'}])
    monkeypatch.setattr(gestion,'_bo_conteo',lambda *a,**k:0)
    return p,data


def test_consultar_cnv_no_renueva_revisiones_manuales(registro,monkeypatch):
    a=gestion.fetch_fal_modernizacion_laboral()
    monkeypatch.setattr(Hoy,'dia',9)
    b=gestion.fetch_fal_modernizacion_laboral()
    assert a['valor']==b['valor']==50
    assert a['consulta_cnv_en']=='2026-09-08'
    assert b['consulta_cnv_en']=='2026-09-09'
    for k,fecha in [('revision_normativa_en','2026-07-20'),('revision_judicial_en','2026-08-21')]:
        assert a[k]==b[k]==fecha
        assert fecha in b['detalle_txt']


@pytest.mark.parametrize('valor',[None,'ilegible','2027-01-01'])
def test_revision_ausente_invalida_o_futura_no_da_falso_dato_actual(registro,valor):
    p,data=registro
    if valor is None:del data['_meta']['revision_judicial_en']
    else:data['_meta']['revision_judicial_en']=valor
    p.write_text(json.dumps(data))
    assert gestion.fetch_fal_modernizacion_laboral() is None
