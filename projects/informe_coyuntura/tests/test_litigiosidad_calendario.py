import io
from pathlib import Path
import sys
import pytest
import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion
import descargar_series


def serie():
    return {f'{2024+i//12}-{i%12+1:02d}': 100. for i in range(29)}


@pytest.mark.parametrize('malo', [None, float('nan'), float('inf'), -1.])
def test_rechaza_mes_invalido_sin_reemplazarlo_por_otro(malo):
    s = serie(); s['2025-01'] = malo
    with pytest.raises(ValueError, match='24 meses consecutivos'):
        gestion._juicios_variacion_24m(s, '2026-05')


def test_cero_observado_es_valido_y_base_cero_no():
    s = serie(); s['2026-05'] = 0.
    assert gestion._juicios_variacion_24m(s, '2026-05') == (-8.3, 1100., 1200.)
    with pytest.raises(ValueError, match='base sin juicios'):
        gestion._juicios_variacion_24m(dict.fromkeys(s, 0.), '2026-05')


@pytest.mark.parametrize('hueco', [False, True])
def test_tarjeta_e_historia_comparten_ventana(monkeypatch, hueco):
    s = serie()
    if hueco:
        s['2025-01'] = None
    meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
    w = openpyxl.Workbook();h=w.active;h.title='TOTAL SISTEMA'
    h.append(['Período']+[f'{meses[int(m[5:])-1]}-{m[:4]}' for m in s])
    h.append(['Total de juicios']+list(s.values()))
    buf=io.BytesIO();w.save(buf)
    monkeypatch.setattr(gestion,'_http_get_resiliente',lambda _:buf.getvalue())
    card=gestion.fetch_litigiosidad_laboral();hist=descargar_series.fetch_litigiosidad_serie()
    if hueco:
        assert card is None
        assert hist == []
    else:
        assert hist[-1] == [card['fecha_dato'], card['valor']] == ['2026-05-01',0.]
