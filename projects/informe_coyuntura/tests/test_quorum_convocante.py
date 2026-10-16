"""veto_quorum: una sesión caída que pidió la oposición no cuenta (ADR-0358)."""
import json
from datetime import date
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica


def reunion(i, fecha, minoria):
    return {'id': str(i), 'fecha': fecha, 'en_minoria': minoria, 'titulo': '', 'url': f'u{i}'}


@pytest.fixture
def registro(tmp_path, monkeypatch):
    def cargar(*sesiones):
        p = tmp_path / 'convocantes.json'
        p.write_text(json.dumps({'revisado_en': '2026-10-15', 'sesiones': list(sesiones)}), encoding='utf-8')
        monkeypatch.setattr(politica, 'QUORUM_CONVOCANTE_PATH', p)
    return cargar


REUNIONES = [reunion(1, '2026-08-26', False), reunion(2, '2026-09-10', False),
             reunion(3, '2026-10-15', True)]


def test_caida_pedida_por_la_oposicion_no_cuenta(registro):
    registro({'id': '3', 'convocante': 'oposicion', 'fuente': 'x'})
    sesiones, excluidas = politica._sesiones_para_veto(REUNIONES)
    assert excluidas == 1
    assert politica._veto_quorum_tasa_12m(sesiones, date(2026, 10, 15)) == (0.0, 2, 0)


def test_caida_del_oficialismo_si_cuenta(registro):
    registro({'id': '3', 'convocante': 'oficialismo', 'fuente': 'x'})
    sesiones, excluidas = politica._sesiones_para_veto(REUNIONES)
    assert excluidas == 0
    assert politica._veto_quorum_tasa_12m(sesiones, date(2026, 10, 15)) == (33.3, 3, 1)


def test_caida_sin_cargar_cuenta_y_pide_cotejo(registro, capsys):
    registro()
    sesiones, excluidas = politica._sesiones_para_veto(REUNIONES, avisar=True)
    assert excluidas == 0 and ('2026-10-15', True) in sesiones
    err = capsys.readouterr().err
    assert '[COTEJO_MANUAL]' in err and 'reunión 3 del 2026-10-15' in err


@pytest.mark.parametrize('entrada', [{'id': '3', 'convocante': 'oposicion', 'fuente': ''},
                                     {'id': '3', 'convocante': 'nadie', 'fuente': 'x'}])
def test_entrada_sin_fuente_o_sin_convocante_valido_falla(registro, entrada):
    registro(entrada)
    with pytest.raises(ValueError):
        politica._sesiones_para_veto(REUNIONES)


def test_registro_versionado_cubre_toda_caida_conocida_con_fuente():
    """Cada entrada del registro real tiene convocante válido y fuente."""
    convocantes = politica._convocantes_minoria()
    assert convocantes, 'registro vacío'
    assert all(e['fuente'].startswith('http') for e in convocantes.values())


def test_reunion_repetida_en_el_registro_falla(registro):
    registro({'id': '3', 'convocante': 'oposicion', 'fuente': 'x'},
             {'id': '3', 'convocante': 'oficialismo', 'fuente': 'y'})
    with pytest.raises(ValueError):
        politica._sesiones_para_veto(REUNIONES)
