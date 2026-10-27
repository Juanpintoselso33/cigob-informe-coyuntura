"""Vetos insistidos y decretos derogados por las dos cámaras (ADR-0377), sin red."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcp  # noqa: E402
import politica  # noqa: E402

REGISTRO = {
    "vetos": [
        {"proyecto": "1", "tema": "a", "insistencia_completa": "2025-10-02"},
        {"proyecto": "2", "tema": "b", "insistencia_completa": None,
         "insistencias_votadas": [{"fecha": "2025-09-18", "camara": "Senado"}]},
    ],
    "decretos": [
        {"clave": "70/2023", "rechazos": [{"fecha": "2024-03-14", "camara": "Senado"}]},
        {"clave": "656/2024", "rechazos": [{"fecha": "2024-08-21", "camara": "Diputados"},
                                           {"fecha": "2024-09-12", "camara": "Senado"}]},
    ],
}


def test_solo_cuenta_la_insistencia_de_las_dos_camaras():
    assert [e["fecha"] for e in politica._insistencias_completas(REGISTRO)] == ["2025-10-02"]


def test_el_rechazo_de_una_camara_no_deroga():
    derogados = politica._decretos_derogados(REGISTRO)
    assert [e["fecha"] for e in derogados] == ["2024-09-12"]   # fechado en la segunda


def test_ventana_de_doce_meses_calendario():
    ev = [{"nombre": "x", "fecha": "2025-10-02"}]
    assert len(politica._eventos_12m(ev, date(2026, 9, 30))) == 1
    assert len(politica._eventos_12m(ev, date(2026, 10, 1))) == 0
    serie = politica.serie_eventos_12m(ev, desde="2025-09", hasta=date(2026, 10, 27))
    assert serie["2025-09"] == 0 and serie["2025-10"] == 1 and serie["2026-10"] == 0


def test_cero_es_senal_y_no_falta_de_dato():
    r = politica.fetch_insistencias_vetos({"vetos": [], "decretos": []})
    assert r["valor"] == 0.0 and "cero es la señal" in r["detalle_txt"]


def test_reemplazan_a_quorum_y_desafios_en_la_dimension():
    dim = itcp.DIMENSIONES_ITCP["poder_legislativo"]["indicadores"]
    assert dim["insistencias_vetos"] == dim["rechazos_decretos"] == 0.15
    assert {"veto_quorum", "desafios_legislativos"} <= set(itcp.INDICADORES_SUSPENDIDOS)
    assert "veto_quorum" not in dim and "desafios_legislativos" not in dim
    assert abs(sum(dim.values()) - 1.0) < 1e-9


def test_anclas_cero_uno_tres_cuatro():
    b = itcp.BANDAS_ITCP["rechazos_decretos"]
    from parametrica import puntaje_interpolado
    assert [puntaje_interpolado(v, b) for v in (0, 1, 3, 4, 6)] == [100, 60, 35, 10, 10]
