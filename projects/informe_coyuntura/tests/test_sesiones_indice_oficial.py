from datetime import date
from pathlib import Path
import sys
import pytest
import re
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


def panel(periodo, *enlaces):
    return (f'<div class="js-accordion__panel"><button class="js-accordion__header">PERIODO {periodo} '
            f'(01/03/2026 - 28/02/2027)</button><ul>{"".join(enlaces)}</ul></div>')


def opaco(h, titulo, fecha):
    return f'<li><a href="../_q/{h}.html" target="_blank">{titulo} - ({fecha})</a></li>'


def test_indice_de_noviembre_2026_con_enlaces_opacos(monkeypatch):
    """Desde el 12-nov-2026 el índice enlaza `/_q/<hash>.html`: la identidad es período-reunión."""
    html = ('<div id="periodos" class="js-accordion">'
            + panel(144, opaco('a73135c927afbe3a', '8° Reunión - Expresiones en Minoría', '15/10/2026'),
                    opaco('37fa3573a4f1ed95', ' Sesión Ordinaria Especial CITADA - NO EFECTUADA', '20/05/2026'),
                    opaco('277e5ae9d84c8454', '3° Reunión - 3° Sesión Ordinaria Especial', '20/05/2026'))
            + panel(143, opaco('30e216c91c7ba9f5', '22° Reunión - 3° Sesión Extraordinaria Especial', '19/02/2026'))
            + '</div>')
    Hoy_ = type('H', (date,), {'today': classmethod(lambda c: c(2026, 11, 12))})
    monkeypatch.setattr(politica, 'date', Hoy_)
    rs = politica._sesiones_desde_indice(html)
    assert [(r['id'], r['fecha'], r['en_minoria']) for r in rs] == [
        ('143-22', '2026-02-19', False), ('144-3', '2026-05-20', False), ('144-8', '2026-10-15', True)]
    assert rs[-1]['url'] == 'https://www.hcdn.gob.ar/_q/a73135c927afbe3a.html'


def test_reunion_opaca_sin_numero_no_pasa_callada():
    html = panel(144, opaco('ab12', 'Sesión Ordinaria Especial', '20/05/2026'))
    with pytest.raises(ValueError, match='identidad'):
        politica._sesiones_desde_indice(html)


def test_registro_de_convocantes_usa_la_clave_nueva():
    ids = list(politica._convocantes_minoria())
    assert ids and all(re.fullmatch(r'\d{3}-\d+', i) for i in ids)
