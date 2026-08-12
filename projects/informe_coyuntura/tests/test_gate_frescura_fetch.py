# -*- coding: utf-8 -*-
"""G2b mide hace cuánto que la fuente no contesta (ADR-0191).

G2 mide el rezago del DATO (`fecha_dato`) y eso deja un agujero: en una serie
anual la fecha no se mueve aunque el fetch ande perfecto, así que su tope tiene
que ser generoso, y esa misma holgura tapa que la fuente lleve meses caída.
`judicializacion` estuvo 12 días publicándose desde cache sin que nada fallara.

G2b mira `obtenido_en`, que el colector sella SÓLO cuando la fuente contestó y
el carry-forward arrastra sin tocar.
"""
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATE = RAIZ / "scripts" / "gate_calidad.py"
sys.path.insert(0, str(RAIZ / "scripts"))


def _snapshot(tmp_path, *, obtenido_en, indicador="indicador_prueba"):
    """Snapshot mínimo y sano salvo por el sello del fetch.

    `fecha_dato` es de hoy a propósito: así lo único que puede disparar una
    falla es G2b, y el test no puede pasar por el motivo equivocado.
    """
    hoy = date.today().isoformat()
    ind = {
        "valor": 5.6,
        "fecha_dato": hoy,
        "fuente": "fuente de prueba",
        "unidad": "u",
        "desactualizado": True,
    }
    if obtenido_en is not None:
        ind["obtenido_en"] = obtenido_en
    informe = {
        "schema_version": 1,
        "generated_at": hoy + "T00:00:00",
        "period": hoy[:7],
        "score_global": 5.0,
        "cinturones": {
            "espiritu_epoca": {"score": 5.0, "indicadores": {indicador: ind}},
        },
    }
    (tmp_path / "informe.json").write_text(json.dumps(informe), encoding="utf-8")
    (tmp_path / "series.json").write_text(json.dumps({}), encoding="utf-8")
    return tmp_path


def _correr_gate(directorio):
    r = subprocess.run(
        [sys.executable, str(GATE), "--snapshot", str(directorio)],
        capture_output=True, text=True, cwd=str(RAIZ),
    )
    return r, r.stdout + r.stderr


def _hace(dias):
    return (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")


def test_una_fuente_que_no_contesta_hace_meses_corta_la_publicacion():
    """El caso que motivó el gate: la card se publica, la fuente no contesta."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r, salida = _correr_gate(_snapshot(Path(d), obtenido_en=_hace(60)))
        assert "[FALLA] G2b" in salida, (
            "una fuente 60 días sin contestar no disparó G2b:\n" + salida)
        assert "sin un fetch exitoso" in salida
        assert r.returncode != 0


def test_un_fetch_reciente_no_molesta():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(_snapshot(Path(d), obtenido_en=_hace(1)))
        assert "G2b" not in salida, salida


def test_sin_sello_el_chequeo_se_saltea():
    """Manuales y derivados de series no tienen fetch propio que medir.

    Es también lo que permite desplegar esto sin una ola de falsos positivos:
    el campo aparece la primera vez que cada indicador se obtiene bien.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(_snapshot(Path(d), obtenido_en=None))
        assert "G2b" not in salida, salida


def test_el_tope_por_indicador_manda_sobre_el_default():
    """judicializacion tiene 45 días declarados: a los 40 todavía no falla."""
    import tempfile
    from gate_calidad import G2B_MAX_DIAS, G2B_MAX_DIAS_DEFAULT
    assert G2B_MAX_DIAS["judicializacion"] > G2B_MAX_DIAS_DEFAULT, (
        "el override existe justamente porque el default es más estricto")
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(
            _snapshot(Path(d), obtenido_en=_hace(40), indicador="judicializacion"))
        assert "G2b" not in salida, (
            "el tope propio de judicializacion no se respetó:\n" + salida)
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(
            _snapshot(Path(d), obtenido_en=_hace(50), indicador="judicializacion"))
        assert "[FALLA] G2b" in salida, (
            "ni siquiera pasado su propio tope falló:\n" + salida)


def test_un_sello_ilegible_es_falla_y_no_un_saltea():
    """Un sello roto no puede degradar a 'sin sello' — sería el agujero de vuelta."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r, salida = _correr_gate(_snapshot(Path(d), obtenido_en="ayer a la tarde"))
        assert "[FALLA] G2b" in salida, salida
        assert "no parseable" in salida
        assert r.returncode != 0
