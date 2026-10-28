# -*- coding: utf-8 -*-
"""El bloque de cada senador es el del día de la votación (ADR-0400).

El portal del Senado muestra en todas las actas el bloque ACTUAL del senador.
Sin el registro de pases, Luis Juez cuenta como La Libertad Avanza en 2024 y
Paoltroni también en los quince meses en que estuvo expulsado del bloque.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica  # noqa: E402

REGISTRO = Path(__file__).resolve().parents[1] / "data" / "politica" / "pases_senadores.json"


def _lla(nombre, fecha, bloque_acta="LA LIBERTAD AVANZA"):
    return politica.es_bloque_lla(politica.bloque_senador_vigente(nombre, bloque_acta, fecha))


def test_juez_es_lla_recien_desde_que_entra_al_bloque():
    assert not _lla("JUEZ, LUIS ALFREDO", "2024-06-12")
    assert not _lla("JUEZ, LUIS ALFREDO", "2025-12-26")   # interbloque, no bloque
    assert not _lla("JUEZ, LUIS ALFREDO", "2026-02-22")
    assert _lla("JUEZ, LUIS ALFREDO", "2026-02-23")
    assert _lla("JUEZ, LUIS ALFREDO", datetime(2026, 9, 24))


def test_paoltroni_fuera_del_bloque_mientras_estuvo_expulsado():
    assert _lla("PAOLTRONI, FRANCISCO MANUEL", "2024-08-27")
    assert not _lla("PAOLTRONI, FRANCISCO MANUEL", "2024-08-28")
    assert not _lla("PAOLTRONI, FRANCISCO MANUEL", date(2025, 7, 10))
    assert _lla("PAOLTRONI, FRANCISCO MANUEL", "2025-12-10")


def test_alvarez_rivero_pasa_del_pro_en_noviembre_de_2025():
    assert not _lla("ALVAREZ RIVERO, CARMEN", "2025-11-03")
    assert _lla("ÁLVAREZ RIVERO, CARMEN", "2025-11-04")   # se compara sin tildes


def test_un_senador_que_no_figura_conserva_el_bloque_del_acta():
    assert politica.bloque_senador_vigente("ABDALA, BARTOLOMÉ ESTEBAN", "LA LIBERTAD AVANZA",
                                           "2024-03-01") == "LA LIBERTAD AVANZA"
    assert politica.bloque_senador_vigente("MAYANS, JOSÉ", "Justicialista", "2024-03-01") == "Justicialista"


def test_el_registro_tiene_fuente_y_tramos_que_no_se_pisan():
    pases = json.loads(REGISTRO.read_text(encoding="utf-8"))["pases"]
    por_senador = {}
    for p in pases:
        assert p["fuente"].startswith("https://"), p
        assert p["hasta"] is None or p["desde"] <= p["hasta"], p
        por_senador.setdefault(politica._clave_senador(p["senador"]), []).append(p)
    for nombre, tramos in por_senador.items():
        tramos.sort(key=lambda p: p["desde"])
        for a, b in zip(tramos, tramos[1:]):
            assert a["hasta"] is not None and a["hasta"] < b["desde"], (nombre, a, b)
        assert tramos[-1]["hasta"] is None, nombre   # el último tramo es el vigente
    assert {"JUEZ, LUIS ALFREDO", "PAOLTRONI, FRANCISCO MANUEL", "ALVAREZ RIVERO, CARMEN"} <= set(por_senador)


ACTA_2024 = [
    {"nombre": "JUEZ, LUIS ALFREDO", "bloque": "LA LIBERTAD AVANZA", "provincia": "Córdoba", "voto": "NEGATIVO"},
    {"nombre": "ABDALA, BARTOLOMÉ ESTEBAN", "bloque": "LA LIBERTAD AVANZA", "provincia": "San Luis", "voto": "AFIRMATIVO"},
    {"nombre": "ATAUCHE, EZEQUIEL", "bloque": "LA LIBERTAD AVANZA", "provincia": "Jujuy", "voto": "AFIRMATIVO"},
    {"nombre": "OTRO, UNO", "bloque": "UCR", "provincia": "Córdoba", "voto": "AFIRMATIVO"},
]


def test_la_cohesion_del_senado_no_cuenta_a_juez_en_2024(monkeypatch):
    monkeypatch.setattr(politica, "datetime", type("Hoy", (datetime,), {"now": classmethod(lambda c: c(2024, 7, 1))}))
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: object())
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda *_: [{"id": "1", "fecha": datetime(2024, 6, 12)}])
    monkeypatch.setattr(politica, "_paced_get", lambda *_: SimpleNamespace(text="x"))
    monkeypatch.setattr(politica, "_parsear_acta", lambda _: ACTA_2024)
    r = politica.fetch_cohesion_bloque_senado()
    assert r["valor"] == 100.0   # con el bloque del portal, Juez partía al bloque: 33,3


def test_el_alineamiento_cuenta_a_juez_como_senador_de_otro_bloque_en_2024():
    filas = politica.filas_senado_a_la_fecha(ACTA_2024, "2024-06-12")
    assert politica._alineamiento_por_provincia(filas) == {"Córdoba": (1, 2)}
    filas_hoy = politica.filas_senado_a_la_fecha(ACTA_2024, "2026-06-12")
    assert politica._alineamiento_por_provincia(filas_hoy) == {"Córdoba": (1, 1)}


def test_votos_sobre_bancas_cuenta_las_bancas_de_lla_a_la_fecha():
    conteos = politica._vsb_conteos(politica.filas_senado_a_la_fecha(ACTA_2024, "2024-06-12"))
    assert conteos["bancas_lla"] == 2 and conteos["lla_neg"] == 0
    assert politica.VSB_VERSION_SENADO >= 3   # el caché viejo se relee con el registro
