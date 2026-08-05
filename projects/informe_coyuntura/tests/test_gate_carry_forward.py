# -*- coding: utf-8 -*-
"""G3 verifica cards FRESCAS (ADR-0174).

Una card en carry-forward es por definición un valor de otro momento: si la
serie se movió, tienen que diferir. Eso es el carry-forward funcionando, no una
desincronización, y no puede cortar la publicación de los cinco cinturones.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATE = RAIZ / "scripts" / "gate_calidad.py"


def _snapshot(tmp_path, desactualizado: bool):
    """Snapshot mínimo con UN indicador cuya card no coincide con su serie."""
    hoy = __import__("datetime").date.today().isoformat()
    informe = {
        "schema_version": 1,
        "generated_at": hoy + "T00:00:00",
        "period": hoy[:7],
        "score_global": 5.0,
        "cinturones": {
            "espiritu_epoca": {
                "score": 5.0,
                "indicadores": {
                    "indicador_prueba": {
                        "valor": 5.6,
                        "fecha_dato": hoy,
                        "fuente": "fuente de prueba",
                        "unidad": "u",
                        "desactualizado": desactualizado,
                    }
                },
            }
        },
    }
    series = {"indicador_prueba": [{"fecha": hoy, "valor": 7.0}]}
    (tmp_path / "informe.json").write_text(json.dumps(informe), encoding="utf-8")
    (tmp_path / "series.json").write_text(json.dumps(series), encoding="utf-8")
    return tmp_path


def _correr_gate(directorio):
    return subprocess.run(
        [sys.executable, str(GATE), "--snapshot", str(directorio)],
        capture_output=True, text=True, cwd=str(RAIZ),
    )


def test_una_card_en_carry_forward_no_bloquea_por_g3(tmp_path):
    """5,6 contra 7,0 con la card desactualizada: avisa, no falla."""
    r = _correr_gate(_snapshot(tmp_path, desactualizado=True))
    salida = r.stdout + r.stderr
    assert "carry-forward" in salida, salida
    assert "[FALLA] G3" not in salida, (
        "una card en carry-forward volvió a bloquear la publicación:\n" + salida)


def test_una_card_fresca_que_no_coincide_si_bloquea(tmp_path):
    """El invariante sigue vivo donde importa: card que dice ser fresca."""
    r = _correr_gate(_snapshot(tmp_path, desactualizado=False))
    salida = r.stdout + r.stderr
    assert "[FALLA] G3" in salida, (
        "G3 dejó pasar una card fresca desincronizada de su serie:\n" + salida)
    assert r.returncode != 0
