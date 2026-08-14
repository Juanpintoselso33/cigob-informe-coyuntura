# -*- coding: utf-8 -*-
"""Las salidas que el pipeline regenera cada noche tienen que commitearse
(ADR-0177).

`output/validacion_externa.json` estaba trackeado pero NO en la lista de
`git add` del workflow: el pipeline lo recalculaba cada noche, publicar.py le
sacaba las correlaciones para el snapshot y después lo descartaba. La copia
versionada quedó cinco días atrás, y con ella la matriz de redundancia, que
hacía fallar un test que durante todo ese tiempo se leyó como "staleness que
resuelve la próxima corrida". No la resolvía nunca.

Estos tests miran la evidencia, no la intención: si la salida versionada es
mucho más vieja que el snapshot publicado, es que nadie la está commiteando.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
WORKFLOW = RAIZ.parents[1] / ".github" / "workflows" / "data-pipeline.yml"
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"

# Salidas que un script del pipeline nocturno reescribe en CADA corrida, con la
# ruta del sello de tiempo que llevan adentro. Las de análisis manual
# (out_of_sample, revision_bandas, interpolacion_sombra, procedencia_anclas) NO
# van acá: nadie las regenera de noche y su antigüedad es legítima.
REGENERADAS = {
    "output/informe.json": ("generated_at",),
    "output/validacion_externa.json": ("_meta", "generated_at"),
}
TOLERANCIA_DIAS = 3     # margen para fines de semana con el cron caído


def _fecha(ruta, camino):
    d = json.loads((RAIZ / ruta).read_text(encoding="utf-8"))
    for k in camino:
        d = (d or {}).get(k)
        if d is None:
            return None
    return datetime.fromisoformat(str(d).replace("Z", ""))


@pytest.mark.parametrize("ruta", sorted(REGENERADAS))
def test_la_salida_regenerada_esta_en_el_git_add_del_workflow(ruta):
    """Sin esto el pipeline la recalcula y la tira."""
    texto = WORKFLOW.read_text(encoding="utf-8")
    bloque = texto.split("git add", 1)[1] if "git add" in texto else ""
    assert re.search(rf"projects/informe_coyuntura/{re.escape(ruta)}\b", bloque), (
        f"{ruta} la regenera el pipeline pero no está en su lista de git add: "
        f"se recalcula cada noche y se descarta")


def test_el_informe_markdown_regenerado_se_versiona_en_el_cron():
    texto = WORKFLOW.read_text(encoding="utf-8")
    bloque = texto.split("git add", 1)[1] if "git add" in texto else ""
    assert "projects/informe_coyuntura/output/informe.md" in bloque


@pytest.mark.parametrize("ruta", sorted(REGENERADAS))
def test_la_salida_versionada_no_quedo_atras_del_snapshot(ruta):
    """El contrapunto del anterior, sobre la evidencia y no sobre el YAML: si
    la copia commiteada es mucho más vieja que el snapshot publicado, alguien
    dejó de commitearla aunque el workflow diga lo contrario."""
    f_salida = _fecha(ruta, REGENERADAS[ruta])
    if f_salida is None:
        pytest.skip(f"{ruta} todavía no tiene sello de tiempo (corrida previa a ADR-0177)")
    f_snap = _fecha("web/src/data/informe.json", ("generated_at",))
    atraso = (f_snap - f_salida).days
    assert atraso <= TOLERANCIA_DIAS, (
        f"{ruta} quedó {atraso} días atrás del snapshot publicado "
        f"({f_salida.date()} vs {f_snap.date()}): el pipeline la regenera y no la commitea")
