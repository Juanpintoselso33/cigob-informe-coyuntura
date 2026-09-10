"""El original exige identidad geográfica y una historia mensual completa."""
import sys
from pathlib import Path
from datetime import date
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/vida_cotidiana/collectors'))
import ipc_alquiler as alq


def libro(monkeypatch, filas):
    hoja = SimpleNamespace(name='Índices aperturas', nrows=len(filas), ncols=3,
                           cell_value=lambda i,j: filas[i][j])
    monkeypatch.setattr(alq.xlrd, 'open_workbook', lambda **kw: SimpleNamespace(
        datemode=0, sheets=lambda:[hoja]))


def filas():
    return [['Región GBA', 45627, 45658], ['Nivel general', 200, 204],
            ['Alquiler de la vivienda', 100, 105],
            ['Región Pampeana', 45627, 45658], ['Alquiler de la vivienda', 900, 950]]


def test_elige_niveles_gba_sin_mezclar_regiones(monkeypatch):
    libro(monkeypatch, filas())
    r=alq.parsear(b'', hoy=date(2025,2,1))
    assert r['alquiler']=={'2024-12':100,'2025-01':105}
    assert r['general']=={'2024-12':200,'2025-01':204}


@pytest.mark.parametrize('fila,columna,valor', [
    (0,2,45627), (0,2,45689), (2,2,''), (2,2,0),
    (2,2,float('nan')), (2,0,'Alquiler de la vivienda y gastos conexos'),
    (0,0,'Región Noroeste'), (1,0,'Nivel general nacional')])
def test_no_acepta_historia_parcial_o_concepto_distinto(monkeypatch,fila,columna,valor):
    f=filas();f[fila][columna]=valor;libro(monkeypatch,f)
    with pytest.raises(ValueError):alq.parsear(b'',hoy=date(2025,3,1))


def test_no_acepta_mes_en_curso(monkeypatch):
    libro(monkeypatch,filas())
    with pytest.raises(ValueError,match='no cerrado'):alq.parsear(b'',hoy=date(2025,1,31))


def test_cabecera_mensual_no_exige_dia_uno(monkeypatch):
    f=filas();f[0][2]+=25;libro(monkeypatch,f)
    assert alq.parsear(b'',hoy=date(2025,2,1))['alquiler']['2025-01']==105


def test_tarjeta_calcula_variacion_del_original(monkeypatch):
    monkeypatch.setattr(alq,'niveles',lambda:{'alquiler':{'2024-12':100,'2025-01':105}})
    r=alq.tarjeta()
    assert r['fecha']=='2025-01-01'
    assert r['variacion_mensual_pct']==pytest.approx(5)
    assert r['fuente_url']==alq.URL
