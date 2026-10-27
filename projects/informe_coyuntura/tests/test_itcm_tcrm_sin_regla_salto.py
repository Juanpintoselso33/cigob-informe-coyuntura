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
import terminos_intercambio
import validacion_externa


def _reconstruido(ym):
    return itcm.calcular_itcm(validacion_externa._valores_itcm_por_mes()[ym])


def test_el_mes_de_la_devaluacion_ya_era_el_peor_de_la_serie():
    """El argumento central del rechazo. En dic-2023 —el mes del salto del
    ITCRM de 83,2 a 124,9— el índice NO leyó una mejora: quedó entre los meses
    más tensos de todo el registro. La competitividad efectivamente saltó a 100,
    pero la estabilidad monetaria se derrumbó a ~21 y pesa más (26% contra
    11%), así que la agregación resolvió bien el episodio sin ninguna regla.

    Se verifica que dic-2023 esté en el DECIL más tenso, no que sea el mínimo
    exacto. Hasta 2026-07-25 el test exigía `min(serie) == "2023-12"`, pero
    dic-2023 y ene-2024 daban 26,30 los dos: el test pasaba porque `min()`
    desempata por orden de iteración, no porque midiera algo. Al entrar
    emae_difusion (ADR-0124) el empate se rompió a favor de ene-2024 por medio
    punto y la falla lo dejó a la vista. Lo que sostiene el rechazo de ADR-0073
    es que el mes de la devaluación esté abajo de todo, no cuál de esos dos
    meses gana por decimales."""
    serie = {ym: r["valor"]
             for ym, vals in validacion_externa._valores_itcm_por_mes().items()
             if (r := itcm.calcular_itcm(vals))}
    orden = sorted(serie, key=serie.get)
    posicion = orden.index("2023-12")
    assert posicion <= max(1, len(orden) // 10), (
        f"dic-2023 quedó en la posición {posicion + 1} de {len(orden)} por tensión; "
        f"ya no está entre los meses más tensos y el rechazo de ADR-0073 hay que "
        f"revisarlo. Los cinco peores: {[(m, serie[m]) for m in orden[:5]]}")

    dims = _reconstruido("2023-12")["dimensiones"]
    # Desde ADR-0360 la dimensión cruza el tipo de cambio real con los términos
    # del intercambio: el salto lleva la posición del tipo de cambio real a su
    # techo (a = 1), y la dimensión queda en la fila de «peso competitivo»
    # (50 a 85 según los términos del intercambio). Antes daba 100.
    assert terminos_intercambio.posicion_tcr(124.88) == 1.0
    assert _cruce(dims) >= 50.0
    assert dims["estabilidad_monetaria"]["puntaje"] < 25.0
    assert (itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]["peso"]
            > _peso_del_cruce()), (
        "si la competitividad pasara a pesar más que la estabilidad monetaria, "
        "el rechazo de ADR-0073 habría que revisarlo")


def _cruce(dims) -> float:
    """Puntaje del cruce tipo de cambio real × términos del intercambio, que
    desde ADR-0387 vive dentro del sector externo y no es una dimensión."""
    ind = dims["sector_externo"]["indicadores"]
    return terminos_intercambio.combinar_dimension(
        {k: ind[k]["puntaje_aplicado"] for k in ("tcrm", "terminos_intercambio")})


def _peso_del_cruce() -> float:
    d = itcm.DIMENSIONES_ITCM["sector_externo"]
    return d["peso"] * (d["indicadores"]["tcrm"] + d["indicadores"]["terminos_intercambio"])


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
    el ITCRM cayó de 124,9 a 97,0 porque la inflación se comió la devaluación,
    y la posición del tipo de cambio real en la matriz (ADR-0360) baja sola de
    1 a ~0,68. Con los términos del intercambio del mismo trimestre en los dos
    meses, la dimensión baja también (57,5 → 52,3 con el dato de oct-2026)."""
    assert terminos_intercambio.posicion_tcr(124.88) == 1.0
    assert 0.6 < terminos_intercambio.posicion_tcr(97.03) < 0.75
    dic = _cruce(_reconstruido("2023-12")["dimensiones"])
    abr = _cruce(_reconstruido("2024-04")["dimensiones"])
    assert dic > abr, (dic, abr)


def test_la_regla_del_saldo_comercial_sigue_viva():
    """El rechazo es del ajuste del TCRM, no de la familia de reglas: la del
    saldo comercial por composición expo/impo (ADR-0056) sigue en pie."""
    assert callable(itcm.ajuste_automatico_saldo)
