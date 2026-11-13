"""La escala del semáforo, la misma en todo lo que se publica (ADR-0427).

ADR-0427 movió los cortes a 2,5 / 5 / 7,5 (puntajes 75 / 50 / 25, índice base
100 en 112,5 / 100 / 87,5) y el cálculo los tomó solo, porque sale de
`parametrica.CORTES_SEMAFORO`. Lo que no los tomó fue todo lo que los tenía
escritos a mano: la tabla de tramos del «¿por qué este color?» de cada
componente del índice de impacto social (85/95/105), las tablas de las fichas
en markdown, el chequeo del verificador de fichas, el eje de colores de la
evolución, los párrafos de las fichas web y las tablas de lectura de los
índices. Ninguno falló: siguieron publicando la escala vieja.

Estas guardas comparan cada una de esas tablas y textos contra la función que
decide el color, en cada borde. Si los cortes vuelven a moverse, fallan acá en
vez de quedar desactualizados en la página.
"""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(1, str(RAIZ / "scripts" / "fichas"))

import generar_informe  # noqa: E402
import itcg  # noqa: E402
import itcm  # noqa: E402
import itcp  # noqa: E402
import itvc  # noqa: E402
import parametrica  # noqa: E402
import publicar  # noqa: E402
from comun import (coma, indice_base100_de_tension, puntaje_de_tension,  # noqa: E402
                   tramos_de_tension, tramos_en_escala, umbrales_base100)

# Los cortes como los publica el snapshot (`semaforo_cortes`), armados desde la
# constante y no leídos del JSON: la guarda tiene que valer para el código, no
# para la última corrida.
CORTES = [{"color": c, "hasta": None if t == parametrica.INF else t}
          for c, t in parametrica.CORTES_SEMAFORO]
EPS = 0.01

