"""ADR-0414: gasto de funcionamiento, promedio de 12 meses contra todo 2023."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gestion  # noqa: E402
import descargar_series as ds  # noqa: E402


def _meses(desde, hasta):
    out, (a, m) = [], (int(desde[:4]), int(desde[5:7]))
    while f"{a:04d}-{m:02d}" <= hasta:
        out.append(f"{a:04d}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return out


def _datos(real=100.0, aguinaldo=0.0):
    """Nominal = real * ipc; el IPC crece 2 % mensual; aguinaldo extra en jun y dic."""
    ms = _meses("2022-01", "2026-08")
    ipc = {m: 100 * 1.02 ** i for i, m in enumerate(ms)}
    nom = {m: real * ipc[m] * (1 + (aguinaldo if m[5:] in ("06", "12") else 0)) for m in ms}
    return nom, ipc


def test_cuenta_correcta():
    nom, ipc = _datos()
    for m in gestion._meses_previos("2026-08", 12):
        nom[m] = 70 * ipc[m]
    var, ym, desde = gestion._var_real_12m_vs_2023(nom, ipc)
    assert (ym, desde) == ("2026-08", "2025-09")
    assert var == pytest.approx(-30.0, abs=0.01)


def test_aguinaldo_se_cancela_exacto():
    # Serie real plana con medio aguinaldo (+50 %) en junio y diciembre: los
    # dos lados traen los dos medios aguinaldos, así que el resultado es 0.
    nom, ipc = _datos(aguinaldo=0.5)
    assert gestion._var_real_12m_vs_2023(nom, ipc, "2026-08")[0] == 0.0


def test_cuenta_con_aguinaldo_es_el_cociente_de_promedios():
    nom, ipc = _datos(aguinaldo=0.5)
    for m in gestion._meses_previos("2026-08", 12):
        nom[m] = 70 * ipc[m] * (1.5 if m[5:] in ("06", "12") else 1)
    var = gestion._var_real_12m_vs_2023(nom, ipc, "2026-08")[0]
    assert var == pytest.approx(-30.0, abs=0.01)


def test_mes_faltante_levanta():
    nom, ipc = _datos()
    del nom["2025-11"]
    with pytest.raises(ValueError):
        gestion._var_real_12m_vs_2023(nom, ipc, "2026-08")
    nom, ipc = _datos()
    del nom["2023-03"]
    with pytest.raises(ValueError):
        gestion._var_real_12m_vs_2023(nom, ipc, "2026-08")


def test_serie_y_tarjeta_dan_lo_mismo(monkeypatch):
    nom, ipc = _datos()
    for m in gestion._meses_previos("2026-08", 12):
        nom[m] = 70 * ipc[m]
    mitad = {m: v / 2 for m, v in nom.items()}

    def falso(sid, limit=48):
        return {gestion.IPC_ID: ipc}.get(sid, mitad)

    monkeypatch.setattr(gestion, "_indec_nivel_mensual", falso)
    serie = ds._serie_var_real_12m_vs_2023(["a", "b"])
    tarjeta = gestion._var_real_12m_vs_2023(nom, ipc)[0]
    assert dict(serie)["2026-08-01"] == tarjeta
    assert serie[0][0] == "2024-01-01"


def _fuente_falsa(monkeypatch, salarios, otros, ipc):
    tabla = {gestion.FUNC_SALARIOS_ID: salarios, gestion.FUNC_OTROS_ID: otros, gestion.IPC_ID: ipc}
    monkeypatch.setattr(gestion, "_indec_nivel_mensual", lambda sid, limit=48: dict(tabla[sid]))


def test_la_serie_usa_solo_meses_con_todos_los_componentes(monkeypatch):
    # hallazgo de Codex (29-oct): sumar sobre la unión publicaba un total parcial
    meses = _meses("2023-01", "2026-08")
    sal = {m: 50.0 for m in meses}
    otros = {m: 50.0 for m in meses if m != "2026-08"}
    _fuente_falsa(monkeypatch, sal, otros, {m: 1.0 for m in meses})
    s = ds._serie_var_real_12m_vs_2023([gestion.FUNC_SALARIOS_ID, gestion.FUNC_OTROS_ID])
    assert s[-1] == ["2026-07-01", 0.0]


def test_un_hueco_en_el_medio_hace_fallar_la_serie(monkeypatch):
    # hallazgo de Codex (29-oct): truncar en silencio reemplazaba la serie buena
    meses = [m for m in _meses("2023-01", "2026-08") if m != "2025-11"]
    _fuente_falsa(monkeypatch, {m: 50.0 for m in meses}, {m: 50.0 for m in meses},
                  {m: 1.0 for m in meses})
    with pytest.raises(ValueError):
        ds._serie_var_real_12m_vs_2023([gestion.FUNC_SALARIOS_ID, gestion.FUNC_OTROS_ID])
