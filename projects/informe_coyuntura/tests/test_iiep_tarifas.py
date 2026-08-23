"""Regresiones del indicador de asequibilidad de servicios (sin red)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(1, str(ROOT / "scripts" / "vida_cotidiana" / "collectors"))

import descargar_series
from iiep_tarifas import (_parsear_reporte, _parsear_texto_pdf, _periodo,
                          _validar_para_puntuar)


def test_parsea_el_dato_que_publica_el_iiep():
    html = """
      <h1>Reporte de Tarifas y Subsidios Agosto 2026</h1>
      <div>14,5% PESO EN EL SALARIO</div>
      <div>-2,1% CANASTA DE SERVICIOS</div>
      <div>55% COBERTURA TARIFARIA</div>
      <p>El transporte (43% de la canasta) creció.</p>
    """
    url = "https://economicas.uba.ar/iiep/reporte-agosto-2026/"
    dato = _parsear_reporte(html, "Reporte de Tarifas y Subsidios Agosto 2026", url)
    assert dato == {
        "valor": 14.5,
        "peso_salario_pct": 14.5,
        "variacion_mensual_pct": -2.1,
        "cobertura_costos_pct": 55.0,
        "transporte_pct_canasta": 43.0,
        "fecha": "2026-08-01",
        "url": url,
    }
    assert _periodo("Reporte de Tarifas y Subsidios diciembre 2025") == "2025-12-01"


def test_anclas_internacionales_se_traducen_a_tension(monkeypatch):
    monkeypatch.setattr(
        descargar_series,
        "fetch_peso_tarifas_iiep_historia",
        lambda: [
            {"fecha": "ambos_justo", "valor": 15.0, "transporte_pct_canasta": 33.3333},
            {"fecha": "transporte_medio", "valor": 17.5, "transporte_pct_canasta": 42.8571},
            {"fecha": "transporte_max", "valor": 20.0, "transporte_pct_canasta": 50.0},
            {"fecha": "actual", "valor": 14.5, "transporte_pct_canasta": 43.0},
        ],
    )
    assert descargar_series.fetch_itvc_tarifas() == [
        ["ambos_justo", 125.0], ["transporte_medio", 100.0],
        ["transporte_max", 75.0], ["actual", 112.6]
    ]


def test_no_publica_total_si_falta_el_desglose_que_puntua():
    dato = {
        "valor": 14.5,
        "transporte_pct_canasta": None,
        "fecha": "2026-08-01",
    }
    import pytest
    with pytest.raises(ValueError, match="transporte_pct_canasta"):
        _validar_para_puntuar(dato)


def test_backfill_pdf_usa_cifras_textuales_y_no_el_grafico():
    texto = """
      Este gasto aumentó 17,5% respecto del mes anterior.
      La canasta de servicios públicos del AMBA de mayo representa el 14,1%
      del salario promedio registrado estimado de mayo.
      A su vez, el peso del gasto en transporte explica el 48% de la canasta.
    """
    dato = _parsear_texto_pdf(
        texto,
        "Reporte de Tarifas y Subsidios Mayo 2026",
        "https://economicas.uba.ar/iiep/reporte-mayo-2026/",
    )
    assert dato["valor"] == 14.1
    assert dato["transporte_pct_canasta"] == 48.0
    assert dato["variacion_mensual_pct"] == 17.5
    assert dato["fecha"] == "2026-05-01"
