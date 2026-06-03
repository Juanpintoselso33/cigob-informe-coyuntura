#!/usr/bin/env python
"""
actualizar_encuestas.py — Agrega una nueva encuesta al Votómetro Argentina 2027.

Dual-write: actualiza projects/votometro/web/encuestas.json Y
projects/votometro/web/votometro.html en cada operación.

Uso:
    python scripts/actualizar_encuestas.py                  # modo interactivo
    python scripts/actualizar_encuestas.py nueva.csv        # modo CSV
    python scripts/actualizar_encuestas.py nueva.json       # modo JSON
"""

import sys
import json
import csv
import re
import shutil
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent.parent
VOTOMETRO_WEB = BASE / 'projects' / 'votometro' / 'web'
JSON_PATH = VOTOMETRO_WEB / 'encuestas.json'
HTML_PATH = VOTOMETRO_WEB / 'votometro.html'
HTML_BAK  = VOTOMETRO_WEB / 'votometro.html.bak'

CAMPOS_NUMERICOS = ['LLA', 'PJ', 'PRO', 'PU', 'FIT', 'OTROS']
TIPOS_VALIDOS    = {'espacio', 'candidato'}
CALIDADES_VALID  = {'A', 'B', 'C'}


# ─────────────────────────────────────────────────────────────
# VALIDACIÓN
# ─────────────────────────────────────────────────────────────

def validar_encuesta(enc, existentes):
    errores = []

    # 1. fecha: formato YYYY-MM-DD, no futura
    fecha_str = enc.get('fecha', '')
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
        hoy = datetime.date.today()
        if fecha > hoy:
            errores.append(f"  - fecha '{fecha_str}' es futura (hoy: {hoy})")
    except ValueError:
        errores.append(f"  - fecha '{fecha_str}' no tiene formato YYYY-MM-DD")
        fecha = None

    # 2. consultora: string no vacío
    consultora = enc.get('consultora', '').strip()
    if not consultora:
        errores.append("  - consultora está vacía")

    # 3. Campos numéricos >= 0
    for campo in CAMPOS_NUMERICOS:
        val = enc.get(campo)
        try:
            v = float(val)
            if v < 0:
                errores.append(f"  - {campo}={val} es negativo")
            enc[campo] = v
        except (TypeError, ValueError):
            errores.append(f"  - {campo}='{val}' no es un número válido")

    # 4. Suma entre 85 y 115
    try:
        suma = sum(float(enc.get(c, 0)) for c in CAMPOS_NUMERICOS)
        if not (85 <= suma <= 115):
            errores.append(f"  - suma de partidos = {suma:.1f} (debe estar entre 85 y 115)")
    except (TypeError, ValueError):
        pass  # ya reportado arriba

    # 5. muestra: entero > 0
    muestra = enc.get('muestra')
    try:
        m = int(muestra)
        if m <= 0:
            errores.append(f"  - muestra={muestra} debe ser > 0")
        enc['muestra'] = m
    except (TypeError, ValueError):
        errores.append(f"  - muestra='{muestra}' no es un entero válido")

    # 6. tipo
    tipo = enc.get('tipo', '').strip()
    if tipo not in TIPOS_VALIDOS:
        errores.append(f"  - tipo='{tipo}' debe ser 'espacio' o 'candidato'")

    # 7. calidad
    calidad = enc.get('calidad', '').strip().upper()
    if calidad not in CALIDADES_VALID:
        errores.append(f"  - calidad='{calidad}' debe ser 'A', 'B' o 'C'")
    else:
        enc['calidad'] = calidad

    # 8. url: opcional, si presente debe empezar con http
    url = enc.get('url', '').strip()
    if url and not url.startswith('http'):
        errores.append(f"  - url='{url}' debe empezar con 'http'")

    # 9. Duplicado: misma fecha + consultora
    if fecha and consultora:
        for ex in existentes:
            if ex.get('fecha') == fecha_str and ex.get('consultora') == consultora:
                errores.append(f"  - DUPLICADO: ya existe encuesta de '{consultora}' con fecha {fecha_str}")
                break

    return errores


