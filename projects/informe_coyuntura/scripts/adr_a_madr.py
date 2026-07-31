"""Migra los ADR al formato MADR v4: frontmatter YAML + secciones canónicas.

Hace solo lo mecánico y verificable:

  - unifica los dos formatos de encabezado (tabla-pipe y lista-bullet) en
    frontmatter YAML,
  - normaliza el estado a un vocabulario cerrado, guardando el matiz
    original en `nota_estado` en vez de tirarlo,
  - cosecha las relaciones entre ADR declaradas en prosa,
  - renombra y reordena las secciones conocidas al esqueleto MADR.

Lo que NO hace, porque exige juicio y se resuelve a mano después:

  - partir «Contexto» en contexto + factores de decisión,
  - recuperar opciones consideradas que el ADR original no registró,
  - reubicar secciones narrativas idiosincrásicas (314 títulos distintos
    usados una o dos veces).

Esos archivos quedan listados en el informe final como pendientes de
revisión. Nada se inventa y nada se borra: el contenido no reconocido se
preserva bajo «Más información».

Uso:
    python scripts/adr_a_madr.py --simular   # informe, sin escribir
    python scripts/adr_a_madr.py             # escribe los 164
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"

CAMPOS = ["Estado", "Fecha", "Ámbito", "Origen", "Commit", "Precedentes directos"]


def sin_acentos(txt: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn"
    ).lower()


# --- secciones canónicas MADR ---------------------------------------------

A_CONTEXTO = {
    "contexto", "el planteo", "el problema", "el hecho", "el hallazgo",
    "lo que se encontro", "contexto y planteo del problema", "planteo",
    "el contexto", "diagnostico", "el diagnostico", "la observacion",
}
A_FACTORES = {"factores de decision", "criterios", "drivers"}
A_OPCIONES = {"opciones consideradas", "opciones descartadas", "alternativas"}
A_DECISION = {"decision", "la decision", "decision adoptada", "que se decide"}
A_CONSECUENCIAS = {"consecuencias", "resultado", "el resultado", "efectos"}
A_CONFIRMACION = {"guardia", "confirmacion", "verificacion", "guardias"}
A_LIMITACIONES = {
    "limitaciones", "limitaciones declaradas", "limitacion",
    "limitacion declarada", "lo que este adr no resuelve",
    "lo que este adr no hace", "lo que esta regla no hace",
}


BUCKETS = (
    (A_CONTEXTO, "contexto"), (A_FACTORES, "factores"), (A_OPCIONES, "opciones"),
    (A_DECISION, "decision"), (A_CONSECUENCIAS, "consecuencias"),
    (A_CONFIRMACION, "confirmacion"), (A_LIMITACIONES, "limitaciones"),
)

# Encabezados que sí anuncian una sección canónica pero con título propio.
# «Decisión 1 — Concesiones: ...» (ADR-0019 tiene siete) o «Por qué se
# rechaza» son decisiones; sin esto quedaban fuera de la sección Decisión y
# el ADR aparecía como si no hubiera decidido nada.
PREFIJOS = [
    ("decision", "decision"),
    ("lo que se implemento", "decision"),
    ("que corrige", "decision"),
    ("por que se rechaza", "decision"),
    ("que se decide", "decision"),
    ("la pregunta", "contexto"),
    ("el planteo", "contexto"),
    ("problema ", "contexto"),
    ("hallazgos", "contexto"),
    ("lo que se encontro", "contexto"),
    ("analisis", "factores"),
    ("practicas de referencia", "factores"),
    ("opciones", "opciones"),
    ("resultados de la validacion", "consecuencias"),
    ("condiciones de reapertura", "consecuencias"),
    ("limitaciones", "limitaciones"),
]


def _normalizar_titulo(titulo: str) -> str:
    t = sin_acentos(titulo).strip().rstrip(":").strip()
    return re.sub(r"^\d+[.)]\s*", "", t)


def clasificar(titulo: str) -> str | None:
    t = _normalizar_titulo(titulo)
    for conjunto, nombre in BUCKETS:
        if t in conjunto:
            return nombre
    for prefijo, nombre in PREFIJOS:
        if t.startswith(prefijo):
            return nombre
    return None


def es_titulo_generico(titulo: str, bucket: str) -> bool:
    """¿El título no dice nada que el nombre canónico no diga ya?

    «## Contexto» no aporta nada sobre «Contexto y planteo del problema», así
    que se absorbe. «## Decisión 2 — Compensabilidad entre dimensiones» sí
    aporta, y se conserva como subtítulo.
    """
    t = _normalizar_titulo(titulo)
    for conjunto, nombre in BUCKETS:
        if nombre == bucket:
            return t in conjunto
    return False


# --- encabezado -----------------------------------------------------------

def leer_encabezado(texto: str) -> tuple[dict, str]:
    """Extrae los campos del encabezado y devuelve (meta, cuerpo_sin_encabezado)."""
    meta: dict[str, str] = {}
    lineas = texto.splitlines()

    # El encabezado vive entre el título y la primera sección ##.
    fin = len(lineas)
    for i, ln in enumerate(lineas):
        if ln.startswith("## "):
            fin = i
            break
    cabecera = "\n".join(lineas[:fin])

    for campo in CAMPOS:
        clave = sin_acentos(campo).replace(" ", "_")
        for patron in (
            re.compile(r"^\|\s*\*\*" + re.escape(campo) + r":?\*\*\s*\|(.+?)\|?\s*$", re.M | re.I),
            re.compile(r"^[-*]\s*\*\*" + re.escape(campo) + r":?\*\*:?\s*(.+?)\s*$", re.M | re.I),
        ):
            m = patron.search(cabecera)
            if m:
                meta[clave] = m.group(1).strip().rstrip("|").strip()
                break

    # Se borran del cuerpo las filas de tabla y los bullets del encabezado,
    # más la fila separadora |---|---| y la tabla vacía | | |.
    limpio = []
    for i, ln in enumerate(lineas):
        if i >= fin:
            limpio.append(ln)
            continue
        es_campo = any(
            re.match(r"^\|?\s*[-*]?\s*\*\*" + re.escape(c) + r":?\*\*", ln, re.I)
            for c in CAMPOS
        )
        es_borde = re.fullmatch(r"\s*\|[\s|:-]*\|\s*", ln or " ")
        if es_campo or es_borde:
            continue
        limpio.append(ln)

    return meta, "\n".join(limpio)


def normalizar_estado(bruto: str) -> tuple[str, str]:
    """Vocabulario cerrado + el matiz original preservado como nota."""
    t = sin_acentos(re.sub(r"[*\[\]]", "", bruto)).strip()
    if "rechaz" in t:
        estado = "rechazado"
    elif "superad" in t or "supersedid" in t:
        estado = "superado"
    elif "parcial" in t:
        estado = "parcial"
    elif "propuest" in t or "pendiente" in t:
        estado = "propuesto"
    else:
        estado = "aceptado"
    # La nota solo se guarda si dice algo más que la palabra sola.
    nota = bruto.strip()
    escueto = re.fullmatch(r"\*{0,2}(aceptad[oa]|rechazad[oa])\*{0,2}\.?", nota, re.I)
    return estado, "" if escueto else nota


CINTURONES = [
    ("transversal", "transversal"), ("itcp", "politica"), ("politica", "politica"),
    ("itcg", "gestion"), ("gestion", "gestion"), ("itcm", "macro"), ("macro", "macro"),
    ("itvc", "vida"), ("vida cotidiana", "vida"), ("espiritu", "espiritu"),
]

EXT_ARCHIVO = (".py", ".ts", ".astro", ".json", ".csv", ".md", ".yml", ".docx", ".tsx")


def partir_ambito(ambito: str) -> dict:
    """Deriva cinturón, indicadores, parámetros y archivos del campo Ámbito."""
    if not ambito:
        return {}
    codigos = re.findall(r"`([^`]+)`", ambito)
    indicadores, parametros, archivos = [], [], []
    for c in codigos:
        c = c.strip()
        if any(c.endswith(e) or e + ":" in c or e + "`" in c for e in EXT_ARCHIVO) or "/" in c:
            archivos.append(c)
        elif c.isupper() or re.fullmatch(r"[A-Z][A-Z0-9_]+(\[.*\])?", c):
            parametros.append(c)
        elif re.fullmatch(r"[a-z][a-z0-9_]*", c):
            indicadores.append(c)
        else:
            archivos.append(c)

    plano = sin_acentos(ambito)
    cinturon = ""
    for aguja, nombre in CINTURONES:
        if aguja in plano:
            cinturon = nombre
            break

    return {
        "cinturon": cinturon,
        "indicadores": indicadores,
        "parametros": parametros,
        "archivos": archivos,
    }


VERBOS = {
    "supersede": "supersede", "reemplaza a": "supersede", "deroga": "supersede",
    "superado por": "superado_por", "supersedido por": "superado_por",
    "revierte": "revierte", "corrige": "corrige", "modifica": "modifica",
    "extiende": "extiende", "complementa": "complementa", "cierra": "cierra",
    "continua": "continua",
}


def cosechar_relaciones(texto: str, propio: str) -> dict[str, list[str]]:
    cabecera = sin_acentos(texto[:2500])
    out: dict[str, set[str]] = {}
    for verbo, rel in VERBOS.items():
        for pat in (
            re.escape(verbo) + r"[^.\n]{0,60}?adr[-\s]?(\d{4})",
            re.escape(verbo) + r"\s+(?:al\s+|a\s+)?(\d{4})\b",
        ):
            for m in re.finditer(pat, cabecera):
                if m.group(1) != propio:
                    out.setdefault(rel, set()).add(m.group(1))
    return {k: sorted(v) for k, v in out.items()}


def refs_del_encabezado(meta: dict, propio: str) -> list[str]:
    txt = meta.get("precedentes_directos", "") + " " + meta.get("origen", "")
    return sorted({r for r in re.findall(r"ADR[-\s]?(\d{4})", txt) if r != propio})


# --- armado del archivo ---------------------------------------------------

def _escalar(v: str) -> str:
    """Escalar YAML entre comillas simples.

    Se dobla la comilla simple interna (regla YAML) y se deja intacta la
    doble: `BANDAS_ITCP["cohesion_bloque"]` tiene que sobrevivir carácter
    por carácter o el control de no-regresión lo lee como identificador
    perdido — y además sin comillas no es YAML válido.
    """
    return "'" + v.strip().replace("'", "''") + "'"


def _yaml_lista(nombre: str, valores: list[str], comillas: bool = False) -> str:
    if not valores:
        return ""
    cuerpo = ", ".join(_escalar(v) if comillas else v for v in valores)
    return f"{nombre}: [{cuerpo}]\n"


def _yaml_texto(nombre: str, valor: str) -> str:
    if not valor:
        return ""
    return f"{nombre}: {_escalar(valor)}\n"


def construir(texto: str, nombre: str) -> tuple[str, list[str]]:
    """Devuelve (contenido_migrado, motivos_de_revision)."""
    propio = nombre[:4]
    texto = texto.replace("\r\n", "\n")
    revisar: list[str] = []

    m_tit = re.search(r"^#\s+(.+?)\s*$", texto, re.M)
    titulo = m_tit.group(1).strip() if m_tit else f"ADR-{propio}"

    meta, cuerpo = leer_encabezado(texto)
    estado, nota = normalizar_estado(meta.get("estado", ""))
    ambito = partir_ambito(meta.get("ambito", ""))
    rel = cosechar_relaciones(texto, propio)
    relacionado = sorted(set(refs_del_encabezado(meta, propio)) - set(sum(rel.values(), [])))

    if not meta.get("ambito"):
        revisar.append("sin campo Ámbito")

    # 9 ADR no declaran Ámbito, pero el cinturón suele estar en el título o
    # en el nombre del archivo ("ITVC-B100: ... cinturón de Vida Cotidiana").
    if not ambito.get("cinturon"):
        pista = sin_acentos(titulo + " " + nombre)
        for aguja, nom in CINTURONES:
            if aguja in pista:
                ambito["cinturon"] = nom
                break

    # --- frontmatter
    # Los identificadores van entre comillas SIEMPRE: en YAML 1.1 un número
    # con cero a la izquierda es octal, así que `id: 0012` se lee 10 y
    # `relacionado: [0036]` se lee [30]. Colisionaban ADR distintos en la
    # misma clave y el índice perdía 38 filas sin avisar.
    fm = "---\n"
    fm += "madr: 4\n"
    fm += f"id: '{propio}'\n"
    fm += f"estado: {estado}\n"
    fm += _yaml_texto("nota_estado", nota)
    fm += f"fecha: {meta.get('fecha', '').strip()}\n" if meta.get("fecha") else ""
    if ambito.get("cinturon"):
        fm += f"cinturon: {ambito['cinturon']}\n"
    fm += _yaml_lista("indicadores", ambito.get("indicadores", []))
    fm += _yaml_lista("parametros", ambito.get("parametros", []), comillas=True)
    fm += _yaml_lista("archivos", ambito.get("archivos", []), comillas=True)
    for clave in ("supersede", "superado_por", "revierte", "corrige", "modifica",
                  "extiende", "complementa", "cierra", "continua"):
        fm += _yaml_lista(clave, rel.get(clave, []), comillas=True)
    fm += _yaml_lista("relacionado", relacionado, comillas=True)
    fm += _yaml_texto("ambito", meta.get("ambito", ""))
    fm += _yaml_texto("origen", meta.get("origen", ""))
    fm += _yaml_texto("commit", meta.get("commit", ""))
    fm += "---\n\n"

    # --- secciones
    partes = re.split(r"^##\s+(.+?)\s*$", cuerpo, flags=re.M)
    intro = partes[0]
    intro = re.sub(r"^#\s+.+?$", "", intro, count=1, flags=re.M).strip()
    pares = [(partes[i].strip(), partes[i + 1]) for i in range(1, len(partes) - 1, 2)]

    cubos: dict[str, list[tuple[str, str]]] = {}
    otras: list[tuple[str, str]] = []
    for tit, cont in pares:
        clave = clasificar(tit)
        if clave:
            cubos.setdefault(clave, []).append((tit, cont.rstrip()))
        else:
            otras.append((tit, cont.rstrip()))

    def unir(clave: str) -> str:
        """Junta las secciones de un cubo, conservando los títulos propios."""
        partes = []
        for tit, cont in cubos.get(clave, []):
            if es_titulo_generico(tit, clave):
                partes.append(cont.strip())
            else:
                partes.append(f"### {tit}\n\n{cont.strip()}")
        return "\n\n".join(p for p in partes if p)

    if otras:
        revisar.append(f"{len(otras)} sección(es) no canónicas: " +
                       ", ".join(t for t, _ in otras[:4]))
    if "opciones" not in cubos:
        revisar.append("sin opciones consideradas registradas")
    if "decision" not in cubos:
        revisar.append("sin sección Decisión")

    # Opciones: lista corta arriba, análisis detallado en «Pros y contras».
    opciones_lista, pros_contras = "", ""
    if "opciones" in cubos:
        # La lista corta sale de los subtítulos del contenido ORIGINAL: si se
        # extrajera del texto ya envuelto, el título de la propia sección
        # entraría como si fuera una opción más.
        bruto = "\n".join(c for _, c in cubos["opciones"])
        subtitulos = re.findall(r"^###\s+(.+?)\s*$", bruto, re.M)
        if subtitulos:
            opciones_lista = "\n".join(f"- {s.strip()}" for s in subtitulos)
            pros_contras = unir("opciones")
        else:
            opciones_lista = unir("opciones")

    salida = [fm.rstrip("\n"), "", f"# {titulo}", ""]

    def bloque(titulo_sec: str, contenido: str, nivel: int = 2) -> None:
        if not contenido or not contenido.strip():
            return
        salida.append("#" * nivel + f" {titulo_sec}")
        salida.append("")
        salida.append(contenido.strip())
        salida.append("")

    if intro:
        salida.append(intro)
        salida.append("")

    bloque("Contexto y planteo del problema", unir("contexto"))
    bloque("Factores de decisión", unir("factores"))

    if opciones_lista:
        bloque("Opciones consideradas", opciones_lista)
    else:
        bloque("Opciones consideradas",
               "_El ADR original no registró opciones alternativas._")

    decision = unir("decision")
    if decision:
        salida.append("## Decisión")
        salida.append("")
        salida.append(decision.strip())
        salida.append("")
    bloque("Consecuencias", unir("consecuencias"), nivel=3)
    bloque("Confirmación", unir("confirmacion"), nivel=3)

    bloque("Pros y contras de las opciones", pros_contras)

    # La anotación de «Precedentes directos» explica POR QUÉ pesa cada
    # precedente ("ADR-0022 (composición 45/40/15 de la dimensión)").
    # Reducirla a `relacionado: [0022]` tiraba esa razón; en MADR el lugar
    # de los enlaces a otras decisiones es «Más información».
    precedentes = meta.get("precedentes_directos", "").strip()
    limitaciones = unir("limitaciones")
    if limitaciones or otras or precedentes:
        salida.append("## Más información")
        salida.append("")
        if precedentes:
            salida.append("### Precedentes directos")
            salida.append("")
            salida.append(precedentes)
            salida.append("")
        if limitaciones:
            salida.append("### Limitaciones")
            salida.append("")
            salida.append(limitaciones.strip())
            salida.append("")
        for tit, cont in otras:
            salida.append(f"### {tit}")
            salida.append("")
            salida.append(cont.strip())
            salida.append("")

    texto_final = "\n".join(salida)
    texto_final = re.sub(r"\n{3,}", "\n\n", texto_final).rstrip() + "\n"
    return texto_final, revisar


def main() -> int:
    simular = "--simular" in sys.argv
    archivos = sorted(p for p in ADR_DIR.glob("[0-9]*.md"))
    pendientes: list[tuple[str, list[str]]] = []
    escritos = 0

    for p in archivos:
        original = p.read_text(encoding="utf-8")
        if original.lstrip().startswith("---\nmadr:"):
            continue  # ya migrado (el piloto)
        nuevo, revisar = construir(original, p.name)
        if revisar:
            pendientes.append((p.name, revisar))
        if not simular:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
        escritos += 1

    print(f"{'Simulación' if simular else 'Migrados'}: {escritos} ADR")
    print(f"Limpios (sin revisión manual): {escritos - len(pendientes)}")
    print(f"Requieren pasada de juicio:    {len(pendientes)}\n")

    motivos: dict[str, int] = {}
    for _, rs in pendientes:
        for r in rs:
            clave = r.split(":")[0]
            motivos[clave] = motivos.get(clave, 0) + 1
    for k, v in sorted(motivos.items(), key=lambda x: -x[1]):
        print(f"  {v:3d}  {k}")

    Path(ADR_DIR / "_pendientes.txt").write_text(
        "\n".join(f"{n}\t{'; '.join(r)}" for n, r in pendientes), encoding="utf-8"
    )
    print(f"\nDetalle en docs/adr/_pendientes.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
