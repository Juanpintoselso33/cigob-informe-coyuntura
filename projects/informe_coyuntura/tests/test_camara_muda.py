"""Guarda de cámara muda (ADR-0332).

Lo que importa de esta guarda es tanto lo que avisa como lo que NO avisa: AEA
publica salteado (mediana 43 días) y una guarda que grite en cada hueco normal
entrena a ignorarla, igual que el resto de los avisos del pipeline.

Y sobre todo: **«no pude evaluar» no puede parecerse a «no está muda»**. Esa era
la falla que encontró la revisión adversarial y varios de estos casos existen
sólo para que no vuelva.

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

HOY = date(2026, 9, 20)


def _casos(fechas_por_camara: dict) -> dict:
    return {"casos": [{"fecha": f, "camara": cam, "postura": "neutro",
                       "destinatario": "ejecutivo_nacional"}
                      for cam, fechas in fechas_por_camara.items() for f in fechas]}


def _cadencia_hasta(fin: date, paso: int, n: int) -> list:
    """n comunicados cada `paso` días, el último exactamente en `fin`."""
    return sorted((fin - timedelta(days=paso * i)).isoformat() for i in range(n))


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """Apunta el inventario (codificación + pendientes) a archivos de prueba."""
    cod = tmp_path / "codificacion.json"
    nov = tmp_path / "novedades.json"

    def escribir(fechas_por_camara, pendientes=None):
        cod.write_text(json.dumps(_casos(fechas_por_camara), ensure_ascii=False),
                       encoding="utf-8")
        nov.write_text(json.dumps({"pendientes": pendientes or {}}, ensure_ascii=False),
                       encoding="utf-8")
        monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", cod)
        monkeypatch.setattr(politica, "APOYO_NOVEDADES_PATH", nov)
        return cod, nov

    return escribir


def _marcadores(capsys) -> list:
    """Los `[COTEJO_MANUAL]` que la guarda escribió realmente a stderr."""
    err = capsys.readouterr().err
    return [json.loads(l.split("] ", 1)[1]) for l in err.splitlines()
            if l.startswith("[COTEJO_MANUAL]")]


# ── avisa cuando corresponde ────────────────────────────────────────────────

def test_avisa_cuando_el_silencio_no_tiene_precedente(corpus, capsys):
    fin = date(2026, 1, 1)
    corpus({"AEA": _cadencia_hasta(fin, 30, 20)})
    hoy = fin + timedelta(days=200)

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["evaluable"] and s["umbral"] == 30 and s["silencio"] == 200
    assert "AEA" in politica._avisar_camara_muda(hoy)

    # No basta con que devuelva la lista: el aviso tiene que SALIR.
    marcas = _marcadores(capsys)
    muda = [m for m in marcas if m["registro"].startswith("AEA muda")]
    assert muda, f"no se registró el cotejo manual; sólo {[m['registro'] for m in marcas]}"
    assert "200 días" in muda[0]["motivo"]


def test_NO_avisa_dentro_del_hueco_ya_visto(corpus):
    """El caso que haría inútil la guarda: un silencio largo pero con precedente.

    Los huecos largos tienen que ser parte del repertorio de la cámara, no uno
    solo: el umbral es el percentil 95 justamente para que un caso aislado NO lo
    levante (es la propiedad anti-ratchet). Tres de 23 lo ponen en 150.
    """
    d = date(2024, 1, 1)
    fechas = []
    for i in range(24):
        fechas.append(d.isoformat())
        d += timedelta(days=150 if i % 8 == 7 else 30)   # 3 huecos de 150 en 23
    corpus({"AEA": fechas})
    hoy = date.fromisoformat(fechas[-1]) + timedelta(days=140)

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["umbral"] == 150, f"el p95 no recogió los huecos largos: {s}"
    assert s["silencio"] == 140 and s["silencio"] <= s["umbral"]
    assert "AEA" not in politica._avisar_camara_muda(hoy), (
        "avisó con un silencio que la cámara ya se había tomado varias veces: haría "
        "ruido en cada hueco normal y se volvería inútil")


def test_un_hueco_extraordinario_aislado_no_levanta_el_umbral(corpus):
    """Anti-ratchet (hallazgo 3): el umbral no aprende del incidente que detectó.

    Con el máximo como umbral, un silencio de 400 días —una vez cerrado— dejaba a
    la guarda sorda hasta el día 401. Con el percentil 95 no.
    """
    fin = date(2025, 1, 1)
    fechas = _cadencia_hasta(fin, 30, 30)
    fechas.append((fin + timedelta(days=400)).isoformat())   # el incidente, ya cerrado
    corpus({"AEA": fechas})
    hoy = date.fromisoformat(fechas[-1]) + timedelta(days=90)

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["maximo_historico"] == 400
    assert s["umbral"] < 100, (
        f"el umbral quedó degradado por un único silencio extraordinario: {s['umbral']}")
    assert "AEA" in politica._avisar_camara_muda(hoy), (
        "un silencio de 90 días no disparó porque la guarda aprendió del incidente "
        "anterior: es el ratchet que el percentil venía a evitar")


def test_el_umbral_es_por_camara_y_no_uno_solo(corpus):
    """Mismo silencio, cadencias distintas: no se juzgan igual."""
    fin = date(2026, 6, 30)
    corpus({"AEA": _cadencia_hasta(fin, 120, 15),    # umbral alto
            "UIA": _cadencia_hasta(fin, 7, 15)})     # umbral bajo
    hoy = fin + timedelta(days=60)

    s = politica.silencio_por_camara(hoy)
    assert s["AEA"]["umbral"] > 60 >= s["UIA"]["umbral"]
    assert politica._avisar_camara_muda(hoy) == ["UIA"]


def test_el_borde_exacto_no_avisa_y_el_dia_siguiente_si(corpus):
    """`supera` es estricto: igualar el umbral todavía no es superarlo."""
    fin = date(2026, 1, 1)
    corpus({"AEA": _cadencia_hasta(fin, 30, 20)})
    umbral = politica.silencio_por_camara(fin)["AEA"]["umbral"]

    assert "AEA" not in politica._avisar_camara_muda(fin + timedelta(days=umbral))
    assert "AEA" in politica._avisar_camara_muda(fin + timedelta(days=umbral + 1))


# ── «no pude evaluar» NUNCA se parece a «no está muda» ──────────────────────

def test_corpus_vacio_avisa_que_no_esta_mirando(corpus, capsys):
    """La falla que encontró la revisión: fallar abierto en silencio."""
    corpus({})
    avisadas = politica._avisar_camara_muda(HOY)

    assert avisadas == ["AEA:no-evaluable", "UIA:no-evaluable"], (
        "con el inventario vacío la guarda devolvió lo mismo que con las dos cámaras "
        "publicando: es exactamente la omisión silenciosa que vino a eliminar")
    registros = [m["registro"] for m in _marcadores(capsys)]
    assert registros == ["vigilancia de AEA sin evaluar", "vigilancia de UIA sin evaluar"]


def test_una_camara_ausente_del_inventario_avisa(corpus, capsys):
    corpus({"UIA": _cadencia_hasta(date(2026, 9, 18), 7, 20)})
    s = politica.silencio_por_camara(HOY)
    assert s["AEA"]["evaluable"] is False
    assert "AEA:no-evaluable" in politica._avisar_camara_muda(HOY)
    assert any("AEA" in m["registro"] for m in _marcadores(capsys))


def test_corpus_corto_avisa_en_vez_de_callarse(corpus, capsys):
    """Antes se abstenía en silencio; ahora dice que no está vigilando."""
    corpus({"AEA": _cadencia_hasta(date(2026, 1, 1), 5, 4)})   # 3 huecos, bajo el piso
    s = politica.silencio_por_camara(HOY)
    assert s["AEA"]["evaluable"] is False
    assert "huecos" in s["AEA"]["motivo"]
    assert "AEA:no-evaluable" in politica._avisar_camara_muda(HOY)
    assert _marcadores(capsys), "se abstuvo sin dejar rastro"


def test_inventario_ilegible_avisa_por_las_dos_camaras(corpus, capsys):
    cod, _ = corpus({"AEA": _cadencia_hasta(date(2026, 1, 1), 30, 20)})
    cod.write_text("{ esto no es json", encoding="utf-8")

    s = politica.silencio_por_camara(HOY)
    assert all(not v["evaluable"] for v in s.values())
    assert politica._avisar_camara_muda(HOY) == ["AEA:no-evaluable", "UIA:no-evaluable"]
    assert len(_marcadores(capsys)) == 2


def test_fecha_futura_no_pasa_como_silencio_negativo(corpus):
    fechas = _cadencia_hasta(date(2026, 1, 1), 30, 20)
    fechas.append("2027-12-31")
    corpus({"AEA": fechas})
    s = politica.silencio_por_camara(HOY)["AEA"]
    assert s["evaluable"] is False and "futura" in s["motivo"]


# ── mide la fuente, no nuestro atraso ───────────────────────────────────────

def test_un_pendiente_sin_codificar_ya_cuenta_como_publicar(corpus):
    """Hallazgo 2: si la cámara volvió, la guarda tiene que callarse enseguida.

    Antes leía sólo el corpus codificado, así que seguía gritando «muda» hasta que
    alguien clasificara el comunicado nuevo: medía nuestro atraso, no el silencio
    de la fuente.
    """
    fin = date(2026, 1, 1)
    corpus({"AEA": _cadencia_hasta(fin, 30, 20)})
    hoy = fin + timedelta(days=200)
    assert "AEA" in politica._avisar_camara_muda(hoy)   # muda, sin el pendiente

    # La cámara publica ayer y el comunicado entra como PENDIENTE, sin codificar.
    ayer = (hoy - timedelta(days=1)).isoformat()
    corpus({"AEA": _cadencia_hasta(fin, 30, 20)},
           pendientes={"AEA|nuevo": {"camara": "AEA", "fecha": ayer, "id": "nuevo"}})

    s = politica.silencio_por_camara(hoy)["AEA"]
    assert s["ultimo"] == ayer and s["silencio"] == 1
    assert "AEA" not in politica._avisar_camara_muda(hoy), (
        "siguió avisando después de que la cámara volvió a publicar: eso mide el "
        "atraso de la codificación, no el silencio de la fuente")


# ── el caso vivo, contra el corpus versionado ───────────────────────────────

def test_el_caso_real_de_aea_dispara_hoy():
    s = politica.silencio_por_camara(HOY)
    assert s["AEA"]["evaluable"], f"AEA quedó sin evaluar: {s['AEA'].get('motivo')}"
    assert s["AEA"]["ultimo"] == "2026-03-31"
    assert s["AEA"]["silencio"] > s["AEA"]["umbral"], (
        "si AEA volvió a publicar, este test tiene que fallar: quiere decir que el "
        "hallazgo de ADR-0332 dejó de estar vigente y hay que revisar el ADR")
    assert s["UIA"]["evaluable"] and s["UIA"]["silencio"] <= s["UIA"]["umbral"], (
        "UIA también quedó muda o sin evaluar: es un hallazgo nuevo, no este")
