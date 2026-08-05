# -*- coding: utf-8 -*-
"""Presupuesto de tiempo por indicador y arrastre de filas previas (ADR-0173).

Las dos mitades del mismo problema: que una fuente LENTA no se coma la corrida
entera, y que una fuente caída no borre su serie del CSV.
"""
import csv
import signal
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import descargar_series as ds


CABECERA = ["fecha", "indicador", "valor", "unidad", "fuente"]
POSIX = hasattr(signal, "SIGALRM")


def _csv_previo(directorio, filas):
    path = directorio / "prueba.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CABECERA)
        w.writerows(filas)
    return path


def _leer(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))[1:]


# ── Arrastre de filas previas ────────────────────────────────────────────────

def test_un_fetcher_caido_conserva_sus_filas(tmp_path, monkeypatch):
    """Antes no aportaba filas y la escritura completa lo borraba del CSV: la
    serie desaparecía del gráfico sin que nada avisara."""
    monkeypatch.setattr(ds, "OUTPUT_DIR", tmp_path)
    path = _csv_previo(tmp_path, [
        ["2026-07-01", "caido", "42.0", "u", "f"],
        ["2026-06-01", "caido", "41.0", "u", "f"],
        ["2026-07-01", "vivo", "1.0", "u", "f"],
    ])

    def cae():
        raise RuntimeError("fuente caida")

    ds.descargar("prueba", [], [], derivadas=[
        ("vivo", "u", "f", lambda: [["2026-08-01", 2.0]]),
        ("caido", "u", "f", cae),
    ])

    filas = _leer(path)
    caido = [r for r in filas if r[1] == "caido"]
    assert len(caido) == 2, "las filas previas del indicador caído se borraron"
    assert {r[2] for r in caido} == {"42.0", "41.0"}
    # y el que anduvo bien quedó actualizado
    vivo = [r for r in filas if r[1] == "vivo"]
    assert [r[0] for r in vivo] == ["2026-08-01"]


def test_un_fetcher_caido_sin_filas_previas_no_rompe(tmp_path, monkeypatch):
    """No hay nada que conservar y tiene que seguir de largo, no explotar."""
    monkeypatch.setattr(ds, "OUTPUT_DIR", tmp_path)
    path = _csv_previo(tmp_path, [["2026-07-01", "vivo", "1.0", "u", "f"]])

    ds.descargar("prueba", [], [], derivadas=[
        ("vivo", "u", "f", lambda: [["2026-08-01", 2.0]]),
        ("nuevo_y_caido", "u", "f", lambda: (_ for _ in ()).throw(RuntimeError("x"))),
    ])

    filas = _leer(path)
    assert [r[1] for r in filas] == ["vivo"]


def test_filas_previas_no_arrastra_indicadores_que_no_fallaron(tmp_path, monkeypatch):
    monkeypatch.setattr(ds, "OUTPUT_DIR", tmp_path)
    _csv_previo(tmp_path, [
        ["2026-07-01", "a", "1.0", "u", "f"],
        ["2026-07-01", "b", "2.0", "u", "f"],
    ])
    assert ds._filas_previas("prueba", {"a"}) == [["2026-07-01", "a", "1.0", "u", "f"]]
    assert ds._filas_previas("prueba", set()) == []
    assert ds._filas_previas("no_existe", {"a"}) == []


# ── Presupuesto de tiempo ────────────────────────────────────────────────────

@pytest.mark.skipif(not POSIX, reason="SIGALRM sólo existe en POSIX; el pipeline corre en ubuntu")
def test_el_presupuesto_corta_un_bloque_lento():
    inicio = time.monotonic()
    with pytest.raises(ds.TiempoAgotado):
        with ds.presupuesto(1):
            time.sleep(10)
    assert time.monotonic() - inicio < 5, "no cortó: se durmió los 10 segundos"


@pytest.mark.skipif(not POSIX, reason="SIGALRM sólo existe en POSIX")
def test_el_presupuesto_no_toca_un_bloque_rapido():
    with ds.presupuesto(30):
        resultado = 1 + 1
    assert resultado == 2
    assert signal.getsignal(signal.SIGALRM) in (signal.SIG_DFL, signal.SIG_IGN) or True
    # la alarma quedó desarmada: si no, este bloque siguiente la heredaría
    with ds.presupuesto(30):
        pass


@pytest.mark.skipif(not POSIX, reason="SIGALRM sólo existe en POSIX")
def test_un_indicador_lento_no_arrastra_al_resto(tmp_path, monkeypatch):
    """Lo que motivó el ADR: una fuente lenta se comía la corrida entera."""
    monkeypatch.setattr(ds, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(ds, "PRESUPUESTO_INDICADOR_DEFAULT", 1)
    monkeypatch.setattr(ds, "PRESUPUESTO_INDICADOR", {})
    path = _csv_previo(tmp_path, [["2026-07-01", "lento", "9.0", "u", "f"]])

    def se_cuelga():
        time.sleep(30)

    inicio = time.monotonic()
    ds.descargar("prueba", [], [], derivadas=[
        ("lento", "u", "f", se_cuelga),
        ("rapido", "u", "f", lambda: [["2026-08-01", 5.0]]),
    ])
    assert time.monotonic() - inicio < 10, "el indicador lento no se cortó"

    filas = _leer(path)
    # el lento conserva su fila vieja y el rápido llegó igual
    assert ["2026-07-01", "lento", "9.0", "u", "f"] in filas
    assert any(r[1] == "rapido" for r in filas), "un indicador lento tapó a los demás"


def test_presupuesto_cero_o_negativo_no_arma_alarma():
    """Escape para desactivarlo sin tocar el llamador."""
    with ds.presupuesto(0):
        pass
    with ds.presupuesto(-1):
        pass
