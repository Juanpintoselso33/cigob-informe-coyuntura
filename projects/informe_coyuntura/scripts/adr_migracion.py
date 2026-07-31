"""Herramienta de migración de los ADR al formato MADR.

Tres funciones, todas determinísticas y sin red:

    huella      calcula la huella de hechos verificables de cada ADR
                (cifras, identificadores, referencias cruzadas, URLs)
    verificar   compara el estado actual contra una huella guardada y
                falla si algún hecho desapareció en la reescritura
    cosechar    extrae los metadatos del encabezado (los dos formatos que
                conviven) para volcarlos al frontmatter YAML

El objetivo de `huella`/`verificar` es que una reescritura de 141.546
palabras de prosa metodológica sea auditable: ningún test del repo mira el
contenido de los ADR, así que una cifra alterada al reescribir pasaría
inadvertida. La huella es el único control que lo detecta.

Uso:
    python scripts/adr_migracion.py huella    > docs/adr/_huellas.json
    python scripts/adr_migracion.py verificar   docs/adr/_huellas.json
    python scripts/adr_migracion.py cosechar  > docs/adr/_metadatos.json
"""

from __future__ import annotations

import collections
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"

# --- patrones de hechos verificables -------------------------------------

RE_ADR_REF = re.compile(r"ADR[-\s]?(\d{4})")
RE_CODIGO = re.compile(r"`([^`\n]+)`")
RE_URL = re.compile(r"https?://[^\s)\]<>\"']+")
RE_FECHA = re.compile(r"\b(\d{4}-\d{2}(?:-\d{2})?)\b")
RE_COMMIT = re.compile(r"\b([0-9a-f]{7,40})\b")

# Números en notación castellana (1.058 · 0,325 · 2,19) y anglosajona (0.3).
# El orden importa: primero el caso con separador de miles.
RE_NUMERO = re.compile(
    r"(?<![\w-])"
    r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?"   # 1.058 · 141.546 · 1.058,50
    r"|\d+,\d+"                         # 0,325 · 2,19
    r"|\d+(?:\.\d+)?)"                  # 46 · 0.3
    r"(?![\w-])"
)


def _normalizar_numero(bruto: str) -> float | None:
    """Lleva 1.058 / 0,325 / 0.3 a un float comparable."""
    txt = bruto
    if "," in txt:  # castellano: el punto es separador de miles
        txt = txt.replace(".", "").replace(",", ".")
    elif txt.count(".") > 1:  # 1.058.200 sin decimales
        txt = txt.replace(".", "")
    elif re.fullmatch(r"\d{1,3}\.\d{3}", txt):
        # Ambiguo: 1.058 puede ser mil-cincuenta-y-ocho o uno-coma-cero-cinco-ocho.
        # En este corpus (castellano) domina el separador de miles.
        txt = txt.replace(".", "")
    try:
        return float(txt)
    except ValueError:
        return None


def _sin_acentos(txt: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn"
    )


RE_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_./:\[\]\"-]*")


def _identificadores_frontmatter(texto: str) -> set[str]:
    """Identificadores que la migración movió del cuerpo al frontmatter.

    Sin esto, mover `BANDAS_ITCP` del campo Ámbito a `parametros:` se lee
    como una pérdida: el extractor solo mira spans entre backticks. El dato
    sigue registrado, solo que en otro lugar del documento.
    """
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return set()
    tokens: set[str] = set()
    for linea in m.group(1).splitlines():
        _, _, valor = linea.partition(":")
        for t in RE_IDENT.findall(valor):
            tokens.add(t.strip("[],\"' "))
    return {t for t in tokens if t}


CAMPOS_RELACION = (
    # directas
    "supersede", "supersede_parcialmente", "relacionado",
    "corrige", "modifica", "extiende", "complementa", "revierte", "continua",
    "cierra",
    # inversas, escritas por adr_coherencia.py en el ADR apuntado
    "superado_por", "superado_parcialmente_por", "corregido_por",
    "modificado_por", "extendido_por", "complementado_por", "revertido_por",
    "continuado_por", "cerrado_por",
)


def _refs_frontmatter(texto: str) -> set[str]:
    """Referencias a otros ADR que la migración volvió campos estructurados.

    `Precedentes directos | ADR-0058 · ADR-0045` pasa a `relacionado: [0058,
    0045]`. La relación sigue registrada, pero sin la palabra «ADR» que el
    extractor de prosa busca.
    """
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return set()
    refs: set[str] = set()
    for linea in m.group(1).splitlines():
        clave, _, valor = linea.partition(":")
        if clave.strip() in CAMPOS_RELACION:
            refs.update(re.findall(r"\b(\d{4})\b", valor))
    return refs


CLAVES_ESTRUCTURALES = {
    "madr", "id", "estado", "fecha", "cinturon", "indice", "indicadores",
    "parametros", *CAMPOS_RELACION,
}


