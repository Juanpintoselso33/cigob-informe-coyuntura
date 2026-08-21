"""Regresión offline: serie mensual del FAL.

Desde ADR-0228 la serie mide lo que RIGE —construcción normativa vigente,
vigencia del régimen y adopción— con la misma regla que la card. Sigue sin
tocar la red mientras el régimen no esté vigente: la adopción es cero por razón
legal hasta el 1-nov-2026 y todo lo demás sale del registro local de hechos.
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
    """La serie sale del registro local. Si alguien vuelve a meter una consulta
    al Boletín Oficial por mes, esto lo detiene: eran ~31 consultas por corrida
    para reconstruir una escalera que ya está fechada en las normas. El registro
    de la CNV tampoco se consulta mientras el régimen no rija, porque antes del
    1-nov-2026 la adopción es cero por norma y no por falta de dato."""
    def explota(*a, **kw):
        raise AssertionError("la serie del FAL no debe salir a la red acá")

    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    monkeypatch.setattr(gestion, "_bo_conteo", explota)
    monkeypatch.setattr(gestion, "_cnv_registro_fci", explota)

    serie = descargar_series.fetch_fal_serie()
    assert len(serie) == 31, "dic-2023 hasta el último mes completo (jun-2026)"
    assert serie[0][0] == "2023-12-01"
    assert serie[-1][0] == "2026-06-01"


def test_cada_peldano_cae_en_el_mes_de_su_hecho(monkeypatch):
    """El salto tiene que coincidir con la publicación de la norma o con la
    resolución judicial, no con una fecha elegida: es lo que hace la serie
    auditable contra InfoLeg y contra los fallos."""
    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    por_fecha = dict(descargar_series.fetch_fal_serie())

    assert por_fecha["2026-02-01"] == 0.0    # antes de la ley
    assert por_fecha["2026-03-01"] == 0.0    # publicada el 6, suspendida el 30
    assert por_fecha["2026-04-01"] == 25.0   # cautelar levantada el 23-abr
    assert por_fecha["2026-05-01"] == 25.0   # ley firme, sin reglamentar
    assert por_fecha["2026-06-01"] == 50.0   # Decreto 408/2026 — 01-jun-2026


def test_el_techo_de_la_serie_queda_reservado(monkeypatch):
    """Ningún mes puede valer 100 antes de la vigencia del régimen: los otros
    cincuenta puntos son vigencia y adopción, y las dos son legalmente
    imposibles hasta el 1-nov-2026. Es la propiedad que ADR-0142 perdió."""
    monkeypatch.setattr(descargar_series, "date", _FechaFija)
    serie = descargar_series.fetch_fal_serie()
    assert max(v for _, v in serie) == 50.0
