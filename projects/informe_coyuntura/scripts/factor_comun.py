# -*- coding: utf-8 -*-
"""Factor común de un panel de estadísticas: PRIMER COMPONENTE PRINCIPAL (ADR-0161).

DE DÓNDE SALE. Es el método con el que la Reserva Federal de Chicago construye el
CFNAI: un índice único armado como el **primer componente principal de 85 series**
de actividad, cada una llevada a estacionariedad, centrada y estandarizada antes
de entrar. Stock y Watson lo formalizaron antes como **modelo de factor**: cada
serie es una parte común —el factor que comparten todas— más una parte propia.

QUÉ PROBLEMA RESUELVE ACÁ. Contrastar un índice contra **una sola** estadística
mide una faceta y se publica como si midiera el todo. La salida obvia —promediar
varias— exige decidir a mano qué serie va invertida (la incertidumbre sube cuando
las otras bajan) y con qué peso entra cada una. Esas dos decisiones a mano son
justamente por donde se cuela el ajuste: quien elige los signos ya vio los
resultados. **Las cargas del factor las resuelven solas**: a la serie que se
mueve al revés que el factor le sale carga negativa, y a la que es sobre todo
ruido propio le sale carga chica, en lugar de dejarla cancelar la señal ajena.

POR QUÉ NO ES CIRCULAR. Las cargas se estiman **con el panel externo solamente**.
El índice no participa del cálculo del factor: recién aparece después, cuando se
lo correlaciona contra el factor ya armado. No hay ningún grado de libertad
tocado para que el resultado dé mejor.

CÓMO SE DIAGONALIZA. Por rotaciones de Jacobi, que para una matriz simétrica es
exacto y determinista. La iteración de potencia —el atajo habitual— **no sirve
acá**: arrancando del vector (1,1,…) queda clavada cuando ese vector ya es un
autovector, y entonces devuelve cargas todas positivas aunque las series estén
correlacionadas negativamente entre sí. Con dos series pasaba siempre.

CUÁNTAS SERIES HACEN FALTA. Con dos, el "factor" es un promedio con el signo de
una única correlación: no hay nada que estimar y basta que una de las dos falle
para darlo vuelta. Se exige un mínimo de tres.
"""

import statistics as st

MINIMO_SERIES = 3
MINIMO_MESES = 12


def _jacobi(A, iteraciones: int = 100, tol: float = 1e-12):
    """Autovalores y autovectores de una matriz simétrica, por rotaciones de Jacobi.

    Devuelve (autovalores, autovectores) con autovectores[i] el i-ésimo vector.
    Exacto y determinista: a diferencia de la iteración de potencia, no depende
    de un vector inicial ni puede quedarse clavado en un autovector no dominante.
    """
    n = len(A)
    A = [fila[:] for fila in A]
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(iteraciones):
        p, q, mayor = 0, 1, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(A[i][j]) > mayor:
                    p, q, mayor = i, j, abs(A[i][j])
        if mayor < tol:
            break
        theta = 0.5 * (A[q][q] - A[p][p]) / A[p][q]
        t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + (theta * theta + 1.0) ** 0.5)
        c = 1.0 / (t * t + 1.0) ** 0.5
        s = t * c
        for k in range(n):
            akp, akq = A[k][p], A[k][q]
            A[k][p], A[k][q] = c * akp - s * akq, s * akp + c * akq
        for k in range(n):
            apk, aqk = A[p][k], A[q][k]
            A[p][k], A[q][k] = c * apk - s * aqk, s * apk + c * aqk
        for k in range(n):
            vkp, vkq = V[k][p], V[k][q]
            V[k][p], V[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [A[i][i] for i in range(n)], [[V[i][j] for i in range(n)] for j in range(n)]


def _estandarizar(serie: dict) -> dict:
    """Centrada y estandarizada, como entran las series al CFNAI."""
    vals = list(serie.values())
    if len(vals) < 2:
        return {}
    d = st.pstdev(vals)
    if d == 0:
        return {}
    m = st.mean(vals)
    return {k: (v - m) / d for k, v in serie.items()}


def _difs(serie: dict) -> dict:
    fs = sorted(serie)
    return {fs[i]: serie[fs[i]] - serie[fs[i - 1]] for i in range(1, len(fs))}


def primer_componente(series: dict) -> dict | None:
    """Primer componente principal de un panel de series mensuales {clave: {mes: valor}}.

    Devuelve las cargas de cada serie, el porcentaje de varianza que el factor
    explica y el propio factor mes a mes. `None` si el panel no alcanza.
    """
    usables = {k: v for k, v in series.items() if v}
    if len(usables) < MINIMO_SERIES:
        return None
    claves = sorted(usables)
    meses = sorted(set.intersection(*[set(usables[k]) for k in claves]))
    if len(meses) < MINIMO_MESES:
        return None

    Z = []
    for k in claves:
        z = _estandarizar({m: usables[k][m] for m in meses})
        if not z:
            return None
        Z.append([z[m] for m in meses])

    n, T = len(Z), len(meses)
    C = [[sum(Z[a][t] * Z[b][t] for t in range(T)) / T for b in range(n)] for a in range(n)]
    autovalores, autovectores = _jacobi(C)
    i = max(range(n), key=lambda k: autovalores[k])
    v, lam = autovectores[i], autovalores[i]

    # ORIENTACIÓN. El signo de un autovector es arbitrario, así que hay que
    # fijarlo con una regla y no a ojo: el factor apunta en el sentido de la
    # serie que más pesa. Determinista y estable ante reordenamientos.
    dominante = max(range(n), key=lambda k: (abs(v[k]), -k))
    if v[dominante] < 0:
        v = [-x for x in v]

    factor = {meses[t]: sum(v[a] * Z[a][t] for a in range(n)) for t in range(T)}
    return {
        "cargas": {claves[a]: round(v[a], 3) for a in range(n)},
        "varianza_explicada": round(100.0 * lam / n, 1),
        "n_series": n,
        "n": T,
        "factor": factor,
    }


def contraste(serie_indice: dict, series: dict, en_diferencias: bool = False):
    """Factor común del panel y correlación del índice contra él.

    Con `en_diferencias`, las series se llevan a variación mes a mes ANTES de
    estandarizar y extraer el factor —el paso a estacionariedad del CFNAI— y el
    índice se compara también en diferencias.
    """
    panel = {k: _difs(v) for k, v in series.items()} if en_diferencias else series
    fc = primer_componente(panel)
    if fc is None:
        return None
    izq = _difs(serie_indice) if en_diferencias else serie_indice
    comunes = sorted(set(izq) & set(fc["factor"]))
    if len(comunes) < MINIMO_MESES:
        return None
    xs = [izq[m] for m in comunes]
    ys = [fc["factor"][m] for m in comunes]
    mx, my = st.mean(xs), st.mean(ys)
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (dx * dy)
    return {
        "r": round(r, 3),
        "n": len(comunes),
        "cargas": fc["cargas"],
        "varianza_explicada": fc["varianza_explicada"],
        "n_series": fc["n_series"],
        # el índice y el factor mes a mes, para poder graficar la comparación
        # que el número resume: un titular que no se corresponde con la curva
        # que tiene debajo es peor que no publicarlo.
        "pares": [[m, round(izq[m], 3), round(fc["factor"][m], 3)] for m in comunes],
    }
