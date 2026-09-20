"""El rótulo y la fuente nombran exactamente las cámaras que entran al cálculo
(ADR-0334).

Hoy pasó dos veces seguidas con este indicador: al sacar AEA del perímetro quedó
la card diciendo «10 comunicados en la ventana» sobre un saldo calculado con 9, y
el `fuente` publicado siguió diciendo «Comunicados de AEA y UIA». Los dos eran el
mismo error: la prosa sobrevivió al dato.

Esta guarda ata las dos puntas cortas —el rótulo de la card y el string `fuente`,
que además mira el gate G6— a `APOYO_CAMARAS_PERIMETRO`. NO prohíbe mencionar a
una cámara fuera del perímetro en la prosa larga: la ficha tiene que poder contar
que hasta marzo de 2026 el indicador promediaba dos, y eso es historia, no una
promesa sobre lo que mide hoy.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

import politica  # noqa: E402

# Cómo se nombra cada cámara en la capa pública.
NOMBRES = {
    "UIA": ("UIA", "Unión Industrial Argentina"),
    "AEA": ("AEA", "Asociación Empresaria Argentina"),
}

DATOS_TS = (RAIZ / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")


def _rotulo() -> str:
    m = re.search(r'^\s*apoyo_empresario:\s*"([^"]+)"', DATOS_TS, re.M)
    assert m, "no se encontró el rótulo de apoyo_empresario en datos.ts"
    return m.group(1)


def test_el_rotulo_no_nombra_una_camara_fuera_del_perimetro():
    rotulo = _rotulo()
    for cam, alias in NOMBRES.items():
        if cam in politica.APOYO_CAMARAS_PERIMETRO:
            continue
        for a in alias:
            assert a not in rotulo, (
                f"el rótulo «{rotulo}» nombra a {cam}, que no entra al cálculo "
                f"(APOYO_CAMARAS_PERIMETRO = {politica.APOYO_CAMARAS_PERIMETRO})")


def test_el_rotulo_no_promete_varias_camaras_si_mide_una():
    rotulo = _rotulo()
    if len(politica.APOYO_CAMARAS_PERIMETRO) == 1:
        assert not re.search(r"\bcámaras\b", rotulo, re.I), (
            f"el rótulo «{rotulo}» habla en plural midiendo una sola cámara: es el "
            f"patrón que ADR-0217 y ADR-0218 dejaron prohibido")


def test_la_fuente_publicada_nombra_el_perimetro_y_nada_mas():
    """`fuente` se publica en el snapshot y la mira el gate G6."""
    card = politica.fetch_apoyo_empresario()
    assert card, "fetch_apoyo_empresario devolvió None; sin card no se puede verificar"
    fuente = card["fuente"]
    for cam, alias in NOMBRES.items():
        dentro = cam in politica.APOYO_CAMARAS_PERIMETRO
        nombrada = any(a in fuente for a in alias)
        assert nombrada == dentro, (
            f"«{fuente}» {'no ' if dentro else ''}nombra a {cam} y "
            f"{'sí' if dentro else 'no'} entra al cálculo")


def test_el_conteo_de_la_ventana_sale_del_mismo_perimetro_que_el_saldo():
    """Lo que rompió antes: ventana 10 debajo de un saldo calculado sobre 9."""
    card = politica.fetch_apoyo_empresario()
    a, c = card["apoyos_ventana"], card["criticas_ventana"]
    assert a + c == card["comunicados_ventana"]
    assert round((a - c) / (a + c), 3) == card["valor"], (
        f"el saldo publicado ({card['valor']}) no sale de los comunicados que la "
        f"card declara ({a} apoyo, {c} crítica): uno de los dos usa otro perímetro")
