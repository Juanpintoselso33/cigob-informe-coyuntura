#!/usr/bin/env python3
"""Avisos del pipeline a Slack (#alertas).

Convive con el aviso por issue de GitHub, no lo reemplaza: el issue es el
registro (se abre, acumula y se cierra solo), Slack es la notificación. Entre
el 22 y el 24-ago-2026 el pipeline falló tres noches seguidas, la web sirvió
datos del 21, y el issue se abrió y se cerró a las 3 de la mañana sin que nadie
lo viera. Eso es lo que este aviso resuelve.

**Regla de admisión de #alertas: sólo lo accionable.** Los deploys y el CI en
verde no entran a propósito — son los que matan estos canales.

Modos:
  fallo      la corrida falló y no publicó
  recuperado volvió a publicar después de al menos una falla
  degradado  revisa el log de colectores y avisa SÓLO lo inesperado

Sin SLACK_BOT_TOKEN no hace nada y sale con 0: el aviso nunca puede cambiar el
resultado del job ni tapar la falla real.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

CANAL = os.environ.get("SLACK_CANAL_ALERTAS", "")
TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# Fuentes con degradación CONOCIDA y decidida: no gritan.
#
# SAIJ bloquea por IP a los runners de GitHub. Está investigado a fondo y la
# política acordada es refrescar a mano cada tanto, no montar infraestructura.
# `politica` devuelve exit=1 por esto CASI TODAS LAS NOCHES: alertarlo haría
# que el canal se vuelva ruido en una semana y deje de leerse.
DEGRADACION_ESPERADA = {"judicializacion"}

# Un error de fuente es de red. Todo lo demás que aparezca en un [ERR] es del
# código nuestro, y ésa es la clase que se disfraza de "fuente caída": pasó con
# `icg_utdt`, que levantaba NameError y el log culpaba a la UTDT (ADR-0175).
RUIDO_DE_RED = re.compile(
    r"\b\d{3}\s+(client|server)\s+error|timeout|timed out|connection|"
    r"ssl|certificate|max retries|temporarily unavailable|read timed out|"
    r"name or service not known|getaddrinfo",
    re.I,
)


def publicar(texto: str) -> int:
    if not TOKEN or not CANAL:
        print("[aviso] sin SLACK_BOT_TOKEN/SLACK_CANAL_ALERTAS: no se avisa", file=sys.stderr)
        return 0
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": CANAL, "text": texto, "unfurl_links": False}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        r = json.load(urllib.request.urlopen(req, timeout=15))
    except Exception as e:                                  # noqa: BLE001
        print(f"[aviso] no se pudo avisar: {e}", file=sys.stderr)
        return 0
    if not r.get("ok"):
        print(f"[aviso] Slack rechazó el mensaje: {r.get('error')}", file=sys.stderr)
    return 0


def analizar(log: str) -> list[str]:
    """Devuelve los motivos por los que hay que avisar. Vacío = todo esperado."""
    motivos: list[str] = []

    for m in re.finditer(r"^##\[notice\](\w+) exit=(\d+)", log, re.M):
        script, code = m.group(1), int(m.group(2))
        if code == 2:
            motivos.append(f"`{script}` no pudo traer *nada* fresco (exit=2): la fuente está caída entera.")

    for m in re.finditer(r"^\s*\[ERR\]\s+([\w.]+):\s*(.+?)(?:\s+--\s|$)", log, re.M):
        ind, msg = m.group(1), m.group(2).strip()
        if ind in DEGRADACION_ESPERADA or RUIDO_DE_RED.search(msg):
            continue
        motivos.append(
            f"`{ind}` falló por algo que *no es la fuente*: `{msg[:150]}`\n"
            f"    Eso se reporta como «fuente caída» y congela la serie. Casi seguro es del código."
        )

    for m in re.finditer(r"^##\[warning\](\w+) agotó su presupuesto", log, re.M):
        motivos.append(f"`{m.group(1)}` agotó su presupuesto de tiempo y siguió con caché.")

    return motivos


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["fallo", "recuperado", "degradado"])
    p.add_argument("--url", default=os.environ.get("RUN_URL", ""))
    p.add_argument("--pasos", default="")
    p.add_argument("--log", default="")
    a = p.parse_args()

    if a.modo == "fallo":
        pasos = a.pasos.strip() or "- (no se pudo determinar el paso)"
        return publicar(
            f"🔴 *El pipeline nocturno falló y no publicó.*\n"
            f"{pasos}\n\n"
            f"La web sigue mostrando la corrida anterior — no hay dato malo publicado, "
            f"hay dato viejo.\n{a.url}"
        )

    if a.modo == "recuperado":
        return publicar(f"🟢 *El pipeline volvió a publicar.* Ya está al día.\n{a.url}")

    if not a.log or not os.path.exists(a.log):
        return 0
    motivos = analizar(open(a.log, encoding="utf-8", errors="replace").read())
    if not motivos:
        return 0                                   # silencio: nada inesperado
    return publicar(
        "🟡 *La corrida publicó, pero con datos degradados que no esperábamos.*\n"
        + "\n".join(f"• {m}" for m in motivos)
        + f"\n\nLas fuentes con degradación conocida (SAIJ) no se avisan.\n{a.url}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
