"""Un solo camino de "valor de la serie" al "puntaje" (ADR-0082).

El mismo bug apareció TRES veces en una jornada, siempre con la misma forma:
dos lugares que tienen que estar de acuerdo sobre cómo se puntúa un indicador,
y nada que los obligue.

  1. La reconstrucción histórica del ITCM usaba una lista escrita a mano de
     componentes: los indicadores nuevos no entraban y la validación externa se
     quedó atrás del índice en silencio.
  2. La matriz de redundancia puntuaba TODO con bandas, pero el motor usa
     anclas explícitas para `presion_dolarizacion` — hasta 25 puntos de
     diferencia sobre un número que se publicaba.
  3. El diagnóstico de bandas puntuaba el valor ANUAL del REM contra bandas
     MENSUALES, y mandaba a revisar una banda perfectamente calibrada.

Ninguno rompía nada: los tres devolvían un número plausible y equivocado. Este
archivo verifica la propiedad que los hace imposibles — que exista UN camino, y
que cualquier reproducción del puntaje pase por él.
"""
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import parametrica

RAIZ = Path(__file__).parent.parent
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"
SCRIPTS = RAIZ / "scripts"

# Módulos que reproducen puntajes fuera del motor. Si aparece uno nuevo, debe
# sumarse acá — y si no pasa por puntaje_de, el test lo delata.
REPRODUCEN_PUNTAJES = ["validacion_externa.py", "revision_bandas.py", "sensibilidad.py"]


def test_el_motor_puntua_a_traves_de_la_funcion_unica():
    """calcular_indice no debe elegir escala por su cuenta."""
    fuente = inspect.getsource(parametrica.calcular_indice)
    assert "puntaje_de(" in fuente
    assert "puntaje_interpolado(" not in fuente, (
        "calcular_indice volvió a elegir la escala por su cuenta")
    assert "puntaje_desde_anclas(" not in fuente


def test_nadie_puntua_indicadores_del_itcm_por_fuera():
    """Los módulos que reproducen puntajes deben llamar a puntaje_de.

    Llamar directo a puntaje_interpolado sobre un indicador del índice es
    exactamente el bug 2 y el 3: se saltea las anclas y las transformaciones.
    """
    for nombre in REPRODUCEN_PUNTAJES:
        codigo = (SCRIPTS / nombre).read_text(encoding="utf-8")
        # se ignoran los comentarios y docstrings: hablan del tema a propósito
        activo = "\n".join(l for l in codigo.splitlines()
                           if not l.strip().startswith("#"))
        for prohibida in ("parametrica.puntaje_interpolado(",
                          "parametrica.puntaje_desde_anclas("):
            assert prohibida not in activo, (
                f"{nombre} llama a {prohibida} en vez de parametrica.puntaje_de(): "
                "se saltea anclas y transformaciones")


def test_toda_transformacion_esta_declarada_y_no_aplicada_por_los_llamadores():
    """Bug 3. Las transformaciones previas al puntaje viven en la tabla, no en
    quien arma los valores. Si un colector vuelve a transformar antes de
    llamar al índice, el motor transformaría DE NUEVO."""
    assert itcm.TRANSFORMACIONES_ITCM, "la tabla quedó vacía"
    for nombre in ("macro.py", "validacion_externa.py"):
        codigo = (SCRIPTS / nombre).read_text(encoding="utf-8")
        activo = [l for l in codigo.splitlines()
                  if "rem_mensual_equivalente" in l and not l.strip().startswith("#")]
        # macro.py conserva un uso para el TEXTO de la ficha, no para puntuar
        for linea in activo:
            assert "valores[" not in linea, (
                f"{nombre} transforma el REM antes de puntuar: el motor lo haría "
                f"de nuevo → doble transformación. Línea: {linea.strip()}")


def test_el_puntaje_publicado_se_reproduce_desde_el_valor_crudo():
    """La prueba de fuego: tomar el valor CRUDO que publica cada indicador y
    reproducir su puntaje_banda con la función única. Cualquiera de los tres
    bugs habría hecho fallar esto."""
    macro = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cinturones"]["macro"]
    bloque = macro["itcm"]
    comprobados = 0
    for dim in bloque["dimensiones"].values():
        for ind, info in dim["indicadores"].items():
            valor = info.get("valor")
            if valor is None:
                continue
            reproducido = parametrica.puntaje_de(
                valor, ind, itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM,
                itcm.TRANSFORMACIONES_ITCM)
            assert abs(reproducido - info["puntaje_banda"]) < 0.15, (
                f"{ind}: crudo {valor} → {reproducido}, publicado "
                f"{info['puntaje_banda']}")
            comprobados += 1
    assert comprobados >= 12, f"solo se comprobaron {comprobados} indicadores"
