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

Y CUANDO LA FAMILIA TIENE TRES O MÁS, además del perfil se calcula su **factor
común** —el primer componente principal, como arma la Reserva Federal de Chicago
el CFNAI (ADR-0161, `factor_comun.py`)— y el índice se contrasta contra ese
factor en vez de contra una estadística suelta. Las cargas del factor deciden
solas el signo y el peso de cada serie; no hay que declarar a mano cuál va
invertida, que es por donde se colaba el ajuste.
"""

import factor_comun

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
    salida = {
        "indice": indice,
        "perfil": filas,
        "n_propias": len(conv_n),
        "n_ajenas": len(disc_n),
        "niveles": {"convergente": cn, "discriminante": dn, "brecha": _brecha(cn, dn)},
        "diferencias": {"convergente": cd, "discriminante": dd, "brecha": _brecha(cd, dd)},
    }
    factor = _factor(indice, serie, panel)
    if factor:
        salida["factor"] = factor
    return salida


def _factor(indice: str, serie: dict, panel: dict) -> dict | None:
    """Contraste contra el factor común de la familia propia del índice.

    Reemplaza al contraste contra una sola estadística cuando la familia tiene
    tres o más: en vez de elegir una faceta, se compara contra lo que las tres
    comparten. La comparación de referencia es la de mejor estadística
    individual, que se guarda al lado para que el lector pueda ver si el
    compuesto aporta o si sólo diluye.
    """
    propias = {k: v for k, v in panel.items() if FAMILIA.get(k) == indice and v}
    niv = factor_comun.contraste(serie, propias)
    if niv is None:
        return None
    dif = factor_comun.contraste(serie, propias, en_diferencias=True)
    mejor_niv = max((abs(f["r_niveles"]) for f in _filas_propias(indice, serie, propias)),
                    default=None)
    mejor_dif = max((abs(f["r_diferencias"]) for f in _filas_propias(indice, serie, propias)
                     if f["r_diferencias"] is not None), default=None)
    return {
        "cargas": niv["cargas"],
        "etiquetas": {k: ETIQUETAS.get(k, k) for k in niv["cargas"]},
        "varianza_explicada": niv["varianza_explicada"],
        "n_series": niv["n_series"],
        "n": niv["n"],
        "pares": niv["pares"],
        "r_niveles": niv["r"],
        "r_diferencias": dif["r"] if dif else None,
        "mejor_sola_niveles": mejor_niv,
        "mejor_sola_diferencias": mejor_dif,
    }


def _filas_propias(indice: str, serie: dict, propias: dict) -> list:
    filas = []
    for clave, ext in sorted(propias.items()):
        r_niv, n = _pearson(serie, ext)
        if r_niv is None:
            continue
        r_dif, _ = _pearson(_difs(serie), _difs(ext))
        filas.append({"estadistica": clave, "r_niveles": r_niv, "r_diferencias": r_dif, "n": n})
    return filas


def _coma(x) -> str:
    return str(x).replace(".", ",").replace("-", "−")


def lectura_factor(p: dict) -> str:
    """Una línea para el tablero: contra qué se compara y con cuánto acompaña.

    Corta a propósito. El desarrollo —cargas, varianza, signos— va en la ficha
    metodológica: en el tablero la conclusión ya es larga y agregarle cuatro
    oraciones más la vuelve ilegible.
    """
    f = p.get("factor")
    if not f or f["r_niveles"] is None:
        return ""
    gana = f.get("mejor_sola_niveles") is not None and abs(f["r_niveles"]) > f["mejor_sola_niveles"]
    cierre = ("más que cualquiera de ellas por separado"
              if gana else "menos que la mejor de ellas por separado")
    return (f"Contra el factor común de las {f['n_series']} estadísticas de su terreno —lo que "
            f"comparten, no una sola— el índice acompaña con {_coma(f['r_niveles'])} en niveles"
            + (f" y {_coma(f['r_diferencias'])} en los cambios mes a mes"
               if f["r_diferencias"] is not None else "")
            + f": {cierre}.")


def lectura_factor_detalle(p: dict) -> list:
    """El desarrollo del factor, para la ficha metodológica, en párrafos.

    Devuelve una LISTA y no un bloque: son cuatro ideas distintas —qué es el
    factor, qué signo dedujo, por qué no es circular, y si le gana a la mejor
    sola— y en un solo párrafo quedan siete líneas seguidas que nadie lee.

    Todo se deriva de las cargas: cuál serie entra invertida, cuál pesa más y si
    el compuesto le gana o no a la mejor estadística sola. Nada de eso se escribe
    a mano — si se escribiera, cambiaría de mes a mes y quedaría viejo.
    """
    f = p.get("factor")
    if not f or f["r_niveles"] is None:
        return []
    etq, cargas = f["etiquetas"], f["cargas"]
    pesada = max(cargas, key=lambda k: abs(cargas[k]))
    invertidas = [etq[k] for k in sorted(cargas) if cargas[k] < 0]

    partes = [
        f"Para no depender de una sola estadística, las {f['n_series']} del terreno propio del "
        f"índice se resumen en su factor común: el primer componente principal, el mismo método "
        f"con el que la Reserva Federal de Chicago arma su índice de actividad a partir de 85 "
        f"series. El factor recoge {_coma(f['varianza_explicada'])}% de lo que las "
        f"{f['n_series']} tienen en común, y pesa más en {etq[pesada]}."
    ]
    if invertidas:
        cual = invertidas[0] if len(invertidas) == 1 else " y ".join(
            [", ".join(invertidas[:-1]), invertidas[-1]])
        partes.append(
            f"El cálculo determina por su cuenta que {cual} entra con signo invertido: no se "
            f"declaró a mano. Es lo que hace que la comparación no se pueda acomodar — quien "
            f"elige los signos de un promedio ya vio los resultados.")
    partes.append(
        "Las cargas se estiman con las estadísticas externas solas: el índice no participa del "
        "cálculo del factor, sólo se compara contra él una vez armado.")

    mejor_n, mejor_d = f.get("mejor_sola_niveles"), f.get("mejor_sola_diferencias")
    if mejor_n is not None:
        if abs(f["r_niveles"]) > mejor_n:
            partes.append(
                f"El compuesto acompaña al índice más que cualquiera de las {f['n_series']} por "
                f"separado, que llegan como máximo a {_coma(round(mejor_n, 3))} en niveles y "
                f"{_coma(round(mejor_d, 3))} en los cambios: lo que las tres comparten —y no una "
                f"en particular— es lo que el índice sigue.")
        else:
            partes.append(
                f"El compuesto queda por debajo de la mejor de las {f['n_series']} por separado, "
                f"que llega a {_coma(round(mejor_n, 3))} en niveles. Se publica igual porque es "
                f"lo que el contraste enseña: lo que las {f['n_series']} comparten es un ciclo "
                f"más ancho que el que el índice sigue, y una de ellas sola lo capta mejor. Es un "
                f"límite del panel disponible —corto y de un solo tipo de fuente— antes que un "
                f"veredicto sobre el índice.")
    return partes


def lectura(p: dict) -> str:
    """Texto público del perfil. Dice la brecha en diferencias, que es la
    exigente, y NO la esconde cuando es negativa: el estándar pide explicar las
    diferencias, no reportar sólo las que confirman."""
    dif, niv = p["diferencias"], p["niveles"]
    if dif["brecha"] is None:
        return ""
    coma = _coma
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
