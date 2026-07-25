"""Tests de la difusión sectorial del EMAE (ADR-0124).

Lo que se protege acá:
  * que se cuenten los 15 SECTORES y no la 16ª serie del dataset, que es una
    partida contable ("Subsidios netos") y no una actividad;
  * que un mes incompleto no se publique (una difusión sobre 12 sectores no es
    comparable con una sobre 15);
  * que los cortes de banda caigan en el HUECO entre dos valores alcanzables,
    de modo que ningún conteo entero quede sobre un borde;
  * que la dimensión siga sumando uno y el peso salga del EMAE, no del IPI.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import macro
import parametrica

BANDAS = itcm.BANDAS_ITCM["emae_difusion"]
N = 15


# ── Universo de sectores ────────────────────────────────────────────────────

def test_son_quince_sectores():
    assert len(macro.INDEC_EMAE_SECTORES) == N


def test_subsidios_netos_queda_afuera():
    """Es un componente de la agregación (impuestos netos de subsidios), no una
    actividad económica. Está en el mismo dataset y es fácil incluirla por
    error: sumaría una partida contable al conteo de sectores."""
    assert "11.3_IF_2004_M_25" not in macro.INDEC_EMAE_SECTORES
    nombres = " ".join(macro.INDEC_EMAE_SECTORES.values()).lower()
    assert "subsidio" not in nombres


def test_los_ids_no_se_repiten():
    assert len(set(macro.INDEC_EMAE_SECTORES.values())) == N


# ── Cálculo de la difusión ──────────────────────────────────────────────────

def _niveles_sinteticos(crecen: int, meses=("2025-05", "2026-05")):
    """{id: {mes: nivel}} donde `crecen` sectores suben y el resto baja."""
    previo, actual = meses
    out = {}
    for i, sid in enumerate(macro.INDEC_EMAE_SECTORES):
        out[sid] = {previo: 100.0, actual: 110.0 if i < crecen else 90.0}
    return out


def test_cuenta_los_sectores_que_crecen(monkeypatch):
    for crecen in (0, 1, 8, 14, 15):
        monkeypatch.setattr(
            macro, "_emae_sectores_niveles",
            lambda limit=300, c=crecen: _niveles_sinteticos(c))
        difusion, detalle = macro._emae_difusion_por_mes()
        assert difusion["2026-05"] == round(crecen / N * 100, 2), crecen
        assert len(detalle["2026-05"]) == N


def test_un_sector_plano_no_cuenta_como_crecimiento(monkeypatch):
    """La condición es > 0 estricto: un sector que no se movió no crece."""
    niveles = _niveles_sinteticos(0)
    primero = next(iter(macro.INDEC_EMAE_SECTORES))
    niveles[primero]["2026-05"] = 100.0          # exactamente igual
    monkeypatch.setattr(macro, "_emae_sectores_niveles", lambda limit=300: niveles)
    difusion, _ = macro._emae_difusion_por_mes()
    assert difusion["2026-05"] == 0.0


def test_mes_incompleto_no_se_emite(monkeypatch):
    """Si a un sector le falta el dato, el mes no se publica: una difusión
    calculada sobre 14 sectores no es comparable con una sobre 15."""
    niveles = _niveles_sinteticos(10)
    primero = next(iter(macro.INDEC_EMAE_SECTORES))
    del niveles[primero]["2026-05"]
    monkeypatch.setattr(macro, "_emae_sectores_niveles", lambda limit=300: niveles)
    difusion, _ = macro._emae_difusion_por_mes()
    assert "2026-05" not in difusion


def test_la_comparacion_es_interanual_por_calendario(monkeypatch):
    """No se compara contra el mes anterior de la lista sino contra el mismo mes
    del año previo: las series son originales, sin desestacionalizar."""
    niveles = {}
    for i, sid in enumerate(macro.INDEC_EMAE_SECTORES):
        niveles[sid] = {"2025-05": 100.0, "2026-04": 500.0, "2026-05": 110.0}
    monkeypatch.setattr(macro, "_emae_sectores_niveles", lambda limit=300: niveles)
    difusion, _ = macro._emae_difusion_por_mes()
    # 2026-05 se compara con 2025-05 (sube), no con 2026-04 (bajaría)
    assert difusion["2026-05"] == 100.0
    # 2026-04 no tiene su par 2025-04, así que no se emite
    assert "2026-04" not in difusion


# ── Bandas ──────────────────────────────────────────────────────────────────

def test_las_bandas_cubren_todo_el_rango():
    for sectores in range(N + 1):
        valor = round(sectores / N * 100, 2)
        parametrica.puntaje_banda(valor, BANDAS)      # no debe levantar


def test_los_cortes_caen_entre_valores_alcanzables():
    """Con 15 sectores el indicador sólo toma múltiplos de 6,67. Si un corte
    coincidiera con un valor alcanzable, un conteo entero quedaría sobre el
    borde y su clasificación dependería de un redondeo."""
    alcanzables = {round(s / N * 100, 2) for s in range(N + 1)}
    for low, high, _ in BANDAS:
        for corte in (low, high):
            if corte in (float("inf"), float("-inf")):
                continue
            assert corte not in alcanzables, f"el corte {corte} es alcanzable"
            assert min(abs(corte - v) for v in alcanzables) > 2.0, corte


def test_puntajes_de_referencia():
    """Los valores que fija ADR-0124 en su tabla."""
    esperado = {0: 10.0, 4: 10.0, 8: 51.7, 12: 80.0, 14: 100.0, 15: 100.0}
    for sectores, puntaje in esperado.items():
        valor = round(sectores / N * 100, 2)
        assert parametrica.puntaje_interpolado(valor, BANDAS) == puntaje, sectores


def test_el_puntaje_es_monotono_creciente():
    previos = [parametrica.puntaje_interpolado(round(s / N * 100, 2), BANDAS)
               for s in range(N + 1)]
    assert previos == sorted(previos), previos


def test_no_satura_en_el_tramo_util():
    """Sólo 14 y 15 sectores llegan a 100: si saturara antes, el indicador
    dejaría de discriminar en la zona donde vive la mitad de la historia."""
    en_cien = [s for s in range(N + 1)
               if parametrica.puntaje_interpolado(round(s / N * 100, 2), BANDAS) == 100.0]
    assert en_cien == [14, 15], en_cien


# ── Dimensión ───────────────────────────────────────────────────────────────

def _dim():
    return itcm.DIMENSIONES_ITCM["actividad"]["indicadores"]


def test_la_difusion_esta_en_la_dimension_actividad():
    assert "emae_difusion" in _dim()


def test_los_pesos_suman_uno():
    assert abs(sum(_dim().values()) - 1.0) < 1e-9


def test_el_peso_salio_del_emae_y_no_del_ipi():
    """ADR-0124: la composición por FUENTE de la dimensión no cambia — el EMAE
    sigue aportando 80% y el IPI 20%. Si mañana alguien saca el peso del IPI
    para hacerle lugar a la difusión, cambia el criterio de ADR-0079 sin
    decirlo."""
    ind = _dim()
    assert ind["ipi_manufacturero"] == 0.20
    assert abs(ind["emae_ia"] + ind["emae_difusion"] - 0.80) < 1e-9


def test_difusion_y_emae_no_pesan_lo_mismo():
    """El nivel es la medida principal; la amplitud la califica."""
    assert _dim()["emae_ia"] > _dim()["emae_difusion"]
