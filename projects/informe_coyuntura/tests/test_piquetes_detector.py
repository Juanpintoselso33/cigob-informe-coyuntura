import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion


@pytest.fixture(autouse=True)
def anclajes(tmp_path, monkeypatch):
    p = tmp_path / 'piquetes.json'
    p.write_text('{"caba": {"2023": 931, "2025": 240}}')
    monkeypatch.setattr(gestion, 'DP_PIQUETES_PATH', p)


def test_http_exitoso_sin_informes_no_certifica_vigencia(monkeypatch):
    monkeypatch.setattr(gestion.requests, 'get', lambda *a, **k: SimpleNamespace(
        text='Account Suspended', raise_for_status=lambda: None))
    card = gestion.fetch_protocolo_antipiquetes()
    assert card['valor'] == 74.2
    assert 'No se pudo verificar' in card['detalle_txt']
    assert card['advertencia_fuente']


def test_nuevo_anio_no_queda_solo_en_el_log(monkeypatch):
    monkeypatch.setattr(gestion.requests, 'get', lambda *a, **k: SimpleNamespace(
        text='Piquetes en 2026', raise_for_status=lambda: None))
    card = gestion.fetch_protocolo_antipiquetes()
    assert '2026' in card['advertencia_fuente']
    assert card['fecha_dato'] == '2025-12-31'
