import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
import xlrd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica
import publicar


def filas():
    meses = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
    out = []
    for n in range(12):
        anio_fin, mes_fin = 2020 + (n + 2) // 12, (n + 2) % 12
        out.append([f"{meses[n]} 2020 - {meses[mes_fin]} de {anio_fin}",
                    20, 70, 10, "", 15, 70, 15])
    return out


def instalar(monkeypatch, f):
    ws = SimpleNamespace(nrows=len(f), cell=lambda i,j:SimpleNamespace(value=f[i][j]))
    monkeypatch.setattr(xlrd, "open_workbook", lambda **kw:SimpleNamespace(sheet_by_name=lambda n:ws))
    monkeypatch.setattr(politica, "_isac_descargar", lambda:b"original")


def test_usa_inicio_del_horizonte_y_admite_de_antes_del_anio(monkeypatch):
    instalar(monkeypatch, filas())
    assert politica.brecha_obra_publica_serie() == [["2020-12-01", -10.0]]
    card=politica.fetch_brecha_obra_publica()
    assert card["fecha_dato"] == "2020-12-01"
    assert card["periodo_expectativas"] == "2020-12 a 2021-02"
    assert card["referencia_temporal"] == "inicio del horizonte de expectativas"


@pytest.mark.parametrize("defecto", ["hueco", "duplicado", "porcentaje", "horizonte", "nan", "futuro"])
def test_no_convierte_un_calendario_o_valores_invalidos_en_promedio(monkeypatch, defecto):
    f=filas()
    if defecto=="hueco":f.pop(4)
    if defecto=="duplicado":f.append(f[0])
    if defecto=="porcentaje":f[0][1]=101
    if defecto=="nan":f[0][1]=float("nan")
    if defecto=="horizonte":f[0][0]="enero 2020 - abril 2020"
    if defecto=="futuro":f[0][0]="enero 2099 - marzo 2099"
    instalar(monkeypatch,f)
    with pytest.raises(ValueError):politica.brecha_obra_publica_serie()


@pytest.mark.parametrize("disponible", [True, False])
def test_contraste_publico_usa_la_corrida_y_no_numeros_historicos(monkeypatch, disponible):
    meses={f"2025-{n:02d}":n for n in range(1,13)}
    val={"serie_itcp":meses,"epu_argentina_mensual":meses,
         "correlaciones_itcp":{"niveles (ITCP vs EPU Argentina)":{"r":-.2,"n":12},
                                "primeras diferencias (ITCP vs EPU)":{"r":-.1,"n":11}}}
    if disponible:
        val["correlaciones_brecha_obra_publica"]={
            "niveles (brecha obra pública vs Construya var. i.a., ambas 12m)":{"r":.12},
            "primeras diferencias (brecha vs Construya)":{"r":-.34}}
    monkeypatch.setattr(publicar,"_cargar_validacion",lambda:val)
    bloque={"dimensiones":{}}
    publicar._validacion_itcp(bloque)
    texto=bloque["validacion"]["conclusion"]
    assert "0,79" not in texto and "0,47" not in texto
    if disponible:
        assert "0,12" in texto and "0,34" in texto
        assert "no demuestra anticipación ni causalidad" in texto
    else:
        assert "Construya no está disponible" in texto
