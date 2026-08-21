# -*- coding: utf-8 -*-
"""Lo que el gate DICE se cruza contra lo que el snapshot TIENE (ADR-0227).

`gate_calidad.py` cerraba toda corrida con demoras diciendo «los indicadores
atrasados van marcados como desactualizados», y no los marcaba: el 21-ago-2026
reportó `macro/icip` (142d) y `vida_cotidiana/mora_familias` (112d), las dos con
`desactualizado: false` y el fetch de esa misma mañana. La frase era falsa desde
que se escribió y nadie la vio porque **ningún test miraba la salida del gate**:
los que hay verifican el código de retorno y la clasificación bloqueante/demora,
nunca la prosa.

Es la misma familia que ADR-0220 —texto publicado que afirma algo que el sistema
no hace— del lado del operador en vez del lector. Este archivo es su guarda: la
prosa se cruza contra los datos, no contra la memoria de alguien.

Dos capas, porque la frase se puede romper de dos formas:

  A. **Lo derivado no puede divergir.** El resumen imprime una línea por card
     demorada con su fecha, su rezago, su tope y su flag. Cada campo se
     re-deriva del snapshot y tiene que coincidir. Cubre el número mal contado
     y el flag mal leído.
  B. **Una afirmación universal obliga al hecho.** Si la salida vuelve a decir
     que las demoradas *están marcadas* como desactualizadas, entonces todas
     tienen que estarlo. No prohíbe la frase: la ata. Es la capa que habría
     agarrado el bug original.
"""
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATE = RAIZ / "scripts" / "gate_calidad.py"
sys.path.insert(0, str(RAIZ / "scripts"))
import gate_calidad  # noqa: E402

# `[DEMORA] G2 <cinturon>/<indicador>: rezago Nd > tope Md (fecha_dato F)`
LINEA_DEMORA = re.compile(
    r"\[DEMORA\]\s+G2\s+(?P<cint>[^/\s]+)/(?P<ind>[^:\s]+):\s+rezago\s+"
    r"(?P<rezago>\d+)d\s+>\s+tope\s+(?P<tope>\d+)d\s+\(fecha_dato\s+"
    r"(?P<fecha>[^)]+)\)")

# La línea derivada del resumen: `· <cint>/<ind>: <fecha>, Nd contra un tope de
# Md · desactualizado=<bool> — …`
LINEA_DERIVADA = re.compile(
    r"·\s+(?P<cint>[^/\s]+)/(?P<ind>[^:\s]+):\s+(?P<fecha>[^,]+),\s+"
    r"(?P<rezago>\d+)d\s+contra\s+un\s+tope\s+de\s+(?P<tope>\d+)d\s+·\s+"
    r"desactualizado=(?P<flag>true|false)")

# Capa B: formas de afirmar que las cards demoradas llevan el flag encendido.
# No son prohibiciones — si alguna aparece, el test exige que sea cierta.
AFIRMA_QUE_ESTAN_MARCADAS = [
    re.compile(r"(atrasad|demorad|rezagad)\w*[^.\n]{0,90}?marcad\w*"
               r"[^.\n]{0,45}?desactualizad", re.I),
    re.compile(r"marcad\w*[^.\n]{0,45}?desactualizad\w*[^.\n]{0,90}?"
               r"(atrasad|demorad|rezagad)", re.I),
    re.compile(r"qued\w+\s+marcad\w*\s+`?desactualizad", re.I),
]


def _correr(snapshot=None, validacion=None):
    cmd = [sys.executable, str(GATE)]
    if snapshot is not None:
        cmd += ["--snapshot", str(snapshot)]
    if validacion is not None:
        cmd += ["--validacion", str(validacion)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(RAIZ))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _cards(snapshot_dir):
    inf = json.loads((Path(snapshot_dir) / "informe.json").read_text(
        encoding="utf-8"))
    return {f"{ck}/{ik}": i
            for ck, c in inf["cinturones"].items()
            for ik, i in c.get("indicadores", {}).items()}


