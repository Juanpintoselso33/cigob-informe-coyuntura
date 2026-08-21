"""La contracara del cierre de PyMEs (ADR-0219).

Mide qué proporción del empleo registrado son autónomos y monotributistas. Sin
esto el informe publica que hay 30.707 empleadores PyME menos y no puede decir
si esas unidades productivas desaparecieron o se reconfiguraron.

Lo que estos tests cuidan es la trampa que casi lo arruina: el **monotributo
social** cae 394 mil personas en un solo mes (dic-2024) por un cambio de
régimen, no por la economía. Con esa serie adentro la participación baja
(22,91% → 22,05%); sin ella, sube (19,12% → 20,60%). Las dos lecturas son
opuestas, y con el signo invertido la primera habría publicado una reforma
administrativa COMO UNA MEJORA DEL EMPLEO.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "trabajo_independiente",
    ROOT / "scripts" / "vida_cotidiana" / "collectors" / "trabajo_independiente.py")
_ti = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ti)

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
ITVC_PY = (ROOT / "scripts" / "itvc.py").read_text(encoding="utf-8")
IND = SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]["trabajo_independiente"]


def test_el_monotributo_social_no_entra():
    """Su id NO puede estar entre las series que se suman, y tiene que seguir
    NOMBRADO en el módulo: una exclusión sin motivo escrito se deshace sola la
    próxima vez que alguien mire la lista y note que falta un régimen."""
    ids = set(_ti.INDEPENDIENTES.values())
    assert "151.1_IPENDIETAC_2012_M_43" not in ids, (
        "volvió a entrar el monotributo social: el indicador pasa a medir una "
        "reforma regulatoria y con el signo invertido la lee como mejora")
    assert _ti.EXCLUIDA[1] == "151.1_IPENDIETAC_2012_M_43"
    assert _ti.EXCLUIDA[2] == "2024-12", "se perdió el mes del quiebre"


def test_los_asalariados_son_los_tres_sectores():
    """El denominador es el empleo registrado TOTAL: alguien que pasa a
    monotributo puede venir del privado, del público o de casas particulares."""
    assert set(_ti.ASALARIADOS) == {"privado", "publico", "casas"}


def test_puntua_invertido():
    """Más peso independiente es peor: se pierden aportes patronales,
    indemnización y estabilidad. La lectura contraria es defendible y está
    declarada en el ADR; si se cambia, se cambia acá y se recalcula."""
    linea = next(l for l in ITVC_PY.splitlines()
                 if 'idx["trabajo_independiente"]' in l)
    bloque = ITVC_PY[ITVC_PY.index(linea):ITVC_PY.index(linea) + 260]
    assert "invertido=True" in bloque, linea


def test_card_y_serie_son_el_mismo_numero():
    serie = SERIES.get("trabajo_independiente") or []
    assert serie, "sin serie publicada"
    assert abs(serie[-1]["valor"] - IND["valor"]) < 0.01, (
        f"card {IND['valor']} ≠ serie {serie[-1]['valor']}")
    assert IND.get("unidad") == "% del empleo registrado"


def test_la_serie_llega_al_4t_2023_y_no_tiene_saltos():
    """Un salto grande en la participación es la firma de un cambio de régimen
    colándose, que es exactamente lo que pasó con el monotributo social."""
    serie = [p for p in SERIES["trabajo_independiente"] if p["fecha"] >= "2023-01-01"]
    assert serie[0]["fecha"][:7] <= "2023-10", "no cubre la base del índice"
    saltos = [abs(b["valor"] - a["valor"]) for a, b in zip(serie, serie[1:])]
    assert max(saltos) < 1.0, (
        f"salto de {max(saltos):.2f} pp en un mes: revisá si entró un cambio "
        f"de régimen a la serie")
