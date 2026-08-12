"""Tests del desequilibrio monetario (sin red).

Pinean lo que la ficha de Diego define y lo que la implementación decidió por
encima de ella (ADR-0192): las cuatro esquinas de la matriz, la posición por
percentiles con saturación, el parseo del concepto 03 con el sector público
afuera, y que la serie no arranque antes de la apertura del cepo.
"""
import io
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import desequilibrio_monetario as dm
import itcm


# ── La matriz ────────────────────────────────────────────────────────────────

def test_las_cuatro_esquinas_reproducen_la_matriz_de_la_ficha():
    # (posicion_a, posicion_b) -> tensión declarada en la ficha
    assert dm.tension_matriz(1.0, 0.0) == 0.0     # verde: confianza real
    assert dm.tension_matriz(0.0, 0.0) == 40.0    # amarillo: contenida en el sistema
    assert dm.tension_matriz(1.0, 1.0) == 77.5    # naranja/rojo: fuga oculta
    assert dm.tension_matriz(0.0, 1.0) == 90.0    # rojo: deterioro dentro y fuera


def test_la_matriz_no_es_simetrica_y_la_fuga_pesa_mas_que_el_stock():
    """La asimetría no es una ponderación inventada: sale de las celdas de la
    ficha. Degradar el stock cuesta 40 puntos; degradar la fuga, 77,5."""
    desde_verde = dm.tension_matriz(1.0, 0.0)
    assert dm.tension_matriz(0.0, 0.0) - desde_verde == 40.0
    assert dm.tension_matriz(1.0, 1.0) - desde_verde == 77.5


def test_el_centro_de_la_matriz_es_el_promedio_de_las_cuatro_esquinas():
    esquinas = (0.0, 40.0, 77.5, 90.0)
    assert dm.tension_matriz(0.5, 0.5) == pytest.approx(sum(esquinas) / 4)


def test_stock_sano_no_alcanza_si_la_fuga_es_fuerte():
    """El caso que el indicador existe para exponer: A en su mejor valor
    histórico y B en el peor no puede leerse como confianza."""
    assert dm.tension_matriz(1.0, 1.0) > dm.tension_matriz(0.0, 0.0)


# ── Posición por percentiles ─────────────────────────────────────────────────

def test_posicion_devuelve_exactamente_los_percentiles_declarados():
    for corte, esperada in zip(dm.CORTES_A, dm.POSICIONES):
        assert dm.posicion(corte, dm.CORTES_A) == pytest.approx(esperada)
    for corte, esperada in zip(dm.CORTES_B, dm.POSICIONES):
        assert dm.posicion(corte, dm.CORTES_B) == pytest.approx(esperada)


def test_posicion_satura_fuera_de_la_ventana_de_calibracion():
    assert dm.posicion(-999, dm.CORTES_A) == 0.0
    assert dm.posicion(999, dm.CORTES_A) == 1.0
    # Una venta neta (B negativo) no genera posición negativa: queda en el piso.
    assert dm.posicion(-500, dm.CORTES_B) == 0.0


def test_posicion_interpola_lineal_dentro_de_un_tramo():
    medio = (dm.CORTES_A[1] + dm.CORTES_A[2]) / 2
    assert dm.posicion(medio, dm.CORTES_A) == pytest.approx(0.375)


def test_los_cortes_estan_ordenados_y_congelados():
    """Si alguien recalibra, que sea deliberado: estos números fijan el puntaje
    de meses ya publicados."""
    assert dm.CORTES_A == (31.62, 34.48, 38.27, 44.34, 49.96)
    assert dm.CORTES_B == (1122.3, 1954.2, 2363.3, 3643.7, 6545.1)
    for cortes in (dm.CORTES_A, dm.CORTES_B):
        assert list(cortes) == sorted(cortes)
        assert len(cortes) == len(dm.POSICIONES)


# ── Enganche con el motor del ITCM ───────────────────────────────────────────

def test_la_escala_del_itcm_es_la_inversion_exacta_de_la_tension():
    """Las cuatro esquinas caen sobre puntaje = 100 − tensión. Si dejaran de
    caer, habría dos escalas y una podría desincronizarse (ADR-0082)."""
    for tension in (0.0, 40.0, 77.5, 90.0, 100.0):
        assert itcm.ESCALA_ITCM.puntaje(tension, "desequilibrio_monetario") == (
            pytest.approx(100.0 - tension)
        )


def test_mayor_tension_nunca_sube_el_puntaje():
    previos = [itcm.ESCALA_ITCM.puntaje(t, "desequilibrio_monetario")
               for t in range(0, 101, 5)]
    assert previos == sorted(previos, reverse=True)


# ── Parseo del anexo cambiario ───────────────────────────────────────────────

