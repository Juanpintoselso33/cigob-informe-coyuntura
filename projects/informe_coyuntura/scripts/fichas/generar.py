"""Markdown de las fichas de un cinturón, en el formato que circuló Luis.

    python scripts/fichas/generar.py <macro|politica|gestion|vida_cotidiana>

Misma anatomía que aquellas fichas de gestión: encabezado, nombre, definición
de una línea, el banner "Hoy:", la tabla de Identificación, y las secciones de
prosa con títulos fijos. Nada interactivo: es una ficha para leer y anotar al
lado. Antes de las fichas va una portada con el cinturón entero — el índice,
las dimensiones y todos los indicadores con su color y su peso.

Todo sale del snapshot y de los textos que ya usa la web. El .md que escribe
acá todavía no es el entregable: falta pandoc con la plantilla CIGOB y después
`estilar.py`. Ver el README de esta carpeta.
"""
import json
import re
from pathlib import Path

# La raíz del proyecto sale de la ubicación de este archivo: vive en
# scripts/fichas/, así que sube dos niveles. Antes era un path absoluto de
# una máquina concreta, que dentro del repo no le sirve a nadie.
RAIZ = Path(__file__).resolve().parents[2]
SALIDA_DIR = RAIZ / "output" / "fichas"
import sys
CINT = sys.argv[1]
SIGLA, NOMBRE = {
 "macro": ("ITCM", "Macroeconomía"),
 "politica": ("ITCP", "Política"),
 "gestion": ("ITCG", "Gestión"),
 "vida_cotidiana": ("ITCIS", "Impacto social"),
}[CINT]
SALIDA_MD = SALIDA_DIR / f"fichas-{CINT}.md"

