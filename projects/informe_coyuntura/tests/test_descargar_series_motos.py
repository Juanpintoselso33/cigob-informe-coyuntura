import sys
import json
import csv
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series


class _FakeDate(date):
    """date con .today() fijo -- rango chico (nov-2022 a dic-2022) para no
    tener que simular las ~44 llamadas reales de la serie completa."""
    _hoy = date(2023, 1, 15)

    @classmethod
    def today(cls):
        return cls._hoy


def _no_deberia_pedir_red(*a, **kw):
    raise AssertionError("no debería pedir red -- los meses ya estaban en cache")


def test_fetch_motos_serie_cached_usa_cache_existente_sin_pedir_red(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "motos.json"
    store.write_text(json.dumps({"2022-11": 35162, "2022-12": 29282}), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "MOTOS_SERIE_STORE", store)
    monkeypatch.setattr(descargar_series.requests, "get", _no_deberia_pedir_red)

    serie = descargar_series.fetch_motos_serie_cached()

    assert serie == [["2022-11-01", 35162], ["2022-12-01", 29282]]


def test_fetch_motos_serie_cached_completa_solo_el_mes_faltante(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "motos.json"
    store.write_text(json.dumps({"2022-11": 35162}), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "MOTOS_SERIE_STORE", store)

    pedidos = []

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"provinces": [{"count": 15000}, {"count": 14282}]}

    def fake_get(url, params=None, headers=None, timeout=None):
        pedidos.append((params["year"], params["month_start"]))
        return _Resp()

    monkeypatch.setattr(descargar_series.requests, "get", fake_get)

    serie = descargar_series.fetch_motos_serie_cached()

    # Solo pide el mes que faltaba (dic-2022) -- nov-2022 ya estaba cacheado.
    assert pedidos == [(2022, 12)]
    assert serie == [["2022-11-01", 35162], ["2022-12-01", 29282]]
    assert json.loads(store.read_text(encoding="utf-8")) == {"2022-11": 35162, "2022-12": 29282}


def test_fetch_motos_serie_cached_siembra_desde_csv_si_no_hay_store(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    # mismo criterio que el resto de los stores de este archivo (p.ej.
    # ALINEAMIENTO_SENADORES_STORE): el directorio padre (data/vida/) ya
    # existe en el repo real, no se crea acá.
    store = tmp_path / "motos.json"
    monkeypatch.setattr(descargar_series, "MOTOS_SERIE_STORE", store)
    output_dir = tmp_path / "series"
    output_dir.mkdir()
    monkeypatch.setattr(descargar_series, "OUTPUT_DIR", output_dir)

    with open(output_dir / "vida_cotidiana.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "indicador", "valor", "fuente"])
        w.writeheader()
        w.writerow({"fecha": "2022-11-01", "indicador": "patentamiento_motos", "valor": "35162", "fuente": "x"})
        w.writerow({"fecha": "2022-12-01", "indicador": "otro_indicador", "valor": "999", "fuente": "x"})

    pedidos = []

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"provinces": [{"count": 29282}]}

    def fake_get(url, params=None, headers=None, timeout=None):
        pedidos.append((params["year"], params["month_start"]))
        return _Resp()

    monkeypatch.setattr(descargar_series.requests, "get", fake_get)

    serie = descargar_series.fetch_motos_serie_cached()

    # nov-2022 vino sembrado del CSV (fila de patentamiento_motos) -- no se
    # pide a la red. dic-2022 no está en el CSV (esa fila es de otro
    # indicador) -- ese sí se pide.
    assert pedidos == [(2022, 12)]
    assert serie == [["2022-11-01", 35162], ["2022-12-01", 29282]]
