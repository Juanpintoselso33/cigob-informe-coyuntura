"""Peso del trabajo independiente en el empleo registrado (SIPA).

Es la contracara del cierre de PyMEs. Cuando cae el número de empleadores, la
pregunta que sigue es si esas unidades productivas desaparecieron o se
reconfiguraron: menos empresas con nómina y más gente facturando por su cuenta.
Sin este indicador, el informe sólo puede ver la mitad del movimiento.

Mide qué proporción del empleo registrado son trabajadores independientes
—autónomos y monotributistas del régimen general— frente a los asalariados de
cualquier sector.

**El universo es restringido y el rótulo lo dice** (ADR-0250). Hasta agosto de
2026 la card decía «% del empleo registrado» a secas mientras dejaba afuera al
monotributo social de los DOS lados del cociente. La exclusión está bien
fundada —ver abajo— pero prometer «el empleo registrado» y publicar otro
universo es lo que la auditoría del 25-ago-2026 marcó. Ahora la card enumera
qué categorías entran, cuál queda afuera y cuánto daría con ella adentro.

## Por qué el monotributo social queda AFUERA

Su serie cae 394 mil personas **en un solo mes**, diciembre de 2024. No es un
fenómeno del mercado de trabajo: es una decisión regulatoria sobre el propio
régimen. Incluirlo haría que el indicador midiera una reforma administrativa y
la publicara como si fuera reconfiguración productiva — y con signo invertido,
además, la habría leído como una mejora.

Con el régimen social adentro, la participación independiente CAE de 22,9% a
22,1% entre el 4T-2023 y hoy. Sin él, SUBE de 19,1% a 20,6%. Las dos lecturas
son opuestas y sólo una describe la economía.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

SERIES_BASE = "https://apis.datos.gob.ar/series/api/series/"
HTTP_TIMEOUT = 90
REINTENTOS = 3

# Todas sin estacionalidad, mensuales, en miles de personas (SIPA).
INDEPENDIENTES = {
    "autonomos":   "151.1_IPENDIETAC_2012_M_34",
    "monotributo": "151.1_IPENDIETAC_2012_M_36",
}
ASALARIADOS = {
    "privado":  "151.1_AARIADOTAC_2012_M_26",
    "publico":  "151.1_AARIADOTAC_2012_M_25",
    "casas":    "151.1_AARIADOTAC_2012_M_40",
}
# El régimen que se excluye, y el mes del quiebre que lo justifica. Se deja
# nombrado para que la exclusión sea una decisión visible y no un olvido.
EXCLUIDA = ("monotributo_social", "151.1_IPENDIETAC_2012_M_43", "2024-12")

# Rótulos publicables de cada componente del cociente. Un porcentaje sobre un
# universo restringido tiene que poder enumerarse: es la diferencia entre una
# exclusión declarada y un recorte silencioso.
CATEGORIAS_NUMERADOR = ("autónomos", "monotributo general")
CATEGORIAS_DENOMINADOR = ("autónomos", "monotributo general",
                          "asalariados privados", "asalariados públicos",
                          "casas particulares")


def _serie(series_id: str) -> dict:
    for intento in range(REINTENTOS):
        try:
            r = requests.get(SERIES_BASE,
                             params={"ids": series_id, "format": "json",
                                     "limit": 200, "sort": "desc"},
                             timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            return {fila[0][:7]: fila[1] for fila in r.json()["data"]
                    if fila[1] is not None}
        except Exception as e:                        # noqa: BLE001
            if intento == REINTENTOS - 1:
                raise
            logger.warning("serie %s: %s (reintento %d)", series_id, e, intento + 1)
            time.sleep(3)
    return {}


def fetch_trabajo_independiente() -> dict:
    partes = {k: _serie(v) for k, v in {**INDEPENDIENTES, **ASALARIADOS}.items()}
    # El régimen excluido se baja igual: se publica como contraste dentro de la
    # explicación de la card, para que el lector vea qué cambia al incluirlo en
    # vez de tener que creernos.
    try:
        social = _serie(EXCLUIDA[1])
    except Exception as e:                                # noqa: BLE001
        logger.warning("monotributo social (contraste): %s", e)
        social = {}
    vacias = [k for k, v in partes.items() if not v]
    if vacias:
        raise ValueError(f"SIPA no devolvió datos para {vacias}")

    meses = sorted(set.intersection(*[set(v) for v in partes.values()]))
    if len(meses) < 24:
        raise ValueError(f"sólo {len(meses)} meses en común entre las series de SIPA")

    indep = {m: sum(partes[k][m] for k in INDEPENDIENTES) for m in meses}
    asal = {m: sum(partes[k][m] for k in ASALARIADOS) for m in meses}
    # Participación sobre el empleo registrado TOTAL, no sólo el privado: un
    # asalariado que pasa a monotributo puede venir de cualquiera de los tres.
    part = {m: round(indep[m] / (indep[m] + asal[m]) * 100, 2) for m in meses}

    ultimo = meses[-1]
    con_social = None
    if ultimo in social:
        i2 = indep[ultimo] + social[ultimo]
        con_social = round(i2 / (i2 + asal[ultimo]) * 100, 2)

    return {
        "mes": ultimo,
        "participacion": part[ultimo],
        "independientes": round(indep[ultimo]),
        "asalariados": round(asal[ultimo]),
        "categorias_numerador": list(CATEGORIAS_NUMERADOR),
        "categorias_denominador": list(CATEGORIAS_DENOMINADOR),
        "excluido": EXCLUIDA[0],
        "excluido_quiebre": EXCLUIDA[2],
        "participacion_con_excluido": con_social,
        "serie": part,
    }
