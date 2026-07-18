"""Tests de la regla anti-salto del TCRM (ADR-0073).

Los casos usan los valores REALES del ITCRM del BCRA, para que el test falle
si alguien recalibra los umbrales sin mirar qué le hacen a la historia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import macro
import parametrica


def _banda(valor):
    return parametrica.puntaje_interpolado(valor, itcm.BANDAS_ITCM["tcrm"])


# ── El caso que motiva la regla ──────────────────────────────────────────────

def test_el_salto_de_diciembre_2023_deja_de_puntuar_perfecto():
    """dic-2023: el ITCRM saltó 83,2 → 124,9 (+50,1% en un mes) y la banda le
    daba 100/100, el máximo de competitividad externa. Cuatro meses después
    estaba en 97,0 — la ganancia se evaporó entera."""
    assert _banda(124.9) == 100.0, "la banda sola sigue premiando el salto"
    aj = itcm.ajuste_automatico_tcrm({"valor": 124.9, "salto_ventana": 50.1})
    assert aj is not None
    assert aj["puntaje"] == itcm.TCRM_SALTO_PISO
    assert aj["origen"] == "automatico"


def test_el_descuento_sobrevive_al_mes_del_salto():
    """ene-2024: el TCRM seguía en 132,8 por el salto de diciembre, pero la
    variación del mes fue solo +6,3%. Mirando el mes suelto habría vuelto a
    puntuar 100; la ventana lo impide."""
    aj = itcm.ajuste_automatico_tcrm({"valor": 132.8, "salto_ventana": 50.1})
    assert aj is not None and aj["puntaje"] == itcm.TCRM_SALTO_PISO


# ── Calibración de la ventana ────────────────────────────────────────────────

def test_la_ventana_cubre_el_traspaso_a_precios():
    """La ventana no es una elección de forma: el pass-through de una
    devaluación en Argentina dura entre seis y ocho meses (Frank 2017-2023;
    Bertholet 2026 lo ve estabilizarse cerca del octavo). Con tres meses el
    descuento se soltaba en mar-2024, cuando el índice volvía a leer 89 puntos
    de competitividad con la inflación todavía comiéndose el salto."""
    assert 6 <= itcm.TCRM_SALTO_VENTANA <= 8, itcm.TCRM_SALTO_VENTANA


def test_la_regla_se_apaga_sola_cuando_el_traspaso_termina():
    """Propiedad emergente que conviene pinear: al octavo mes el TCRM ya había
    caído a 87,9 (banda 54,7), por debajo del piso de 55, así que el descuento
    deja de aplicar sin necesidad de soltarlo — lo suelta el propio nivel."""
    assert _banda(87.9) < itcm.TCRM_SALTO_PISO
    assert itcm.ajuste_automatico_tcrm({"valor": 87.9, "salto_ventana": 50.1}) is None


# ── Lo que la regla NO debe tocar ────────────────────────────────────────────

def test_la_recuperacion_gradual_de_2025_queda_intacta():
    """jul-sep 2025: el TCRM subió de 86,1 a 99,1 tras ampliarse la banda
    cambiaria, con un máximo de +6,6% m/m. Esa mejora se sostuvo y no es un
    salto — la regla no debe opinar."""
    for valor in (91.8, 95.0, 99.1):
        assert itcm.ajuste_automatico_tcrm({"valor": valor, "salto_ventana": 6.6}) is None


def test_no_castiga_cuando_la_banda_ya_esta_en_el_piso():
    """Un salto sobre un TCRM muy apreciado no tiene nada que descontar: la
    banda ya puntúa por debajo del piso."""
    assert _banda(78.0) < itcm.TCRM_SALTO_PISO
    assert itcm.ajuste_automatico_tcrm({"valor": 78.0, "salto_ventana": 30.0}) is None


def test_sin_dato_de_variacion_no_opina():
    """Fallback a la serie INDEC discontinuada: sin salto_ventana, sin ajuste."""
    assert itcm.ajuste_automatico_tcrm({"valor": 124.9}) is None
    assert itcm.ajuste_automatico_tcrm({}) is None


# ── Forma de la interpolación ────────────────────────────────────────────────

def test_el_descuento_es_gradual_y_no_un_acantilado():
    """ADR-0056 estableció que estos ajustes interpolan en vez de cortar. Justo
    encima del umbral el descuento tiene que ser casi nulo, y crecer parejo
    hasta la saturación."""
    valor = 124.9
    puntajes = [
        itcm.ajuste_automatico_tcrm({"valor": valor, "salto_ventana": s})["puntaje"]
        for s in (8.5, 12.0, 17.0, 22.0, 25.0)
    ]
    assert puntajes == sorted(puntajes, reverse=True), puntajes
    assert puntajes[0] > 95.0, f"salto apenas sobre el umbral castiga demasiado: {puntajes[0]}"
    assert puntajes[-1] == itcm.TCRM_SALTO_PISO


def test_mas_alla_de_la_saturacion_no_sigue_bajando():
    piso = itcm.ajuste_automatico_tcrm({"valor": 124.9, "salto_ventana": 25.0})["puntaje"]
    extremo = itcm.ajuste_automatico_tcrm({"valor": 124.9, "salto_ventana": 200.0})["puntaje"]
    assert piso == extremo == itcm.TCRM_SALTO_PISO


def test_el_umbral_separa_los_dos_casos_historicos():
    """El umbral tiene que caer entre la corrección genuina más fuerte del
    período (+6,6% m/m, jul-2025) y el salto (+50,1%, dic-2023). Si alguien lo
    baja de 6,6 empieza a castigar depreciaciones reales."""
    assert 6.6 < itcm.TCRM_SALTO_UMBRAL < 50.1


# ── Integración ──────────────────────────────────────────────────────────────

def test_la_regla_esta_enganchada_en_el_calculo_del_cinturon():
    """Sin este cableado la regla existe pero nunca corre."""
    ind = {"tcrm": {"valor": 124.9, "salto_ventana": 50.1}}
    res = macro.calcular_itcm_cinturon(ind)
    assert res is not None
    aplicado = res["dimensiones"]["competitividad_externa"]["indicadores"]["tcrm"]
    assert aplicado["puntaje_banda"] == 100.0
    assert aplicado["puntaje_aplicado"] == itcm.TCRM_SALTO_PISO
