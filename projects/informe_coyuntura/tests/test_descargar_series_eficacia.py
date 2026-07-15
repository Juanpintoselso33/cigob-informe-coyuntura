"""Serie mensual de eficacia_legislativa con cohorte madura (ADR-0061,
reemplaza a la ventana compartida de ADR-0050)."""
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import politica


def test_fetch_eficacia_serie_cohorte_madura_del_mes_actual(monkeypatch):
    """El último punto de la serie (mes en curso) solo cuenta proyectos con
    al menos 365 días de margen: uno publicado hace 500 días entra a la
    cohorte, uno publicado hace 100 días queda afuera."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    hoy = date(2024, 6, 15)
    maduro = (hoy - timedelta(days=500)).isoformat()
    reciente = (hoy - timedelta(days=100)).isoformat()

    def fake_paginate(rid, q=""):
        if rid == politica.HCDN_PROYECTOS_RID:
            return [
                {"PROYECTO_ID": "M1", "EXP_DIPUTADOS": "0001-PE-2023", "PUBLICACION_FECHA": maduro},
                {"PROYECTO_ID": "R1", "EXP_SENADO": "0002-PE-2024", "PUBLICACION_FECHA": reciente},
            ]
        return [
            {"PROYECTO_ID": "M1", "MOVIMIENTO": "CONSIDERACION Y SANCION",
             "FECHA": (hoy - timedelta(days=50)).isoformat()},
        ]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    serie = descargar_series.fetch_eficacia_serie()

    assert serie[-1][0] == "2024-06-01"
    assert serie[-1][1] == 100.0   # 1/1: solo M1 entra a la cohorte, y se sancionó


def test_fetch_eficacia_serie_es_reproducible_no_retroactivo(monkeypatch):
    """Un proyecto sancionado DESPUÉS del cierre de un mes histórico no debe
    aparecer como aprobado en el punto de ESE mes — la serie no se revisa
    retroactivamente solo porque el proyecto finalmente se sancionó más
    tarde (a diferencia del indicador titular, que sí lo vería hoy)."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    hoy = date(2024, 6, 15)
    # 650 días atrás cae dentro de la cohorte madura tanto de 2024-01 como de
    # 2024-06 (cada mes desplaza su propia ventana de 12 meses)
    publicado = (hoy - timedelta(days=650)).isoformat()
    # sancionado DESPUÉS del cierre de 2024-01 pero antes de hoy
    sancionado_en = date(2024, 3, 1).isoformat()

    def fake_paginate(rid, q=""):
        if rid == politica.HCDN_PROYECTOS_RID:
            return [{"PROYECTO_ID": "M1", "EXP_DIPUTADOS": "0001-PE-2022",
                      "PUBLICACION_FECHA": publicado}]
        return [{"PROYECTO_ID": "M1", "MOVIMIENTO": "CONSIDERACION Y SANCION",
                  "FECHA": sancionado_en}]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    serie = descargar_series.fetch_eficacia_serie()
    por_mes = {fecha: valor for fecha, valor in serie}

    assert por_mes["2024-01-01"] == 0.0     # todavía no se había sancionado
    assert por_mes["2024-06-01"] == 100.0   # para el mes en curso, ya sí
