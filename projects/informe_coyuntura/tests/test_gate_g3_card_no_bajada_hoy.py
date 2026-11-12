"""G3 no corta la publicación por una card que no se bajó en esta corrida.

El 31-oct-2026 gestion agotó su presupuesto: sus cards salieron del archivo de
la víspera sin la marca `desactualizado`, la serie de reduccion_estado bajó
septiembre fresca y G3 cortó todo. Una card con sello de un día anterior es
carry-forward (lo vigila G2b); una fresca que no coincide sigue bloqueando.
"""
import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))


def _gate_con(tmp_path, monkeypatch, horas_antes):
    """El sello se pone `horas_antes` del `generated_at` REAL del snapshot.

    Antes el test fijaba el snapshot al 1-nov: toda card vigente con sello
    posterior parecía «fresca» y el gate fallaba por otra card en
    carry-forward (conflictividad_nacional, 12-nov-2026)."""
    import gate_calidad
    for f in gate_calidad.SNAPSHOT.iterdir():
        if f.is_file():
            shutil.copy(f, tmp_path / f.name)
    inf = json.loads((tmp_path / "informe.json").read_text(encoding="utf-8"))
    ind = inf["cinturones"]["gestion"]["indicadores"]["reduccion_estado"]
    ind["valor"] = ind["valor"] + 5
    ind["desactualizado"] = False
    generado = datetime.fromisoformat(inf["generated_at"])
    ind["obtenido_en"] = (generado - timedelta(hours=horas_antes)).replace(tzinfo=None).isoformat()
    (tmp_path / "informe.json").write_text(json.dumps(inf, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(gate_calidad, "SNAPSHOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["gate_calidad.py"])
    return gate_calidad.main()


def test_card_fresca_que_no_coincide_bloquea(tmp_path, monkeypatch, capsys):
    assert _gate_con(tmp_path, monkeypatch, 0.5) == 1
    assert "G3 gestion/reduccion_estado" in capsys.readouterr().out


def test_card_de_la_vispera_no_bloquea(tmp_path, monkeypatch, capsys):
    assert _gate_con(tmp_path, monkeypatch, 24.5) == 0
    assert "carry-forward" in capsys.readouterr().out


def test_bajada_antes_de_medianoche_sigue_fresca(tmp_path, monkeypatch, capsys):
    """Descargada 41 minutos antes del snapshot (p. ej. 23:59 y 00:40): es de esta corrida y bloquea."""
    assert _gate_con(tmp_path, monkeypatch, 0.7) == 1
