"""Los `*_OCULTOS` del snapshot salen de las listas que declara cada índice.

`publicar.py` decide qué indicadores NO se publican como card. Tres de los
cuatro cinturones lo derivaban de las listas de su módulo de índice
(`INDICADORES_CONTEXTO`, `INDICADORES_SUSPENDIDOS`, `INDICADORES_CUMPLIDOS`) y
**macro repetía la lista como literal**.

Esa copia rompe la regla que el proyecto ya tuvo que aplicar dos veces
—ADR-0153 y ADR-0216, «o integra el índice, o no es card»— y la rompe **en
silencio**: sacar un indicador del score y anotarlo en la lista del módulo no
lo sacaba del snapshot, así que quedaba publicado como card sin puntaje,
cayendo en el `else` de `_scoring_indice` que le pone la nota de contexto.

Apareció el 25 de agosto de 2026 al sacar `idm` e `icip` del ITCM: los dos
habrían quedado visibles y mudos en la web, con el mismo aspecto que un
indicador vigente.

La guarda es genérica a propósito. Una que nombrara `idm` e `icip` habría que
acordarse de extenderla en la próxima baja, que es exactamente lo que no pasa.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import publicar     # noqa: E402
import parametrica  # noqa: E402
import itcm       # noqa: E402
import itcp       # noqa: E402
import itcg       # noqa: E402
import itvc       # noqa: E402

# (nombre del conjunto en publicar.py, módulo del índice)
CINTURONES = [
    ("MACRO_OCULTOS", itcm),
    ("POLITICA_OCULTOS", itcp),
    ("GESTION_OCULTOS", itcg),
    ("VIDA_OCULTOS", itvc),
]

# Las tres listas que un módulo de índice puede declarar como «esto no puntúa».
#
# Ojo con `INDICADORES_CUMPLIDOS`: hoy está VACÍA en los cuatro cinturones, así
# que esa rama no está probada contra datos reales — sacarla de la derivación
# de `GESTION_OCULTOS` no hace fallar nada, y se comprobó rompiéndola. Está
# igual porque el día que vuelva a poblarse la guarda tiene que cubrirla sola,
# que es el punto de que sea genérica.
DECLARADAS = ("INDICADORES_CONTEXTO", "INDICADORES_SUSPENDIDOS",
              "INDICADORES_CUMPLIDOS")


def _declarados(mod) -> set:
    fuera = set()
    for nombre in DECLARADAS:
        fuera |= set(getattr(mod, nombre, ()) or ())
    return fuera


@pytest.mark.parametrize("conjunto,mod", CINTURONES,
                         ids=[c for c, _ in CINTURONES])
def test_todo_lo_que_el_indice_declara_fuera_esta_oculto(conjunto, mod):
    """La dirección que importa: si el módulo dice que no puntúa, no se publica.

    Al revés no se exige. `VIDA_OCULTOS` y `MACRO_OCULTOS` esconden además
    insumos que nunca puntuaron y que no tienen por qué estar en una lista de
    bajas (`indice_lider`, `endeudamiento_familiar`)."""
    ocultos = getattr(publicar, conjunto)
    faltan = sorted(_declarados(mod) - set(ocultos))
    assert not faltan, (
        f"{conjunto}: el índice declara que {faltan} no puntúa(n) y "
        f"`publicar.py` los seguiría publicando como card sin puntaje. "
        f"Derivá el conjunto de las listas del módulo en vez de repetirlas.")


@pytest.mark.parametrize("conjunto,mod", CINTURONES,
                         ids=[c for c, _ in CINTURONES])
def test_ningun_oculto_puntua(conjunto, mod):
    """La otra mitad de la regla: lo que no se muestra tampoco puede pesar.

    Se mide contra los pesos VIGENTES, no contra la tabla `DIMENSIONES_*`.
    Estar en la tabla no es puntuar: ADR-0245 conserva a propósito el peso y la
    banda de un suspendido —para que la reincorporación no tenga que
    reinventarlos— y lo filtra al calcular con `parametrica.sin_suspendidos`.
    Una guarda que mirara la tabla cruda marcaría a los cuatro suspendidos de
    hoy como intrusos, que es lo contrario de lo que pasa."""
    ocultos = getattr(publicar, conjunto)
    dimensiones = next(getattr(mod, n) for n in dir(mod)
                       if n.startswith("DIMENSIONES_"))
    vigentes = parametrica.indicadores_vigentes(dimensiones, _declarados(mod))
    puntuan = {i for d in vigentes.values() for i in d}
    intrusos = sorted(set(ocultos) & puntuan)
    assert not intrusos, (
        f"{conjunto}: {intrusos} no se publica(n) pero pesa(n) en el índice — "
        f"un componente invisible que mueve el score")


def test_la_guarda_mira_algo():
    """Que las listas no estén todas vacías, que haría pasar todo por omisión."""
    assert sum(len(_declarados(m)) for _, m in CINTURONES) >= 10
