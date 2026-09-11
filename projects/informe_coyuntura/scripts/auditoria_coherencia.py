"""Inventario reproducible de todos los componentes del snapshot, sin red.

Uso: .venv/bin/python scripts/auditoria_coherencia.py --salida /tmp/auditoria
No modifica datos del monitor. Verifica estructura y aritmética; no certifica
por sí solo disponibilidad de fuentes ni validez de los constructos.
"""
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import config
import itcm
import itcg
import itcp
import itvc

MOTORES = {
    'macro': (itcm, 'ITCM'), 'politica': (itcp, 'ITCP'),
    'gestion': (itcg, 'ITCG'), 'vida_cotidiana': (itvc, 'ITVC'),
}


def auditar():
    ruta = RAIZ / 'web/src/data/informe.json'
    raw = ruta.read_bytes()
    snap = json.loads(raw)
    fecha = date.fromisoformat(snap['generated_at'][:10])
    fallas, filas, dimensiones = [], [], []
    for cint, (motor, sigla) in MOTORES.items():
        bloque = snap['cinturones'][cint]
        idx = bloque[sigla.lower()]
        nominal = getattr(motor, 'DIMENSIONES_' + sigla)
        suspendidos = set(getattr(motor, 'INDICADORES_SUSPENDIDOS', {}))
        activos = set()
        suma = 0
        for dk, d in idx['dimensiones'].items():
            internos = d['indicadores']
            pesos = sum(x['peso'] for x in internos.values())
            # El snapshot conserva pesos INTERNOS NOMINALES aunque suspenda
            # componentes; el efectivo renormaliza sobre los presentes.
            if not 0 < pesos <= 1.001:
                fallas.append(f'{cint}/{dk}: suma nominal inválida {pesos}')
                continue
            puntaje = sum(x['peso'] * x['puntaje_aplicado'] for x in internos.values()) / pesos
            if abs(puntaje - d['puntaje']) > .11:
                fallas.append(f'{cint}/{dk}: suma {puntaje} != {d["puntaje"]}')
            pd = d.get('peso_efectivo', d['peso'])
            suma += pd * d['puntaje']
            dimensiones.append({
                'cinturon': cint, 'dimension': dk, 'nombre': d['nombre'],
                'peso_nominal': nominal[dk]['peso'], 'peso_efectivo': pd,
                'puntaje': d['puntaje'], 'activos': len(internos),
                'nominales': len(nominal[dk]['indicadores']),
            })
            for ik, v in internos.items():
                if ik in activos:
                    fallas.append(f'{cint}/{ik}: duplicado entre dimensiones')
                activos.add(ik)
                if ik in suspendidos:
                    fallas.append(f'{cint}/{ik}: suspendido puntúa')
                dato = bloque['indicadores'].get(ik)
                if dato is None:
                    fallas.append(f'{cint}/{ik}: componente sin tarjeta')
                    continue
                if dato.get('en_indice') is not True:
                    fallas.append(f'{cint}/{ik}: componente sin pertenencia explícita en tarjeta')
                campo_puntaje = 'indice_itvc' if sigla == 'ITVC' else f'puntaje_{sigla.lower()}'
                if dato.get(campo_puntaje) != v['puntaje_aplicado']:
                    fallas.append(f'{cint}/{ik}: puntaje de tarjeta distinto del componente')
                if dato.get('peso_efectivo') != v.get('peso_efectivo'):
                    fallas.append(f'{cint}/{ik}: peso de tarjeta distinto del componente')
                fd = str(dato.get('fecha_dato') or '')
                try:
                    edad = (fecha - date.fromisoformat(fd[:10] if len(fd) >= 10 else fd + '-01')).days
                except ValueError:
                    edad = None
                    fallas.append(f'{cint}/{ik}: fecha inválida {fd}')
                pe = v.get('peso_efectivo')
                if pe is not None and abs(pe - pd * v['peso'] / pesos) > .00015:
                    fallas.append(f'{cint}/{ik}: peso efectivo inconsistente')
                filas.append({
                    'cinturon': cint, 'dimension': dk, 'indicador': ik,
                    'estado_calculo': 'observado',
                    'valor': dato.get('valor'), 'unidad': dato.get('unidad'),
                    'fecha_dato': fd, 'obtenido_en': dato.get('obtenido_en', ''),
                    'antiguedad_dias': edad, 'tope_dias': config.MAX_DIAS.get(ik, config.MAX_DIAS_DEFAULT),
                    'demora_por_umbral': edad is not None and edad > config.MAX_DIAS.get(ik, config.MAX_DIAS_DEFAULT),
                    'cache': bool(dato.get('desactualizado')),
                    'peso_interno': v['peso'], 'peso_efectivo': pe,
                    'puntaje_aplicado': v['puntaje_aplicado'],
                    'color': (dato.get('semaforo') or {}).get('color'),
                    'fuente': dato.get('fuente'),
                    'verificacion_externa_individual': 'Ver matriz de contraste; no inferida de tests',
                })
        sin_universo = set()
        for ik, dato in bloque['indicadores'].items():
            if dato.get('estado') != 'sin_universo':
                continue
            valido = (cint == 'politica' and ik == 'bloqueo_sostenido'
                      and dato.get('valor') is None and dato.get('desafiadas_12m') == 0
                      and dato.get('en_indice') is False and ik not in activos
                      and not dato.get('semaforo')
                      and not any(k.startswith('puntaje_') for k in dato)
                      and dato.get('peso_efectivo') is None)
            if not valido:
                fallas.append(f'{cint}/{ik}: estado sin universo contradictorio')
                continue
            sin_universo.add(ik)
            fila = dict.fromkeys(filas[0])
            fila.update(cinturon=cint, dimension=dato.get('dimension'), indicador=ik,
                        estado_calculo='sin_universo', valor=None, unidad=dato.get('unidad'),
                        fecha_dato=dato.get('fecha_dato'), obtenido_en=dato.get('obtenido_en'),
                        cache=bool(dato.get('desactualizado')), fuente=dato.get('fuente'),
                        verificacion_externa_individual='Ver matriz de contraste; no inferida de tests')
            filas.append(fila)
        if activos | sin_universo != set(bloque['indicadores']):
            fallas.append(f'{cint}: tarjetas y componentes difieren')
        if abs(suma - idx['valor']) > .11:
            fallas.append(f'{cint}: dimensiones suman {suma} != {idx["valor"]}')
        tension = max(0, min(10, 5 - (idx['valor'] - 100) * .2)) if sigla == 'ITVC' else (100 - idx['valor']) / 10
        if abs(tension - bloque['score']) > .11:
            fallas.append(f'{cint}: tensión inconsistente')
    return {
        'generated_at_snapshot': snap['generated_at'],
        'sha256_snapshot': hashlib.sha256(raw).hexdigest(),
        'indicadores': len(filas), 'dimensiones': len(dimensiones),
        'indicadores_observados_en_calculo': sum(f['estado_calculo'] == 'observado' for f in filas),
        'indicadores_sin_universo': sum(f['estado_calculo'] == 'sin_universo' for f in filas),
        'fallas_estructura_y_aritmetica': fallas,
        'alcance': 'Censo del snapshot. No acredita veracidad de fuentes ni validez externa.',
    }, filas, dimensiones


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    resumen, filas, dimensiones = auditar()
    args.salida.mkdir(parents=True, exist_ok=True)
    for nombre, rows in [('indicadores', filas), ('dimensiones', dimensiones)]:
        with (args.salida / f'{nombre}.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (args.salida / 'coherencia.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    raise SystemExit(bool(resumen['fallas_estructura_y_aritmetica']))
