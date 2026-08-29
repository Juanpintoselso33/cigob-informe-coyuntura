"""Tests de la dimensión del Poder Judicial en el ITCP (ADR-0126)."""
import sys
from datetime import date
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


# ── Universo de sesiones de control (ADR-0268) ──────────────────────────────

@pytest.fixture
def consejo_posts():
    path = Path(__file__).parent / "fixtures" / "consejo_comisiones_posts.json"
    import json
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def consejo_api_falsa(monkeypatch, consejo_posts):
    class Respuesta:
        status_code = 200
        headers = {}

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            return None

    def get(_url, params=None, **_kwargs):
        categoria = int(params["categories"])
        nombre = next(k for k, v in politica.CONSEJO_CATS.items() if v == categoria)
        return Respuesta(consejo_posts[nombre])

    monkeypatch.setattr(politica.requests, "get", get)


def test_una_nota_conjunta_asignada_a_una_categoria_aporta_ambas_comisiones(
        monkeypatch):
    post = {
        "id": 1,
        "date": "2026-08-20T12:00:00",
        "slug": "sesionaron-las-comisiones-de-acusacion-y-de-disciplina",
        "link": "https://consejo.test/1",
        "title": {"rendered": (
            "Sesionaron las Comisiones de Acusación y de Disciplina")},
        "content": {"rendered": "<p>Ambas comisiones celebraron su sesión.</p>"},
    }

    class Respuesta:
        status_code = 200
        headers = {"X-WP-TotalPages": "1"}

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            return None

    def get(_url, params=None, **_kwargs):
        data = [post] if int(params["categories"]) == politica.CONSEJO_CATS["acusacion"] else []
        return Respuesta(data)

    monkeypatch.setattr(politica.requests, "get", get)
    inventario = politica._consejo_inventario_sesiones()
    assert {(e["fecha"], e["comision"]) for e in inventario} == {
        ("2026-08-20", "acusacion"), ("2026-08-20", "disciplina"),
    }


def test_la_paginacion_respeta_el_total_aunque_el_lote_tenga_cien(monkeypatch):
    valido = {
        "id": 1,
        "date": "2026-08-19T12:00:00",
        "slug": "sesiono-la-comision-de-disciplina-10",
        "link": "https://consejo.test/1",
        "title": {"rendered": "Sesionó la Comisión de Disciplina"},
        "content": {"rendered": "<p>Sesión ordinaria.</p>"},
    }
    relleno = [{
        "id": n,
        "date": "2026-08-01T12:00:00",
        "slug": f"noticia-{n}",
        "link": f"https://consejo.test/{n}",
        "title": {"rendered": f"Noticia {n}"},
        "content": {"rendered": "<p>Sin sesión de comisión.</p>"},
    } for n in range(2, 101)]
    paginas_pedidas = []

    class Respuesta:
        status_code = 200
        headers = {"X-WP-TotalPages": "1"}

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            return None

    def get(_url, params=None, **_kwargs):
        paginas_pedidas.append((params["categories"], params["page"]))
        data = [valido, *relleno] if int(params["categories"]) == politica.CONSEJO_CATS["disciplina"] else []
        return Respuesta(data)

    monkeypatch.setattr(politica.requests, "get", get)
    inventario = politica._consejo_inventario_sesiones()
    assert len(inventario) == 1
    assert all(pagina == 1 for _, pagina in paginas_pedidas)


def test_inventario_cuenta_el_universo_y_deduplica(consejo_api_falsa):
    inventario = politica._consejo_inventario_sesiones()
    claves = [(e["fecha"], e["comision"]) for e in inventario]

    assert len(inventario) == 16
    assert len(claves) == len(set(claves))
    assert claves.count(("2025-08-13", "disciplina")) == 1, (
        "dos copias de una nota no pueden duplicar una reunión")


