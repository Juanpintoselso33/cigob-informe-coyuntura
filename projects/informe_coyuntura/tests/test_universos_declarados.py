# -*- coding: utf-8 -*-
"""Entrega 3: cada indicador declara el universo que realmente mide (ADR-0249/0250/0251).

Los tres casos comparten la misma forma de error: **el rótulo prometía un
universo y el cálculo usaba otro**. Ninguno tenía la aritmética mal.

- `credito_privado` decía «préstamos al sector privado» y sumaba la cartera en
  dólares valuada en pesos, así que una devaluación entraba como crédito.
- `trabajo_independiente` decía «% del empleo registrado» y dejaba el
  monotributo social afuera de los dos lados del cociente.
- `pluriempleo` nombraba un fenómeno —tener más de un empleo— y medía otro: la
  tasa de subocupación demandante, que además es sobre la PEA y no sobre los
  ocupados.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import descargar_series
import itvc
import macro
import publicar


def _por_ruta(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Crédito privado: pesos, no efecto cambiario (ADR-0251) ──────────────────

def test_el_titular_usa_la_serie_en_pesos():
    """La 26 es `MEyML` en el propio catálogo del BCRA: pesos Y moneda
    extranjera valuada en pesos. El titular tiene que salir de la 117."""
    assert macro.BCRA_PRESTAMOS_ID == 117
    assert macro.BCRA_PRESTAMOS_TOT_ID == 26
    assert macro.BCRA_PRESTAMOS_USD_ID == 125
    assert macro.BCRA_PRESTAMOS_ME_ID == 126


@pytest.fixture
def bcra_sintetico(monkeypatch):
    """Un año sin crédito nuevo en pesos y con una devaluación del 50%.

    Los saldos en pesos y en dólares no se mueven; sólo cambia el tipo de
    cambio, así que la cartera en moneda extranjera vale un 50% más en pesos.
    Con inflación cero, la respuesta correcta es **0% real**."""
    saldos = {
        117: {"2025-07": 100.0, "2026-07": 100.0},          # pesos, quieto
        125: {"2025-07": 10.0, "2026-07": 10.0},            # dólares, quieto
        126: {"2025-07": 50.0, "2026-07": 75.0},            # +50% por el TC
        26:  {"2025-07": 150.0, "2026-07": 175.0},          # el total se mueve
    }
    monkeypatch.setattr(macro, "_bcra_fin_de_mes", lambda vid, n=16: dict(saldos[vid]))
    monkeypatch.setattr(macro, "_ipc_indice_mensual", lambda n=20: {"2025-07": 100.0,
                                                                    "2026-07": 100.0})
    monkeypatch.setattr(macro, "_bcra_detalle", lambda vid, dias=400: [
        {"fecha": "2026-07-31", "valor": 100.0}])
    return saldos


def test_una_devaluacion_sin_prestamos_nuevos_no_es_crecimiento(bcra_sintetico):
    """El criterio de aceptación que pidió la auditoría.

    Es lo que hacía el indicador anterior: con estos mismos saldos, la var. 26
    da +16,7% real y no se prestó un peso más."""
    card = macro.fetch_credito_privado()
    assert card is not None
    assert card["valor"] == 0.0, "el efecto cambiario se coló en el titular"
    assert card["total_ia_real"] > 15, (
        "el fixture perdió la devaluación: si el total tampoco se mueve, el "
        "test no prueba nada")


def test_el_credito_en_dolares_no_desaparece_se_desglosa(bcra_sintetico):
    """No se descarta: se muestra en su propia unidad y en pesos, que es donde
    se puede leer sin que se mezcle con el tipo de cambio."""
    card = macro.fetch_credito_privado()
    assert card["usd_ia"] == 0.0                       # en dólares no creció
    assert card["me_en_pesos_ia_real"] == 50.0         # en pesos, la devaluación
    assert "moneda extranjera" in card["detalle_txt"]


def test_la_unidad_dice_que_es_en_pesos(bcra_sintetico):
    card = macro.fetch_credito_privado()
    assert "pesos" in card["unidad"]
    assert "var. 117" in card["fuente"]
    assert "var. 26" not in card["fuente"]


def test_card_y_serie_leen_la_misma_variable():
    """El desacople clásico: el titular cambia de serie y el gráfico se queda
    con la anterior, y el gate G3 lo lee como un dato desactualizado."""
    fuente = descargar_series.VIDA_DERIVADAS  # noqa: F841  (sólo para importar)
    macro_defs = {d[0]: d for d in descargar_series.MACRO_DERIVADAS}
    assert "var. 117" in macro_defs["credito_privado"][2]
    assert "pesos" in macro_defs["credito_privado"][1]


# ── Trabajo independiente: universo restringido, y declarado (ADR-0250) ─────

@pytest.fixture(scope="module")
def colector_ti():
    return _por_ruta("ti", RAIZ / "scripts" / "vida_cotidiana" / "collectors"
                     / "trabajo_independiente.py")


def test_enumera_las_categorias_de_los_dos_lados(colector_ti):
    """Un porcentaje sobre un universo restringido tiene que poder
    enumerarse. Es la diferencia entre una exclusión declarada y un recorte."""
    assert colector_ti.CATEGORIAS_NUMERADOR == ("autónomos", "monotributo general")
    assert set(colector_ti.CATEGORIAS_DENOMINADOR) == {
        "autónomos", "monotributo general", "asalariados privados",
        "asalariados públicos", "casas particulares"}
    # el numerador está contenido en el denominador
    assert set(colector_ti.CATEGORIAS_NUMERADOR) <= set(colector_ti.CATEGORIAS_DENOMINADOR)


def test_el_regimen_excluido_esta_nombrado(colector_ti):
    """La exclusión es una decisión visible, no un olvido: se nombra el régimen
    y el mes del quiebre que la justifica."""
    nombre, serie, quiebre = colector_ti.EXCLUIDA
    assert nombre == "monotributo_social"
    assert quiebre == "2024-12"
    assert serie.startswith("151.1_")


def test_la_unidad_declara_el_universo_restringido():
    """«% del empleo registrado» a secas prometía SIPA entero. El rótulo tiene
    que decir qué queda afuera, o el lector compara contra otra cosa."""
    fuentes = {d[0]: d for d in descargar_series.VIDA_DERIVADAS}
    unidad = fuentes["trabajo_independiente"][1]
    assert "sin monotributo social" in unidad
    assert unidad != "% del empleo registrado"


# ── Subocupación demandante: el nombre y la base (ADR-0249) ─────────────────

CLAVE_VIEJA = "pluriempleo"
CLAVE = "subocupacion_demandante"


def test_el_indicador_se_llama_como_lo_que_mide():
    en_dimensiones = {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    assert CLAVE in en_dimensiones
    assert CLAVE_VIEJA not in en_dimensiones


def test_la_clave_vieja_no_sobrevive_en_ningun_lado():
    """Migración explícita, no dos claves conviviendo. `pluriempleo` sólo puede
    quedar donde documenta el OTRO indicador —el que no se construyó— y en los
    ADR, que son registro histórico."""
    vivos = []
    for ruta in (RAIZ / "scripts").rglob("*.py"):
        if "vida_cotidiana/data" in ruta.as_posix():
            continue
        texto = ruta.read_text(encoding="utf-8")
        if CLAVE_VIEJA not in texto:
            continue
        # `manual.py` documenta cómo se construiría el pluriempleo de verdad
        if ruta.name == "manual.py":
            continue
        for linea in texto.splitlines():
            limpia = linea.strip()
            if CLAVE_VIEJA not in limpia or limpia.startswith("#"):
                continue
            # La declaración de sustitución TIENE que nombrar la clave vieja:
            # es lo que la purga del CSV en una corrida acotada.
            if CLAVE_VIEJA in limpia and CLAVE in limpia:
                continue
            vivos.append(f"{ruta.name}: {limpia[:90]}")
    assert not vivos, "quedó la clave vieja como identificador:\n  " + "\n  ".join(vivos)


def test_la_serie_historica_se_migro_entera():
    """El renombre no puede perder la historia ni duplicarla."""
    csv = (RAIZ / "output" / "series" / "vida_cotidiana.csv").read_text(encoding="utf-8-sig")
    filas_nuevas = [l for l in csv.splitlines() if f",{CLAVE}," in l]
    filas_viejas = [l for l in csv.splitlines() if f",{CLAVE_VIEJA}," in l]
    assert len(filas_nuevas) >= 40
    assert not filas_viejas


def test_la_serie_declara_la_base_correcta():
    """INDEC calcula la tasa sobre la PEA. Decir «% de ocupados» invita a
    compararla con la tasa de empleo, que sí es sobre la población."""
    csv = (RAIZ / "output" / "series" / "vida_cotidiana.csv").read_text(encoding="utf-8-sig")
    filas = [l for l in csv.splitlines() if f",{CLAVE}," in l]
    assert all("% de la PEA" in l for l in filas)
    fuentes = {d[0]: d for d in descargar_series.VIDA_DERIVADAS}
    assert fuentes[CLAVE][1] == "% de la PEA"


def test_la_web_no_dice_que_es_sobre_los_ocupados():
    datos = (RAIZ / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
    assert f'{CLAVE}: "% de la PEA"' in datos
    assert f'{CLAVE}: "% de ocupados"' not in datos
    assert f"{CLAVE_VIEJA}:" not in datos


def test_el_renombre_purga_la_clave_vieja_en_una_corrida_acotada():
    """Una corrida por indicador hace merge con el CSV que ya está. Sin
    declararlo como sustitución, quedarían las dos claves como si fueran series
    distintas del mismo cinturón."""
    assert descargar_series.INDICADORES_SUSTITUIDOS[CLAVE] == {CLAVE_VIEJA}
