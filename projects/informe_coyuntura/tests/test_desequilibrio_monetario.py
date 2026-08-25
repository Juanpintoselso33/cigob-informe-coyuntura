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

def test_las_cuatro_esquinas():
    # (posicion_a, posicion_b) -> tensión
    assert dm.tension_matriz(1.0, 0.0) == 0.0      # nada degradado
    assert dm.tension_matriz(0.0, 0.0) == 58.75    # se degradó A sola
    assert dm.tension_matriz(1.0, 1.0) == 58.75    # se degradó B sola
    assert dm.tension_matriz(0.0, 1.0) == 90.0     # las dos


def test_la_matriz_es_simetrica_porque_el_orden_no_se_pudo_determinar(monkeypatch):
    """ADR-0257. La asimetría de la ficha (40 contra 77,5) se apoyaba en la
    tesis de la fuga fuera del sistema, que ADR-0252 invalidó, y el dato no
    pudo reponerla: contra tres referencias externas cada componente sale con
    el signo invertido en al menos una.

    El test no pide «45»: pide que las dos esquinas cruzadas valgan LO MISMO.
    Un número distinto es una recalibración legítima; un orden entre ellas es
    volver a afirmar lo que no se puede sostener."""
    assert dm.tension_matriz(0.0, 0.0) == dm.tension_matriz(1.0, 1.0)


def test_cruzar_sigue_sin_ser_promediar():
    """La guarda que atrapó una sobrecorrección real, y por eso está escrita
    contra el 45 y no contra el 58,75.

    Al quitar el orden entre las dos esquinas cruzadas, la tentación es
    igualarlas en el punto medio de las dos puras (45). Ahí la bilineal se
    vuelve `45·d_A + 45·B`, que es exactamente el PROMEDIO de las dos
    degradaciones — y no promediar es la premisa fundacional del indicador
    (ADR-0192: «el resultado sale de CRUZARLOS, no de promediarlos»), que
    ADR-0252 no puso en duda. Un componente en su mejor valor no puede tapar
    al otro en el peor."""
    promedio = (dm.TENSION_A_ALTO_B_BAJO + dm.TENSION_A_BAJO_B_ALTO) / 2
    assert dm.tension_matriz(0.0, 0.0) > promedio
    assert dm.tension_matriz(1.0, 1.0) > promedio


def test_la_severidad_total_de_las_cruzadas_es_la_que_fijo_la_ficha():
    """Se redistribuye, no se recalibra: lo que ADR-0252 invalidó fue el orden
    entre las dos, no cuánta tensión valían juntas. Su suma también es lo único
    que fija el término de interacción de la bilineal, así que conservarla deja
    la forma de la matriz intacta."""
    assert dm.TENSION_A_BAJO_B_BAJO + dm.TENSION_A_ALTO_B_ALTO == pytest.approx(117.5)
    interaccion = (dm.TENSION_A_BAJO_B_ALTO - dm.TENSION_A_BAJO_B_BAJO
                   - dm.TENSION_A_ALTO_B_ALTO)
    assert interaccion == pytest.approx(-27.5)


def test_el_centro_de_la_matriz_es_el_promedio_de_las_cuatro_esquinas():
    esquinas = (dm.TENSION_A_ALTO_B_BAJO, dm.TENSION_A_BAJO_B_BAJO,
                dm.TENSION_A_ALTO_B_ALTO, dm.TENSION_A_BAJO_B_ALTO)
    assert dm.tension_matriz(0.5, 0.5) == pytest.approx(sum(esquinas) / 4)


def test_ningun_componente_sano_tapa_al_otro_degradado():
    """Lo que el indicador existe para exponer, y que la simetría no toca: que
    un componente esté en su mejor valor no puede leerse como confianza si el
    otro está en el peor. Las dos cruzadas están lejos del verde."""
    verde = dm.tension_matriz(1.0, 0.0)
    assert dm.tension_matriz(1.0, 1.0) - verde >= 50.0
    assert dm.tension_matriz(0.0, 0.0) - verde >= 50.0


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
    assert dm.CORTES_A == (30.6, 32.05, 32.83, 34.46, 37.65)
    assert dm.CORTES_B == (1122.3, 1954.2, 2363.3, 3643.7, 6545.1)
    for cortes in (dm.CORTES_A, dm.CORTES_B):
        assert list(cortes) == sorted(cortes)
        assert len(cortes) == len(dm.POSICIONES)


# ── Los dos componentes, el mismo régimen (ADR-0257) ────────────────────────

