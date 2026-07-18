"""Tests del peso del IPI dentro de la dimensión de actividad (ADR-0079).

Lo que se protege acá no es un número redondo sino un criterio: el IPI es un
componente de RESPALDO y el EMAE ya contiene a la industria, así que la
exposición de la dimensión a un solo sector tiene un techo.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import macro
import parametrica

# Participación de la industria manufacturera en el EMAE (ponderadores INDEC)
SHARE_MANUF_EN_EMAE = 0.17


def _dim():
    return itcm.DIMENSIONES_ITCM["actividad"]["indicadores"]


def test_el_emae_manda_por_amplio_margen():
    ind = _dim()
    assert ind["emae_ia"] > 3 * ind["ipi_manufacturero"], ind


def test_la_exposicion_a_manufactura_no_pasa_del_doble_de_su_peso_natural():
    """El criterio explícito de ADR-0079. El EMAE ya contiene a la industria,
    así que la exposición total es (1−p)·17% + p. Con el 35% original daba 46%,
    casi la mitad de una dimensión llamada 'actividad económica'."""
    p = _dim()["ipi_manufacturero"]
    exposicion = (1 - p) * SHARE_MANUF_EN_EMAE + p
    assert exposicion <= 2 * SHARE_MANUF_EN_EMAE + 0.01, (
        f"la dimensión quedó {exposicion:.0%} expuesta a manufactura")


def test_los_pesos_de_la_dimension_suman_uno():
    assert abs(sum(_dim().values()) - 1.0) < 1e-9


# ── El arrastre estructural que motivó bajar el peso ────────────────────────

def test_un_mes_mediano_del_ipi_puntua_muy_por_debajo_del_emae():
    """El hallazgo de ADR-0079: con las MISMAS bandas, la mediana histórica del
    IPI puntúa ~39 y la del EMAE ~71, porque la industria argentina rindió peor
    que la actividad agregada. No es un defecto de calibración —es desempeño
    real— y por eso se compensa con el peso y no recalibrando las anclas
    (criterio de ADR-0045).

    Si este test empieza a fallar porque la brecha se cerró, el peso del IPI
    conviene revisarlo: el motivo de tenerlo bajo habría desaparecido."""
    ipi = list(macro._ipi_ia_por_mes().values())
    p_ipi = parametrica.puntaje_interpolado(
        statistics.median(ipi), itcm.BANDAS_ITCM["ipi_manufacturero"])
    assert p_ipi < 50.0, (
        f"la mediana del IPI ya puntúa {p_ipi}: la brecha estructural con el "
        "EMAE se habría cerrado y el peso de ADR-0079 hay que revisarlo")


def test_las_bandas_del_ipi_siguen_siendo_las_del_emae():
    """No se recalibraron para cerrar la brecha: hacerlo blanquearía desempeño
    real (ADR-0045)."""
    assert itcm.BANDAS_ITCM["ipi_manufacturero"] == itcm.BANDAS_ITCM["emae_ia"]
