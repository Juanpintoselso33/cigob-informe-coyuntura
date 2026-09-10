"""Calendario del agregado ACLED: week es sábado inicial, hasta el viernes."""
import calendar
from datetime import date, timedelta
import math
import re


def cobertura_hasta(store, hoy=None):
    inicio = date.fromisoformat(store['_meta']['hasta_semana'])
    if inicio.weekday() != 5:
        raise ValueError('ACLED: week debe ser un sábado')
    fin = inicio + timedelta(days=6)
    if fin > (hoy or date.today()):
        raise ValueError('ACLED: semana aún no cerrada')
    return fin


def meses_completos(store, clave, hoy=None):
    """Meses de INICIO de semanas completos, no conteos por fecha del evento."""
    fin = cobertura_hasta(store, hoy)
    mensual = store[clave]
    meses = sorted(mensual)
    anterior = None
    completos = []
    for ym in meses:
        if not re.fullmatch(r'\d{4}-\d{2}', ym):
            raise ValueError('ACLED: mes inválido')
        primero = date.fromisoformat(ym+'-01')
        ordinal = primero.year * 12 + primero.month
        if anterior is not None and ordinal - anterior != 1:
            raise ValueError('ACLED: calendario mensual incompleto')
        anterior = ordinal
        n = mensual[ym]
        if not isinstance(n, (int,float)) or not math.isfinite(n) or n < 0 or int(n) != n:
            raise ValueError('ACLED: conteo inválido')
        ultimo = date(primero.year, primero.month, calendar.monthrange(primero.year, primero.month)[1])
        if ultimo <= fin:
            completos.append(ym)
    return completos


def serie_12m(store, clave, hoy=None):
    meses = meses_completos(store, clave, hoy)
    mensual = store[clave]
    base_meses = [f'2023-{m:02d}' for m in range(1,13)]
    if not set(base_meses) <= set(meses):
        raise ValueError('ACLED: base 2023 incompleta')
    base = sum(mensual[m] for m in base_meses)
    if base <= 0:
        raise ValueError('ACLED: base 2023 no positiva')
    puntos=[]
    for i, ym in enumerate(meses):
        if ym < '2023-12' or i < 11:
            continue
        total=sum(mensual[m] for m in meses[i-11:i+1])
        puntos.append({'fecha':ym+'-01', 'acum_12m':total,
                       'variacion':round(100*(total/base-1),1)})
    if not puntos:
        raise ValueError('ACLED: sin ventana completa de doce meses')
    return {'base_2023':base, 'puntos':puntos,
            'cobertura_hasta':cobertura_hasta(store,hoy).isoformat()}
