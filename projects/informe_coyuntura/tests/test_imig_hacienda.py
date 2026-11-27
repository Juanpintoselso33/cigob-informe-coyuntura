"""La planilla de Economía completa la serie fiscal de datos.gob.ar (ADR-0443)."""
import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import imig_hacienda as m  # noqa: E402

RES = "452.3_RESULTADO_RIO_0_M_18_54"
SAL = "452.2_SALARIOSIOS_0_T_8_22"


def _xlsx(meses=("2026-08", "2026-09", "2026-10"), resultado=(1990321.8, 1427640.0, 1931156.3)) -> bytes:
    wb = openpyxl.Workbook()
    wb.active.title = "Octubre"
    ws = wb.create_sheet("Mensualizacion")
    ws.append(["Base Caja - En millones de pesos"])
    ws.append([None, None, None] + [datetime(int(x[:4]), int(x[5:]), 1) for x in meses])
    ws.append([None, None, None, None])
    ws.append([None, None, "Salarios"] + [1603158.0, 1668761.4, 1726828.1][:len(meses)])
    ws.append([None, None, "Otros gastos de funcionamiento"] + [447304.1, 732841.9, 639456.1][:len(meses)])
    ws.append([None, "RESULTADO PRIMARIO"] + [None] + list(resultado))
    ws.append([None, "RESULTADO PRIMARIO según Programa Facilidades Extendidas", None, 1.0, 2.0, 3.0])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def _zip(**archivos) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre, contenido)
    return b.getvalue()


def test_parsea_las_tres_filas_por_mes():
    f = m.parsear(_xlsx())
    assert f["resultado primario"]["2026-10"] == pytest.approx(1931156.3)
    assert f["salarios"]["2026-09"] == pytest.approx(1668761.4)
    # la fila del programa con el FMI no pisa a la primera «resultado primario»
    assert f["resultado primario"]["2026-08"] == pytest.approx(1990321.8)


def test_lee_el_imig_dentro_del_zip_y_no_el_de_base_caja():
    z = _zip(**{"Octubre/Octubre 26.xlsx": b"no", "Octubre/IMIG Octubre 2026.xlsx": _xlsx()})
    assert m.parsear(m.libro(z, "https://x/octubre.zip"))["salarios"]["2026-10"] == pytest.approx(1726828.1)


def test_un_xlsx_suelto_pasa_y_un_rar_no():
    x = _xlsx()
    assert m.libro(x, "https://x/marzo_26.xlsx") == x
    with pytest.raises(ValueError):
        m.libro(b"Rar!\x1a\x07\x00", "https://x/cuentas_publicas3.rar")


def test_descubre_el_ultimo_mes_del_anio_mas_nuevo():
    base = "https://www.argentina.gob.ar/sites/default/files/"
    html = "".join(f'<a href="{base}{u}">{t}</a>' for t, u in [
        ("Enero", "e26.xlsx"), ("Junio", "junio.zip"), ("Agosto", "agosto_1.zip"), ("Octubre", "octubre.zip"),
        ("Enero", "e25.xlsx"), ("Diciembre", "d25.xlsx")]) + '<a href="https://otro.sitio/x.zip">Noviembre</a>'
    assert m.descubrir(html) == [base + "octubre.zip", base + "agosto_1.zip", base + "junio.zip", base + "e26.xlsx"]


def test_completa_con_los_meses_que_la_api_no_tiene():
    fuente = {"filas": m.parsear(_xlsx())}
    api = [["2026-09-01", 1427640.0], ["2026-08-01", 1990321.8], ["2026-07-01", 2960332.7]]
    filas = m.completar(api, RES, 3, fuente)
    assert filas == [["2026-10-01", pytest.approx(1931156.3)], ["2026-09-01", 1427640.0], ["2026-08-01", 1990321.8]]


def test_si_no_coinciden_no_se_cose_la_serie():
    fuente = {"filas": m.parsear(_xlsx(resultado=(1990321.8, 9.0, 1931156.3)))}
    api = [["2026-09-01", 1427640.0]]
    with pytest.raises(ValueError):
        m.completar(api, RES, 5, fuente)
    # y el colector sigue con la API
    m.planilla.cache_clear()
    orig = m.completar
    try:
        m.completar = lambda *a, **k: (_ for _ in ()).throw(ValueError("no coinciden"))
        assert m.con_planilla(RES, api, 5) == api
    finally:
        m.completar = orig


def test_las_series_que_no_son_del_imig_no_se_tocan():
    api = [["2026-09-01", 1.0]]
    assert m.con_planilla("otra_serie", api, 5) is api
    assert set(m.SERIES) == {RES, SAL, "452.2_OTROS_GASTNTO_0_T_27_55"}


def test_un_mes_nulo_de_la_api_no_queda_duplicado():
    """Codex: octubre nulo en la API y la planilla con octubre → una sola fila."""
    fuente = {"filas": m.parsear(_xlsx())}
    api = [["2026-10-01", None], ["2026-09-01", 1427640.0], ["2026-08-01", 1990321.8]]
    filas = m.completar(api, RES, 3, fuente)
    assert [f[0] for f in filas] == ["2026-10-01", "2026-09-01", "2026-08-01"]
    assert filas[0][1] == pytest.approx(1931156.3)
