"""G3 no corta la publicación por una card que no se bajó en esta corrida.

El 31-oct-2026 gestion agotó su presupuesto: sus cards salieron del archivo de
la víspera sin la marca `desactualizado`, la serie de reduccion_estado bajó
septiembre fresca y G3 cortó todo. Una card con sello de un día anterior es
carry-forward (lo vigila G2b); una fresca que no coincide sigue bloqueando.
"""
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))


def _gate_con(tmp_path, monkeypatch, sello):
    import gate_calidad
    for f in gate_calidad.SNAPSHOT.iterdir():
        if f.is_file():
            shutil.copy(f, tmp_path / f.name)
    inf = json.loads((tmp_path / "informe.json").read_text(encoding="utf-8"))
    ind = inf["cinturones"]["gestion"]["indicadores"]["reduccion_estado"]
    ind["valor"] = ind["valor"] + 5
    ind["desactualizado"] = False
    ind["obtenido_en"] = sello
    (tmp_path / "informe.json").write_text(json.dumps(inf, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(gate_calidad, "SNAPSHOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["gate_calidad.py"])
    return gate_calidad.main()


def test_card_fresca_que_no_coincide_bloquea(tmp_path, monkeypatch, capsys):
    assert _gate_con(tmp_path, monkeypatch, date.today().isoformat()) == 1
    assert "G3 gestion/reduccion_estado" in capsys.readouterr().out


def test_card_de_la_vispera_no_bloquea(tmp_path, monkeypatch, capsys):
    ayer = (date.today() - timedelta(days=1)).isoformat()
    assert _gate_con(tmp_path, monkeypatch, ayer) == 0
    assert "carry-forward" in capsys.readouterr().out
