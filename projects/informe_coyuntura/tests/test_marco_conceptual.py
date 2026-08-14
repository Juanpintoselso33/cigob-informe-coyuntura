"""El encuadre conceptual del informe tiene que seguir publicado en /metodologia.

El 2026-08-12, el rediseño de la aguja (ADR-0194) sacó del hero de la portada el
párrafo que define qué mide el informe -- «procesar la tensión entre las demandas
del entorno y los recursos de acción disponibles» -- justificándolo en que «el
encuadre conceptual vive en /metodologia». No vivía: nunca había estado ahí y no
se movió. Durante un día el sitio publicó una tensión 0-10, una aguja, un
semáforo y una regla de «dos o más tensionados» sin decir en ninguna página qué
es esa tensión. Lo encontró una pregunta del editor, no un gate.

Ningún gate podía encontrarlo: gate_calidad.py mira estructura, frescura y
card-contra-serie, y los tests de reconciliación comparan el snapshot consigo
mismo. Nada mira la prosa publicada. Este test cierra esa clase de hueco para el
texto que no es redundante con ninguna aguja -- una aguja no puede decir qué es
lo que mide. Ver ADR-0199.

No juzga la redacción: sólo que el marco siga estando y que las nociones que el
resto del sitio usa sin definir queden nombradas donde se explican.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METODOLOGIA_INDEX = ROOT / "web" / "src" / "pages" / "metodologia" / "index.astro"


def _texto_normalizado(path: Path) -> str:
    """El JSX parte los párrafos en varias líneas con sangría arbitraria, así que
    cualquier match sobre el archivo crudo depende de dónde cortó el formateo.
    Se colapsa todo el whitespace a un espacio antes de buscar."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


# El párrafo original de la Fundación, tal como estaba en Hero.astro antes de
# 1f6aa0e. Se busca por fragmentos porque el marcado intercala <strong>.
FRAGMENTOS_DEL_PARRAFO_ORIGINAL = [
    "La gobernabilidad de un proyecto de gobierno no se mide por la ausencia de conflictos",
    "procesar la tensión",
    "entre las demandas del entorno y los recursos de acción disponibles",
    "sistematiza el mapa de tensiones de la Argentina actual",
    "cinco cinturones analíticos",
    "operan un constante intercambio de problemas",
    "la viabilidad fiscal, cambiaria, social y política se recalculan en tiempo real",
]

# Nociones que el sitio usa en otras páginas sin definirlas ahí: la tensión y su
# escala aparecen en cada aguja, "cinturón" en toda la navegación, y "barbarismo"
# en el BLUF de la portada, en cada card y en cada página de cinturón. El marco
# es el único lugar donde se explican.
NOCIONES_QUE_EL_MARCO_DEFINE = ["tensión", "cinturón", "0 a 10", "barbarismo"]


def test_el_parrafo_original_sigue_publicado():
    texto = _texto_normalizado(METODOLOGIA_INDEX)
    faltantes = [f for f in FRAGMENTOS_DEL_PARRAFO_ORIGINAL if f not in texto]
    assert not faltantes, (
        "El encuadre conceptual del informe se borró o se reescribió en "
        f"{METODOLOGIA_INDEX.relative_to(ROOT)}. Fragmentos que ya no están: "
        f"{faltantes}. Es texto institucional de la Fundación y se publica "
        "palabra por palabra (ADR-0199); si hay que cambiarlo, va con un ADR "
        "que supersede al 0199, no con una poda de prosa."
    )


def test_la_seccion_del_marco_tiene_ancla():
    texto = _texto_normalizado(METODOLOGIA_INDEX)
    assert 'id="marco"' in texto, (
        "La sección del marco perdió su ancla id=\"marco\". Es la sección que "
        "abre /metodologia y el destino natural de cualquier enlace que explique "
        "qué es la tensión (ADR-0199)."
    )


def test_el_marco_nombra_las_nociones_que_el_resto_del_sitio_usa():
    texto = _texto_normalizado(METODOLOGIA_INDEX)
    # Recorta a la sección del marco: que las palabras aparezcan en otra parte de
    # la página (por ejemplo "tensionado" en la regla de lectura) no alcanza.
    inicio = texto.find('id="marco"')
    assert inicio != -1, "No se encontró la sección del marco"
    fin = texto.find("<section", inicio + 1)
    seccion = texto[inicio:fin if fin != -1 else len(texto)]

    faltantes = [n for n in NOCIONES_QUE_EL_MARCO_DEFINE if n not in seccion]
    assert not faltantes, (
        f"El marco de /metodologia dejó de nombrar: {faltantes}. El resto del "
        "sitio usa esas nociones sin definirlas (la aguja publica una tensión "
        "0-10, cada card declara su barbarismo de riesgo); si el marco no las "
        "explica, no las explica nadie. Ver ADR-0199."
    )
