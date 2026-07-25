"""Tests del cambio de recaudación total → DGI (ADR-0127)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import macro
import parametrica


def test_el_indicador_apunta_a_la_dgi():
    assert macro.INDEC_RECAUDACION_ID == "172.3_SOTAL_DDGI_M_0_0_12"


def test_el_total_y_la_aduana_siguen_disponibles_como_contexto():
    assert macro.INDEC_RECAUDACION_TOTAL_ID == "172.3_TL_RECAION_M_0_0_17"
    assert macro.INDEC_RECAUDACION_DGA_ID == "172.3_SOTAL_DDGA_M_0_0_12"


def test_el_resultado_primario_se_mide_contra_la_recaudacion_TOTAL():
    """El bug que ADR-0127 casi deja pasar: resultado_primario usaba la MISMA
    constante que el indicador de recaudación como denominador ("% de la
    recaudación"). Al apuntar esa constante a la DGI, el resultado primario
    habría pasado a medirse contra una base ~40% más chica sin que nada avisara.

    Se verifica leyendo el código, no el dato: lo que se protege es que el
    denominador esté escrito explícitamente y no herede el cambio de otro
    indicador."""
    fuente = Path(macro.__file__).read_text(encoding="utf-8")
    inicio = fuente.index("def _superavit_sobre_recaudacion_12m")
    cuerpo = fuente[inicio:inicio + 3000]
    assert "INDEC_RECAUDACION_TOTAL_ID" in cuerpo, (
        "el resultado primario dejó de apuntar explícitamente al total")
    assert "_indec_serie(INDEC_RECAUDACION_ID" not in cuerpo, (
        "el resultado primario volvió a compartir la constante del indicador "
        "de recaudación: su denominador cambiaría al cambiar de serie esa card")


def test_las_bandas_no_se_recalibraron():
    """ADR-0127 cambió la SERIE y no las bandas: misma unidad (% real i.a.) y
    mismo punto de referencia (el cero). Si alguien las mueve, que sea con un
    ADR propio y no de arrastre."""
    assert itcm.BANDAS_ITCM["recaudacion"] == [
        (10.0, float("inf"), 100), (5.0, 10.0, 80), (0.0, 5.0, 60),
        (-5.0, 0.0, 40), (float("-inf"), -5.0, 10),
    ]


def test_el_cero_sigue_siendo_el_punto_de_corte_relevante():
    """Crecer o no crecer en términos reales separa dos bandas."""
    assert parametrica.puntaje_banda(0.01, itcm.BANDAS_ITCM["recaudacion"]) == 60
    assert parametrica.puntaje_banda(0.0, itcm.BANDAS_ITCM["recaudacion"]) == 40


def test_la_serie_y_la_card_comparten_la_constante():
    """Si la serie fijara el id a mano, cambiar la card dejaría el gráfico del
    modal midiendo otra magnitud que el titular — el defecto que persigue
    test_puntaje_unico_camino."""
    import descargar_series as ds
    fuente = Path(ds.__file__).read_text(encoding="utf-8")
    inicio = fuente.index("def fetch_recaudacion_real_serie")
    cuerpo = fuente[inicio:inicio + 900]
    assert "macro.INDEC_RECAUDACION_ID" in cuerpo, cuerpo[:400]