# ─────────────────────────────────────────────────────────────
# LECTURA DEL JSON CANÓNICO
# ─────────────────────────────────────────────────────────────

def leer_json():
    if not JSON_PATH.exists():
        return []
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)


def guardar_json(encuestas):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(encuestas, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
# ACTUALIZACIÓN DEL HTML
# ─────────────────────────────────────────────────────────────

def enc_to_js_line(enc):
    """Genera la línea JS para el array encuestasRaw del HTML."""
    fecha      = enc['fecha']
    consultora = enc['consultora']
    LLA   = enc['LLA']
    PJ    = enc['PJ']
    PRO   = enc['PRO']
    PU    = enc['PU']
    FIT   = enc['FIT']
    OTROS = enc['OTROS']
    muestra = enc['muestra']
    tipo    = enc['tipo']
    calidad = enc['calidad']
    url     = enc.get('url', '').strip()

    def fmt(v):
        # Mostrar sin decimales innecesarios: 42.0 → 42.0 (mantener .1f para consistencia)
        return f"{float(v):.1f}"

    url_part = f", url:'{url}'" if url else ''
    return (
        f"    {{ fecha:'{fecha}', consultora:'{consultora}', "
        f"LLA:{fmt(LLA)}, PJ:{fmt(PJ)}, PRO:{fmt(PRO)},  "
        f"PU:{fmt(PU)}, FIT:{fmt(FIT)}, OTROS:{fmt(OTROS)}, "
        f"muestra:{muestra}, tipo:'{tipo}',   calidad:'{calidad}'"
        f"{url_part} }},"
    )


def actualizar_html(nueva_enc, fecha_max_str):
    """
    Agrega la nueva encuesta al array encuestasRaw del HTML y actualiza
    ULTIMA_ACTUALIZACION. Opera sobre el texto del archivo con str.replace.
    """
    html = HTML_PATH.read_text(encoding='utf-8')

    # ── Insertar en encuestasRaw ──────────────────────────────
    # El cierre del array es una línea con "];" sola (al inicio de línea,
    # precedida por el último objeto del array).
    # Buscamos el patrón: último objeto seguido del cierre.
    # Anchor: "\n];" (el cierre del array está en su propia línea)
    nueva_linea = enc_to_js_line(nueva_enc)

    # El cierre del array encuestasRaw tiene esta forma exacta en el HTML:
    #     { fecha:'...', ...},\n];\n
    # Usamos el anchor de la línea de cierre del array: "\n];"
    # pero restringido al bloque de encuestasRaw (antes de calcPeso).
    # Estrategia: encontrar la posición de "];\n\nfunction calcPeso" y
    # reemplazar el "];" inmediatamente antes de esa función.

    CIERRE_ANCHOR = '];\n\nfunction calcPeso'
    if CIERRE_ANCHOR not in html:
        # Fallback: buscar "];" solo
        CIERRE_ANCHOR = '];\n'
        if CIERRE_ANCHOR not in html:
            raise ValueError("No se encontró el cierre del array encuestasRaw en el HTML.")

    # Insertar la nueva línea antes del cierre
    html_nuevo = html.replace(
        CIERRE_ANCHOR,
        f'\n{nueva_linea}\n{CIERRE_ANCHOR}',
        1  # solo la primera ocurrencia
    )

    if html_nuevo == html:
        raise ValueError(f"El reemplazo del array no produjo cambios. Anchor: '{CIERRE_ANCHOR}'")

    # ── Actualizar ULTIMA_ACTUALIZACION ──────────────────────
    # El patrón consume toda la línea (incluyendo comentario opcional)
    # para evitar duplicar el comentario en el reemplazo.
    patron_ua = re.compile(
        r"const ULTIMA_ACTUALIZACION = new Date\('(\d{4}-\d{2}-\d{2})'\);[^\n]*"
    )
    m = patron_ua.search(html_nuevo)
    if not m:
        raise ValueError("No se encontró 'const ULTIMA_ACTUALIZACION = new Date(...)' en el HTML.")

    fecha_actual = m.group(1)
    if fecha_max_str > fecha_actual:
        html_nuevo = patron_ua.sub(
            f"const ULTIMA_ACTUALIZACION = new Date('{fecha_max_str}'); // última encuesta agregada manualmente",
            html_nuevo
        )
    else:
        fecha_max_str = fecha_actual  # no cambió

    return html_nuevo, fecha_max_str


# ─────────────────────────────────────────────────────────────
# MODO INTERACTIVO
# ─────────────────────────────────────────────────────────────

def pedir_campo(nombre, descripcion, requerido=True):
    while True:
        val = input(f"  {nombre} ({descripcion}): ").strip()
        if val or not requerido:
            return val
        print(f"    [!] {nombre} es requerido.")


def modo_interactivo():
    print("\n=== Agregar nueva encuesta al Votómetro ===\n")
    enc = {}
    enc['fecha']      = pedir_campo('fecha',      'YYYY-MM-DD')
    enc['consultora'] = pedir_campo('consultora',  'nombre de la consultora')
    for c in CAMPOS_NUMERICOS:
        enc[c] = pedir_campo(c, 'número >= 0')
    enc['muestra']    = pedir_campo('muestra',    'entero > 0')
    enc['tipo']       = pedir_campo('tipo',       '"espacio" o "candidato"')
    enc['calidad']    = pedir_campo('calidad',    '"A", "B" o "C"')
    enc['url']        = pedir_campo('url',        'URL opcional (Enter para omitir)', requerido=False)
    return [enc]


# ─────────────────────────────────────────────────────────────
# MODO CSV
# ─────────────────────────────────────────────────────────────

def modo_csv(path):
    encuestas = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            encuestas.append(dict(row))
    return encuestas


# ─────────────────────────────────────────────────────────────
# MODO JSON
# ─────────────────────────────────────────────────────────────

def modo_json_file(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    # Determinar modo
    if len(sys.argv) == 1:
        nuevas = modo_interactivo()
    else:
        archivo = Path(sys.argv[1])
        if not archivo.exists():
            print(f"Error: no existe el archivo '{archivo}'")
            sys.exit(1)
        ext = archivo.suffix.lower()
        if ext == '.csv':
            nuevas = modo_csv(archivo)
        elif ext == '.json':
            nuevas = modo_json_file(archivo)
        else:
            print(f"Error: extensión '{ext}' no soportada. Usar .csv o .json")
            sys.exit(1)

    # Leer estado actual del JSON
    existentes = leer_json()
    n_antes = len(existentes)

    # Validar todas las encuestas nuevas antes de escribir nada
    todos_errores = []
    # Para detección de duplicados entre las propias nuevas (si viene un batch)
    acumuladas = list(existentes)
    for i, enc in enumerate(nuevas):
        errs = validar_encuesta(enc, acumuladas)
        if errs:
            todos_errores.append((i + 1, enc.get('consultora', '?'), enc.get('fecha', '?'), errs))
        else:
            acumuladas.append(enc)

    if todos_errores:
        print("\n[!] Errores de validación — no se escribió nada:\n")
        for idx, consultora, fecha, errs in todos_errores:
            print(f"  Encuesta #{idx} ({consultora} / {fecha}):")
            for e in errs:
                print(e)
        sys.exit(1)

    print("\n✓ Validación OK")

    # Calcular fecha máxima (para ULTIMA_ACTUALIZACION)
    todas_fechas = [e.get('fecha', '') for e in existentes + nuevas if e.get('fecha')]
    fecha_max = max(todas_fechas) if todas_fechas else datetime.date.today().isoformat()

    # ── Backup del HTML ──────────────────────────────────────
    shutil.copy2(HTML_PATH, HTML_BAK)

    # ── Actualizar JSON ──────────────────────────────────────
    for enc in nuevas:
        # Limpiar campo url vacío
        if not enc.get('url', '').strip():
            enc.pop('url', None)
        existentes.append(enc)

    guardar_json(existentes)
    n_despues = len(existentes)
    print(f"✓ JSON actualizado: projects/votometro/web/encuestas.json ({n_antes} → {n_despues} entradas)")

    # ── Actualizar HTML ──────────────────────────────────────
    html_contenido = HTML_PATH.read_text(encoding='utf-8')
    n_antes_html = html_contenido.count("fecha:'") + html_contenido.count('fecha:"')

    html_nuevo = html_contenido
    fecha_ua_final = None
    for enc in nuevas:
        try:
            html_nuevo, fecha_ua_final = actualizar_html_inplace(html_nuevo, enc, fecha_max)
        except ValueError as e:
            print(f"\n[!] Error actualizando HTML: {e}")
            print("    El JSON fue actualizado pero el HTML NO. Restaurando desde backup...")
            shutil.copy2(HTML_BAK, HTML_PATH)
            sys.exit(1)

    HTML_PATH.write_text(html_nuevo, encoding='utf-8')

    print(f"✓ HTML actualizado: projects/votometro/web/votometro.html")
    for enc in nuevas:
        print(f"  - encuestasRaw: +1 entrada ({enc['consultora']} {enc['fecha']})")
    print(f"  - ULTIMA_ACTUALIZACION: {fecha_ua_final or fecha_max}")

    # ── Mensaje final ────────────────────────────────────────
    if len(nuevas) == 1:
        enc = nuevas[0]
        mes = enc['fecha'][:7].replace('-', '-')
        msg = f"data: agrega {enc['consultora']} {mes}"
    else:
        msg = f"data: agrega {len(nuevas)} encuestas"

    print(f"\n✓ Listo. Próximo paso: git add web/ && git commit -m \"{msg}\" && git push")


def actualizar_html_inplace(html, nueva_enc, fecha_max_str):
    """
    Versión que opera sobre un string html ya leído (permite procesamiento en batch).
    Retorna (html_nuevo, fecha_ua_efectiva).
    """
    nueva_linea = enc_to_js_line(nueva_enc)

    CIERRE_ANCHOR = '];\n\nfunction calcPeso'
    if CIERRE_ANCHOR not in html:
        CIERRE_ANCHOR_ALT = '];\n'
        if CIERRE_ANCHOR_ALT not in html:
            raise ValueError("No se encontró el cierre del array encuestasRaw en el HTML.")
        CIERRE_ANCHOR = CIERRE_ANCHOR_ALT

    html_nuevo = html.replace(
        CIERRE_ANCHOR,
        f'\n{nueva_linea}\n{CIERRE_ANCHOR}',
        1
    )

    if html_nuevo == html:
        raise ValueError(f"El reemplazo del array no produjo cambios. Anchor: '{CIERRE_ANCHOR}'")

    # Actualizar ULTIMA_ACTUALIZACION
    # El patrón consume toda la línea (incluyendo comentario opcional)
    # para evitar duplicar el comentario en el reemplazo.
    patron_ua = re.compile(
        r"const ULTIMA_ACTUALIZACION = new Date\('(\d{4}-\d{2}-\d{2})'\);[^\n]*"
    )
    m = patron_ua.search(html_nuevo)
    if not m:
        raise ValueError("No se encontró 'const ULTIMA_ACTUALIZACION = new Date(...)' en el HTML.")

    fecha_actual = m.group(1)
    if fecha_max_str > fecha_actual:
        html_nuevo = patron_ua.sub(
            f"const ULTIMA_ACTUALIZACION = new Date('{fecha_max_str}'); // última encuesta agregada manualmente",
            html_nuevo
        )
        fecha_ua_efectiva = fecha_max_str
    else:
        fecha_ua_efectiva = fecha_actual

    return html_nuevo, fecha_ua_efectiva


if __name__ == '__main__':
    main()
