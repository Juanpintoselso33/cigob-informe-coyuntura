"""Resiliencia de politica.py: tres fallos que tumbaban o falseaban un indicador."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica


class Hoy(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 10)


# ── 1. adhesión RIGI: la verificación hecha se guarda ───────────────────────

@pytest.fixture
def rigi(monkeypatch, tmp_path):
    leyes = {
        "SANTA FE": {"fecha": "2025-01-01", "fuente": "https://test/sf",
                     "comprobar_textos": ["Ley 14386"]},
        "CABA": {"fecha": "2026-05-28", "fuente": "https://test/caba",
                 "comprobar_textos": ["LEY 6949"]},
    }
    reg = tmp_path / "compl.json"
    reg.write_text(json.dumps(leyes))
    monkeypatch.setattr(politica, "ADHESION_COMPLEMENTARIAS_PATH", reg)
    monkeypatch.setattr(politica, "ADHESION_VERIFICACION_PATH", tmp_path / "verif.json")
    monkeypatch.setattr(politica, "date", Hoy)
    pedidos = []
    caido = set()
    cont = {
        politica.MAGYP_RIGI_URL: "<table><tr><td>CATAMARCA</td><td>Ley</td></tr></table>",
        "https://test/sf": "<p>Ley 14386</p>",
        "https://test/caba": "<p>LEY 6949</p>",
    }

    def get(url, **kw):
        pedidos.append(url)
        if url in caido:
            raise politica.requests.Timeout("timeout")
        return Mock(status_code=200, text=cont[url], raise_for_status=lambda: None)
    monkeypatch.setattr(politica.requests, "get", get)
    return pedidos, caido, cont


def test_no_vuelve_a_bajar_las_leyes_ya_verificadas(rigi):
    pedidos, _, _ = rigi
    assert politica.fetch_adhesion_reformas_provincial()["n_provincias"] == 3
    pedidos.clear()
    assert politica.fetch_adhesion_reformas_provincial()["n_provincias"] == 3
    assert "https://test/sf" not in pedidos and "https://test/caba" not in pedidos


def test_timeout_en_la_reverificacion_usa_la_verificacion_guardada(rigi, monkeypatch, capsys):
    pedidos, caido, _ = rigi
    politica.fetch_adhesion_reformas_provincial()
    # pasa el plazo de re-verificación y la fuente se cae
    monkeypatch.setattr(politica, "ADHESION_REVERIFICAR_DIAS", -1)
    caido.add("https://test/caba")
    r = politica.fetch_adhesion_reformas_provincial()
    assert r is not None and r["jurisdicciones"] == ["CABA", "CATAMARCA", "SANTA FE"]
    assert "[WARN]" in capsys.readouterr().out


def test_sin_verificacion_guardada_el_error_de_red_sigue_siendo_none(rigi):
    _, caido, _ = rigi
    caido.add("https://test/caba")
    assert politica.fetch_adhesion_reformas_provincial() is None


def test_reverificar_con_texto_que_ya_no_confirma_no_usa_lo_guardado(rigi, monkeypatch):
    _, _, cont = rigi
    politica.fetch_adhesion_reformas_provincial()
    monkeypatch.setattr(politica, "ADHESION_REVERIFICAR_DIAS", -1)
    cont["https://test/caba"] = "<p>Servicio no disponible</p>"
    assert politica.fetch_adhesion_reformas_provincial() is None


def test_cambiar_los_textos_a_comprobar_invalida_lo_guardado(rigi):
    pedidos, _, cont = rigi
    politica.fetch_adhesion_reformas_provincial()
    reg = json.loads(politica.ADHESION_COMPLEMENTARIAS_PATH.read_text())
    reg["CABA"]["comprobar_textos"] = ["otro texto"]
    politica.ADHESION_COMPLEMENTARIAS_PATH.write_text(json.dumps(reg))
    assert politica.fetch_adhesion_reformas_provincial() is None  # re-verifica y no confirma


# ── 2. producción legislativa: una fila sin número no tumba el indicador ────

def _filas():
    return [
        {"LEY": "27001", "SANCION_DEFINITIVA": "2026-08-10", "EXPEDIENTE_INICIAL": "", "PROYECTO_ID": ""},
        {"LEY": "27002", "SANCION_DEFINITIVA": "2026-08-20", "EXPEDIENTE_INICIAL": "", "PROYECTO_ID": ""},
        {"LEY": "", "SANCION_DEFINITIVA": "2026-09-02", "EXPEDIENTE_INICIAL": "", "PROYECTO_ID": ""},
    ]


@pytest.fixture
def sin_cotejo(monkeypatch):
    import cotejo_manual
    monkeypatch.setattr(cotejo_manual, "aplicar_correcciones_sancion", lambda f: f)
    monkeypatch.setattr(cotejo_manual, "revisar_fechas_sancion", lambda *a, **k: None)
    monkeypatch.setattr(politica, "_leyes_sancionadas_complementarias", lambda: [])
    monkeypatch.setattr(politica, "date", Hoy)


def test_fila_sin_ley_ni_expediente_se_excluye_con_warn(sin_cotejo, capsys):
    out = politica._leyes_fechadas(_filas())
    assert sorted(l for l, _ in out) == ["ley:27001", "ley:27002"]
    assert "[WARN]" in capsys.readouterr().out


def test_el_warn_identifica_la_fila(sin_cotejo, capsys):
    politica._leyes_fechadas(_filas())
    assert "2026-09-02" in capsys.readouterr().out


def test_si_todas_las_filas_son_invalidas_sigue_fallando(sin_cotejo):
    with pytest.raises(ValueError):
        politica._leyes_fechadas([_filas()[2]])


# ── 3. cobertura judicial: desactualizado = conciliación vencida ────────────

def _card(monkeypatch, dias_atras):
    corte = (Hoy.today() - timedelta(days=dias_atras)).isoformat()
    meta = {"total_cargos": 100, "cargos_con_juez": 70, "fecha_corte": corte,
            "composicion": {"Titular": 60, "Subrogante": 20, "Sin subrogante designado": 10},
            "vacantes_padron": 10, "fecha_padron": "2026-06-05", "ancla_corregida": 60,
            "correcciones_padron": 0, "designaciones": 0, "renuncias": 0,
            "otras_bajas": 0, "limites": []}
    monkeypatch.setattr(politica, "cobertura_judicial_serie", lambda: ({"2026-09": 70.0}, meta))
    monkeypatch.setattr(politica, "date", Hoy)
    monkeypatch.setattr(politica, "_avisar_vencimiento_judicial", lambda c: None)
    return politica.fetch_cobertura_judicial()


@pytest.mark.parametrize("dias,esperado", [(0, False), (3, False), (14, False), (15, True), (40, True)])
def test_desactualizado_es_vencimiento_no_paso_de_un_dia(monkeypatch, dias, esperado):
    from config import dias_sin_fetch_tolerados
    assert dias_sin_fetch_tolerados("cobertura_judicial") == 14
    assert _card(monkeypatch, dias)["desactualizado"] is esperado
