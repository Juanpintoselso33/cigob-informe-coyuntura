#!/usr/bin/env python3
"""El Monitor en Slack, sin ahogar el canal de discusión.

`#informe-de-coyuntura` tuvo **8 mensajes en 60 días**. Un resumen diario serían
~30 por mes contra ~4 humanos: el bot pasaría a ser el 88% del canal. Así que
hace dos cosas distintas:

1. **Un mensaje fijo que se actualiza en su lugar.** `chat.update` no notifica,
   así que la foto de hoy está siempre disponible y no genera un solo mensaje
   nuevo. Es el "quiero ver cómo está" sin costo.

2. **Un mensaje nuevo SÓLO cuando algo se movió de verdad**: cambió el riesgo
   dominante, cambió de cinturón, un cinturón cambió de estado, se prendió la
   alerta multicinturón, o el score global se movió más que el umbral. Son 2 a 5
   por mes, y cada uno merece interrumpir a seis personas.

Mismo criterio que el canario de `aviso_slack.py`: se habla cuando hay algo que
decir, no porque pasó un día.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"
ESTADO = RAIZ / "output" / "estado_slack.json"
URL_PUBLICA = "https://informe.cigob.org/"

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
CANAL = os.environ.get("SLACK_CANAL_INFORME", "")

# Cuánto se tiene que mover el score global para merecer un mensaje. Los scores
# van de 0 a 10 con un decimal, así que 0,5 es un movimiento que se nota y no
# el ruido de un indicador que se actualizó.
UMBRAL_SCORE = 0.5

NOMBRES = {"macro": "Macro", "politica": "Política",
           "vida_cotidiana": "Vida Cotidiana", "gestion": "Gestión"}
ESTADOS = {"estable": "estable", "en_tension": "en tensión",
           "tensionado": "tensionado", "critico": "crítico"}


def slack(metodo: str, **datos) -> dict:
    req = urllib.request.Request(
        f"https://slack.com/api/{metodo}",
        data=json.dumps(datos).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=15))
    except Exception as e:                                   # noqa: BLE001
        return {"ok": False, "error": str(e)}


def leer_estado(d: dict) -> dict:
    return {
        "score_global": d.get("score_global"),
        "cinturon_dominante": d.get("cinturon_dominante"),
        "riesgo": d.get("barbarismo_activo"),
        "multicinturon": bool(d.get("alerta_multicinturon")),
        "cinturones": {k: {"score": v.get("score"), "estado": v.get("estado")}
                       for k, v in (d.get("cinturones") or {}).items()},
    }


def num(x) -> str:
    return "?" if x is None else f"{x:.1f}".replace(".", ",")


def texto_fijo(d: dict, e: dict) -> str:
    fecha = (d.get("generated_at") or "")[:16].replace("T", " ")
    linea = " · ".join(
        f"{NOMBRES.get(k, k)} *{num(v['score'])}* {ESTADOS.get(v['estado'], v['estado'])}"
        for k, v in e["cinturones"].items()
    )
    alerta = "\n:warning: *Alerta multicinturón activa.*" if e["multicinturon"] else ""
    return (
        f":bar_chart: *Monitor del Plan de Gobierno* — estado de hoy\n"
        f"Score global *{num(e['score_global'])}* · riesgo dominante "
        f"*{e['riesgo']}*, desde *{NOMBRES.get(e['cinturon_dominante'], e['cinturon_dominante'])}*"
        f"{alerta}\n\n{linea}\n\n"
        f"<{URL_PUBLICA}|Ver el Monitor> · actualizado {fecha}\n"
        f"_Este mensaje se actualiza solo. Cuando algo cambie de verdad, aviso aparte._"
    )


def cambios(ant: dict, act: dict) -> list[str]:
    """Sólo lo que amerita interrumpir a seis personas."""
    out: list[str] = []
    if ant.get("riesgo") != act["riesgo"]:
        out.append(f"El riesgo dominante pasó de *{ant.get('riesgo')}* a *{act['riesgo']}*.")
    if ant.get("cinturon_dominante") != act["cinturon_dominante"]:
        out.append(
            f"El riesgo dominante ahora sale de *"
            f"{NOMBRES.get(act['cinturon_dominante'], act['cinturon_dominante'])}* "
            f"(antes {NOMBRES.get(ant.get('cinturon_dominante'), ant.get('cinturon_dominante'))})."
        )
    if act["multicinturon"] and not ant.get("multicinturon"):
        out.append("Se prendió la *alerta multicinturón*.")
    elif ant.get("multicinturon") and not act["multicinturon"]:
        out.append("Se apagó la alerta multicinturón.")

    for k, v in act["cinturones"].items():
        prev = (ant.get("cinturones") or {}).get(k, {})
        if prev.get("estado") and prev["estado"] != v["estado"]:
            out.append(
                f"*{NOMBRES.get(k, k)}* pasó de {ESTADOS.get(prev['estado'], prev['estado'])} "
                f"a *{ESTADOS.get(v['estado'], v['estado'])}*."
            )

    a, b = ant.get("score_global"), act["score_global"]
    if a is not None and b is not None and abs(b - a) >= UMBRAL_SCORE:
        out.append(f"El score global se movió de *{num(a)}* a *{num(b)}*.")
    return out


def main() -> int:
    if not TOKEN or not CANAL:
        print("[informe] sin SLACK_BOT_TOKEN/SLACK_CANAL_INFORME: no se avisa", file=sys.stderr)
        return 0
    if not SNAPSHOT.exists():
        print("[informe] no hay snapshot", file=sys.stderr)
        return 0

    d = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    act = leer_estado(d)
    guardado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    ant, ts = guardado.get("estado", {}), guardado.get("ts_fijo")

    # 1. El mensaje que se actualiza en su lugar.
    cuerpo = texto_fijo(d, act)
    r = slack("chat.update", channel=CANAL, ts=ts, text=cuerpo) if ts else {"ok": False}
    if not r.get("ok"):
        # No existía, o alguien lo borró: se crea de nuevo.
        r = slack("chat.postMessage", channel=CANAL, text=cuerpo, unfurl_links=False)
        if r.get("ok"):
            ts = r["ts"]
            pin = slack("pins.add", channel=CANAL, timestamp=ts)
            if not pin.get("ok"):
                print(f"[informe] no se pudo fijar ({pin.get('error')}): fijalo a mano una vez",
                      file=sys.stderr)
        else:
            print(f"[informe] no se pudo publicar: {r.get('error')}", file=sys.stderr)

    # 2. El mensaje nuevo, sólo si algo se movió.
    novedades = cambios(ant, act) if ant else []
    if novedades:
        slack("chat.postMessage", channel=CANAL, unfurl_links=False, text=(
            ":large_blue_circle: *El Monitor se movió.*\n"
            + "\n".join(f"• {n}" for n in novedades)
            + f"\n\n<{URL_PUBLICA}|Ver el Monitor>"
        ))
        print(f"[informe] avisados {len(novedades)} cambio(s)")
    else:
        print("[informe] sin cambios que ameriten aviso")

    ESTADO.write_text(
        json.dumps({"ts_fijo": ts, "estado": act}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
