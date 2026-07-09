import sys
import json
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series


class _FakeDate(date):
    """date con .today() fijo, para no depender del reloj real al probar
    la lógica de 'año cerrado vs. año en curso'."""
    _hoy = date(2026, 7, 8)

    @classmethod
    def today(cls):
        return cls._hoy


def test_primera_corrida_baja_y_cachea_todos_los_anios(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "cohesion.json"
    llamados = []

    def fetch_fn(anio, dias_ventana):
        llamados.append(anio)
        return {"valor": 80.0 + anio - 2023}

    serie = descargar_series._serie_cohesion_cacheada(store, fetch_fn, 2023, "test")

    assert llamados == [2023, 2024, 2025, 2026]
    assert serie == [
        ["2023-01-01", 80.0], ["2024-01-01", 81.0],
        ["2025-01-01", 82.0], ["2026-01-01", 83.0],
    ]
    assert json.loads(store.read_text(encoding="utf-8")) == {
        "2023": 80.0, "2024": 81.0, "2025": 82.0, "2026": 83.0,
    }


def test_anio_cerrado_ya_cacheado_no_se_vuelve_a_pedir(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "cohesion.json"
    store.write_text(json.dumps({"2023": 80.0, "2024": 81.0, "2025": 82.0}), encoding="utf-8")
    llamados = []

    def fetch_fn(anio, dias_ventana):
        llamados.append(anio)
        return {"valor": 99.0}

    serie = descargar_series._serie_cohesion_cacheada(store, fetch_fn, 2023, "test")

    # Los 3 años cerrados ya cacheados NO generan requests -- solo el año en curso.
    assert llamados == [2026]
    assert serie == [
        ["2023-01-01", 80.0], ["2024-01-01", 81.0],
        ["2025-01-01", 82.0], ["2026-01-01", 99.0],
    ]


def test_anio_en_curso_siempre_se_repide_aunque_ya_este_cacheado(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "cohesion.json"
    store.write_text(json.dumps({"2026": 90.0}), encoding="utf-8")
    llamados = []

    def fetch_fn(anio, dias_ventana):
        llamados.append(anio)
        return {"valor": 95.0}   # valor nuevo, distinto del cacheado

    serie = descargar_series._serie_cohesion_cacheada(store, fetch_fn, 2026, "test")

    assert llamados == [2026]
    assert serie == [["2026-01-01", 95.0]]   # se actualizó, no quedó pisado por el cache viejo


def test_fallo_del_anio_en_curso_degrada_al_ultimo_valor_cacheado(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "cohesion.json"
    store.write_text(json.dumps({"2026": 93.2}), encoding="utf-8")

    def fetch_fn(anio, dias_ventana):
        raise RuntimeError("timeout de red")

    serie = descargar_series._serie_cohesion_cacheada(store, fetch_fn, 2026, "test")

    # El punto más nuevo NO se pierde: se degrada al último valor cacheado.
    assert serie == [["2026-01-01", 93.2]]


def test_anio_cerrado_sin_dato_y_sin_cache_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    store = tmp_path / "cohesion.json"

    def fetch_fn(anio, dias_ventana):
        return {"valor": None}   # corrida exitosa pero sin actas divididas

    serie = descargar_series._serie_cohesion_cacheada(store, fetch_fn, 2025, "test")

    assert serie == []   # ningún año con dato real -- no se inventa un punto


def test_fetch_cohesion_bloque_serie_usa_el_store_de_diputados(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "COHESION_BLOQUE_STORE", tmp_path / "dip.json")
    monkeypatch.setattr(descargar_series.politica, "fetch_cohesion_bloque",
                         lambda anio, dias_ventana: {"valor": 70.0})
    serie = descargar_series.fetch_cohesion_bloque_serie(anio_inicio=2026)
    assert serie == [["2026-01-01", 70.0]]


def test_fetch_cohesion_bloque_senado_serie_usa_el_store_de_senado(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "COHESION_BLOQUE_SENADO_STORE", tmp_path / "sen.json")
    monkeypatch.setattr(descargar_series.politica, "fetch_cohesion_bloque_senado",
                         lambda anio, dias_ventana: {"valor": 99.7})
    serie = descargar_series.fetch_cohesion_bloque_senado_serie(anio_inicio=2026)
    assert serie == [["2026-01-01", 99.7]]


def test_fetch_alineamiento_senadores_prov_serie_usa_su_propio_store(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "ALINEAMIENTO_SENADORES_STORE", tmp_path / "alineamiento.json")
    monkeypatch.setattr(descargar_series.politica, "fetch_alineamiento_senadores_prov",
                         lambda anio, dias_ventana: {"valor": 66.7})
    serie = descargar_series.fetch_alineamiento_senadores_prov_serie(anio_inicio=2026)
    assert serie == [["2026-01-01", 66.7]]


def test_fines_de_mes_redondea_desde_y_corta_en_hasta():
    puntos = descargar_series._fines_de_mes(date(2026, 1, 15), date(2026, 4, 10))
    assert puntos == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]


def test_actas_alineamiento_cacheadas_anio_cerrado_no_se_vuelve_a_pedir(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "ALINEAMIENTO_SENADORES_ACTAS_STORE", tmp_path / "actas.json")
    (tmp_path / "actas.json").write_text(json.dumps({
        "2023": [{"fecha": "2023-06-01", "provincias": {"CABA": [1, 1]}}],
    }), encoding="utf-8")
    llamados = []

    def fake_fetch(anio):
        llamados.append(anio)
        return [{"fecha": f"{anio}-06-01", "provincias": {"CABA": [1, 1]}}]

    monkeypatch.setattr(descargar_series.politica, "fetch_alineamiento_senadores_actas_anio", fake_fetch)

    cache = descargar_series._actas_alineamiento_cacheadas(2023)

    # 2023 (cerrado) ya estaba cacheado -- solo se re-pide 2024/2025/2026 (en curso).
    assert llamados == [2024, 2025, 2026]
    assert set(cache.keys()) == {"2023", "2024", "2025", "2026"}


def test_fetch_alineamiento_senadores_prov_mensual_deriva_ventanas_rolling(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)   # hoy = 2026-07-08
    monkeypatch.setattr(descargar_series, "ALINEAMIENTO_SENADORES_ACTAS_STORE", tmp_path / "actas.json")

    detalle_2026 = [
        {"fecha": "2026-03-15", "provincias": {"CABA": [1, 1], "Córdoba": [1, 3]}},
        {"fecha": "2026-06-01", "provincias": {"CABA": [0, 1]}},
    ]
    monkeypatch.setattr(descargar_series.politica, "fetch_alineamiento_senadores_actas_anio",
                         lambda anio: detalle_2026 if anio == 2026 else [])

    # anio_inicio=2023 (default real) para que _fines_de_mes arranque en
    # dic-2023 -- con anio_inicio=2026 el punto de partida (dic-2026) caería
    # DESPUÉS de "hoy" (2026-07-08) y la serie saldría vacía.
    serie = descargar_series.fetch_alineamiento_senadores_prov_mensual(anio_inicio=2023, dias_ventana=90)

    # Fin de marzo (31-mar): solo la acta del 15-mar cae en la ventana de 90d.
    # CABA 1/1=100%, Córdoba 1/3=33.3% -> promedio 66.7%.
    marzo = next(p for p in serie if p[0] == "2026-03-31")
    assert marzo[1] == 66.7
    # Fin de junio (30-jun): la acta del 15-mar queda FUERA de la ventana de
    # 90d (15-mar a 30-jun = 107 días) -- solo cuenta la acta del 1-jun
    # (CABA 0/1 -> 0%). Única provincia con señal -> promedio 0%.
    junio = next(p for p in serie if p[0] == "2026-06-30")
    assert junio[1] == 0.0


def test_fetch_alineamiento_senadores_prov_mensual_sin_detalle_devuelve_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(descargar_series, "date", _FakeDate)
    monkeypatch.setattr(descargar_series, "ALINEAMIENTO_SENADORES_ACTAS_STORE", tmp_path / "actas.json")
    monkeypatch.setattr(descargar_series.politica, "fetch_alineamiento_senadores_actas_anio", lambda anio: [])
    assert descargar_series.fetch_alineamiento_senadores_prov_mensual(anio_inicio=2026) == []
