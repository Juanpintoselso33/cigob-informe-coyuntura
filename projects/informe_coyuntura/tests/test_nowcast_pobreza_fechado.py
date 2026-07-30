# -*- coding: utf-8 -*-
"""El nowcast de pobreza se fecha por el semestre MÁS NUEVO que declara (ADR-0153).

Cada informe nombra su semestre dos veces —el título de RESULTADOS y el
enunciado que trae la tasa— y las dos las escribe el autor a mano. Cualquiera de
las dos puede quedar del mes anterior, y se comprobó en los dos sentidos sobre
los 18 informes publicados, así que preferir una fuente sobre la otra pierde un
mes en algún caso. La regla que resuelve los dos: lo que queda viejo es siempre
el mes anterior, nunca el siguiente, así que gana el semestre más nuevo.

Fecharlo mal no fallaba: el dedupe por período hace que el informe más nuevo
gane, así que pisar un mes con el valor del siguiente se veía como una "revisión"
legítima del autor, y el hueco que dejaba parecía un mes sin publicación.

Los textos son recortes literales de los PDF publicados; no hay red acá.
"""
import importlib.util
import sys
import types
from pathlib import Path

_RUTA = (Path(__file__).resolve().parents[1] / "scripts" / "vida_cotidiana"
         / "collectors" / "utdt_nowcast_pobreza.py")


def _cargar_colector():
    """Carga el colector por ruta, sin pasar por `collectors/__init__`.

    Dos motivos: el `__init__` importa todos los colectores del paquete, y el
    `config.py` de la raíz del proyecto tapa al de `vida_cotidiana` cuando pytest
    corre desde el root. Las dos funciones que se prueban acá son puras —texto y
    diccionarios—, así que alcanza con un stub de config para el import.
    """
    previo = sys.modules.get("config")
    stub = types.ModuleType("config")
    stub.HTTP_HEADERS, stub.HTTP_TIMEOUT = {}, 30
    sys.modules["config"] = stub
    try:
        spec = importlib.util.spec_from_file_location("_utdt_nowcast_bajo_test", _RUTA)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if previo is None:
            sys.modules.pop("config", None)
        else:
            sys.modules["config"] = previo


_COLECTOR = _cargar_colector()
_resultado, _huecos = _COLECTOR._resultado, _COLECTOR._huecos

# El caso que motivó el cambio: informe publicado el 16-jun-2026. El título dice
# noviembre-abril y el enunciado dice diciembre-mayo. El gráfico de evolución del
# propio informe rotula ese 29,6 como Dic25May26.
TITULO_VIEJO = (
    "RESULTADOS Semestre Noviembre 2025 - Abril 2026 El nowcast estima una tasa "
    "de pobreza de 29.6 por ciento para el semestre diciembre 2025 - mayo 2026 "
    "con un intervalo del 95 por ciento de confianza entre [28.2%, 31.0%]."
)
# El mes anterior, donde título y enunciado coinciden.
COINCIDEN = (
    "RESULTADOS Semestre Noviembre 2025 - Abril 2026 El nowcast estima una tasa "
    "de pobreza de 29.2 por ciento para el semestre noviembre 2025 - abril 2026 "
    "con un intervalo del 95 por ciento de confianza entre [27.7%, 30.6%]."
)
# El caso SIMÉTRICO: informe publicado el 13-nov-2025, donde el que quedó viejo
# es el ENUNCIADO. El informe del mes anterior ya había estimado abril-septiembre,
# así que éste estima mayo-octubre y el título es el que acierta. Es el que impide
# resolver el bug simplemente prefiriendo el enunciado.
ENUNCIADO_VIEJO = (
    "RESULTADOS Semestre Mayo 2025 - Octubre 2025 El nowcast estima una tasa de "
    "pobreza de 30.7 por ciento para el semestre abril 2025 - septiembre 2025 con "
    "un intervalo del 95 por ciento de confianza entre [29.3%, 32.2%]."
)
# La variante que cierra un semestre calendario y no nombra los meses.
CALENDARIO = (
    "RESULTADOS Semestre Enero 2026 - Junio 2026 El nowcast estima una tasa de "
    "pobreza de 31.6 por ciento para el primer semestre calendario de 2026 con "
    "un intervalo del 95 por ciento de confianza entre [30.1%, 33.0%]."
)
# La misma variante escrita «del 2025», que es como sale en el informe de
# diciembre de 2025.
CALENDARIO_DEL = (
    "RESULTADOS Semestre Julio 2025 - Diciembre 2025 El nowcast estima una tasa de "
    "pobreza de 30.6 por ciento para el segundo semestre calendario del 2025 con "
    "un intervalo del 95 por ciento de confianza entre [29.2%, 32.1%]."
)


