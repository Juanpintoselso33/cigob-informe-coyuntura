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

def test_la_dimension_existe_con_sus_indicadores():
    """ADR-0126 abrió la dimensión con un solo indicador y dejó escrito que eso
    era «una limitación real, no un diseño terminado»: la cobertura mide la
    CAPACIDAD de integrar el Poder Judicial, no su COMPORTAMIENTO. ADR-0168 la
    cierra sumando los tres que medían comportamiento."""
    d = itcp.DIMENSIONES_ITCP["poder_judicial"]
    assert d["peso"] == 0.15
    assert d["indicadores"] == {
        "cobertura_judicial": 0.40, "judicializacion": 0.20,
        "velocidad_resolucion": 0.20, "paralisis_denuncias": 0.20,
    }
    assert abs(sum(d["indicadores"].values()) - 1.0) < 1e-9
    assert d["indicadores"]["cobertura_judicial"] > 0.20, (
        "cobertura_judicial lleva el peso mayor por ser el único mensual y el "
        "de menor rezago (1 mes contra 2-12 de los otros tres)")


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


# ── El número y su explicación (ADR-0240) ────────────────────────────────────
# La card publicaba 69,63% arriba y «604 de 955 cargos» abajo, que es 63,25%.
# No era un redondeo: el porcentaje contaba `cargo_vacante` al corte de hoy y el
# texto contaba `cargo_cobertura` a la fecha del padrón —dos definiciones y dos
# cortes—. Ningún gate compara un texto con el número que dice explicar.

class _PadronFalso:
    """Padrón mínimo con la trampa real adentro: seis cargos NO vacantes cuyo
    `cargo_cobertura` dice «Subrogante» porque el titular está de licencia. Son
    los que hacen que 610 y 604 no sean el mismo número."""

    def __init__(self, con_titular=604, con_licencia=6, subrogados=276, sin_cubrir=69):
        self.filas = (
            [{"organo_habilitado": "SI", "cargo_vacante": "NO",
              "cargo_cobertura": "Titular"}] * con_titular
            + [{"organo_habilitado": "SI", "cargo_vacante": "NO",
                "cargo_cobertura": "Subrogante"}] * con_licencia
            + [{"organo_habilitado": "SI", "cargo_vacante": "SI",
                "cargo_cobertura": "Subrogante"}] * subrogados
            + [{"organo_habilitado": "SI", "cargo_vacante": "SI",
                "cargo_cobertura": "Sin subrogante designado"}] * sin_cubrir
            # un órgano no habilitado: no entra al denominador
            + [{"organo_habilitado": "NO", "cargo_vacante": "SI",
                "cargo_cobertura": "Sin subrogante designado"}] * 47
        )


@pytest.fixture
def padron_falso(monkeypatch):
    p = _PadronFalso()

    def _csv(q, *a, **k):
        if q == politica.JUS_PADRON_Q:
            return p.filas
        if q == politica.JUS_DESIGNACIONES_Q:
            return [{"cargo_tipo": "Juez", "fecha_desginacion": "2026-06-24"}] * 60
        return [{"cargo_tipo": "Juez", "fecha_renuncia": "2026-07-01"}] * 5

    monkeypatch.setattr(politica, "_jus_csv", _csv)
    monkeypatch.setattr(politica, "_jus_fecha_padron", lambda: "2026-06-05")
    return p


def test_el_valor_es_el_cociente_que_la_card_publica(padron_falso):
    """`valor == 100 · numerador / denominador`, con los dos del MISMO corte.

    Es la guarda que la auditoría pidió, y la que no existía: cualquiera de las
    dos mitades podía moverse sola."""
    card = politica.fetch_cobertura_judicial()
    assert card is not None
    esperado = 100.0 * card["cargos_con_juez"] / card["cargos_totales"]
    assert abs(card["valor"] - esperado) < 0.01


def test_el_numerador_del_padron_no_se_publica_como_numerador_del_valor(padron_falso):
    """604 es del padrón y con otra definición; 665 es el numerador del valor.

    Si vuelven a coincidir, alguien mezcló los cortes otra vez."""
    card = politica.fetch_cobertura_judicial()
    assert card["cargos_con_juez"] == 665
    assert card["padron_titular"] == 604
    assert card["padron_con_juez"] == 610
    assert card["cargos_con_juez"] != card["padron_titular"]


def test_el_valor_erroneo_no_puede_volver(padron_falso):
    """63,25% es 604/955: el número que la card *decía* mientras publicaba otro.

    No es que 63,25% esté mal a secas —es correcto para 'cargos con titular en
    funciones al 5-jun'—: está mal como explicación de 69,63%."""
    card = politica.fetch_cobertura_judicial()
    assert abs(card["valor"] - 69.63) < 0.01
    assert abs(card["valor"] - 63.25) > 1.0


def test_cada_numero_viaja_con_su_fecha(padron_falso):
    """El corte del valor y el del padrón son distintos y los dos se publican.

    Publicar un porcentaje sin decir a qué fecha corresponde su numerador es lo
    que permitió que las dos fechas convivieran sin que se notara."""
    card = politica.fetch_cobertura_judicial()
    assert card["fecha_padron"] == "2026-06-05"
    assert card["fecha_corte"] > card["fecha_padron"]
    assert card["fecha_padron"] in card["detalle_txt"]
    assert card["fecha_corte"] in card["detalle_txt"]


def test_el_inventario_explica_la_distancia_entre_las_dos_fechas(padron_falso):
    """665 = 610 + 60 designaciones − 5 renuncias. La cuenta tiene que cerrar
    con lo que la card declara, no con lo que el lector suponga."""
    card = politica.fetch_cobertura_judicial()
    assert (card["padron_con_juez"]
            + card["designaciones_desde_padron"]
            - card["renuncias_desde_padron"]) == card["cargos_con_juez"]


def test_la_composicion_del_padron_suma_el_denominador(padron_falso):
    """604 + 282 + 69 = 955. Es una partición del total, no del numerador: si el
    texto la presentara como desglose de 610 estaría mintiendo por omisión."""
    card = politica.fetch_cobertura_judicial()
    assert (card["padron_titular"] + card["padron_subrogante"]
            + card["padron_sin_cubrir"]) == card["cargos_totales"]


def test_una_designacion_futura_no_adelanta_cobertura(padron_falso, monkeypatch):
    """El dataset trae designaciones con fecha posterior a hoy.

    Contarlas publicaría como cubierto un cargo que todavía no lo está, y el
    error entraría solo el día que esa fecha llegue."""
    from datetime import date, timedelta
    futura = (date.today() + timedelta(days=90)).isoformat()

    def _csv(q, *a, **k):
        if q == politica.JUS_PADRON_Q:
            return padron_falso.filas
        if q == politica.JUS_DESIGNACIONES_Q:
            return ([{"cargo_tipo": "Juez", "fecha_desginacion": "2026-06-24"}] * 60
                    + [{"cargo_tipo": "Juez", "fecha_desginacion": futura}] * 20)
        return [{"cargo_tipo": "Juez", "fecha_renuncia": "2026-07-01"}] * 5

    monkeypatch.setattr(politica, "_jus_csv", _csv)
    card = politica.fetch_cobertura_judicial()
    assert card["designaciones_desde_padron"] == 60
    assert card["cargos_con_juez"] == 665


def test_el_denominador_son_los_organos_habilitados(padron_falso):
    """47 cargos de órganos no habilitados no existen todavía: meterlos en el
    denominador bajaría la cobertura sin que nada hubiera pasado."""
    card = politica.fetch_cobertura_judicial()
    assert card["cargos_totales"] == 955
