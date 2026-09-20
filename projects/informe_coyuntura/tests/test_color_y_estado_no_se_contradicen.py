"""El color y el estado leen la MISMA escala: no pueden contradecirse (ADR-0333).

La tensión 0-10 se publica dos veces con palabras distintas: como color de
semáforo («Sin tensión relevante» / «Tensión moderada» / …) y como estado de
cinturón («estable» / «en tensión» / «tensionado»). Durante meses el primer
corte del color fue 4,0 —el borde 60 de las bandas de interpretación— y el del
estado 3, que no salía de ningún lado, así que todo lo que cayera entre 3,0 y 4,0
se publicaba a la vez como sin tensión y en tensión. Le pasaba a macro, en 3,69.

Este test no comprueba un número: comprueba que las dos tablas sigan atadas.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

import parametrica  # noqa: E402
from config import UMBRALES, estado_de_score  # noqa: E402

# Cómo se dice cada color en la web (web/src/lib/datos.ts::LECTURA_SEMAFORO) y
# qué estado le corresponde. Es el mapa que el lector ve.
ESTADO_ESPERADO = {"verde": "estable", "amarillo": "en_tension",
                   "naranja": "tensionado", "rojo": "tensionado"}


def test_los_cortes_del_color_salen_de_los_umbrales_del_estado():
    """No pueden estar escritos dos veces: el color los deriva."""
    cortes = dict(parametrica.CORTES_SEMAFORO)
    assert cortes["verde"] == float(UMBRALES["ESTABLE_MAX"]), (
        "el primer corte del color se separó del umbral de «estable»: es la "
        "contradicción de ADR-0333 volviendo")
    assert cortes["amarillo"] == float(UMBRALES["EN_TENSION_MAX"])


def test_ningun_valor_de_tension_recibe_dos_lecturas_opuestas():
    """Barrido fino de 0 a 10: el color y el estado tienen que coincidir siempre."""
    choques = []
    for centesimas in range(0, 1001):
        t = centesimas / 100
        color = parametrica.color_de_tension(t)
        estado = estado_de_score(t)
        if ESTADO_ESPERADO[color] != estado:
            choques.append((t, color, estado))
    assert not choques, (
        f"{len(choques)} valores de tensión reciben color y estado que se "
        f"contradicen. Primeros: {choques[:5]}. Ejemplo de lo que ve el lector: "
        f"«Sin tensión relevante» en el titular y «en tensión» en el cinturón, "
        f"con el mismo número.")


def test_el_caso_que_lo_destapo_ya_no_se_contradice():
    """Macro con ITCM 63,1 → tensión 3,69: era verde y «en tensión» a la vez."""
    t = (100 - 63.1) / 10
    assert 3.0 < t <= 4.0, "la franja del choque cambió; revisar el ADR"
    # Ahora las dos tablas lo leen igual: el ITCM 63,1 es "moderadamente
    # aflojado" para el método, así que verde y estable.
    assert parametrica.color_de_tension(t) == "verde"
    assert estado_de_score(t) == "estable"


def test_el_borde_de_cada_tramo_cae_del_mismo_lado_en_las_dos_tablas():
    for corte in (UMBRALES["ESTABLE_MAX"], UMBRALES["EN_TENSION_MAX"]):
        for t in (corte - 0.01, corte, corte + 0.01):
            color = parametrica.color_de_tension(t)
            assert ESTADO_ESPERADO[color] == estado_de_score(t), (
                f"desacuerdo en el borde {corte} con tensión {t}: color {color} "
                f"contra estado {estado_de_score(t)}")
