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


BASE_MESES = ('2023-10', '2023-11', '2023-12')   # 4º trimestre de 2023


def base_4t2023(serie):
    """Promedio del 4T-2023 de {YYYY-MM: nivel}; exige los tres meses."""
    faltan = [m for m in BASE_MESES if m not in serie]
    if faltan:
        raise ValueError(f'base 4T-2023 incompleta (faltan {faltan})')
    return sum(serie[m] for m in BASE_MESES) / 3.0


def indice_real(alquiler, general):
    """{YYYY-MM: alquiler real} con 100 = 4T-2023, desde oct-2023.

    100 x (alquiler_t / alquiler_base) / (general_t / general_base): cuánto se
    encareció el alquiler del IPC contra el resto de los precios del mismo
    aglomerado. Por encima de 100 = más caro en términos reales. Es la misma
    cuenta que puntúa (`itvc_alquiler`) puesta del lado de la lectura: aquel es
    100 x base / real, de modo que >100 = alivio."""
    a_base, g_base = base_4t2023(alquiler), base_4t2023(general)
    return {ym: round(100.0 * (alquiler[ym] / a_base) / (general[ym] / g_base), 2)
            for ym in sorted(set(alquiler) & set(general))
            if ym >= BASE_MESES[0] and alquiler[ym] and general[ym]}


def tarjeta():
    n = niveles()
    serie = indice_real(n['alquiler'], n['general'])
    ultimo = max(serie)
    return {'valor': serie[ultimo], 'fecha': ultimo + '-01', 'fuente_url': URL}
