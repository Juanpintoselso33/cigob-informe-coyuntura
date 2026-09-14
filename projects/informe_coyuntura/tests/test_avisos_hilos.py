"""Un hilo por problema en #monitor-alertas (ADR-0309).

Hasta el 14-sep-2026 la misma falla salía como un mensaje nuevo cada noche y,
cuando se arreglaba, no avisaba nada: una corrida limpia no manda mensajes, y
ese silencio no se distingue de un bot que no corrió. Estas pruebas fijan el
ciclo: aparece → mensaje; sigue → se edita, sin mensaje nuevo; se resuelve →
respuesta en el hilo que también sale en el canal, y la raíz pasa a ✅.
"""
import itertools
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import aviso_slack
from cotejo_manual import revisar_fechas_sancion

ERR = '  [ERR] produccion_legislativa: leyes-sancionadas sin ley -- se conservan\n'


@pytest.fixture
def slack(monkeypatch):
    """Slack falso: registra posteos (con hilo y broadcast) y ediciones."""
    reg = SimpleSlack()
    monkeypatch.setattr(aviso_slack, 'publicar', reg.publicar)
    monkeypatch.setattr(aviso_slack, 'editar', reg.editar)
    return reg


class SimpleSlack:
    def __init__(self):
        self.posts, self.ediciones, self._ts = [], [], itertools.count(1)
        self.errores_edicion = []

    def publicar(self, texto, **extra):
        ts = f'100.{next(self._ts)}'
        self.posts.append(dict(texto=texto, ts=ts, **extra))
        return ts

    def editar(self, ts, texto):
        self.ediciones.append(dict(ts=ts, texto=texto))
        return self.errores_edicion.pop(0) if self.errores_edicion else ''

    def raices(self):
        return [p for p in self.posts if 'thread_ts' not in p]


def correr(monkeypatch, tmp_path, modo, log='', gates='', extra=()):
    for nombre, texto in (('colectores.log', log), ('gates.log', gates)):
        (tmp_path / nombre).write_text(texto)
    monkeypatch.setattr(sys, 'argv', [
        'aviso_slack', modo, '--log', str(tmp_path / 'colectores.log'),
        '--gates', str(tmp_path / 'gates.log'), '--url', 'https://github.com/run/1',
        '--archivo-estado', str(tmp_path / 'estado' / 'estado.json'), *extra])
    assert aviso_slack.main() == 0


def estado(tmp_path):
    return json.loads((tmp_path / 'estado' / 'estado.json').read_text())['problemas']


