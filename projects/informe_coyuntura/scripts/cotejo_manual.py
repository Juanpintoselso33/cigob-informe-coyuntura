"""Incidencias de datos que requieren cotejo humano; no corrige ni puntúa.

Dos piezas, y ninguna rellena un dato por su cuenta:

- `registrar` escribe una línea `[COTEJO_MANUAL] {json}` en stderr. El log de
  colectores la lleva a Slack por `aviso_slack.py` (modos `degradado` y
  `fallo`), con indicador, registro, motivo y fuente.
- Los registros de correcciones verificadas (`data/politica/*_verificadas.json`)
  son el único camino por el que un dato ausente o ilegible entra al cálculo:
  cada entrada lleva la fuente documental que la respalda. Nacen vacíos.
"""
import json
import sys
from datetime import date
from pathlib import Path

MARCA = '[COTEJO_MANUAL] '
DATA = Path(__file__).resolve().parents[1] / 'data' / 'politica'
CORRECCIONES_SANCION = DATA / 'sanciones_fechas_verificadas.json'
ACTAS_VERIFICADAS = DATA / 'actas_diputados_fechas_verificadas.json'
_CLAVES_SANCION = ('PROYECTO_ID', 'EXPEDIENTE_INICIAL', 'LEY')


def registrar(indicador, registro, motivo, fuente):
    """Escribe el marcador en una línea propia aunque stdout venga en bloque.

    En el runner stdout y stderr comparten un pipe (`2>&1`) y stdout va
    bufferizado: sin vaciarlo antes, el marcador caía en medio de una línea de
    salida pendiente y el parser no lo veía.
    """
    sys.stdout.flush()
    sys.stderr.write(MARCA + json.dumps(dict(indicador=indicador, registro=registro,
                                             motivo=motivo, fuente=fuente), ensure_ascii=False) + '\n')
    sys.stderr.flush()


def fecha_canonica(valor):
    """YYYY-MM-DD si `valor` empieza por una fecha ISO válida; si no, None."""
    dia = str(valor)[:10]
    try:
        return dia if date.fromisoformat(dia).isoformat() == dia else None
    except (ValueError, TypeError):
        return None


def _registro(path, clave):
    registro = json.loads(path.read_text(encoding='utf-8'))
    if date.fromisoformat(registro['revisado_en']) > date.today():
        raise ValueError(f'{path.name}: revisión futura')
    return registro[clave]


def correcciones_sancion():
    """{campo:valor -> corrección} para las tres referencias de una fila HCDN."""
    out = {}
    for c in _registro(CORRECCIONES_SANCION, 'correcciones'):
        if fecha_canonica(c.get('SANCION_DEFINITIVA')) is None or not str(c.get('fuente') or '').strip():
            raise ValueError('corrección de sanción sin fecha canónica o sin fuente')
        referencias = [f"{k}:{str(c[k]).strip().upper()}" for k in _CLAVES_SANCION if c.get(k)]
        if not referencias:
            raise ValueError('corrección de sanción sin fila identificable')
        for ref in referencias:
            out[ref] = c
    return out


def aplicar_correcciones_sancion(filas):
    """Sustituye SOLO una fecha ausente o inválida por la documentada.

    Una fecha válida del catálogo nunca se reescribe. La fila corregida queda
    marcada con la fuente para que el detalle público pueda citarla.
    """
    correcciones = correcciones_sancion()
    if not correcciones:
        return list(filas)
    salida = []
    for fila in filas:
        if fecha_canonica(fila.get('SANCION_DEFINITIVA')) is None:
            for campo in _CLAVES_SANCION:
                c = correcciones.get(f"{campo}:{str(fila.get(campo) or '').strip().upper()}")
                if c:
                    fila = {**fila, 'SANCION_DEFINITIVA': fecha_canonica(c['SANCION_DEFINITIVA']),
                            'sancion_fecha_verificada': c['fuente']}
                    break
        salida.append(fila)
    return salida


def revisar_fechas_sancion(filas, fuente):
    for fila in filas:
        if fecha_canonica(fila.get('SANCION_DEFINITIVA')) is not None:
            continue
        registro = fila.get('PROYECTO_ID') or fila.get('EXPEDIENTE_INICIAL') or f"ley {fila.get('LEY', 'sin identificar')}"
        registrar('eficacia_legislativa', str(registro),
                  'Fecha de sanción ausente o inválida. Cotejar expediente o ley y documentar la fecha '
                  'real en data/politica/sanciones_fechas_verificadas.json; no usar fecha de consulta.',
                  fuente)


def fecha_acta_verificada(id_acta):
    """date documentada para un acta sin fecha legible, o None."""
    entrada = _registro(ACTAS_VERIFICADAS, 'actas').get(str(id_acta))
    if not entrada:
        return None
    dia = fecha_canonica(entrada.get('fecha'))
    if dia is None or not str(entrada.get('fuente') or '').strip():
        raise ValueError(f'acta {id_acta}: fecha verificada sin formato canónico o sin fuente')
    return date.fromisoformat(dia)


def avisos(log):
    salida, vistos = [], set()
    for linea in log.splitlines():
        inicio = linea.find(MARCA)
        if inicio < 0:
            continue
        try:
            dato = json.loads(linea[inicio + len(MARCA):])
            campos = [dato[k] for k in ('indicador', 'registro', 'motivo', 'fuente')]
            if not all(isinstance(x, str) and x.strip() for x in campos):
                continue
        except (ValueError, KeyError, TypeError):
            continue
        clave = tuple(campos)
        if clave in vistos:
            continue
        vistos.add(clave)
        # Neutralizar menciones y formato de enlaces de Slack en texto de fuente.
        def texto(s):
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')[:500]
        ind, reg, motivo, fuente = map(texto, campos)
        salida.append(f'Cotejo manual · {ind} · {reg}\n    {motivo}\n    Fuente: {fuente}')
    return salida
