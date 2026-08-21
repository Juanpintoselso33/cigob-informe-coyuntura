# -*- coding: utf-8 -*-
"""G7: las anclas de la validación externa siguen vivas (ADR-0176).

Una serie que es sólo insumo de validación no tiene card, así que G2 y G3/G3b
no la miran. El ICG de la UTDT se congeló y siguió entrando al factor común con
su última observación vieja durante meses, publicando correlaciones como si
nada. Estos tests fijan que eso ahora se ve.
"""
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATE = RAIZ / "scripts" / "gate_calidad.py"
sys.path.insert(0, str(RAIZ / "scripts"))

import panel_validacion as pnl


def _mes(dias_atras: int) -> str:
    d = date.today() - timedelta(days=dias_atras)
    return f"{d.year}-{d.month:02d}"


def _snapshot(tmp_path):
    """Snapshot mínimo y sano: G7 tiene que ser lo único que pueda fallar."""
    hoy = date.today().isoformat()
    informe = {
        "schema_version": 1, "generated_at": hoy + "T00:00:00", "period": hoy[:7],
        "score_global": 5.0,
        "cinturones": {"macro": {"score": 5.0, "indicadores": {
            "ind": {"valor": 1.0, "fecha_dato": hoy, "fuente": "f",
                    "unidad": "u", "desactualizado": False}}}},
    }
    (tmp_path / "informe.json").write_text(json.dumps(informe), encoding="utf-8")
    (tmp_path / "series.json").write_text(
        json.dumps({"ind": [{"fecha": hoy, "valor": 1.0}]}), encoding="utf-8")
    return tmp_path


def _validacion(tmp_path, anclas, nombre="ve.json"):
    p = tmp_path / nombre
    cuerpo = {} if anclas is None else {"panel_anclas": anclas}
    p.write_text(json.dumps(cuerpo), encoding="utf-8")
    return p


def _correr(snap, val=None):
    cmd = [sys.executable, str(GATE), "--snapshot", str(snap)]
    if val is not None:
        cmd += ["--validacion", str(val)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(RAIZ))
    return r.returncode, r.stdout + r.stderr


def _todas_frescas(dias=10):
    hoy = date.today().isoformat()
    return {n: {"ultimo": _mes(dias), "n": 40, "avanzo": hoy} for n in pnl.FAMILIA}


def test_anclas_frescas_pasan(tmp_path):
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, _todas_frescas()))
    assert "G7" not in salida, salida
    assert cod == 0, salida


def test_un_ancla_sin_datos_bloquea(tmp_path):
    """El factor común se calcularía sobre menos series que las declaradas."""
    anclas = _todas_frescas()
    anclas["icg_utdt"] = None
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, anclas))
    assert "[FALLA] G7 icg_utdt" in salida, salida
    assert "SIN datos" in salida
    assert cod != 0, "un ancla ausente tiene que bloquear la publicación"


def test_un_ancla_congelada_avisa_pero_no_bloquea(tmp_path):
    """Es una fuente demorada (ADR-0133), pero queda NOMBRADA en cada corrida:
    exactamente lo que le faltó al ICG durante meses."""
    anclas = _todas_frescas()
    anclas["icg_utdt"] = {"ultimo": _mes(400), "n": 296}
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, anclas))
    assert "G7-frescura icg_utdt" in salida, salida
    assert "se congeló" in salida
    assert "[FALLA]" not in salida, "una fuente demorada no debe bloquear:\n" + salida
    assert cod == 0, salida


def test_sin_registro_de_anclas_bloquea(tmp_path):
    """Si validacion_externa.py deja de escribir panel_anclas, el gate se queda
    ciego. Esa ceguera no puede degradarse a aviso."""
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, None))
    assert "[FALLA] G7" in salida, salida
    assert "panel_anclas" in salida
    assert cod != 0


def test_toda_ancla_declarada_se_verifica(tmp_path):
    """El registro de G7 se lee de panel_validacion.FAMILIA: si mañana se agrega
    un ancla nueva, entra sola al gate sin tocar gate_calidad.py."""
    anclas = _todas_frescas()
    faltante = sorted(pnl.FAMILIA)[0]
    del anclas[faltante]
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, anclas))
    assert f"G7 {faltante}" in salida, salida
    assert cod != 0


# ── Congelamiento detectado por "hace cuánto no avanza" (ADR-0178) ───────────

def test_un_ancla_que_dejo_de_avanzar_se_ve_aunque_el_rezago_pase(tmp_path):
    """El caso que el rezago absoluto NO agarra: una fuente con atraso
    estructural grande (consumo mayorista INDEC, tope 190d) que se clava. Su rezago sigue
    por debajo del tope durante meses; lo que la delata es que hace 200 días que
    no publica un período nuevo."""
    anclas = _todas_frescas()
    anclas["consumo_mayoristas"] = {
        "ultimo": _mes(120), "n": 113,
        "avanzo": (date.today() - timedelta(days=200)).isoformat(),
    }
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, anclas))
    assert "no publica un período nuevo" in salida, salida
    assert "consumo_mayoristas" in salida
    assert "[FALLA]" not in salida, "es una demora, no puede bloquear:\n" + salida
    assert cod == 0


def test_una_fuente_con_atraso_estructural_pero_que_avanza_no_molesta():
    """El contrapunto: 120 días de rezago son normales en el consumo mayorista INDEC
    mientras siga publicando todos los meses."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        anclas = _todas_frescas()
        anclas["consumo_mayoristas"] = {
            "ultimo": _mes(120), "n": 113,
            "avanzo": (date.today() - timedelta(days=20)).isoformat(),
        }
        cod, salida = _correr(_snapshot(tmp), _validacion(tmp, anclas))
        assert "G7" not in salida, salida
        assert cod == 0


def test_un_registro_sin_avanzo_no_inventa_una_falla(tmp_path):
    """Corridas anteriores a ADR-0178 no traen el campo: se saltea."""
    anclas = {n: {"ultimo": _mes(10), "n": 40} for n in pnl.FAMILIA}
    cod, salida = _correr(_snapshot(tmp_path), _validacion(tmp_path, anclas))
    assert "no publica un período nuevo" not in salida, salida
    assert cod == 0
