"""Julio del XLS oficial no debe desaparecer por tener una fecha textual."""
import sys
from pathlib import Path
from types import SimpleNamespace as N
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import descargar_series as d
import xlrd


def test_icg_mezcla_fechas_excel_y_texto(monkeypatch):
    fechas = [N(ctype=3, value=x) for x in (46023, 46054, 46082, 46113, 46143)]
    fechas += [N(ctype=1, value="jul-26"), N(ctype=1, value="nota")]
    valores = [N(ctype=2, value=2.0) for _ in fechas]
    valores[5] = N(ctype=2, value=1.93555262226756)
    ws = N(nrows=2, ncols=7, cell=lambda i,j: [fechas,valores][i][j])
    monkeypatch.setattr(xlrd, "open_workbook", lambda **kw: N(datemode=0, sheets=lambda:[ws]))
    response = N(text='download.php?fname=serie.xls', content=b'fake', raise_for_status=lambda:None)
    monkeypatch.setattr(d.requests, "get", lambda *a,**kw:response)
    serie = dict(d.fetch_icg_serie())
    assert serie["2026-07-01"] == 1.936
    assert len(serie) == 6
