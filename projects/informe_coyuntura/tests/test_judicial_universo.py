"""El movimiento debe pertenecer al stock medido, no sólo decir «Juez»."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica


def _fila(norma, cargo, fecha="2025-01-01"):
    return {"cargo_tipo": "Juez", "norma_numero": norma,
            "cargo_detalle": cargo, "fecha_desginacion": fecha,
            "fecha_renuncia": fecha}


def test_la_renovacion_no_crea_vacante_cubierta():
    filas = [_fila("DEC. 876/2024", "Vocal de cámara"),
             _fila("DEC. 875/2024", "Vocal de cámara"),
             _fila("DEC. 736/2025", "Vocal de cámara"),
             _fila("DEC. 446/2026", "Juez federal", "2026-06-11")]
    assert politica._jus_fechas(filas, "fecha_desginacion") == ["2026-06-11"]


def test_renovaciones_posteriores_no_se_convierten_en_altas_al_vencer_fecha():
    filas = [_fila(f"DEC. {n}/2026", "Vocal", "2026-11-11")
             for n in (367, 615, 645, 853)]
    assert politica._jus_fechas(filas, "fecha_desginacion") == []


def test_corte_suprema_no_entra_por_designacion_ni_por_renuncia():
    filas = [_fila("DEC. 137/2025", "Juez de la Corte Suprema de Justicia de la Nación"),
             _fila("DEC. 1128/2024", "Juez de la Corte Suprema de Justicia de la Nación")]
    for campo in ("fecha_desginacion", "fecha_renuncia"):
        assert politica._jus_fechas(filas, campo) == []


def test_la_camara_tambien_identifica_el_universo():
    fila = _fila("DEC. 137/2025", "Juez")
    fila["camara"] = "CORTE SUPREMA DE JUSTICIA"
    assert politica._jus_fechas([fila], "fecha_desginacion") == []


def test_renuncia_de_juez_inferior_se_conserva():
    fila = _fila("DEC. 664/2026", "Juzgado Federal de Neuquén", "2026-09-01")
    assert politica._jus_fechas([fila], "fecha_renuncia") == ["2026-09-01"]
