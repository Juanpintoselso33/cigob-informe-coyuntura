"""Tests del empleo registrado en el ITVC (ADR-0130)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itvc

RAIZ = Path(__file__).parent.parent


def _dim():
    return itvc.DIMENSIONES_ITVC["empleo"]["indicadores"]


def test_la_dimension_empleo_mide_empleo():
    """El motivo del ADR: la dimensión se llamaba así y ninguno de sus cuatro
    componentes contaba puestos de trabajo."""
    assert "empleo_registrado" in _dim()


def test_sigue_pesando_mas_que_los_proxies():
    """Lo que ADR-0130 puso a cuidar es que la medida DIRECTA de empleo pese
    más que los tres proxies de entorno (IPI, cemento, subocupación). Eso sigue
    en pie. Lo que cambió es que ya no es el componente más pesado de la
    dimensión: ADR-0214 mudó `informalidad` acá con su peso efectivo intacto
    (9,19% del índice contra 6,04%), y quedó primera. No es una degradación del
    registrado — es que la dimensión pasó a tener DOS medidas directas de
    empleo, una de volumen y otra de calidad, que es lo que ADR-0033 pedía."""
    ind = _dim()
    assert ind["empleo_registrado"] == 0.2246   # ADR-0219: cedió ×0,90
    for proxy in ("mortalidad_pymes", "despacho_cemento", "pluriempleo"):
        assert ind["empleo_registrado"] > ind[proxy], f"{proxy} lo pasó"
    assert max(ind, key=ind.get) == "informalidad", "ADR-0214 la puso primera"


def test_los_pesos_suman_uno():
    assert abs(sum(_dim().values()) - 1.0) < 1e-9


def test_los_proxies_conservan_su_orden_relativo():
    """ADR-0130 los hace ceder PROPORCIONALMENTE (×0,65) y ADR-0154 los hace
    ABSORBER proporcionalmente (÷0,87) al salir el índice líder. Las dos
    operaciones preservan el orden; reordenarlos es otra decisión y necesita su
    propio ADR."""
    ind = _dim()
    assert "indice_lider" not in ind, "ADR-0154 lo sacó del cinturón"
    valores = [ind[k] for k in ("mortalidad_pymes", "despacho_cemento",
                                "pluriempleo")]
    assert valores == sorted(valores, reverse=True), ind


def test_el_peso_nominal_sube_solo_por_lo_que_entro():
    """ADR-0130 no tocó el nominal (0,15). ADR-0214 lo sube a 0,2419, y el
    delta tiene que ser EXACTAMENTE el peso efectivo que traía `informalidad`
    (0,3725 × 0,2467 = 0,0919). Si difiere, alguien recalibró de contrabando."""
    peso = itvc.DIMENSIONES_ITVC["empleo"]["peso"]
    assert abs(peso - (0.15 + 0.3725 * 0.2467)) < 5e-5, peso


def test_no_se_invierte():
    """Más empleo es MEJOR. Si alguien lo invierte, el ITVC leería la
    destrucción de empleo como una mejora."""
    # La línea vivía en publicar.py hasta ADR-0208, que mudó la construcción
    # de los índices a itvc.py para que generar_informe.py también la use.
    fuente = (RAIZ / "scripts" / "itvc.py").read_text(encoding="utf-8")
    linea = next(l for l in fuente.splitlines() if 'idx["empleo_registrado"]' in l)
    assert "invertido" not in linea, linea


def test_el_colector_lo_emite():
    """LA TRAMPA DE ADR-0130: el colector tiene una whitelist por sección.
    Agregarlo a INDEC_SERIES no alcanza — sin la clave en el bucle, la card
    sale sin valor y el gate falla con G1, lejos de la causa."""
    cfg = (RAIZ / "scripts" / "vida_cotidiana" / "config.py").read_text(encoding="utf-8")
    col = (RAIZ / "scripts" / "vida_cotidiana" / "collectors"
           / "indec_series.py").read_text(encoding="utf-8")
    assert '"empleo_registrado":' in cfg, "falta en INDEC_SERIES"
    assert '"empleo_registrado"' in col, "falta en la whitelist del colector"


def test_la_serie_esta_registrada_para_descarga():
    ds = (RAIZ / "scripts" / "descargar_series.py").read_text(encoding="utf-8")
    assert '"empleo_registrado"' in ds
    assert "151.1_AARIADODAD_2012_M_31" in ds


def test_entra_a_la_reconstruccion_del_itvc():
    """Si no está en COMPONENTES, la validación externa reconstruye un ITVC que
    no es el que se publica."""
    import validacion_externa as ve
    assert "empleo_registrado" in ve.COMPONENTES
    _skey, invertido, anual, _ya = ve.COMPONENTES["empleo_registrado"]
    assert invertido is False and anual is False