def _anexo(filas):
    """Planilla mínima con la forma de la hoja tabular del BCRA."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = dm.HOJA_MERCADO_CAMBIOS
    ws.append(["Anexo", "Mes", "Sector", "Monto", "A", "B", "C", "D"])
    for mes, sector, monto, concepto in filas:
        ws.append(["x", mes, sector, monto, "", concepto, "", ""])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


CONCEPTO = dm.CONCEPTO_SIN_FINES_ESPECIFICOS


def test_parseo_suma_sectores_privados_e_invierte_el_signo():
    contenido = _anexo([
        ("2026-06", "Personas Humanas", -2_000_000_000.0, CONCEPTO),
        ("2026-06", "Comercio", -500_000_000.0, CONCEPTO),
    ])
    assert dm.parsear_fuga_spnf(contenido) == {"2026-06": 2500.0}


def test_parseo_excluye_al_sector_publico():
    """El concepto 03 trae al sector público entre sus sectores y el componente
    es del sector privado NO financiero."""
    contenido = _anexo([
        ("2026-06", "Personas Humanas", -2_000_000_000.0, CONCEPTO),
        ("2026-06", "Sector Público", -900_000_000.0, CONCEPTO),
    ])
    assert dm.parsear_fuga_spnf(contenido) == {"2026-06": 2000.0}


def test_parseo_ignora_otros_conceptos():
    contenido = _anexo([
        ("2026-06", "Comercio", -2_000_000_000.0, CONCEPTO),
        ("2026-06", "Comercio", -9_000_000_000.0, "01- Bienes"),
    ])
    assert dm.parsear_fuga_spnf(contenido) == {"2026-06": 2000.0}


def test_parseo_falla_si_el_anexo_cambia_de_columnas():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = dm.HOJA_MERCADO_CAMBIOS
    ws.append(["Anexo", "Periodo", "Rubro", "Importe"])
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(ValueError, match="Faltan columnas"):
        dm.parsear_fuga_spnf(buf.getvalue())


def test_parseo_falla_si_no_hay_filas_del_concepto():
    contenido = _anexo([("2026-06", "Comercio", -1.0, "01- Bienes")])
    with pytest.raises(ValueError, match="concepto 03"):
        dm.parsear_fuga_spnf(contenido)


# ── Construcción de la serie ─────────────────────────────────────────────────

BCRA_FIXTURE = {
    "2025-03": dict(m2=50_000.0, circ=20_000.0, dep=90_000.0, usd=30_000.0, fuga=-269.0),
    "2025-04": dict(m2=50_000.0, circ=20_000.0, dep=90_000.0, usd=30_000.0, fuga=2_021.0),
    "2026-06": dict(m2=60_000.0, circ=25_000.0, dep=100_000.0, usd=40_000.0, fuga=2_067.0),
}


def _insumos(meses=None, faltante=None):
    meses = meses or list(BCRA_FIXTURE)
    campos = {"m2": {}, "circ": {}, "dep": {}, "usd": {}, "fuga": {}}
    for mes in meses:
        for k, v in BCRA_FIXTURE[mes].items():
            if faltante and mes == faltante[0] and k == faltante[1]:
                continue
            campos[k][mes] = v
    return dict(m2_privado=campos["m2"], circulante=campos["circ"],
                dep_priv_ars=campos["dep"], dep_priv_usd=campos["usd"],
                fuga_spnf=campos["fuga"])


def test_la_serie_no_arranca_antes_de_la_apertura_del_cepo():
    """Marzo de 2025 tiene todos los insumos y aun así no entra: con cepo el
    flujo daba ~0 por falta de acceso, no por confianza, y la matriz lo leería
    como verde (ADR-0192)."""
    serie = dm.construir_serie(**_insumos())
    assert [f["mes"] for f in serie] == ["2025-04", "2026-06"]
    assert dm.MES_INICIO == "2025-04"


def test_un_mes_sin_todos_los_insumos_no_se_calcula():
    serie = dm.construir_serie(**_insumos(faltante=("2026-06", "usd")))
    assert [f["mes"] for f in serie] == ["2025-04"]


def test_cada_fila_trae_los_dos_componentes_y_su_celda():
    fila = dm.construir_serie(**_insumos())[-1]
    assert fila["componente_a"] == pytest.approx(60_000 / 165_000 * 100, abs=0.01)
    assert fila["componente_b"] == 2067.0
    assert fila["puntaje_itcm"] == pytest.approx(100 - fila["tension"], abs=0.05)
    assert fila["celda"] in {"verde", "amarillo", "naranja_rojo", "rojo"}


def test_obtener_serie_exige_el_fetcher_del_bcra():
    with pytest.raises(ValueError, match="fetch_bcra_fin_mes"):
        dm.obtener_serie()


def test_obtener_serie_falla_si_una_fuente_viene_vacia():
    def sin_datos(var_id, meses):
        return {}

    with pytest.raises(ValueError, match="sin datos"):
        dm.obtener_serie(fetch_bcra_fin_mes=sin_datos, fetch_fuga=lambda: {"2026-06": 1.0})
