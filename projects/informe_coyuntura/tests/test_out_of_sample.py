# -*- coding: utf-8 -*-
"""El out-of-sample no puede volver a prometer más de lo que mide (ADR-0104)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import out_of_sample as oos


def test_el_control_positivo_no_dispara():
    """`brecha_obra_publica` es el control del método, no un caso más.

    Tiene 100 meses de serie y ADR-0088 declara que sus anclas NO se calibraron
    contra el rango observado sino alrededor del cero. Si el test funciona, esa
    banda tiene que discriminar en ambas ventanas. Si algún día dispara, lo
    primero a sospechar es el test, no la banda.
    """
    filas = {f["indicador"]: f for f in oos.analizar()["evaluados"]}
    assert "brecha_obra_publica" in filas, (
        "se perdió el control positivo: sin él, que ningún indicador dispare no "
        "prueba que el método discrimine"
    )
    assert filas["brecha_obra_publica"]["señal"] == "sin señal"


def test_toda_ventana_publica_su_rango_crudo():
    """El crudo es lo que distingue banda-que-no-alcanza de período-extremo.

    Es el dato que faltaba en la primera versión y por el que llegó a etiquetar
    `ipc_total` como circular cuando la inflación previa era genuinamente de
    ~112% anual. Sin esta columna la tabla induce esa lectura.
    """
    for f in oos.analizar()["evaluados"]:
        for ventana in ("fuera_de_muestra", "dentro_de_muestra"):
            d = f[ventana]
            assert {"crudo_min", "crudo_max", "crudo_media"} <= set(d), (
                f"{f['indicador']}/{ventana} sin rango crudo"
            )
            assert d["crudo_min"] <= d["crudo_media"] <= d["crudo_max"]


def test_no_se_concluye_sobre_ventanas_diminutas():
    """Nada evaluado con menos de un año fuera de muestra.

    `iaf_transferencias` tiene serie desde dic-2018 pero es ANUAL: cinco puntos
    previos. Concluir de ahí sería peor que no medir.
    """
    r = oos.analizar()
    for f in r["evaluados"]:
        assert f["fuera_de_muestra"]["n"] >= oos.MIN_PUNTOS
    assert any(d["indicador"] == "iaf_transferencias" for d in r["no_evaluables"])


def test_el_alcance_declarado_es_minoritario_y_se_dice():
    """La cobertura del test es su limitación principal, y tiene que verse.

    Si algún día la mayoría de los indicadores fuera evaluable, este test falla
    y hay que actualizar el ADR-0104, que hoy afirma lo contrario.
    """
    r = oos.analizar()
    assert len(r["no_evaluables"]) > len(r["evaluados"]), (
        "cambió la cobertura: revisar la conclusión de ADR-0104"
    )
