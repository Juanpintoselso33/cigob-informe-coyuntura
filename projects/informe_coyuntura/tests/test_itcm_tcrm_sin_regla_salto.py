"""Por qué el ITCM NO tiene una regla anti-salto para el tipo de cambio real.

La auditoría de consistencia de jul-2026 pidió que la banda superior del TCRM
fuera condicional a la velocidad de la depreciación: sin eso, decía, "una crisis
cambiaria mejoraría el puntaje de competitividad mientras destruye el de
estabilidad". Se implementó la regla (ADR-0073) y se descartó tras revisión
externa, porque la premisa no se sostiene.

Estos tests fijan la evidencia del rechazo. Si alguien vuelve a proponer la
regla —la observación es intuitiva y va a volver a aparecer— acá están los
números que la contestan, ejecutables, y no como prosa en un documento.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import validacion_externa


def _reconstruido(ym):
    return itcm.calcular_itcm(validacion_externa._valores_itcm_por_mes()[ym])


def test_el_mes_de_la_devaluacion_ya_era_el_peor_de_la_serie():
    """El argumento central del rechazo. En dic-2023 —el mes del salto del
    ITCRM de 83,2 a 124,9— el índice NO leyó una mejora: marcó el valor más
    tenso de todo el registro. La competitividad efectivamente saltó a 100,
    pero la estabilidad monetaria se derrumbó a ~21 y pesa más (26% contra
    11%), así que la agregación resolvió bien el episodio sin ninguna regla."""
    serie = {ym: r["valor"]
             for ym, vals in validacion_externa._valores_itcm_por_mes().items()
             if (r := itcm.calcular_itcm(vals))}
    peor = min(serie, key=serie.get)
    assert peor == "2023-12", f"el mes más tenso pasó a ser {peor}"

    dims = _reconstruido("2023-12")["dimensiones"]
    assert dims["competitividad_externa"]["puntaje"] == 100.0
    assert dims["estabilidad_monetaria"]["puntaje"] < 25.0
    assert (itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]["peso"]
            > itcm.DIMENSIONES_ITCM["competitividad_externa"]["peso"]), (
        "si la competitividad pasara a pesar más que la estabilidad monetaria, "
        "el rechazo de ADR-0073 habría que revisarlo")


def test_no_existe_regla_automatica_para_el_tcrm():
    """El TCRM se puntúa por su nivel y nada más. Un descuento por salto
    castigaría la misma inflación dos veces: el ITCRM ya es un tipo de cambio
    REAL, así que el traspaso a precios lo hace caer solo, y esa misma
    inflación ya puntúa con 26% del índice en estabilidad monetaria."""
    assert not hasattr(itcm, "ajuste_automatico_tcrm")
    assert not hasattr(itcm, "TCRM_SALTO_PISO")


def test_el_indice_registra_por_si_solo_la_evaporacion_del_salto():
    """La otra mitad del argumento: el índice no necesita anticipar que el
    salto se va a licuar, porque lo ve cuando ocurre. Entre dic-2023 y abr-2024
    la competitividad baja sola de 100 a ~71 — el ITCRM cayó de 124,9 a 97,0
    porque la inflación se comió la devaluación."""
    dic = _reconstruido("2023-12")["dimensiones"]["competitividad_externa"]["puntaje"]
    abr = _reconstruido("2024-04")["dimensiones"]["competitividad_externa"]["puntaje"]
    assert dic == 100.0 and 65.0 < abr < 80.0, (dic, abr)


def test_la_regla_del_saldo_comercial_sigue_viva():
    """El rechazo es del ajuste del TCRM, no de la familia de reglas: la del
    saldo comercial por composición expo/impo (ADR-0056) sigue en pie."""
    assert callable(itcm.ajuste_automatico_saldo)
