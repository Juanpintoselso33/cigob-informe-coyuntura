# -*- coding: utf-8 -*-
"""Puntos de giro y concordancia de fase (ADR-0158).

POR QUÉ. Las guías UNECE/ONU sobre indicadores compuestos parten la familia en
dos: los **económicos** tienen una serie de referencia y se validan por su
relación de adelanto/coincidencia/rezago con ella; los **socioeconómicos**
normalmente no la tienen y se comparan contra varias estadísticas relacionadas.
El ITCM es del primer tipo, y el sistema de indicadores líderes de la OCDE lo
valida así: no por correlación de Pearson sobre niveles —que en una muestra
corta y con tendencia común dice poco— sino por **puntos de giro**: dónde el
ciclo cambia de dirección, con cuánto adelanto y con cuántas señales falsas.

QUÉ IMPLEMENTA. Una versión simplificada de Bry-Boschan (NBER):

  1. ciclo = desviación de la tendencia (media móvil centrada);
  2. extremos locales;
  3. **alternancia** (entre dos picos queda el más alto) y **duración mínima de
     fase**, ITERADAS hasta converger.

El paso 3 es el que hay que hacer bien y no es obvio: aplicar la alternancia una
vez y después el filtro de fase la vuelve a romper — el primer intento producía
secuencias valle-valle y pico-pico-pico. Las dos reglas tienen que converger
juntas, y por eso el bucle. `alternan()` existe para poder afirmarlo en un test.

LO QUE NO ES. El sistema de la OCDE estima la tendencia con una media móvil de
75 meses (método PAT) y puede permitirse descartar ciclos cortos. Con series de
~30 meses eso es imposible: acá la ventana es de 13 meses y la fase mínima de 5.
Es la adaptación honesta a la muestra que hay, no el procedimiento completo, y
los resultados hay que leerlos con el número de giros a la vista.
"""


def _ord(ym: str) -> int:
    """Mes como entero, para restar fechas."""
    return int(ym[:4]) * 12 + int(ym[5:7])


def ciclo(serie: dict, ventana: int = 13) -> dict:
    """Desviación de la tendencia: la serie menos su media móvil centrada.

    Ventana impar. En los bordes la media se calcula con los meses disponibles,
    así que los extremos de la serie son menos confiables — igual que en el
    sistema original, donde los giros cerca del final son provisorios.
    """
    fs = sorted(serie)
    k = ventana // 2
    out = {}
    for i, f in enumerate(fs):
        lo, hi = max(0, i - k), min(len(fs), i + k + 1)
        tend = sum(serie[fs[j]] for j in range(lo, hi)) / (hi - lo)
        out[f] = round(serie[f] - tend, 4)
    return out


def _extremos(c: dict) -> list:
    fs = sorted(c)
    out = []
    for i in range(1, len(fs) - 1):
        a, b, d = c[fs[i - 1]], c[fs[i]], c[fs[i + 1]]
        if b == a == d:
            continue
        if b >= a and b >= d:
            out.append([fs[i], "pico", b])
        elif b <= a and b <= d:
            out.append([fs[i], "valle", b])
    return out


def _alternar(tps: list) -> list:
    """Entre dos giros consecutivos del mismo tipo queda el más extremo."""
    out = []
    for tp in tps:
        if out and out[-1][1] == tp[1]:
            mas_extremo = ((tp[1] == "pico" and tp[2] > out[-1][2])
                           or (tp[1] == "valle" and tp[2] < out[-1][2]))
            if mas_extremo:
                out[-1] = tp
        else:
            out.append(tp)
    return out


def _quitar_fase_corta(tps: list, fase_min: int):
    """Saca el menos prominente del primer par que forma una fase muy corta."""
    for i in range(len(tps) - 1):
        if _ord(tps[i + 1][0]) - _ord(tps[i][0]) < fase_min:
            fuera = i if abs(tps[i][2]) < abs(tps[i + 1][2]) else i + 1
            return tps[:fuera] + tps[fuera + 1:], True
    return tps, False


def _amplitud_suficiente(tps: list, c: dict, minimo_rel: float) -> list:
    """Descarta giros de amplitud despreciable.

    Sin esto, una serie SIN ciclo (monótona) devuelve giros: la media móvil
    centrada usa menos meses en los bordes, y esa asimetría produce extremos de
    amplitud ~0 que no son giros de nada.
    """
    if not c:
        return tps
    escala = max(c.values()) - min(c.values())
    if escala <= 0:
        return []
    return [tp for tp in tps if abs(tp[2]) >= minimo_rel * escala]


