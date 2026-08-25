# -*- coding: utf-8 -*-
"""El deflactor de las transferencias federales (ADR-0239).

Un flujo anual no se deflacta con un solo número. Las transferencias se
devengan mes a mes —con estacionalidad propia: mayo y diciembre pesan mucho más
que febrero— así que el deflactor que corresponde está ponderado por el flujo y
no por el calendario. Dividir el cociente de dos sumas nominales por el IPC
promedio del año publicó **+0,8% real para 2025** donde IARAF informó +1,6% y
Politikon +1,7%.

Los tests corren contra `tests/fixtures/ron_transferencias_2024_2025.json`: los
24 flujos mensuales reales y el índice IPC de cada mes, congelados el
25-ago-2026.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica

FIXTURE = Path(__file__).parent / "fixtures" / "ron_transferencias_2024_2025.json"
MESES = [f"{y}-{k:02d}" for y in (2024, 2025) for k in range(1, 13)]


@pytest.fixture(scope="module")
def datos():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _por_anio(datos, y):
    return [f"{y}-{k:02d}" for k in range(1, 13)]


def _real_mes_a_mes(datos):
    ron, ipc = datos["ron_mensual"], datos["ipc_indice"]
    a = sum(ron[m] / ipc[m] for m in _por_anio(datos, 2025))
    b = sum(ron[m] / ipc[m] for m in _por_anio(datos, 2024))
    return (a / b - 1) * 100.0


def _real_ipc_promedio(datos):
    """El método anterior, reproducido acá para poder compararlo."""
    ron, ipc = datos["ron_mensual"], datos["ipc_indice"]
    nom = sum(ron[m] for m in _por_anio(datos, 2025)) / sum(ron[m] for m in _por_anio(datos, 2024)) - 1
    p25 = sum(ipc[m] for m in _por_anio(datos, 2025)) / 12
    p24 = sum(ipc[m] for m in _por_anio(datos, 2024)) / 12
    return ((1 + nom) / (p25 / p24) - 1) * 100.0


def test_el_fixture_esta_completo(datos):
    assert sorted(datos["ron_mensual"]) == MESES
    assert all(m in datos["ipc_indice"] for m in MESES)


def test_deflactar_mes_a_mes_reproduce_a_los_dos_benchmarks_externos(datos):
    """No es que dé "parecido": da el mismo número que IARAF, al decimal.

    Dos organismos que no comparten método con este repo llegan a +1,6 y +1,7.
    Que la reconstrucción propia caiga entre los dos es la única forma de saber
    que el deflactor es el correcto y no otro que también parece razonable."""
    real = _real_mes_a_mes(datos)
    iaraf = datos["_benchmarks_externos"]["IARAF"]
    politikon = datos["_benchmarks_externos"]["Politikon"]
    assert abs(real - iaraf) < 0.1, f"{real:.2f}% contra IARAF {iaraf}%"
    assert min(iaraf, politikon) - 0.15 <= real <= max(iaraf, politikon) + 0.15


def test_el_valor_publicado_no_puede_volver(datos):
    """+0,8% era el cociente de sumas nominales sobre un IPC promedio único.

    El test comprueba las dos mitades: que el método viejo efectivamente daba
    ese número —o sea que el diagnóstico de la auditoría era correcto— y que el
    método nuevo no puede darlo."""
    erroneo = datos["_benchmarks_externos"]["publicado_erroneo"]
    assert abs(_real_ipc_promedio(datos) - erroneo) < 0.1, (
        "el método anterior ya no reproduce el valor que se publicó; "
        "si eso cambió, el diagnóstico de la auditoría hay que rehacerlo"
    )
    assert abs(_real_mes_a_mes(datos) - erroneo) > 0.5


def test_el_deflactor_correcto_es_menor_que_el_promedio_del_calendario(datos):
    """La razón por la que el promedio simple subdeflacta.

    El IPC promedio del año le da a cada mes el mismo peso; el flujo real no se
    reparte así. Con la inflación en baja y las transferencias cargadas hacia el
    segundo semestre —meses ya más baratos—, el deflactor ponderado por flujo
    queda por debajo, y la variación real por encima."""
    ron, ipc = datos["ron_mensual"], datos["ipc_indice"]
    nom = sum(ron[m] for m in _por_anio(datos, 2025)) / sum(ron[m] for m in _por_anio(datos, 2024)) - 1
    ponderado = (1 + nom) / (1 + _real_mes_a_mes(datos) / 100) - 1
    calendario = (sum(ipc[m] for m in _por_anio(datos, 2025)) /
                  sum(ipc[m] for m in _por_anio(datos, 2024))) - 1
    assert ponderado < calendario
    assert abs(ponderado * 100 - 40.8) < 0.15
    assert abs(calendario * 100 - 41.9) < 0.15


def test_la_variacion_nominal_no_se_toca(datos):
    """La auditoría verificó que el nominal (+43,1%) ya era correcto.

    Sirve de control: si el nominal se moviera, el problema no sería el
    deflactor sino el universo, que es otra corrección."""
    ron = datos["ron_mensual"]
    nom = (sum(ron[m] for m in _por_anio(datos, 2025)) /
           sum(ron[m] for m in _por_anio(datos, 2024)) - 1) * 100
    assert abs(nom - 43.1) < 0.1


# ── Universo y unidades del cuadro ───────────────────────────────────────────

def _cuadro(total_hdr, filas_datos, consenso_hdr=None):
    """Un cuadro mínimo con la forma del de Hacienda: encabezado partido en
    varias filas, dos columnas «Sub-total» antes del total, y la fila de
    subtotal de provincias repitiendo el rótulo del encabezado."""
    ancho = 5
    hdr1 = ["", "C.F.I.", "Sub-", "", ""]
    hdr2 = ["Provincias", "Neta De", "total", total_hdr, consenso_hdr or ""]
    return [hdr1, hdr2] + filas_datos


def test_el_total_se_ubica_por_encabezado_y_no_por_posicion():
    """El cuadro fue ganando columnas: una posición fija se corre sin avisar."""
    filas = _cuadro("Total Recursos Origen Nacional (1)",
                    [["Buenos Aires", 10.0, 10.0, 10.0, 0.0],
                     ["Provincias", 10.0, 10.0, 10.0, 1.0],
                     ["C.A.B.A", 2.0, 2.0, 2.0, 0.0],
                     ["Fdo.Compensador", 0.0, 0.0, None, 0.0],
                     ["Tesoro Nacional (*)", 90.0, 90.0, 90.0, -1.0],
                     ["Total (**)", 102.0, 102.0, 102.0, 0.0]],
                    consenso_hdr="Compensación Consenso Fiscal")
    total, consenso = politica._columnas_ron(filas)
    assert (total, consenso) == (3, 4)


def test_no_se_confunde_el_total_con_un_subtotal():
    """Hasta 2017 la columna se llamaba sólo «T O T A L» y hay dos «Sub-total»
    antes. Quedarse con uno de ellos dejaría afuera media planilla."""
    filas = _cuadro("T O T A L", [["Provincias", 1.0, 1.0, 1.0, 0.0]])
    total, _ = politica._columnas_ron(filas)
    assert total == 3


def test_solo_suman_las_filas_que_son_transferencias():
    """Tesoro Nacional, Seguridad Social y Fondo A.T.N. no salen de la Nación
    (ADR-0066), y el total del cuadro los incluye. Sumar la fila «Total» daría
    el universo equivocado."""
    filas = _cuadro("Total Recursos Origen Nacional",
                    [["P R O V I N C I A S", None, None, None, None],
                     ["Buenos Aires", 10.0, 10.0, 10.0, 0.0],
                     ["P R O V I N C I A S", 10.0, 10.0, 10.0, 1.0],
                     ["C.A.B.A", 2.0, 2.0, 2.0, 0.0],
                     ["Fdo.Compensador", 0.0, 0.0, None, None],
                     ["Tesoro Nacional (*)", 90.0, 90.0, 90.0, -1.0],
                     ["Seguridad Social", 5.0, 5.0, 5.0, 0.0],
                     ["Fondo A.T.N.", 3.0, 3.0, 3.0, 0.0],
                     ["Total (**)", 110.0, 110.0, 110.0, 0.0]],
                    consenso_hdr="Compensación Consenso Fiscal")
    # provincias 10 + consenso 1 + caba 2 = 13; ni 110 ni 98
    assert politica._total_jurisdicciones(filas) == 13.0


def test_el_rotulo_espaciado_de_las_planillas_viejas_cuenta_igual():
    """«P R O V I N C I A S» y «Provincias» son la misma fila."""
    assert politica._rotulo_ron("P R O V I N C I A S") == "provincias"
    assert politica._rotulo_ron("FDO.COMPENSADOR") == "fdo.compensador"


def test_sin_la_fila_de_provincias_el_cuadro_se_rechaza():
    """Si el subtotal desapareciera, sumar sólo CABA daría un número plausible
    y chiquito. Mejor que falle."""
    filas = _cuadro("Total Recursos Origen Nacional",
                    [["C.A.B.A", 2.0, 2.0, 2.0, 0.0]])
    with pytest.raises(ValueError):
        politica._total_jurisdicciones(filas)


def test_el_cambio_de_unidad_entre_2022_y_2023_se_detecta(datos):
    """Las planillas pasaron de miles a millones de pesos y no lo declaran.

    Sin ancla contra el CSV anual, 2023 daba **−99,9% real**: un salto de tres
    órdenes de magnitud leído como derrumbe. El factor lleva la hoja mensual a
    la unidad del CSV, así que para 2018 —hoja en miles, CSV en millones— es
    0,001, y de 2023 en adelante es 1."""
    assert politica._factor_unidad(1_073_806_353.0, 1_076_749.0) == 0.001
    assert politica._factor_unidad(42_133_458.0, 42_133_458.0) == 1.0


def test_un_desvio_que_no_es_de_unidad_hace_fallar(datos):
    """Un residuo grande no es un cambio de unidad: es el cuadro cambiando de
    forma. Publicar una variación real armada sobre dos universos distintos es
    peor que no publicarla."""
    with pytest.raises(ValueError):
        politica._factor_unidad(30_000_000.0, 42_133_458.0)


def test_la_reconciliacion_con_el_csv_anual_es_exacta(datos):
    """Las hojas mensuales y el CSV anual tienen que describir el mismo
    universo. Es lo que permite usar uno como ancla de unidad del otro."""
    for y in (2024, 2025):
        suma = sum(datos["ron_mensual"][m] for m in _por_anio(datos, y))
        csv_anual = datos["ron_total_anual_csv"][str(y)]
        assert abs(suma / csv_anual - 1) < 0.001, f"{y}: {suma:,.0f} vs {csv_anual:,.0f}"


# ── El colector, no la aritmética ────────────────────────────────────────────
# Los tests de arriba prueban que deflactar mes a mes es lo correcto. Estos
# prueban que es lo que el colector HACE: sin ellos, alguien podría volver al
# IPC promedio y toda la sección anterior seguiría en verde.

@pytest.fixture
def sin_red(datos, monkeypatch):
    """Enchufa el fixture donde el colector iría a la red."""
    monkeypatch.setattr(politica, "_ron_mensual", lambda desde=2016: dict(datos["ron_mensual"]))
    monkeypatch.setattr(politica, "_ipc_indice_mensual", lambda: dict(datos["ipc_indice"]))
    monkeypatch.setattr(politica, "_ron_total_anual_csv",
                        lambda: {int(k): v for k, v in datos["ron_total_anual_csv"].items()})
    return datos


def test_el_colector_publica_el_valor_deflactado_mes_a_mes(sin_red):
    por_anio = politica._iaf_real_por_anio()
    assert 2025 in por_anio, "2025 tiene los doce meses; tiene que estar"
    var_real, var_nom, deflactor, _, _ = por_anio[2025]
    assert abs(var_real * 100 - 1.64) < 0.05
    assert abs(var_nom * 100 - 43.08) < 0.05
    assert abs(deflactor * 100 - 40.78) < 0.05
    assert abs(var_real * 100 - 0.8) > 0.5, "el colector volvió al IPC promedio"


def test_la_card_dice_el_mismo_numero_que_la_serie(sin_red):
    """Card y serie salen de la misma función, y el test lo comprueba en vez de
    confiar en que sí. Es el desacople que ya rompió otras cards."""
    import descargar_series
    card = politica.fetch_iaf_transferencias()
    serie = dict(descargar_series.fetch_iaf_serie())
    assert card["valor"] == serie["2025-12-01"] == 1.6
    assert card["periodo"] == "2025 vs 2024"
    assert card["fecha_dato"] == "2025-12-31"


def test_un_ano_incompleto_no_entra(sin_red, datos, monkeypatch):
    """Nueve meses contra doce no es una variación interanual.

    Es el modo de falla del año en curso: la planilla publica los meses que van
    y compararlos contra un año cerrado daría una caída enorme e inventada."""
    parcial = dict(datos["ron_mensual"])
    parcial.update({f"2026-{k:02d}": 6_000_000.0 for k in range(1, 8)})
    monkeypatch.setattr(politica, "_ron_mensual", lambda desde=2016: parcial)
    monkeypatch.setattr(politica, "_ron_total_anual_csv",
                        lambda: {**{int(k): v for k, v in datos["ron_total_anual_csv"].items()},
                                 2026: 42_000_000.0})
    assert 2026 not in politica._iaf_real_por_anio()


def test_la_fuente_declara_como_se_deflacto(sin_red):
    """El rótulo de la fuente decía «(dic-dic)» mucho después de que el
    deflactor dejara de ser dic-dic. Un metadato que describe el método
    anterior es exactamente el error que la auditoría vino a buscar."""
    card = politica.fetch_iaf_transferencias()
    assert "mes a mes" in card["fuente"]
    assert "dic-dic" not in card["fuente"]
    assert "promedio" not in card["fuente"]
