import io
import sys
from pathlib import Path
from datetime import date

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gestion
import descargar_series


def libro(nombre, codigo, valores):
    w = openpyxl.Workbook()
    w.active.title = nombre
    w.active.append(['Código', 'Enero', 'Junio', 'Julio'])
    w.active.append([codigo, *valores])
    return w


@pytest.mark.parametrize('inactivo', [False, True])
def test_descubre_sufijo_y_conserva_estado_del_enlace(monkeypatch, inactivo):
    url = gestion.SSS_RNAS_URL.format(anio=2026).replace('.xlsx', '.14.08.xlsx')
    b = io.BytesIO(); libro('RNAS 2026', 900001, [10, 20, None]).save(b)
    llamadas = []
    def get(u):
        llamadas.append(u)
        if u == gestion.SSS_PORTAL_URL:
            return f'<a href="{"blank:#" if inactivo else ""}{url}">Datos</a>'.encode()
        assert u == url
        return b.getvalue()
    monkeypatch.setattr(gestion, '_http_get_resiliente', get)
    w = gestion._sss_archivo(gestion.SSS_RNAS_URL, 2026)
    assert w._cigob_fuente_url == url
    assert w._cigob_referencia_inactiva is inactivo
    assert len(llamadas) == 2


def test_archivo_referenciado_roto_no_vuelve_a_un_archivo_viejo(monkeypatch):
    llamadas = []
    def abrir(tpl, anio):
        llamadas.append(anio)
        raise ConnectionError('Descarga incompleta')
    monkeypatch.setattr(gestion, '_sss_archivo', abrir)
    with pytest.raises(ConnectionError):
        gestion._sss_xlsx(gestion.SSS_RNAS_URL)
    assert llamadas == [date.today().year]


def test_tarjeta_y_serie_comparten_archivo_y_no_usan_denominador_futuro(monkeypatch):
    class Fecha(date):
        @classmethod
        def today(cls):
            return cls(2026, 9, 8)
    monkeypatch.setattr(gestion, 'date', Fecha)
    monkeypatch.setattr(descargar_series, 'date', Fecha)
    llamadas = []
    def abrir(tpl, anio):
        llamadas.append((tpl, anio))
        if tpl == gestion.SSS_RNAS_URL:
            return libro(f'RNAS {anio}', 900001, [20, 30, None])
        return libro(f'RNEMP {anio}', 1, [100, 120, 150])
    monkeypatch.setattr(gestion, '_sss_archivo', abrir)
    card = gestion.fetch_libertad_opcion_salud()
    puntos = dict(descargar_series.fetch_opcion_salud_serie())
    assert card['fecha_dato'] == card['fecha_denominador'] == '2026-06-01'
    assert card['valor'] == puntos['2026-06-01'] == 25
    assert (gestion.SSS_RNAS_URL, 2024) in llamadas


def test_catalogo_ambiguo_no_elige_por_orden_html(monkeypatch):
    url = gestion.SSS_RNAS_URL.format(anio=2026)
    html = f'<a href="{url}">uno</a><a href="{url.replace(".xlsx", ".14.08.xlsx")}">dos</a>'
    monkeypatch.setattr(gestion, '_http_get_resiliente', lambda u: html.encode())
    with pytest.raises(ValueError, match='ambigua'):
        gestion._sss_archivo(gestion.SSS_RNAS_URL, 2026)
