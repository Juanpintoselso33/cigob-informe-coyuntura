# -*- coding: utf-8 -*-
"""ADR-0394: la pobreza del INDEC se fecha al inicio de SU semestre.

La API fecha cada semestre en el mes siguiente a su cierre; el fetcher lo
corría seis meses y la base de `itvc_pobreza` tomaba el semestre equivocado."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series as ds

# Como la entrega la API (del más nuevo al más viejo): fecha de cierre + proporción.
API = [["2026-07-01", 0.323], ["2025-07-01", 0.316], ["2024-01-01", 0.417],
       ["2023-07-01", 0.401], ["2003-07-01", 0.54]]


@pytest.fixture(autouse=True)
def _api_falsa(monkeypatch):
    ds.fetch_pobreza_indec_serie.cache_clear()
    monkeypatch.setattr(ds, "fetch_indec", lambda sid, limit=48: [list(x) for x in API])
    yield
    ds.fetch_pobreza_indec_serie.cache_clear()


def test_cada_semestre_queda_en_su_inicio():
    serie = dict(ds.fetch_pobreza_indec_serie())
    assert serie["2003-01-01"] == 54.0        # 1S-2003
    assert serie["2023-01-01"] == 40.1        # 1S-2023
    assert serie["2023-07-01"] == 41.7        # 2S-2023
    assert serie["2025-01-01"] == 31.6        # 1S-2025
    assert "2024-01-01" not in serie or serie["2024-01-01"] != 41.7


def test_fecha_semestral_inesperada_falla():
    with pytest.raises(ValueError):
        ds._inicio_de_su_semestre("2024-03-01")


def test_base_de_itvc_pobreza_es_el_2s_2023(monkeypatch):
    monkeypatch.setattr(ds, "fetch_pobreza_nowcast_serie",
                        lambda: [["2025-01-01", 41.7], ["2025-02-01", 20.85]])
    out = ds.fetch_itvc_pobreza()
    assert out == [["2025-01-01", 100.0], ["2025-02-01", 200.0]]
