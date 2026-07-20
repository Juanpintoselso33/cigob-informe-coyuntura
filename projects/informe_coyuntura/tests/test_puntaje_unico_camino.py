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


# ── La serie tiene que medir lo MISMO que puntúa el índice (ADR-0086) ───────

def test_ninguna_serie_mide_otra_magnitud_que_la_que_puntua_su_indice():
    """Quinto caso de la familia, encontrado el 18-jul-2026 en el ITCG.

    La serie de `rigi_inversiones` guardaba el pipeline en MILLONES DE DÓLARES
    (31.192) mientras las bandas del indicador están calibradas para un
    PORCENTAJE (0-60+). La card puntuaba 22,0 → 47,5, correcto; la
    reconstrucción histórica puntuaba 31.192 → 100,0. En la práctica la serie
    del ITCG veía un escalón binario: 10 durante todo 2024 y 100 desde
    ene-2025.

    Lo que lo hizo invisible: la divergencia estaba DECLARADA como excepción
    del gate G3 —legítima para su propósito, que es vigilar la frescura de la
    card— y nadie advirtió que esa misma serie alimenta la reconstrucción.

    Este test compara el puntaje del último punto de cada serie contra el
    puntaje publicado. Tolerancia amplia (20 puntos) a propósito: card y serie
    suelen estar ancladas a fechas distintas —hoy vs fin de mes— y eso produce
    diferencias chicas y legítimas. Lo que se busca es una diferencia de
    MAGNITUD, que es de otro orden.
    """
    import itcg
    import itcp

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cinturones"]
    series = json.loads((RAIZ / "web" / "src" / "data" / "series.json")
                        .read_text(encoding="utf-8"))
    escalas = {
        "itcm": itcm.ESCALA_ITCM,
        "itcg": parametrica.Escala(itcg.BANDAS_ITCG, getattr(itcg, "ANCLAS_ITCG", None)),
        "itcp": parametrica.Escala(itcp.BANDAS_ITCP, getattr(itcp, "ANCLAS_ITCP", None)),
    }
    # Series declaradas como NO comparables: se excluyen de la reconstrucción
    # justamente por esto, así que no deben fallar el test — pero la exclusión
    # tiene que existir en el código, no ser un olvido.
    import validacion_externa
    no_comparables = set(getattr(validacion_externa, "ITCG_SERIE_NO_COMPARABLE", {}))

    problemas = []
    for ckey, ikey in (("macro", "itcm"), ("gestion", "itcg"), ("politica", "itcp")):
        escala = escalas[ikey]
        for dim in snap[ckey][ikey]["dimensiones"].values():
            for ind, info in dim["indicadores"].items():
                pts = series.get(ind) or []
                if not pts or not escala.puntuable(ind):
                    continue
                ultimo = pts[-1].get("valor")
                if ultimo is None:
                    continue
                p_serie = escala.puntaje(ultimo, ind)
                p_pub = info["puntaje_banda"]
                if abs(p_serie - p_pub) > 20 and ind not in no_comparables:
                    problemas.append(
                        f"{ikey}/{ind}: la serie ({ultimo}) puntúa {p_serie} y el "
                        f"índice publica {p_pub} — ¿la serie guarda otra magnitud?")
    assert not problemas, "\n".join(problemas)


def test_la_exclusion_del_rigi_esta_declarada_con_motivo():
    """Si alguien la borra, el escalón binario vuelve sin avisar."""
    import validacion_externa
    no_comp = validacion_externa.ITCG_SERIE_NO_COMPARABLE
    assert "rigi_inversiones" in no_comp
    assert len(no_comp["rigi_inversiones"]) > 20, "el motivo tiene que estar explicado"
