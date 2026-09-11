"""Un TP mal fechado no adelanta la entrada de un proyecto a la cohorte."""
from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica
import descargar_series


@pytest.mark.parametrize("corte,esperado", [("2026-07-31", 100.0), ("2026-08-06", 50.0)])
def test_fecha_tp_compartida_en_borde_de_cohorte(monkeypatch, corte, esperado):
    class Fecha(date):
        @classmethod
        def today(cls):
            return cls.fromisoformat(corte)

    proyectos = [
        {"PROYECTO_ID": "maduro", "EXP_DIPUTADOS": "0001-PE-2025",
         "TIPO": "MENSAJE Y PROYECTO DE LEY", "PUBLICACION_FECHA": "2025-03-17"},
        {"PROYECTO_ID": "medalla", "EXP_DIPUTADOS": "0007-PE-2025",
         "TIPO": "MENSAJE Y PROYECTO DE LEY", "PUBLICACION_FECHA": "2025-07-30",
         "PUBLICACION_ID": "HCDN143TP109"},
    ]
    leyes = [{"PROYECTO_ID": "maduro", "SANCION_DEFINITIVA": "2025-06-01"}]
    monkeypatch.setattr(politica, "date", Fecha)
    monkeypatch.setattr(politica, "_hcdn_paginate", lambda rid, **kw:
                        proyectos if rid == politica.HCDN_PROYECTOS_RID else leyes)
    from datetime import timedelta
    limite = (Fecha.today() - timedelta(days=365)).isoformat()
    monkeypatch.setattr(descargar_series, "_hcdn_ventanas_12m",
                        lambda: [(corte[:7], limite, corte)])
    assert politica.fetch_eficacia_legislativa()["valor"] == esperado
    assert descargar_series.fetch_eficacia_serie()[0][1] == esperado
    assert proyectos[1]["PUBLICACION_FECHA"] == "2025-07-30"


def test_publicacion_enero_no_es_fecha_de_firma():
    fila = {"PUBLICACION_ID": "HCDN142TP223", "PUBLICACION_FECHA": "2025-01-22"}
    assert politica._fecha_publicacion_proyecto(fila) == "2025-01-20"
    assert politica._fecha_publicacion_proyecto({"PUBLICACION_FECHA": "2025-01-17T00:00:00"}) == "2025-01-17"
