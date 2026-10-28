# -*- coding: utf-8 -*-
"""ADR-0395: la serie de piquetes usa el último año CERRADO, no el en curso."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series as ds


def _serie(monkeypatch, hoy):
    class _D(date):
        @classmethod
        def today(cls):
            return hoy
    monkeypatch.setattr(ds, "date", _D)
    return dict(ds.fetch_protocolo_serie())


def test_el_dato_de_un_anio_entra_en_enero_del_siguiente(monkeypatch):
    s = _serie(monkeypatch, date(2026, 10, 5))
    # ADR-0408: la Ciudad (931 estimado en 2023, 440 en 2024, 240 en 2025).
    assert s["2025-01-01"] == 52.7 and s["2025-12-01"] == 52.7   # 2024 cerrado
    assert s["2026-01-01"] == 74.2 and s["2026-09-01"] == 74.2   # 2025 cerrado


def test_no_hay_puntos_con_un_anio_sin_cerrar(monkeypatch):
    s = _serie(monkeypatch, date(2026, 10, 5))
    assert min(s) == "2025-01-01"          # nada de 2024: sólo existe la base
    assert not any(f.startswith("2024") for f in s)
