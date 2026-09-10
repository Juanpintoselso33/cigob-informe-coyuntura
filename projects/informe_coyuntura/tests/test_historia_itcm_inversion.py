import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import itcm
import validacion_externa as ve


def test_la_historia_incluye_inversion_con_el_valor_de_su_serie(monkeypatch):
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: {
        "ipc_total": [{"fecha": "2026-07-01", "valor": 2.1}],
        "iai": [{"fecha": "2026-06-01", "valor": -0.06},
                {"fecha": "2026-07-01", "valor": -5.66}],
    })
    valores = ve._valores_itcm_por_mes()
    assert valores["2026-06"]["iai"] == -0.06
    assert valores["2026-07"]["iai"] == -5.66
    r = itcm.calcular_itcm(valores["2026-07"])
    assert r["dimensiones"]["inversion"]["indicadores"]["iai"]["valor"] == -5.66
    assert r["dimensiones"]["inversion"]["peso"] == 0.12


def test_todos_los_componentes_activos_se_buscan_en_la_historia(monkeypatch):
    monkeypatch.setattr(ve, "_cargar_series_itcm", lambda: {
        "ipc_total": [{"fecha": "2026-07-01", "valor": 2.1}]})
    esperado = {k for d in itcm.DIMENSIONES_ITCM.values() for k in d["indicadores"]}
    punto = ve._valores_itcm_por_mes()["2026-07"]
    assert set(punto) == esperado
    # Un mes ausente conserva None; no se rellena con cero ni con otro mes.
    assert punto["iai"] is None
