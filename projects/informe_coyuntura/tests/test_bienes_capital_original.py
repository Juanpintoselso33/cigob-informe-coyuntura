import sys
from pathlib import Path
from datetime import date
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bienes_capital as bk


def filas():
    f = [["", "Importaciones mensuales por usos económicos. Enero-julio de 2026 y año 2025", "", "", ""],
         ["", "Período", "Bienes de capital (BK)", "", ""],
         ["", "", "Año 2026*", "Año 2025*", "Variación %"],
         ["", "", "Millones de USD", "", ""]]
    for i, mes in enumerate("ene feb mar abr may jun jul ago sep oct nov dic".split()):
        f.append(["", mes, 90.123 + i if i < 7 else "", 100 + i, ""])
    return f


def libro(monkeypatch, f):
    hoja = SimpleNamespace(nrows=len(f), ncols=5, cell_value=lambda i,j:f[i][j])
    monkeypatch.setattr(bk.xlrd, "open_workbook", lambda **_: SimpleNamespace(sheets=lambda:[hoja]))


def test_lee_meses_y_precision_sin_incorporar_anuales(monkeypatch):
    f=filas();f.append(["", "Total anual", 9999, 9999, ""]);libro(monkeypatch,f)
    s=bk.parsear(b"",date(2026,9,8))
    assert len(s)==19
    assert s["2026-01-01"]==90.123
    assert max(s)=="2026-07-01"


@pytest.mark.parametrize("fila,col,valor",[
    (4,3,""), (5,2,""), (5,1,"ene"), (4,2,float("nan")), (4,2,-1),
    (1,2,"Piezas y accesorios para bienes de capital (PyA)"),
    (2,3,"Año 2024*"), (3,2,"Miles de USD"),
])
def test_rechaza_universo_unidad_o_calendario_incorrectos(monkeypatch,fila,col,valor):
    f=filas();f[fila][col]=valor;libro(monkeypatch,f)
    with pytest.raises(ValueError):bk.parsear(b"",date(2026,9,8))


def test_original_reemplaza_revisiones_y_conserva_api_anterior():
    api=[["2024-12-01",50],["2025-01-01",100],["2026-06-01",300]]
    original={"2025-01-01":101.234,"2026-06-01":301.234,"2026-07-01":290.123}
    s=bk.completar(api,original,50)
    assert s==[["2026-07-01",290.123],["2026-06-01",301.234],["2025-01-01",101.234],["2024-12-01",50]]
    assert bk.completar(api,original,1)==s[:1]


def test_api_mas_nueva_no_se_oculta_con_original_viejo():
    with pytest.raises(ValueError,match="más reciente"):
        bk.completar([["2026-08-01",1]],{"2026-07-01":2},16)


def test_no_acepta_mes_en_curso(monkeypatch):
    libro(monkeypatch,filas())
    with pytest.raises(ValueError,match="no cerrado"):
        bk.parsear(b"",date(2026,7,31))


@pytest.mark.parametrize("api",[
    [["2024-12-01",float("nan")]],
    [["2024-12-01",1],["2024-12-01",2]],
    [["2024-12-15",1]],
])
def test_no_preserva_historia_anterior_invalida(api):
    with pytest.raises(ValueError):
        bk.completar(api,{"2025-01-01":2},16)


def test_enlace_exige_operacion_anios_consecutivos_y_dominio_oficial():
    html="""<a href='/ftp/cuadros/economia/impo_uso_economico_2024_2025.xls'>viejo</a>
    <a href='/ftp/cuadros/economia/impo_uso_economico_2025_2026.xls'>nuevo</a>
    <a href='/ftp/cuadros/economia/impo_uso_economico_2023_2026.xls'>incompatible</a>
    <a href='https://otro.test/ftp/cuadros/economia/impo_uso_economico_2026_2027.xls'>otro</a>"""
    assert bk.descubrir(html,date(2026,9,8)).endswith("2025_2026.xls")
