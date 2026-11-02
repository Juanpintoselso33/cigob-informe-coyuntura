"""Votos sobre bancas: un id de Diputados que no contesta desde CI queda
pendiente para la noche siguiente en vez de congelar la lectura entera
(decisión de Juan, 2-nov-2026)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica


def _correr(monkeypatch, respuesta):
    guardados = []
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: None)
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo",
                        lambda s, tolerar_fallo_al_avanzar=False: 12)
    monkeypatch.setattr(politica, "_diputados_acta_pdf", respuesta)
    monkeypatch.setattr(politica, "_vsb_guardar_cache", lambda c: guardados.append(dict(c)))
    monkeypatch.setattr(politica, "VSB_MARGEN_HUECOS_DIPUTADOS", 3)
    cache = {"diputados": {"10": {"fecha": "2026-10-22", "resultado": "NEGATIVO", "titulo": "X"}},
             "diputados_ausentes": [], "diputados_piso": None}
    return politica._vsb_actualizar_diputados(cache), cache


def test_id_que_no_contesta_queda_pendiente(monkeypatch, capsys):
    ok, cache = _correr(monkeypatch, lambda s, i: politica._ACTA_FALLO if i in (11, 12)
                        else politica._ACTA_NO_EXISTE)
    assert ok is True
    assert cache["diputados_piso"] is None          # con pendientes el piso no avanza
    assert "11, 12" in capsys.readouterr().out


def test_sin_pendientes_el_piso_avanza(monkeypatch):
    ok, cache = _correr(monkeypatch, lambda s, i: politica._ACTA_NO_EXISTE)
    assert ok is True
    assert cache["diputados_piso"] == 10


def test_tras_tres_colgados_no_se_piden_mas(monkeypatch):
    pedidos = []

    def resp(s, i):
        pedidos.append(i)
        return politica._ACTA_FALLO
    monkeypatch.setattr(politica, "_diputados_acta_id_maximo",
                        lambda s, tolerar_fallo_al_avanzar=False: 12)
    ok, cache = _correr(monkeypatch, resp)
    assert ok is True and len(pedidos) == 3
