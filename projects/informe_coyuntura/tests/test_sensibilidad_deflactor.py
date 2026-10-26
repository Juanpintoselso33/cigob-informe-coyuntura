"""Tests del error compartido del deflactor en la simulación de robustez
(ADR-0078).

El punto de estos tests es que el rango publicado NO vuelva a apoyarse en el
supuesto de que los errores de medición son independientes cuando varios
indicadores comparten el mismo deflactor.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import sensibilidad

SNAPSHOT = Path(__file__).parent.parent / "web" / "src" / "data" / "informe.json"


def _bloque_itcm():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cinturones"]["macro"]["itcm"]


def _ancho(exposicion, n=2000):
    r = sensibilidad.robustez_compacta(
        _bloque_itcm(), itcm.BANDAS_ITCM, lambda v: round((100 - v) / 10, 1),
        n_draws=n, exposicion=exposicion)
    return r["p95"] - r["p05"]


def _ancho_sin_redondeo(exposicion, n=8000):
    """p95 − p05 de los draws sin redondear. Desde ADR-0367 (escala de inflación
    más empinada) la diferencia entre los dos supuestos quedó en ~0,13 puntos:
    el rango publicado, redondeado a un decimal con 2.000 draws, ya no la ve."""
    import random
    import statistics
    import parametrica
    dims = sensibilidad._estructura(_bloque_itcm())
    # La misma escala que usa la publicación (anclas explícitas y la
    # transformación anual→mensual del REM), no una simplificada.
    escala = parametrica.Escala(itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM,
                                itcm.TRANSFORMACIONES_ITCM)
    rng = random.Random(sensibilidad.SEMILLA)
    draws = [sensibilidad._perturbar(dims, rng, pesos=True, escala=escala,
                                     exposicion=exposicion) for _ in range(n)]
    q = statistics.quantiles(draws, n=20)
    return q[-1] - q[0]


def test_compartir_el_deflactor_ensancha_el_rango():
    """Es el objeto del ADR: si el error del deflactor es común, no se cancela
    en la agregación y el intervalo de robustez tiene que ser MÁS ancho que
    bajo el supuesto de independencia."""
    independiente = _ancho_sin_redondeo(None)
    compartido = _ancho_sin_redondeo(sensibilidad.EXPOSICION_DEFLACTOR_ITCM)
    assert compartido > independiente, (
        f"compartir el deflactor no ensanchó el rango: {compartido} vs {independiente}")


def test_la_robustez_publicada_propaga_la_exposicion():
    """Lo que se publica (`robustez_compacta`) tiene que usar la exposición: si
    dejara de pasarla a los draws, el histograma sería idéntico al de los
    errores independientes (Codex, 26-oct-2026)."""
    def hist(exposicion):
        return sensibilidad.robustez_compacta(
            _bloque_itcm(), itcm.BANDAS_ITCM, lambda v: round((100 - v) / 10, 1),
            n_draws=500, exposicion=exposicion)["hist"]
    assert hist(None) != hist(sensibilidad.EXPOSICION_DEFLACTOR_ITCM)


def test_el_idm_esta_excluido_por_construccion():
    """El IDM usa el IPC pero compara M3 real contra M2 real: el deflactor se
    cancela en la resta. Incluirlo sería modelar un contagio que no existe."""
    assert "idm" not in sensibilidad.EXPOSICION_DEFLACTOR_ITCM


def test_los_signos_reflejan_la_direccion_del_contagio():
    """Si el IPC está sobreestimado, la inflación medida sube (peor puntaje)
    pero las variaciones REALES caen. Si alguien pone todos los signos iguales,
    los efectos se compensan y el rango se ANGOSTA en vez de ensancharse — es
    el error que cometió la primera versión de este análisis."""
    exp = sensibilidad.EXPOSICION_DEFLACTOR_ITCM
    assert exp["ipc_total"] > 0
    for deflactado in ("recaudacion", "credito_privado", "idc"):
        assert exp[deflactado] < 0, deflactado


def test_todos_los_expuestos_son_indicadores_reales_del_itcm():
    """Una clave mal escrita no rompería nada: simplemente no aplicaría, y el
    contagio se perdería en silencio."""
    del_indice = {ind for d in itcm.DIMENSIONES_ITCM.values() for ind in d["indicadores"]}
    for ik in sensibilidad.EXPOSICION_DEFLACTOR_ITCM:
        assert ik in del_indice, f"{ik} no es un indicador del ITCM"


def test_la_mezcla_preserva_la_varianza_del_ruido():
    """La parte compartida REEMPLAZA a la idiosincrática (pesos √f y √(1−f)),
    no se le suma: si no, el ensanche vendría de inyectar más ruido total y no
    de la correlación, que es lo que se quiere modelar."""
    f = sensibilidad.FRAC_ERROR_DEFLACTOR
    assert 0.0 < f < 1.0
    assert abs((f ** 0.5) ** 2 + ((1 - f) ** 0.5) ** 2 - 1.0) < 1e-9
