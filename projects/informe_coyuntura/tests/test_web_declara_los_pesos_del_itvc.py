"""La web declara pesos y pertenencias del ITCIS en prosa, a mano, y el motor
los calcula en `itvc.DIMENSIONES_ITVC`. Cuando una recalibración mueve un peso,
la prosa no se entera: nada la vincula al número.

Ya pasó, y quedó publicado durante semanas:

- `descripciones.ts` decía que `pobreza_nowcast` "se publica como contexto: no
  integra el índice" cuando pesa 9,31% desde ADR-0153 — y la ficha del MISMO
  indicador, en `fichas.ts`, decía lo correcto. La web se desmentía a sí misma
  en dos archivos.
- `endeudamiento_familiar` e `indice_lider` seguían descritos como si
  puntuaran; salieron del índice en ADR-0154.
- La ficha de `brecha_salario_cbt` declaraba 17,06% en un párrafo y 22,75% en
  otro (el valor previo a ADR-0111/0153).

Ningún gate podía verlo: `gate_calidad.py` compara la card contra su serie, y
los tests de reconciliación comparan el snapshot consigo mismo. Nadie cruzaba
la PROSA contra la paramétrica. Este test hace eso.
"""
import bisect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc  # noqa: E402
from publicar import VIDA_OCULTOS  # noqa: E402