def test_un_problema_nuevo_abre_un_mensaje_que_dice_que_producto_y_que_ve_la_gente(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    [raiz] = slack.raices()
    primera = raiz['texto'].splitlines()[0]
    assert primera.startswith('🟡 *Monitor del Plan de Gobierno — ')
    assert '«Producción legislativa del Congreso»' in primera       # el nombre de la card, no la clave
    assert '*Qué ve la gente:*' in raiz['texto'] and '*Qué hacer:*' in raiz['texto']
    assert estado(tmp_path)['err:produccion_legislativa']['ts'] == raiz['ts']


def test_si_sigue_no_postea_de_nuevo_edita_la_raiz_con_el_contador(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    assert len(slack.posts) == 1                                     # tres noches, un solo mensaje
    assert 'lleva 3 corridas' in slack.ediciones[-1]['texto']
    assert slack.ediciones[-1]['ts'] == slack.posts[0]['ts']


def test_si_cambia_el_diagnostico_responde_en_el_hilo_sin_ensuciar_el_canal(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'degradado', ERR.replace('sin ley', 'con fecha futura'))
    [respuesta] = [p for p in slack.posts if 'thread_ts' in p]
    assert respuesta['thread_ts'] == slack.posts[0]['ts']
    assert not respuesta.get('reply_broadcast')
    assert 'fecha futura' in respuesta['texto']


def test_al_resolverse_avisa_en_el_canal_y_la_raiz_pasa_a_resuelto(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'degradado', '')                   # corrida limpia
    cierre = slack.posts[-1]
    assert cierre['thread_ts'] == slack.posts[0]['ts'] and cierre['reply_broadcast'] is True
    assert cierre['texto'].startswith('✅ *Monitor del Plan de Gobierno — «Producción legislativa del Congreso» vuelve a actualizarse*')
    assert 'después de 2 corridas' in cierre['texto']
    raiz = slack.ediciones[-1]['texto']
    assert raiz.startswith('✅ *Monitor del Plan de Gobierno — «Producción legislativa del Congreso» vuelve a actualizarse*')
    assert '_Era:_ «Producción legislativa del Congreso» no se está actualizando' in raiz
    assert estado(tmp_path) == {}
    correr(monkeypatch, tmp_path, 'degradado', '')                   # y no lo repite
    assert len(slack.posts) == 2


def test_una_corrida_caida_no_da_por_resueltas_las_degradaciones(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    assert 'err:produccion_legislativa' in estado(tmp_path)          # esa noche no se midió
    assert not any(p.get('reply_broadcast') for p in slack.posts)
    assert slack.raices()[-1]['texto'].startswith('🔴 *Monitor del Plan de Gobierno — ')


def test_la_corrida_caida_se_cierra_cuando_una_publica(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    correr(monkeypatch, tmp_path, 'degradado', '')
    assert len(slack.raices()) == 1
    assert slack.posts[-1]['reply_broadcast'] is True
    assert 'la corrida nocturna vuelve a publicar' in slack.posts[-1]['texto']
    assert estado(tmp_path) == {}


def test_un_corte_despues_de_publicar_no_dice_que_no_publico(slack, monkeypatch, tmp_path):
    # 14-sep-2026: el tope de 45 min cortó el job en BigQuery, con el snapshot
    # ya en main. El 🔴 dijo «se corta sin publicar» y que la web mostraba la
    # corrida anterior, que era justamente la nueva.
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    correr(monkeypatch, tmp_path, 'fallo', extra=[
        '--publico', '--estado', 'cancelled', '--pasos', '- Espejar la corrida en BigQuery',
        '--sirviendo', '2026-09-14T21:44:07+00:00'])
    raiz = slack.raices()[-1]['texto']
    assert raiz.startswith('🟡 *Monitor del Plan de Gobierno — la corrida publicó, pero se cortó antes de terminar*')
    assert 'no publica' not in raiz and 'corrida anterior' not in raiz
    assert 'Espejar la corrida en BigQuery' in raiz and 'bigquery_backfill' in raiz
    # y cierra el «no publica» de la corrida anterior, que ya no es cierto
    assert any(p.get('reply_broadcast') and 'vuelve a publicar' in p['texto'] for p in slack.posts)
    assert set(estado(tmp_path)) == {'cierre'}
    correr(monkeypatch, tmp_path, 'degradado', '')                   # la siguiente termina bien
    assert estado(tmp_path) == {}


def test_si_slack_no_confirma_el_cierre_queda_abierto_para_reintentar(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    monkeypatch.setattr(aviso_slack, 'publicar', lambda texto, **kw: '')
    correr(monkeypatch, tmp_path, 'degradado', '')
    assert 'err:produccion_legislativa' in estado(tmp_path)


def test_si_falla_solo_la_edicion_del_cierre_se_reintenta_sin_repetir_el_aviso(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    slack.errores_edicion = ['ratelimited']
    correr(monkeypatch, tmp_path, 'degradado', '')
    assert estado(tmp_path)['err:produccion_legislativa']['cierre_publicado'] is True
    correr(monkeypatch, tmp_path, 'degradado', '')
    assert sum(bool(p.get('reply_broadcast')) for p in slack.posts) == 1   # el ✅ salió una vez
    assert slack.ediciones[-1]['texto'].startswith('✅') and estado(tmp_path) == {}


def test_si_borraron_la_raiz_abre_otra_en_vez_de_quedar_mudo(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    slack.errores_edicion = ['message_not_found']
    correr(monkeypatch, tmp_path, 'degradado', ERR)
    assert len(slack.raices()) == 2
    assert estado(tmp_path)['err:produccion_legislativa']['ts'] == slack.raices()[-1]['ts']
    assert 'lleva 2 corridas' in slack.raices()[-1]['texto']


def test_los_cotejos_van_en_un_hilo_por_indicador_con_tope(slack, monkeypatch, tmp_path, capsys):
    revisar_fechas_sancion([{'PROYECTO_ID': f'HCDN{n}'} for n in range(10)], 'https://datos.hcdn.gob.ar')
    correr(monkeypatch, tmp_path, 'degradado', capsys.readouterr().err + ERR)
    causa, cotejo = slack.raices()                                   # la causa primero
    assert 'no se está actualizando' in causa['texto'] and 'HCDN' not in causa['texto']
    assert 'tiene 10 registros para cotejar a mano' in cotejo['texto']
    assert sum(f'HCDN{n}`' in cotejo['texto'] for n in range(10)) == 3
    assert '…y 7 más, en el run.' in cotejo['texto']


def test_sin_archivo_de_estado_avisa_igual_suelto(monkeypatch, tmp_path):
    enviados = []
    monkeypatch.setattr(aviso_slack, 'publicar', lambda texto, **kw: enviados.append(texto) or '')
    (tmp_path / 'log').write_text(ERR)
    monkeypatch.setattr(sys, 'argv', ['aviso_slack', 'degradado', '--log', str(tmp_path / 'log')])
    assert aviso_slack.main() == 0
    assert len(enviados) == 1 and 'Monitor del Plan de Gobierno' in enviados[0]


def test_el_workflow_restaura_pasa_y_guarda_el_estado_siempre():
    # Sin esto el ciclo se rompe en silencio: cada noche arranca sin hilos y
    # vuelve a postear todo como nuevo, que es exactamente lo que se arregló.
    import yaml
    wf = Path(__file__).resolve().parents[3] / '.github' / 'workflows' / 'data-pipeline.yml'
    pasos = yaml.safe_load(wf.read_text(encoding='utf-8'))['jobs']['run']['steps']
    usos = [p.get('uses', '') for p in pasos]
    assert any(u.startswith('actions/cache/restore@') for u in usos)
    [guardar] = [p for p in pasos if p.get('uses', '').startswith('actions/cache/save@')]
    assert guardar['if'].startswith('always()')
    avisos = [p['run'] for p in pasos if 'aviso_slack.py degradado' in p.get('run', '')
              or 'aviso_slack.py fallo' in p.get('run', '')]
    assert len(avisos) == 2 and all('--archivo-estado' in r for r in avisos)
    # Sólo `main` lleva hilos: una corrida manual sobre otra rama no publica
    # producción y no puede dar por resuelto lo de `main` (hallazgo de Codex).
    restaurar = next(p for p in pasos if p.get('uses', '').startswith('actions/cache/restore@'))
    assert "refs/heads/main" in restaurar['if'] and "refs/heads/main" in guardar['if']
    assert all('refs/heads/main' in r for r in avisos)
    # El aviso de falla distingue un corte posterior al commit: sin el id del
    # paso de commit no hay forma de saberlo y vuelve a decir «no publicó».
    commit = next(p for p in pasos if p.get('name', '').startswith('Commitear'))
    assert commit.get('id') == 'commit'
    falla = next(p for p in pasos if p.get('name') == 'Avisar que la corrida falló')
    assert falla['env']['COMMIT'] == '${{ steps.commit.outcome }}' and '--publico' in falla['run']
    assert 'conclusion=="cancelled"' in falla['run']
    # Y dos corridas a la vez leerían el mismo estado y duplicarían hilos.
    flujo = yaml.safe_load(wf.read_text(encoding='utf-8'))
    assert flujo.get('concurrency', {}).get('cancel-in-progress') is False