def test_los_dos_componentes_se_calibran_en_la_misma_ventana():
    """El defecto que ADR-0257 arregla, y que ninguna guarda podía ver.

    ADR-0192 fijó la ventana de B en la apertura del cepo con un argumento
    explícito —bajo cepo el flujo daba ~0 por falta de acceso, no por
    confianza— y calibró A contra 2021-2026, donde 51 de 68 meses son de cepo.
    El argumento vale igual para A: un ratio alto de pesos transaccionales bajo
    cepo es tenencia forzada, no confianza.

    El efecto no era cosmético. Las dos distribuciones casi no se tocan (el
    máximo del régimen abierto cae por debajo de la mediana del cepo), así que
    A quedaba clavada contra su piso y la matriz era casi unidimensional."""
    assert dm.VENTANA_A.split(" / ")[0] == dm.VENTANA_B.split(" / ")[0]
    assert dm.VENTANA_A.startswith(dm.MES_INICIO)


def test_los_cortes_de_a_son_de_regimen_abierto_y_no_de_la_era_del_cepo():
    """Contra los valores reales: bajo cepo el ratio corrió entre 33,1 y 50,0;
    en régimen abierto, entre 30,6 y 37,7. Unos cortes que lleguen cerca de 50
    son los viejos, vengan de donde vengan."""
    assert dm.CORTES_A[-1] < 40.0, "el techo de A es de la era del cepo"
    assert dm.CORTES_A[0] < 32.0


# ── Los cuadrantes nombran el diagnóstico, no la gravedad ───────────────────

def test_ningun_cuadrante_se_llama_por_un_color():
    """Con la matriz simétrica, «amarillo» y «naranja_rojo» puntúan lo mismo:
    un nombre de color afirmaría un orden que el número de al lado desmiente.
    El cuadrante dice QUÉ se degradó; la banda dice CUÁNTO."""
    colores = ("verde", "amarillo", "naranja", "rojo")
    for nombre in dm.CELDAS.values():
        assert not any(c in nombre for c in colores), nombre


def test_cada_combinacion_tiene_su_propio_cuadrante():
    """Aunque dos cuadrantes puntúen igual, siguen siendo diagnósticos
    distintos: cuál de los dos componentes se movió es la información que la
    tensión sola no puede dar."""
    assert len(set(dm.CELDAS.values())) == 4
    assert dm._celda(1.0, 0.0) == "sin_tension"
    assert dm._celda(0.0, 0.0) == "solo_liquidez"
    assert dm._celda(1.0, 1.0) == "solo_presion"
    assert dm._celda(0.0, 1.0) == "liquidez_y_presion"


def test_la_lectura_dice_contra_que_ventana_se_mide():
    """«Alta» y «baja» son posiciones dentro de la ventana, no niveles.

    Con la ventana vieja el adjetivo se leía contra 2021-2026; con la nueva se
    lee contra 17 meses, y el mismo 33,5% que ahora sale «alto» era de los más
    bajos de la serie larga. Si el texto no dice contra qué mide, la card
    afirma un nivel que no observó."""
    import publicar
    txt = publicar._macro_input_txt("desequilibrio_monetario", {
        "valor": 38.69, "componente_a": 33.49, "componente_b": 2067.4,
        "celda": "sin_tension"})
    assert "régimen abierto" in txt


# ── Enganche con el motor del ITCM ───────────────────────────────────────────

def test_la_escala_del_itcm_es_la_inversion_exacta_de_la_tension():
    """Las cuatro esquinas caen sobre puntaje = 100 − tensión. Si dejaran de
    caer, habría dos escalas y una podría desincronizarse (ADR-0082).

    La tolerancia es el redondeo a un decimal que aplica el motor, no holgura:
    58,75 de tensión da 41,25 de puntaje y se publica 41,2. Con las esquinas
    viejas (0 · 40 · 77,5 · 90) el redondeo no se notaba porque todas caían en
    un decimal exacto, y por eso el test venía sin tolerancia."""
    for tension in (0.0, 58.75, 90.0, 100.0):
        assert itcm.ESCALA_ITCM.puntaje(tension, "desequilibrio_monetario") == (
            pytest.approx(100.0 - tension, abs=0.05)
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
    assert fila["celda"] in set(dm.CELDAS.values())


def test_obtener_serie_exige_el_fetcher_del_bcra():
    with pytest.raises(ValueError, match="fetch_bcra_fin_mes"):
        dm.obtener_serie()


def test_obtener_serie_falla_si_una_fuente_viene_vacia():
    def sin_datos(var_id, meses):
        return {}

    with pytest.raises(ValueError, match="sin datos"):
        dm.obtener_serie(fetch_bcra_fin_mes=sin_datos, fetch_fuga=lambda: {"2026-06": 1.0})
