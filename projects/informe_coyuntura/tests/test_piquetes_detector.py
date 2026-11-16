import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion


@pytest.fixture(autouse=True)
def anclajes(tmp_path, monkeypatch):
    p = tmp_path / 'piquetes.json'
    # ADR-0408: puntúa la Ciudad; el total nacional queda como contexto (con
    # otro valor, para que el test detecte si se vuelve a leer la clave nacional).
    p.write_text('{"nacional": {"2023": 8239, "2025": 3893}, "caba": {"2023": 931, "2025": 240}}')
    monkeypatch.setattr(gestion, 'DP_PIQUETES_PATH', p)


def test_http_exitoso_sin_informes_no_es_falla(monkeypatch):
    """Desde el 15-nov-2026 el sitio de Diagnóstico Político sólo muestra el
    cierre anual, en enero: una página sin años nuevos es lo normal y no se
    publica como «no se pudo verificar» (test_detector_piquetes_dp)."""
    monkeypatch.setattr(gestion.requests, 'get', lambda *a, **k: SimpleNamespace(
        text='Account Suspended', raise_for_status=lambda: None))
    card = gestion.fetch_protocolo_antipiquetes()
    assert card['valor'] == 74.2
    assert card['advertencia_fuente'] == ''


def test_si_la_pagina_no_responde_lo_dice(monkeypatch):
    def caida(*a, **k):
        raise gestion.requests.ConnectionError("caído")
    monkeypatch.setattr(gestion.requests, 'get', caida)
    card = gestion.fetch_protocolo_antipiquetes()
    assert 'No se pudo verificar' in card['detalle_txt']


def test_nuevo_anio_no_queda_solo_en_el_log(monkeypatch):
    monkeypatch.setattr(gestion.requests, 'get', lambda *a, **k: SimpleNamespace(
        text='Piquetes en 2026', raise_for_status=lambda: None))
    card = gestion.fetch_protocolo_antipiquetes()
    assert '2026' in card['advertencia_fuente']
    assert card['fecha_dato'] == '2025-12-31'