FICHAS_TS = (RAIZ / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
DESCRIPCIONES_TS = (RAIZ / "web/src/lib/descripciones.ts").read_text(encoding="utf-8")


def _num(txt: str) -> float:
    return float(txt.replace("−", "-").replace(".", "").replace(",", "."))


def _bloque(clave: str) -> str:
    """El objeto de una ficha en fichas.ts, hasta la ficha siguiente."""
    m = re.search(rf"^  {clave}: \{{", FICHAS_TS, re.M)
    assert m, f"no hay ficha {clave} en fichas.ts"
    fin = re.search(r"^  [a-z_0-9]+: \{", FICHAS_TS[m.end():], re.M)
    return FICHAS_TS[m.start(): m.end() + (fin.start() if fin else len(FICHAS_TS))]


# ── Tablas en Python ─────────────────────────────────────────────────────────

def _tramos_coinciden(tramos, color_de):
    for t in tramos:
        if t["desde"] is not None:
            # El borde va con el color mejor: `desde` ya es de este tramo.
            assert color_de(t["desde"]) == t["color"], t
            assert color_de(t["desde"] - EPS) != t["color"], t
        if t["hasta"] is not None:
            assert color_de(t["hasta"] - EPS) == t["color"], t


def test_los_tramos_base100_del_por_que_son_los_del_color():
    """`publicar._TRAMOS_BASE100` era 85/95/105 escrito a mano: con ADR-0427 la
    frase de cada componente del índice de impacto social citaba bordes que no
    eran los del color publicado."""
    assert publicar._TRAMOS_BASE100 == parametrica.TRAMOS_BASE100
    assert [t["color"] for t in publicar._TRAMOS_BASE100] == ["rojo", "naranja", "amarillo", "verde"]
    _tramos_coinciden(publicar._TRAMOS_BASE100, parametrica.color_de_indice_base100)


def test_100_justo_es_amarillo_y_la_frase_lo_ata_al_borde_con_naranja():
    assert parametrica.color_de_indice_base100(100.0) == "amarillo"
    assert parametrica.color_de_indice_base100(99.99) == "naranja"
    frase = publicar._por_que_indice_base100("amarillo", 100.0)
    assert "está en Amarillo" in frase and "Naranja (100" in frase, frase


@pytest.mark.parametrize("a_escala,color_de", [
    (indice_base100_de_tension, parametrica.color_de_indice_base100),
    (puntaje_de_tension, parametrica.color_de_puntaje),
], ids=["base100", "puntaje"])
def test_las_tablas_de_las_fichas_en_markdown_coinciden_con_el_color(a_escala, color_de):
    filas = tramos_en_escala(CORTES, a_escala)
    assert [c for _, c in filas] == ["verde", "amarillo", "naranja", "rojo"]
    for texto, color in filas:
        nums = [_num(x) for x in re.findall(r"\d+(?:,\d+)?", texto)]
        if texto.endswith("o más"):
            assert color_de(nums[0]) == color, texto
            assert color_de(nums[0] - EPS) != color, texto
        elif texto.startswith("menos de"):
            assert color_de(nums[0] - EPS) == color, texto
            assert color_de(nums[0]) != color, texto
        else:
            desde, hasta = nums
            assert color_de(desde) == color, texto
            assert color_de(hasta - EPS) == color, texto
            assert color_de(hasta) != color, texto


def test_las_filas_de_tension_de_las_fichas_son_los_cortes():
    t = [coma(x, 1) for x in parametrica.TENSIONES_DE_CORTE]
    assert tramos_de_tension(CORTES) == [
        f"hasta {t[0]}", f"más de {t[0]} y hasta {t[1]}",
        f"más de {t[1]} y hasta {t[2]}", f"más de {t[2]}"]


def test_el_verificador_de_fichas_usa_los_cortes_del_color():
    umbrales = umbrales_base100(CORTES)
    assert [c for _, c in umbrales] == ["verde", "amarillo", "naranja"]
    for umbral, color in umbrales:
        assert parametrica.color_de_indice_base100(umbral) == color
        assert parametrica.color_de_indice_base100(umbral - EPS) != color


def test_la_marca_de_alerta_va_en_todo_cinturon_que_cuenta_para_la_alerta():
    """Quedaba `score >= EN_TENSION_MAX + 1` (ADR-0195 lo había descartado):
    con ADR-0427, un cinturón entre 5 y 6 contaba para la alerta y no llevaba
    la marca."""
    datos = {"a": {"score": 5.5}, "b": {"score": 5.01}, "c": {"score": 5.0}, "d": {"score": 1.0}}
    generar_informe.marcar_alerta_multicinturon(datos)
    marcados = {k for k, v in datos.items() if v.get("alerta") == "multicinturon"}
    assert marcados == {k for k, v in datos.items() if parametrica.color_de_tension(v["score"]) in ("naranja", "rojo")}
    assert marcados == {"a", "b"}


# ── Textos de la web ─────────────────────────────────────────────────────────

def _txt(x):
    return coma(x, 1)


@pytest.mark.parametrize("clave", ["itcm", "itcg", "itcp"])
def test_la_ficha_del_indice_0_100_cita_los_cortes_vigentes(clave):
    b = _bloque(clave)
    v, a, n = (_txt(x) for x in parametrica.PUNTAJES_DE_CORTE)
    t1, t2, t3 = (_txt(x) for x in parametrica.TENSIONES_DE_CORTE)
    i1, i2, i3 = (_txt(x) for x in parametrica.INDICES_BASE100_DE_CORTE)
    assert (f"verde con {v} o más, amarillo de {a} a menos de {v}, naranja de {n} a "
            f"menos de {a} y rojo por debajo de {n}") in b
    assert f"cortes de tensión ({t1}, {t2} y {t3} sobre 10" in b
    assert f"sus propios cortes ({i1}, {i2} y {i3})" in b


def test_la_ficha_del_indice_de_impacto_social_cita_los_cortes_vigentes():
    b = _bloque("itvc")
    v, a, n = (_txt(x) for x in parametrica.INDICES_BASE100_DE_CORTE)
    assert (f"verde con {v} o más, amarillo de {a} a menos de {v}, naranja de {n} a "
            f"menos de {a} y rojo por debajo de {n}") in b


@pytest.mark.parametrize("clave,mod", [("itcm", itcm), ("itcg", itcg), ("itcp", itcp), ("itvc", itvc)])
def test_la_tabla_de_lectura_de_la_ficha_es_la_del_indice(clave, mod):
    """Las bandas de lectura de los índices 0-100 se alinearon con ADR-0427
    (25 / 50 / 75 / 87,5) y las fichas seguían en 20 / 40 / 60 / 80."""
    filas = re.findall(r'\{ rango: "([^"]+)", lectura: "[^"]+" \}', _bloque(clave))
    bordes = {float(x) for lo, hi, _ in mod.BANDAS_INTERPRETACION
              for x in (lo, hi) if abs(x) != parametrica.INF}
    assert len(filas) == len(mod.BANDAS_INTERPRETACION)
    nums = {_num(x) for f in filas for x in re.findall(r"\d+(?:,\d+)?", f)}
    assert bordes <= nums, (bordes - nums, filas)
    permitidos = bordes | {round(b + 0.1, 1) for b in bordes} | {0.0, 100.0}
    assert nums <= permitidos, (nums - permitidos, filas)


def _tramo(umbrales, color):
    return next(t for t in umbrales if t["color"] == color)


def test_los_cortes_de_la_capacidad_prestable_en_el_texto_son_los_del_color():
    um = parametrica.umbrales_en_unidad("idc", publicar._escala_de(itcm, "ITCM"))
    c = lambda x: coma(round(x, 2))  # noqa: E731
    v = _tramo(um, "verde")["desde"]
    a = _tramo(um, "amarillo")["desde"]
    n = _tramo(um, "naranja")["desde"]
    frase = (f"desde {c(v)} es verde, de {c(a)} a {c(v)} amarillo, de {c(n)} a {c(a)} "
             f"naranja y por debajo de {c(n)} rojo")
    assert frase in DESCRIPCIONES_TS
    assert frase in _bloque("idc")


def test_los_cortes_de_las_tarifas_en_la_descripcion_son_los_del_color():
    ae = itvc.cortes_color_tarifas("agua_energia")
    tr = itvc.cortes_color_tarifas("transporte")
    assert (f"el transporte sigue en verde hasta {coma(tr[0])}% y agua+energía "
            f"hasta {coma(ae[0])}%") in DESCRIPCIONES_TS
