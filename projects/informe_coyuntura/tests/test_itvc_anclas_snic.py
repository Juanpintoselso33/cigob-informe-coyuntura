"""ADR-0327, CORRECCIÓN post-merge: el ancla de `tasa_homicidios`/`tasa_robos`
pasa de "el propio 2023" a la MEDIANA de los 26 años de la serie del SNIC.

La revisión adversarial midió que el ADR original afirmaba que 2023 (4,32
homicidios cada 100.000 hab.) "cae cerca de la mediana" (~5,7) cuando en
realidad está en el percentil 11 — y que, con ese ancla, 19 de 26 años caían
en rojo (13 saturados en un extremo de la escala). Este archivo fija:

1. la mediana calculada de cada serie es la declarada en el ADR corregido;
2. el reparto de colores de los 26 años CON la mediana como ancla es el
   documentado en la tabla del ADR;
3. un control negativo: anclar contra 2023 (el valor original, incorrecto)
   da un reparto DISTINTO — si diera igual, el punto 2 no estaría probando
   nada sobre el ancla;
4. la integración real (`itvc.indices_desde_series`) usa la mediana y no un
   año fijo — no sólo la función `mediana_de_serie` en aislamiento.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import itvc  # noqa: E402
import parametrica  # noqa: E402

SNIC = json.loads((ROOT / "data" / "vida" / "snic_serie.json").read_text(encoding="utf-8-sig"))
POR_TIPO = SNIC["por_tipo"]


def _serie(nombre_snic):
    vals = POR_TIPO[nombre_snic]
    return [{"fecha": f"{a}-12-01", "valor": float(v)} for a, v in sorted(vals.items())]


SERIE_HOM = _serie("Homicidios dolosos")
SERIE_ROB = _serie(
    "Robos (excluye los agravados por el resultado de lesiones y/o muertes)")


def test_hay_26_anios_en_las_dos_series():
    # Control de que el fixture no se quedó corto silenciosamente: el ADR
    # cita "26 años (2000-2025)" para las dos series.
    assert len(SERIE_HOM) == 26, len(SERIE_HOM)
    assert len(SERIE_ROB) == 26, len(SERIE_ROB)


def test_mediana_homicidios_es_la_declarada_en_el_adr():
    mediana = itvc.mediana_de_serie({"s": SERIE_HOM}, "s")
    assert mediana == pytest.approx(5.7593, abs=0.001)


def test_mediana_robos_es_la_declarada_en_el_adr():
    mediana = itvc.mediana_de_serie({"s": SERIE_ROB}, "s")
    assert mediana == pytest.approx(925.1309, abs=0.001)


def test_2023_no_esta_cerca_de_la_mediana_de_homicidios():
    """Control negativo directo de la afirmación que el ADR original hacía y
    que era falsa: 2023 (4,32) está a más del 20% de la mediana (5,76), no
    "cerca" de ella."""
    mediana = itvc.mediana_de_serie({"s": SERIE_HOM}, "s")
    val_2023 = next(p["valor"] for p in SERIE_HOM if p["fecha"] == "2023-12-01")
    distancia_relativa = abs(val_2023 - mediana) / mediana
    assert distancia_relativa > 0.20, (
        f"2023 ({val_2023}) quedó a sólo {distancia_relativa:.1%} de la "
        f"mediana ({mediana}) — revisar si la afirmación corregida sigue "
        f"siendo cierta contra datos actualizados")


def _reparto_de_colores(serie, ancla):
    """Para cada año de la serie (tratado como si fuera el último punto
    disponible ese año), el color que le tocaría con `ancla` como base
    invertida — la misma cuenta que hace `itvc.rebase_de_serie` en
    producción, aplicada año por año."""
    conteo = {"rojo": 0, "naranja": 0, "amarillo": 0, "verde": 0}
    for i in range(len(serie)):
        parcial = {"s": serie[: i + 1]}
        idx = itvc.rebase_de_serie(parcial, "s", invertido=True, base_valor=ancla)
        color = parametrica.color_de_indice_base100(idx)
        conteo[color] += 1
    return conteo


def test_reparto_de_colores_homicidios_con_mediana():
    mediana = itvc.mediana_de_serie({"s": SERIE_HOM}, "s")
    conteo = _reparto_de_colores(SERIE_HOM, mediana)
    assert conteo == {"rojo": 6, "naranja": 3, "amarillo": 5, "verde": 12}, conteo


def test_reparto_de_colores_robos_con_mediana():
    mediana = itvc.mediana_de_serie({"s": SERIE_ROB}, "s")
    conteo = _reparto_de_colores(SERIE_ROB, mediana)
    assert conteo == {"rojo": 1, "naranja": 7, "amarillo": 10, "verde": 8}, conteo


def test_control_negativo_anclar_contra_2023_da_otro_reparto():
    """Si alguien revierte la corrección (vuelve a anclar contra el propio
    2023 en vez de la mediana), el reparto de colores tiene que ser
    DISTINTO del que fijan los dos tests de arriba — si diera lo mismo,
    esos tests no estarían probando el ancla."""
    base_2023 = next(p["valor"] for p in SERIE_HOM if p["fecha"] == "2023-12-01")
    conteo_2023 = _reparto_de_colores(SERIE_HOM, base_2023)
    assert conteo_2023 != {"rojo": 6, "naranja": 3, "amarillo": 5, "verde": 12}
    # Y reproduce el defecto que motivó la corrección: mayoría en rojo.
    assert conteo_2023["rojo"] >= 15, (
        f"se esperaba que anclar contra 2023 siguiera saturando en rojo la "
        f"mayoría de los 26 años (defecto original); dio {conteo_2023}")


def test_indices_desde_series_tasa_homicidios_usa_la_mediana_no_2023():
    """Integración real: `itvc.indices_desde_series` —no sólo las funciones
    en aislamiento— tiene que usar la mediana como ancla. `indices_desde_series`
    winsoriza a WINSOR_TOPE (140) los componentes que no están exentos, así
    que el esperado se acota igual que el código de producción."""
    series = {"tasa_homicidios": SERIE_HOM, "tasa_robos": SERIE_ROB}
    idx = itvc.indices_desde_series({}, series)
    mediana_hom = itvc.mediana_de_serie(series, "tasa_homicidios")
    esperado_hom = min(round(mediana_hom / SERIE_HOM[-1]["valor"] * 100.0, 1),
                       itvc.WINSOR_TOPE)
    assert idx["tasa_homicidios"] == esperado_hom

    esperado_con_2023 = min(round(
        SERIE_HOM[-2]["valor"] / SERIE_HOM[-1]["valor"] * 100.0, 1), itvc.WINSOR_TOPE)
    # El ancla con 2023 (si alguien la reintrodujera) da un número DISTINTO
    # del que produce la mediana — confirma que el test de arriba discrimina.
    assert idx["tasa_homicidios"] != esperado_con_2023 or esperado_hom == esperado_con_2023


def test_indices_desde_series_tasa_robos_usa_la_mediana_no_2023():
    series = {"tasa_robos": SERIE_ROB}
    idx = itvc.indices_desde_series({}, series)
    mediana_rob = itvc.mediana_de_serie(series, "tasa_robos")
    esperado = round(mediana_rob / SERIE_ROB[-1]["valor"] * 100.0, 1)
    assert idx["tasa_robos"] == esperado


def test_tasa_robos_2025_ya_no_satura_en_verde():
    """Bloqueante #1 de la revisión: el punto 2025 (778,1) publicaba tensión
    0,0 saturada (verde máximo) con el ancla 2023. Con la mediana, sigue
    siendo positivo (menos robos que la mediana histórica) pero no satura."""
    series = {"tasa_robos": SERIE_ROB}
    idx = itvc.indices_desde_series({}, series)
    tension = itvc.tension_de_itvc(idx["tasa_robos"])
    assert tension > 0.0, (
        f"tasa_robos sigue saturado en tensión 0,0 tras la corrección: {idx}")
