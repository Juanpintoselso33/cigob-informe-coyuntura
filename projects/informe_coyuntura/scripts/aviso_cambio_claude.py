#!/usr/bin/env python3
"""Avisos a #monitor-alertas de los cambios pedidos desde claude.ai.

Desde el 6-oct-2026 lo que se pide al Monitor desde claude.ai se publica solo:
corren los tests y se mergea al terminar, pasen o no. Sin este aviso, un
cambio que rompe algo se enteraba recién la corrida nocturna, y sin decir
quién lo pidió ni qué cambió. Lo corre `.github/workflows/cambios-desde-claude.yml`.

Avisa sólo cuando hay algo que mirar (la regla del canal: sólo lo accionable):

  🔴 las pruebas, los tipos o el build quedaron en rojo
  🔴 el deploy de Vercel falló o la página no carga
  🔴 la corrida de datos que lanzó el cambio falló
  🟡 se tocó el cálculo, las bandas, los pesos o qué indicadores son card
  🟡 cambiaron muchas cosas de golpe

Cada aviso dice quién lo pidió, qué cambió, qué falló y el link al PR. El
primero abre un mensaje; lo que pase después (deploy, corrida) va en su hilo.

Es AUTÓNOMO a propósito: no importa nada del repo. El workflow lo corre desde
la versión de `main` anterior al merge, en el job que tiene el token, y si
importara un módulo del PR, el PR podría ejecutar código con ese token.

Sin SLACK_BOT_TOKEN o SLACK_CANAL_ALERTAS no hace nada y sale con 0: el aviso
nunca cambia el resultado del job.

Modos:
  evaluar  después del merge: pruebas en rojo, cambios sensibles o grandes
  deploy   después del deploy: el estado de Vercel y si la página carga
  corrida  cuando termina la corrida de datos que lanzó el cambio
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

MONITOR = "Monitor del Plan de Gobierno"
WEB = "https://informe.cigob.org/"
PROYECTO = "projects/informe_coyuntura/"

# Lo que cambia un número del tablero o qué se muestra. Tocarlo no es un
# error, pero alguien tiene que saberlo el mismo día.
SENSIBLES = [
    (re.compile(r"^scripts/(itcm|itcp|itcg|itvc|parametrica)\.py$"), "el cálculo de los índices (bandas y pesos)"),
    (re.compile(r"^config\.py$"), "la configuración general (pesos de los cinturones y umbrales)"),
    (re.compile(r"^scripts/publicar\.py$"), "qué indicadores se publican como card y cómo"),
    (re.compile(r"^scripts/(macro|politica|gestion|vida_cotidiana)(\.py|/)"), "un colector de datos"),
    (re.compile(r"^scripts/validacion_externa\.py$"), "la validación externa"),
    (re.compile(r"^data/"), "datos cargados a mano"),
    (re.compile(r"^tests/"), "las pruebas"),
]

# Por encima de esto, «muchas cosas de golpe». Las fichas en markdown no
# cuentan: las regenera el propio workflow.
MAX_ARCHIVOS = 5
MAX_LINEAS = 300

TOPE_FALLAS = 8


def _relativa(ruta: str) -> str:
    return ruta[len(PROYECTO):] if ruta.startswith(PROYECTO) else ruta


def pedido_por(cuerpo: str) -> str:
    """Quién lo pidió, como lo escribe el conector en el cuerpo del PR."""
    m = re.search(r"Pedido por \*\*(.+?)\*\*", cuerpo or "")
    return m.group(1).strip() if m else "alguien desde claude.ai"


def sensibles(archivos: list[str]) -> list[str]:
    """Qué zonas sensibles toca, sin repetir y en el orden de SENSIBLES."""
    rel = [_relativa(a) for a in archivos]
    return [nombre for patron, nombre in SENSIBLES if any(patron.search(r) for r in rel)]


def contables(archivos: list[str]) -> list[str]:
    return [a for a in archivos if not _relativa(a).startswith("output/fichas/")]


def es_grande(archivos: list[str], lineas: int) -> bool:
    return len(contables(archivos)) > MAX_ARCHIVOS or lineas > MAX_LINEAS


def fallas(dir_logs: str | None) -> list[str]:
    """Las líneas que dicen qué falló, de los logs de pytest, tsc y el build."""
    if not dir_logs:
        return []
    out: list[str] = []
    for paso in ("pytest", "tsc", "build"):
        f = Path(dir_logs) / f"{paso}.log"
        if not f.is_file():
            continue
        for linea in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"^(FAILED|ERROR)\b", linea) or "error TS" in linea or "[ERROR]" in linea:
                out.append(f"{paso}: {linea.strip()[:180]}")
    return out


def motivos(archivos: list[str], lineas: int, pruebas: str, lineas_falla: list[str]) -> list[tuple[str, str]]:
    """(glifo, texto) por cada cosa que hay que avisar. Vacío = no se avisa."""
    out: list[tuple[str, str]] = []
    if pruebas == "failure":
        detalle = "; ".join(lineas_falla[:TOPE_FALLAS]) or "ver el detalle en el PR"
        resto = f" (y {len(lineas_falla) - TOPE_FALLAS} más)" if len(lineas_falla) > TOPE_FALLAS else ""
        out.append(("🔴", f"Se publicó con pruebas en rojo: {detalle}{resto}."))
    zonas = sensibles(archivos)
    if zonas:
        out.append(("🟡", "Toca " + ", ".join(zonas) + "."))
    if es_grande(archivos, lineas):
        out.append(("🟡", f"Cambian muchas cosas de golpe: {len(contables(archivos))} archivos, "
                          f"{lineas} líneas."))
    return out


def _lista_archivos(archivos: list[str], tope: int = 6) -> str:
    rel = [f"`{_relativa(a)}`" for a in contables(archivos)]
    extra = f" (+{len(rel) - tope})" if len(rel) > tope else ""
    return ", ".join(rel[:tope]) + extra if rel else "—"


def texto_cambio(pr: int, url: str, titulo: str, quien: str, archivos: list[str],
                 lista: list[tuple[str, str]]) -> str:
    glifo = "🔴" if any(g == "🔴" for g, _ in lista) else "🟡"
    cabecera = ("un cambio pedido desde claude.ai se publicó con algo roto" if glifo == "🔴"
                else "un cambio pedido desde claude.ai conviene mirarlo")
    lineas = [
        f"{glifo} *{MONITOR} — {cabecera}*",
        f"*Lo pidió:* {quien} · *Cambio:* {titulo} (<{url}|#{pr}>)",
        f"*Archivos:* {_lista_archivos(archivos)}",
        *[f"*{'Qué falló' if g == '🔴' else 'Ojo'}:* {t}" for g, t in lista],
        f"*Qué hacer:* revisarlo en el PR. Si hay que volver atrás, pedirle a Claude en claude.ai "
        f"que lo deshaga (monitor_deshacer_cambio). {WEB}",
    ]
    return "\n".join(lineas)


def texto_deploy(pr: int, url: str, titulo: str, quien: str, estado: str, http: str) -> str | None:
    problemas = []
    if estado != "success":
        problemas.append("el deploy de Vercel " + ({"failure": "falló", "error": "dio error"}
                                                    .get(estado, f"no terminó ({estado or 'sin estado'})")))
    if http != "200":
        problemas.append(f"la página no carga (respondió {http or 'nada'})")
    if not problemas:
        return None
    return "\n".join([
        f"🔴 *{MONITOR} — después del cambio #{pr}, {' y '.join(problemas)}*",
        f"*Lo pidió:* {quien} · *Cambio:* {titulo} (<{url}|#{pr}>)",
        "*Qué ve la gente:* si el build falló, la versión anterior; si la página no carga, nada.",
        "*Qué hacer:* mirar el deploy en Vercel y, si es el cambio, pedirle a Claude que lo deshaga.",
    ])


def texto_corrida(pr: int, url: str, titulo: str, quien: str, conclusion: str, corrida_url: str) -> str | None:
    if conclusion == "success":
        return None
    return "\n".join([
        f"🔴 *{MONITOR} — la corrida de datos que lanzó el cambio #{pr} no terminó bien ({conclusion or 'sin resultado'})*",
        f"*Lo pidió:* {quien} · *Cambio:* {titulo} (<{url}|#{pr}>)",
        "*Qué ve la gente:* los datos de la corrida anterior; el cambio de cálculo todavía no llegó.",
        f"*Qué hacer:* el diagnóstico está en la corrida: <{corrida_url}|ver la corrida>. "
        f"La corrida también avisa por su cuenta en su propio hilo.",
    ])


# ── Slack ────────────────────────────────────────────────────────────────

def _slack(metodo: str, **datos) -> dict:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    canal = os.environ.get("SLACK_CANAL_ALERTAS", "")
    if not token or not canal:
        print("[aviso] sin SLACK_BOT_TOKEN/SLACK_CANAL_ALERTAS: no se avisa", file=sys.stderr)
        return {}
    req = urllib.request.Request(
        f"https://slack.com/api/{metodo}",
        data=json.dumps({"channel": canal, "unfurl_links": False, **datos}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        r = json.load(urllib.request.urlopen(req, timeout=15))
    except Exception as e:                                  # noqa: BLE001
        print(f"[aviso] no se pudo avisar: {e}", file=sys.stderr)
        return {}
    if not r.get("ok"):
        print(f"[aviso] Slack rechazó {metodo}: {r.get('error')}", file=sys.stderr)
    return r


def publicar(texto: str, hilo: str = "") -> str:
    """Postea (en el hilo `hilo` si hay, y también en el canal) y devuelve el ts."""
    extra = {"thread_ts": hilo, "reply_broadcast": True} if hilo else {}
    r = _slack("chat.postMessage", text=texto, **extra)
    return r.get("ts", "") if r.get("ok") else ""


def _salida(clave: str, valor: str) -> None:
    f = os.environ.get("GITHUB_OUTPUT")
    if f:
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(f"{clave}={valor}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["evaluar", "deploy", "corrida"])
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--datos-pr", required=True,
                    help="JSON de `gh pr view --json title,url,body,files,additions,deletions`")
    ap.add_argument("--pruebas", default="success")
    ap.add_argument("--logs")
    ap.add_argument("--hilo", default="")
    ap.add_argument("--estado", default="")
    ap.add_argument("--http", default="")
    ap.add_argument("--conclusion", default="")
    ap.add_argument("--corrida-url", default="")
    a = ap.parse_args(argv)

    d = json.loads(Path(a.datos_pr).read_text(encoding="utf-8"))
    titulo, url, quien = d.get("title", ""), d.get("url", ""), pedido_por(d.get("body", ""))
    archivos = [f["path"] for f in d.get("files", [])]
    lineas = int(d.get("additions", 0)) + int(d.get("deletions", 0))

    if a.modo == "evaluar":
        lista = motivos(archivos, lineas, a.pruebas, fallas(a.logs))
        if not lista:
            print("[aviso] nada que avisar")
            return 0
        ts = publicar(texto_cambio(a.pr, url, titulo, quien, archivos, lista))
        _salida("hilo", ts)
        return 0
    if a.modo == "deploy":
        texto = texto_deploy(a.pr, url, titulo, quien, a.estado, a.http)
    else:
        texto = texto_corrida(a.pr, url, titulo, quien, a.conclusion, a.corrida_url)
    if texto:
        publicar(texto, a.hilo)
    else:
        print("[aviso] nada que avisar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