def giros(c: dict, fase_min: int = 5, amplitud_min: float = 0.05) -> list:
    """[(mes, 'pico'|'valle', amplitud)] alternados y con fase mínima."""
    tps = _amplitud_suficiente(_extremos(c), c, amplitud_min)
    for _ in range(100):
        tps = _alternar(tps)
        tps, hubo_cambio = _quitar_fase_corta(tps, fase_min)
        if not hubo_cambio:
            break
    return _alternar(tps)


def provisorio(mes: str, c: dict, ventana: int = 13) -> bool:
    """Un giro a menos de media ventana de un extremo de la serie NO se puede
    confirmar: ahí la tendencia se estima con datos incompletos.

    El sistema de la OCDE trata así los giros recientes, y por eso los publica
    como provisorios hasta que entran más meses.
    """
    fs = sorted(c)
    if not fs:
        return True
    k = ventana // 2
    return _ord(mes) - _ord(fs[0]) < k or _ord(fs[-1]) - _ord(mes) < k


def alternan(tps: list) -> bool:
    """Invariante que el algoritmo debe cumplir siempre; se testea."""
    return all(tps[i][1] != tps[i + 1][1] for i in range(len(tps) - 1))


def fases(c: dict, tps: list) -> dict:
    """{mes: +1 expansión | −1 contracción}, desde el primer giro en adelante."""
    if not tps:
        return {}
    out, estado, idx = {}, None, 0
    for f in sorted(c):
        while idx < len(tps) and tps[idx][0] <= f:
            estado = -1 if tps[idx][1] == "pico" else 1
            idx += 1
        if estado is not None:
            out[f] = estado
    return out


def concordancia(fa: dict, fb: dict):
    """(fracción de meses en la misma fase, n). El estadístico de Harding-Pagan.

    0,5 es lo que daría el azar; 1 es coincidencia perfecta.
    """
    comunes = sorted(set(fa) & set(fb))
    if not comunes:
        return None, 0
    iguales = sum(1 for m in comunes if fa[m] == fb[m])
    return round(iguales / len(comunes), 3), len(comunes)


def aparear(tps_a: list, tps_b: list, ventana: int = 6) -> list:
    """Empareja cada giro de A con el del MISMO tipo más cercano de B.

    Devuelve [(mes_a, tipo, mes_b|None, desfase)] donde el desfase es positivo
    cuando A se adelanta a B.
    """
    out = []
    for f, t, _ in tps_a:
        cand = [(_ord(fb) - _ord(f), fb) for fb, tb, _ in tps_b
                if tb == t and abs(_ord(fb) - _ord(f)) <= ventana]
        if cand:
            d, fb = min(cand, key=lambda x: abs(x[0]))
            out.append((f, t, fb, d))
        else:
            out.append((f, t, None, None))
    return out


def analisis(serie: dict, referencia: dict, ventana: int = 13,
             fase_min: int = 5) -> dict:
    """Análisis completo de una serie contra su referencia."""
    c_a, c_b = ciclo(serie, ventana), ciclo(referencia, ventana)
    g_a, g_b = giros(c_a, fase_min), giros(c_b, fase_min)
    conc, n = concordancia(fases(c_a, g_a), fases(c_b, g_b))
    pares = aparear(g_a, g_b)
    prov = {f for f, _, _ in g_a if provisorio(f, c_a, ventana)}
    # el desfase medio se calcula SÓLO con giros confirmados: uno provisorio
    # puede moverse varios meses cuando entren datos nuevos
    desfases = [d for f, _, fb, d in pares if fb is not None and f not in prov]
    return {
        "giros": [{"mes": f, "tipo": t, "amplitud": round(v, 2),
                   "provisorio": f in prov} for f, t, v in g_a],
        "giros_referencia": [{"mes": f, "tipo": t} for f, t, _ in g_b],
        "concordancia": conc,
        "n_meses": n,
        "pares": [{"mes": f, "tipo": t, "referencia": fb, "desfase": d}
                  for f, t, fb, d in pares],
        "desfase_medio": round(sum(desfases) / len(desfases), 1) if desfases else None,
        "apareados": len(desfases),
        "provisorios": len(prov),
        "sin_par": sum(1 for _, _, fb, _ in pares if fb is None),
    }
