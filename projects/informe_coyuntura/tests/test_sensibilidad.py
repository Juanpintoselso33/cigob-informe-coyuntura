"""Regresiones offline del Monte Carlo paramétrico."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itcm
import sensibilidad


def test_base_redondea_dimension_como_motor_con_faltantes():
    import itcp

    resultado = itcp.calcular_itcp({
        "ratio_dnu": 1.4, "eficacia_legislativa": 14.3,
        "desafios_legislativos": 0, "veto_quorum": 10,
    })
    # Con una sola dimensión presente, su puntaje publicado es la base.
    # `_agregar` no redondea el paso final (multiplica y divide por el mismo
    # peso de dimensión), así que compara con tolerancia de punto flotante en
    # vez de igualdad exacta (ADR-0330: los pesos internos de poder_legislativo
    # cambiaron y algunas combinaciones binarias no cancelan exacto).
    assert sensibilidad._agregar(sensibilidad._estructura(resultado)) == pytest.approx(resultado["valor"])


class _RuidoMaximo:
    def uniform(self, minimo, maximo):
        return maximo


def test_itcm_declara_anclas_explicitas_en_sensibilidad():
    assert sensibilidad.INDICES["itcm"]["anclas"] == itcm.ANCLAS_ITCM


def test_perturbacion_del_desequilibrio_repuntua_con_anclas_explicitas():
    dims = {
        "estabilidad_monetaria": {
            "peso": 1.0,
            "ind": {
                "desequilibrio_monetario": {
                    "peso": 1.0,
                    "puntaje": 64.8,
                    "banda": 64.8,
                    "valor": 35.2,
                }
            },
        }
    }

    # ADR-0082: _perturbar recibe la ESCALA del índice —bandas, anclas y
    # transformaciones juntas— y no las tablas por separado.
    resultado = sensibilidad._perturbar(
        dims,
        _RuidoMaximo(),
        pesos=False,
        escala=itcm.ESCALA_ITCM,
    )

    # +5% del rango crudo 0-100: 35,2 → 40,2; anclas ITCM → 59,8.
    assert resultado == 59.8


def test_informe_sin_ruido_conserva_rem_anual_y_numero_de_corridas(monkeypatch):
    # Una simulación sin ruido debe devolver el mismo puntaje del motor.
    # El REM 21% anual vale 83 puntos; interpretarlo como mensual daba 10.
    monkeypatch.setattr(sensibilidad, 'RUIDO_INSUMO', 0)
    monkeypatch.setattr(sensibilidad, 'RUIDO_PESO', 0)
    monkeypatch.setattr(sensibilidad, 'N_DRAWS', 20)
    puntos = itcm.ESCALA_ITCM.puntaje(21.0, 'rem_ipc_12m')
    bloque = {'valor': puntos, 'dimensiones': {'monetaria': {
        'peso': 1.0, 'indicadores': {'rem_ipc_12m': {
            'peso': 1.0, 'puntaje_aplicado': puntos,
            'puntaje_banda': puntos, 'valor': 21.0}}}}}
    resultado = sensibilidad.analizar('itcm', bloque, sensibilidad.INDICES['itcm'])
    assert resultado['n_draws'] == 20
    for experimento in resultado['experimentos'].values():
        assert experimento['p05'] == experimento['p95'] == puntos
        assert experimento['desvio'] == 0


def test_informe_propaga_error_compartido_en_componentes_identicos():
    # Dos componentes idénticos con igual exposición conservan el error común.
    # Con exposiciones opuestas esa parte se cancela al agregarlos.
    bandas = {'a': [(0, 100, 50)], 'b': [(0, 100, 50)]}
    anclas = {k: [(0, 0), (100, 100)] for k in bandas}
    bloque = {'valor': 50, 'dimensiones': {'d': {'peso': 1, 'indicadores': {
        k: {'peso': .5, 'puntaje_aplicado': 50, 'puntaje_banda': 50, 'valor': 50}
        for k in bandas}}}}
    def desvio(exposicion):
        return sensibilidad.analizar_bloque(
            bloque, bandas, lambda x: x, n_draws=1000,
            anclas=anclas, exposicion=exposicion)['experimentos']['insumos']['desvio']
    assert desvio({'a': 1, 'b': 1}) > desvio({'a': 1, 'b': -1})
