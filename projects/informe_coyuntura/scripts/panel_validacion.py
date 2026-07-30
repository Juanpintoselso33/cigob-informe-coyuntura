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
import regresion_validacion

# familia conceptual de cada estadística del panel. Ninguna es componente de
# ninguno de los cuatro índices — se verifica en un test.
FAMILIA = {
    # consumo de los hogares: tres canales del mismo fenómeno
    "consumo_supermercados": "itvc",
    "consumo_mayoristas": "itvc",
    "consumo_shoppings": "itvc",
    # vida material de los hogares medida en VOLÚMENES FÍSICOS (ADR-0163):
    # cuánta luz y gas consumen, cuánto se mueven, cuánto combustible cargan
    "electricidad_residencial": "itvc",
    "gas_residencial": "itvc",
    "transporte_pasajeros": "itvc",
    "ventas_naftas": "itvc",
    # respuesta del capital privado al programa: cuánto vale lo que ya está
    # instalado en el país y cuánto capital de afuera decide entrar (ADR-0164)
    "merval_usd": "itcg",
    "inversion_directa_externa": "itcg",
    "inversion_portafolio_externa": "itcg",
    "financiamiento_externo_privado": "itcg",
    # política: incertidumbre, capital político y expectativa electoral
    "epu_argentina": "itcp",
    "icg_utdt": "itcp",
    "clima_electoral": "itcp",
    # ciclo de la actividad: es el ancla del ITCM, que tiene su propio régimen
    # (ADR-0158). Acá entra sólo como contraste AJENO para los otros tres.
    "indice_lider": "itcm",
}

# Nombre público de cada estadística. En mayúscula inicial —son nombres de
# estadísticas, no descripciones— y con su ORGANISMO al lado: sin la fuente, el
# lector no tiene forma de saber qué se está usando de validador ni de ir a
# chequearlo, que es justamente lo que esta sección promete.
ETIQUETAS = {
    "consumo_supermercados": "Ventas en supermercados",
    "consumo_mayoristas": "Ventas en autoservicios mayoristas",
    "consumo_shoppings": "Ventas en centros de compras",
    "electricidad_residencial": "Demanda eléctrica residencial",
    "gas_residencial": "Consumo residencial de gas",
    "transporte_pasajeros": "Pasajeros en transporte público",
    "ventas_naftas": "Ventas de naftas",
    "merval_usd": "Merval en dólares",
    "inversion_directa_externa": "Inversión directa de no residentes",
    "inversion_portafolio_externa": "Inversión de cartera de no residentes",
    "financiamiento_externo_privado": "Financiamiento externo a empresas",
    "epu_argentina": "Incertidumbre de política (EPU)",
    "icg_utdt": "Confianza en el Gobierno (ICG)",
    "clima_electoral": "Clima electoral",
    "indice_lider": "Índice Líder de actividad",
}

FUENTES = {
    "consumo_supermercados": "INDEC",
    "consumo_mayoristas": "INDEC",
    "consumo_shoppings": "INDEC",
    "electricidad_residencial": "CAMMESA",
    "gas_residencial": "Sec. de Energía",
    "transporte_pasajeros": "INDEC",
    "ventas_naftas": "Sec. de Energía",
    "merval_usd": "BYMA / CCL",
    "inversion_directa_externa": "BCRA",
    "inversion_portafolio_externa": "BCRA",
    "financiamiento_externo_privado": "BCRA",
    "epu_argentina": "Banco de España / SECMCA",
    "icg_utdt": "UTDT",
    "clima_electoral": "Votómetro",
    "indice_lider": "UTDT",
}

