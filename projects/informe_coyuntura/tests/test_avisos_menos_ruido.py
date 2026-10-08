"""Menos ruido en #monitor-alertas (ADR-0350).

Medido el 8-oct-2026 sobre las 91 notificaciones del canal desde el 25-ago: 52
no le pedían nada a nadie. Estas pruebas fijan las cuatro reglas que las
callan, con los casos reales como fixtures, y sobre todo lo que tiene que
SEGUIR avisando: un error de código avisa en la primera corrida, un cotejo
que sí hay que hacer avisa, un 🔴 resuelto sale al canal.

Los logs están en la forma que produce el `tee` del runner (`::notice::`,
`::warning::`, `  [ERR] x: … -- se conservan…`), no como GitHub los renderiza
(ADR-0270).
"""
import itertools
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import aviso_slack  # noqa: E402
from cotejo_manual import registrar  # noqa: E402

RUTA = '/home/runner/work/cigob-informe-coyuntura/cigob-informe-coyuntura/projects/informe_coyuntura/config.py'

# Los 21 indicadores del 22-sep-2026, con el nombre que cada uno no pudo
# importar (sacado de los avisos reales de ese día).
VEINTIDOS_SEP = [
    ('icc_utdt', 'UTDT_ICC_LISTADO'), ('itvc_lider', 'UTDT_IL_LISTADO'),
    ('indice_lider', 'UTDT_IL_LISTADO'), ('pobreza_nowcast', 'HTTP_HEADERS'),
    ('itvc_pobreza', 'HTTP_HEADERS'), ('sentimiento_digital', 'TRENDS_KEYWORDS'),
    ('itvc_alimentos', 'INDEC_SERIES'), ('itvc_alquiler', 'INDEC_SERIES'),
    ('alquiler_real', 'INDEC_SERIES'), ('trabajo_independiente', 'DATOS_GOB_BASE'),
    ('mortalidad_pymes', 'DATOS_GOB_BASE'), ('motorizacion_total', 'DATOS_GOB_BASE'),
    ('ratio_motos_autos', 'DATOS_GOB_BASE'), ('patentamiento_motos', 'DATOS_GOB_BASE'),
    ('patentamiento_autos', 'DATOS_GOB_BASE'), ('consumo_supermercados', 'DATOS_GOB_BASE'),
    ('inseguridad_snic', 'SNIC_CSV'), ('tasa_homicidios', 'SNIC_CSV'),
    ('tasa_robos', 'SNIC_CSV'), ('consumo_carne', 'CICCRA_HOME'),
    ('brecha_salario_cbt', 'RIPTE_CSV'),
]


def log_errores(pares):
    return ''.join(f"  [ERR] {ind}: cannot import name '{nombre}' from 'config' ({RUTA}) "
                   f"-- se conservan las filas anteriores\n" for ind, nombre in pares)


LOG_22_SEP = '::notice::macro exit=0\n::notice::politica exit=1\n' + log_errores(VEINTIDOS_SEP) \
    + '::notice::series exit=1\n'

# 17 y 18-sep: `validacion` se comió su presupuesto y el workflow lo mapeó a exit=2.
VALIDACION_LENTA = ('::warning::validacion agotó su presupuesto de 5m — se sigue con caché\n'
                    '::notice::validacion exit=2\n')
GESTION_CAIDA = '::notice::gestion exit=2\n'

# El motivo real de la guarda de cámara muda (politica._avisar_camara_muda).
MOTIVO_AEA = ('AEA lleva 191 días sin publicar un comunicado. Su umbral es 134 días —el '
              'percentil 95 de sus 42 huecos, mediana 43, máximo 154—, así que el silencio no '
              'tiene precedente. Ya está fuera del cálculo (ADR-0334): este aviso se resuelve solo '
              'el día que vuelva a publicar, y esa es la señal para reponerla en '
              'APOYO_CAMARAS_PERIMETRO.')


class Slack:
    def __init__(self):
        self.posts, self.ediciones, self._ts = [], [], itertools.count(1)

    def publicar(self, texto, **extra):
        ts = f'200.{next(self._ts)}'
        self.posts.append(dict(texto=texto, ts=ts, **extra))
        return ts

    def editar(self, ts, texto):
        self.ediciones.append(dict(ts=ts, texto=texto))
        return ''

    def en_el_canal(self):
        """Lo que notifica al canal: raíces y respuestas con broadcast."""
        return [p for p in self.posts if 'thread_ts' not in p or p.get('reply_broadcast')]


@pytest.fixture
def slack(monkeypatch):
    s = Slack()
    monkeypatch.setattr(aviso_slack, 'publicar', s.publicar)
    monkeypatch.setattr(aviso_slack, 'editar', s.editar)
    return s


