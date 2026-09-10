import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica


@pytest.mark.parametrize("vencida", [True, False])
def test_main_no_renueva_ni_cuenta_como_fresca_una_revision_vencida(monkeypatch, vencida):
    for nombre in dir(politica):
        if nombre.startswith("fetch_"):
            monkeypatch.setattr(politica, nombre, lambda *a, **kw: None)
    for nombre in ("detectar_novedades_judiciales", "detectar_novedades_empresarias"):
        monkeypatch.setattr(politica, nombre, lambda: {})
    resultado = {"valor": 73.82, "fecha_corte": "2026-09-08",
                 "obtenido_en": "2026-09-08", "desactualizado": vencida}
    monkeypatch.setattr(politica, "fetch_cobertura_judicial", lambda: resultado.copy())
    monkeypatch.setattr(politica, "load_cache", lambda: {"indicadores": {}})
    monkeypatch.setattr(politica, "_sellar", lambda r: {**r, "obtenido_en": "NUEVO"})
    guardados = []
    monkeypatch.setattr(politica, "save_cache", guardados.append)
    with pytest.raises(SystemExit) as salida:
        politica.main()
    card = guardados[0]["indicadores"]["cobertura_judicial"]
    assert card["obtenido_en"] == ("2026-09-08" if vencida else "NUEVO")
    assert card["valor"] == 73.82
    assert salida.value.code == (2 if vencida else 1)
