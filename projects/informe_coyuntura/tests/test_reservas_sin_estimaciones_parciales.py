"""Un insumo ausente no es cero ni habilita otra definición de reservas."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import macro
import descargar_series
import pytest


def test_sin_sdds_no_sustituye_formula_aunque_config_sea_del_mismo_mes(monkeypatch, tmp_path):
    monkeypatch.setattr(macro, '_reservas_netas_sdds',
                        lambda: (_ for _ in ()).throw(ValueError('fuente caída')))
    config = tmp_path / 'pasivos.json'
    config.write_text('{"actualizado":"2026-07-31","drenajes_seccion_ii":40000}')
    monkeypatch.setattr(macro, 'RESERVAS_PASIVOS_PATH', config)
    monkeypatch.setattr(macro, '_bcra_ultimo', lambda _: {'valor':47599, 'fecha':'2026-07-31'})
    monkeypatch.setattr(macro, '_tesoro_deposits_usd', lambda _: 3606)
    assert macro.fetch_reservas_netas() is None


@pytest.mark.parametrize('tesoro,esperado', [({}, []), ({'2026-07':0}, [['2026-07-01',1200]])])
def test_historia_distingue_tesoro_ausente_de_cero(monkeypatch, tesoro, esperado):
    monkeypatch.setattr(descargar_series, '_tesoro_por_mes', lambda: tesoro)
    monkeypatch.setattr(descargar_series.requests, 'get', lambda *a, **kw:
                        SimpleNamespace(status_code=200,content=b'x'*50001))
    monkeypatch.setattr(macro, '_parse_sdds_content', lambda _: {
        'fecha':'31/07/26','netas':1000,'bopreal_12m':-200})
    assert descargar_series.fetch_reservas_netas_serie(meses=1) == esperado


@pytest.mark.parametrize('tramos,esperado', [('',None), (' -80,00 -20,00 0,00',0)])
def test_parser_no_convierte_columna_ausente_en_cero(monkeypatch,tramos,esperado):
    import pdfplumber
    texto=('A. Activos de reserva oficiales 500,00\n'
           'Préstamos en moneda extranjera, valores, y depósitos -100,00'+tramos+'\n'
           'swaps de monedas)\n-50,00\n3. Otros (especificar) -10,00')
    class PDF:
        pages=[SimpleNamespace(extract_text=lambda: texto)]
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(pdfplumber,'open',lambda _:PDF())
    resultado=macro._parse_sdds_content(b'pdf')
    if esperado is None:
        assert resultado is None
    else:
        assert resultado['bopreal_12m'] == esperado
