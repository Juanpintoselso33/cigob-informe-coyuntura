"""`transferencias_no_automaticas` mide lo que la Nación gira por decisión (ADR-0378).

Sin red: las filas de Presupuesto Abierto y el IPC son fixtures. Lo que se fija:
qué partidas entran y cuáles salen, que el mes en curso no cuente, que cada flujo
se deflacte por el IPC de SU mes, que se compare el nivel contra el total de 2023
(ADR-0397), que el peso en la dimensión sea el del indicador anterior y que
`iaf_transferencias` ya no puntúe.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itcp
import politica


def fila(mes, dev, principal=7, jur=88, prog=40, actividad="Universalizacion Jornada Extendida"):
    return {"impacto_presupuestario_mes": mes, "jurisdiccion_id": jur,
            "programa_id": prog, "actividad_desc": actividad,
            "principal_id": principal, "credito_devengado": dev}


# ── Qué entra y qué sale ────────────────────────────────────────────────────

def test_entran_atn_corrientes_y_capital():
    m = politica._transf_na_mensual_de_filas({2025: [
        fila(1, 100, 7, 25, 19, "Aportes del Tesoro Nacional (ATN)"),
        fila(1, 50, 7),
        fila(1, 30, 8, 50, 82, "Obras de agua"),
    ]})
    assert m["2025-01"] == {"atn": 100.0, "corrientes": 50.0, "capital": 30.0}


def test_el_atn_se_reconoce_aunque_cambie_de_jurisdiccion():
    for jur in (30, 25):
        m = politica._transf_na_mensual_de_filas({2024: [
            fila(3, 10, 7, jur, 19, "Aportes del Tesoro Nacional (ATN)")]})
        assert m["2024-03"]["atn"] == 10.0


@pytest.mark.parametrize("f", [
    fila(1, 999, 7, 91, 67, "Cumplimiento de Medida Cautelar CSJN 1864/2022"),
    fila(1, 999, 7, 91, 67, "Reglamentacion Ley N° 27.606"),
    fila(1, 999, 7, 70, 98, "Fondo Nacional de Incentivo Docente"),
    fila(1, 999, 7, 88, 99, "Transferencias a Cajas Previsionales Provinciales"),
    fila(1, 999, 7, 80, 99, "Funcionamiento Hospital Garrahan"),
])
def test_las_partidas_automaticas_quedan_afuera(f):
    m = politica._transf_na_mensual_de_filas({2025: [f, fila(1, 5, 7)]})
    assert m["2025-01"] == {"atn": 0.0, "corrientes": 5.0, "capital": 0.0}


def test_otros_incisos_y_principales_no_entran():
    m = politica._transf_na_mensual_de_filas({2025: [
        fila(1, 999, principal=1), fila(1, 999, principal=5), fila(1, 7, principal=7)]})
    assert sum(m["2025-01"].values()) == 7.0


def test_un_mes_sin_devengado_existe_en_cero():
    m = politica._transf_na_mensual_de_filas({2025: [fila(2, 4)]})
    assert m["2025-01"] == {"atn": 0.0, "corrientes": 0.0, "capital": 0.0}
    assert len(m) == 12


# ── Nivel contra 2023 y deflación (ADR-0397) ────────────────────────────────

def _mensual(montos):
    """{YYYY-MM: composición} para 2023-01…2024-12 con `montos[i]` corrientes."""
    meses = [f"{2023 + i // 12}-{i % 12 + 1:02d}" for i in range(24)]
    return {m: {"atn": 0.0, "corrientes": float(montos[i]), "capital": 0.0}
            for i, m in enumerate(meses)}


def test_la_primera_ventana_es_la_base_y_da_cero():
    mensual = _mensual([100] * 24)
    ipc = {m: 1.0 for m in mensual}
    v = politica._transf_na_nivel_vs_base(mensual, ipc)
    assert min(v) == "2023-12"
    assert v["2023-12"][0] == pytest.approx(0.0)


def test_flujo_plano_con_ipc_que_duplica_da_menos_cincuenta_real():
    mensual = _mensual([100] * 24)
    ipc = {m: 1.0 for m in list(mensual)[:12]}
    ipc.update({m: 2.0 for m in list(mensual)[12:]})
    v = politica._transf_na_nivel_vs_base(mensual, ipc)["2024-12"]
    assert v[0] == pytest.approx(-0.5)          # real contra 2023
    assert v[1] == pytest.approx(1200.0)        # 12 meses a precios de dic-2024
    assert v[2] == pytest.approx(2400.0)        # 2023 a precios de dic-2024
    assert v[3] == pytest.approx(1200.0)        # nominal: misma plata


def test_cada_flujo_se_deflacta_con_el_ipc_de_su_propio_mes():
    # Todo el giro de 2023 cae en el mes de IPC bajo; el de la ventana, en el alto.
    montos = [0] * 24
    montos[0], montos[23] = 100, 100
    mensual = _mensual(montos)
    ipc = {m: 1.0 for m in mensual}
    ipc["2024-12"] = 4.0
    v = politica._transf_na_nivel_vs_base(mensual, ipc)["2024-12"]
    assert v[0] == pytest.approx(0.25 - 1.0)    # 100/4 contra 100/1


def test_la_base_es_fija_y_no_corre_con_la_ventana():
    # La ventana a jun-2024 mezcla medio 2023 y medio 2024: se compara contra
    # todo 2023, no contra los 12 meses previos (que no existen en el fixture).
    mensual = _mensual([100] * 12 + [200] * 12)
    ipc = {m: 1.0 for m in mensual}
    v = politica._transf_na_nivel_vs_base(mensual, ipc)
    assert v["2024-06"][0] == pytest.approx(0.5)     # 1800 contra 1200
    assert v["2024-12"][0] == pytest.approx(1.0)     # 2400 contra 1200


def test_sin_la_base_completa_no_hay_puntos():
    mensual = _mensual([100] * 24)
    del mensual["2023-06"]
    ipc = {m: 1.0 for m in _mensual([1] * 24)}
    assert politica._transf_na_nivel_vs_base(mensual, ipc) == {}


def test_sin_ipc_del_ultimo_mes_la_ventana_termina_antes():
    mensual = _mensual([100] * 24)
    ipc = {m: 1.0 for m in mensual}
    del ipc["2024-12"]
    ventanas = politica._transf_na_nivel_vs_base(mensual, ipc)
    assert max(ventanas) == "2024-11"


# ── La card ─────────────────────────────────────────────────────────────────

class _Hoy(date):
    @classmethod
    def today(cls):
        return cls(2025, 1, 15)


def test_el_mes_en_curso_no_entra_y_la_card_declara_su_fecha(monkeypatch):
    politica._TRANSF_NA_MEMO.clear()
    filas = {2023: [fila(m, 100) for m in range(1, 13)],
             2024: [fila(m, 200, 7, 25, 19, "Aportes del Tesoro Nacional (ATN)") for m in range(1, 13)],
             2025: [fila(1, 9999)]}                       # enero 2025: en curso, parcial

    monkeypatch.setattr(politica.gestion, "_pa_token", lambda: "t")
    monkeypatch.setattr(politica.gestion, "_pa_credito",
                        lambda token, anio, filtros, columns=None: filas[anio])
    ipc = {f"{a}-{m:02d}": 1.0 for a in range(2023, 2026) for m in range(1, 13)}
    monkeypatch.setattr(politica, "_ipc_indice_mensual", lambda: ipc)
    monkeypatch.setattr(politica, "date", _Hoy)
    card = politica.fetch_transferencias_no_automaticas()
    politica._TRANSF_NA_MEMO.clear()
    assert card is not None
    assert card["fecha_dato"] == "2024-12-31"            # dic-2024, no ene-2025
    assert card["valor"] == pytest.approx(100.0)          # 2400 contra 1200 de 2023, IPC plano
    assert card["unidad"] == "% real frente a 2023"
    assert "Aportes del Tesoro Nacional" in card["detalle_txt"] and card["periodo"].endswith("frente a 2023")


def test_si_falla_la_fuente_devuelve_none(monkeypatch):
    politica._TRANSF_NA_MEMO.clear()
    monkeypatch.setattr(politica.gestion, "_pa_token", lambda: None)
    assert politica.fetch_transferencias_no_automaticas() is None


# ── El índice ───────────────────────────────────────────────────────────────

def test_reemplaza_a_iaf_con_el_mismo_peso():
    ind = itcp.DIMENSIONES_ITCP["alianzas_territoriales"]["indicadores"]
    assert ind["transferencias_no_automaticas"] == 0.40
    assert "iaf_transferencias" not in ind
    assert "iaf_transferencias" in itcp.INDICADORES_SUSPENDIDOS
    assert itcp.INDICADORES_SUSPENDIDOS["iaf_transferencias"]["adr"] == "0378"
    assert itcp.FAMILIAS_ITCP["transferencias_no_automaticas"] == "recursos"
    assert "iaf_transferencias" not in itcp.FAMILIAS_ITCP
    assert "iaf_transferencias" not in itcp.REZAGO_MESES_ITCP


def test_iaf_ya_no_puntua_y_la_nueva_si():
    base = {"alineamiento_senadores_prov": 70.0, "adhesion_reformas_provincial": 90.0}
    sin = itcp.calcular_itcp({**base, "iaf_transferencias": 50.0})
    con = itcp.calcular_itcp({**base, "transferencias_no_automaticas": 80.0})
    ind = lambda r: r["dimensiones"]["alianzas_territoriales"]["indicadores"]
    assert "iaf_transferencias" not in ind(sin)
    assert ind(con)["transferencias_no_automaticas"]["puntaje_aplicado"] == 100.0


def test_cortes_de_uno_y_dos_desvios_previos():
    # ADR-0397: desvío de 35,9 pp de la variación interanual de nov-2018 a
    # nov-2023 → ±36 (un desvío) y ±72 (dos).
    assert itcp.BANDAS_ITCP["transferencias_no_automaticas"] == [
        (72.0, itcp.INF, 100), (36.0, 72.0, 85), (-36.0, 36.0, 65),
        (-72.0, -36.0, 40), (-itcp.INF, -72.0, 10)]


@pytest.mark.parametrize("valor,puntaje", [
    (80.0, 100.0),     # más de dos desvíos por encima de 2023
    (0.0, 65.0),       # el nivel de 2023: un año normal
    (-82.1, 10.0),     # el nivel a sep-2026: 82 % por debajo de 2023
    (-85.0, 10.0),
])
def test_la_banda_puntua_el_nivel_contra_2023(valor, puntaje):
    r = itcp.calcular_itcp({"transferencias_no_automaticas": valor})
    d = r["dimensiones"]["alianzas_territoriales"]["indicadores"]
    assert d["transferencias_no_automaticas"]["puntaje_aplicado"] == pytest.approx(puntaje, abs=0.1)
