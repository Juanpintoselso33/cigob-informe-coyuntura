"""ICA original: API histórica completada por el cuadro oficial vigente.

Las series original, desestacionalizada y tendencia-ciclo no son intercambiables.
El cuadro 1 conserva los originales de los dos años y sus revisiones.
"""
import json
import math
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
import xlrd

CATALOGO = 'https://www.indec.gob.ar/Nivel4/Tema/3/2/40'
STORE = Path(__file__).resolve().parents[1] / 'data/macro/ica_mensual.json'
MESES = {m: i for i, m in enumerate(('enero', 'febrero', 'marzo', 'abril', 'mayo',
    'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'), 1)}


def enlaces(html):
    rutas = re.findall(r'''["']([^"']*ica_cuadros_(\d{2})_(\d{2})_(\d{2})\.xls)["']''', html)
    return [urljoin('https://www.indec.gob.ar/', r[0]) for r in
            sorted(rutas, key=lambda r: (r[3], r[2], r[1]), reverse=True)]


def parsear(contenido):
    libro = xlrd.open_workbook(file_contents=contenido)
    hoja = next((s for s in libro.sheets()
                  if 'Cuadro 1.' in str(s.cell_value(0, 0))
                  and 'Intercambio comercial' in str(s.cell_value(0, 0))), None)
    if hoja is None:
        raise ValueError('ICA: no se encontró el cuadro 1 de intercambio comercial')
    filas = [hoja.row_values(r) for r in range(hoja.nrows)]
    encabezado = next((i for i, f in enumerate(filas)
                       if 'Exportaciones' in f and 'Importaciones' in f), None)
    if encabezado is None:
        raise ValueError('ICA: faltan columnas de exportaciones/importaciones')
    ce, ci = filas[encabezado].index('Exportaciones'), filas[encabezado].index('Importaciones')
    anos = []
    for col in (ce, ce + 1):
        m = re.fullmatch(r'(20\d{2})\s*[e*]?', str(filas[encabezado + 1][col]).strip())
        if not m:
            raise ValueError('ICA: año de la columna original no reconocido')
        anos.append(int(m[1]))
    if anos[0] != anos[1] + 1:
        raise ValueError('ICA: años no consecutivos')
    puntos = {}
    for f in filas[encabezado + 2:]:
        mes = next((MESES[str(c).strip().lower()] for c in f[:ce]
                    if str(c).strip().lower() in MESES), None)
        if mes is None:
            continue
        for offset, anio in enumerate(anos):
            ex, im = f[ce + offset], f[ci + offset]
            if ex in ('', '///') and im in ('', '///'):
                continue
            if not all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in (ex, im)):
                raise ValueError('ICA: par exportaciones/importaciones inválido')
            ym = f'{anio}-{mes:02}-01'
            if ym in puntos:
                raise ValueError(f'ICA: mes repetido {ym}')
            puntos[ym] = [float(ex), float(im)]
    if len([m for m in puntos if m.startswith(str(anos[1]))]) != 12:
        raise ValueError('ICA: año anterior incompleto')
    if len(puntos) < 13:
        raise ValueError('ICA: no hay observaciones del año vigente')
    return puntos


def completar(expo, impo):
    """Devuelve puntos [fecha, expo, impo], procedencia y estado de consulta.

    Un fallo del portal conserva el último cuadro validado; no hace retroceder
    silenciosamente julio a junio. El cache no acredita actualidad de la fuente.
    """
    anterior = json.loads(STORE.read_text()) if STORE.exists() else {}
    actual, aviso = anterior, None
    try:
        r = requests.get(CATALOGO, timeout=30)
        r.raise_for_status()
        urls = enlaces(r.text)
        if not urls:
            raise ValueError('ICA: catálogo sin planilla original enlazada')
        r = requests.get(urls[0], timeout=30)
        r.raise_for_status()
        puntos = parsear(r.content)
        if anterior.get('mensual') and max(puntos) < max(anterior['mensual']):
            raise ValueError('ICA: el catálogo retrocedió respecto al cuadro guardado')
        actual = {'url': urls[0], 'consultado': datetime.now().astimezone().isoformat(), 'mensual': puntos}
        STORE.parent.mkdir(parents=True, exist_ok=True)
        STORE.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + '\n')
    except (requests.RequestException, ValueError, xlrd.XLRDError) as exc:
        aviso = str(exc)
    if aviso and not actual.get('mensual'):
        raise ValueError(f'ICA: sin cuadro validado para conservar: {aviso}')
    ei, ii = dict(expo), dict(impo)
    pares = {f: [e, ii[f]] for f, e in ei.items() if e is not None and ii.get(f) is not None}
    pares.update(actual.get('mensual', {}))
    return {'puntos': [[f, *v] for f, v in sorted(pares.items(), reverse=True)],
            'url': actual.get('url'), 'advertencia': aviso,
            'obtenido_en': actual.get('consultado'),
            'consulta_oficial_exitosa': aviso is None}


def ventana(puntos, n):
    datos = puntos[:n]
    if len(datos) != n:
        raise ValueError(f'ICA: se necesitan {n} meses, hay {len(datos)}')
    meses = [int(f[:4])*12 + int(f[5:7]) for f, *_ in datos]
    if any(a - b != 1 for a, b in zip(meses, meses[1:])):
        raise ValueError('ICA: meses no consecutivos; no se publica una ventana con huecos')
    return datos
