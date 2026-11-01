"""La BADLAR del BCRA es una tasa NOMINAL anual («en % n.a.»): su tasa efectiva
mensual es TNA/12, no la raíz doceava de (1 + TNA). El IdC (ADR-0028) mide el
precio del fondeo como TEM − IPC m/m, así que una conversión equivocada corre
toda la serie de tasa real hacia abajo y, con ella, la estandarización z.

Caso real: septiembre de 2026, BADLAR 22,8125 % n.a. e IPC m/m 1,933610 %.
Con raíz doceava daba −0,21 pp; con TNA/12 da −0,03 pp."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import macro


def test_tem_de_una_tna_es_la_doceava_parte():
    assert macro.tem_de_tna(22.8125) == pytest.approx(1.9010417, abs=1e-6)
    assert macro.tem_de_tna(120.0) == pytest.approx(10.0)


def _ym(i: int) -> str:
    return f"{2016 + i // 12}-{i % 12 + 1:02d}"


def test_la_tasa_real_del_idc_usa_tna_sobre_12(monkeypatch):
    """Toda la historia de `_idc_base_mensual` pasa por la conversión: se arma
    una base sintética con la BADLAR de septiembre de 2026 en el último mes y
    se lee la tasa real resultante."""
    meses = [_ym(i) for i in range(30)]
    ultimo = meses[-1]
    ipc_m = 1.933610
    ipc, nivel = {}, 100.0
    for ym in meses:
        nivel *= 1.0 + (ipc_m / 100.0 if ym == ultimo else 0.02)
        ipc[ym] = nivel
    badlar = {ym: 22.8125 for ym in meses}
    dep = {ym: 1000.0 + i for i, ym in enumerate(meses)}
    pre = {ym: 600.0 for ym in meses}
    series = {macro.BCRA_BADLAR_ID: badlar, macro.BCRA_DEP_PRIV_ID: dep,
              macro.BCRA_PREST_PRIV_ID: pre}
    monkeypatch.setattr(macro, "_IDC_BASE_MEMO", {})
    monkeypatch.setattr(macro, "_bcra_fin_de_mes", lambda var, n: series[var])
    monkeypatch.setattr(macro, "_ipc_indice_mensual", lambda n: ipc)

    tasa_real = macro._idc_base_mensual(30)[ultimo][0]

    assert tasa_real == pytest.approx(22.8125 / 12 - ipc_m, abs=1e-4)
    assert round(tasa_real, 2) == -0.03       # con raíz doceava daba −0,21