# QUÉ ESTADÍSTICAS ARMAN EL FACTOR de cada índice (ADR-0163). No es «las de su
# familia» sin más: dentro de una familia puede haber tipos de medición que no
# se pueden mezclar, porque entonces el factor termina capturando el método de
# medición en vez del fenómeno.
#
# ITVC → los cuatro VOLÚMENES FÍSICOS, y no las tres ventas de comercio. El
# criterio es el mismo que dejó afuera a los índices salariales: no compartir
# insumo con un componente del índice. Las ventas «a precios constantes» se
# deflactan con índices de precios del INDEC, y `ipc_alimentos` es componente
# del ITVC; un volumen físico no necesita deflactor. Se suma una razón de
# concepto: los autoservicios mayoristas abastecen también a revendedores y los
# centros de compras son gasto discrecional, así que ninguno de los dos es
# «cómo vive el hogar promedio».
#
# HONESTIDAD SOBRE EL ORDEN EN QUE PASÓ: el criterio es independiente del
# resultado y ya se venía aplicando, pero se lo aplicó DESPUÉS de medir el panel
# ancho. Eso no lo invalida y tampoco lo convierte en un hallazgo confirmado: la
# prueba real son los meses que vienen, con el corte ya fijado acá.
#
# Las tres de comercio siguen en el panel y en la familia del ITVC: se publican
# sus correlaciones, sólo que no arman el factor.
# ITCG → las cuatro de la respuesta del capital privado (ADR-0164). Acá el
# factor NO le gana a la mejor estadística sola y se publica igual: es el mismo
# criterio con el que se publicó el caso negativo del ITVC antes de resolverlo.
# Elegir el subconjunto que diera mejor sería justamente lo prohibido.
FACTOR = {
    "itvc": ["electricidad_residencial", "gas_residencial",
             "transporte_pasajeros", "ventas_naftas"],
    "itcp": ["epu_argentina", "icg_utdt", "clima_electoral"],
    "itcg": ["merval_usd", "inversion_directa_externa",
             "inversion_portafolio_externa", "financiamiento_externo_privado"],
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
                      "fuente": FUENTES.get(clave, ""), "propia": propia,
                      "r_niveles": r_niv, "r_diferencias": r_dif, "n": n})
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
    claves = FACTOR.get(indice) or []
    propias = {k: panel[k] for k in claves if panel.get(k)}
    niv = factor_comun.contraste(serie, propias)
    if niv is None:
        return None
    dif = factor_comun.contraste(serie, propias, en_diferencias=True)
    # la referencia es la mejor estadística individual DEL FACTOR, no de toda la
    # familia: si se comparara contra la mejor de la familia entera, el
    # compuesto competiría contra una serie que ni siquiera lo integra
    filas = _filas_propias(indice, serie, propias)
    mejor_niv = max((abs(f["r_niveles"]) for f in filas), default=None)
    mejor_dif = max((abs(f["r_diferencias"]) for f in filas
                     if f["r_diferencias"] is not None), default=None)
    salida = {
        "cargas": niv["cargas"],
        "etiquetas": {k: ETIQUETAS.get(k, k) for k in niv["cargas"]},
        "fuentes": {k: FUENTES.get(k, "") for k in niv["cargas"]},
        "varianza_explicada": niv["varianza_explicada"],
        "n_series": niv["n_series"],
        "n": niv["n"],
        "pares": niv["pares"],
        "r_niveles": niv["r"],
        "r_diferencias": dif["r"] if dif else None,
        "mejor_sola_niveles": mejor_niv,
        "mejor_sola_diferencias": mejor_dif,
    }
    # ¿Cuánto de la correlación en NIVELES es sólo la tendencia del período?
    # (ADR-0162). Es la pregunta que la correlación no responde y que en estos
    # treinta meses argentinos importa más que en ningún otro lado: casi todas
    # las series se movieron para el mismo lado, así que un r alto en niveles
    # puede ser eso y nada más. Se corre sobre niveles a propósito — diferenciar
    # ya le quita la tendencia, así que ahí la pregunta no tiene sentido.
    # Se guardan los NÚMEROS, no la redacción: el texto se arma al publicar
    # (`lectura_factor_detalle`). Si viniera escrito de acá, corregir una frase
    # obligaría a re-correr `validacion_externa`, que sale a la red — es la
    # misma convención que ya sigue el resto del panel, y romperla costó
    # publicar una versión vieja del texto.
    serie_factor = {p[0]: p[2] for p in niv["pares"]}
    aporte = regresion_validacion.aporte_sobre_tendencia(serie, serie_factor)
    if aporte.get("suficiente"):
        salida["aporte_sobre_tendencia"] = aporte

    salida["plano"] = plano_del_veredicto(salida)
    salida["pares_grafico"] = dif["pares"] if salida["plano"] == "diferencias" else niv["pares"]
    return salida


def _gana(r, mejor) -> bool:
    return r is not None and mejor is not None and abs(r) > mejor


def plano_del_veredicto(f: dict) -> str:
    """En qué plano se apoya el veredicto, y por lo tanto cuál hay que graficar.

    Un índice casi plano contra series con tendencia propia da ~0 en niveles.
    Dibujar ese plano mientras el encabezado informa el resultado de los cambios
    mes a mes deja un gráfico que contradice a su propio titular — el defecto
    que ya se corrigió una vez y que acá volvería por otra puerta.

    Por defecto se grafican los NIVELES: son más legibles y es el plano habitual.
    Se pasa a los cambios sólo cuando el veredicto descansa exclusivamente ahí.
    """
    if _gana(f.get("r_diferencias"), f.get("mejor_sola_diferencias")) \
            and not _gana(f.get("r_niveles"), f.get("mejor_sola_niveles")):
        return "diferencias"
    return "niveles"


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
    return (f"Contra el factor común de las {f['n_series']} estadísticas de su terreno —lo que "
            f"comparten, no una sola— el índice acompaña con {_coma(f['r_niveles'])} en niveles"
            + (f" y {_coma(f['r_diferencias'])} en los cambios mes a mes"
               if f["r_diferencias"] is not None else "")
            + f": {_veredicto(f)}.")


