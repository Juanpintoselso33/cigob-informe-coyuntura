# -*- coding: utf-8 -*-
"""Store persistente del Nowcast de Pobreza (mismo patrón que `fetch_ivi_serie`).

Antes, `fetch_pobreza_nowcast_serie` bajaba y parseaba TODOS los PDF
publicados por la UTDT en cada corrida (~140s medidos, hasta 400s+ según la
red). Estos tests cubren el store: que un informe ya visto no se vuelve a
parsear si su Content-Length no cambió, que uno nuevo sí se lee y se guarda,
que un cambio de tamaño en una URL ya conocida dispara una relectura puntual
y una alerta (el riesgo real: el `fname` es un timestamp de subida, no un
hash -- nada impide en principio que la UTDT reemplace el PDF de una URL sin
cambiar la URL), que la regla "gana el más nuevo" (ADR-0153) sobrevive a la
mezcla store/red, y que las fallas (listado caído, un PDF puntual caído, un
informe viejo no parseable) se comportan igual que en el resto del archivo.

No hay red acá: `utdt_nowcast_pobreza` se reemplaza en `sys.modules` por un
stub, igual que hace `descargar_series.fetch_pobreza_nowcast_serie` con su
import diferido (`from utdt_nowcast_pobreza import ...` adentro de la
función), así no hace falta el `config.py` real de vida_cotidiana ni tocar
la red.
"""
import sys
import json
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series


@pytest.fixture(autouse=True)
def _limpiar_cache_una_vez_por_corrida():
    """fetch_pobreza_nowcast_serie está decorada con @_una_sola_vez_por_corrida
    (un lru_cache de un solo slot, atado al objeto función en el módulo) --
    sin este fixture, el resultado del primer test de este archivo quedaría
    pegado para todos los que corren después en la misma sesión de pytest."""
    descargar_series.fetch_pobreza_nowcast_serie.cache_clear()
    yield
    descargar_series.fetch_pobreza_nowcast_serie.cache_clear()


def _instalar_fake_colector(monkeypatch, listar, leer, huecos=None):
    """Planta un `utdt_nowcast_pobreza` de mentira en sys.modules.

    El import de `fetch_pobreza_nowcast_serie` es diferido (adentro de la
    función) y Python resuelve `from X import ...` contra sys.modules
    primero -- alcanza con poner el stub ahí para que la función lo use.
    """
    fake = types.ModuleType("utdt_nowcast_pobreza")
    fake._listar_informes = listar
    fake._leer_informe = leer
    fake._huecos = huecos or (lambda serie: [])
    fake.NOWCAST_DESCARGA = "https://www.utdt.edu/download.php?fname="
    monkeypatch.setitem(sys.modules, "utdt_nowcast_pobreza", fake)
    return fake


def _fake_head(largo_por_fname, llamadas=None):
    """`requests.head` de mentira: responde el Content-Length pedido para
    cada fname (o ninguno, simulando una respuesta sin ese header)."""
    class _Resp:
        def __init__(self, largo):
            self.headers = {} if largo is None else {"Content-Length": str(largo)}

    def _head(url, headers=None, timeout=None, verify=None, allow_redirects=None):
        fname = url.split("fname=")[1]
        if llamadas is not None:
            llamadas.append(fname)
        return _Resp(largo_por_fname.get(fname))
    return _head


def _informe(periodo, valor):
    return {"periodo": periodo, "valor": valor, "semestre": "x", "ic_inf": None, "ic_sup": None}


def _escribir_store(path, informes, meta=None):
    path.write_text(json.dumps({"_meta": meta or {}, "informes": informes}, ensure_ascii=False),
                     encoding="utf-8")


# ── Cache hit: Content-Length sin cambios no vuelve a leer ──────────────────

