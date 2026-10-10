# -*- coding: utf-8 -*-
"""`iaf_transferencias` mide 12 meses móviles, no años calendario (ADR-0353).

El colector comparaba el último año CERRADO contra el anterior: en octubre de
2026 informaba 2025 contra 2024 (fecha del dato 2025-12-31) aunque la planilla de
Hacienda ya traía enero a septiembre de 2026. Ahora la ventana termina en el
último mes que tiene IPC publicado.

Los flujos son sintéticos a propósito: el resultado correcto se calcula a mano,
sin pasar por la misma función que se prueba.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica
import descargar_series


def _meses(desde, hasta):
    m, out = desde, []
    while m <= hasta:
        out.append(m)
        m = politica._mes_siguiente(m, 1)
    return out


def _ipc(hasta="2026-08"):
    """IPC +2% mensual, base 100 en 2024-01."""
    return {m: 100.0 * 1.02 ** i for i, m in enumerate(_meses("2024-01", hasta))}


def _planilla(real_por_mes, ipc, hasta="2026-09"):
    """Flujos nominales = flujo real elegido × IPC del mes. Los meses sin IPC
    usan el último IPC conocido (la planilla llega un mes más lejos)."""
    ult = ipc[max(ipc)]
    return {m: real_por_mes(m) * ipc.get(m, ult * 1.02) for m in _meses("2024-01", hasta)}


@pytest.fixture
def sin_red(monkeypatch):
    def armar(real_por_mes, ipc_hasta="2026-08", ron_hasta="2026-09"):
        ipc = _ipc(ipc_hasta)
        ron = _planilla(real_por_mes, ipc, ron_hasta)
        csv = {y: sum(ron[f"{y}-{k:02d}"] for k in range(1, 13)) for y in (2024, 2025)
               if all(f"{y}-{k:02d}" in ron for k in range(1, 13))}
        monkeypatch.setattr(politica, "_anio_corriente", lambda: 2026)
        monkeypatch.setattr(politica, "_ron_mensual", lambda desde=2016: dict(ron))
        monkeypatch.setattr(politica, "_ipc_indice_mensual", lambda: dict(ipc))
        monkeypatch.setattr(politica, "_ron_total_anual_csv", lambda: dict(csv))
        return ron, ipc
    return armar


def _cae_10_ultimos_12(m):
    """Real 100 hasta ago-2025; 90 de sep-2025 en adelante."""
    return 90.0 if m >= "2025-09" else 100.0


def test_la_ventana_termina_en_el_ultimo_mes_con_ipc_y_no_con_planilla(sin_red):
    sin_red(_cae_10_ultimos_12, ipc_hasta="2026-08", ron_hasta="2026-09")
    v = politica._iaf_12m_moviles()
    assert max(v) == "2026-08", "la planilla llega a septiembre pero no hay IPC de septiembre"


def test_doce_meses_contra_los_doce_previos_da_el_numero_calculado_a_mano(sin_red):
    sin_red(_cae_10_ultimos_12)
    var_real = politica._iaf_12m_moviles()["2026-08"][0]
    assert var_real == pytest.approx(-0.10, abs=1e-9)   # 12×90 contra 12×100


def test_una_caida_que_arranca_en_el_ano_corriente_distingue_movil_de_acumulado(sin_red):
    """Real 100 hasta dic-2025 y 80 de ene-2026: el acumulado ene-ago da −20%,
    la móvil a ago-2026 da 8 meses a 80 y 4 a 100 contra 12 a 100: −13,33%."""
    ron, ipc = sin_red(lambda m: 80.0 if m >= "2026-01" else 100.0)
    movil = politica._iaf_12m_moviles()["2026-08"][0]
    assert movil == pytest.approx((8 * 80 + 4 * 100) / 1200 - 1, abs=1e-9)
    assert movil == pytest.approx(-0.13333333, abs=1e-6)
    assert abs(movil - (-0.20)) > 0.05, "dio el acumulado del año, no los 12 meses móviles"


def test_flujo_constante_en_terminos_reales_da_cero(sin_red):
    """Control positivo: sin cambio real la variación es 0 aunque el nominal sea
    ~27%; un deflactor mal aplicado no daría cero."""
    sin_red(lambda m: 100.0)
    ventanas = politica._iaf_12m_moviles()
    assert len(ventanas) >= 9, "sin ventanas el control pasaría vacío"
    for fin, (real, nom, *_) in ventanas.items():
        assert real == pytest.approx(0.0, abs=1e-9), fin
        assert nom > 0.2


def test_la_ventana_de_diciembre_coincide_con_el_ano_calendario(sin_red):
    sin_red(_cae_10_ultimos_12)
    assert politica._iaf_12m_moviles()["2025-12"] == politica._iaf_real_por_anio()[2025]
    assert 2026 not in politica._iaf_real_por_anio(), "2026 no tiene los doce meses"


def test_la_card_publica_la_ventana_y_fecha_del_dato_es_fin_de_mes(sin_red):
    sin_red(_cae_10_ultimos_12)
    card = politica.fetch_iaf_transferencias()
    assert card["valor"] == -10.0
    assert card["fecha_dato"] == "2026-08-31"
    assert card["periodo"] == "sep 2025–ago 2026 vs sep 2024–ago 2025"
    assert "ago 2026" in card["detalle_txt"]


def test_card_y_serie_dicen_lo_mismo_en_el_ultimo_mes(sin_red):
    sin_red(lambda m: 80.0 if m >= "2026-01" else 100.0)
    card = politica.fetch_iaf_transferencias()
    serie = dict(descargar_series.fetch_iaf_serie())
    assert serie["2026-08-01"] == card["valor"] == -13.3
    assert serie["2025-12-01"] == 0.0
    assert "2026-09-01" not in serie


def test_el_ano_en_curso_sin_ancla_hereda_la_unidad_pero_no_un_cambio_de_unidad(sin_red, monkeypatch):
    """2026 no está en el CSV anual. Hereda el factor de 2025; si la planilla de
    2026 viniera en otra unidad (×1000) el cálculo falla en vez de publicar."""
    ron, ipc = sin_red(lambda m: 100.0)
    assert politica._iaf_12m_moviles()                      # control: así sí calcula
    en_miles = {m: (v * 1000 if m >= "2026-01" else v) for m, v in ron.items()}
    monkeypatch.setattr(politica, "_ron_mensual", lambda desde=2016: en_miles)
    with pytest.raises(ValueError, match="unidad"):
        politica._iaf_12m_moviles()


def test_sin_24_meses_de_planilla_no_hay_ventana(sin_red):
    sin_red(lambda m: 100.0, ipc_hasta="2025-11", ron_hasta="2025-11")
    assert politica._iaf_12m_moviles() == {}
    assert politica.fetch_iaf_transferencias() is None


def test_un_ano_cerrado_sin_ancla_no_hereda_la_unidad(sin_red, monkeypatch):
    """La herencia es sólo para el año en curso. Si el CSV anual no se actualiza
    y 2026 ya cerró, las ventanas que lo necesitan no se calculan: antes que
    apoyarse en una unidad supuesta."""
    sin_red(lambda m: 100.0)
    monkeypatch.setattr(politica, "_anio_corriente", lambda: 2027)
    v = politica._iaf_12m_moviles()
    assert v and max(v) == "2025-12", "2026 sin ancla no puede tener ventanas"
