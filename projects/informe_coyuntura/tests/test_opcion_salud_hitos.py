"""ADR-0371: la libre elección en salud se mide por hitos fechados."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import gestion  # noqa: E402

HITOS = json.loads(gestion.OPCION_SALUD_HITOS_PATH.read_text(encoding="utf-8"))


def test_los_pesos_suman_uno_y_cada_hito_tiene_fuente():
    assert round(sum(h["peso"] for h in HITOS["hitos"]), 6) == 1.0
    assert all(h.get("fuente") for h in HITOS["hitos"])


def test_la_escalera_cae_en_las_fechas_de_las_normas():
    pct = {"2024-11": 0.3, "2024-12": 0.7, "2025-01": 24.5}
    def av(f):
        return gestion.salud_indice(HITOS, f, {k: v for k, v in pct.items() if k <= f[:7]})[0]
    assert av("2023-11-30") == 0.0
    assert av("2023-12-31") == 25.0     # DNU 70/2023, rige el 29-dic
    assert av("2024-03-31") == 45.0     # Decreto 170/2024, 1-mar
    assert av("2024-12-31") == 85.0     # derivación directa y trámite, dic-2024
    assert av("2025-01-31") == 100.0    # funcionamiento verificado en el padrón


def test_un_hito_cumplido_no_se_pierde():
    """Codex, 26-oct-2026: si el % cae bajo el umbral, el funcionamiento ya
    fechado sigue contando (tarjeta y serie dan lo mismo)."""
    assert gestion.salud_indice(HITOS, "2026-09-30", {"2026-09": 5.0})[0] == 100.0
