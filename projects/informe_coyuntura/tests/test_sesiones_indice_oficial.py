from datetime import date
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import politica


class Hoy(date):
    @classmethod
    def today(cls): return cls(2026,9,8)


def enlace(i,titulo,fecha,reunion='1'):
    return f'<a href="sesion.html?id={i}&periodo=144&reunion={reunion}">{titulo} - ({fecha})</a>'


@pytest.fixture(autouse=True)
def reloj(monkeypatch): monkeypatch.setattr(politica,'date',Hoy)


def test_fecha_del_indice_recupera_agosto_y_excluye_convocatoria_futura():
    html=enlace(1,'Sesión Ordinaria Especial','26/08/2026')+enlace(2,'Sesión Ordinaria Especial','09/09/2026')
    rs=politica._sesiones_desde_indice(html)
    assert [(r['id'],r['fecha']) for r in rs]==[('1','2026-08-26')]


def test_identidad_deduplica_enlaces_pero_conserva_dos_reuniones_del_dia():
    a=enlace(1,'Sesión Ordinaria Especial','26/08/2026')
    b=enlace(2,'Sesión Ordinaria Especial','26/08/2026',reunion='2')
    rs=politica._sesiones_desde_indice(a+a+b)
    assert len(rs)==2
    assert politica._veto_quorum_tasa_12m([(r['fecha'],r['en_minoria']) for r in rs],Hoy.today())==(0.0,2,0)


def test_minoria_y_exclusiones_del_universo():
    html=enlace(1,'Expresiones en Minoría','23/06/2026')
    for i,tipo in enumerate(['Asamblea Legislativa','Sesión Informativa','Sesión Preparatoria',
                            'Sesión Ordinaria Especial de Homenaje','Sesión Especial CITADA - NO EFECTUADA'],2):
        html+=enlace(i,tipo,'23/06/2026')
    rs=politica._sesiones_desde_indice(html)
    assert len(rs)==1 and rs[0]['en_minoria']


@pytest.mark.parametrize('html',['<html>Portal no disponible</html>',
    enlace(1,'Sesión Especial','31/02/2026'),
    enlace(1,'Sesión Especial','26/08/2026')+enlace(1,'Sesión Especial','27/08/2026')])
def test_respuesta_invalida_no_da_falsa_tasa_cero(html):
    with pytest.raises(ValueError):politica._sesiones_desde_indice(html)


def test_tasa_respeta_fecha_exacta_y_borde_del_mes():
    rs=[('2025-09-30',True),('2025-10-01',False),('2026-09-08',True),('2026-09-09',False)]
    assert politica._veto_quorum_tasa_12m(rs,Hoy.today())==(50.0,2,1)
