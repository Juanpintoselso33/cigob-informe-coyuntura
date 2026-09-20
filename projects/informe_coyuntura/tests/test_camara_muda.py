"""Guarda de cámara muda (ADR-0332).

Lo que importa de esta guarda es tanto lo que avisa como lo que NO avisa: AEA
publica salteado (mediana 43 días) y una guarda que grite en cada hueco normal
entrena a ignorarla, igual que el resto de los avisos del pipeline.

Se prueba rompiéndola en las dos direcciones, no sólo confirmando el caso vivo.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

import politica  # noqa: E402


def _corpus(fechas_por_camara: dict) -> dict:
    return {"casos": [{"fecha": f, "camara": cam, "postura": "neutro",
                       "destinatario": "ejecutivo_nacional"}
                      for cam, fechas in fechas_por_camara.items() for f in fechas]}


def _cadencia(inicio: str, paso: int, n: int) -> list:
    d0 = date.fromisoformat(inicio)
    return [(d0 + timedelta(days=paso * i)).isoformat() for i in range(n)]


def _cadencia_hasta(fin: date, paso: int, n: int) -> list:
    """n comunicados cada `paso` días, el último exactamente en `fin`."""
    return sorted((fin - timedelta(days=paso * i)).isoformat() for i in range(n))


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """Apunta APOYO_CODIFICACION_PATH a un corpus de prueba en tmp_path."""
    destino = tmp_path / "codificacion.json"

    def escribir(fechas_por_camara):
        destino.write_text(json.dumps(_corpus(fechas_por_camara), ensure_ascii=False),
                           encoding="utf-8")
        monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", destino)
        return destino

    return escribir


HOY = date(2026, 9, 20)


def test_avisa_cuando_el_silencio_no_tiene_precedente(corpus):
    # 20 comunicados cada 30 días; el último deja 200 días de silencio.
    fechas = _cadencia("2024-01-01", 30, 20)
    ultimo = date.fromisoformat(fechas[-1])
    corpus({"AEA": fechas})
    hoy = ultimo + timedelta(days=200)

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["maximo_historico"] == 30
    assert s["silencio"] == 200
    assert politica._avisar_camara_muda(hoy) == ["AEA"]


def test_NO_avisa_dentro_del_hueco_ya_visto(corpus):
    """El caso que haría inútil la guarda: un hueco largo pero con precedente."""
    # Cadencia de 30 días con un hueco histórico de 154 (el real de AEA).
    fechas = _cadencia("2024-01-01", 30, 15)
    hueco_largo = (date.fromisoformat(fechas[-1]) + timedelta(days=154)).isoformat()
    fechas.append(hueco_largo)
    corpus({"AEA": fechas})
    # Silencio de 150 días: largo, pero MENOR que el máximo ya observado.
    hoy = date.fromisoformat(hueco_largo) + timedelta(days=150)

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["maximo_historico"] == 154
    assert s["silencio"] == 150
    assert politica._avisar_camara_muda(hoy) == [], (
        "avisó con un silencio que la cámara ya se había tomado antes: la guarda "
        "haría ruido en cada hueco normal y se volvería inútil")


def test_no_avisa_con_un_corpus_demasiado_corto(corpus):
    """Con pocos huecos el máximo subestima la cadencia real: no se opina."""
    corpus({"AEA": _cadencia("2026-01-01", 5, 4)})   # 3 huecos, bajo el piso
    hoy = date(2026, 12, 31)
    assert "AEA" not in politica.silencio_por_camara(hoy)
    assert politica._avisar_camara_muda(hoy) == []


def test_el_umbral_es_por_camara_y_no_uno_solo(corpus):
    """Dos cámaras con cadencias distintas: el mismo silencio no las juzga igual."""
    # Las dos terminan el MISMO día y callan lo mismo; sólo cambia su cadencia.
    fin = date(2026, 6, 30)
    lenta = _cadencia_hasta(fin, 120, 15)   # máximo histórico 120
    rapida = _cadencia_hasta(fin, 7, 15)    # máximo histórico 7
    corpus({"AEA": lenta, "UIA": rapida})
    hoy = fin + timedelta(days=60)

    s = politica.silencio_por_camara(hoy)
    assert s["AEA"]["maximo_historico"] == 120
    assert s["UIA"]["maximo_historico"] == 7
    # 60 días: normal para la lenta, sin precedente para la rápida.
    assert politica._avisar_camara_muda(hoy) == ["UIA"]


def test_el_caso_real_de_aea_dispara_hoy():
    """Contra el corpus versionado, no un fixture: AEA está muda sin precedente."""
    s = politica.silencio_por_camara(HOY)
    assert "AEA" in s, "AEA salió del corpus o quedó bajo el piso de huecos"
    assert s["AEA"]["ultimo"] == "2026-03-31"
    assert s["AEA"]["maximo_historico"] == 154
    assert s["AEA"]["silencio"] > s["AEA"]["maximo_historico"], (
        "si AEA volvió a publicar, este test tiene que fallar: quiere decir que el "
        "hallazgo de ADR-0332 dejó de estar vigente y hay que revisar el ADR")
    assert s["UIA"]["silencio"] <= s["UIA"]["maximo_historico"], (
        "UIA también quedó muda: es un hallazgo nuevo, no este")
