"""TIREA publicada en gacetillas de meses cerrados con cobertura revisada.

Complementa meses posteriores al corte anual. No combina una muestra de
licitaciones con un mes parcial ni agrega CER, dólar linked o moneda extranjera.
"""
import json
import math
import re
import unicodedata
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

MANIFIESTO = Path(__file__).resolve().parents[1] / 'data/macro/colocaciones_complementarias.json'
MESES = ('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre').split()


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(texto))
                           if not unicodedata.combining(c)).lower().split())


def numero(texto):
    # Notas al pie (*) no forman parte del importe.
    limpio = re.sub(r'\([^)]*\)', '', texto).replace('$', '').replace('%', '').strip()
    valor = float(limpio.replace('.', '').replace(',', '.').replace(' ', ''))
    if not math.isfinite(valor):
        raise ValueError('Importe/tasa no finito')
    return valor


def fecha_textual(iso):
    f = date.fromisoformat(iso)
    return f'{f.day} de {MESES[f.month-1]} de {f.year}'


def parsear_resultado(html, registro):
    soup = BeautifulSoup(html, 'html.parser')
    texto = normalizar(soup.get_text(' ', strip=True))
    if fecha_textual(registro['fecha']) not in texto:
        raise ValueError('La fecha del resultado no coincide con la licitación')
    tablas = []
    for tabla in soup.find_all('table'):
        filas = tabla.find_all('tr')
        if not filas:
            continue
        cab = [normalizar(c.get_text(' ', strip=True)) for c in filas[0].find_all(['th', 'td'])]
        if cab and re.fullmatch(r'instrumentos? a tasa fija', cab[0]):
            tablas.append((filas, cab))
    if len(tablas) != 1 or 'montos expresados en millones' not in texto:
        raise ValueError('No hay una única tabla fija en pesos con unidad reconocida')
    filas, cab = tablas[0]
    def columna(nombre):
        coincidencias = [i for i, c in enumerate(cab) if c.startswith(nombre)]
        if len(coincidencias) != 1:
            raise ValueError(f'Columna ambigua o ausente: {nombre}')
        return coincidencias[0]
    ve, tasa, precio = columna('valor efectivo adjudicado'), columna('tirea'), columna('precio')
    inventario = []
    for fila in filas[1:]:
        c = [x.get_text(' ', strip=True) for x in fila.find_all(['th', 'td'])]
        if not c:
            continue
        if len(c) != len(cab) or 'en pesos' not in normalizar(c[0]):
            raise ValueError('Fila fija incompleta o moneda no reconocida')
        monto, t = numero(c[ve]), numero(c[tasa])
        if monto <= 0 or t <= -100 or '%' not in c[tasa]:
            raise ValueError('Monto o TIREA inválidos')
        es_tem = '%' in c[precio]
        inventario.append({
            'instrumento': c[0], 'tirea': t, 'valor_efectivo': monto,
            'colocacion': registro['liquidacion'], 'licitacion': registro['fecha'],
            'precio_corte': None if es_tem else numero(c[precio]),
            'tem_corte': numero(c[precio]) if es_tem else None,
            'reapertura': 'reapertura' in normalizar(c[0]),
            'tirea_contractual': None, 'fuente_url': registro['resultado'],
            'metodo_tirea': 'publicada por Finanzas',
        })
    if len(inventario) != registro['filas_fijas']:
        raise ValueError('Cambió la cobertura de instrumentos de la licitación')
    return inventario


def completar(serie, *, manifiesto=MANIFIESTO, get=None, hoy=None):
    """Devuelve una copia ampliada o falla entera; nunca incorpora medio mes."""
    get = get or requests.get
    hoy = hoy or date.today()
    datos = json.loads(Path(manifiesto).read_text())
    salida = dict(serie)
    corte = max(serie, default='0000-00')
    for mes, bloque in sorted(datos['meses'].items()):
        if mes <= corte or mes >= hoy.strftime('%Y-%m'):
            continue
        registros = bloque.get('licitaciones', [])
        if not bloque.get('cobertura_verificada') or not registros:
            raise ValueError('Complemento sin cierre de cobertura')
        urls = [r['resultado'] for r in registros]
        if len(set(urls)) != len(urls):
            raise ValueError('Licitación duplicada')
        inv = []
        for registro in registros:
            if registro['liquidacion'][:7] != mes:
                raise ValueError('La liquidación no pertenece al mes declarado')
            llamado = get(registro['llamado'], timeout=40)
            llamado.raise_for_status()
            txt = normalizar(BeautifulSoup(llamado.text, 'html.parser').get_text(' ', strip=True))
            # Debe estar declarada como liquidación; no basta encontrar la fecha suelta.
            patron = r'liquidacion.{0,130}' + re.escape(fecha_textual(registro['liquidacion']))
            if not re.search(patron, txt):
                raise ValueError('No se confirma la fecha de liquidación en el llamado')
            respuesta = get(registro['resultado'], timeout=40)
            respuesta.raise_for_status()
            inv.extend(parsear_resultado(respuesta.text, registro))
        monto = sum(f['valor_efectivo'] for f in inv)
        tasa = sum(f['valor_efectivo'] * f['tirea']/100 for f in inv) / monto
        salida[mes] = (tasa, monto, len(inv), inv)
    return salida
