"""Serie mensual de eficacia_legislativa: cohorte madura (ADR-0061) con
numerador desde leyes-sancionadas y denominador sin comunicaciones
administrativas (ADR-0062)."""
import sys
import pytest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series
import politica
from cotejo_manual import avisos


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


@pytest.mark.parametrize("invalida", ["", "NA", "2024-02-30", None])
def test_fetch_eficacia_serie_falla_y_avisa_con_fecha_de_sancion_invalida(monkeypatch, capsys, invalida):
    """Una fila de leyes-sancionadas sin fecha canónica no se puede ubicar en
    ningún mes: en vez de contarla o descartarla en silencio, la serie falla
    (misma regla que la card) y registra el cotejo manual."""
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
                  "SANCION_DEFINITIVA": invalida},
                {"PROYECTO_ID": "M2", "LEY": 27703, "CAMARA_SANCIONADORA": "Senado",
                  "SANCION_DEFINITIVA": "2024-03-01"}]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    with pytest.raises(ValueError):
        descargar_series.fetch_eficacia_serie()
    mensajes = avisos(capsys.readouterr().err)
    assert len(mensajes) == 1 and "M1" in mensajes[0]


def test_fetch_eficacia_serie_conserva_csv_anterior_si_una_fecha_es_invalida(tmp_path, monkeypatch, capsys):
    """Por el camino real de `descargar`: el fallo del fetcher deja las filas
    que el CSV ya tenía, sin publicar una serie parcial ni borrar la vieja."""
    monkeypatch.setattr(descargar_series, "OUTPUT_DIR", tmp_path)
    (tmp_path / "politica.csv").write_text(
        "fecha,indicador,valor,unidad,fuente\n"
        "2024-05-01,eficacia_legislativa,25.0,%,x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(politica, "_hcdn_paginate",
                        lambda rid, q="": [{"PROYECTO_ID": "M1", "LEY": 1, "SANCION_DEFINITIVA": ""}])
    derivadas = [d for d in descargar_series.POLITICA_DERIVADAS if d[0] == "eficacia_legislativa"]
    descargar_series.descargar("politica", [], [], derivadas, solo_indicador="eficacia_legislativa")
    filas = (tmp_path / "politica.csv").read_text(encoding="utf-8").splitlines()
    assert "2024-05-01,eficacia_legislativa,25.0,%,x" in filas
    assert len([f for f in filas if "eficacia_legislativa" in f]) == 1
    salida = capsys.readouterr()
    assert "[ERR] eficacia_legislativa" in salida.out
    assert len(avisos(salida.err)) == 1 and "M1" in avisos(salida.err)[0]


def test_fetch_eficacia_serie_usa_correccion_documentada_como_la_card(tmp_path, monkeypatch, capsys):
    """Una fecha documentada en sanciones_fechas_verificadas.json entra al
    numerador de la serie igual que al de la card, sin aviso."""
    import json
    import cotejo_manual
    p = tmp_path / "sanciones.json"
    p.write_text(json.dumps({"revisado_en": "2024-06-15", "correcciones": [
        {"PROYECTO_ID": "M1", "SANCION_DEFINITIVA": "2024-03-01", "fuente": "https://boletinoficial.gob.ar/x"}]}))
    monkeypatch.setattr(cotejo_manual, "CORRECCIONES_SANCION", p)

    class FechaFija(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 15)

    monkeypatch.setattr(descargar_series, "date", FechaFija)
    monkeypatch.setattr(cotejo_manual, "date", FechaFija)
    hoy = date(2024, 6, 15)
    publicado = (hoy - timedelta(days=650)).isoformat()

    def fake_paginate(rid, q=""):
        if rid == politica.HCDN_PROYECTOS_RID:
            return [{"PROYECTO_ID": "M1", "TIPO": "MENSAJE Y PROYECTO DE LEY",
                      "EXP_DIPUTADOS": "0001-PE-2022", "PUBLICACION_FECHA": publicado}]
        return [{"PROYECTO_ID": "M1", "LEY": 27702, "SANCION_DEFINITIVA": "NA"}]

    monkeypatch.setattr(politica, "_hcdn_paginate", fake_paginate)
    por_mes = dict(descargar_series.fetch_eficacia_serie())
    assert por_mes["2024-01-01"] == 0.0
    assert por_mes["2024-06-01"] == 100.0
    assert politica._leyes_sancionadas_ids("2024-06-15") == {"M1"}
    assert avisos(capsys.readouterr().err) == []
