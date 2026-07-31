"""Reubica secciones que la migración automática no supo clasificar.

19 ADR quedaron sin `## Decisión`. Dos causas distintas:

  - El original anidaba `### Decisión` dentro de `## Problema N`. Al mapear
    "Problema" a contexto, la decisión se fue con él y quedó sepultada bajo
    Contexto (0033, 0128).
  - El ADR entero era narrativo —`La regla`, `El trinquete`, `Qué hace`— y
    ninguna sección casaba con el esqueleto, así que cayó todo en «Más
    información» (0105, 0119, 0149, 0150).

Dónde va cada sección es juicio sobre qué dice ese ADR, no un patrón: va
acá como tabla explícita, un renglón por sección, para que se pueda
auditar y discutir renglón por renglón en vez de quedar escondido en una
heurística.

El contenido no se toca: se mueve el bloque entero con su título. El
control de no-regresión de `adr_migracion.py` lo comprueba.

Uso:
    python scripts/adr_reubicar.py --simular
    python scripts/adr_reubicar.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"

CONTEXTO = "Contexto y planteo del problema"
FACTORES = "Factores de decisión"
OPCIONES = "Opciones consideradas"
DECISION = "Decisión"
PROS = "Pros y contras de las opciones"
MAS = "Más información"

ORDEN = [CONTEXTO, FACTORES, OPCIONES, DECISION, PROS, MAS]

# {id: {título de la sección H3: destino}}
UBICACION: dict[str, dict[str, str]] = {
    "0027": {
        "Consecuencias mientras esté abierto": "consecuencias",
    },
    "0033": {
        "Decisión": "decision",
        "Decisión: winsorización ASIMÉTRICA — techo 140, sin piso": "decision",
    },
    "0088": {
        "El indicador elegido": "decision",
        "Por qué la brecha y no el nivel": "factores",
        "Bandas": "decision",
        "Pesos": "decision",
        "Validación externa: percepción contra conducta": "consecuencias",
        "Consecuencias de diseño": "consecuencias",
        "Candidatos descartados": "pros",
    },
    "0105": {
        "Por qué hace falta": "contexto",
        "La regla": "decision",
        "El trinquete": "decision",
    },
    "0108": {
        "Cómo entra un índice sin bandas": "decision",
        "Lo que respondió": "consecuencias",
        "La lectura que importa es la de diferencias": "decision",
    },
    "0111": {
        "Alquiler: entra": "decision",
        "Que aporta señal propia está medido, no supuesto": "factores",
        "Peso": "decision",
        "Limitación": "limitaciones",
        "Pobreza: no entra, y el hueco es menor de lo que parece": "decision",
        "Expectativas: no entra": "decision",
    },
    "0115": {
        "La estructura nueva": "decision",
        "El criterio: peso efectivo idéntico": "decision",
        "El ITVC publicado se mueve 0,1 y no debería asustar": "consecuencias",
        "Limitación conocida: una dimensión de una sola pata": "limitaciones",
    },
    "0118": {
        "La nota": "decision",
        "El recorte de motos: se mantiene, y ahora está medido": "decision",
        "De paso, tres números viejos": "consecuencias",
    },
    "0119": {
        "1. Consumo de carne: la limitación es real y ahora tiene número": "decision",
        "2. Notación de las fórmulas invertidas": "decision",
        "3. Identificadores legado: no se renombran, y está bien": "decision",
        "Estado de la auditoría": "consecuencias",
    },
    "0120": {
        "Lo que se descubrió al escribir el origen": "contexto",
        "La reclasificación": "decision",
        "El trinquete hizo su trabajo": "consecuencias",
    },
    "0121": {
        "La disciplina, distinta a la del ITCM": "decision",
        "Se movieron a conceptual (7)": "decision",
        "Se quedaron como convención (honesto)": "decision",
        "Resultado: los tres convergen, y el piso tiene sentido": "consecuencias",
        "El trinquete, otra vez": "consecuencias",
    },
    "0123": {
        "Cómo se clasifica un índice sin bandas": "decision",
        "La winsorización no es una excepción a esto": "decision",
        'Lo que "0% circular" NO quiere decir': "limitaciones",
    },
    "0128": {
        "1. El denominador de la dotación APN incluye a las fuerzas": "contexto",
        "Cuánto cambia la lectura": "factores",
        "Decisión": "decision",
        "2. El FAL pasa a pesar la mitad de su dimensión": "decision",
        "El efecto, dicho como es": "consecuencias",
        "Lo que NO se tomó de la propuesta": "pros",
    },
    "0133": {
        "Lo que pasó": "contexto",
        "Tres cambios": "decision",
        "1. Las dependencias que faltaban": "decision",
        "2. El gate distingue integridad de demora": "decision",
        "3. Un crash de script deja de disfrazarse de dato": "decision",
        "Lo que esto NO arregla": "limitaciones",
    },
    "0143": {
        "Se descartó el ratio contra el stock regulatorio, por incommensurabilidad": "pros",
        "La serie: existe desde dic-2023 y está validada": "factores",
        "Bandas": "decision",
        "Lo implementado": "decision",
    },
    "0146": {
        "Resolución: sí cuenta": "decision",
        "La misma regla resuelve el otro caso, en sentido contrario": "decision",
        "Dos hallazgos de la revisión que hay que registrar": "consecuencias",
        "Lo que esto NO resuelve": "limitaciones",
    },
    "0149": {
        "Por qué, y por qué ahora": "contexto",
        "Qué hace": "decision",
        "Lo que NO hace": "limitaciones",
        "Un detalle que hubiera roto el detector en silencio": "decision",
        "Primera corrida": "consecuencias",
    },
    "0150": {
        "Lo que se buscaba y lo que apareció": "contexto",
        "El bug": "contexto",
        "El diseño de concordancia también estaba mal": "contexto",
        "Reglas v2": "decision",
        "El indicador": "decision",
        "Lo que queda pendiente": "limitaciones",
    },
    "0151": {
        "La segunda pasada, completa": "decision",
        "12 casos cambian con el texto completo": "consecuencias",
        "Los 11 desacuerdos se adjudicaron con tres criterios, no caso por caso": "decision",
        "Efecto sobre el indicador": "consecuencias",
        "Lo que NO cambió, y por qué importa": "consecuencias",
        "Lo que se corrigió en código": "decision",
    },
}

DESTINO_A_H2 = {
    "contexto": CONTEXTO, "factores": FACTORES, "opciones": OPCIONES,
    "decision": DECISION, "consecuencias": DECISION, "pros": PROS,
    "limitaciones": MAS,
}


def partir(texto: str) -> tuple[str, str, list[tuple[str, str, list[tuple[str, str]]]]]:
    """(frontmatter+título, intro, [(h2, preámbulo, [(h3, cuerpo)])])

    La `intro` es el texto entre el título y la primera sección. Varios ADR
    ponen ahí las relaciones en prosa ("**Relacionados**: ADR-0131 ...");
    descartarla borraba esas referencias.
    """
    m = re.match(r"\A(---\n.*?\n---\n\n?#[^\n]*\n)(.*)\Z", texto, re.S)
    cabeza, resto = (m.group(1), m.group(2)) if m else ("", texto)

    bloques = re.split(r"^##\s+(?!#)(.+?)\s*$", resto, flags=re.M)
    intro = bloques[0].strip()
    secciones = []
    for i in range(1, len(bloques) - 1, 2):
        h2, cuerpo = bloques[i].strip(), bloques[i + 1]
        trozos = re.split(r"^###\s+(.+?)\s*$", cuerpo, flags=re.M)
        preambulo = trozos[0].strip()
        h3s = [(trozos[j].strip(), trozos[j + 1].strip())
               for j in range(1, len(trozos) - 1, 2)]
        secciones.append((h2, preambulo, h3s))
    return cabeza, intro, secciones


def reubicar(texto: str, tabla: dict[str, str]) -> tuple[str, int, list[str]]:
    cabeza, intro, secciones = partir(texto)
    movidos, no_encontrados = 0, list(tabla)

    # cubo -> (preámbulo, [(h3, cuerpo)])
    cubos: dict[str, list] = {h2: ["", []] for h2 in ORDEN}
    for h2, pre, h3s in secciones:
        destino = h2 if h2 in cubos else MAS
        if pre:
            cubos[destino][0] = (cubos[destino][0] + "\n\n" + pre).strip()
        for h3, cuerpo in h3s:
            objetivo = tabla.get(h3)
            if objetivo:
                cubos[DESTINO_A_H2[objetivo]][1].append((h3, cuerpo))
                movidos += 1
                if h3 in no_encontrados:
                    no_encontrados.remove(h3)
            else:
                cubos[destino][1].append((h3, cuerpo))

    partes = [cabeza.rstrip(), ""]
    if intro:
        partes += [intro, ""]
    for h2 in ORDEN:
        pre, h3s = cubos[h2]
        if not pre and not h3s:
            continue
        partes += [f"## {h2}", ""]
        if pre:
            partes += [pre, ""]
        for h3, cuerpo in h3s:
            partes += [f"### {h3}", "", cuerpo, ""]

    salida = re.sub(r"\n{3,}", "\n\n", "\n".join(partes)).rstrip() + "\n"
    return salida, movidos, no_encontrados


def main() -> int:
    simular = "--simular" in sys.argv
    total, problemas = 0, []
    for propio, tabla in UBICACION.items():
        candidatos = list(ADR_DIR.glob(f"{propio}*.md"))
        if not candidatos:
            problemas.append(f"{propio}: no existe el archivo")
            continue
        p = candidatos[0]
        nuevo, movidos, faltan = reubicar(p.read_text(encoding="utf-8"), tabla)
        if faltan:
            problemas.append(f"{propio}: títulos no encontrados -> {faltan}")
        if not simular:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
        total += movidos
        print(f"  {propio}: {movidos} sección(es) reubicadas")

    print(f"\n{'Simulación' if simular else 'Aplicado'}: {total} secciones en {len(UBICACION)} ADR")
    for x in problemas:
        print(f"  PROBLEMA  {x}")
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
