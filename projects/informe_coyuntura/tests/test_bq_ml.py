# -*- coding: utf-8 -*-
"""El detector de anomalías clasifica por FORMA, que es lo que lo hace usable.

Auditoría del 2026-08-12 sobre las 118 anomalías de la historia completa: 75
escalones, 12 picos, y las 12 de forma pico resultaron ser TODAS eventos reales
(la devaluación de dic-2023, la cuarentena, tres picos de protestas). Cero
errores de dato en toda la vida del proyecto.

De ahí la partición: un dígito mal leído es un PICO por construcción —al mes
siguiente la fuente se lee bien y la serie vuelve—, mientras que un cambio de
política es un ESCALÓN. Sin este corte, el 85% del volumen de la alerta es
historia conocida y la bandeja se vuelve ilegible.

Ningún test de acá toca BigQuery: `bq_ml` no importa `google.cloud` a nivel
módulo, justamente para que su lógica se pueda probar sin credenciales.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import bq_ml  # noqa: E402


def _f(previo, valor, siguiente):
    return {"previo": previo, "valor": valor, "siguiente": siguiente}


def test_pico_es_el_que_se_va_y_vuelve():
    """La firma de un error de lectura: un mes fuera de lugar y al siguiente la
    serie está donde estaba. Caso real: ipc_alimentos 7,7 → 15,7 → 29,7 → 20,4."""
    assert bq_ml.forma_de(_f(15.7, 29.7, 16.0)) == "pico"
    assert bq_ml.forma_de(_f(8.2, 5.0, 8.1)) == "pico"      # pluriempleo 2020-04


def test_escalon_es_el_que_salta_y_se_queda():
    """La firma de un cambio real. Caso real: concesiones_infraestructura
    llevaba 8,2 cuatro meses, saltó a 28,7 y se quedó en 28,7."""
    assert bq_ml.forma_de(_f(8.2, 28.7, 28.7)) == "escalon"
    assert bq_ml.forma_de(_f(64.1, 70.2, 70.0)) == "escalon"   # cobertura_judicial


def test_sin_vecinos_cuando_es_el_ultimo_punto():
    """El caso que MÁS hay que mirar: saltó y todavía no sabemos si vuelve.
    Por eso entra a la bandeja de revisar y no se descarta."""
    assert bq_ml.forma_de(_f(31192.0, 46161.0, None)) == "sin_vecinos"
    assert bq_ml.forma_de(_f(None, 46161.0, 50000.0)) == "sin_vecinos"


def test_plano_no_rompe():
    assert bq_ml.forma_de(_f(10.0, 10.0, 10.0)) == "plano"


def test_la_bandeja_de_revisar_deja_afuera_los_eventos():
    """El contrato: reciente + forma de error entra; reciente + escalón no.
    Es lo que baja el volumen de 5 a 1 en la corrida real."""
    hoy = date.today()
    reciente = (hoy - timedelta(days=20)).isoformat()
    viejo = (hoy - timedelta(days=400)).isoformat()
    salidas = bq_ml._posproceso_anomalias({"filas": [
        {"indicador": "error_de_lectura", "fecha": reciente, **_f(10.0, 99.0, 10.2)},
        {"indicador": "cambio_real", "fecha": reciente, **_f(8.2, 28.7, 28.7)},
        {"indicador": "recien_saltado", "fecha": reciente, **_f(10.0, 99.0, None)},
        {"indicador": "historia", "fecha": viejo, **_f(10.0, 99.0, 10.1)},
    ]})
    assert [f["indicador"] for f in salidas["revisar"]] == ["error_de_lectura",
                                                            "recien_saltado"]
    assert [f["indicador"] for f in salidas["recientes_otras_formas"]] == ["cambio_real"]
    assert [f["indicador"] for f in salidas["historicas"]] == ["historia"]
    assert "filas" not in salidas


def test_datetime_no_rompe_la_comparacion_de_fechas():
    """ML.DETECT_ANOMALIES devuelve la columna de tiempo como datetime aunque el
    modelo entrene sobre DATE, y datetime hereda de date: preguntar por el padre
    primero rompía la comparación."""
    from datetime import datetime
    salidas = bq_ml._posproceso_anomalias({"filas": [
        {"indicador": "x", "fecha": datetime.now(), **_f(10.0, 99.0, 10.1)}]})
    assert len(salidas["revisar"]) == 1


def test_el_nowcast_no_volvio():
    """Se descartó midiendo (perdía contra repetir el mes anterior). Si alguien
    lo reintroduce, que sea con una medición nueva y no de memoria."""
    assert "nowcast" not in bq_ml.TAREAS
    assert set(bq_ml.TAREAS) == {"anomalias", "forecast"}
