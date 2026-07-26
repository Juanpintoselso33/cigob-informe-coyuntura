"""Detector de novedades judiciales de la CSJN (ADR-0140).

Lo que se protege es que AVISE y no que cuente: el endpoint abierto topea en
10 registros por consulta, así que cualquier intento futuro de convertirlo en
serie es un error de diseño, no una mejora.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import politica  # noqa: E402


class _SesionFalsa:
    """Devuelve un lote fijo; no toca la red."""

    def __init__(self, registros):
        self.registros = registros
        self.consultas = []

    def post(self, url, data=None, **kw):
        self.consultas.append(data["texto"])
        return self

    def raise_for_status(self):
        pass

    def json(self):
        return {"Result": "OK", "Records": self.registros}


REGISTROS = [
    # el Estado como parte, en el fuero contencioso administrativo federal
    {"idAnalisis": "1", "identificadorExpediente": "CAF 024580/2022/1/RH001",
     "fecha": "07/07/2026", "caratula": "EN-M ECONOMIA c/ BUNGE ARGENTINA SA s/INHIBITORIA",
     "materia": "ADMINISTRATIVO", "titulo": "t", "inconstitucional": False,
     "sentenciaArbitraria": False},
    # declara inconstitucionalidad
    {"idAnalisis": "2", "identificadorExpediente": "CAF 000001/2024/CS001",
     "fecha": "30/04/2026", "caratula": "TORRES ABAD, CARMEN c/ EN-JGM s/HABEAS DATA",
     "materia": "ADMINISTRATIVO", "titulo": "t", "inconstitucional": True,
     "sentenciaArbitraria": False},
    # ni una cosa ni la otra: pleito entre privados
    {"idAnalisis": "3", "identificadorExpediente": "CCF 005988/2017/1/RH001",
     "fecha": "07/07/2026", "caratula": "G. B., R. c/ OSDE s/AMPARO DE SALUD",
     "materia": "SALUD", "titulo": "t", "inconstitucional": False,
     "sentenciaArbitraria": True},
]


@pytest.fixture
def store_temporal(tmp_path, monkeypatch):
    destino = tmp_path / "csjn_novedades.json"
    monkeypatch.setattr(politica, "CSJN_NOVEDADES_PATH", destino)
    return destino


def _correr(monkeypatch, registros, terminos=("inconstitucionalidad",)):
    sesion = _SesionFalsa(registros)
    monkeypatch.setattr(politica, "_csjn_sesion", lambda: sesion)
    return politica.detectar_novedades_judiciales(terminos=terminos), sesion


def test_marca_solo_lo_relevante(store_temporal, monkeypatch):
    store, _ = _correr(monkeypatch, REGISTROS)
    pendientes = store["pendientes"]
    assert set(pendientes) == {"1", "2"}, "debía marcar Estado-parte e inconstitucional"
    assert "3" in store["revisadas"], "el descartado igual queda anotado como revisado"
    assert store["revisadas"]["3"]["marcado"] is False
    assert pendientes["2"]["inconstitucional"] is True
    assert "declara inconstitucionalidad" in pendientes["2"]["motivos"]
    assert pendientes["1"]["fuero"] == "CAF"


def test_no_avisa_dos_veces_el_mismo_fallo(store_temporal, monkeypatch):
    """Un fallo publicado es inmutable: se evalúa una vez y no vuelve a contarse
    como novedad, aunque siga apareciendo en el feed."""
    _correr(monkeypatch, REGISTROS)
    store, _ = _correr(monkeypatch, REGISTROS)
    assert store["_meta"]["nuevas_en_la_corrida"] == 0
    assert len(store["pendientes"]) == 2


def test_una_consulta_caida_no_tumba_el_resto(store_temporal, monkeypatch):
    """Si un término falla, los otros igual se procesan: es un detector, y
    perder un aviso es mejor que perderlos todos."""
    class MediaCaida(_SesionFalsa):
        def post(self, url, data=None, **kw):
            if data["texto"] == "medida cautelar":
                raise RuntimeError("timeout")
            return super().post(url, data=data, **kw)

    sesion = MediaCaida(REGISTROS)
    monkeypatch.setattr(politica, "_csjn_sesion", lambda: sesion)
    store = politica.detectar_novedades_judiciales(
        terminos=("medida cautelar", "inconstitucionalidad"))
    assert len(store["pendientes"]) == 2


def test_no_alimenta_ningun_indice(store_temporal, monkeypatch):
    """La garantía central de ADR-0140: es un aviso, no una serie. El endpoint
    topea en 10 registros, así que un conteo saldría siempre mal."""
    store, _ = _correr(monkeypatch, REGISTROS)
    assert "valor" not in store and "serie" not in store
    assert "NO es un contador" in store["_meta"]["descripcion"]
    assert "csjn_novedades" not in (RAIZ / "scripts" / "itcp.py").read_text(
        encoding="utf-8"), "el detector no puede entrar al ITCP"


def test_el_store_es_json_valido_y_ordenado(store_temporal, monkeypatch):
    _correr(monkeypatch, REGISTROS)
    d = json.loads(store_temporal.read_text(encoding="utf-8"))
    assert set(d) == {"_meta", "pendientes", "revisadas"}
    assert d["_meta"]["registros_vistos_en_la_corrida"] == 3


def test_el_store_esta_en_el_git_add_del_cron():
    """feedback_cache_persistence_cron: un store nuevo que no está en el git add
    del workflow no sobrevive a la corrida nocturna."""
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml"
          ).read_text(encoding="utf-8")
    assert "csjn_novedades.json" in wf
