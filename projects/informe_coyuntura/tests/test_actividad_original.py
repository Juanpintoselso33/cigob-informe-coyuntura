from datetime import date
from types import SimpleNamespace
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/vida_cotidiana"))
import indec_actividad as actividad


def filas():
    f = [["Cuadro 1. IPI manufacturero nivel general. Serie original, desestacionalizada y tendencia-ciclo, base 2004=100", "", "", "", "", ""],
         ["", "", "", "Serie original", "", "Serie desestacionalizada (1)"]]
    for i in range(13):
        f.append(["", 2024 + i // 12 if i % 12 == 0 else "",
                  list(actividad.MESES)[i % 12], 100 + i, "", 200 + i])
    return f


def libro(monkeypatch, f):
    hoja = SimpleNamespace(name="Cuadro 1", nrows=len(f), ncols=6,
                           cell_value=lambda i, j: f[i][j])
    monkeypatch.setattr(actividad.xlrd, "open_workbook",
                        lambda **kw: SimpleNamespace(sheets=lambda: [hoja]))


def test_separa_original_de_desestacionalizado_y_conserva_revision(monkeypatch):
    f = filas(); f[2][3] = 101.23456789
    libro(monkeypatch, f)
    r = actividad.parsear(b"", "ipi", date(2025, 2, 1))
    assert r["original"]["2024-01"] == 101.23456789
    assert r["desestacionalizada"]["2024-01"] == 200
    assert max(r["original"]) == "2025-01"


@pytest.mark.parametrize("fila,columna,valor", [
    (3, 2, "enero"), (3, 2, "marzo"), (3, 2, "febrero revisado"),
    (2, 1, ""), (2, 3, 0), (2, 3, float("nan")), (2, 5, ""),
    (0, 0, "Cuadro 1. IPI manufacturero por sectores base 2004=100"),
])
def test_rechaza_huecos_duplicados_identidad_o_niveles_invalidos(monkeypatch, fila, columna, valor):
    f = filas(); f[fila][columna] = valor; libro(monkeypatch, f)
    with pytest.raises(ValueError):
        actividad.parsear(b"", "ipi", date(2025, 2, 1))


def test_rechaza_mes_no_cerrado(monkeypatch):
    libro(monkeypatch, filas())
    with pytest.raises(ValueError, match="no cerrado"):
        actividad.parsear(b"", "ipi", date(2025, 1, 31))


def test_descubre_anio_vigente_sin_seguir_espejos_o_archivos_distintos():
    html = """<a href='/ftp/cuadros/economia/sh_ipi_manufacturero_2025.xls'>viejo</a>
    <a href='/ftp/cuadros/economia/sh_ipi_manufacturero_2026.xls'>vigente</a>
    <a href='https://otro.test/ftp/cuadros/economia/sh_ipi_manufacturero_2027.xls'>otro</a>
    <a href='/ftp/cuadros/economia/sh_ipi_manufacturero_2027.xls'>futuro</a>
    <a href='/ftp/cuadros/economia/sh_isac_2026.xls'>otra operación</a>"""
    assert actividad.descubrir(html, "ipi", date(2026, 9, 8)).endswith("manufacturero_2026.xls")


def test_tarjeta_e_historia_comparten_ruta_original(monkeypatch):
    import macro
    import descargar_series
    import importlib.util
    raiz = Path(__file__).resolve().parents[1] / "scripts/vida_cotidiana"
    spec = importlib.util.spec_from_file_location("config_social_prueba", raiz / "config.py")
    configuracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(configuracion)
    monkeypatch.setitem(sys.modules, "config", configuracion)
    spec = importlib.util.spec_from_file_location("actividad_collector_prueba", raiz / "collectors/indec_series.py")
    indec_series = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indec_series)
    monkeypatch.setattr(actividad, "niveles", lambda tipo: {
        "original": {"2026-06": 123.456, "2026-07": 118.789},
        "desestacionalizada": {"2026-06": 146.789, "2026-07": 140.123},
        "fuente_url": "https://www.indec.gob.ar/planilla.xls",
        "obtenido_en": "2026-09-08T16:20:00-03:00"})
    for sid in actividad.SERIES:
        esperado = actividad.filas(sid, 2)
        assert macro._indec_serie(sid, 2) == esperado
        assert descargar_series.fetch_indec(sid, 2) == esperado
        assert indec_series._get_serie(sid, 2) == esperado
        tarjeta = indec_series._var_mensual(sid)
        assert tarjeta["valor"] == esperado[0][1]
        assert tarjeta["fecha"] == esperado[0][0]
        assert tarjeta["obtenido_en"] == "2026-09-08T16:20:00-03:00"


def test_la_hora_de_actualizacion_parcial_no_se_reemplaza_por_la_del_crudo():
    import publicar
    raw = {"metadata": {"timestamp": "2026-09-08T03:00:00"},
           "indec": {"isac": {"valor": 140.163, "fecha": "2026-07-01",
                              "obtenido_en": "2026-09-08T16:20:00-03:00"}}}
    card = publicar._sellar_vida(publicar.build_vida(raw), raw)["despacho_cemento"]
    assert card["obtenido_en"] == "2026-09-08T16:20:00-03:00"