def test_content_length_sin_cambios_no_vuelve_a_leer(tmp_path, monkeypatch):
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {
        "_1.pdf": {"periodo": "2025-01", "valor": 35.8, "content_length": 1000},
        "_2.pdf": {"periodo": "2025-02", "valor": 34.9, "content_length": 2000},
    })
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _no_deberia_leer(fname):
        raise AssertionError(f"no debería reparsear {fname} -- el Content-Length no cambió")

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf", "_2.pdf"], leer=_no_deberia_leer)
    monkeypatch.setattr(descargar_series.requests, "head",
                         _fake_head({"_1.pdf": 1000, "_2.pdf": 2000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == [["2025-01-01", 35.8], ["2025-02-01", 34.9]]


# ── Informe nuevo: se lee y se guarda en el store ───────────────────────────

def test_informe_nuevo_se_lee_y_se_guarda(tmp_path, monkeypatch):
    store = tmp_path / "pobreza_nowcast_serie.json"   # no existe todavía
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    llamadas = []

    def _leer(fname):
        llamadas.append(fname)
        return _informe("2025-01", 35.8)

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf"], leer=_leer)
    monkeypatch.setattr(descargar_series.requests, "head", _fake_head({"_1.pdf": 1000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert llamadas == ["_1.pdf"]
    assert serie == [["2025-01-01", 35.8]]
    guardado = json.loads(store.read_text(encoding="utf-8"))
    assert guardado["informes"]["_1.pdf"] == {
        "periodo": "2025-01", "valor": 35.8, "content_length": 1000}


# ── Un URL ya conocido que cambió de tamaño: alerta + relectura puntual ────

def test_content_length_distinto_dispara_alerta_y_relectura(tmp_path, monkeypatch, capsys):
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {"_1.pdf": {"periodo": "2025-01", "valor": 35.8, "content_length": 1000}})
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    llamadas = []

    def _leer(fname):
        llamadas.append(fname)
        return _informe("2025-01", 99.9)   # "contenido" corregido

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf"], leer=_leer)
    monkeypatch.setattr(descargar_series.requests, "head", _fake_head({"_1.pdf": 5000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert llamadas == ["_1.pdf"], "un cambio de tamaño debe forzar la relectura de ESE informe"
    assert serie == [["2025-01-01", 99.9]]
    salida = capsys.readouterr().out
    assert "ALERTA" in salida and "_1.pdf" in salida, (
        "el reemplazo silencioso de un PDF en la misma URL tiene que ser detectable, no mudo"
    )
    guardado = json.loads(store.read_text(encoding="utf-8"))
    assert guardado["informes"]["_1.pdf"] == {
        "periodo": "2025-01", "valor": 99.9, "content_length": 5000}


# ── "Gana el más nuevo" (ADR-0153) sobrevive a la mezcla store + red ───────

def test_gana_el_mas_nuevo_entre_un_informe_del_store_y_uno_nuevo(tmp_path, monkeypatch):
    """_1.pdf (ya en el store) y _2.pdf (nuevo) declaran el MISMO semestre con
    valores distintos. _2.pdf es cronológicamente posterior (mismo criterio
    de orden que usa _listar_informes) y tiene que ganar, sea cual sea el
    origen -- store o red recién leída -- de cada uno."""
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {"_1.pdf": {"periodo": "2025-06", "valor": 30.0, "content_length": 1000}})
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _leer(fname):
        assert fname == "_2.pdf"
        return _informe("2025-06", 31.5)

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf", "_2.pdf"], leer=_leer)
    monkeypatch.setattr(descargar_series.requests, "head",
                         _fake_head({"_1.pdf": 1000, "_2.pdf": 2000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == [["2025-06-01", 31.5]], "el informe más nuevo (_2.pdf) debe ganar el semestre"


# ── Fallas: el listado cae, un PDF puntual cae, un informe viejo no parsea ─

def test_si_el_listado_falla_la_serie_sale_del_store_sin_romper(tmp_path, monkeypatch, capsys):
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {"_1.pdf": {"periodo": "2025-01", "valor": 35.8, "content_length": 1000}})
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _listar():
        raise RuntimeError("sin red")

    def _no_deberia_leer(fname):
        raise AssertionError("no debería intentar leer nada si ni siquiera hay listado")

    _instalar_fake_colector(monkeypatch, listar=_listar, leer=_no_deberia_leer)

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == [["2025-01-01", 35.8]]
    assert "WARN" in capsys.readouterr().out


def test_si_un_pdf_puntual_falla_no_rompe_la_corrida_ni_se_marca_procesado(tmp_path, monkeypatch, capsys):
    store = tmp_path / "pobreza_nowcast_serie.json"   # no existe todavía
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _leer(fname):
        raise RuntimeError("timeout")

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf"], leer=_leer)
    monkeypatch.setattr(descargar_series.requests, "head", _fake_head({"_1.pdf": 1000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == []
    assert "WARN" in capsys.readouterr().out
    assert not store.exists(), "nada que guardar -- el informe se reintenta la próxima corrida"


def test_informe_no_parseable_no_se_reintenta_para_siempre(tmp_path, monkeypatch):
    """Los informes más viejos tienen otro layout y `_leer_informe` devuelve
    None -- el store lo recuerda como "ya visto, sin valor" y no lo vuelve a
    pedir mientras su Content-Length no cambie (igual que el resto de la
    historia nunca parseable de este colector)."""
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {"_viejo.pdf": {"periodo": None, "valor": None, "content_length": 500}})
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _no_deberia_leer(fname):
        raise AssertionError("un informe ya marcado sin valor, con el mismo tamaño, "
                              "no debería reintentarse en cada corrida")

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_viejo.pdf"], leer=_no_deberia_leer)
    monkeypatch.setattr(descargar_series.requests, "head", _fake_head({"_viejo.pdf": 500}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == []


# ── Backfill: un HEAD que había fallado no deja el informe ciego para siempre ─

def test_head_sin_content_length_previo_se_completa_sin_releer(tmp_path, monkeypatch):
    """Si el primer HEAD de un informe falló (o no vino con Content-Length),
    quedó guardado con content_length=None -- eso lo dejaría sin verificación
    de staleness para siempre. En cuanto un HEAD posterior sí responde, el
    valor se completa SIN gastar una relectura del PDF."""
    store = tmp_path / "pobreza_nowcast_serie.json"
    _escribir_store(store, {"_1.pdf": {"periodo": "2025-01", "valor": 35.8, "content_length": None}})
    monkeypatch.setattr(descargar_series, "POBREZA_NOWCAST_SERIE_STORE", store)

    def _no_deberia_leer(fname):
        raise AssertionError("completar el fingerprint no debería gastar una relectura")

    _instalar_fake_colector(monkeypatch, listar=lambda: ["_1.pdf"], leer=_no_deberia_leer)
    monkeypatch.setattr(descargar_series.requests, "head", _fake_head({"_1.pdf": 1000}))

    serie = descargar_series.fetch_pobreza_nowcast_serie()

    assert serie == [["2025-01-01", 35.8]]
    guardado = json.loads(store.read_text(encoding="utf-8"))
    assert guardado["informes"]["_1.pdf"]["content_length"] == 1000