def _auditar(salida, snapshot_dir):
    """El corazón de la guarda. Devuelve los nombres de las cards demoradas."""
    cards = _cards(snapshot_dir)
    hoy = date.today()

    demoradas = {}
    for m in LINEA_DEMORA.finditer(salida):
        demoradas[f"{m['cint']}/{m['ind']}"] = m

    # ── La demora reportada existe y es cierta ────────────────────────────────
    for nombre, m in demoradas.items():
        assert nombre in cards, (
            f"el gate reporta demorada a «{nombre}», que no está en el "
            f"snapshot:\n{salida}")
        ind = cards[nombre]
        assert str(ind.get("fecha_dato")) == m["fecha"], (
            f"{nombre}: el gate dice fecha_dato={m['fecha']} y el snapshot "
            f"tiene {ind.get('fecha_dato')}")
        f = gate_calidad._parse_fecha(ind.get("fecha_dato"))
        assert int(m["rezago"]) == (hoy - f).days, (
            f"{nombre}: el gate dice {m['rezago']}d de rezago y del snapshot "
            f"salen {(hoy - f).days}d")
        tope = gate_calidad.MAX_DIAS.get(m["ind"], gate_calidad.MAX_DIAS_DEFAULT)
        assert int(m["tope"]) == tope, (
            f"{nombre}: el gate dice tope {m['tope']}d y MAX_DIAS tiene {tope}d")
        assert (hoy - f).days > tope, (
            f"{nombre}: reportada como demorada sin estarlo ({(hoy - f).days}d "
            f"contra un tope de {tope}d)")

    # ── Ninguna demora se calla ───────────────────────────────────────────────
    for nombre, ind in cards.items():
        f = gate_calidad._parse_fecha(ind.get("fecha_dato"))
        if f is None:
            continue
        ik = nombre.split("/", 1)[1]
        tope = gate_calidad.MAX_DIAS.get(ik, gate_calidad.MAX_DIAS_DEFAULT)
        if (hoy - f).days > tope:
            assert nombre in demoradas, (
                f"{nombre} pasa su tope ({(hoy - f).days}d > {tope}d) y el "
                f"gate no lo reportó:\n{salida}")

    # ── Capa A: la línea derivada no puede divergir del snapshot ──────────────
    derivadas = {f"{m['cint']}/{m['ind']}": m
                 for m in LINEA_DERIVADA.finditer(salida)}
    if demoradas and "[FALLA]" not in salida:
        assert set(derivadas) == set(demoradas), (
            "el resumen no detalla las mismas cards que reportó como "
            f"demoradas: detalla {sorted(derivadas)} y reportó "
            f"{sorted(demoradas)}\n{salida}")
    for nombre, m in derivadas.items():
        ind = cards[nombre]
        real = "true" if ind.get("desactualizado") else "false"
        assert m["flag"] == real, (
            f"{nombre}: el gate imprime desactualizado={m['flag']} y el "
            f"snapshot tiene {real}. Es exactamente el bug de ADR-0227: el "
            f"gate afirmando del snapshot algo que el snapshot no cumple.")
        assert str(ind.get("fecha_dato")) == m["fecha"].strip()
        assert int(m["rezago"]) == int(demoradas[nombre]["rezago"])
        assert int(m["tope"]) == int(demoradas[nombre]["tope"])

    # ── Capa B: si lo afirma, tiene que ser cierto ────────────────────────────
    for patron in AFIRMA_QUE_ESTAN_MARCADAS:
        hallazgo = patron.search(salida)
        if not hallazgo:
            continue
        sin_marcar = [n for n in demoradas if not cards[n].get("desactualizado")]
        assert not sin_marcar, (
            f"el gate afirma que las cards demoradas están marcadas como "
            f"desactualizadas —«{hallazgo.group(0)}»— y estas no lo están: "
            f"{sorted(sin_marcar)}.\nEs la frase que ADR-0227 sacó. Si el "
            f"comportamiento cambió y ahora sí se marcan, este test pasa solo; "
            f"si no cambió, el que tiene que cambiar es el texto.")

    return set(demoradas)


# ── El snapshot vigente ───────────────────────────────────────────────────────

def test_sobre_el_snapshot_publicado():
    """La corrida real, tal como sale en el pipeline."""
    codigo, salida = _correr()
    _auditar(salida, gate_calidad.SNAPSHOT)
    assert codigo == 0, salida[-2000:]


# ── Snapshots sintéticos: el caso que hay que poder describir bien ────────────

def _armar(tmp_path, *, dias_atras, desactualizado, indicador="icip",
           cinturon="macro"):
    """Snapshot mínimo con UNA card, demorada o no, con el flag que se pida.

    `icip` se usa a propósito: tiene tope propio en MAX_DIAS (140d), así que el
    test cubre también que el gate reporte el tope del indicador y no el
    default.
    """
    fecha = (date.today() - timedelta(days=dias_atras)).isoformat()
    informe = {
        "schema_version": 1,
        "generated_at": date.today().isoformat() + "T00:00:00",
        "period": date.today().isoformat()[:7],
        "score_global": 5.0,
        "cinturones": {cinturon: {"score": 5.0, "indicadores": {indicador: {
            "valor": 8.36,
            "fecha_dato": fecha,
            "fuente": "fuente de prueba",
            "unidad": "u",
            "desactualizado": desactualizado,
            "obtenido_en": date.today().isoformat() + "T09:00:00",
        }}}},
    }
    (tmp_path / "informe.json").write_text(json.dumps(informe), encoding="utf-8")
    (tmp_path / "series.json").write_text("{}", encoding="utf-8")
    return tmp_path, f"{cinturon}/{indicador}"


def test_una_card_demorada_con_el_fetch_sano_no_se_describe_como_marcada(tmp_path):
    """El caso del 21-ago-2026, reproducido: la fuente publica tarde y el fetch
    anduvo perfecto. `desactualizado` es false y el gate tiene que decirlo así."""
    snap, nombre = _armar(tmp_path, dias_atras=142, desactualizado=False)
    codigo, salida = _correr(snap, tmp_path / "sin-validacion.json")
    assert codigo == 0, salida
    assert _auditar(salida, snap) == {nombre}
    assert "desactualizado=false" in salida, salida


def test_una_card_demorada_y_ademas_en_carry_forward_tambien_se_describe_bien(tmp_path):
    """El otro lado: una card puede estar demorada Y en caché. El mensaje no
    puede tener «false» cableado — tiene que leer el flag."""
    snap, nombre = _armar(tmp_path, dias_atras=142, desactualizado=True)
    codigo, salida = _correr(snap, tmp_path / "sin-validacion.json")
    assert codigo == 0, salida
    assert _auditar(salida, snap) == {nombre}
    assert "desactualizado=true" in salida, salida


def test_sin_demoras_no_hay_nada_que_describir(tmp_path):
    snap, _ = _armar(tmp_path, dias_atras=10, desactualizado=False)
    codigo, salida = _correr(snap, tmp_path / "sin-validacion.json")
    assert codigo == 0, salida
    assert _auditar(salida, snap) == set()
    assert "[DEMORA]" not in salida, salida