@pytest.mark.parametrize("fecha", ["2025-08-06", "2026-03-17", "2026-05-28"])
def test_las_sesiones_con_resultado_sustantivo_no_dependen_del_slug(
        consejo_api_falsa, fecha):
    inventario = politica._consejo_inventario_sesiones()
    evento = next(e for e in inventario if e["fecha"] == fecha)
    assert evento["comision"] == "acusacion"
    assert evento["tipo"] == "resultado_sustantivo"


def test_las_publicaciones_agrupadas_y_extraordinarias_cuentan(consejo_api_falsa):
    inventario = politica._consejo_inventario_sesiones()
    por_fecha = {e["fecha"]: e for e in inventario}
    assert por_fecha["2025-11-12"]["tipo"] == "publicacion_agrupada"
    assert por_fecha["2025-11-12"]["comision"] == "acusacion"
    assert por_fecha["2026-05-13"]["tipo"] == "extraordinaria"
    assert por_fecha["2026-05-13"]["comision"] == "disciplina"


def test_las_audiencias_y_el_jurado_no_cuentan(consejo_api_falsa):
    inventario = politica._consejo_inventario_sesiones()
    ids = {e["post_id"] for e in inventario}
    assert not {53570, 53850, 54431} & ids


def test_una_referencia_retrospectiva_no_se_clasifica_como_sesion_actual():
    post = {
        "slug": "la-comision-informo-sobre-una-causa",
        "title": {"rendered": "La Comisión de Acusación informó sobre una causa"},
        "content": {"rendered": (
            "La causa se había originado en una sesión de la Comisión de "
            "Acusación del mes pasado. Hoy se publicó la resolución.")},
    }
    assert politica._clasificar_sesion_consejo(post, "acusacion") is None


def test_la_serie_reconstruida_da_14_en_agosto_2026(consejo_api_falsa):
    inventario = politica._consejo_inventario_sesiones()
    serie = politica._paralisis_serie_desde_eventos(inventario, date(2026, 8, 26))
    assert serie["2026-08"] == 14


def test_la_ventana_movil_incluye_exactamente_doce_meses_calendario():
    eventos = [
        {"fecha": "2025-08-31"},
        {"fecha": "2025-09-01"},
        {"fecha": "2026-08-31"},
    ]
    serie = politica._paralisis_serie_desde_eventos(eventos, date(2026, 8, 31))
    assert serie["2026-08"] == 2


def test_la_card_expone_el_inventario_y_el_criterio(consejo_api_falsa):
    inventario = politica._consejo_inventario_sesiones()
    serie = politica._paralisis_serie_desde_eventos(inventario, date(2026, 8, 26))
    vigentes = [
        e for e in inventario if "2025-09-01" <= e["fecha"] < "2026-09-01"
    ]
    assert serie["2026-08"] == len(vigentes) == 14

    # La fecha real de ejecución puede avanzar; se prueban acá los campos que
    # hacen auditable el número sin congelar el mes corriente global.
    card = politica.fetch_paralisis_denuncias()
    assert card["sesiones_12m"]
    assert "fecha y comisión se deduplican" in card["criterio_conjuntas"]
    assert "audiencias no cuentan" in card["criterio_conjuntas"]


def test_el_inventario_versionado_cierra_con_la_serie_publicada():
    import json
    store = json.loads(
        (Path(__file__).parent.parent / "data" / "politica" /
         "denuncias_comisiones_universo.json").read_text(encoding="utf-8"))
    eventos = store["sesiones_2026_08"]
    claves = {(e["fecha"], e["comision"]) for e in eventos}

    assert len(eventos) == len(claves) == store["conteo_2026_08"]["total"] == 14
    assert store["conteo_2026_08"] == {
        "acusacion": 8, "disciplina": 6, "total": 14,
    }
    assert store["serie_12m"]["puntos"]["2026-08"] == 14
    for fecha in ("2026-03-17", "2026-05-28"):
        assert (fecha, "acusacion") in claves
