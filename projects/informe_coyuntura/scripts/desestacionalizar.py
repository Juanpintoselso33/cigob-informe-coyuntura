# -*- coding: utf-8 -*-
"""Ajuste estacional de series mensuales (ADR-0163).

POR QUÉ HACE FALTA. El panel de contraste del ITVC pasa a incluir volúmenes
físicos —demanda eléctrica residencial, gas residencial, transporte de pasajeros,
ventas de naftas— que traen estacionalidad fuerte: la luz sube en verano, el gas
en invierno, el transporte cae en enero. Las series de comercio, en cambio, ya
vienen desestacionalizadas por el INDEC. Mezclarlas crudas haría que el primer
componente principal del panel sea **la estación del año** en lugar de la
condición material de los hogares.

QUÉ HACE. Estima un factor multiplicativo fijo por mes calendario y lo divide.
El procedimiento es el clásico de cociente sobre media móvil:

  1. se pasa a logaritmos (la estacionalidad es proporcional, no aditiva);
  2. se le quita la tendencia con una media móvil **2×12** centrada —los dos
     extremos pesan la mitad—, que es la forma estándar de centrar una media de
     período par: una media simple de 13 meses contaría dos veces el mismo mes
     calendario y sesgaría la amplitud estimada (medido: 47,4% donde el patrón
     verdadero era 44,0%);
  3. el efecto de cada mes calendario es el promedio de lo que queda;
  4. se divide ese efecto.

QUÉ NO HACE. No es X-13-ARIMA-SEATS: no modela estacionalidad que cambia con los
años, ni efectos de calendario (Pascua, días hábiles), ni valores atípicos. Para
el gas residencial —que depende de cuán crudo viene el invierno, y no sólo de que
sea invierno— deja un residuo grande, y eso se mide y se declara en vez de
suponer que quedó limpio. `amplitud_estacional` existe justamente para poder
verificar el antes y el después, y hay un test que lo exige.

Se aplica a TODAS las series del panel por igual, no sólo a las que parecen
sucias: sobre una serie ya ajustada los factores estimados dan ~1 y la operación
es prácticamente la identidad, así que aplicarlo de más no distorsiona y evita
tener que decidir a ojo cuál necesita ajuste.
"""

import math
import statistics as st

VENTANA = 13          # media móvil centrada: 6 meses a cada lado
MINIMO_MESES = 36     # tres años: menos que eso no estima 12 efectos mensuales


def _efectos(serie: dict):
    """Efecto logarítmico de cada mes calendario, o None si no alcanza."""
    positivos = {m: v for m, v in serie.items() if v and v > 0}
    if len(positivos) < MINIMO_MESES:
        return None
    logs = {m: math.log(v) for m, v in positivos.items()}
    meses = sorted(logs)
    lado = VENTANA // 2
    desvios = {}
    for i in range(lado, len(meses) - lado):
        # media móvil 2×12: los extremos con peso 1/2, el resto con peso 1
        centro = (0.5 * logs[meses[i - lado]] + 0.5 * logs[meses[i + lado]]
                  + sum(logs[meses[j]] for j in range(i - lado + 1, i + lado))) / 12.0
        desvios[meses[i]] = logs[meses[i]] - centro
    if not desvios:
        return None
    por_mes = {}
    for ym, d in desvios.items():
        por_mes.setdefault(ym[5:7], []).append(d)
    efectos = {mes: st.mean(vs) for mes, vs in por_mes.items() if vs}
    # se centran para que el ajuste no corra el nivel de la serie
    medio = st.mean(efectos.values())
    return {mes: e - medio for mes, e in efectos.items()}


def amplitud_estacional(serie: dict):
    """Cuánto separa al mes más alto del más bajo, en %. `None` si no se puede
    estimar. Sirve para verificar que el ajuste efectivamente hizo algo."""
    efectos = _efectos(serie)
    if not efectos:
        return None
    return round(100 * (max(efectos.values()) - min(efectos.values())), 1)


def desestacionalizar(serie: dict) -> dict:
    """Serie sin el efecto fijo de cada mes calendario.

    Si no hay historia suficiente para estimarlo, devuelve la serie tal cual: es
    preferible un contraste con estacionalidad declarada a uno ajustado con
    factores estimados sobre dos años.
    """
    efectos = _efectos(serie)
    if not efectos:
        return dict(serie)
    return {m: v / math.exp(efectos.get(m[5:7], 0.0)) for m, v in serie.items()}
