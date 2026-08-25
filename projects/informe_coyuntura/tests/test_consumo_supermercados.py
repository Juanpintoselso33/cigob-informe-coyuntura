"""El supermercado deja de validar el índice y pasa a integrarlo (ADR-0225).

Era el ancla de validación externa del cinturón. Mide condiciones materiales del
hogar, así que le corresponde ser componente y no juez: es la misma regla que
había desplazado al ICC.

Estos tests cuidan cinco cosas que pueden volver a romperse:

1. **No puede volver al panel.** Un indicador que compone el índice y a la vez
   lo valida vuelve circular la validación, y el camino de vuelta es de una
   línea en `panel_validacion.FAMILIA`.
2. **El colector revienta si falta la base.** Sin los tres meses del 4T-2023 el
   rebase mide contra otra cosa, y un índice rebaseado contra vaya a saber qué
   no se distingue a ojo de uno sano.
3. **Card y serie son el mismo número**, para que no haya dos caminos que
   puedan divergir.
4. **No lleva promedio móvil de 12 meses.** La fuente ya publica la serie
   desestacionalizada y volver a suavizarla la atrasaría medio año — el error
   que ADR-0155 documentó midiéndolo.
5. **El cinturón sigue sin ancla única**, que es la otra mitad de la decisión:
   si alguien vuelve a poner un par suelto de titular, el gráfico y la matriz
   cruzada dejan de decir lo que el texto afirma.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc                      # noqa: E402
import panel_validacion          # noqa: E402
import validacion_externa        # noqa: E402

# El colector se carga POR RUTA, igual que el de autos: `scripts/vida_cotidiana/`
# tiene su propio `config.py` y ponerlo al frente del path tapa al del proyecto.
_spec = importlib.util.spec_from_file_location(
    "indec_supermercados",
    ROOT / "scripts" / "vida_cotidiana" / "collectors" / "indec_supermercados.py")
_col = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_col)

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
VIDA = SNAPSHOT["cinturones"]["vida_cotidiana"]
IND = VIDA["indicadores"]["consumo_supermercados"]
CLAVE = "consumo_supermercados"


UNITS_REALES = "Índice base 2017=100"


def _respuesta(filas, units=UNITS_REALES):
    """Respuesta de la API con metadatos: la base la declara la fuente y el
    colector la lee de ahí (ADR-0243), así que sin `meta` no hay card."""
    meta = ([{"field": {"units": units}}] if units is not None else [])

    class R:
        def raise_for_status(self): pass
        def json(self): return {"data": filas, "meta": meta}
    return types.SimpleNamespace(get=lambda *a, **k: R())


# ── 1 · Componente sí, ancla no ─────────────────────────────────────────────
def test_es_componente_del_indice():
    comp = {i for d in itvc.DIMENSIONES_ITVC.values() for i in d["indicadores"]}
    assert CLAVE in comp, "dejó de ser componente del ITCIS"
    assert CLAVE in itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]


def test_no_puede_estar_en_el_panel_de_validacion():
    """El camino de vuelta es de una línea, y volvería circular la validación:
    el índice se estaría contrastando contra una parte de sí mismo."""
    assert CLAVE not in panel_validacion.FAMILIA
    assert CLAVE not in panel_validacion.ETIQUETAS
    assert CLAVE not in panel_validacion.FUENTES
    for claves in panel_validacion.FACTOR.values():
        assert CLAVE not in claves


def test_no_quedo_plumbing_de_ancla_en_validacion_externa():
    """Dos caminos de descarga para la misma serie es como el índice y su
    contraste terminan leyendo bases distintas sin que nada avise."""
    fuente = (ROOT / "scripts" / "validacion_externa.py").read_text(encoding="utf-8")
    assert "fetch_consumo_supermercados_mensual" not in fuente
    assert "consumo_supermercados_mensual" not in fuente
    assert "ITVC vs consumo" not in fuente


def test_puntua_y_no_es_card_de_contexto():
    """ADR-0216/0153: o integra el índice, o no es card."""
    assert IND.get("en_indice") is True
    assert IND.get("peso_efectivo", 0) > 0
    assert IND.get("dimension") == "ingresos"


# ── 2 · El colector revienta en vez de mentir ───────────────────────────────
def test_sin_los_meses_de_la_base_el_colector_levanta():
    _col.requests = _respuesta([["2024-01-01", 100.0], ["2024-02-01", 101.0]])
    with pytest.raises(ValueError, match="base 4T-2023"):
        _col.fetch_consumo_supermercados()


def test_una_respuesta_vacia_levanta():
    _col.requests = _respuesta([])
    with pytest.raises(ValueError, match="ningún punto"):
        _col.fetch_consumo_supermercados()


def test_con_la_base_completa_devuelve_el_ultimo_punto():
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2024-01-01", 91.5]])
    d = _col.fetch_consumo_supermercados()
    assert d["consumo_supermercados"] == {
        "valor": 91.5, "fecha": "2024-01", "anio_base": 2017,
        "unidad": "índice (2017 = 100, desestacionalizado)"}
    assert len(d["serie"]) == 4


def test_los_meses_de_la_base_son_los_del_cinturon():
    assert tuple(_col.BASE_MESES) == tuple(validacion_externa.BASE_MESES)


# ── 3 · Card y serie, un solo número ────────────────────────────────────────
def test_la_card_es_el_ultimo_punto_de_la_serie():
    serie = [p for p in SERIES.get(CLAVE, []) if p.get("valor") is not None]
    assert serie, "la serie no llegó al snapshot"
    ult = serie[-1]
    assert round(float(ult["valor"]), 1) == round(float(IND["valor"]), 1), (
        f"card {IND['valor']} contra último punto {ult['valor']}")
    assert ult["fecha"][:7] == IND["fecha_dato"][:7]


def test_la_serie_llega_a_la_base():
    meses = {p["fecha"][:7] for p in SERIES.get(CLAVE, [])}
    faltan = [m for m in validacion_externa.BASE_MESES if m not in meses]
    assert not faltan, f"sin base no hay rebase posible: faltan {faltan}"


# ── 4 · Sin promedio móvil, que la fuente ya desestacionalizó ───────────────
def test_no_entra_por_movil_12m():
    """Motos y autos sí; éste no. La ventana móvil existe para sacarle el
    calendario a un flujo crudo, y acá el INDEC ya lo sacó — volver a suavizar
    atrasa la serie medio año, que es el error medido en ADR-0155."""
    assert CLAVE not in validacion_externa.MOVIL12
    itvc_py = (ROOT / "scripts" / "itvc.py").read_text(encoding="utf-8")
    linea = next(l for l in itvc_py.splitlines() if f'idx["{CLAVE}"]' in l)
    assert "rebase_de_serie" in linea and "rebase_movil12" not in linea


def test_la_reconstruccion_lee_la_misma_serie_que_la_card():
    skey, invertido, anual, ya_rebaseada = validacion_externa.COMPONENTES[CLAVE]
    assert skey == CLAVE
    assert invertido is False, "más volumen comprado es mejor, no se invierte"
    assert anual is False and ya_rebaseada is False


# ── 5 · Los pesos: la regla, no los decimales ───────────────────────────────
def test_entra_con_20_por_ciento_y_los_previos_cedieron():
    ind = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    assert ind[CLAVE] == 0.20
    assert abs(sum(ind.values()) - 1.0) < 1e-9
    # los CUATRO previos, contra lo que tenían antes de esta alta. Eran cinco
    # cuando el alta se escribió; ADR-0224 fundió los dos vehículos en
    # `motorizacion_total` mientras la rama estaba abierta, y la cesión se
    # recalculó sola sobre lo que quedó — que es para lo que existe
    # `alta_proporcional`.
    previos = {"brecha_salario_cbt": 0.5959, "pobreza_nowcast": 0.3253,
               "consumo_carnes_total": 0.0392, "motorizacion_total": 0.0396}
    for k, v in previos.items():
        assert abs(ind[k] - round(v * 0.80, 4)) < 1e-9, f"{k} no cedió ×0,80"


def test_el_peso_nominal_de_la_dimension_no_se_toco():
    assert itvc.DIMENSIONES_ITVC["ingresos"]["peso"] == 0.2806


# ── 6 · El cinturón sigue sin ancla única ───────────────────────────────────
def test_la_validacion_no_titula_contra_una_serie_suelta():
    """La otra mitad de la decisión. Si alguien vuelve a poner un par suelto de
    titular, el gráfico dibuja el factor y el encabezado informa otra cosa."""
    val = VIDA["itvc"]["validacion"]
    assert "factor" in val["externa_label"].lower(), val["externa_label"]
    assert val["plot"] == "minmax", "el factor es un puntaje estandarizado, cruza el cero"
    for prohibido in ("supermercado", "consumo en supermercados"):
        assert prohibido not in val["externa_label"].lower()


def test_la_conclusion_explica_por_que_no_hay_ancla_unica():
    """El motivo es parte del resultado: si el texto sólo dijera «se usa un
    panel», el lector no tendría cómo saber que hay una referencia identificada
    y esperando muestra."""
    txt = VIDA["itvc"]["validacion"]["conclusion"].lower()
    assert "cuentas nacionales" in txt
    assert "trimestr" in txt


def test_la_matriz_cruzada_no_se_contrasta_contra_un_componente():
    """`validacion.pares` alimenta la matriz de ADR-0031. Dejarla apuntando al
    supermercado la habría vuelto circular sin que ningún test avisara."""
    fila = next(f for f in SNAPSHOT["validacion_cruzada"]["filas"]
                if f["indice"] == "ITCIS")
    assert fila["propio"] == "volumen_hogar"
    externas = dict(SNAPSHOT["validacion_cruzada"]["externas"])
    assert "supermercado" not in externas["volumen_hogar"].lower()


# ── 6 · La base y las revisiones (ADR-0243) ─────────────────────────────────
# La card rotulaba «índice (2004 = 100)». La Encuesta de Supermercados vigente
# usa base 2017=100 y la serie ni siquiera tiene puntos antes de enero de 2017:
# el rótulo no describía nada. Sobrevivió porque era un literal repetido en
# tres archivos y no había contra qué compararlo.

def test_la_base_sale_de_la_fuente_y_no_de_un_literal():
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2024-01-01", 91.5]])
    d = _col.fetch_consumo_supermercados()["consumo_supermercados"]
    assert d["anio_base"] == 2017
    assert "2017 = 100" in d["unidad"]


def test_la_base_erronea_no_puede_volver():
    """2004 no es una base plausible para una serie que empieza en 2017."""
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2024-01-01", 91.5]])
    d = _col.fetch_consumo_supermercados()["consumo_supermercados"]
    assert "2004" not in d["unidad"]


def test_si_la_fuente_cambia_de_base_el_rotulo_la_sigue():
    """El punto de leerla: que no haya que acordarse de actualizar el rótulo."""
    _col.requests = _respuesta(
        [["2023-10-01", 100.0], ["2023-11-01", 102.0],
         ["2023-12-01", 98.0], ["2024-01-01", 91.5]],
        units="Índice base año 2021=100")
    d = _col.fetch_consumo_supermercados()["consumo_supermercados"]
    assert d["anio_base"] == 2021
    assert "2021 = 100" in d["unidad"]


def test_sin_base_declarada_el_colector_levanta():
    """Antes que inventar un rótulo, fallar. El anterior no vino de ningún lado
    verificable y estuvo publicado igual."""
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0]], units="Índice")
    with pytest.raises(ValueError, match="base"):
        _col.fetch_consumo_supermercados()


def test_una_serie_anterior_a_su_propia_base_levanta():
    """Si la serie tuviera puntos de antes del año base, la base declarada no
    es la de esos puntos: hay dos bases empalmadas y el nivel no es comparable."""
    _col.requests = _respuesta([["2010-01-01", 70.0], ["2023-10-01", 100.0],
                                ["2023-11-01", 102.0], ["2023-12-01", 98.0]],
                               units="Índice base 2017=100")
    with pytest.raises(ValueError, match="base declarada"):
        _col.fetch_consumo_supermercados()


def test_una_revision_del_indec_reemplaza_el_valor_anterior():
    """El INDEC revisó mayo-2026 de 83,2 a 83,0 al publicar junio.

    El colector pide el histórico entero en cada corrida, así que la revisión
    entra sola. Lo que este test cuida es que nadie meta un cache o un
    `setdefault` que conserve la versión vieja: la serie desestacionalizada se
    recalcula cada mes, y guardar la primera lectura la congelaría."""
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2026-05-01", 83.222]])
    primera = _col.fetch_consumo_supermercados()
    assert primera["consumo_supermercados"]["valor"] == 83.2

    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2026-05-01", 83.0],
                                ["2026-06-01", 82.1]])
    segunda = _col.fetch_consumo_supermercados()
    assert segunda["serie"]["2026-05"] == 83.0, "quedó congelada la lectura vieja"
    assert segunda["consumo_supermercados"] == {
        "valor": 82.1, "fecha": "2026-06", "anio_base": 2017,
        "unidad": "índice (2017 = 100, desestacionalizado)"}


def test_el_ultimo_periodo_es_el_ultimo_publicado_no_el_penultimo():
    """Con junio disponible, la card tiene que ser junio."""
    _col.requests = _respuesta([["2023-10-01", 100.0], ["2023-11-01", 102.0],
                                ["2023-12-01", 98.0], ["2026-05-01", 83.0],
                                ["2026-06-01", 82.1]])
    d = _col.fetch_consumo_supermercados()["consumo_supermercados"]
    assert d["fecha"] == "2026-06" and d["valor"] == 82.1