DESCRIPCIONES = (ROOT / "web" / "src" / "lib" / "descripciones.ts").read_text(encoding="utf-8")
FICHAS = (ROOT / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")

# {indicador: (peso interno, peso efectivo en el índice)}
PESOS = {
    ind: (interno, round(interno * dim["peso"] * 100, 2))
    for dim in itvc.DIMENSIONES_ITVC.values()
    for ind, interno in dim["indicadores"].items()
}


def _bloque(texto: str, clave: str) -> str:
    """El objeto literal de un indicador: desde `clave: {` hasta el `},` que lo
    cierra en la misma indentación. Alcanza para no cruzar de vecino."""
    m = re.search(rf"^(\s*){re.escape(clave)}: \{{$", texto, re.M)
    if not m:
        return ""
    fin = re.compile(rf"^{m.group(1)}\}},?$", re.M).search(texto, m.end())
    return texto[m.end():fin.start()] if fin else texto[m.end():]


@pytest.mark.parametrize("indicador", sorted(PESOS))
def test_lo_que_puntua_no_se_describe_como_contexto(indicador):
    bloque = _bloque(DESCRIPCIONES, indicador)
    if not bloque:
        pytest.skip(f"{indicador} no tiene entrada en descripciones.ts")
    for frase in ("no integra el índice", "se publica como contexto",
                  "NO puntúa", "no puntúa"):
        assert frase not in bloque, (
            f"descripciones.ts dice «{frase}» de {indicador}, que integra el "
            f"ITCIS con {PESOS[indicador][1]}% del índice."
        )


@pytest.mark.parametrize("indicador", sorted(VIDA_OCULTOS))
def test_lo_que_salio_del_indice_lo_dice(indicador):
    bloque = _bloque(DESCRIPCIONES, indicador)
    if not bloque:
        pytest.skip(f"{indicador} no tiene entrada en descripciones.ts")
    assert "NO puntúa" in bloque or "no puntúa" in bloque, (
        f"{indicador} salió del ITCIS (ADR-0154) y descripciones.ts no lo dice. "
        f"Si se describe sin aclararlo, se lee como componente."
    )
    assert "En el ITCIS puntúa" not in bloque, (
        f"descripciones.ts todavía afirma que {indicador} puntúa en el índice."
    )


def _declarados(texto: str) -> list[tuple[str, float]]:
    """Los porcentajes «X% del ITCIS» de fichas.ts, cada uno atribuido al
    indicador en cuyo bloque cae: el último `  clave: {` que lo precede."""
    claves = [(m.start(), m.group(1))
              for m in re.finditer(r"^  ([a-z_0-9]+): \{$", texto, re.M)]
    fuera = []
    # "del índice" tambien cuenta: la ficha de la brecha declaraba su peso así,
    # y así fue como se quedó con el valor previo a ADR-0111/0153. Los que
    # hablan de OTRO índice (los del ITCM) caen en claves que no están en
    # PESOS y el comparador los saltea.
    for m in re.finditer(r"([0-9]+(?:,[0-9]+)?)% del (?:ITCIS|índice)", texto):
        i = bisect.bisect_right(claves, (m.start(), "\uffff")) - 1
        if i >= 0:
            fuera.append((claves[i][1], float(m.group(1).replace(",", "."))))
    return fuera


# La oración canónica de la ficha: dimensión, peso interno y peso efectivo en
# una sola frase. Se parsea entera y no por pedazos, para no confundirla con
# los `cambios`, que citan pesos VIEJOS a propósito ("entra con 50% interno")
# y son registro histórico, no declaración vigente.
PERTENECE = re.compile(
    r"Pertenece a la dimensión de ([^(]+?)\s*"
    r"\((\d+(?:,\d+)?)% interno · (\d+(?:,\d+)?)% del ITCIS\)")


def _pertenencias(texto: str):
    """(indicador, dimensión declarada, % interno, % efectivo) de cada ficha
    que use la oración canónica."""
    claves = [(m.start(), m.group(1))
              for m in re.finditer(r"^  ([a-z_0-9]+): \{$", texto, re.M)]
    fuera = []
    for m in PERTENECE.finditer(texto):
        i = bisect.bisect_right(claves, (m.start(), "\uffff")) - 1
        if i >= 0:
            fuera.append((claves[i][1], m.group(1).strip().lower(),
                          float(m.group(2).replace(",", ".")),
                          float(m.group(3).replace(",", "."))))
    return fuera


def test_hay_pertenencias_que_verificar():
    assert len(_pertenencias(FICHAS)) >= 8


def test_la_ficha_ubica_y_pesa_cada_indicador_como_la_parametrica():
    """El peso INTERNO y la dimensión son lo que se mueve cuando un indicador
    cambia de casa: el efectivo puede quedar intacto —ADR-0214 lo conserva a
    propósito— y aun así la ficha queda declarando un reparto que ya no
    existe."""
    nombres = {k: d["nombre"].lower() for k, d in itvc.DIMENSIONES_ITVC.items()}
    dim_de = {i: nombres[k] for k, d in itvc.DIMENSIONES_ITVC.items()
              for i in d["indicadores"]}
    malos = []
    for ind, dim, interno, efectivo in _pertenencias(FICHAS):
        if ind not in PESOS:
            continue
        if dim != dim_de[ind]:
            malos.append(f"{ind}: la ficha lo pone en «{dim}», la paramétrica "
                         f"en «{dim_de[ind]}»")
        esperado = PESOS[ind][0] * 100
        if abs(interno - esperado) > 0.06:
            malos.append(f"{ind}: la ficha dice {interno}% interno, la "
                         f"paramétrica da {round(esperado, 2)}%")
    assert not malos, "fichas.ts y la paramétrica no dicen lo mismo:\n  " + "\n  ".join(malos)


def test_las_fichas_declaran_el_peso_que_calcula_la_parametrica():
    malos = []
    for indicador, declarado in _declarados(FICHAS):
        esperado = PESOS.get(indicador, (None, None))[1]
        if esperado is None:
            continue
        # Tolerancia de un decimal: las fichas redondean a dos y a uno.
        if abs(declarado - esperado) > 0.06:
            malos.append(f"{indicador}: la ficha dice {declarado}%, "
                         f"la paramétrica da {esperado}%")
    assert not malos, "fichas.ts declara pesos que ya no son:\n  " + "\n  ".join(malos)


def test_hay_pesos_que_verificar():
    """Si el patrón de la prosa cambia y el parser deja de encontrar nada, el
    test de arriba pasaría vacío."""
    assert len(_declarados(FICHAS)) >= 6


# ── Un indicador que dejó de puntuar tiene que decirlo en su descripción ─────
# El caso que motiva la regla (2026-08-21): `consumo_carne` dejó de puntuar
# —pasó a puntuar el total de las tres carnes— y su descripción siguió diciendo
# "proxy histórico del bienestar alimentario", como si nada. Peor: la
# descripción del indicador NUEVO mandaba a "leerlo junto al de carne vacuna",
# que ya no era una card.
#
# Ningún test miraba eso. Los pesos sí, la dimensión sí, la prosa no. Esta es la
# prosa: si el indicador tiene descripción publicada y NO está en la
# paramétrica, su texto tiene que declararlo.
DESCRIPCIONES = (ROOT / "web" / "src" / "lib" / "descripciones.ts").read_text(encoding="utf-8")


def _claves_con_descripcion() -> set:
    bloque = DESCRIPCIONES[DESCRIPCIONES.index("export const DESCRIPCIONES"):]
    return set(re.findall(r"^  ([a-z_0-9]+): \{$", bloque, re.M))


def test_hay_descripciones_que_revisar():
    assert len(_claves_con_descripcion()) > 20


def test_lo_que_dejo_de_puntuar_lo_dice_su_descripcion():
    """Sólo se exige a los del cinturón: son los que la paramétrica conoce, así
    que son los únicos donde 'no está en DIMENSIONES_ITVC' significa de verdad
    'dejó de puntuar' y no 'es de otro cinturón'."""
    del_cinturon = {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    # Los que alguna vez integraron el ITCIS y hoy no: viven en VIDA_OCULTOS o
    # quedaron como desglose de otro (consumo_carne dentro de la matriz A×B).
    from publicar import VIDA_OCULTOS
    retirados = (VIDA_OCULTOS | {"consumo_carne"}) & _claves_con_descripcion()
    assert retirados, "el conjunto de referencia quedó vacío: revisá el parser"

    mudos = []
    for clave in sorted(retirados):
        bloque = _bloque(DESCRIPCIONES, clave)
        if not any(f in bloque for f in ("NO puntúa", "no puntúa", "no integra")):
            mudos.append(clave)
    assert not mudos, (
        "estos indicadores dejaron de puntuar y su descripción no lo dice, así "
        "que el lector los lee como si siguieran adentro: " + ", ".join(mudos))


# ── La ficha del ÍNDICE: lo que ninguna guarda por indicador podía ver ───────
# Los tests de arriba cruzan la ficha de CADA indicador contra la paramétrica.
# La ficha del índice no tiene indicador, así que se quedó afuera y acumuló tres
# años de deriva sin que nada la mirara (encontrado el 2026-08-21):
#
#   - declaraba "37% ingresos · 25% precios · 15% empleo", el reparto anterior a
#     mudar la informalidad de casa (ADR-0214). Cuatro de seis pesos mal, en el
#     párrafo que explica cómo se agrega el índice.
#   - decía "Dieciséis componentes" en el resumen y "Trece componentes en cinco
#     dimensiones" en la selección: se contradecía a sí misma, y las dos cifras
#     estaban mal.
#
# No es prosa de adorno: es la metodología publicada. Un lector que quiera
# reproducir el índice con lo que dice la ficha obtiene otro número.
NUMERALES = {"tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
             "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
             "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16,
             "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20}

FICHA_ITVC = _bloque(FICHAS, "itvc")


def _n_componentes() -> int:
    return sum(len(d["indicadores"]) for d in itvc.DIMENSIONES_ITVC.values())


def test_la_ficha_del_indice_declara_bien_cuantos_componentes_tiene():
    """Cualquier «N componentes en M dimensiones» de la ficha del índice, sea en
    el resumen o en la selección, tiene que dar los números de la paramétrica."""
    frases = re.findall(
        r"(\w+) componentes en (\w+) dimensiones", FICHA_ITVC, re.I)
    assert frases, "la ficha del ITCIS dejó de declarar su composición: revisá el parser"
    malos = []
    for comp, dim in frases:
        c, d = NUMERALES.get(comp.lower()), NUMERALES.get(dim.lower())
        if c is None or d is None:
            malos.append(f"«{comp} componentes en {dim} dimensiones» no se pudo leer")
            continue
        if c != _n_componentes() or d != len(itvc.DIMENSIONES_ITVC):
            malos.append(
                f"la ficha dice «{comp} componentes en {dim} dimensiones» y la "
                f"paramétrica tiene {_n_componentes()} en {len(itvc.DIMENSIONES_ITVC)}")
    assert not malos, "la ficha del ITCIS no se cuenta bien:\n  " + "\n  ".join(malos)


def test_la_leyenda_de_agregacion_declara_los_pesos_de_dimension_vigentes():
    """El paréntesis de la leyenda es la única declaración pública del reparto
    ENTRE dimensiones. Los pesos por indicador ya tienen guarda; éste no la
    tenía, y era el que estaba mal."""
    m = re.search(r"Promedio ponderado en dos niveles \(([^)]+)\)", FICHA_ITVC)
    assert m, "la leyenda de agregación cambió de forma: actualizá este parser"
    declarados = {}
    for trozo in m.group(1).split("·"):
        d = re.match(r"\s*(\d+(?:,\d+)?)%\s+(.+?)\s*$", trozo)
        assert d, f"no se pudo leer «{trozo.strip()}» de la leyenda"
        declarados[d.group(2).lower()] = float(d.group(1).replace(",", "."))

    reales = {d["nombre"].lower(): round(d["peso"] * 100, 2)
              for d in itvc.DIMENSIONES_ITVC.values()}
    faltan = set(reales) - set(declarados)
    sobran = set(declarados) - set(reales)
    assert not faltan and not sobran, (
        f"la leyenda no nombra las mismas dimensiones que la paramétrica.\n"
        f"  falta declarar: {sorted(faltan)}\n  declara de más: {sorted(sobran)}")
    malos = [f"{n}: la ficha dice {declarados[n]}%, la paramétrica da {reales[n]}%"
             for n in reales if abs(declarados[n] - reales[n]) > 0.06]
    assert not malos, ("la leyenda de agregación declara pesos que ya no son:\n  "
                       + "\n  ".join(malos))


# ── Todo lo que puntúa tiene ficha ──────────────────────────────────────────
# `trabajo_independiente` entró al índice con 2,42% y estuvo publicado sin ficha
# técnica: el modal lo mostraba y no había a dónde ir a leer qué mide, de dónde
# sale ni qué no cubre. Ningún test lo veía porque todos los que cruzan fichas
# saltean con `skip` al indicador que no tiene entrada — la ausencia se leía
# como "nada que verificar".
def test_todo_componente_del_indice_tiene_ficha_tecnica():
    claves = set(re.findall(r"^  ([a-z_0-9]+): \{$", FICHAS, re.M))
    sin_ficha = sorted(set(PESOS) - claves)
    assert not sin_ficha, (
        "estos indicadores puntúan en el ITCIS y no tienen ficha en fichas.ts, "
        "así que la web los muestra sin decir qué miden ni qué no cubren: "
        + ", ".join(f"{i} ({PESOS[i][1]}%)" for i in sin_ficha))