def correr(monkeypatch, tmp_path, modo, log='', gates='', extra=()):
    (tmp_path / 'colectores.log').write_text(log, encoding='utf-8')
    (tmp_path / 'gates.log').write_text(gates, encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', [
        'aviso_slack', modo, '--log', str(tmp_path / 'colectores.log'),
        '--gates', str(tmp_path / 'gates.log'), '--url', 'https://github.com/run/1',
        '--archivo-estado', str(tmp_path / 'estado' / 'estado.json'), *extra])
    assert aviso_slack.main() == 0


def estado(tmp_path):
    return json.loads((tmp_path / 'estado' / 'estado.json').read_text())['problemas']


# ── 1. Una causa común es un problema ────────────────────────────────────────

def test_la_firma_borra_ruta_numeros_y_el_nombre_que_falta():
    a = aviso_slack.firma_error(f"cannot import name 'UTDT_ICC_LISTADO' from 'config' ({RUTA})")
    b = aviso_slack.firma_error(f"cannot import name 'SNIC_CSV' from 'config' ({RUTA})")
    assert a == b == "cannot import name '…' from 'config'"
    assert aviso_slack.firma_error('KeyError: 2024-03 en /tmp/a/b.csv fila 31') \
        == aviso_slack.firma_error('KeyError: 2025-11 en /tmp/x/y.csv fila 7')
    # Errores distintos no se mezclan: otro módulo, otro tipo.
    assert aviso_slack.firma_error("cannot import name 'X' from 'config'") \
        != aviso_slack.firma_error("cannot import name 'X' from 'fuentes'")
    assert aviso_slack.firma_error('KeyError: x') != aviso_slack.firma_error('ValueError: x')


