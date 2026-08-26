"""Una fuente caída degrada el indicador; nunca lo hace desaparecer.

`_carry_forward` repara los indicadores que llegan con `valor: None`
restaurando el último valor bueno y marcándolos `desactualizado`. Pero **sólo
ve las claves que existen**: si el colector falla y `publicar.py` directamente
no agrega la clave, no hay nada que reparar y el indicador se cae del snapshot
sin que nada avise.

Ya pasó tres veces, y las tres se arreglaron de a una:

| fecha | indicador | cómo se descubrió |
|---|---|---|
| 2026-07-09 | `sentimiento_digital` | Google Trends con rate limit; lo agarró `test_publicar.py` después de haberlo pusheado |
| 2026-08 | `motorizacion_total` | preventivo, al fundir autos y motos (ADR-0224) |
| 2026-08-25 | `consumo_carnes_total` | SAGYP devolvió `None`; el snapshot salió con 62 cards en vez de 63 |

`gate_calidad.py` no lo agarra en ninguno de los tres casos y no es un olvido:
mira estructura, frescura y card-contra-serie, no invariantes de conteo. Un
snapshot al que le falta un indicador está perfectamente bien formado.

Esta guarda es **genérica a propósito**. Las tres reparaciones anteriores
fueron por indicador, y por eso hubo tres: lo que hay que verificar no es que
la carne esté, sino que **construir el cinturón con TODAS las fuentes caídas
siga produciendo todos los indicadores que puntúan**. Así el próximo colector
que se agregue queda cubierto sin que nadie se acuerde.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import publicar   # noqa: E402
import itvc       # noqa: E402
import parametrica  # noqa: E402


def _puntuan(mod) -> set:
    """Indicadores que HOY integran el índice del cinturón."""
    dimensiones = next(getattr(mod, n) for n in dir(mod)
                       if n.startswith("DIMENSIONES_"))
    suspendidos = set(getattr(mod, "INDICADORES_SUSPENDIDOS", ()) or ())
    vigentes = parametrica.indicadores_vigentes(dimensiones, suspendidos)
    return {i for d in vigentes.values() for i in d}


# Componentes que no salen del `raw` del colector sino de las series ya
# descargadas, así que no pueden estar en el resultado de `build_vida({})`.
# Es una lista corta y explícita: si crece, alguien tiene que justificarla.
DESDE_SERIES = {
    # Sin colector propio: la card se sintetiza desde la serie ya descargada,
    # así que `build_vida({})` no puede producirla y su ausencia acá no es el
    # bug que esta guarda persigue (ADR-0067 y el patrón de la card del IVI).
    "carga_servicio_deuda_hogares",
    "mora_familias",
}


def test_vida_construye_todos_sus_indicadores_con_las_fuentes_caidas():
    """El caso real: `build_vida({})` es una corrida donde falló TODO.

    Cada indicador que puntúa tiene que aparecer igual, con `valor: None`, para
    que `_carry_forward` tenga qué reparar. La alternativa —que la clave no
    esté— es la que borra el indicador de la web en silencio.
    """
    out = publicar.build_vida({})
    faltan = sorted(_puntuan(itvc) - set(out) - DESDE_SERIES)
    assert not faltan, (
        f"con todas las fuentes caídas, estos indicadores no llegan a existir en "
        f"el snapshot: {faltan}. `_carry_forward` sólo repara claves presentes "
        f"con valor None, así que desaparecerían de la web en vez de quedar "
        f"marcados como desactualizados. Agregalos SIEMPRE, fuera del `if` que "
        f"comprueba si la fuente contestó.")


def test_los_que_aparecen_llegan_con_valor_none_y_no_con_un_relleno():
    """No alcanza con que la clave exista: tiene que venir vacía.

    Un cero o un valor por defecto sería peor que la ausencia — `_carry_forward`
    lo daría por bueno y publicaría un número inventado como si fuera dato."""
    out = publicar.build_vida({})
    con_valor = {k: v.get("valor") for k, v in out.items()
                 if isinstance(v, dict) and v.get("valor") is not None}
    # `informalidad` y `alquiler_real` redondean sobre un `.get(..., 0)` previo
    # a esta guarda: quedan declarados en vez de tapados.
    conocidos = {"informalidad", "alquiler_real"}
    intrusos = sorted(set(con_valor) - conocidos)
    assert not intrusos, (
        f"con todas las fuentes caídas, estos llegan con un valor de relleno en "
        f"vez de None: { {k: con_valor[k] for k in intrusos} }. "
        f"`_carry_forward` lo tomaría por dato bueno.")


def test_la_guarda_mira_algo():
    """Que `_puntuan` no devuelva vacío, que haría pasar todo por omisión."""
    assert len(_puntuan(itvc)) >= 15
