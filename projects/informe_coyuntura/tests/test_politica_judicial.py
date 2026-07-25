"""Tests de la dimensión del Poder Judicial en el ITCP (ADR-0126)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcp
import parametrica
import politica

BANDAS = itcp.BANDAS_ITCP["cobertura_judicial"]


# ── Dimensión y pesos ───────────────────────────────────────────────────────

def test_la_dimension_existe_con_su_indicador():
    d = itcp.DIMENSIONES_ITCP["poder_judicial"]
    assert d["peso"] == 0.15
    assert d["indicadores"] == {"cobertura_judicial": 1.0}


def test_los_pesos_entre_dimensiones_suman_uno():
    assert abs(sum(d["peso"] for d in itcp.DIMENSIONES_ITCP.values()) - 1.0) < 1e-9


def test_el_orden_relativo_de_las_dimensiones_previas_se_conservo():
    """ADR-0126 hace ceder a las seis existentes PROPORCIONALMENTE. Si alguien
    aprovecha el cambio para reordenarlas, este test lo marca: mover pesos
    entre dimensiones es una decisión editorial con ADR propio (ADR-0036)."""
    p = {k: v["peso"] for k, v in itcp.DIMENSIONES_ITCP.items()}
    orden = ["poder_legislativo", "alianzas_territoriales", "cohesion_interna",
             "sector_privado", "conflicto_social", "imagen_voto"]
    valores = [p[k] for k in orden]
    assert valores == sorted(valores, reverse=True), p


def test_los_pesos_internos_de_cada_dimension_suman_uno():
    for nombre, d in itcp.DIMENSIONES_ITCP.items():
        assert abs(sum(d["indicadores"].values()) - 1.0) < 1e-9, nombre


# ── Bandas ──────────────────────────────────────────────────────────────────

def test_las_bandas_cubren_todo_el_rango():
    for v in (0.0, 55.0, 64.08, 69.95, 72.77, 85.0, 100.0):
        parametrica.puntaje_banda(v, BANDAS)


def test_las_bandas_no_se_calibraron_al_rango_observado():
    """El rango 2023-2026 es 64-73%. Si los cortes se hubieran ajustado a él,
    el techo estaría cerca de 73 y el piso cerca de 64. Están en 90 y 60: la
    escala describe la cobertura de un cuerpo, no el desempeño del período
    (ADR-0045)."""
    finitos = sorted({c for low, high, _ in BANDAS for c in (low, high)
                      if abs(c) != float("inf")})
    assert max(finitos) >= 90.0, finitos
    assert min(finitos) <= 60.0, finitos


def test_el_puntaje_discrimina_en_el_rango_real():
    """Aunque sólo dos bandas estén pobladas, la interpolación tiene que separar
    el piso del techo del período. Si esta amplitud se achica, el indicador deja
    de aportar variación al índice."""
    piso = parametrica.puntaje_interpolado(64.08, BANDAS)
    techo = parametrica.puntaje_interpolado(72.77, BANDAS)
    assert techo - piso >= 20.0, (piso, techo)


def test_mas_cobertura_es_mejor_puntaje():
    puntajes = [parametrica.puntaje_interpolado(v, BANDAS)
                for v in range(55, 96, 5)]
    assert puntajes == sorted(puntajes), puntajes


# ── Serie ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("campo", ["total_cargos", "vacantes_padron",
                                   "fecha_padron", "composicion"])
def test_los_metadatos_del_padron_llegan(campo):
    _, meta = _serie()
    assert campo in meta


def _serie():
    try:
        return politica.cobertura_judicial_serie()
    except Exception as e:                      # red caída en CI
        pytest.skip(f"fuente inaccesible: {e}")


def test_la_serie_arranca_en_diciembre_2023_y_no_tiene_huecos():
    serie, _ = _serie()
    meses = sorted(serie)
    assert meses[0] == "2023-12"
    for a, b in zip(meses, meses[1:]):
        anio, mes = int(a[:4]), int(a[5:7]) + 1
        siguiente = f"{anio + 1}-01" if mes == 13 else f"{anio}-{mes:02d}"
        assert b == siguiente, f"hueco entre {a} y {b}"


def test_la_cobertura_esta_en_un_rango_plausible():
    serie, _ = _serie()
    for ym, v in serie.items():
        assert 0.0 <= v <= 100.0, (ym, v)
        assert 40.0 < v < 95.0, f"{ym}={v}: valor implausible para cobertura judicial"


def test_las_subrogancias_no_cuentan_como_cobertura():
    """La decisión central del indicador (ADR-0126): un cargo servido por un
    subrogante es un cargo vacante. Si mañana se contaran como cubiertos, la
    cobertura saltaría ~30 puntos sin que nada haya cambiado en la realidad.

    La igualdad no es exacta y la diferencia tiene explicación: un puñado de
    cargos tiene titular designado EN LICENCIA y un subrogante a cargo. Ese
    cargo NO está vacante —tiene juez designado— aunque su cobertura figure
    como subrogante. Al 05-jun-2026 son seis. Se admite ese margen chico y se
    rechaza que las 282 subrogancias plenas entren como cobertura."""
    _, meta = _serie()
    comp = meta["composicion"]
    titular = comp.get("Titular", 0)
    subrogante = comp.get("Subrogante", 0)
    cubiertos = meta["total_cargos"] - meta["vacantes_padron"]

    assert subrogante > 0, "el padrón dejó de informar subrogancias"
    # los cubiertos son los titulares más, a lo sumo, unas pocas licencias
    assert titular <= cubiertos <= titular + 0.1 * subrogante, (
        f"cubiertos={cubiertos}, titulares={titular}, subrogantes={subrogante}: "
        f"las subrogancias parecen estar contándose como cobertura")
