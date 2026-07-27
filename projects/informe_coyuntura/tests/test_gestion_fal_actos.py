"""El FAL mide sus dos actos fundamentales (ADR-0142).

Lo que se protege es la ESCALA: tres estados posibles (0 / 50 / 100), uno por
acto cumplido, y la serie reconstruida con la misma regla. También queda
anclada por escrito la limitación asumida —el indicador ya no discrimina— para
que no se descubra por sorpresa dentro de seis meses.
"""
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import descargar_series  # noqa: E402
import gestion  # noqa: E402
import itcg  # noqa: E402
import parametrica  # noqa: E402


def test_los_dos_actos_son_ley_y_reglamentacion():
    normas = [n for n, _ in gestion.FAL_ACTOS_FUNDAMENTALES]
    assert normas == ["Ley 27.802", "Decreto 408/2026"]
    assert len(gestion.FAL_ACTOS_FUNDAMENTALES) == 2, "cada acto vale la mitad"


def test_los_dos_actos_estan_en_el_registro_de_hitos():
    """No se inventan fechas: cada acto tiene que estar respaldado por una norma
    publicada en fal_hitos.json, verificable por número en InfoLeg."""
    import json
    hitos = json.loads(gestion.FAL_HITOS_PATH.read_text(encoding="utf-8-sig"))
    por_norma = {h["norma"]: h for h in hitos["construccion"]}
    for norma, _ in gestion.FAL_ACTOS_FUNDAMENTALES:
        assert norma in por_norma, f"{norma} no está en fal_hitos.json"
        assert por_norma[norma]["fecha"] <= date.today().isoformat()
        assert por_norma[norma].get("fuente"), "el hito debe declarar su fuente"


def test_la_escala_solo_toma_tres_valores():
    """La consecuencia directa del diseño: dos actos binarios → 0, 50 o 100."""
    B = itcg.BANDAS_ITCG
    esperado = {0.0: 10.0, 50.0: 50.0, 100.0: 100.0}
    for valor, puntaje in esperado.items():
        assert parametrica.puntaje_de(
            valor, "fal_modernizacion_laboral", B) == puntaje


def test_la_serie_es_una_escalera_de_tres_peldanos():
    serie = descargar_series.fetch_fal_serie()
    valores = sorted({v for _, v in serie})
    assert valores == [0.0, 50.0, 100.0]
    # arranca en dic-2023 (feedback_backfill_series) y sube en el mes de cada norma
    assert serie[0][0] == "2023-12-01" and serie[0][1] == 0.0
    por_fecha = dict(serie)
    assert por_fecha["2026-02-01"] == 0.0, "antes de la ley"
    assert por_fecha["2026-03-01"] == 50.0, "Ley 27.802, 06-mar-2026"
    assert por_fecha["2026-06-01"] == 100.0, "Decreto 408/2026, 01-jun-2026"
    # monótona: los actos no se deshacen
    assert all(b >= a for (_, a), (_, b) in zip(serie, serie[1:]))


def test_el_contexto_no_puntua():
    """Fondos CNV y menciones del BO se siguen relevando pero salieron del
    cálculo: si volvieran a entrar sin ADR, esto lo delata."""
    fuente = (RAIZ / "scripts" / "gestion.py").read_text(encoding="utf-8")
    i = fuente.index("def fetch_fal_modernizacion_laboral")
    j = fuente.index("def fetch_litigiosidad_laboral")
    cuerpo = fuente[i:j]
    assert "FAL_PESO_CONSTRUCCION" not in cuerpo, "volvió el compuesto de ADR-0098"
    assert "indice = round(100.0 * len(cumplidos)" in cuerpo


def test_la_limitacion_esta_declarada_en_la_ficha():
    """El indicador quedó fijo en 100 y no vuelve a moverse. Es una limitación
    seria y asumida: tiene que estar dicha en el texto público, no sólo en el
    ADR."""
    ficha = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
    i = ficha.index("fal_modernizacion_laboral: {")
    bloque = ficha[i:i + 4000]
    assert "no pueden deshacerse" in bloque
    assert "fijo en cien" in bloque
