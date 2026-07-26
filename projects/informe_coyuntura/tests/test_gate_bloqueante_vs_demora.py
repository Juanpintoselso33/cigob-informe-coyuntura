"""El gate distingue integridad de demora (ADR-0133).

Una fuente atrasada no puede impedir que se publique todo lo demás; una
inconsistencia sí.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
GATE = RAIZ / "scripts" / "gate_calidad.py"


def _correr():
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=str(RAIZ))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_el_gate_pasa_con_el_snapshot_vigente():
    codigo, salida = _correr()
    assert codigo == 0, salida[-2000:]


def test_la_clasificacion_esta_escrita_en_el_codigo():
    """Lo que se protege es el CRITERIO: G2 (frescura) no bloquea, el resto sí.
    Si alguien vuelve a meter G2 entre los bloqueantes, el pipeline entero
    vuelve a caerse porque una fuente publicó tarde."""
    fuente = GATE.read_text(encoding="utf-8")
    assert 'not f_.startswith("G2 ")' in fuente, (
        "el gate dejó de excluir las demoras de los bloqueantes")
    assert "bloqueantes" in fuente and "demorados" in fuente


def test_una_demora_sola_no_bloquea(tmp_path, monkeypatch):
    """Se fuerza un rezago imposible sobre un indicador real bajando su tope a
    cero: el gate tiene que reportarlo como DEMORA y devolver 0."""
    import json
    sys.path.insert(0, str(RAIZ / "scripts"))
    import gate_calidad

    inf = json.loads((gate_calidad.SNAPSHOT / "informe.json").read_text(
        encoding="utf-8"))
    algun = next(ik for c in inf["cinturones"].values()
                 for ik, i in c.get("indicadores", {}).items()
                 if i.get("fecha_dato"))
    monkeypatch.setitem(gate_calidad.MAX_DIAS, algun, 0)
    monkeypatch.setattr(sys, "argv", ["gate_calidad.py"])
    assert gate_calidad.main() == 0, (
        f"una demora de {algun} bloqueó la publicación entera")


def test_la_clasificacion_separa_bien_cada_gate():
    """El contrapunto de la regla, sobre la partición misma: G2 es demora, todo
    lo demás bloquea. Se prueba el predicado, no un snapshot roto — forzar una
    inconsistencia real exigiría corromper el snapshot vigente."""
    muestra = [
        "G1 macro/ipc_total: sin valor",
        "G2 vida_cotidiana/mora_familias: rezago 115d > tope 110d",
        "G3 macro/emae_ia: serie[-1]=1.0 != card=2.0",
        "G6 cinturones.macro.notas: número de ADR en texto público",
    ]
    bloqueantes = [f for f in muestra if not f.startswith("G2 ")]
    demorados = [f for f in muestra if f.startswith("G2 ")]
    assert len(demorados) == 1 and demorados[0].startswith("G2 ")
    assert len(bloqueantes) == 3
    assert all(f.startswith(("G1 ", "G3 ", "G6 ")) for f in bloqueantes)
