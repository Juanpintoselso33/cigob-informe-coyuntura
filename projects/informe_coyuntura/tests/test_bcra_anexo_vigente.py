"""El HTTP 200 del archivo anterior no prueba que sea la edición vigente."""
import io
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import descargar_series as ds


def test_mora_usa_personales_y_tarjetas_del_anexo_actual(monkeypatch):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Calidad de Cartera (por líneas)'
    fechas = [datetime(2022 + m // 12, m % 12 + 1, 1) for m in range(54)]
    ws.append(['2. Familias - Total'])
    ws.append(['Fecha', *fechas])
    ws.append(['Personales', *([20.] * 54)])
    ws.append(['Tarjetas de crédito', *([10.] * 54)])
    ws.append(['Fuente'])
    ws.append(['Fecha', *fechas])
    ws.append(['Personales', *([100.] * 54)])
    ws.append(['Tarjetas de crédito', *([300.] * 54)])
    ws.append(['Fuente'])
    buf = io.BytesIO()
    wb.save(buf)
    urls = []

    def get(url, **kwargs):
        urls.append(url)
        return SimpleNamespace(content=buf.getvalue(), raise_for_status=lambda: None)

    monkeypatch.setattr(ds.requests, 'get', get)
    deuda, mora = ds._anexo_bancos_familias()
    assert urls == ['https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-bancos-anexo.xlsx']
    assert max(mora) == '2026-06'
    assert mora['2026-06'] == 12.5
    assert deuda['2026-06'] == 400
