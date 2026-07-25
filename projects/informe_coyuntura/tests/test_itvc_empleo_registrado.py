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


def test_es_el_componente_principal():
    ind = _dim()
    assert ind["empleo_registrado"] == max(ind.values()) == 0.35


def test_los_pesos_suman_uno():
    assert abs(sum(_dim().values()) - 1.0) < 1e-9


def test_los_proxies_conservan_su_orden_relativo():
    """ADR-0130 los hace ceder PROPORCIONALMENTE (×0,65). Reordenarlos es otra
    decisión y necesita su propio ADR."""
    ind = _dim()
    valores = [ind[k] for k in ("mortalidad_pymes", "despacho_cemento",
                                "indice_lider", "pluriempleo")]
    assert valores == sorted(valores, reverse=True), ind


def test_el_peso_nominal_de_la_dimension_no_se_toco():
    assert itvc.DIMENSIONES_ITVC["empleo"]["peso"] == 0.15


def test_no_se_invierte():
    """Más empleo es MEJOR. Si alguien lo invierte, el ITVC leería la
    destrucción de empleo como una mejora."""
    fuente = (RAIZ / "scripts" / "publicar.py").read_text(encoding="utf-8")
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
