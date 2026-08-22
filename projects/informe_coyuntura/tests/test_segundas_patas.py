"""Contratos de las dos dimensiones que dejaron de depender de una sola señal."""
import io
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import itcp
import itvc
import politica


class _Respuesta:
    def __init__(self, *, content=b"", text=""):
        self.content = content
        self.text = text

    def raise_for_status(self):
        return None


def _xlsx_deuda() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "carga"
    ws["A2"] = "Estimación de la carga mensual de los servicios de deuda de las familias"
    ws.append([])
    ws.append([])
    ws.append([])
    ws.append(["Período / Period", "CDF / MS", "CDF / MSA", "CDF / PIB"])
    ws.append([datetime(2023, 10, 1), 10.0, 7.0, 3.0])
    ws.append([datetime(2026, 4, 1), 24.0758, 16.8, 4.6])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _xlsx_jornadas() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "1"
    ws.append(["C1. Conflictos con paro, huelguistas y jornadas de paro"])
    ws.append(["Mes", None, None, None, None, None, None, "Jornadas de paro"])
    ws.append([None, None, None, None, None, None, None, "Total"])
    for mes in range(1, 13):
        ws.append([datetime(2025, mes, 1), None, None, None, None, None, None, mes * 100])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def test_parser_carga_deuda_busca_rotulos_no_numero_de_hoja(monkeypatch):
    monkeypatch.setattr(descargar_series.requests, "get",
                        lambda *args, **kwargs: _Respuesta(content=_xlsx_deuda()))
    serie = descargar_series.fetch_carga_servicio_deuda_serie()
    assert serie == [["2023-10-01", 10.0], ["2026-04-01", 24.076]]


def test_parser_jornadas_suma_exactamente_doce_meses(monkeypatch):
    contenido = _xlsx_jornadas()

    def fake_get(url, **_kwargs):
        if url == politica.CONFLICTOS_LABORALES_URL:
            return _Respuesta(text='<a href="/datos/conflictos-vigente.xlsx">mensual</a>')
        return _Respuesta(content=contenido)

    monkeypatch.setattr(politica.requests, "get", fake_get)
    serie = politica.fetch_jornadas_individuales_no_trabajadas_serie()
    assert serie == [["2025-12-01", 7_800]]


def test_jornadas_usa_planilla_directa_si_falla_la_pagina_indice(monkeypatch):
    contenido = _xlsx_jornadas()

    def fake_get(url, **_kwargs):
        if url == politica.CONFLICTOS_LABORALES_URL:
            raise politica.requests.ConnectionError("landing caída")
        assert url == politica.CONFLICTOS_LABORALES_XLSX_FALLBACK
        return _Respuesta(content=contenido)

    monkeypatch.setattr(politica.requests, "get", fake_get)
    assert politica.fetch_jornadas_individuales_no_trabajadas_serie()[-1] == [
        "2025-12-01", 7_800]


def test_vulnerabilidad_combina_incumplimiento_y_carga():
    indices = {"mora_familias": 20.0, "carga_servicio_deuda_hogares": 50.0}
    dim = itvc.calcular_itvc(indices)["dimensiones"]["vulnerabilidad"]
    assert dim["puntaje"] == 29.0
    assert dim["indicadores"]["mora_familias"]["peso"] == 0.70
    assert dim["indicadores"]["carga_servicio_deuda_hogares"]["peso"] == 0.30


def test_conflicto_social_combina_calle_e_intensidad_laboral():
    valores = {
        "conflictividad_nacional": -40.0,  # 100 puntos
        "jornadas_individuales_no_trabajadas_12m": 11_000_000,  # 10 puntos
    }
    dim = itcp.calcular_itcp(valores)["dimensiones"]["conflicto_social"]
    assert dim["puntaje"] == 64.0
    assert dim["indicadores"]["conflictividad_nacional"]["peso"] == 0.60
    assert dim["indicadores"]["jornadas_individuales_no_trabajadas_12m"]["peso"] == 0.40
