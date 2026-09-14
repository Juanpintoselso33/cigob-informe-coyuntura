from datetime import date
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica


class Hoy(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 8)


def fila(ley, fecha):
    return {'LEY': ley, 'SANCION_DEFINITIVA': fecha}


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    monkeypatch.setattr(politica, 'date', Hoy)
    monkeypatch.setattr(politica, '_leyes_sancionadas_complementarias', lambda: [])


def test_ventana_incluye_mes_final_y_excluye_mes_en_curso(monkeypatch):
    rows = [fila(1, '2025-08-31'), fila(2, '2025-09-01'),
            fila(3, '2026-08-31'), fila(4, '2026-09-01')]
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a: rows)
    serie = politica.produccion_legislativa_serie()
    assert max(serie) == '2026-08'
    assert serie['2026-08'] == 2
    assert politica.fetch_produccion_legislativa()['fecha_dato'] == '2026-08-01'


def test_cuenta_leyes_no_filas_y_no_inventa_corte_de_cobertura(monkeypatch):
    rows = [fila(1, '2026-06-24'), fila(1, '2026-06-24'),
            fila(1, '2026-06-23')]
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a: rows)
    card = politica.fetch_produccion_legislativa()
    assert card['valor'] == 1
    assert card['fecha_dato'] == '2026-08-01'
    assert card['ultima_sancion_registrada'] == '2026-06-24'
    assert 'no certifica' in card['detalle_txt']


@pytest.mark.parametrize('rows', [[], [fila(1, '2026-02-30')],
    [fila(None, '2026-06-01')], [fila(1, '2027-01-01')],
    [fila(1, '2026-06-30'), fila(1, '2026-07-01')]])
def test_datos_invalidos_no_producen_conteo_parcial(monkeypatch, rows):
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a: rows)
    assert politica.fetch_produccion_legislativa() is None


def test_complemento_recupera_omision_sin_duplicar_si_ckan_la_incorpora(monkeypatch):
    extra = fila(27774, '2024-10-01')
    monkeypatch.setattr(politica, '_leyes_sancionadas_complementarias', lambda: [extra])
    for rows in [[fila(1, '2024-09-01')], [fila(1, '2024-09-01'), extra]]:
        monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a: rows)
        assert politica.produccion_legislativa_serie()['2024-10'] == 2


def test_sancion_sin_numero_y_alta_posterior_no_se_duplican(monkeypatch):
    extra={'EXPEDIENTE_INICIAL':'0028-S-2026','SANCION_DEFINITIVA':'2026-08-26',
           'sancion_definitiva_verificada':True}
    monkeypatch.setattr(politica,'_leyes_sancionadas_complementarias',lambda:[extra])
    for rows in [[fila(1,'2026-06-24')],
                 [fila(1,'2026-06-24'),{**extra,'LEY':99999,'sancion_definitiva_verificada':False}]]:
        monkeypatch.setattr(politica,'_hcdn_paginate',lambda *a:rows)
        assert politica.produccion_legislativa_serie()['2026-08']==2


def test_expediente_sin_numero_exige_sancion_verificada(monkeypatch):
    monkeypatch.setattr(politica,'_hcdn_paginate',lambda *a:[
        {'EXPEDIENTE_INICIAL':'0028-S-2026','SANCION_DEFINITIVA':'2026-08-26'}])
    assert politica.fetch_produccion_legislativa() is None


def test_expediente_con_dos_leyes_no_se_fusiona_silenciosamente(monkeypatch):
    monkeypatch.setattr(politica,'_hcdn_paginate',lambda *a:[
        {**fila(n,'2026-08-26'),'EXPEDIENTE_INICIAL':'0028-S-2026'} for n in [1,2]])
    assert politica.fetch_produccion_legislativa() is None


def test_ckan_sin_numero_toma_la_ley_de_su_expediente(monkeypatch):
    # CKAN publicó los tratados del 27-ago sin número; el registro ya los tenía
    # como 27.824 con el mismo expediente. Antes esto congelaba el indicador.
    extra = {**fila('27824', '2026-08-27'), 'EXPEDIENTE_INICIAL': '0011-PE-2024',
             'sancion_definitiva_verificada': True}
    monkeypatch.setattr(politica, '_leyes_sancionadas_complementarias', lambda: [extra])
    monkeypatch.setattr(politica, '_hcdn_paginate', lambda *a: [
        fila(1, '2026-06-24'),
        {'LEY': None, 'EXPEDIENTE_INICIAL': '0011-PE-2024', 'SANCION_DEFINITIVA': '2026-08-27T00:00:00'}])
    assert politica.produccion_legislativa_serie()['2026-08'] == 2
