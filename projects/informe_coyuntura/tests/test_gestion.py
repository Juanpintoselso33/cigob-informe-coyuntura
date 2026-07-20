"""Colector de gestión: estados de las fuentes licitatorias."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── Estados de CONTRAT.AR: preadjudicado NO es adjudicado (ADR-0087) ────────

def test_preadjudicado_no_cuenta_como_adjudicado():
    """`"ADJUDICADO" in "PREADJUDICADO"` es True, y por eso la etapa II-B de la
    Red Federal de Concesiones —2.557 km, 28,1 puntos porcentuales del
    indicador— se contó como adjudicada estando sólo preadjudicada.

    Los strings de abajo son los que CONTRAT.AR devolvía el 19-jul-2026.
    """
    import gestion
    assert gestion._esta_adjudicado("Adjudicado")
    assert gestion._esta_adjudicado("ADJUDICADO")
    assert gestion._esta_adjudicado("Adjudicado Parcial")
    assert not gestion._esta_adjudicado("Preadjudicado")
    assert not gestion._esta_adjudicado("Pendiente Acto Administrativo de Preselección")
    assert not gestion._esta_adjudicado("Desierto")
    assert not gestion._esta_adjudicado("")
    assert not gestion._esta_adjudicado(None)


def test_el_store_de_concesiones_no_reintrodujo_la_etapa_preadjudicada():
    """Si II-B vuelve al store, tiene que ser porque CONTRAT.AR la muestra
    adjudicada — no porque el bug de substring haya vuelto."""
    import json
    from pathlib import Path
    store = json.loads((Path(__file__).resolve().parents[1] / "data" / "gestion" /
                        "concesiones_fechas.json").read_text(encoding="utf-8-sig"))
    assert "II-B" not in store["etapas"], (
        "II-B volvió al store: verificar en CONTRAT.AR que esté ADJUDICADO y no "
        "PREADJUDICADO antes de aceptar el cambio (ADR-0087)")
