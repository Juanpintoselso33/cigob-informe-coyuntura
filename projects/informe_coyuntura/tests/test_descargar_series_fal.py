"""Regresión offline: serie mensual del FAL por sus dos actos fundamentales.

Reemplaza a los dos tests que describían la escala de tres etapas de ADR-0098
(construcción + vigencia + adopción, con una consulta al Boletín Oficial por mes
y fallback al histórico). Desde ADR-0142 la serie sale entera del registro de
hitos y no toca la red: es una escalera de tres peldaños fechada en las normas.
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series  # noqa: E402
import gestion  # noqa: E402


class _FechaFija(date):
    @classmethod
    def today(cls):
        return cls(2026, 7, 15)


def test_la_serie_no_toca_la_red(monkeypatch):
    """La serie sale del registro local de hitos. Si alguien vuelve a meter una
    consulta al Boletín Oficial por mes, esto lo detiene: eran ~31 consultas por
    corrida para reconstruir una escalera que ya está fechada en las normas."""
    def explota(*a, **kw):
        raise AssertionError("la serie del FAL no debe consultar el Boletín Oficial")

    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    monkeypatch.setattr(gestion, "_bo_conteo", explota)
    monkeypatch.setattr(gestion, "_cnv_fondos_cese", explota)

    serie = descargar_series.fetch_fal_serie()
    assert len(serie) == 31, "dic-2023 hasta el último mes completo (jun-2026)"
    assert serie[0][0] == "2023-12-01"
    assert serie[-1][0] == "2026-06-01"


def test_cada_peldano_cae_en_el_mes_de_su_norma(monkeypatch):
    """El salto tiene que coincidir con la publicación de la norma, no con una
    fecha elegida: es lo que hace la serie auditable contra InfoLeg."""
    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    por_fecha = dict(descargar_series.fetch_fal_serie())

    assert por_fecha["2026-02-01"] == 0.0    # antes de la ley
    assert por_fecha["2026-03-01"] == 50.0   # Ley 27.802 — publicada 06-mar-2026
    assert por_fecha["2026-05-01"] == 50.0   # sancionada, sin reglamentar
    assert por_fecha["2026-06-01"] == 100.0  # Decreto 408/2026 — 01-jun-2026


def test_la_serie_no_retrocede(monkeypatch):
    """Los actos no se deshacen. Es la propiedad que hace al indicador auditable
    y, a la vez, la que lo dejó sin recorrido (ADR-0142)."""
    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    serie = descargar_series.fetch_fal_serie()
    assert all(b >= a for (_, a), (_, b) in zip(serie, serie[1:]))
    assert {v for _, v in serie} == {0.0, 50.0, 100.0}