def _sin_frontmatter_estructural(texto: str) -> str:
    """Descarta del conteo de cifras solo los campos de máquina.

    Los campos de texto libre (`ambito`, `origen`, `nota_estado`) sí entran:
    la migración movió ahí prosa que traía cifras — nombres de documento
    como `260723`, números de dimensión — y descartarlas enteras hacía que
    el gate las leyera como pérdidas.
    """
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return texto
    conservado = []
    for linea in m.group(1).splitlines():
        clave, sep, valor = linea.partition(":")
        if sep and clave.strip() in CLAVES_ESTRUCTURALES:
            continue
        conservado.append(valor if sep else linea)
    return " ".join(conservado) + "\n" + texto[m.end():]


def huella_de(texto: str, nombre: str) -> dict:
    """Extrae los hechos que una reescritura NO puede perder."""
    propio = nombre[:4]

    numeros = set()
    conteo: collections.Counter[float] = collections.Counter()
    # Las referencias ADR-XXXX no son cifras sustantivas: se cuentan aparte.
    sin_refs = RE_ADR_REF.sub(" ", texto)
    sin_refs = _sin_frontmatter_estructural(sin_refs)
    for bruto in RE_NUMERO.findall(sin_refs):
        valor = _normalizar_numero(bruto)
        if valor is not None:
            numeros.add(valor)
            conteo[valor] += 1

    codigos = {c.strip() for c in RE_CODIGO.findall(texto) if c.strip()}
    codigos |= _identificadores_frontmatter(texto)
    urls = set(RE_URL.findall(texto))
    refs = {r for r in RE_ADR_REF.findall(texto) if r != propio}
    refs |= _refs_frontmatter(texto) - {propio}
    fechas = set(RE_FECHA.findall(texto))

    # Hashes de commit: solo los que aparecen entre backticks, para no
    # confundir con cualquier cadena hexadecimal suelta.
    commits = {c for c in codigos if RE_COMMIT.fullmatch(c)}

    return {
        "numeros": sorted(numeros),
        # Cuántas veces aparece cada cifra. Sin esto el gate no ve una
        # sustitución: cambiar 2,19 por 2,45 en un párrafo deja el valor
        # 2,19 "presente" si además figura en una tabla, y la falla pasa.
        "numeros_conteo": {str(k): v for k, v in sorted(conteo.items())},
        "codigos": sorted(codigos),
        "urls": sorted(urls),
        "refs_adr": sorted(refs),
        "fechas": sorted(fechas),
        "commits": sorted(commits),
        "palabras": len(texto.split()),
    }


# --- cosecha de metadatos del encabezado ----------------------------------

CAMPOS = ["Estado", "Fecha", "Ámbito", "Origen", "Commit", "Precedentes directos"]


def cosechar_de(texto: str) -> dict:
    """Lee el encabezado en cualquiera de los dos formatos que conviven.

    Formato A (124 archivos):   | **Estado** | Aceptado |
    Formato B (40 archivos):    - **Estado:** aceptada
    """
    meta: dict[str, str] = {}
    cabecera = texto[:2500]

    for campo in CAMPOS:
        clave = _sin_acentos(campo).lower().replace(" ", "_")
        patron_tabla = re.compile(
            r"^\|\s*\*\*" + re.escape(campo) + r":?\*\*\s*\|(.+?)\|?\s*$",
            re.M | re.I,
        )
        patron_lista = re.compile(
            r"^[-*]\s*\*\*" + re.escape(campo) + r":?\*\*:?\s*(.+?)\s*$",
            re.M | re.I,
        )
        for patron in (patron_tabla, patron_lista):
            m = patron.search(cabecera)
            if m:
                meta[clave] = m.group(1).strip().rstrip("|").strip()
                break

    titulo = ""
    m = re.search(r"^#\s+(.+?)\s*$", texto, re.M)
    if m:
        titulo = m.group(1).strip()
    meta["titulo"] = titulo

    # Secciones presentes, para saber qué hay que remapear.
    meta["secciones"] = re.findall(r"^##\s+(.+?)\s*$", texto, re.M)

    return meta


# --- relaciones entre ADRs ------------------------------------------------

VERBOS = {
    "supersede": "supersedes",
    "reemplaza a": "supersedes",
    "deroga": "supersedes",
    "superado por": "superseded_by",
    "supersedido por": "superseded_by",
    "revierte": "revierte",
    "corrige": "corrige",
    "modifica": "modifica",
    "extiende": "extiende",
    "complementa": "complementa",
    "continua": "continua",
    "cierra": "cierra",
}


def relaciones_de(texto: str, nombre: str) -> dict[str, list[str]]:
    """Cosecha relaciones declaradas en prosa: «supersede al ADR-0050».

    Solo mira el encabezado y la primera sección: más abajo las menciones
    suelen ser narrativas ("como decidió ADR-0045"), no declarativas.
    """
    propio = nombre[:4]
    cabecera = _sin_acentos(texto[:2500]).lower()
    hallazgos: dict[str, set[str]] = {}

    for verbo, relacion in VERBOS.items():
        for m in re.finditer(re.escape(verbo) + r"[^.\n]{0,60}?adr[-\s]?(\d{4})", cabecera):
            num = m.group(1)
            if num != propio:
                hallazgos.setdefault(relacion, set()).add(num)
        # variante sin la palabra ADR: «supersede 0050»
        for m in re.finditer(re.escape(verbo) + r"\s+(?:al\s+|a\s+)?(\d{4})\b", cabecera):
            num = m.group(1)
            if num != propio:
                hallazgos.setdefault(relacion, set()).add(num)

    return {k: sorted(v) for k, v in hallazgos.items()}


