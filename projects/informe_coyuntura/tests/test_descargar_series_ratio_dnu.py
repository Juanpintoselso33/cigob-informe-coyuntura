"""Regresión offline: serie mensual de ratio_dnu con ventana móvil (ADR-0058).

Desde ADR-0415 la serie baja leyes y DNU UNA vez para todo el tramo y cuenta
cada ventana con `politica.ratio_dnu_contar`, la misma función que la card."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import politica


def _fake_infoleg(monkeypatch, leyes, dnus):
    pedidos = []

    def listado(ses, au, tipo, desde, hasta, texto="", invisibles_tolerados=0):
        pedidos.append(("1", desde, hasta))
        return [dict(it) for it in leyes if desde.isoformat() <= it["fecha_pub"] <= hasta.isoformat()]

    def contar(ses, au, desde, hasta):
        pedidos.append(("2", desde, hasta))
        d = [it for it in dnus if desde.isoformat() <= it["fecha_pub"] <= hasta.isoformat()]
        return len(d), d

    monkeypatch.setattr(politica, "_infoleg_abrir_sesion", lambda: (None, "x"))
    monkeypatch.setattr(politica, "_infoleg_listado_completo", listado)
    monkeypatch.setattr(politica, "_infoleg_contar_dnus", contar)
    return pedidos


def _ley(i, fecha):
    return {"infoleg_id": f"l{i}", "norma": f"Ley {27000 + i}", "fecha_pub": fecha,
            "sumario": "REGIMEN PENAL DISPOSICIONES"}


def _dnu(i, fecha):
    return {"infoleg_id": f"d{i}", "norma": f"Decreto DNU {i} / 2023", "fecha_pub": fecha}


def test_fetch_ratio_dnu_serie_ventana_movil_por_mes(monkeypatch):
    """Un punto por MES (no por año), cada uno sobre la ventana móvil de 365
    días que cierra ese mes; los insumos se bajan una sola vez."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 2, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    leyes = [_ley(i, "2023-06-10") for i in range(10)]
    dnus = [_dnu(i, "2023-06-11") for i in range(15)] + [_dnu(99, "2024-02-01")]
    pedidos = _fake_infoleg(monkeypatch, leyes, dnus)

    serie = descargar_series.fetch_ratio_dnu_serie()

    assert serie == [
        ["2023-12-01", 1.5],
        ["2024-01-01", 1.5],
        ["2024-02-01", 1.6],
    ]
    # leyes por año calendario del tramo (ene-2023 a hoy) + UNA de DNU
    assert pedidos == [("1", date(2023, 1, 1), date(2023, 12, 31)),
                       ("1", date(2024, 1, 1), date(2024, 2, 15)),
                       ("2", date(2023, 1, 1), date(2024, 2, 15))]


def test_fetch_ratio_dnu_serie_omite_mes_sin_leyes(monkeypatch):
    """Si una ventana no trae leyes, se omite ese punto en vez de dividir por
    cero — mismo criterio que el indicador titular."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 1, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    leyes = [_ley(i, "2024-01-05") for i in range(10)]
    dnus = [_dnu(i, "2023-12-20") for i in range(15)]
    _fake_infoleg(monkeypatch, leyes, dnus)

    serie = descargar_series.fetch_ratio_dnu_serie()

    assert serie == [["2024-01-01", 1.5]]
