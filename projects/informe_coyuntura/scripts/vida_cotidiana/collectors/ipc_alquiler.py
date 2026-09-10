"""Alquiler y nivel general GBA desde el libro original INDEC."""
from datetime import date
import math
import unicodedata

import requests
import xlrd

URL = 'https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls'


def _normalizar(x):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(x))
                           if not unicodedata.combining(c)).lower().split())


def parsear(contenido, hoy=None):
    hoy = hoy or date.today()
    libro = xlrd.open_workbook(file_contents=contenido)
    hojas = [s for s in libro.sheets() if _normalizar(s.name) == 'indices aperturas']
    if len(hojas) != 1:
        raise ValueError('Hoja de niveles IPC ausente o ambigua')
    hoja = hojas[0]
    cabeceras = [i for i in range(hoja.nrows)
                 if _normalizar(hoja.cell_value(i, 0)) == 'region gba']
    if len(cabeceras) != 1:
        raise ValueError('Región GBA ausente o ambigua')
    inicio = cabeceras[0]
    fin = next((i for i in range(inicio+1, hoja.nrows)
                if _normalizar(hoja.cell_value(i, 0)).startswith('region ')), hoja.nrows)
    filas = {}
    for concepto in ['alquiler de la vivienda', 'nivel general']:
        indices = [i for i in range(inicio+1, fin)
                   if _normalizar(hoja.cell_value(i, 0)) == concepto]
        if len(indices) != 1:
            raise ValueError(f'Concepto GBA ausente o ambiguo: {concepto}')
        filas[concepto] = indices[0]
    salida = {'alquiler': {}, 'general': {}}
    anterior = None
    for j in range(1, hoja.ncols):
        bruto = hoja.cell_value(inicio, j)
        if bruto == '':
            if any(hoja.cell_value(i, j) != '' for i in filas.values()):
                raise ValueError('Valor sin fecha en IPC')
            continue
        fecha = xlrd.xldate_as_datetime(bruto, libro.datemode).date()
        ordinal = fecha.year*12+fecha.month
        # El libro es mensual; algunas cabeceras Excel llevan un día distinto
        # de 1 (marzo de 2026, por ejemplo). Se valida el mes calendario.
        if anterior is not None and ordinal != anterior+1:
            raise ValueError('Meses IPC duplicados, desordenados o discontinuos')
        if ordinal >= hoy.year*12+hoy.month:
            raise ValueError('IPC contiene un mes no cerrado')
        anterior = ordinal
        for clave, concepto in [('alquiler', 'alquiler de la vivienda'), ('general', 'nivel general')]:
            valor = float(hoja.cell_value(filas[concepto], j))
            if not math.isfinite(valor) or valor <= 0:
                raise ValueError('Nivel IPC ausente, no finito o no positivo')
            salida[clave][fecha.strftime('%Y-%m')] = valor
    if len(salida['alquiler']) < 2:
        raise ValueError('IPC sin dos meses para comparar')
    return salida


def niveles():
    r = requests.get(URL, timeout=40)
    r.raise_for_status()
    return parsear(r.content)


def tarjeta():
    serie = niveles()['alquiler']
    meses = sorted(serie)
    actual, previo = meses[-2:][::-1]
    return {'valor': serie[actual], 'fecha': actual+'-01',
            'variacion_mensual_pct': 100*(serie[actual]/serie[previo]-1),
            'fuente_url': URL}