def test_el_22_sep_es_un_solo_problema_con_los_rotulos_y_tope(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', LOG_22_SEP)
    [raiz] = slack.en_el_canal()
    primera = raiz['texto'].splitlines()[0]
    assert primera.startswith('🟡 *Monitor del Plan de Gobierno — 21 indicadores no se actualizan '
                              'por el mismo error de código: `cannot import name \'…\' from \'config\'`')
    assert '«Confianza del consumidor»' in raiz['texto']             # rótulo de la card, no la clave
    assert 'y 13 más' in raiz['texto']                               # tope de 8 rótulos
    assert '/home/runner' not in raiz['texto']
    assert list(estado(tmp_path)) == ["causa:cannot import name '…' from 'config'"]


def test_el_grupo_que_se_achica_edita_la_raiz_y_se_cierra_con_un_solo_ok(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', LOG_22_SEP)
    correr(monkeypatch, tmp_path, 'degradado', log_errores(VEINTIDOS_SEP[:2]))   # quedan 2 (< umbral)
    assert len(slack.posts) == 1                                     # ni raíz nueva ni hilos por indicador
    assert slack.ediciones[-1]['texto'].splitlines()[0].startswith(
        '🟡 *Monitor del Plan de Gobierno — 2 indicadores no se actualizan')
    correr(monkeypatch, tmp_path, 'degradado', '::notice::macro exit=0\n')
    oks = [p for p in slack.posts if p['texto'].startswith('✅')]
    assert len(oks) == 1 and oks[0]['thread_ts'] == slack.posts[0]['ts']
    assert not oks[0].get('reply_broadcast')                         # 🟡: queda en el hilo
    assert estado(tmp_path) == {}


def test_menos_del_umbral_sigue_avisando_por_indicador(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', log_errores(VEINTIDOS_SEP[:2]))
    assert len(slack.en_el_canal()) == 2
    assert set(estado(tmp_path)) == {'err:icc_utdt', 'err:itvc_lider'}


def test_dos_errores_distintos_no_se_agrupan_entre_si(slack, monkeypatch, tmp_path):
    log = log_errores(VEINTIDOS_SEP[:3]) + (
        '  [ERR] tasa_robos: division by zero -- se conservan las filas anteriores\n')
    correr(monkeypatch, tmp_path, 'degradado', log)
    assert set(estado(tmp_path)) == {"causa:cannot import name '…' from 'config'", 'err:tasa_robos'}


# ── 3b. Fuente caída y presupuesto: desde la tercera corrida seguida ─────────

def test_una_fuente_caida_no_avisa_hasta_la_tercera_corrida(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', GESTION_CAIDA)
    correr(monkeypatch, tmp_path, 'degradado', GESTION_CAIDA)
    assert slack.posts == []
    assert estado(tmp_path)['caida:gestion']['corridas'] == 2       # pero se cuenta
    correr(monkeypatch, tmp_path, 'degradado', GESTION_CAIDA)
    [raiz] = slack.posts
    assert 'el colector `gestion` no trae nada fresco' in raiz['texto']
    assert 'Desde el' in raiz['texto'] and 'lleva 3 corridas' in raiz['texto']


def test_una_fuente_que_vuelve_antes_del_umbral_no_dice_nada(slack, monkeypatch, tmp_path):
    # 17 y 18-sep: `validacion` se arregló sola en dos noches; salieron 2 🟡 y 2 ✅.
    correr(monkeypatch, tmp_path, 'degradado', VALIDACION_LENTA)
    correr(monkeypatch, tmp_path, 'degradado', VALIDACION_LENTA)
    correr(monkeypatch, tmp_path, 'degradado', '::notice::validacion exit=0\n')
    assert slack.posts == [] and slack.ediciones == []
    assert estado(tmp_path) == {}


def test_un_presupuesto_agotado_es_un_problema_no_dos(slack, monkeypatch, tmp_path):
    for _ in range(3):
        correr(monkeypatch, tmp_path, 'degradado', VALIDACION_LENTA)
    [raiz] = slack.posts
    assert '`validacion` se queda sin tiempo' in raiz['texto']
    assert set(estado(tmp_path)) == {'presupuesto:validacion'}


def test_una_corrida_caida_en_el_medio_no_reinicia_ni_suma(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado', GESTION_CAIDA)
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    assert estado(tmp_path)['caida:gestion']['corridas'] == 1


def test_un_error_de_codigo_sigue_avisando_en_la_primera(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'degradado',
           "  [ERR] icg_utdt: name 'UTDT_ICG_REFERER' is not defined -- se conservan las filas anteriores\n")
    assert len(slack.posts) == 1


# ── 3a. Cotejos que se resuelven solos ───────────────────────────────────────

def _cotejos(capsys, *, uia=True):
    registrar('apoyo_empresario', 'AEA muda desde 2026-03-31', MOTIVO_AEA, 'https://www.aeanet.net/prensa.html')
    if uia:
        registrar('apoyo_empresario', 'UIA|la-uia-busco-alianzas',
                  'Comunicado sin codificar: la serie se corta en el mes anterior hasta codificarlo.',
                  'https://www.uia.org.ar/x')
    return capsys.readouterr().err


def test_aea_muda_no_va_a_slack(slack, monkeypatch, tmp_path, capsys):
    correr(monkeypatch, tmp_path, 'degradado', _cotejos(capsys, uia=False))
    assert slack.posts == [] and estado(tmp_path) == {}


def test_un_comunicado_sin_codificar_del_mismo_indicador_si_avisa(slack, monkeypatch, tmp_path, capsys):
    correr(monkeypatch, tmp_path, 'degradado', _cotejos(capsys))
    [raiz] = slack.posts
    assert 'tiene 1 registro para cotejar' in raiz['texto']
    assert 'UIA|la-uia' in raiz['texto'] and 'AEA muda' not in raiz['texto']


def test_si_aea_vuelve_al_perimetro_el_aviso_vuelve_a_sonar(slack, monkeypatch, tmp_path, capsys):
    # Dentro del perímetro el colector escribe otro motivo: el silencio no aplica.
    registrar('apoyo_empresario', 'AEA muda desde 2026-03-31',
              'AEA lleva 191 días sin publicar. Verificar en la fuente si dejó de publicar.', 'x')
    correr(monkeypatch, tmp_path, 'degradado', capsys.readouterr().err)
    assert len(slack.posts) == 1 and 'AEA muda' in slack.posts[0]['texto']


def test_la_lista_sale_de_un_adr_decidido():
    adrs = Path(__file__).resolve().parents[1] / 'docs' / 'adr'
    for _, _, adr in aviso_slack.COTEJO_SE_RESUELVE_SOLO:
        [archivo] = adrs.glob(f'{adr}-*.md')
        assert "estado: 'aceptado'" in archivo.read_text(encoding='utf-8')


def test_en_el_rojo_de_slack_no_va_pero_en_el_issue_si(slack, monkeypatch, tmp_path, capsys):
    log = _cotejos(capsys, uia=False)
    gates = 'FAILED tests/test_x.py::test_a - boom\n'
    correr(monkeypatch, tmp_path, 'fallo', log, gates)
    assert 'AEA muda' not in slack.posts[0]['texto']
    correr(monkeypatch, tmp_path, 'reporte', log, gates)
    assert 'AEA muda' in capsys.readouterr().out


# ── 4. Resoluciones: al canal sólo el rojo ───────────────────────────────────

def test_la_corrida_que_vuelve_a_publicar_si_sale_al_canal(slack, monkeypatch, tmp_path):
    correr(monkeypatch, tmp_path, 'fallo', gates='FAILED tests/test_x.py::test_a - boom\n')
    correr(monkeypatch, tmp_path, 'degradado', '')
    cierre = slack.posts[-1]
    assert 'la corrida nocturna vuelve a publicar' in cierre['texto'] and cierre['reply_broadcast'] is True


# ── Cómo se habría visto ─────────────────────────────────────────────────────

def test_el_22_y_el_24_sep_con_las_reglas_nuevas(slack, monkeypatch, tmp_path):
    """Antes: 21 🟡 el 22 y 21 ✅ con broadcast el 24 = 42 notificaciones."""
    correr(monkeypatch, tmp_path, 'degradado', LOG_22_SEP)
    correr(monkeypatch, tmp_path, 'degradado', '::notice::macro exit=0\n')
    assert len(slack.en_el_canal()) == 1
    assert len(slack.posts) == 2                                     # la raíz y su ✅ en el hilo
