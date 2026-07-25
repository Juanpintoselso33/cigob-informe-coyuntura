"""Tests del indicador de desregulación con fuente oficial (ADR-0125).

Lo que se protege:
  * que el período salga de la FECHA DE CORTE y no del mes de portada (hay
    informes cuya tapa dice "JUNIO 2025" y cuyo corte es el 4 de julio);
  * que los dos formatos de informe (prosa 2025 / fichas 2026) se parseen;
  * que el backfill medido sobre el gráfico siga coincidiendo con las cifras
    de portada, que son independientes de él;
  * que la serie cubra el mandato completo desde dic-2023 y no baje nunca.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import gestion
import itcg
import parametrica

STORE = gestion.DESREG_OFICIAL_STORE


def _store():
    if not STORE.exists():
        pytest.skip("todavía no se corrió el colector de desregulación")
    import json
    return json.loads(STORE.read_text(encoding="utf-8-sig"))


# ── Período por fecha de corte ──────────────────────────────────────────────

def test_el_periodo_sale_de_la_fecha_de_corte(monkeypatch):
    """El informe de tapa "JUNIO 2025" corta al 4 de julio: cubre hasta el
    cierre de junio, así que le corresponde 2025-06 y no 2025-07."""
    casos = [
        ("JUNIO 2025 ... al 4 de julio de 2025, se registran 348 normas de "
         "desregulación que eliminan o modifican 1.157 normativas anteriores, "
         "o un total de 8.090 artículos", "2025-06", 348),
        ("OCTUBRE 2025 ... al 31 de octubre de 2025, se registran 451 normas de "
         "desregulación que eliminan o modifican 2.104 normativas anteriores, "
         "o -de forma más desagregada- un total de 12.357 artículos", "2025-10", 451),
        ("JUNIO 2025 ... al 6 de junio de 2025, se registran 212 normas de "
         "desregulación que eliminan o modifican 700 normativas anteriores, "
         "o un total de 4.000 artículos", "2025-05", 212),
    ]
    for texto, periodo, normas in casos:
        monkeypatch.setattr(gestion, "requests", _FakePdf(texto))
        d = gestion._desreg_leer_informe("http://x/y.pdf")
        assert d["periodo"] == periodo, texto[:30]
        assert d["normas"] == normas


class _FakePdf:
    """Sustituye a requests devolviendo un PDF de una página con `texto`."""

    def __init__(self, texto):
        self._texto = texto

    def get(self, *a, **k):
        import io

        import fitz
        doc = fitz.open()
        pg = doc.new_page()
        pg.insert_textbox(fitz.Rect(20, 20, 560, 800), self._texto, fontsize=8)
        buf = io.BytesIO()
        doc.save(buf)

        class R:
            content = buf.getvalue()
        return R()


# ── Serie ───────────────────────────────────────────────────────────────────

def test_la_serie_arranca_en_diciembre_2023():
    serie = _store().get("backfill_grafico", {})
    assert min(serie) == "2023-12", min(serie)


def test_la_serie_no_baja_nunca():
    """Es un acumulado: una norma dictada no se des-dicta."""
    serie = gestion.desregulacion_oficial_serie()
    valores = [v for _, v in sorted(serie.items())]
    assert valores == sorted(valores), valores


def test_la_serie_no_tiene_huecos():
    serie = gestion.desregulacion_oficial_serie()
    meses = sorted(serie)
    for a, b in zip(meses, meses[1:]):
        assert gestion._mes_previo_ym(b) == a, f"hueco entre {a} y {b}"


def test_el_backfill_coincide_con_las_cifras_de_portada():
    """La reconstrucción se mide sobre el gráfico; las cifras de portada de los
    otros informes son independientes de él. Si esta comparación se rompe, o
    cambió el gráfico o se rompió la medición de las barras."""
    store = _store()
    backfill = store.get("backfill_grafico", {})
    if not backfill:
        pytest.skip("sin backfill cacheado")
    errores = []
    for datos in store.get("informes", {}).values():
        p = datos["periodo"]
        if p in backfill:
            errores.append(abs(backfill[p] - datos["normas"]))
    assert errores, "ningún informe se solapa con el backfill"
    assert max(errores) <= 5, f"el backfill se despegó de los titulares: {errores}"


# ── Bandas ──────────────────────────────────────────────────────────────────

def test_la_unidad_ya_no_es_un_porcentaje_de_avance():
    """Las bandas viejas iban de 10 a 70 sobre una escala 0-100 de «% de
    avance». Con el conteo oficial (cientos de normas) esa tabla habría dado
    100 fijo desde el primer dato."""
    bandas = itcg.BANDAS_ITCG["desregulacion_normativa"]
    finitos = [c for low, high, _ in bandas for c in (low, high)
               if c not in (float("inf"), float("-inf"))]
    assert max(finitos) >= 1000, bandas


def test_hoy_no_satura():
    """Si el indicador nace en 100 deja de aportar información — el defecto que
    tenía la meta de 300 propuesta por la revisión externa."""
    serie = gestion.desregulacion_oficial_serie()
    bandas = itcg.BANDAS_ITCG["desregulacion_normativa"]
    p = parametrica.puntaje_interpolado(serie[max(serie)], bandas)
    assert 10.0 < p < 100.0, p


def test_las_cinco_bandas_estan_definidas_y_cubren_el_rango():
    bandas = itcg.BANDAS_ITCG["desregulacion_normativa"]
    assert len(bandas) == 5
    for v in (0, 50, 250, 500, 689, 1500):
        parametrica.puntaje_banda(float(v), bandas)


def test_el_indicador_sigue_en_reformas_economicas():
    ind = itcg.DIMENSIONES_ITCG["reformas_economicas"]["indicadores"]
    assert ind["desregulacion_normativa"] == 0.20
    assert abs(sum(ind.values()) - 1.0) < 1e-9
