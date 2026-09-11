"""El tercer componente entra en el mismo mes y con la misma fórmula."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import macro


@pytest.fixture
def fuentes(monkeypatch):
    meses = [macro._ym_shift('2025-05', i) for i in range(15)]
    pat = {m: 100 for m in meses}
    pat.update({'2026-06': 150, '2026-07': 300})
    isac = {m: 100 for m in meses if m <= '2026-06'}
    bk = dict(isac)
    isac['2026-06'] = 110
    bk['2026-06'] = 120
    monkeypatch.setattr(macro, '_cargar_patentamientos', lambda: pat)
    monkeypatch.setattr(macro, '_indec_nivel_mensual',
                        lambda identificador, **_: isac if identificador == macro.INDEC_ISAC_NIVEL_ID else bk)
    return pat


def test_tarjeta_e_historia_incluyen_patentamientos_del_mes_comun(fuentes):
    card = macro.fetch_iai()
    assert card['fecha_dato'] == '2026-06-01'
    assert card['componentes']['patentamientos_comerciales'] == 50
    assert card['valor'] == pytest.approx(19)  # 0.55*10 + 0.30*20 + 0.15*50
    assert macro._iai_serie_mensual()[-1] == ('2026-06', 19)
    assert 'DNRPA' in card['fuente']


def test_no_usa_el_ultimo_patentamiento_si_falta_mes_comun(fuentes):
    del fuentes['2026-06']
    card = macro.fetch_iai()
    assert 'patentamientos_comerciales' not in card['componentes']
    assert card['valor'] == pytest.approx(13.5)
    assert macro._iai_serie_mensual()[-1] == ('2026-06', 13.5)


def test_datos_futuros_no_activan_tercer_componente_en_meses_previos(fuentes):
    assert macro._patentamientos_ia('2026-04') is None
    assert macro._patentamientos_ia('2026-05')['fecha'] == '2026-05'