# --- comandos -------------------------------------------------------------

def _archivos() -> list[Path]:
    return sorted(p for p in ADR_DIR.glob("[0-9]*.md"))


def _texto_en_head(p: Path) -> str | None:
    """Contenido del archivo tal como está commiteado en HEAD."""
    raiz = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, cwd=ADR_DIR,
        ).stdout.strip()
    )
    rel = p.resolve().relative_to(raiz).as_posix()
    r = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        capture_output=True, cwd=raiz,
    )
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8")


def cmd_huella(desde_git: bool = False) -> None:
    """Congela la línea de base.

    Con --git lee la versión commiteada en HEAD en vez del árbol de
    trabajo: así la base es siempre el estado previo a la migración y el
    comando se puede volver a correr aunque ya haya ADR reescritos sin
    commitear.
    """
    salida = {}
    for p in _archivos():
        texto = _texto_en_head(p) if desde_git else p.read_text(encoding="utf-8")
        if texto is None:
            print(f"aviso: {p.name} no está en HEAD, se omite", file=sys.stderr)
            continue
        salida[p.name] = huella_de(texto, p.name)
    print(json.dumps(salida, ensure_ascii=False, indent=1))


def cmd_cosechar() -> None:
    salida = {}
    for p in _archivos():
        texto = p.read_text(encoding="utf-8")
        salida[p.name] = {
            **cosechar_de(texto),
            "relaciones": relaciones_de(texto, p.name),
        }
    print(json.dumps(salida, ensure_ascii=False, indent=1))


def cmd_verificar(ruta_huellas: str) -> int:
    base = json.loads(Path(ruta_huellas).read_text(encoding="utf-8"))
    fallas: list[str] = []
    avisos: list[str] = []

    actuales = {p.name: p for p in _archivos()}

    for nombre, esperado in base.items():
        if nombre not in actuales:
            fallas.append(f"{nombre}: el archivo desapareció")
            continue
        ahora = huella_de(actuales[nombre].read_text(encoding="utf-8"), nombre)

        for campo in ("numeros", "codigos", "urls", "refs_adr", "commits"):
            faltan = set(map(_clave, esperado[campo])) - set(map(_clave, ahora[campo]))
            if faltan:
                muestra = ", ".join(sorted(map(str, faltan))[:8])
                fallas.append(
                    f"{nombre}: perdió {len(faltan)} {campo} en la reescritura → {muestra}"
                )

        # Sustituciones de cifras: una repetición que baja de conteo, o una
        # cifra nueva que no existía, delatan un número cambiado aunque el
        # valor viejo siga apareciendo en otra parte del documento.
        antes_c = collections.Counter(
            {float(k): v for k, v in esperado.get("numeros_conteo", {}).items()}
        )
        ahora_c = collections.Counter(
            {float(k): v for k, v in ahora["numeros_conteo"].items()}
        )
        bajaron = {k: (v, ahora_c.get(k, 0)) for k, v in antes_c.items() if ahora_c.get(k, 0) < v}
        if bajaron:
            muestra = ", ".join(f"{k:g} ({a}→{b})" for k, (a, b) in list(bajaron.items())[:6])
            fallas.append(f"{nombre}: cifras que pierden apariciones → {muestra}")
        nuevas = {k for k in ahora_c if k not in antes_c}
        if nuevas:
            muestra = ", ".join(f"{k:g}" for k in sorted(nuevas)[:8])
            avisos.append(
                f"{nombre}: {len(nuevas)} cifra(s) que no estaban en el original → {muestra}"
                " — confirmar que no sea una sustitución"
            )

        antes, despues = esperado["palabras"], ahora["palabras"]
        if despues < antes * 0.55:
            avisos.append(
                f"{nombre}: el cuerpo bajó de {antes} a {despues} palabras "
                f"({100 - despues * 100 // antes}% menos) — revisar que no se haya podado contenido"
            )

    for nombre in actuales:
        if nombre not in base:
            avisos.append(f"{nombre}: ADR nuevo, sin huella previa")

    for a in avisos:
        print(f"AVISO  {a}")
    for f in fallas:
        print(f"FALLA  {f}")

    print(
        f"\n{len(base)} ADR verificados · {len(fallas)} fallas · {len(avisos)} avisos"
    )
    return 1 if fallas else 0


def _clave(v):
    """Normaliza para comparar: los floats se redondean, el resto va tal cual."""
    return round(v, 6) if isinstance(v, float) else v


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "huella":
        cmd_huella(desde_git="--git" in sys.argv)
        return 0
    if cmd == "cosechar":
        cmd_cosechar()
        return 0
    if cmd == "verificar":
        if len(sys.argv) < 3:
            print("falta la ruta del archivo de huellas")
            return 2
        return cmd_verificar(sys.argv[2])
    print(f"comando desconocido: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