def test_gana_el_enunciado_cuando_el_titulo_quedo_del_mes_anterior():
    tasa, periodo, semestre = _resultado(TITULO_VIEJO)
    assert (tasa, periodo) == (29.6, "2026-05"), (
        "fechado por el título daba 2026-04, que pisa abril y deja mayo vacío"
    )
    assert semestre == "Diciembre 2025 - Mayo 2026"


def test_gana_el_titulo_cuando_el_enunciado_quedo_del_mes_anterior():
    tasa, periodo, _ = _resultado(ENUNCIADO_VIEJO)
    assert (tasa, periodo) == (30.7, "2025-10"), (
        "preferir el enunciado daba 2025-09, que ya lo había estimado el informe "
        "anterior, y dejaba octubre vacío"
    )


def test_cuando_coinciden_no_cambia_nada():
    assert _resultado(COINCIDEN)[:2] == (29.2, "2026-04")


def test_semestre_calendario_sin_meses_en_el_enunciado():
    tasa, periodo, semestre = _resultado(CALENDARIO)
    assert (tasa, periodo) == (31.6, "2026-06")
    assert semestre == "Enero 2026 - Junio 2026"


def test_semestre_calendario_escrito_del_anio():
    """«del 2025» y no «de 2025» — el informe usa las dos formas."""
    assert _resultado(CALENDARIO_DEL)[:2] == (30.6, "2025-12")


def test_la_tasa_y_el_periodo_salen_del_mismo_enunciado():
    """Si vinieran de oraciones distintas se podría emparejar la tasa de un
    semestre con la fecha de otro, que es exactamente el bug de origen.

    Este texto trae DOS tasas: la del semestre estimado y la comparación contra
    el mismo semestre del año anterior, que en los informes reales aparece más
    abajo. La que vale es la del enunciado de resultados.
    """
    texto = (
        "El nowcast estima una tasa de pobreza de 29.6 por ciento para el semestre "
        "diciembre 2025 - mayo 2026 con un intervalo del 95 por ciento de confianza "
        "entre [28.2%, 31.0%]. En la comparación con respecto al mismo semestre del "
        "año anterior la tasa de pobreza de 28.7 por ciento se redujo."
    )
    assert _resultado(texto)[:2] == (29.6, "2026-05")


def test_texto_sin_enunciado_no_inventa_periodo():
    assert _resultado("Nowcast de Pobreza. Por qué un nowcast?") is None


def test_un_hueco_en_la_serie_delata_un_informe_mal_fechado():
    """El autor publica un informe por mes y cada uno corre el semestre móvil un
    mes: la serie no puede tener huecos. El del bug era exactamente éste."""
    assert _huecos({"2026-04": 29.2, "2026-06": 31.6}) == ["2026-05"]
    assert _huecos({"2025-11": 31.0, "2026-02": 30.6}) == ["2025-12", "2026-01"]
    assert _huecos({"2025-12": 30.6, "2026-01": 30.2}) == []
    # con un punto o ninguno no hay nada que comparar, y no es un hallazgo
    assert _huecos({"2025-01": 35.8}) == [] and _huecos({}) == []