def _veredicto(f: dict) -> str:
    """Si el compuesto le gana o no a la mejor estadística individual, en cada
    plano. Manda el de los cambios mes a mes: en una muestra de treinta meses
    casi todas las series argentinas comparten la tendencia del período, así que
    ganar en niveles se consigue con mucho menos."""
    niv = _gana(f.get("r_niveles"), f.get("mejor_sola_niveles"))
    dif = _gana(f.get("r_diferencias"), f.get("mejor_sola_diferencias"))
    if niv and dif:
        return "más que cualquiera de ellas por separado, en los dos planos"
    if dif:
        return ("en los cambios mes a mes —la prueba exigente— más que cualquiera de ellas por "
                "separado")
    if niv:
        return "más que cualquiera de ellas por separado en niveles, pero no en los cambios"
    return "menos que la mejor de ellas por separado"


def lectura_factor_detalle(p: dict) -> list:
    """El desarrollo del factor para la ficha, en DOS párrafos: qué es y qué dio.

    Era de cinco y sobraban tres. Lo que explicaba cómo funciona el método —que
    los signos los fija el cálculo, que el índice no participa— pasó a `NOTA_FACTOR`,
    una línea al pie de la tabla de cargas: ahí se lee al lado de los números que
    describe, en vez de ser un párrafo que hay que atravesar para llegar a ellos.
    """
    f = p.get("factor")
    if not f or f["r_niveles"] is None:
        return []
    partes = [
        f"El contraste no es una estadística sola sino el factor común de las "
        f"{f['n_series']}: su primer componente principal, el método con el que la Reserva "
        f"Federal de Chicago arma su índice de actividad. Recoge {_coma(f['varianza_explicada'])}% "
        f"de lo que las {f['n_series']} tienen en común."
    ]
    mejor_n, mejor_d = f.get("mejor_sola_niveles"), f.get("mejor_sola_diferencias")
    if mejor_n is not None:
        gana_dif = (f.get("r_diferencias") is not None and mejor_d is not None
                    and abs(f["r_diferencias"]) > mejor_d)
        gana_niv = abs(f["r_niveles"]) > mejor_n
        tope = (f"La mejor de las {f['n_series']} por separado llega a "
                f"{_coma(round(mejor_n, 3))} en niveles"
                + (f" y {_coma(round(mejor_d, 3))} en los cambios" if mejor_d is not None else "")
                + ". ")
        if gana_dif and gana_niv:
            partes.append(tope + "El compuesto le gana a todas en los dos planos: lo que las "
                                 "estadísticas comparten —y no una en particular— es lo que el "
                                 "índice sigue.")
        elif gana_dif:
            partes.append(
                tope + "El compuesto le gana a todas en los cambios mes a mes, que es la prueba "
                       "exigente. En niveles queda por debajo porque este índice se movió muy "
                       "poco en términos netos —sus componentes se compensan— mientras que las "
                       "estadísticas del contraste tienen tendencia propia.")
        elif gana_niv:
            partes.append(tope + "El compuesto le gana en niveles pero no en los cambios mes a "
                                 "mes, que es la prueba exigente.")
        else:
            partes.append(tope + "El compuesto queda por debajo, y se publica igual: lo que las "
                                 "estadísticas comparten es un ciclo más ancho que el que el "
                                 "índice sigue.")
    aporte = f.get("aporte_sobre_tendencia")
    if aporte:
        reg = regresion_validacion.lectura(
            aporte, "positivo" if (f.get("r_niveles") or 0) > 0 else "negativo")
        if reg:
            partes.append(reg)
    return partes


# Va al pie de la tabla de cargas, no como párrafo: describe los números que
# tiene al lado. Es fijo porque describe el método, no el resultado del mes.
NOTA_FACTOR = ("El peso y el signo de cada estadística los fija el cálculo, no el autor: a la que "
               "se mueve al revés le sale carga negativa sola. Se estiman con las estadísticas "
               "externas únicamente —el índice no participa—, y por eso el contraste no se puede "
               "acomodar.")


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
