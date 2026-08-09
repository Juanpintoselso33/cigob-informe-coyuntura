"""Tests de `reestructuracion_organismos`: numerador caso por caso (ADR-0188).

Lo que se protege:
  * el registro curado (data/gestion/reestructuracion_organismos_normas.json)
    sigue teniendo exactamente las 18 normas ya revisadas, con la misma
    partición 11 vigentes / 3 falsos positivos / 4 rechazados por el
    Congreso — si una edición futura borra o desclasifica una exclusión sin
    querer, este test lo nota antes que el ITCG publicado;
  * el colector nunca ESCRIBE ese registro (es criterio del analista, mismo
    principio que privatizaciones.json/privatizaciones_fechas.json);
  * una norma que la búsqueda encuentra y no está en el registro NO cuenta
    en el avance y queda avisada en `sin_clasificar`, en vez de sumarse o
    perderse en silencio.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import gestion


def _registro() -> dict:
    return json.loads(
        gestion.REESTRUCTURACION_NORMAS_PATH.read_text(encoding="utf-8-sig"))["normas"]


# ── El registro curado ───────────────────────────────────────────────────────

def test_el_registro_curado_pinea_las_exclusiones():
    """La lectura caso por caso de ADR-0185/ADR-0188: 18 normas, 11 cuentan,
    7 no (3 falsos positivos + 4 actos rechazados por el Congreso)."""
    normas = _registro()
    assert len(normas) == 18, sorted(normas)

    vigentes = [nid for nid, d in normas.items() if d.get("estado") == "vigente"]
    excluidas = [nid for nid, d in normas.items() if d.get("estado") == "excluido"]
    assert len(vigentes) == 11, sorted(vigentes)
    assert len(excluidas) == 7, sorted(excluidas)

    motivos = {nid: normas[nid].get("motivo") for nid in excluidas}
    falsos_positivos = [n for n, m in motivos.items() if m == "falso_positivo"]
    rechazados = [n for n, m in motivos.items() if m == "rechazado_congreso"]
    assert len(falsos_positivos) == 3, sorted(falsos_positivos)
    assert len(rechazados) == 4, sorted(rechazados)


def test_toda_norma_del_registro_tiene_evidencia():
    """Ninguna clasificación es un número sin rastro: toda entrada declara
    estado + detalle, y las excluidas además su motivo del vocabulario cerrado."""
    for nid, d in _registro().items():
        assert d.get("estado") in ("vigente", "excluido"), (nid, d)
        assert d.get("detalle"), f"{nid} sin detalle"
        assert d.get("titulo"), f"{nid} sin título"
        if d["estado"] == "excluido":
            assert d.get("motivo") in ("falso_positivo", "rechazado_congreso"), (nid, d)
        else:
            assert d.get("organismo"), f"{nid} vigente sin organismo"


def test_el_colector_no_escribe_el_registro_curado():
    """Clasificar una norma es juicio del analista, no algo que el código
    pueda inferir del texto — mismo principio que ADR-0129 aplicó a
    privatizaciones.json. Si esto se rompe, una corrida automática podría
    reclasificar una exclusión sin que nadie lo revise."""
    fuente = Path(gestion.__file__).read_text(encoding="utf-8")
    ini = fuente.index("def fetch_reestructuracion_organismos")
    fin_idx = fuente.find("\ndef ", ini + 1)
    cuerpo = fuente[ini:fin_idx if fin_idx != -1 else None]
    for prohibido in ("REESTRUCTURACION_NORMAS_PATH.write",
                       "REESTRUCTURACION_NORMAS_PATH, \"w\""):
        assert prohibido not in cuerpo, f"el colector escribe el registro curado ({prohibido})"


# ── Clasificación en la corrida (sin red: _infoleg_buscar_mes simulado) ─────

def test_lo_no_clasificado_no_cuenta_y_se_avisa(monkeypatch, capsys):
    """El defecto que corrige ADR-0188: un hallazgo nuevo de InfoLeg no debe
    sumarse solo porque el texto contiene 'disolucion'. Se simulan tres
    normas en un único mes: una vigente (cuenta), una excluida del registro
    real (no cuenta) y una que no está en ningún lado (no cuenta y avisa)."""
    id_vigente, id_excluida = next(
        nid for nid, d in _registro().items() if d["estado"] == "vigente"), next(
        nid for nid, d in _registro().items() if d["estado"] == "excluido")
    id_nueva = "999999"

    def _fake_buscar_mes(texto, anio, mes, session=None):
        if (anio, mes) == (2024, 3):
            return [(id_vigente, "norma vigente"),
                    (id_excluida, "norma excluida"),
                    (id_nueva, "norma nunca vista")]
        return []

    monkeypatch.setattr(gestion, "_infoleg_buscar_mes", _fake_buscar_mes)
    r = gestion.fetch_reestructuracion_organismos()
    assert r is not None

    assert r["conteo_normas"] == 1
    assert [e["id"] for e in r["excluidas"]] == [id_excluida]
    assert [n["id"] for n in r["sin_clasificar"]] == [id_nueva]
    assert r["valor"] == round(1 * 100.0 / gestion.ORGANISMOS_PLAN_TOTAL, 1)

    salida = capsys.readouterr().out
    assert "[WARN]" in salida and id_nueva in salida, (
        "una norma sin clasificar tiene que avisarse, no perderse en silencio")


def test_una_exclusion_del_registro_no_se_cuenta_aunque_reaparezca(monkeypatch):
    """Si InfoLeg vuelve a traer la misma norma excluida en dos meses (no
    debería, pero el filtro de fecha de InfoLeg no es a prueba de todo), no
    se cuenta dos veces ni pasa a contar."""
    id_excluida = next(nid for nid, d in _registro().items() if d["estado"] == "excluido")

    def _fake_buscar_mes(texto, anio, mes, session=None):
        if (anio, mes) in ((2024, 1), (2024, 2)):
            return [(id_excluida, "norma excluida")]
        return []

    monkeypatch.setattr(gestion, "_infoleg_buscar_mes", _fake_buscar_mes)
    r = gestion.fetch_reestructuracion_organismos()
    assert r is not None
    assert r["conteo_normas"] == 0
    assert len(r["excluidas"]) == 1


# ── Corrida en vivo (tolerante: no fija cuántas hay, solo la forma) ─────────

def test_la_card_en_vivo_es_consistente_con_su_propio_conteo():
    """Smoke test contra InfoLeg real. Deliberadamente NO fija el conteo de
    'sin_clasificar' en 0: que aparezca un hallazgo nuevo sin clasificar es
    el comportamiento esperado el día que el Gobierno cierre otro organismo,
    no una falla — el test solo verifica que la card sea internamente
    consistente y que las exclusiones vengan con su motivo."""
    r = gestion.fetch_reestructuracion_organismos()
    if r is None:
        pytest.skip("colector sin datos (InfoLeg no respondió)")

    assert r["valor"] == round(min(100.0, r["conteo_normas"] * 100.0
                                    / gestion.ORGANISMOS_PLAN_TOTAL), 1)
    for e in r["excluidas"]:
        assert e.get("motivo") in ("falso_positivo", "rechazado_congreso"), e
        assert e.get("detalle"), e
    for n in r["sin_clasificar"]:
        assert n.get("id") and n.get("titulo") and n.get("periodo"), n
