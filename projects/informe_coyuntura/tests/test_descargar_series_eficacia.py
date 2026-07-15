"""Serie mensual de eficacia_legislativa: cohorte madura (ADR-0061) con
numerador desde leyes-sancionadas y denominador sin comunicaciones
administrativas (ADR-0062)."""
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import politica


def test_fetch_eficacia_serie_cohorte_madura_del_mes_actual(monkeypatch):
    """El último punto de la serie (mes en curso) solo cuenta proyectos de
    ley con al menos 365 días de margen: uno publicado hace 500 días entra
    a la cohorte (y cuenta como aprobado vía leyes-sancionadas, aunque la
    sanción haya sido en el Senado); uno de hace 100 días queda afuera; una
    comunicación de veto (TIPO 'MENSAJE') no entra al denominador."""
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
                {"PROYECTO_ID": "M1", "TIPO": "MENSAJE Y PROYECTO DE LEY",
                 "EXP_DIPUTADOS": "0001-PE-2023", "PUBLICACION_FECHA": maduro},
                {"PROYECTO_ID": "R1", "TIPO": "MENSAJE Y PROYECTO DE LEY",
                 "EXP_SENADO": "0002-PE-2024", "PUBLICACION_FECHA": reciente},
                {"PROYECTO_ID": "V1", "TIPO": "MENSAJE",
                 "EXP_DIPUTADOS": "0003-PE-2023", "PUBLICACION_FECHA": maduro},
            ]
        assert rid == politica.HCDN_LEYES_SANC_RID
        return [
            {"PROYECTO_ID": "M1", "LEY": 27700, "CAMARA_SANCIONADORA": "Senado",
             "SANCION_DEFINITIVA": (hoy - timedelta(days=50)).isoformat()},
        ]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    serie = descargar_series.fetch_eficacia_serie()

    assert serie[-1][0] == "2024-06-01"
    assert serie[-1][1] == 100.0   # 1/1: solo M1 entra a la cohorte, y es ley


def test_fetch_eficacia_serie_es_reproducible_no_retroactivo(monkeypatch):
    """Un proyecto sancionado DESPUÉS del cierre de un mes histórico no debe
    aparecer como aprobado en el punto de ESE mes — la serie usa
    SANCION_DEFINITIVA <= fin de mes, no 'sancionado alguna vez hasta hoy',
    para que los puntos ya publicados no cambien retroactivamente."""
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
            return [{"PROYECTO_ID": "M1", "TIPO": "MENSAJE Y PROYECTO DE LEY",
                      "EXP_DIPUTADOS": "0001-PE-2022", "PUBLICACION_FECHA": publicado}]
        assert rid == politica.HCDN_LEYES_SANC_RID
        return [{"PROYECTO_ID": "M1", "LEY": 27701, "CAMARA_SANCIONADORA": "Senado",
                  "SANCION_DEFINITIVA": sancionado_en}]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    serie = descargar_series.fetch_eficacia_serie()
    por_mes = {fecha: valor for fecha, valor in serie}

    assert por_mes["2024-01-01"] == 0.0     # todavía no se había sancionado
    assert por_mes["2024-06-01"] == 100.0   # para el mes en curso, ya sí


def test_fetch_eficacia_serie_ignora_sancion_definitiva_na(monkeypatch):
    """Una fila de leyes-sancionadas con SANCION_DEFINITIVA 'NA' no puede
    fecharse: queda fuera de todos los puntos históricos de la serie (no se
    puede saber si la sanción ya había ocurrido al cierre de cada mes)."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    hoy = date(2024, 6, 15)
    publicado = (hoy - timedelta(days=650)).isoformat()

    def fake_paginate(rid, q=""):
        if rid == politica.HCDN_PROYECTOS_RID:
            return [{"PROYECTO_ID": "M1", "TIPO": "MENSAJE Y PROYECTO DE LEY",
                      "EXP_DIPUTADOS": "0001-PE-2022", "PUBLICACION_FECHA": publicado}]
        return [{"PROYECTO_ID": "M1", "LEY": 27702, "CAMARA_SANCIONADORA": "Senado",
                  "SANCION_DEFINITIVA": "NA"}]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    serie = descargar_series.fetch_eficacia_serie()

    assert all(valor == 0.0 for _, valor in serie)
