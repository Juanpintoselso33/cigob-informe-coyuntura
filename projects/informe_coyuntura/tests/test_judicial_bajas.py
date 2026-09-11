import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cobertura_judicial import conciliar_bajas


def _baja(fecha="2026-03-18", tipo="fallecimiento"):
    return {"persona": "PÉREZ, Ana", "organo": "Tribunal 17", "fecha": fecha,
            "tipo": tipo, "fuente": "https://organismo.gob.ar/acto"}


def _padron(vacante="NO"):
    return [{"magistrado_nombre": "PEREZ, Ana", "organo_nombre": "Tribunal 17",
             "organo_habilitado": "SI", "cargo_vacante": vacante}]


def test_baja_omitida_corrige_el_ancla_sin_mutar_la_fuente():
    p = _padron()
    eventos, correcciones = conciliar_bajas(p, "2026-06-05", [_baja()])
    assert len(eventos) == len(correcciones) == 1
    assert p[0]["cargo_vacante"] == "NO"


def test_baja_ya_reflejada_no_se_descuenta_dos_veces():
    eventos, correcciones = conciliar_bajas(_padron("SI"), "2026-06-05", [_baja()])
    assert len(eventos) == 1
    assert correcciones == []


def test_baja_posterior_no_modifica_la_foto_anterior():
    eventos, correcciones = conciliar_bajas(_padron(), "2026-06-05", [_baja("2026-08-18")])
    assert len(eventos) == 1
    assert correcciones == []


def test_suspension_no_se_puede_convertir_en_vacante():
    with pytest.raises(ValueError, match="baja efectiva"):
        conciliar_bajas(_padron(), "2026-06-05", [_baja(tipo="suspension")])


def test_republicar_una_baja_no_duplica_el_conteo():
    eventos, correcciones = conciliar_bajas(_padron(), "2026-06-05", [_baja(), _baja()])
    assert len(eventos) == len(correcciones) == 1
