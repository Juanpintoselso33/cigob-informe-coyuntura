"""Las fichas generadas tienen que decir el mismo dato que el snapshot.

`output/fichas/*.md` lo escribe `scripts/fichas/generar.py` leyendo
`web/src/data/informe.json`. Hasta ADR-0260 ese script **no estaba en el
pipeline nocturno**: el snapshot avanzaba todas las noches y el artefacto se
quedaba donde alguien lo hubiera dejado la última vez que se acordó de correrlo
a mano. Como nadie lo compara con nada, la deriva no rompe nada — se publica.

No son archivos decorativos. `CLAUDE.md` los nombra como el material de ingesta
para modelos (`output/informe.md` y `output/fichas/*.md` son lo único que entra
en una ventana de contexto; el HTML autocontenido son 1,5 millones de tokens),
así que un número viejo ahí se propaga a cualquier análisis que los lea, y lo
hace con el aspecto de un dato publicado.

La auditoría del 25-ago-2026 lo encontró en `consumo_supermercados`: la ficha
decía mayo = 83,2 mientras la card, la serie y el colector ya publicaban junio =
82,1. Al regenerar aparecieron dos más que nadie había mirado —el ITCM entero
(64,1 contra 64,8) y `desequilibrio_monetario` (50,86 AMARILLO contra 38,69
VERDE)—, que es la razón por la que esta guarda recorre **todos** los
indicadores y no sólo el del hallazgo: una guarda por indicador no se extiende
sola al siguiente.

Qué compara, para cada indicador de cada cinturón:
  · el **período** del dato (`fecha_dato`), en el banner «Hoy:» y en la línea
    «Dato vigente:»;
  · el **valor** y su unidad, en el banner, en la tabla resumen de la portada y
    en «Dato vigente:»;
  · el **puntaje**: el color del semáforo (banner, tabla resumen y «Color
    vigente»), el peso efectivo en el índice, y el índice base-100 del ITCIS
    donde corresponde.
Y en la portada: el valor y el color del índice del cinturón, el recuento de
indicadores por color, y el puntaje, el color y el peso de cada dimensión.

Qué NO compara, a propósito: la prosa. Que el texto de una ficha describa el
indicador que realmente se está midiendo ya lo cuida
`test_la_ficha_no_se_queda_atras.py` (ADR-0220), y duplicarlo acá haría fallar
esta guarda por una coma editada en `fichas.ts`, que es la forma rápida de que
se la empiece a ignorar.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "fichas"))
from comun import CINTURONES, COLOR, clave_indice, coma, labels, ruta_md  # noqa: E402

INFORME = json.loads(
    (ROOT / "web/src/data/informe.json").read_text(encoding="utf-8-sig"))
LABELS = labels()

# El separador de página que mete `generar.py` entre la portada y cada ficha.
# Se usa para cortar el documento en bloques: cada ficha es exactamente un
# bloque, y cada bloque de ficha tiene una sola fila de IDENTIFICADOR TÉCNICO.
SALTO = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'

RE_BANNER = re.compile(
    r"^\| \*\*Hoy: (?P<hoy>.*?)\*\* \((?P<periodo>[^)]*)\) \| "
    r"\*\*(?P<color>[^*]+)\*\* \| (?P<peso>[^|]*?) \| Cinturón ",
    re.M)
RE_IDENT = re.compile(r"^\| \*\*IDENTIFICADOR TÉCNICO\*\* \| (\S+) \|", re.M)
RE_DATO_VIGENTE = re.compile(
    r"^Dato vigente: (?P<hoy>.*?) \((?P<periodo>[^)]*)\)\.$", re.M)
RE_COLOR_VIGENTE = re.compile(r"^\*\*Color vigente: (?P<color>[^*]+)\*\*$", re.M)
RE_INDICE_ITVC = re.compile(r"^Este componente está hoy en \*\*(?P<v>[^*]+)\*\*\.$", re.M)
RE_INDICE_ITVC_PROSA = re.compile(r"^El componente está en (?P<v>\S+) sobre la base 100", re.M)


def _norm(s: str) -> str:
    """`generar.py` usa espacios de no separación a propósito —«ITCIS\u00a093,8»,
    «10,4\u00a0%»— para que Word no parta el número de su unidad. Es una decisión
    tipográfica del artefacto, no un dato: se normaliza a los dos lados de cada
    comparación, como ya hace `verificar.py` con lo que Word agrega por su
    cuenta."""
    return s.replace("\u00a0", " ")


def _celdas(linea: str) -> list[str]:
    """Las celdas de una fila de tabla markdown, sin los pipes de los bordes."""
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def _bloques(texto: str) -> list[str]:
    return texto.split(SALTO)


def _fichas(texto: str) -> dict[str, str]:
    """{identificador técnico: bloque de esa ficha}."""
    out = {}
    for bloque in _bloques(texto):
        ids = RE_IDENT.findall(bloque)
        assert len(ids) <= 1, f"un bloque con {len(ids)} identificadores: {ids}"
        if ids:
            out[ids[0]] = bloque
    return out


def _tabla(texto: str, titulo: str) -> list[list[str]]:
    """Las filas de datos de la tabla que sigue a un título `## …`."""
    i = texto.find(f"\n## {titulo}\n")
    if i < 0:
        return []
    filas = []
    for linea in texto[i:].splitlines()[1:]:
        if linea.startswith("|"):
            filas.append(_celdas(linea))
        elif filas and not linea.strip():
            break                         # la tabla termina en la línea en blanco
    # la primera fila es el encabezado y la segunda el separador |---|
    return filas[2:]


def _hoy_esperado(o: dict) -> str:
    return f"{coma(o.get('valor'))} {o.get('unidad') or ''}".strip()


def _peso_banner_esperado(o: dict, sigla: str) -> str:
    peso = o.get("peso_efectivo")
    if peso:
        return f"Peso efectivo {coma(peso * 100, 1)} % del {sigla}"
    return "Fuera del índice"


def _peso_resumen_esperado(o: dict) -> str:
    peso = o.get("peso_efectivo")
    if peso:
        return f"{coma(peso * 100, 1, recortar=False)} %"
    if o.get("cumplido"):
        return "fuera: promesa cumplida"
    if o.get("suspendido"):
        return "fuera: suspendido, en revisión"
    return "fuera del índice"


def _revisar_cinturon(cint: str, problemas: list[str]) -> int:
    """Cruza la ficha generada del cinturón contra el snapshot. Devuelve cuántas
    comparaciones hizo, para que la guarda pueda probar que miró algo."""
    sigla, _nombre = CINTURONES[cint]
    ruta = ruta_md(cint)
    assert ruta.exists(), (
        f"falta {ruta.relative_to(ROOT)}: el cinturón publica indicadores pero "
        f"no tiene ficha generada. Correr `python scripts/fichas/generar.py --todos`.")
    texto = ruta.read_text(encoding="utf-8")
    ind = INFORME["cinturones"][cint]["indicadores"]
    fichas = _fichas(texto)
    comparaciones = 0

    def falla(que, dice, deberia):
        problemas.append(f"{cint}: {que} dice «{dice}», el snapshot dice «{deberia}»")

    def igual(que, dice, deberia):
        nonlocal comparaciones
        comparaciones += 1
        if _norm(dice) != _norm(deberia):
            falla(que, dice, deberia)

    faltan = sorted(set(ind) - set(fichas))
    sobran = sorted(set(fichas) - set(ind))
    if faltan:
        problemas.append(f"{cint}: el snapshot publica indicadores sin ficha: {faltan}")
    if sobran:
        problemas.append(f"{cint}: la ficha conserva indicadores que el snapshot "
                         f"ya no publica: {sobran}")

    # ── una ficha por indicador ──────────────────────────────────────────────
    for ikey, o in ind.items():
        bloque = fichas.get(ikey)
        if bloque is None:
            continue
        sem = o.get("semaforo") or {}
        periodo = (o.get("fecha_dato") or "")[:7]
        color = COLOR.get(sem.get("color"), "—")

        m = RE_BANNER.search(bloque)
        if not m:
            problemas.append(f"{cint}/{ikey}: no se pudo leer el banner «Hoy:»")
            continue
        igual(f"{ikey}: el banner", m["hoy"].strip(), _hoy_esperado(o))
        igual(f"{ikey}: el período del banner", m["periodo"], periodo)
        igual(f"{ikey}: el color del banner", m["color"], color)
        igual(f"{ikey}: el peso del banner", m["peso"],
              _peso_banner_esperado(o, sigla))

        # «Dato vigente» y «Color vigente» sólo existen si la ficha tiene la
        # sección «Color vigente y por qué»; el generador la omite cuando el
        # snapshot no trae un `por_que` ni un índice base-100.
        m = RE_DATO_VIGENTE.search(bloque)
        if m:
            igual(f"{ikey}: «Dato vigente»", m["hoy"].strip(), _hoy_esperado(o))
            igual(f"{ikey}: el período de «Dato vigente»", m["periodo"], periodo)
        m = RE_COLOR_VIGENTE.search(bloque)
        if m:
            igual(f"{ikey}: «Color vigente»", m["color"], color)

        # El índice base-100 del ITCIS es el puntaje con el que ese componente
        # entra al cinturón: si queda viejo, la ficha explica un color con un
        # número que ya no es el que lo produjo.
        i100 = o.get("indice_itvc")
        if i100 is not None:
            for rx, que in ((RE_INDICE_ITVC, "«está hoy en»"),
                            (RE_INDICE_ITVC_PROSA, "el índice base-100 en prosa")):
                m = rx.search(bloque)
                if m:
                    igual(f"{ikey}: {que}", m["v"], coma(i100, 1))

    # ── portada: tabla «Todos los indicadores» ───────────────────────────────
    por_label = {}
    for ikey in ind:
        por_label.setdefault(LABELS.get(ikey, ikey), []).append(ikey)
    repetidos = {k: v for k, v in por_label.items() if len(v) > 1}
    assert not repetidos, f"{cint}: rótulos repetidos, la tabla no se puede cruzar: {repetidos}"

    vistos = set()
    for fila in _tabla(texto, "Todos los indicadores"):
        if fila[0].startswith("**DIMENSIÓN:"):
            continue
        ikeys = por_label.get(fila[0])
        if not ikeys:
            problemas.append(f"{cint}: la tabla resumen lista «{fila[0]}», que no "
                             f"corresponde a ningún indicador del snapshot")
            continue
        ikey = ikeys[0]
        vistos.add(ikey)
        o = ind[ikey]
        igual(f"{ikey}: la tabla resumen (valor)", fila[2], _hoy_esperado(o))
        igual(f"{ikey}: la tabla resumen (color)", fila[3],
              COLOR.get((o.get("semaforo") or {}).get("color"), "—"))
        if len(fila) > 4:
            igual(f"{ikey}: la tabla resumen (peso)", fila[4], _peso_resumen_esperado(o))
    faltan_tabla = sorted(set(ind) - vistos)
    if faltan_tabla:
        problemas.append(f"{cint}: la tabla resumen de la portada no lista "
                         f"{faltan_tabla}")

    # ── portada: el índice del cinturón y sus dimensiones ────────────────────
    idx = INFORME["cinturones"][cint].get(clave_indice(INFORME["cinturones"][cint]))
    if idx:
        conteo = {}
        for o in ind.values():
            c = (o.get("semaforo") or {}).get("color")
            conteo[c] = conteo.get(c, 0) + 1
        resumen = " · ".join(f"{conteo[c]} en {c}"
                             for c in ("verde", "amarillo", "naranja", "rojo")
                             if conteo.get(c))
        fila = _tabla(texto, f"{sigla} — el índice del cinturón")
        assert fila, f"{cint}: no se pudo leer la fila del índice en la portada"
        f0 = fila[0]
        igual(f"{sigla}: el valor del índice", f0[0],
              f"**{sigla}: {coma(idx.get('valor'), 1, recortar=False)}**")
        igual(f"{sigla}: el color del índice", f0[1],
              f"**{COLOR.get((idx.get('semaforo') or {}).get('color'), '—')}**")
        igual(f"{sigla}: la banda del índice", f0[2],
              idx.get("banda_legible") or idx.get("banda") or "—")
        igual(f"{sigla}: el recuento por color", f0[3],
              f"{len(ind)} indicadores: {resumen}")

        dims = idx.get("dimensiones") or {}
        filas = {f[0]: f for f in _tabla(texto, "Dimensiones")}
        for dk, d in dims.items():
            nombre = d.get("nombre") or dk
            f = filas.get(nombre)
            if f is None:
                problemas.append(f"{cint}: la portada no muestra la dimensión «{nombre}»")
                continue
            igual(f"dimensión {nombre}: el puntaje", f[2],
                  coma(d.get("puntaje"), 1, recortar=False))
            igual(f"dimensión {nombre}: el color", f[3],
                  COLOR.get((d.get("semaforo") or {}).get("color"), "—"))
            igual(f"dimensión {nombre}: el peso", f[4],
                  f"{coma((d.get('peso') or 0) * 100, 1, recortar=False)} %")

    return comparaciones


def test_las_fichas_generadas_dicen_el_dato_del_snapshot():
    problemas: list[str] = []
    for cint in CINTURONES:
        _revisar_cinturon(cint, problemas)
    assert not problemas, (
        "las fichas generadas quedaron atrás del snapshot. Se regeneran con\n"
        "    .venv/bin/python scripts/fichas/generar.py --todos\n"
        "y el commit tiene que llevar output/fichas/*.md.\n  "
        + "\n  ".join(problemas))


def test_los_cinturones_con_ficha_son_los_del_snapshot():
    """Un cinturón nuevo sin ficha, o una ficha de uno retirado, no se detecta
    sola: el generador se llama por nombre y el que no está no se pide."""
    assert set(CINTURONES) == set(INFORME["cinturones"]), (
        f"scripts/fichas/comun.py declara {sorted(CINTURONES)} y el snapshot "
        f"publica {sorted(INFORME['cinturones'])}")
    huerfanas = sorted(p.name for p in (ROOT / "output/fichas").glob("fichas-*.md")
                       if p.name[len("fichas-"):-len(".md")] not in CINTURONES)
    assert not huerfanas, (
        f"quedan fichas .md de cinturones que el snapshot ya no publica: {huerfanas}")


def test_la_guarda_mira_algo():
    """Un parser que no matchea nada no falla: pasa. Los pisos van por debajo de
    lo que hay hoy (65 indicadores en cuatro cinturones, ~470 comparaciones)
    para no romperse cuando entre un indicador, pero lo bastante alto como para
    que un cambio de formato del generador se note."""
    problemas: list[str] = []
    total = sum(_revisar_cinturon(c, problemas) for c in CINTURONES)
    assert total >= 400, f"sólo se hicieron {total} comparaciones: ¿cambió el formato?"
    assert len(LABELS) >= 60, f"sólo se leyeron {len(LABELS)} rótulos de datos.ts"
    for cint in CINTURONES:
        fichas = _fichas(ruta_md(cint).read_text(encoding="utf-8"))
        esperadas = len(INFORME["cinturones"][cint]["indicadores"])
        assert len(fichas) == esperadas, (
            f"{cint}: se parsearon {len(fichas)} fichas y el snapshot publica "
            f"{esperadas} indicadores")
