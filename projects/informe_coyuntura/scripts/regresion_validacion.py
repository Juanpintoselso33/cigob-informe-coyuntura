# -*- coding: utf-8 -*-
"""Vínculos por regresión (ADR-0162) — el paso 9 del handbook, completo.

El paso 9 del handbook OCDE/JRC pide correlacionar con otros indicadores **y**
«identificar vínculos mediante regresiones». Lo primero ya está (ADR-0155, 0159);
esto es lo segundo, y no es un adorno: **ataca el problema que aparece en todas
las mediciones de este proyecto — que en estos años casi todas las series
argentinas comparten la tendencia del período**, así que una correlación alta
puede ser sólo eso.

La pregunta que responde: *¿el índice explica algo del contraste externo que una
simple tendencia temporal no explique ya?*

  modelo A:  externa = a + b·t
  modelo B:  externa = a + b·t + c·índice

y se reporta el **aporte incremental de R²** entre los dos. Si el índice sólo
aportara tendencia, el aporte sería ~0 por construcción, porque el modelo A ya
la tiene.

Mínimos cuadrados resuelto a mano (eliminación gaussiana sobre las ecuaciones
normales): son tres parámetros y no justifica una dependencia nueva. La
implementación se verifica contra casos de respuesta conocida en los tests
—ajuste perfecto, predictor irrelevante, colinealidad— porque una regresión mal
resuelta es peor que no tenerla: publica un número con aire de autoridad.
"""


def _resolver(A: list, b: list):
    """Sistema lineal por eliminación gaussiana con pivoteo parcial."""
    n = len(A)
    M = [list(fila) + [b[i]] for i, fila in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return None                      # singular: predictores colineales
        M[col], M[piv] = M[piv], M[col]
        for fila in range(n):
            if fila == col:
                continue
            factor = M[fila][col] / M[col][col]
            for k in range(col, n + 1):
                M[fila][k] -= factor * M[col][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def ols(y: list, columnas: list):
    """(coeficientes, R²) de y sobre las columnas dadas más una constante."""
    n = len(y)
    X = [[1.0] + [col[i] for col in columnas] for i in range(n)]
    k = len(X[0])
    if n <= k:
        return None, None
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    coef = _resolver(XtX, Xty)
    if coef is None:
        return None, None
    media = sum(y) / n
    sct = sum((v - media) ** 2 for v in y)
    if sct == 0:
        return coef, None
    scr = sum((y[i] - sum(coef[a] * X[i][a] for a in range(k))) ** 2 for i in range(n))
    return coef, round(1 - scr / sct, 3)


def aporte_sobre_tendencia(indice: dict, externa: dict, min_meses: int = 18) -> dict:
    """¿Cuánto explica el índice del contraste externo, descontada la tendencia?

    Devuelve el R² de la tendencia sola, el del modelo con el índice, el aporte
    incremental y el signo del coeficiente del índice.
    """
    meses = sorted(set(indice) & set(externa))
    n = len(meses)
    if n < min_meses:
        return {"n": n, "suficiente": False}
    t = [float(i) for i in range(n)]
    x = [indice[m] for m in meses]
    y = [externa[m] for m in meses]
    _, r2_tend = ols(y, [t])
    if r2_tend is None:
        return {"n": n, "suficiente": False}
    coef, r2_full = ols(y, [t, x])
    if r2_full is None:
        # El modelo completo sale singular cuando el índice es una función lineal
        # exacta del tiempo. Eso NO es falta de datos: es el caso que motiva la
        # prueba, y la respuesta es que el índice no agrega nada a la tendencia.
        # Devolver «insuficiente» acá haría que la función se callara justo
        # cuando el resultado importa.
        return {"n": n, "suficiente": True, "colineal": True,
                "r2_tendencia": r2_tend, "r2_con_indice": r2_tend,
                "aporte": 0.0, "signo": "nulo", "coef": 0.0}
    return {
        "n": n,
        "suficiente": True,
        "colineal": False,
        "r2_tendencia": r2_tend,
        "r2_con_indice": r2_full,
        "aporte": round(r2_full - r2_tend, 3),
        "signo": ("positivo" if coef[2] > 0 else "negativo" if coef[2] < 0 else "nulo"),
        "coef": round(coef[2], 4),
    }


def lectura(r: dict, esperado: str = "positivo") -> str:
    """Texto público del aporte incremental."""
    if not r.get("suficiente"):
        return ""
    coma = lambda x: str(x).replace(".", ",").replace("-", "−")
    pct = lambda v: coma(round(100 * v))
    base = (f"Queda una prueba más, la que separa explicar de acompañar: una simple tendencia "
            f"temporal ya da cuenta del {pct(r['r2_tendencia'])}% de lo que hace el contraste "
            f"externo, porque en estos años casi todo se movió en la misma dirección. ")
    if r.get("colineal"):
        return base + ("El índice, en este período, no es más que esa misma tendencia: no se "
                       "distingue de ella, así que no hay nada que pueda agregarle. Se publica "
                       "porque es el resultado, no porque confirme.")
    if r["aporte"] <= 0.02:
        return base + (f"Sumar el índice a esa tendencia no agrega prácticamente nada "
                       f"({pct(r['aporte'])} puntos porcentuales): en este período el índice no "
                       f"explica el contraste más allá de lo que explica el paso del tiempo. Se "
                       f"publica porque es el resultado, no porque confirme.")
    calidad = "signo esperado" if r["signo"] == esperado else "signo CONTRARIO al esperado"
    extra = (f"Sumar el índice lleva ese poder explicativo al {pct(r['r2_con_indice'])}%: aporta "
             f"{pct(r['aporte'])} puntos porcentuales por encima de la tendencia, con el "
             f"{calidad}.")
    if r["signo"] != esperado:
        extra += (" Un aporte con el signo cambiado no valida: indica que el índice y el "
                  "contraste se mueven en direcciones opuestas una vez quitada la tendencia, y "
                  "hay que mirarlo.")
    return base + extra