informe = json.loads((RAIZ / "web/src/data/informe.json").read_text(encoding="utf-8"))
fichas_ts = (RAIZ / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
desc_ts = (RAIZ / "web/src/lib/descripciones.ts").read_text(encoding="utf-8")
datos_ts = (RAIZ / "web/src/lib/datos.ts").read_text(encoding="utf-8")
series = json.loads((RAIZ / "web/src/data/series.json").read_text(encoding="utf-8"))

CADENA = r'"((?:[^"\\]|\\.)*)"'
COLOR = {"verde": "VERDE", "amarillo": "AMARILLO", "naranja": "NARANJA", "rojo": "ROJO"}
ORDEN_COLOR = ["verde", "amarillo", "naranja", "rojo"]
def _clave_indice():
    """Bajo qué clave publica el snapshot el índice de este cinturón, si tiene
    uno. Espíritu de época no arma paramétrica, así que devuelve None."""
    b = informe["cinturones"][CINT]
    return next((k for k in ("itcm", "itcg", "itcp", "itvc") if k in b), None)


CLAVE_INDICE = _clave_indice()
DIMS = ({d: v["nombre"]
         for d, v in informe["cinturones"][CINT][CLAVE_INDICE]["dimensiones"].items()}
        if CLAVE_INDICE else {})


def _lab():
    m = re.search(r"export const LABELS[^{]*\{(.*?)\n\};", datos_ts, re.S)
    return dict(re.findall(r"(\w+):\s*" + CADENA, m.group(1)))


LABELS = _lab()


def _dim_desc():
    """Qué mide cada dimensión, del mapa que ya usa la web para su modal. Se
    lee de ahí y no se redacta acá: si las fichas dijeran otra cosa que la
    página, tendríamos dos definiciones de la misma dimensión."""
    m = re.search(r"export const DIM_DESCRIPCIONES[^{]*\{(.*?)\n\};", desc_ts, re.S)
    return dict(re.findall(r"(\w+):\s*" + CADENA, m.group(1))) if m else {}


DIM_DESCRIPCIONES = _dim_desc()


def una_oracion(txt, limite=165):
    """La definición recortada a algo que entre en una celda. Corta en el
    primer punto; si esa oración es muy larga —varias lo son, arrancan con un
    enunciado y siguen enumerando con dos puntos— corta antes en los dos
    puntos, y si aun así no entra, trunca en el último espacio."""
    if not txt:
        return "—"
    t = txt.strip()
    corte = t.find(". ")
    if corte > 0:
        t = t[:corte + 1]
    if len(t) > limite:
        dp = t.find(":")
        if 0 < dp <= limite:
            t = t[:dp] + "."
    if len(t) > limite:
        t = t[:t.rfind(" ", 0, limite)].rstrip(" ,;:") + "…"
    return t


def _bloque(txt, ikey):
    m = re.search(r"\n  " + re.escape(ikey) + r":\s*\{(.*?)\n  \},", txt, re.S)
    return m.group(1) if m else ""


def campo(txt, ikey, nombre, sub=None):
    blk = _bloque(txt, ikey)
    if sub:
        m = re.search(sub + r":\s*\{(.*?)\n    \}", blk, re.S)
        blk = m.group(1) if m else ""
    m = re.search(r"\b" + nombre + r":\s*" + CADENA, blk, re.S)
    return m.group(1).replace('\\"', '"') if m else None


def lista(txt, ikey, nombre):
    m = re.search(r"\b" + nombre + r":\s*\[(.*?)\n    \]", _bloque(txt, ikey), re.S)
    return [x.replace('\\"', '"') for x in re.findall(CADENA, m.group(1))] if m else []


def cambios(ikey):
    m = re.search(r"cambios:\s*\[(.*?)\n    \]", _bloque(fichas_ts, ikey), re.S)
    if not m:
        return []
    return re.findall(r'fecha:\s*"([^"]+)",\s*cambio:\s*' + CADENA, m.group(1))


def coma(x, dec=2, recortar=True):
    """Número en formato local. `recortar` saca los decimales que sobran, que
    es lo que se quiere en prosa; en una columna de tabla no, porque deja
    "71" al lado de "67,1" y la columna se lee torcida."""
    if x is None:
        return "—"
    s = f"{float(x):,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    if recortar and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s.replace("-", "−")  # menos tipográfico, no guión


def rango(t, unidad):
    d, h = t.get("desde"), t.get("hasta")
    n = lambda v: coma(v).replace("-", "−")
    if d is None and h is None:
        return "todo el rango"
    if d is None:
        return f"≤ {n(h)}"
    if h is None:
        return f"≥ {n(d)}"
    return f"{n(d)} – {n(h)}"


def cobertura(ikey):
    s = series.get(ikey) or []
    if not s:
        return "—"
    f = [p["fecha"][:7] for p in s if p.get("fecha")]
    return f"{min(f)} → {max(f)} ({len(f)} puntos)" if f else "—"


# El ITVC no tiene tablas de bandas por componente: cada uno entra como índice
# continuo base-100 (100 = promedio 4T-2023), así que `publicar.py` no le puede
# calcular umbrales en la unidad nativa y publica `umbrales: null`. Pero la
# escala existe y es exacta: tensión = 5 − (índice − 100) × 0,2, verificada
# contra los 16 componentes sin un solo desajuste. Los cortes 4/6/8 de tensión
# se invierten a índice, y como el corte es techo inclusivo (`tension <= tope`
# en parametrica.color_de_tension), el borde queda del lado del color mejor:
# índice 105 es verde, 95 amarillo, 85 naranja.
#
# El texto de cada tramo va literal y no por la función `rango` genérica: ésta
# rinde el tramo abierto de abajo como "≤ 85", que contradice al de arriba
# ("85 – 95") justo en el borde que la tabla tiene que dejar sin ambigüedad.
UMBRALES_ITVC = [
    {"color": "verde", "texto": "105 o más"},
    {"color": "amarillo", "texto": "de 95 a 105"},
    {"color": "naranja", "texto": "de 85 a 95"},
    {"color": "rojo", "texto": "menos de 85"},
]
# La tensión se acota a [0, 10], así que fuera de esta franja el semáforo deja
# de moverse. 140 es además el techo de winsorización del índice: un componente
# ahí está doblemente saturado.
ITVC_PISO, ITVC_TECHO, ITVC_WINSOR = 75.0, 125.0, 140.0


L = []
w = L.append
SALTO = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'

w("---")
w(f'title: "Fichas metodológicas · Cinturón {NOMBRE}"')
w('subtitle: "Informe de Coyuntura · Capa de semáforo (4 colores)"')
w('author: "Fundación CIGOB"')
w("---")
w("")

ind = informe["cinturones"][CINT]["indicadores"]

# ── Portada: el cinturón entero antes de las fichas ──────────────────────────
# Sin esto el documento arranca en el primer indicador y no hay dónde ver el
# conjunto: cuántos hay, cómo se agrupan, cuánto pesa cada uno y qué color
# tiene. Los colores salen publicados del snapshot (índice, dimensiones e
# indicadores traen su `semaforo`), así que la portada no recalcula nada.
cint = informe["cinturones"][CINT]
idx = cint.get(CLAVE_INDICE) if CLAVE_INDICE else None

w("**CIGOB · INFORME DE COYUNTURA**")
w("")
w(f"# Cinturón {NOMBRE} — resumen")
w("")
w("Este documento tiene una ficha por indicador"
  + (f" — son {len(ind)} en total" if len(ind) > 1 else " — acá hay una sola")
  + ", y cada una arranca en página nueva. Antes de las fichas, el cinturón "
    "completo de un vistazo.")
w("")
conteo = {}
for o in ind.values():
    c = (o.get("semaforo") or {}).get("color")
    conteo[c] = conteo.get(c, 0) + 1
resumen_colores = " · ".join(f"{conteo[c]} en {c}" for c in ORDEN_COLOR if conteo.get(c))

# ── Cómo se define el color ──────────────────────────────────────────────────
# La portada muestra colores en el índice, en cada dimensión y en cada
# indicador, y sin esto no dice en ninguna parte qué rango produce cada uno.
# Faltaba: el lector veía "77,5 VERDE" y "24,4 % NARANJA" sin la regla que los
# une. Las tablas por indicador están, pero recién dentro de cada ficha y en
# la unidad propia de ese indicador.
#
# Los cortes salen del snapshot (`semaforo_cortes`), no se escriben acá: son
# los mismos que aplica el informe, y si se recalibran, esta tabla los sigue.
CORTES = informe.get("semaforo_cortes") or []
if CORTES:
    w("## Cómo se define el color")
    w("")
    w("Todos los colores de este documento —el del índice, el de cada dimensión "
      "y el de cada indicador— salen de una sola escala: la **tensión de 0 a 10** "
      "que publica el informe. Se parte en cuatro tramos y esos tramos son los "
      "mismos para todo.")
    w("")
    topes = [c.get("hasta") for c in CORTES]
    if CINT == "vida_cotidiana":
        # El ITVC es base-100 (100 = 4T-2023), no un puntaje 0-100: su tensión
        # es 5 − (índice − 100) × 0,2, así que los mismos cortes 4/6/8 caen en
        # otros números y la tabla tiene que decir ésos, no los del resto.
        escala = [("105 o más", "verde"), ("de 95 a 105", "amarillo"),
                  ("de 85 a 95", "naranja"), ("menos de 85", "rojo")]
        titulo_col = f"Índice del {SIGLA} y de sus dimensiones (base 100 = 4º trim. 2023)"
        nota = ("El ITVC no es un puntaje de 0 a 100: es un índice base 100, donde "
                "100 es el promedio del 4º trimestre de 2023. Por encima de 100 hay "
                "mejora acumulada; por debajo, deterioro. La tensión sale de "
                "5 − (índice − 100) × 0,2.")
    else:
        escala = [("60 o más", "verde"), ("de 40 a 60", "amarillo"),
                  ("de 20 a 40", "naranja"), ("menos de 20", "rojo")]
        # Sin índice —espíritu de época— la columna del puntaje no describe
        # nada de este cinturón: la escala 0-100 es la de los índices, y acá
        # no hay ninguno. Se deja igual, dicho como referencia general.
        titulo_col = (f"Puntaje del {SIGLA} y de sus dimensiones (0 a 100)" if idx
                      else "Puntaje en la escala de los índices (0 a 100)")
        nota = ((f"El puntaje del {SIGLA} y el de cada dimensión van de 0 a 100, donde "
                 "100 es la mejor situación. La tensión es su reflejo: "
                 "(100 − puntaje) ÷ 10.") if idx else
                ("Este cinturón no arma un índice paramétrico, así que no tiene "
                 "puntaje propio ni dimensiones: el color de su indicador sale "
                 "directamente de la tensión. La columna del medio queda como "
                 "referencia de cómo se lee la misma escala en los cinturones que "
                 "sí tienen índice."))
    w(nota)
    w("")
    w(f"| Tensión | {titulo_col} | Color |")
    w("|---|---|---|")
    filas_t = ["hasta 4", "más de 4 y hasta 6", "más de 6 y hasta 8", "más de 8"]
    for (rango_valor, color), t in zip(escala, filas_t):
        w(f"| {t} | {rango_valor} | {COLOR[color]} |")
    w("")
    w("**Cada indicador tiene además su propia tabla**, en su unidad de medida "
      "—pesos, porcentaje, índice, lo que corresponda—, dentro de su ficha, bajo "
      "el título «Semáforo — valores que determinan el color». Ahí no hay ninguna "
      "escala intermedia: sólo el dato real y el color que le toca.")
    w("")
    w(SALTO)
    w("")
    w("**CIGOB · INFORME DE COYUNTURA**")
    w("")

if idx:
    sem_idx = idx.get("semaforo") or {}
    w(f"## {SIGLA} — el índice del cinturón")
    w("")
    w("| | | | |")
    w("|---|---|---|---|")
    w(f"| **{SIGLA}: {coma(idx.get('valor'), 1, recortar=False)}** | **{COLOR.get(sem_idx.get('color'), '—')}** "
      f"| {idx.get('banda_legible') or idx.get('banda') or '—'} "
      f"| {len(ind)} indicadores: {resumen_colores} |")
    w("")
    dims = idx.get("dimensiones") or {}
    w("## Dimensiones")
    w("")
    escala = "Índice" if CINT == "vida_cotidiana" else "Puntaje"
    w(f"| Dimensión | Qué mide | {escala} | Color | Peso |")
    w("|---|---|---|---|---|")
    for dk, d in sorted(dims.items(), key=lambda kv: -(kv[1].get("peso") or 0)):
        sd = d.get("semaforo") or {}
        w(f"| {d.get('nombre') or dk} | {una_oracion(DIM_DESCRIPCIONES.get(dk))} "
          f"| {coma(d.get('puntaje'), 1, recortar=False)} "
          f"| {COLOR.get(sd.get('color'), '—')} "
          f"| {coma((d.get('peso') or 0) * 100, 1, recortar=False)} % |")
    w("")
else:
    w(f"Este cinturón no arma un índice paramétrico: sus indicadores se leen "
      f"solos, sin puntaje agregado ni dimensiones ponderadas.")
    w("")
    if resumen_colores:
        w(f"Colores vigentes: {resumen_colores}.")
        w("")

w(SALTO)
w("")
w("**CIGOB · INFORME DE COYUNTURA**")
w("")
w("## Todos los indicadores")
w("")
w("Agrupados por dimensión. La columna de peso dice cuánto mueve cada "
  "indicador el índice del cinturón; el color es el del semáforo de este mes.")
w("")
# Una sola tabla con la dimensión como fila separadora, en vez de una tabla
# por dimensión: así los pesos siguen siendo comparables de un vistazo entre
# dimensiones, que es lo que se viene a mirar acá. La fila separadora se
# combina y se pinta en el post-proceso, que la reconoce por este prefijo.
MARCA_DIM = "DIMENSIÓN:"
cols = ["Indicador", "Qué mide", "Hoy", "Color"] + ([f"Peso en el {SIGLA}"] if idx else [])
w("| " + " | ".join(cols) + " |")
w("|" + "---|" * len(cols))


def _fila_indicador(ikey, o):
    sem = o.get("semaforo") or {}
    fila = [LABELS.get(ikey, ikey),
            una_oracion(campo(desc_ts, ikey, "que"), 120),
            f"{coma(o.get('valor'))} {o.get('unidad') or ''}".strip(),
            COLOR.get(sem.get("color"), "—")]
    if idx:
        peso_i = o.get("peso_efectivo")
        # Un indicador puede estar fuera del índice por dos motivos declarados
        # y bien distintos —promesa cumplida, o suspendido a pedido de CIGOB— y
        # el snapshot los trae. Decir solo "fuera del índice" los confunde: uno
        # llegó a 100 y el otro está en revisión.
        if peso_i:
            fila.append(f"{coma(peso_i * 100, 1, recortar=False)} %")
        elif o.get("cumplido"):
            fila.append("fuera: promesa cumplida")
        elif o.get("suspendido"):
            fila.append("fuera: suspendido, en revisión")
        else:
            fila.append("fuera del índice")
    w("| " + " | ".join(fila) + " |")


if idx:
    orden_dim = [dk for dk, _ in sorted((idx.get("dimensiones") or {}).items(),
                                        key=lambda kv: -(kv[1].get("peso") or 0))]
    agrupados = {dk: [(k, o) for k, o in ind.items() if o.get("dimension") == dk]
                 for dk in orden_dim}
    for dk in orden_dim:
        if not agrupados[dk]:
            continue
        w(f"| **{MARCA_DIM} {DIMS.get(dk, dk)}** |" + " |" * (len(cols) - 1))
        for ikey, o in agrupados[dk]:
            _fila_indicador(ikey, o)
    # Los que no caen en ninguna dimensión —contexto, suspendidos— no pueden
    # quedar fuera de la tabla: el total dejaría de cuadrar con el "son N" de
    # la portada, sin que nada lo avise.
    sueltos = [(k, o) for k, o in ind.items() if o.get("dimension") not in agrupados]
    if sueltos:
        w(f"| **{MARCA_DIM} Fuera del índice** |" + " |" * (len(cols) - 1))
        for ikey, o in sueltos:
            _fila_indicador(ikey, o)
else:
    for ikey, o in ind.items():
        _fila_indicador(ikey, o)
w("")
w(f"*Datos al {informe['generated_at'][:10]}.*")
w("")

for n, (ikey, o) in enumerate(ind.items(), 1):
    w(SALTO)
    w("")
    sem = o.get("semaforo") or {}
    peso = o.get("peso_efectivo")
    indice = o.get("indice_itvc")
    lims = lista(fichas_ts, ikey, "limitaciones")
    trans = lista(fichas_ts, ikey, "transformaciones")

    w("**CIGOB · INFORME DE COYUNTURA**")
    w("")
    w(f"*Ficha metodológica · Cinturón {NOMBRE} · Capa de semáforo (4 colores)*")
    w("")
    w(f"# {LABELS.get(ikey, ikey)}")
    w("")
    w(campo(desc_ts, ikey, "que") or "")
    w("")
    w("| | | | |")
    w("|---|---|---|---|")
    w(f"| **Hoy: {coma(o.get('valor'))} {o.get('unidad') or ''}** "
      f"({(o.get('fecha_dato') or '')[:7]}) | **{COLOR.get(sem.get('color'), '—')}** "
      f"| {('Peso efectivo ' + coma((peso or 0) * 100, 1) + ' % del ' + SIGLA) if peso else 'Fuera del índice'} "
      f"| Cinturón {NOMBRE} |")
    w("")
    w("## Identificación")
    w("")
    w("| | | | |")
    w("|---|---|---|---|")
    w(f"| **IDENTIFICADOR TÉCNICO** | {ikey} | **CINTURÓN** | {NOMBRE} |")
    dim = DIMS.get(o.get("dimension"), "—")
    rot = f"DIMENSIÓN EN EL {SIGLA}" if SIGLA else "DIMENSIÓN"
    w(f"| **{rot}** | {dim if dim != '—' else 'Este cinturón no arma un índice paramétrico'} | **UNIDAD DE MEDIDA** | {o.get('unidad') or '—'} |")
    w(f"| **SERIE DISPONIBLE** | {cobertura(ikey)} | **REZAGO DE PUBLICACIÓN** | {campo(fichas_ts, ikey, 'rezago') or '—'} |")
    w(f"| **PRODUCTOR DEL DATO** | {campo(fichas_ts, ikey, 'organismo', 'fuente') or '—'} "
      f"| **OPERACIÓN ESTADÍSTICA** | {campo(fichas_ts, ikey, 'operacion', 'fuente') or '—'} |")
    w(f"| **MODO DE ACCESO** | {campo(fichas_ts, ikey, 'acceso', 'fuente') or '—'} "
      f"| **ÚLTIMA ACTUALIZACIÓN** | Dato a {(o.get('fecha_dato') or '')[:7]} · informe generado el {informe['generated_at'][:10]} |")
    w("")
    w("## Definición — qué mide y por qué importa")
    w("")
    w(campo(desc_ts, ikey, "que") or "")
    w("")
    w(campo(desc_ts, ikey, "aporta") or "")
    w("")
    dim_txt = DIM_DESCRIPCIONES.get(o.get("dimension"))
    if dim_txt and dim:
        w(f"**Dimensión que integra — {dim}.** {dim_txt}")
        w("")
    if trans:
        w("## Método de cómputo")
        w("")
        for t in trans:
            w(f"- {t}")
        w("")
    if sem.get("umbrales"):
        w("## Semáforo — valores que determinan el color")
        w("")
        w("Estos son los valores concretos, en la unidad propia de este indicador, que hacen "
          "que el semáforo esté en verde, amarillo, naranja o rojo. No se muestra ninguna "
          "fórmula ni escala intermedia de 0 a 100 — solo el dato real y el color que le "
          "corresponde.")
        w("")
        w("**Valores que definen cada color**")
        w("")
        w(f"| Rango ({sem.get('unidad') or o.get('unidad') or ''}) | Color |")
        w("|---|---|")
        # Siempre de mejor a peor. Ordenar por el eje del valor dejaba la columna
        # de color en tres órdenes distintos entre las 17 fichas —diez de peor a
        # mejor, cuatro al revés y la no monótona en zigzag— y obligaba a
        # reorientarse en cada una.
        for t in sorted(sem["umbrales"], key=lambda t: ORDEN_COLOR.index(t["color"])):
            w(f"| {rango(t, sem.get('unidad'))} | {COLOR.get(t['color'], t['color'])} |")
        w("")
    elif indice is not None:
        w("## Semáforo — valores que determinan el color")
        w("")
        w("Este cinturón no usa tablas de bandas por indicador: cada componente entra al "
          "índice como un número rebaseado a 100 = promedio del 4º trimestre de 2023, el "
          "arranque del mandato. Por encima de 100 hay mejora acumulada; por debajo, "
          "deterioro. El color se lee sobre ese número rebaseado, no sobre el valor en su "
          "unidad original.")
        w("")
        w("**Valores que definen cada color**")
        w("")
        w("| Rango (índice base 100 = 4º trim. 2023) | Color |")
        w("|---|---|")
        for t in UMBRALES_ITVC:
            w(f"| {t['texto']} | {COLOR[t['color']]} |")
        w("")
        w(f"Este componente está hoy en **{coma(indice, 1)}**.")
        w("")
    w("## Datos concretos detrás del valor")
    w("")
    w("Qué hay, específicamente, detrás del dato que define el color de este mes — o qué "
      "falta publicar para poder verificarlo con precisión.")
    w("")
    duro = o.get("detalle_txt") or o.get("aporte_input_txt")
    if duro:
        w(f"- {duro}")
    else:
        w(f"- El informe publica el valor ({coma(o.get('valor'))} {o.get('unidad') or ''}) "
          "pero no los números que lo componen: la fuente entrega la serie ya calculada. "
          "Para auditar el dato hay que ir a la operación estadística citada más arriba.")
    w("")
    por_que = sem.get("por_que")
    if not por_que and indice is not None:
        tramo = next(t for t in UMBRALES_ITVC if t["color"] == sem.get("color"))
        por_que = (f"El componente está en {coma(indice, 1)} sobre la base 100 del 4º "
                   f"trimestre de 2023 — {tramo['texto']} —, que es el tramo "
                   f"{COLOR.get(sem.get('color'), '—')}.")
        # Los bordes de la escala son parte de la lectura, no una nota al pie: fuera
        # de [75, 125] la tensión queda acotada y el color deja de moverse con el
        # dato, así que la ficha no puede mostrar el color sin decirlo.
        if indice >= ITVC_WINSOR:
            por_que += (f" Está en el techo de winsorización ({coma(ITVC_WINSOR, 0)}): el "
                        "índice se recorta ahí, así que el valor real es mejor que el que "
                        "entra al cálculo y el semáforo ya no distingue mejoras.")
        elif indice > ITVC_TECHO:
            por_que += (" Supera el punto donde la tensión toca 0, así que el semáforo ya "
                        "no distingue mejoras adicionales: seguiría verde igual.")
        elif indice < ITVC_PISO:
            por_que += (" Está por debajo del punto donde la tensión toca 10, así que el "
                        "semáforo ya no distingue deterioros adicionales: seguiría rojo "
                        "igual.")
    if por_que:
        w("## Color vigente y por qué")
        w("")
        w(f"Dato vigente: {coma(o.get('valor'))} {o.get('unidad') or ''} "
          f"({(o.get('fecha_dato') or '')[:7]}).")
        w("")
        w(por_que)
        w("")
        w(f"**Color vigente: {COLOR.get(sem.get('color'), '—')}**")
        w("")
        if peso:
            w(f"Ponderación vigente en el {SIGLA}: {coma(peso * 100, 1)} % efectivo. "
              "El color es una lectura adicional — no reemplaza ni cambia esta ponderación.")
            w("")
    if campo(fichas_ts, ikey, "dobleUso"):
        w(f"- **Participación en otros indicadores.** {campo(fichas_ts, ikey, 'dobleUso')}")
        w("")
    if lims:
        w("## Transparencia — limitaciones declaradas")
        w("")
        for x in lims:
            w(f"- {x}")
        w("")
    w("## Si falta el dato / Política de revisiones")
    w("")
    w(f"- **Si falta el dato:** {campo(fichas_ts, ikey, 'faltantes') or '—'}")
    w("")
    w(f"- **Política de revisiones:** {campo(fichas_ts, ikey, 'revisiones') or '—'}")
    w("")
    cs = cambios(ikey)
    if cs:
        w("## Historial — cambios metodológicos documentados")
        w("")
        for fecha, texto in cs:
            w(f"**{fecha}** — {texto}")
            w("")

SALIDA_MD.write_text("\n".join(L), encoding="utf-8")
print("fichas:", len(ind), "| escrito:", SALIDA_MD.name, f"({len(chr(10).join(L)):,} caracteres)")
faltan = [k for k in ind if k not in LABELS]
print("sin nombre legible:", faltan or "ninguno")
