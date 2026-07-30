"""Los datos leídos de PÍXELES pasan sus controles cruzados, en cada corrida.

Sin esto, un dígito mal transcripto no lo detecta nada: gate_calidad.py verifica
estructura, frescura y card-vs-serie, y los tests de reconciliación verifican
invariantes de conteo. Un 23.803 escrito como 23.303 pasa todos.

El caso de acá es el tablero de la CSJN, cuyo dato sólo existe como imagen. La
identidad contable la enuncia la propia fuente por separado —publica ingresos,
resueltos y saldo como tres series— así que cerrarla es un control genuino y no
una tautología de cómo se cargó el store.

Corre SIN red: sobre el store versionado.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import lectura_pixeles as lp

STORE = ROOT / "data" / "politica" / "csjn_resueltos_pixeles.json"
CRUDO = json.loads(STORE.read_text(encoding="utf-8-sig"))
DATOS = {k: v for k, v in CRUDO.items() if not k.startswith("_")}


def _lectura() -> lp.Lectura:
    m = CRUDO["_meta"]
    return lp.Lectura(
        fuente=m["fuente"], leido_por=m["leido_por"], fecha_lectura=m["fecha_lectura"],
        datos=DATOS,
        controles=[
            lp.identidad_contable("ingresos", "resueltos", "saldo"),
            lp.sin_huecos("ingresos", 2014, 2024),
            lp.sin_huecos("resueltos", 2014, 2024),
            lp.sin_huecos("saldo", 2014, 2024),
            # cotas de sanidad: un dígito de más se sale del fenómeno
            lp.rango_plausible("ingresos", 5_000, 100_000),
            lp.rango_plausible("resueltos", 5_000, 100_000),
        ])


def test_la_lectura_pasa_todos_sus_controles():
    resultados = _lectura().verificar()
    fallidos = [r for r in resultados if r["estado"] == "FALLA"]
    assert not fallidos, fallidos
    assert len(resultados) == 6


def test_la_identidad_contable_cierra_los_once_anios():
    """El control fuerte, explícito: la fuente publica las tres series por
    separado, así que el cierre no es una tautología del store."""
    for anio in map(str, range(2014, 2025)):
        assert DATOS["saldo"][anio] == DATOS["ingresos"][anio] - DATOS["resueltos"][anio], anio


def test_un_digito_mal_leido_es_detectado():
    """Falsificación: si el control no atrapara esto, no serviría de nada."""
    roto = {k: dict(v) for k, v in DATOS.items()}
    roto["resueltos"]["2014"] = 23_303          # 23.803 con un dígito cambiado
    mala = lp.Lectura(fuente="test", leido_por="test", fecha_lectura="2026-07-29",
                      datos=roto,
                      controles=[lp.identidad_contable("ingresos", "resueltos", "saldo")])
    with pytest.raises(lp.ControlFallido) as e:
        mala.verificar()
    assert "2014" in str(e.value)


def test_una_fila_salteada_es_detectada():
    """El otro error de transcripción frecuente, y más fácil de cometer."""
    roto = {k: dict(v) for k, v in DATOS.items()}
    del roto["ingresos"]["2019"]
    mala = lp.Lectura(fuente="test", leido_por="test", fecha_lectura="2026-07-29",
                      datos=roto, controles=[lp.sin_huecos("ingresos", 2014, 2024)])
    with pytest.raises(lp.ControlFallido) as e:
        mala.verificar()
    assert "2019" in str(e.value)


def test_un_control_que_no_aplica_no_se_confunde_con_uno_que_falla():
    """Distinción que importa: al leer la tabla de la OPC, sumar los renglones de
    impuestos da 70% de más porque «Otros impuestos» ya es un agregado. Eso no es
    una lectura mala, es un control que no corresponde — y tratarlo como falla
    llevaría a descartar un dato bueno."""
    l = lp.Lectura(fuente="test", leido_por="test", fecha_lectura="2026-07-29",
                   datos=DATOS,
                   controles=[lp.Control("suma de renglones", lambda d: (False, "no debería correr"),
                                         aplica=False,
                                         motivo_no_aplica="«Otros impuestos» ya es un agregado")])
    res = l.verificar()          # no levanta
    assert res[0]["estado"] == "no_aplica"


def test_el_store_declara_su_procedencia():
    """Un número de píxeles sin procedencia no es auditable."""
    m = CRUDO["_meta"]
    for campo in ("fuente", "leido_por", "fecha_lectura", "controles"):
        assert m.get(campo), f"falta {campo} en _meta"
    assert m["fuente"].startswith("http")


def test_la_tasa_de_resolucion_reproduce_lo_que_publico_el_adr():
    """ADR-0139 usó esta lectura para reabrir velocidad_de_resolucion: de 141,8%
    en 2014 a 41,7% en 2024. Si el store cambia, el ADR queda mintiendo."""
    tasa = lambda a: 100 * DATOS["resueltos"][a] / DATOS["ingresos"][a]
    assert round(tasa("2014"), 1) == 141.8
    assert round(tasa("2024"), 1) == 41.7
