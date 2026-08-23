"""Que un cambio de datos no pueda dejar atrás el texto que lo describe.

El 21 de agosto de 2026 se publicó, durante días, una ficha técnica que
describía **entera** una fuente que el indicador ya no usaba: `mortalidad_pymes`
decía INDEC · IPI manufacturero —organismo, serie, transformaciones,
limitaciones y rezago— mientras el colector bajaba el XLSX de la SRT. En la
misma barrida apareció `trabajo_independiente`, que puntuaba con 2,42% del
ITCIS y no tenía ficha: la web lo mostraba y no había a dónde ir a leer qué
mide.

Ninguna guarda podía verlo, y el motivo es estructural: las que existían nacen
cada una de un incidente y cruzan **una frase concreta contra un número
concreto** (el peso, la dimensión, el «no puntúa»). Cubren el campo que alguien
ya se acordó de mirar. Nadie iba a escribir a mano la guarda del campo
`fuente.organismo` antes de que ese campo se rompiera.

Este archivo intenta otra cosa: guardas **genéricas**, que se aplican a todos
los indicadores a la vez y no hay que acordarse de extender cuando entra uno
nuevo. Son tres, y cada una cierra un tramo distinto del camino:

1. lo que se publica tiene ficha            → no se puede publicar a ciegas
2. la ficha declara la fuente que se usó    → la ficha no puede mentir la fuente
3. el ADR deja rastro en la ficha           → decidir el cambio obliga a contarlo

La tercera es la que importa a largo plazo. Las otras dos comparan estado con
estado; ésa engancha la guarda al **acto** de cambiar algo. El ADR ya es el
registro canónico de "cambiamos este indicador" y ya nombra los indicadores en
frontmatter legible por máquina: no hace falta acordarse de nada, no se puede
aceptar un ADR que toca un indicador sin dejar la entrada en su ficha.
"""
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
FICHAS = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
SNAPSHOT = json.loads((RAIZ / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
ADR_DIR = RAIZ / "docs" / "adr"

# A partir de acá se exige el rastro en la ficha. No se retrofitea lo anterior:
# el frontmatter `indicadores:` se usó con criterios distintos a lo largo del
# proyecto —hay ADRs que ahí nombran funciones del colector, no indicadores— y
# reescribir 88 fichas viejas para poder encender la guarda sería cambiar el
# registro histórico para que un test pase. De hoy en adelante el rastro es
# obligatorio, que es lo que evita el próximo caso.
DESDE = "2026-08-21"


def _bloque(texto: str, clave: str) -> str:
    r"""El objeto literal de un indicador, acotado a su propia llave.

    La sangría va con `[ \t]*` y no con `\s*`: `\s` incluye el salto de línea,
    la versión greedy arranca el match en la línea en blanco anterior y se lleva
    el `\n` adentro de la sangría; el cierre pasa a buscarse como `^\n  \},?$`,
    que no existe, y el bloque se extiende hasta el fin del archivo. Con eso, la
    aserción «esta frase tiene que estar en el bloque» pasa siempre.
    """
    m = re.search(rf"^([ \t]*){re.escape(clave)}: \{{$", texto, re.M)
    if not m:
        return ""
    fin = re.compile(rf"^{m.group(1)}\}},?$", re.M).search(texto, m.end())
    return texto[m.end():fin.start()] if fin else texto[m.end():]


def _indicadores_publicados():
    for ck, c in SNAPSHOT["cinturones"].items():
        for ik, ind in (c.get("indicadores") or {}).items():
            yield ck, ik, ind


def test_el_extractor_de_bloques_no_desborda():
    """La guarda de la guarda. Si `_bloque` vuelve a llevarse el archivo entero,
    todo lo de abajo pasa sin mirar nada — y pasar sin mirar es el modo en que
    esto falla: silencioso y con los tests en verde."""
    claves = re.findall(r"^  ([a-z_0-9]+): \{$", FICHAS, re.M)
    assert len(claves) > 50, "cambió la forma de fichas.ts: revisá el parser"
    desbordados = [k for k in claves if len(_bloque(FICHAS, k)) > 20_000]
    assert not desbordados, (
        "estos bloques se extienden más allá de su propia ficha, así que "
        "cualquier aserción sobre ellos es vacua: " + ", ".join(desbordados[:10]))


# ── 1 · Lo que se publica tiene ficha ───────────────────────────────────────
def test_todo_indicador_publicado_tiene_ficha_tecnica():
    claves = set(re.findall(r"^  ([a-z_0-9]+): \{$", FICHAS, re.M))
    sin = sorted({f"{ck}/{ik}" for ck, ik, _ in _indicadores_publicados()
                  if ik not in claves})
    assert not sin, (
        "estos indicadores se publican en la web y no tienen ficha, así que se "
        "muestran sin decir qué miden, de dónde salen ni qué no cubren: "
        + ", ".join(sin))


# ── 2 · La ficha declara la fuente que el colector realmente usó ────────────
# El snapshot trae, por indicador, la fuente que escribió el colector en la
# corrida: es la verdad de campo, regenerada todas las noches. La ficha declara
# un organismo a mano. Cruzarlas es lo que hubiera cantado el caso de la SRT en
# el acto, sin que nadie tuviera que preverlo.
#
# Las siglas se declaran acá porque un organismo se nombra de dos maneras
# legítimas —"UTDT" y "Universidad Torcuato Di Tella" son el mismo— y esa
# equivalencia tiene que estar escrita en algún lado en vez de adivinarse.
SIGLAS = {
    "AEA": "ASOCIACION EMPRESARIA ARGENTINA",
    "UIA": "UNION INDUSTRIAL ARGENTINA",
    "UTDT": "UNIVERSIDAD TORCUATO DI TELLA",
    "CSJN": "CORTE SUPREMA DE JUSTICIA DE LA NACION",
    "SSS": "SUPERINTENDENCIA DE SERVICIOS DE SALUD",
    "SRT": "SUPERINTENDENCIA DE RIESGOS DEL TRABAJO",
    "SIPA": "SISTEMA INTEGRADO PREVISIONAL ARGENTINO",
}

# Palabras que casi todos los organismos del Estado comparten. Sin sacarlas, el
# cotejo por palabras da por buena cualquier pareja: "Ministerio de Economía" y
# "Ministerio de Trabajo" comparten «ministerio» y pasarían.
GENERICAS = {
    "ministerio", "secretaria", "subsecretaria", "nacional", "nacion",
    "direccion", "instituto", "sistema", "argentina", "argentino", "gobierno",
    "oficina", "registro", "serie", "series", "datos", "base", "indice",
    "informe", "publica", "publico", "publicos", "total", "propia", "encuesta",
    "estadistica", "estadisticas", "tablero", "anuario", "general", "federal",
    "centro", "investigacion", "universidad",
}


def _sin_tildes(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _siglas(s: str) -> set:
    """Siglas de verdad: se leen del texto TAL CUAL, no de su versión en
    mayúsculas. La primera versión de esta función pasaba el string a
    mayúsculas y recién ahí buscaba `[A-Z]{3,}`, con lo cual toda palabra de
    tres letras contaba como sigla y el cotejo se volvía «comparten alguna
    palabra» — «Ministerio de Economía» daba por buena a «Ministerio de
    Trabajo». Acá una sigla es lo que estaba en mayúsculas en el original."""
    return set(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", _sin_tildes(s)))


def _palabras(s: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", _sin_tildes(s).lower())} - GENERICAS


def _mismo_organismo(declarado: str, real: str, url_ficha: str) -> bool:
    sd, sr = _siglas(declarado), _siglas(real)
    # Una sigla compartida sólo acredita identidad si está declarada como
    # organismo. `ART`, `IPC` o `PIB` pueden aparecer en dos fuentes distintas
    # por ser el objeto medido, no quien lo produce.
    if any(sigla in SIGLAS for sigla in sd & sr):
        return True
    # La expansión de una sigla se busca en EL OTRO lado. Buscarla en el propio
    # —como hacía la primera versión— da siempre verdadero: «SRT» expande a
    # «Superintendencia de Riesgos del Trabajo», que por supuesto aparece en el
    # string del que salió la sigla. Con eso, la SRT «coincidía» con el INDEC.
    for sigla, otro in ([(x, _sin_tildes(real).upper()) for x in sd]
                        + [(x, _sin_tildes(declarado).upper()) for x in sr]):
        largo = SIGLAS.get(sigla)
        if largo and largo in otro:
            return True
    # El colector a veces publica la URL de descarga como fuente: se compara el
    # host contra el de la ficha, que es la misma afirmación por otra vía.
    if real.strip().lower().startswith("http") and url_ficha:
        h1 = urlparse(real.strip()).netloc.lower().removeprefix("www.")
        h2 = urlparse(url_ficha.strip()).netloc.lower().removeprefix("www.")
        if h1 and h1 == h2:
            return True
    # Sin siglas compartidas: se comparan las palabras que distinguen. Hace
    # falta porque 14 de los 66 nombran su fuente sin ninguna sigla.
    return bool(_palabras(declarado) & _palabras(real))


def test_una_sigla_del_tema_no_hace_coincidir_dos_organismos_distintos():
    assert not _mismo_organismo(
        "INDEC — encuesta de cobertura de ART",
        "Superintendencia de Riesgos del Trabajo (SRT)",
        "",
    )


def test_una_sigla_institucional_declarada_si_acredita_la_misma_fuente():
    assert _mismo_organismo(
        "SRT",
        "Superintendencia de Riesgos del Trabajo",
        "",
    )


# Los dos de abajo son los que fijan la regla que distingue una sigla de
# organismo de una del objeto medido. Los dos de arriba pasan igual con la regla
# vieja (`if sd & sr`): en el primero las siglas no se intersecan y el False sale
# del cotejo por palabras; en el segundo la intersección también es vacía —el
# nombre largo no tiene siglas— y el True sale de la expansión.
def test_una_sigla_compartida_que_no_es_organismo_no_acredita_la_fuente():
    """Con la regla vieja esto daba verdadero: ficha y colector comparten «IPC»,
    que es lo medido y no quien lo mide, así que un cambio de organismo pasaba."""
    assert not _mismo_organismo(
        "INDEC — IPC nivel general",
        "UTDT — expectativas de IPC",
        "",
    )


def test_una_sigla_de_organismo_compartida_acredita_la_fuente_sin_expansion():
    """La contracara: sin este camino, dos formas del mismo organismo que sólo
    comparten la sigla no coincidirían por ninguna de las vías siguientes."""
    assert _mismo_organismo(
        "SRT — partes empleadoras con cobertura de ART",
        "SRT",
        "",
    )


def test_la_ficha_declara_la_fuente_que_el_colector_uso():
    malos, comparados = [], 0
    for ck, ik, ind in _indicadores_publicados():
        b = _bloque(FICHAS, ik)
        org = re.search(r'organismo:\s*"((?:[^"\\]|\\.)*)"', b)
        url = re.search(r'url:\s*"((?:[^"\\]|\\.)*)"', b)
        real = ind.get("fuente") or ""
        if not org or not real:
            continue
        comparados += 1
        if not _mismo_organismo(org.group(1), real, url.group(1) if url else ""):
            malos.append(f"{ck}/{ik}\n      ficha declara: {org.group(1)}\n"
                         f"      colector usó:  {real}")
    assert comparados > 50, f"sólo se pudieron comparar {comparados}: revisá el parser"
    assert not malos, (
        "la ficha declara un organismo que no es el que produjo el dato "
        "publicado. O cambió la fuente y la ficha se quedó atrás, o la sigla "
        "nueva hay que declararla en SIGLAS:\n  " + "\n  ".join(malos))


# ── 3 · Un ADR que toca un indicador deja rastro en su ficha ────────────────
def _adrs_con_indicadores():
    for p in sorted(ADR_DIR.glob("[0-9]*.md")):
        txt = p.read_text(encoding="utf-8")
        if not txt.startswith("---"):
            continue
        fm = txt.split("---")[1]
        def campo(k):
            m = re.search(rf"^{k}:\s*(.+)$", fm, re.M)
            return m.group(1).strip().strip("'\"") if m else ""
        inds, estado, fecha = campo("indicadores"), campo("estado"), campo("fecha")
        if not (inds and fecha):
            continue
        if estado not in ("aceptado", "aceptada"):
            continue
        claves = [x.strip().strip("'\"") for x in inds.strip("[]").split(",") if x.strip()]
        yield p.stem[:4], fecha, claves, campo("archivos")


# Un ADR que sólo toca tests o workflows no cambió el indicador: cambió cómo lo
# verificamos. ADR-0221 es el caso — recalibra el cable trampa de
# `litigiosidad_laboral` sin mover un dato— y la guardia disparó contra él a los
# cinco minutos de escrita. La salida NO es sacarle el indicador al frontmatter
# para que el test calle: eso es acomodar el registro a la herramienta. Es
# distinguir lo que de verdad son dos cosas distintas.
#
# Ante la duda se exige el rastro: un ADR sin `archivos:` entra igual.
SOLO_VERIFICACION = ("tests/", ".github/")


def _cambia_como_se_produce(archivos: str) -> bool:
    rutas = [x.strip().strip("'\"") for x in archivos.strip("[]").split(",") if x.strip()]
    if not rutas:
        return True
    return any(not r.startswith(SOLO_VERIFICACION) for r in rutas)


def test_hay_adrs_que_verificar():
    assert len(list(_adrs_con_indicadores())) > 50


def test_un_adr_que_toca_un_indicador_lo_cuenta_en_su_ficha():
    """El disparador. Un ADR aceptado que nombra un indicador es, por
    definición, una decisión sobre ese indicador: su ficha tiene que registrarla
    —citando el ADR o con una entrada de `cambios` de esa fecha o posterior—.

    Se exige sólo a los indicadores que TIENEN ficha: el frontmatter
    `indicadores:` también se usó para nombrar funciones del colector, y el
    hueco de "no tiene ficha" ya lo cierra la guarda 1 contra el snapshot."""
    faltan = []
    for num, fecha, claves, archivos in _adrs_con_indicadores():
        if fecha < DESDE or not _cambia_como_se_produce(archivos):
            continue
        for clave in claves:
            b = _bloque(FICHAS, clave)
            if not b:
                continue
            m = re.search(r"cambios:\s*\[(.*?)\n    \]", b, re.S)
            cambios = m.group(1) if m else ""
            fechas = re.findall(r'fecha:\s*"([0-9]{4}-[0-9]{2}(?:-[0-9]{2})?)"', cambios)
            if f"ADR-{num}" in cambios or any(f >= fecha[:len(f)] for f in fechas):
                continue
            faltan.append(f"ADR-{num} ({fecha}) decide sobre «{clave}» y su ficha "
                          f"no lo registra")
    assert not faltan, (
        "un ADR aceptado cambió estos indicadores y su ficha no se enteró. "
        "Agregá la entrada en `cambios:` con lo que cambió y por qué — es el "
        "texto que lee quien quiera saber si el número de hace seis meses se "
        "compara con el de hoy:\n  " + "\n  ".join(faltan))
