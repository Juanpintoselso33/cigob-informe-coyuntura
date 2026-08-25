"""El aviso del Monitor habla poco y sólo cuando pasa algo.

`#informe-de-coyuntura` tuvo 8 mensajes humanos en 60 días. Un resumen diario
lo convertiría en un feed: el bot sería el 88% del canal. Por eso lo que se
prueba acá es, sobre todo, cuándo NO avisa.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from aviso_informe import UMBRAL_SCORE, cambios

BASE = {
    "score_global": 3.9,
    "cinturon_dominante": "vida_cotidiana",
    "riesgo": "político",
    "multicinturon": False,
    "cinturones": {
        "macro": {"score": 3.6, "estado": "en_tension"},
        "politica": {"score": 3.3, "estado": "en_tension"},
        "vida_cotidiana": {"score": 6.1, "estado": "tensionado"},
        "gestion": {"score": 2.7, "estado": "estable"},
    },
}


def variando(**kw):
    d = {**BASE, "cinturones": {k: dict(v) for k, v in BASE["cinturones"].items()}}
    d.update(kw)
    return d


def test_sin_cambios_no_avisa():
    assert cambios(BASE, variando()) == []


def test_un_movimiento_chico_del_score_no_avisa():
    """Un indicador que se actualiza mueve el score unas décimas todos los
    días. Avisar eso es el resumen diario por la ventana."""
    assert cambios(BASE, variando(score_global=BASE["score_global"] + UMBRAL_SCORE / 2)) == []


def test_un_movimiento_grande_del_score_si_avisa():
    ms = cambios(BASE, variando(score_global=BASE["score_global"] + UMBRAL_SCORE))
    assert len(ms) == 1 and "score global" in ms[0]


def test_cambia_el_riesgo_dominante():
    ms = cambios(BASE, variando(riesgo="tecnocrático"))
    assert any("riesgo dominante pasó" in m for m in ms)


def test_cambia_el_cinturon_del_que_sale_el_riesgo():
    ms = cambios(BASE, variando(cinturon_dominante="macro"))
    assert any("sale de *Macro*" in m for m in ms)


def test_un_cinturon_cambia_de_estado():
    otro = variando()
    otro["cinturones"]["gestion"]["estado"] = "en_tension"
    ms = cambios(BASE, otro)
    assert len(ms) == 1 and "Gestión" in ms[0] and "en tensión" in ms[0]


def test_el_score_de_un_cinturon_solo_no_avisa():
    """Mientras no cambie de estado, el número por sí solo no interrumpe."""
    otro = variando()
    otro["cinturones"]["macro"]["score"] = 4.4
    assert cambios(BASE, otro) == []


def test_la_alerta_multicinturon_avisa_al_prenderse_y_al_apagarse():
    assert any("prendió" in m for m in cambios(BASE, variando(multicinturon=True)))
    assert any("apagó" in m for m in cambios(variando(multicinturon=True), BASE))


def test_la_primera_corrida_no_inventa_cambios():
    """Sin estado anterior no hay con qué comparar: el script no llama a
    `cambios`, pero si lo hiciera con un dict vacío no debe romper."""
    assert isinstance(cambios({}, BASE), list)
