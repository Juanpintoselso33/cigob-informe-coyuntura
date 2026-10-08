#!/usr/bin/env python3
"""Avisos a #monitor-alertas de los cambios pedidos desde claude.ai.

Desde el 6-oct-2026 lo que se pide al Monitor desde claude.ai se publica solo:
corren los tests y se mergea al terminar, pasen o no. Sin este aviso, un
cambio que rompe algo se enteraba recién la corrida nocturna, y sin decir
quién lo pidió ni qué cambió. Lo corre `.github/workflows/cambios-desde-claude.yml`.

Avisa sólo cuando hay algo que mirar (la regla del canal: sólo lo accionable):

  🔴 el cambio dejó en rojo pruebas, tipos o build que antes andaban
  🔴 el deploy de Vercel falló o la página no carga
  🔴 la corrida de datos que lanzó el cambio falló
  🟡 se tocó el cálculo, las bandas, los pesos o qué indicadores son card
  🟡 cambiaron muchas cosas de golpe
  🟡 main ya tenía pruebas en rojo y el cambio se publicó encima (un solo
     hilo para todos los cambios que caen encima, no uno por cambio)
  🟡 Vercel llegó al tope de deploys del día: el cambio espera, no está roto

Las dos últimas son de ADR-0350. El 8-oct-2026 cuatro cambios de Luis
dispararon cuatro 🔴 «se publicó con algo roto», y dos de ellos culpaban a un
cambio que no había roto nada: las pruebas ya estaban rojas desde los dos
anteriores. Y el 7-oct un 🔴 «el deploy falló» pedía deshacer un cambio cuando
lo que había pasado era el tope diario del plan Hobby.

Para saber qué ya estaba rojo, cada cambio guarda al final el conjunto de
pruebas rojas con que quedó main (se mergea igual, así que es el estado de
main), en un artifact de Actions (`estado-avisos-cambios`), y el siguiente lo
compara. No se corre pytest dos veces. La corrida nocturna en verde lo vacía.

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
  verde    la corrida nocturna pasó las pruebas: main está en verde
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

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

# El status que deja Vercel en el commit cuando el plan llega al tope diario de
# deploys (7-oct-2026: «Deployment rate limited — retry in 24 hours»). Si la
# descripción no dice esto con todas las letras, se avisa como antes.
TOPE_VERCEL = re.compile(r"rate[ -]?limited|Resource is limited|api-deployments-free-per-day", re.I)
ART = ZoneInfo("America/Argentina/Buenos_Aires")
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()


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


def id_falla(linea: str) -> str:
    """Lo que identifica una falla entre dos cambios: el nombre de la prueba
    (el motivo puede cambiar de texto sin que sea otra falla)."""
    m = re.match(r"^pytest: (?:FAILED|ERROR)\s+(\S+)", linea)
    return f"pytest: {m.group(1)}" if m else linea


def separar(actuales: list[str], previas: list[str] | None) -> tuple[list[str], list[str]]:
    """(nuevas, heredadas). Sin estado previo conocido, todas son nuevas: se
    culpa al cambio como antes de ADR-0350, que es lo seguro."""
    if previas is None:
        return list(actuales), []
    ya = set(previas)
    return ([l for l in actuales if id_falla(l) not in ya],
            [l for l in actuales if id_falla(l) in ya])


def motivos(archivos: list[str], lineas: int, pruebas: str, lineas_falla: list[str],
            heredadas: list[str] = ()) -> list[tuple[str, str]]:
    """(glifo, texto) por cada cosa que hay que avisar. Vacío = no se avisa.

    `lineas_falla` son las fallas NUEVAS; `heredadas`, las que main ya tenía
    antes de este cambio. Si todas son heredadas, el cambio no rompió nada.
    """
    out: list[tuple[str, str]] = []
    if pruebas == "failure" and (lineas_falla or not heredadas):
        detalle = "; ".join(lineas_falla[:TOPE_FALLAS]) or "ver el detalle en el PR"
        resto = f" (y {len(lineas_falla) - TOPE_FALLAS} más)" if len(lineas_falla) > TOPE_FALLAS else ""
        ya = (f" Además, {len(heredadas)} ya estaba{'n' if len(heredadas) > 1 else ''} en rojo en main "
              f"antes de este cambio: no son de él." if heredadas else "")
        out.append(("🔴", f"Se publicó con pruebas en rojo: {detalle}{resto}.{ya}"))
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


def publicar(texto: str, hilo: str = "", al_canal: bool = True) -> str:
    """Postea (en el hilo `hilo` si hay, y también en el canal salvo
    `al_canal=False`) y devuelve el ts."""
    extra = {"thread_ts": hilo, **({"reply_broadcast": True} if al_canal else {})} if hilo else {}
    r = _slack("chat.postMessage", text=texto, **extra)
    return r.get("ts", "") if r.get("ok") else ""


def editar(ts: str, texto: str) -> bool:
    """Edita un mensaje en su lugar: `chat.update` no notifica a nadie."""
    return bool(ts) and bool(_slack("chat.update", ts=ts, text=texto).get("ok"))


# ── Estado entre cambios (ADR-0350) ─────────────────────────────────────

def cargar_estado(ruta: str) -> dict:
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8")) if ruta else {}
    except (OSError, ValueError):
        return {}


def guardar_estado(ruta: str, estado: dict) -> None:
    if ruta:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        Path(ruta).write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def _fecha(d: datetime) -> str:
    d = d.astimezone(ART)
    return f"{d.day}-{MESES[d.month - 1]}"


# ── main tiene pruebas rojas: un hilo, no un 🔴 por cambio ──────────────

def texto_main_rojas(p: dict) -> str:
    lista = p["lista"]
    n, c = len(lista), len(p["cambios"])
    items = [f"• `{x}`" for x in lista[:TOPE_FALLAS]]
    if n > TOPE_FALLAS:
        items.append(f"  …y {n - TOPE_FALLAS} más.")
    return "\n".join([
        f"🟡 *{MONITOR} — main tiene {n} prueba{'s' if n > 1 else ''} en rojo de antes*",
        *items,
        f"*Lleva {c} cambio{'s' if c > 1 else ''} encima:* " + ", ".join(f"#{x}" for x in p["cambios"])
        + f". Se publicaron igual y no rompieron esto{'s' if n > 1 else ''}: no hay que deshacerlos.",
        "*Qué ve la gente:* los cambios, publicados. Pero mientras main tenga pruebas en rojo la corrida "
        "nocturna no publica datos nuevos (eso avisa en su propio hilo).",
        f"*Qué hacer:* arreglar {'esas pruebas' if n > 1 else 'esa prueba'}, o el cambio que "
        f"{'las' if n > 1 else 'la'} rompió. Este aviso se cierra solo cuando main vuelve a verde.",
        f"_Desde el {p['desde']}._",
    ])


def _cerrar_main_rojas(estado: dict, como: str, ahora: datetime) -> None:
    p = estado.pop("main_rojas", None)
    if not p:
        return
    n = len(p["lista"])
    editar(p["ts"], "\n".join([
        f"✅ *{MONITOR} — main vuelve a tener las pruebas en verde*",
        f"_Estuvo abierto del {p['desde']} al {_fecha(ahora)} · {len(p['cambios'])} cambio(s) encima._",
        f"> _Era:_ main tenía {n} prueba{'s' if n > 1 else ''} en rojo de antes.",
    ]))
    # 🟡: el ✅ queda en el hilo, sin salir al canal (ADR-0350).
    publicar(f"✅ Main vuelve a verde: {como}.", p["ts"], al_canal=False)


def seguir_main_rojas(estado: dict, pr: int, nuevas: list[str], heredadas: list[str],
                      ahora: datetime) -> None:
    """Abre, actualiza o cierra el hilo «main tiene pruebas rojas».

    La clave es el conjunto de pruebas heredadas. Mismo conjunto (o uno que se
    achica) → se edita la raíz y se suma el cambio a «lleva N encima», sin
    mensaje nuevo. Pruebas heredadas que el hilo no tenía → es otro problema:
    la raíz vieja se cierra y se abre otra. Si el cambio rompió algo propio, su
    🔴 ya menciona las heredadas y no se abre un hilo aparte por él.
    """
    p = estado.get("main_rojas")
    ids = sorted({id_falla(x) for x in heredadas})
    if not ids:
        _cerrar_main_rojas(estado, f"las pruebas que estaban en rojo ya pasan con el #{pr}", ahora)
        return
    if p and set(ids) <= set(p["lista"]):
        p.update(lista=ids, clave="\n".join(ids))
        p["cambios"].append(pr)
        editar(p["ts"], texto_main_rojas(p))
        return
    if p:
        _cerrar_main_rojas(estado, "lo reemplaza un aviso nuevo, con otro conjunto de pruebas en rojo", ahora)
    elif nuevas:
        return
    p = dict(clave="\n".join(ids), lista=ids, cambios=[pr], desde=_fecha(ahora), ts="")
    p["ts"] = publicar(texto_main_rojas(p))
    if p["ts"]:
        estado["main_rojas"] = p


# ── Tope de deploys de Vercel ───────────────────────────────────────────

def es_tope_vercel(estado: str, descripcion: str) -> bool:
    return estado in ("failure", "error") and bool(TOPE_VERCEL.search(descripcion or ""))


def fin_del_tope(descripcion: str, fecha_status: str) -> datetime | None:
    """Cuándo se libera, si el status lo dice («retry in 24 hours»)."""
    m = re.search(r"retry in (\d+)\s*(hours?|h|minutes?|mins?|m)\b", descripcion or "", re.I)
    try:
        base = datetime.fromisoformat((fecha_status or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if not m or base.tzinfo is None:
        return None
    n = int(m.group(1))
    return base + (timedelta(hours=n) if m.group(2).lower().startswith("h") else timedelta(minutes=n))


def texto_tope(t: dict) -> str:
    if t.get("hasta"):
        h = datetime.fromisoformat(t["hasta"]).astimezone(ART)
        cuando = f"cerca de las {h:%H:%M} del {_fecha(h)} (hora argentina)"
    else:
        cuando = "en ≈24 h"
    return "\n".join([
        f"🟡 *{MONITOR} — Vercel llegó al tope de deploys del día: los cambios esperan, no hay nada roto*",
        "*Cambios que esperan publicarse:* " + ", ".join(f"<{u}|#{n}>" for n, u in t["prs"]) + ".",
        "*Qué ve la gente:* la versión anterior, sin estos cambios. No se rompió nada.",
        f"*Qué hacer:* nada que deshacer. El tope se libera solo {cuando}; después, el próximo push a "
        "main (alcanza con la corrida nocturna) publica todo lo pendiente junto. Si urge, re-desplegar "
        "a mano desde Vercel una vez liberado.",
    ])


def avisar_tope(estado: dict, pr: int, url: str, descripcion: str, fecha_status: str,
                ahora: datetime) -> None:
    """Un 🟡 por tope, no uno por cambio: los que caen dentro se suman a la raíz."""
    t = estado.get("tope_vercel")
    vigente = False
    if t:
        hasta = datetime.fromisoformat(t["hasta"]) if t.get("hasta") else \
            datetime.fromisoformat(t["desde"]) + timedelta(hours=24)
        vigente = ahora < hasta
    if vigente:
        if pr not in [n for n, _ in t["prs"]]:
            t["prs"].append([pr, url])
            editar(t["ts"], texto_tope(t))
        return
    fin = fin_del_tope(descripcion, fecha_status)
    t = dict(desde=ahora.isoformat(), hasta=fin.isoformat() if fin else "", prs=[[pr, url]], ts="")
    t["clave"] = f"tope-vercel:{(fin or ahora):%Y-%m-%dT%H}"
    t["ts"] = publicar(texto_tope(t))
    if t["ts"]:
        estado["tope_vercel"] = t


def _salida(clave: str, valor: str) -> None:
    f = os.environ.get("GITHUB_OUTPUT")
    if f:
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(f"{clave}={valor}\n")


def main(argv: list[str] | None = None, ahora: datetime | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["evaluar", "deploy", "corrida", "verde"])
    ap.add_argument("--pr", type=int, default=0)
    ap.add_argument("--datos-pr", default="",
                    help="JSON de `gh pr view --json title,url,body,files,additions,deletions`")
    ap.add_argument("--archivo-estado", default="",
                    help="JSON con las pruebas rojas de main y los hilos abiertos (ADR-0350)")
    ap.add_argument("--descripcion", default="", help="descripción del status de Vercel")
    ap.add_argument("--fecha-status", default="", help="updated_at del status de Vercel")
    ap.add_argument("--pruebas", default="success")
    ap.add_argument("--logs")
    ap.add_argument("--hilo", default="")
    ap.add_argument("--estado", default="")
    ap.add_argument("--http", default="")
    ap.add_argument("--conclusion", default="")
    ap.add_argument("--corrida-url", default="")
    a = ap.parse_args(argv)
    ahora = ahora or datetime.now(timezone.utc)
    estado = cargar_estado(a.archivo_estado)

    if a.modo == "verde":
        # La corrida nocturna pasó pytest sobre main: no queda nada heredado.
        _cerrar_main_rojas(estado, "la corrida nocturna pasó todas las pruebas", ahora)
        estado["rojas"] = []
        guardar_estado(a.archivo_estado, estado)
        return 0
    if not a.pr or not a.datos_pr:
        ap.error(f"{a.modo} necesita --pr y --datos-pr")

    d = json.loads(Path(a.datos_pr).read_text(encoding="utf-8"))
    titulo, url, quien = d.get("title", ""), d.get("url", ""), pedido_por(d.get("body", ""))
    archivos = [f["path"] for f in d.get("files", [])]
    lineas = int(d.get("additions", 0)) + int(d.get("deletions", 0))

    if a.modo == "evaluar":
        todas = fallas(a.logs)
        # Con qué pruebas rojas quedó main: ninguna si pasó todo; las del log si
        # falló y se pudo leer; desconocido si falló sin log legible.
        actuales = [] if a.pruebas == "success" else (todas if a.pruebas == "failure" and todas else None)
        if actuales is None:
            nuevas, heredadas = todas, []
            estado["rojas"] = None
        else:
            nuevas, heredadas = separar(actuales, estado.get("rojas"))
            seguir_main_rojas(estado, a.pr, nuevas, heredadas, ahora)
            estado["rojas"] = sorted({id_falla(x) for x in actuales})
        guardar_estado(a.archivo_estado, estado)
        lista = motivos(archivos, lineas, a.pruebas, nuevas, heredadas)
        if not lista:
            print("[aviso] nada que avisar")
            return 0
        ts = publicar(texto_cambio(a.pr, url, titulo, quien, archivos, lista))
        _salida("hilo", ts)
        return 0
    if a.modo == "deploy":
        vercel = a.estado
        if es_tope_vercel(a.estado, a.descripcion):
            # No es falla del cambio: aviso aparte, uno por tope (ADR-0350).
            avisar_tope(estado, a.pr, url, a.descripcion, a.fecha_status, ahora)
            guardar_estado(a.archivo_estado, estado)
            vercel = "success"              # sigue avisando si además la página no carga
        texto = texto_deploy(a.pr, url, titulo, quien, vercel, a.http)
    else:
        texto = texto_corrida(a.pr, url, titulo, quien, a.conclusion, a.corrida_url)
    if texto:
        publicar(texto, a.hilo)
    else:
        print("[aviso] nada que avisar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
