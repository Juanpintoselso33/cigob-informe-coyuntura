# -*- coding: utf-8 -*-
"""Resumen de una oración para la card, con el desarrollo aparte (ADR-0165).

EL PROBLEMA. Cada sección del tablero publicaba su análisis completo en la card:
la de redundancia del ITCG llegaba a 1.087 caracteres, la matriz cruzada a 877.
Siete cards así son unos cinco mil caracteres de prosa en una página que se mira
para leer números. Y en las tres secciones que tienen modal, ese mismo texto ya
estaba repetido adentro.

QUÉ HACE. Corta el texto en la primera oración —o las dos primeras si la primera
es muy corta— sin pasar de un tope de caracteres, siempre en un límite de
oración. Nunca corta a mitad de frase ni agrega puntos suspensivos: el resumen
es texto completo y gramatical, no un truncamiento.

POR QUÉ LA PRIMERA ORACIÓN ALCANZA. Las conclusiones de este informe se escriben
con el resultado adelante y la explicación atrás — es la misma regla que obligó
a poner el factor común al principio y no al final. Si una sección no cumple eso,
su resumen va a quedar flojo, y eso es una señal sobre cómo está escrita esa
conclusión, no sobre este módulo.

NO SE PIERDE NADA: el resto queda en el modal (secciones que lo tienen) o en un
desplegable de la card.
"""

import re

TOPE = 260
MINIMO_PRIMERA = 120

# Fin de oración: punto seguido de espacio y de algo que empiece oración. Se
# excluye el punto entre dígitos (fechas, montos) y las abreviaturas frecuentes
# en estos textos, que si no cortan la oración por la mitad.
_ABREVIATURAS = ("Sec.", "Ing.", "Lic.", "Dr.", "art.", "arts.", "cap.", "aprox.",
                 "p. ej.", "etc.", "vs.", "núm.", "pág.")
_FIN = re.compile(r"(?<=[^\d])\.\s+(?=[A-ZÁÉÍÓÚÑ¿«“(])")


def _oraciones(texto: str) -> list:
    partes, resto = [], texto.strip()
    while resto:
        m = _FIN.search(resto)
        if not m:
            partes.append(resto)
            break
        corte = m.start() + 1
        candidata = resto[:corte]
        if any(candidata.rstrip().endswith(a) for a in _ABREVIATURAS):
            # falso positivo: la abreviatura no termina la oración
            siguiente = _FIN.search(resto, m.end())
            if not siguiente:
                partes.append(resto)
                break
            corte = siguiente.start() + 1
            candidata = resto[:corte]
        partes.append(candidata.strip())
        resto = resto[corte:].strip()
    return [p for p in partes if p]


def resumen(texto: str, tope: int = TOPE) -> str:
    """Primera(s) oración(es) completas, sin pasar del tope."""
    if not texto:
        return ""
    texto = texto.strip()
    if len(texto) <= tope:
        return texto
    partes = _oraciones(texto)
    if not partes:
        return texto
    salida = partes[0]
    # una primera oración muy corta no dice nada por sí sola; se suma la
    # siguiente mientras entre en el tope
    for siguiente in partes[1:]:
        if len(salida) >= MINIMO_PRIMERA or len(salida) + 1 + len(siguiente) > tope:
            break
        salida = salida + " " + siguiente
    return salida


def cola(texto: str, tope: int = TOPE) -> str:
    """Lo que el resumen deja afuera. Vacío si el resumen es el texto entero."""
    r = resumen(texto, tope)
    return texto.strip()[len(r):].strip() if r != texto.strip() else ""


# Campos de texto largo de cada sección y el prefijo de sus derivados. `sub` es
# la bajada que va ARRIBA de la card —lo primero que se lee— y llegaba a 796
# caracteres: el lector se come un párrafo entero antes de ver un número.
CAMPOS = (("conclusion", "resumen", "detalle_texto"),
          ("sub", "sub_resumen", "sub_detalle"))


def anotar(nodo, tope: int = TOPE) -> None:
    """Recorre el informe y le agrega su resumen a todo bloque con texto largo.

    Genérico a propósito: una sección nueva queda cubierta sin tener que
    acordarse de nada. Nunca modifica el texto original — el desarrollo se muda,
    no se pierde.
    """
    if isinstance(nodo, dict):
        for campo, clave_res, clave_det in CAMPOS:
            texto = nodo.get(campo)
            if isinstance(texto, str) and texto.strip():
                r = resumen(texto, tope)
                if r != texto.strip():
                    nodo[clave_res] = r
                    nodo[clave_det] = cola(texto, tope)
        for v in nodo.values():
            anotar(v, tope)
    elif isinstance(nodo, list):
        for v in nodo:
            anotar(v, tope)
