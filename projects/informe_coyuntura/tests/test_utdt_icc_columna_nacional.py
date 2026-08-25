# -*- coding: utf-8 -*-
"""El ICC que se publica es el nacional, no el de CABA (ADR-0242).

El colector leía la **columna 1 por posición**, que en el cuadro de la UTDT es
`ICC Capital`. Durante meses el tablero publicó el índice de la Ciudad de Buenos
Aires rotulado «total nacional»: 39,87 donde el nacional era 40,23.

Card y serie leían la misma columna equivocada, así que coincidían entre sí y el
gate G3 —que compara la card contra el último punto de la serie— no tenía nada
que marcar. Dos cosas mal de la misma manera se ven bien.

El fixture congela los encabezados **reales**, con la trampa adentro: la primera
fila trae el banner `ICC Nacional - Desagregación por regiones` **encima de la
columna de Capital**.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import xlrd

RAIZ = Path(__file__).resolve().parents[1]

# El colector se carga POR RUTA, y su `config` también: `scripts/vida_cotidiana/`
# tiene el suyo, y corrido dentro de la suite completa el nombre `config` ya
# quedó tomado por el de la raíz del proyecto —otro archivo— en `sys.modules`.
# Poner el directorio al frente del path no alcanza: hay que suplantar el módulo
# mientras dura la carga y devolverlo después. Es la misma trampa que ya
# documentan `indec_supermercados` y `dnrpa_autos`.
def _cargar_por_ruta(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_VIDA = RAIZ / "scripts" / "vida_cotidiana"
_previo = sys.modules.get("config")
sys.modules["config"] = _cargar_por_ruta("config", _VIDA / "config.py")
try:
    utdt_icc = _cargar_por_ruta("utdt_icc", _VIDA / "collectors" / "utdt_icc.py")
finally:
    if _previo is not None:
        sys.modules["config"] = _previo
    else:
        sys.modules.pop("config", None)

FIXTURE = Path(__file__).parent / "fixtures" / "utdt_icc_regiones.json"


@pytest.fixture(scope="module")
def datos():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class _Celda:
    def __init__(self, valor):
        if valor is None:
            self.ctype, self.value = xlrd.XL_CELL_EMPTY, ""
        elif isinstance(valor, str):
            self.ctype, self.value = xlrd.XL_CELL_TEXT, valor
        else:
            self.ctype, self.value = xlrd.XL_CELL_NUMBER, float(valor)


class _Hoja:
    """Hoja mínima con la forma real del cuadro: tres filas de encabezado y las
    cuatro series en las columnas 1, 3, 5 y 7."""

    def __init__(self, encabezado, filas, columnas):
        self.grilla = [[_Celda(v) for v in fila] for fila in encabezado]
        ancho = max(len(f) for f in encabezado)
        for f in filas:
            fila = [None] * ancho
            for nombre, j in columnas.items():
                fila[j] = f.get(nombre)
            self.grilla.append([_Celda(v) for v in fila])
        self.nrows = len(self.grilla)
        self.ncols = ancho

    def cell(self, i, j):
        return self.grilla[i][j]


@pytest.fixture
def hoja(datos):
    return _Hoja(datos["encabezado"], datos["filas"], datos["_columnas_reales"])


def test_ubica_la_columna_nacional(hoja, datos):
    assert utdt_icc.columna_icc_nacional(hoja) == datos["_columnas_reales"]["nacional"]


def test_no_elige_capital_aunque_el_banner_diga_nacional(hoja, datos):
    """La trampa que haría fallar a la solución obvia.

    Un `"nacional" in encabezado` que leyera las tres filas elegiría **Capital**,
    porque arriba tiene el banner `ICC Nacional - Desagregación por regiones`.
    Sería el mismo error de antes, ahora con aire de estar ubicado por nombre."""
    assert utdt_icc.columna_icc_nacional(hoja) != datos["_columnas_reales"]["capital"]
    banner = datos["encabezado"][0][datos["_columnas_reales"]["capital"]]
    assert banner and "Nacional" in banner, (
        "el fixture perdió el banner; sin él este test no prueba nada"
    )


def test_descartar_el_banner_alcanza_aunque_cambie_el_nombre_de_la_region():
    """Contra el cuadro de hoy hay dos guardas y cualquiera alcanza: se descarta
    el banner Y se excluyen los rótulos regionales. Son redundantes a propósito,
    porque cubren derivas distintas.

    Acá se prueba la que sostiene el caso que la otra no ve: si la UTDT
    renombrara `Capital` a `CABA` —que no está en la lista de regiones— lo único
    que impide volver a elegir esa columna es haber descartado el banner."""
    encabezado = [
        ["SERIES", "ICC Nacional - Desagregación por regiones", None, "ICC", None],
        [None, "ICC ", "Variación", "Nacional", None],
        [None, "CABA", "mensual", None, None],
    ]
    hoja = _Hoja(encabezado, [{"caba": 39.87, "nac": 40.23}], {"caba": 1, "nac": 3})
    assert utdt_icc.columna_icc_nacional(hoja) == 3


def test_excluir_las_regiones_alcanza_si_la_columna_regional_dice_nacional():
    """La otra mitad de la redundancia.

    El caso que el descarte del banner NO ve: que la propia columna regional
    lleve la palabra en su rótulo, como `ICC Nacional - Capital`. No es
    rebuscado: es exactamente el texto del banner de hoy, una fila más abajo. Lo
    único que impide elegirla es que además nombre una región."""
    encabezado = [
        ["SERIES", None, None, "ICC", None],
        [None, "ICC Nacional -", "Variación", "Nacional", None],
        [None, "Capital", "mensual", None, None],
    ]
    hoja = _Hoja(encabezado, [{"cap": 39.87, "nac": 40.23}], {"cap": 1, "nac": 3})
    assert utdt_icc.columna_icc_nacional(hoja) == 3


def test_el_valor_publicado_es_el_nacional(hoja, datos):
    esperado = datos["esperado"]
    col = utdt_icc.columna_icc_nacional(hoja)
    ultima = hoja.grilla[-1]
    assert abs(ultima[col].value - esperado["nacional"]) < 0.01


def test_el_valor_erroneo_no_puede_volver(hoja, datos):
    """39,87 es CABA. No está mal como número: está mal como total nacional."""
    esperado = datos["esperado"]
    col = utdt_icc.columna_icc_nacional(hoja)
    assert abs(hoja.grilla[-1][col].value - esperado["capital_erroneo"]) > 0.2


def test_no_confunde_una_columna_de_variacion(hoja):
    """Al lado de cada índice hay su variación mensual. Elegir esa columna daría
    un número chiquito y plausible —0,01 en vez de 40,2— y el semáforo lo leería
    como confianza en piso."""
    col = utdt_icc.columna_icc_nacional(hoja)
    partes = " ".join(str(hoja.cell(i, col).value).lower() for i in range(3))
    assert "variaci" not in partes


def test_si_el_cuadro_cambia_de_forma_falla(datos):
    """Sin columna nacional identificable, mejor fallar que volver a la
    posición: un colector que adivina publica CABA sin decirlo."""
    encabezado = [
        ["SERIES", "ICC Nacional - Desagregación por regiones", None],
        [None, "ICC ", "Variación"],
        [None, "Capital", "mensual"],
    ]
    hoja = _Hoja(encabezado, [{"capital": 39.87}], {"capital": 1})
    with pytest.raises(ValueError, match="ICC Nacional"):
        utdt_icc.columna_icc_nacional(hoja)


def test_dos_columnas_nacionales_tampoco_pasan():
    """Ambigüedad no es lo mismo que ausencia, pero se trata igual: elegir la
    primera sería una convención inventada."""
    encabezado = [
        ["SERIES", "ICC", "ICC"],
        [None, "Nacional", "Nacional"],
        [None, None, None],
    ]
    hoja = _Hoja(encabezado, [{"a": 40.0, "b": 41.0}], {"a": 1, "b": 2})
    with pytest.raises(ValueError):
        utdt_icc.columna_icc_nacional(hoja)


def test_la_serie_nacional_cubre_lo_que_el_itvc_necesita(datos):
    """El ITVC arranca en dic-2023 y la columna nacional empieza en 2001-03, así
    que la historia se reconstruye entera sin empalmar con la de Capital.

    El fixture guarda 30 períodos; la cobertura completa se midió sobre el XLS
    entero y quedó anotada. Lo que el fixture sí prueba es que en su ventana la
    columna nacional no tiene huecos."""
    cob = datos["_cobertura_verificada"]
    assert cob["primer_periodo_nacional"] < "2023-12"
    assert cob["puntos_nacionales"] > 250
    nacionales = [f for f in datos["filas"] if f["nacional"] is not None]
    assert len(nacionales) == len(datos["filas"]), "hueco en la columna nacional"


def test_las_cuatro_series_son_distintas(datos):
    """Si Capital y Nacional coincidieran, el error no habría tenido efecto y
    este arreglo no haría falta. La distancia media dice cuánto valía."""
    pares = [(f["capital"], f["nacional"]) for f in datos["filas"]
             if f["capital"] is not None and f["nacional"] is not None]
    assert pares
    brecha = sum(abs(c - n) for c, n in pares) / len(pares)
    assert brecha > 0.3, f"brecha media {brecha:.2f}: el fixture perdió el caso"
