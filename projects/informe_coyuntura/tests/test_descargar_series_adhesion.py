import sys
import json
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series
import politica


class _FakeDate(date):
    # abr-2026 para que fin de marzo (31/03) ya haya "cerrado" -- _fines_de_mes
    # excluye el mes en curso si su propio fin de mes cae después de "hoy".
    _hoy = date(2026, 4, 5)

    @classmethod
    def today(cls):
        return cls._hoy


def test_fetch_adhesion_reformas_provincial_serie_reconstruye_acumulado_mensual(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    fechas_path = tmp_path / "fechas.json"
    fechas_path.write_text(json.dumps({
        "_meta": {"nota": "no es una provincia, debe ignorarse"},
        "PROVINCIA_A": {"fecha": "2026-01-10", "criterio": "publicacion_bo"},
        "PROVINCIA_B": {"fecha": "2026-02-20", "criterio": "publicacion_bo"},
    }), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "ADHESION_REFORMAS_FECHAS_PATH", fechas_path)
    monkeypatch.setattr(politica, "_provincias_adheridas_rigi", lambda: {"PROVINCIA_A", "PROVINCIA_B"})

    serie = descargar_series.fetch_adhesion_reformas_provincial_serie()

    assert serie == [
        ["2026-01-31", round(1 / 24 * 100, 1)],
        ["2026-02-28", round(2 / 24 * 100, 1)],
        ["2026-03-31", round(2 / 24 * 100, 1)],
    ]


def test_fetch_adhesion_reformas_provincial_serie_excluye_provincias_sin_fecha_investigada(tmp_path, monkeypatch, capsys):
    # una provincia nueva que adhirió pero todavía no fue investigada a mano
    # no debe inventarse una fecha -- se excluye del histórico (con WARN) y
    # solo cuenta en el valor live de la card (politica.fetch_adhesion_reformas_provincial).
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    fechas_path = tmp_path / "fechas.json"
    fechas_path.write_text(json.dumps({
        "PROVINCIA_A": {"fecha": "2026-01-10", "criterio": "publicacion_bo"},
    }), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "ADHESION_REFORMAS_FECHAS_PATH", fechas_path)
    monkeypatch.setattr(politica, "_provincias_adheridas_rigi",
                         lambda: {"PROVINCIA_A", "PROVINCIA_NUEVA_SIN_FECHA"})

    serie = descargar_series.fetch_adhesion_reformas_provincial_serie()

    assert all(v == round(1 / 24 * 100, 1) for _, v in serie)   # solo PROVINCIA_A cuenta
    assert "PROVINCIA_NUEVA_SIN_FECHA" in capsys.readouterr().out


def test_fetch_adhesion_reformas_provincial_serie_sin_provincias_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(politica, "_provincias_adheridas_rigi", lambda: None)
    assert descargar_series.fetch_adhesion_reformas_provincial_serie() == []


def test_fetch_adhesion_reformas_provincial_serie_sin_archivo_de_fechas_devuelve_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "ADHESION_REFORMAS_FECHAS_PATH", tmp_path / "no_existe.json")
    monkeypatch.setattr(politica, "_provincias_adheridas_rigi", lambda: {"PROVINCIA_A"})
    assert descargar_series.fetch_adhesion_reformas_provincial_serie() == []


def test_provincias_adheridas_rigi_dedupe_filas_repetidas(monkeypatch):
    class _FakeResp:
        status_code = 200
        text = (
            "<table>"
            "<tr><td>Catamarca</td><td>x</td></tr>"
            "<tr><td>Catamarca</td><td>x</td></tr>"  # fila duplicada (hallazgo real MAGyP)
            "<tr><td>Chubut</td><td>x</td></tr>"
            "</table>"
        )
    monkeypatch.setattr(politica.requests, "get", lambda *a, **kw: _FakeResp())
    assert politica._provincias_adheridas_rigi() == {"CATAMARCA", "CHUBUT"}


def test_provincias_adheridas_rigi_request_fallido_devuelve_none(monkeypatch):
    monkeypatch.setattr(politica.requests, "get", lambda *a, **kw: (_ for _ in ()).throw(politica.requests.RequestException()))
    assert politica._provincias_adheridas_rigi() is None
