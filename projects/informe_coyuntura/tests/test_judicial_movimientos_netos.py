import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cobertura_judicial import conciliar_movimientos, reconstruir_meses


def _mov(norma="1/2026", delta=1, fecha="2026-07-10"):
    return {"norma": norma, "tipo": "designacion", "fecha": fecha, "delta": delta,
            "fuente": "https://organismo.gob.ar/norma", "motivo": "Cotejo del acto"}


def test_promocion_no_se_suma_como_alta_nueva():
    eventos = conciliar_movimientos([_mov()], [_mov(delta=0)])
    assert sum(e["delta"] for e in eventos) == 0


def test_suplemento_no_duplica_el_alta_al_actualizarse_el_csv():
    antes = conciliar_movimientos([], [_mov()])
    despues = conciliar_movimientos([_mov()], [_mov()])
    assert antes == despues
    assert sum(e["delta"] for e in despues) == 1


def test_norma_multimovimiento_exige_desagregacion():
    with pytest.raises(ValueError, match="desagregación"):
        conciliar_movimientos([_mov(), _mov()], [])


def test_ancla_corregida_no_duplica_baja_anterior_y_aplica_baja_posterior():
    bajas = [_mov("baja-1", -1, "2026-03-18"), _mov("baja-2", -1, "2026-08-18")]
    serie = reconstruir_meses(10, 7, "2026-06-05", bajas, "2026-09-08")
    assert serie["2026-02"]["cubiertos"] == 8
    assert serie["2026-03"]["cubiertos"] == 7
    assert serie["2026-07"]["cubiertos"] == 7
    assert serie["2026-08"]["cubiertos"] == 6
    assert serie["2026-09"]["corte"] == "2026-09-08"


def test_un_evento_futuro_no_entra_en_el_corte():
    serie = reconstruir_meses(10, 7, "2026-06-05", [_mov(fecha="2026-09-20")], "2026-09-08")
    assert serie["2026-09"]["cubiertos"] == 7


def test_no_extrapola_meses_posteriores_a_la_revision():
    serie = reconstruir_meses(10, 7, "2026-06-05", [], "2026-07-13")
    assert max(serie) == "2026-07"
