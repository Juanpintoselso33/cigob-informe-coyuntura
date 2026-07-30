# -*- coding: utf-8 -*-
"""Validación por PANEL para los compuestos socioeconómicos (ADR-0159).

POR QUÉ NO UN ANCLA. Las guías UNECE/ONU sobre indicadores compuestos separan dos
familias: los **económicos** tienen una serie de referencia y se validan contra
ella (para el ITCM, ADR-0158); los **socioeconómicos** normalmente **no la
tienen**, y lo que se prescribe (§6.61) es compararlos con **varias estadísticas
relacionadas** y **explicar las diferencias al publicar**.

El ITVC, el ITCG y el ITCP son de la segunda familia. Validar cada uno contra una
sola variable medía una faceta y se publicaba como si midiera el todo.

QUÉ MIDE. Para cada índice, su correlación contra TODO el panel, y dos
promedios: con las estadísticas de su **familia** (convergente) y con las
**ajenas** (discriminante). El resumen no es un r sino la **brecha** entre los
dos: cuánto más se parece el índice a lo suyo que a lo ajeno.

EN NIVELES Y EN DIFERENCIAS, y la segunda es la que manda: en una muestra de
unos treinta meses casi todas las series argentinas comparten la tendencia del
período, así que un r alto en niveles puede ser sólo eso. La brecha en
diferencias es la que no se puede satisfacer con tendencia común.

LAS FAMILIAS SE FIJAN ACÁ, POR CONCEPTO, y antes de mirar ningún resultado. Es
la parte que no puede decidirse mirando los números: si se asignara la familia
según con quién correlaciona mejor, la prueba se volvería circular y siempre
daría bien.
"""

# familia conceptual de cada estadística del panel. Ninguna es componente de
# ninguno de los cuatro índices — se verifica en un test.
FAMILIA = {
    # consumo de los hogares: tres canales del mismo fenómeno
    "consumo_supermercados": "itvc",
    "consumo_mayoristas": "itvc",
    "consumo_shoppings": "itvc",
    # valor de las empresas: lo que el capital paga por la transformación
    "merval_usd": "itcg",
    # política: incertidumbre, capital político y expectativa electoral
    "epu_argentina": "itcp",
    "icg_utdt": "itcp",
    "clima_electoral": "itcp",
    # ciclo de la actividad: es el ancla del ITCM, que tiene su propio régimen
    # (ADR-0158). Acá entra sólo como contraste AJENO para los otros tres.
    "indice_lider": "itcm",
}

ETIQUETAS = {
    "consumo_supermercados": "consumo en supermercados",
    "consumo_mayoristas": "consumo en autoservicios mayoristas",
    "consumo_shoppings": "consumo en centros de compras",
    "merval_usd": "Merval en dólares",
    "epu_argentina": "incertidumbre de política (EPU)",
    "icg_utdt": "confianza en el gobierno",
    "clima_electoral": "clima electoral",
    "indice_lider": "marcha de la actividad",
}


def _pearson(a: dict, b: dict):
    comunes = sorted(set(a) & set(b))
    n = len(comunes)
    if n < 12:
        return None, n
    xs = [a[m] for m in comunes]
    ys = [b[m] for m in comunes]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None, n
    return round(num / (dx * dy), 3), n


def _difs(s: dict) -> dict:
    fs = sorted(s)
    return {fs[i]: s[fs[i]] - s[fs[i - 1]] for i in range(1, len(fs))}


def perfil(indice: str, serie: dict, panel: dict) -> dict:
    """Perfil de un índice contra el panel completo, en niveles y diferencias."""
    filas, conv_n, disc_n, conv_d, disc_d = [], [], [], [], []
    for clave, ext in sorted(panel.items()):
        if not ext:
            continue
        r_niv, n = _pearson(serie, ext)
        r_dif, _ = _pearson(_difs(serie), _difs(ext))
        if r_niv is None:
            continue
        propia = FAMILIA.get(clave) == indice
        filas.append({"estadistica": clave, "etiqueta": ETIQUETAS.get(clave, clave),
                      "propia": propia, "r_niveles": r_niv,
                      "r_diferencias": r_dif, "n": n})
        (conv_n if propia else disc_n).append(abs(r_niv))
        if r_dif is not None:
            (conv_d if propia else disc_d).append(abs(r_dif))

    def _media(xs):
        return round(sum(xs) / len(xs), 3) if xs else None

    def _brecha(a, b):
        return round(a - b, 3) if (a is not None and b is not None) else None

    cn, dn = _media(conv_n), _media(disc_n)
    cd, dd = _media(conv_d), _media(disc_d)
    return {
        "indice": indice,
        "perfil": filas,
        "n_propias": len(conv_n),
        "n_ajenas": len(disc_n),
        "niveles": {"convergente": cn, "discriminante": dn, "brecha": _brecha(cn, dn)},
        "diferencias": {"convergente": cd, "discriminante": dd, "brecha": _brecha(cd, dd)},
    }


def lectura(p: dict) -> str:
    """Texto público del perfil. Dice la brecha en diferencias, que es la
    exigente, y NO la esconde cuando es negativa: el estándar pide explicar las
    diferencias, no reportar sólo las que confirman."""
    dif, niv = p["diferencias"], p["niveles"]
    if dif["brecha"] is None:
        return ""
    coma = lambda x: str(x).replace(".", ",").replace("-", "−")
    propias = ("la única estadística de su propio terreno" if p["n_propias"] == 1
               else f"las {p['n_propias']} estadísticas de su propio terreno")
    ajenas = ("la única ajena" if p["n_ajenas"] == 1 else f"las {p['n_ajenas']} ajenas")
    partes = [
        f"Contra un panel de {p['n_propias'] + p['n_ajenas']} estadísticas externas —ninguna "
        f"forma parte del índice— la comparación se hace en dos planos. En niveles el índice "
        f"acompaña a {propias} con {coma(niv['convergente'])} y a {ajenas} con "
        f"{coma(niv['discriminante'])}."
    ]
    if dif["brecha"] > 0:
        partes.append(
            f"En los cambios mes a mes —la prueba exigente, la que no se puede satisfacer con la "
            f"tendencia que en estos años arrastró a casi todas las series argentinas— la "
            f"separación se mantiene: {coma(dif['convergente'])} con lo propio contra "
            f"{coma(dif['discriminante'])} con lo ajeno.")
    else:
        partes.append(
            f"En los cambios mes a mes la separación no se sostiene: {coma(dif['convergente'])} "
            f"con lo propio contra {coma(dif['discriminante'])} con lo ajeno. Descontada la "
            f"tendencia común del período, el índice se mueve tanto o más con estadísticas de "
            f"otros terrenos que con las del suyo. Se publica porque el estándar pide explicar "
            f"las diferencias, no informar sólo las que confirman: con unos treinta meses de "
            f"historia y un panel corto, es un resultado a vigilar antes que un veredicto.")
    return " ".join(partes)
