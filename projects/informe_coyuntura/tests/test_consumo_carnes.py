# -*- coding: utf-8 -*-
"""El parser del tablero de carnes de SAGYP se autoverifica (plan de adopción).

El PDF es un gráfico aplanado: los números salen mezclados con las etiquetas de
los ejes y sin orden estable. Un parser posicional devolvería el número
equivocado en silencio la primera vez que la fuente mueva algo.

Por eso el parser RESUELVE: empareja cada nivel con su año anterior de modo que
el cociente reproduzca la variación que el propio PDF publica, y además exige
que los tres componentes sumen el total publicado. Estos tests fijan las dos
defensas, no el layout.
"""
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

# El módulo se carga POR RUTA y no agregando scripts/vida_cotidiana al sys.path.
# Ese directorio tiene su propio `config.py`, y ponerlo en el path tapa al
# `config.py` de la raíz para toda la sesión de pytest: rompe la importación de
# otros doce módulos de test, que quedan sin UMBRALES ni PESOS_CINTURONES. El
# sys.path es estado global compartido entre archivos de test.
_spec = importlib.util.spec_from_file_location(
    "consumo_carnes",
    RAIZ / "scripts" / "vida_cotidiana" / "collectors" / "consumo_carnes.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


# Texto tal como lo aplana pdfplumber sobre el tablero de junio de 2026.
# Se conserva el desorden a propósito: es el caso real que el parser resuelve.
TEXTO_JUNIO_2026 = """2026
Al mes de JUNIO
CONSUMO DE CARNES
CONSUMO PER CAPITA PROMEDIO CONSUMO PER CAPITA PROMEDIO Variación del consumo per capita
MÓVIL 2026 (en Kg) MÓVIL 2025 (en Kg) MÓVIL de carnes 2026 / 2025
140,00 140,00 TOTAL -1,69%
114,45 116,42 TOTAL -1,97
120,00 120,00
100,00 100,00
Carne aviar 0,57%
Carne aviar 0,27
80,00 80,00
51,21
60,00 47,28 47,24 60,00 46,97
Carne Porcina 9,29%
Carne Porcina 1,70
40,00 40,00
19,93 18,24
20,00
20,00
-7,67%
Carne Vacuna Carne Vacuna -3,93
CONSUMO PER CAPITA MÓVIL AL MES DE JUNIO TODAS LAS CARNES
CARNE VACUNA CARNE AVIAR CARNE PORCINA
117,05 116,42
53,67 50,78 51,21 49,27 48,03 47,28 46,29 46,58 46,65 45,67 46,97 47,24
110,57 114,09 110,50 114,45 19,93 18,24 15,01 16,73 16,72 16,80
"""


def _parsear(texto):
    """Salta pdfplumber: los tests fijan la LÓGICA, no la extracción del PDF."""
    return texto


def test_lee_los_cuatro_niveles_del_mes():
    variaciones = cc._variaciones(TEXTO_JUNIO_2026)
    pares = cc._emparejar(cc._numeros(TEXTO_JUNIO_2026), variaciones)
    actual = {k: v[0] for k, v in pares.items()}
    assert actual == {"vacuna": 47.28, "aviar": 47.24, "porcina": 19.93, "total": 114.45}


def test_la_variacion_de_vacuna_viene_antes_de_su_etiqueta():
    """El único tramo negativo queda del otro lado al aplanar el gráfico: la
    etiqueta va después del porcentaje. Si el parser sólo mirara hacia adelante,
    perdería justo la carne que el indicador vigente ya mide."""
    v = cc._variaciones(TEXTO_JUNIO_2026)
    assert v["vacuna"] == -7.67
    assert v == {"vacuna": -7.67, "aviar": 0.57, "porcina": 9.29, "total": -1.69}


def test_los_componentes_suman_el_total_publicado():
    variaciones = cc._variaciones(TEXTO_JUNIO_2026)
    a = {k: v[0] for k, v in cc._emparejar(cc._numeros(TEXTO_JUNIO_2026), variaciones).items()}
    assert a["vacuna"] + a["aviar"] + a["porcina"] == pytest.approx(a["total"], abs=0.01)


def test_ignora_la_serie_anual_del_pie():
    """Abajo el PDF repite cinco años por categoría, con valores muy parecidos
    entre sí. Si entraran al emparejamiento, más de un par reproduciría la misma
    variación y el resultado seria ambiguo."""
    completos = cc._numeros(TEXTO_JUNIO_2026)
    assert 53.67 not in completos and 15.01 not in completos
    assert len(completos) == 8


def test_falla_si_el_total_deja_de_ser_la_suma():
    """Si SAGYP suma ovina o pescado al total, el indicador cambia de
    perímetro sin avisar. Tiene que romper, no seguir publicando."""
    roto = TEXTO_JUNIO_2026.replace("114,45 116,42", "134,45 136,42")
    with pytest.raises(ValueError):
        _validar(roto)


def _validar(texto):
    variaciones = cc._variaciones(texto)
    a = {k: v[0] for k, v in cc._emparejar(cc._numeros(texto), variaciones).items()}
    suma = a["vacuna"] + a["aviar"] + a["porcina"]
    if abs(suma - a["total"]) > 0.5:
        raise ValueError("cambió el perímetro")
    return a


def test_ratio_bovina_es_el_componente_c():
    """C = qué porción del consumo total sigue siendo vacuna. Es el que
    distingue sustitución (C cae, total se sostiene) de empobrecimiento
    (C y total caen juntos)."""
    a = _validar(TEXTO_JUNIO_2026)
    assert round(a["vacuna"] / a["total"] * 100, 2) == 41.31
