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
  reporte    el mismo diagnóstico en markdown, para el cuerpo del issue
  recuperado volvió a publicar después de al menos una falla
  degradado  revisa el log de colectores y avisa SÓLO lo inesperado

`fallo` y `reporte` comparten el parser: un solo lugar que sabe leer un log de
corrida, dos formatos de salida. Duplicarlo en bash dentro del workflow es la
forma segura de que el issue y Slack terminen contando cosas distintas.

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
# `::notice::` es lo que el script ESCRIBE y lo que el `tee` guarda en el
# archivo; `##[notice]` es como GitHub lo RENDERIZA en el log que se descarga.
# Los parsers de acá leían sólo la segunda forma y el archivo trae la primera:
# los avisos de "fuente caída entera" y "presupuesto agotado" nunca se
# dispararon en producción, con los tests en verde porque los alimentaban con
# la forma renderizada. Se aceptan las dos, siempre.
def _cmd(nombre: str) -> str:
    """Las DOS formas del mismo comando de workflow, cada una entera.

    Definir apertura y cierre por separado matchea también `::error]` y
    `##[error::`, que no existen. Acá se alternan comandos completos.
    """
    return rf"(?:::{nombre}::|\#\#\[{nombre}\])"

RUIDO_DE_RED = re.compile(
    r"\b\d{3}\s+(client|server)\s+error|timeout|timed out|connection|"
    r"ssl|certificate|max retries|temporarily unavailable|read timed out|"
    r"name or service not known|getaddrinfo",
    re.I,
)


# ── Qué falló, en concreto ───────────────────────────────────────────────────
#
# Hasta septiembre de 2026 el aviso decía el PASO ("Tests de reconciliación y
# robustez") y nada más. Para saber qué pasó había que abrir el run igual, que
# es exactamente el trabajo que el aviso venía a evitar. Peor: tres noches
# seguidas con el mismo mensaje se leen como tres fallas distintas, cuando era
# una sola con un mes escrito a mano adentro de un test.

FALLA_PYTEST = re.compile(r"^FAILED\s+(\S+?)(?:\s+-\s+(.*))?$", re.M)
RESUMEN_PYTEST = re.compile(r"^(\d+) failed,\s*(\d+) passed", re.M)
# Un ModuleNotFoundError rompe pytest en la COLECCIÓN: no hay ni un `FAILED` ni
# un `N failed`, hay `ERROR tests/x.py` y `N errors`. Es la forma en que un
# crash de import se veía como un diagnóstico vacío.
ERROR_PYTEST = re.compile(r"^ERROR\s+(\S+?)(?:\s+-\s+(.*))?$", re.M)
RESUMEN_ERRORES = re.compile(r"^(\d+) errors?\b", re.M)
FALLA_GATE = re.compile(r"^\s*\[FALLA\]\s+(.+)$", re.M)
ERROR_WORKFLOW = re.compile(rf"^{_cmd('error')}(.+)$", re.M)
RUIDO_GENERICO = re.compile(r"Process completed with exit code|^No se pudo publicar|^causa queda", re.I)
EXIT_COLECTOR = re.compile(rf"^{_cmd('notice')}(\w+) exit=(\d+)$", re.M)


def _leer(ruta: str) -> str:
    if not ruta or not os.path.exists(ruta):
        return ""
    return open(ruta, encoding="utf-8", errors="replace").read()


def causas(log: str) -> list[str]:
    """Las razones concretas por las que el job se cortó, en orden de utilidad.

    Devuelve vacío si no reconoce nada: es mejor decir "no se pudo leer" que
    inventar una causa. El aviso nunca es la única fuente — siempre lleva el
    link al run.
    """
    fuera: list[str] = []

    for m in FALLA_GATE.finditer(log):
        fuera.append(f"Gate de calidad · {m.group(1).strip()}")

    for patron in (FALLA_PYTEST, ERROR_PYTEST):
        for m in patron.finditer(log):
            prueba, motivo = m.group(1), (m.group(2) or "").strip()
            if not motivo:
                # En un error de colección el motivo va en una línea `E   ...`
                # aparte, no pegado al nombre del archivo.
                em = re.search(r"^E\s+(\w*Error.*)$", log, re.M)
                motivo = em.group(1).strip() if em else ""
            fuera.append(f"{prueba}" + (f"\n    {motivo[:300]}" if motivo else ""))

    for m in ERROR_WORKFLOW.finditer(log):
        texto = m.group(1).strip()
        # "Process completed with exit code 1" es el epitafio genérico que
        # GitHub le pone a TODO paso que falla: repetirlo como causa es decir
        # "falló porque falló". La causa real ya la pusieron los parsers de
        # arriba, o no está en el log.
        if texto and not RUIDO_GENERICO.match(texto):
            fuera.append(texto[:300])

    return fuera


def resumen_pytest(log: str) -> str:
    m = RESUMEN_PYTEST.search(log)
    if m:
        return f"{m.group(1)} de {int(m.group(1)) + int(m.group(2))} pruebas"
    e = RESUMEN_ERRORES.search(log)
    return f"{e.group(1)} módulo(s) ni siquiera se pudieron cargar" if e else ""


def cola(log: str, n: int = 6) -> list[str]:
    """Las últimas líneas con contenido, para cuando no se reconoce nada.

    Es peor decir «no se pudo leer la causa» y nada más: el final del log casi
    siempre tiene el traceback, aunque no tenga un formato conocido.
    """
    lineas = [l.strip() for l in log.splitlines() if l.strip()]
    return lineas[-n:]


def colectores(log: str) -> list[tuple[str, int]]:
    """(script, exit) de cada colector. 0 fresco · 1 mixto · 2 todo caché."""
    return [(m.group(1), int(m.group(2))) for m in EXIT_COLECTOR.finditer(log)]


def _linea_colectores(cols: list[tuple[str, int]]) -> str:
    if not cols:
        return ""
    glifo = {0: "fresco", 1: "mixto", 2: "todo caché"}
    return " · ".join(f"{n} {glifo.get(c, f'exit={c}')}" for n, c in cols)


def _racha(n: int) -> str:
    """Cuántas corridas caídas seguidas lleva el aviso ABIERTO.

    Se dice «corrida» y no «noche» a propósito: un reintento a mano el mismo día
    también suma, y llamarlo noche sería mentir por redondeo.
    """
    if n <= 1:
        return ""
    return f" *(corrida caída nº {n} desde que se abrió el aviso — puede ser la misma causa)*"


CANCELADO = (
    "El job fue *cancelado*, no falló: o se comió el tope de 45 minutos, o lo "
    "cortó alguien. Suele no dejar causa en el log — mirá dónde se quedó."
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

    for m in re.finditer(rf"^{_cmd('notice')}(\w+) exit=(\d+)", log, re.M):
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

    for m in re.finditer(rf"^{_cmd('warning')}(\w+) agotó su presupuesto", log, re.M):
        motivos.append(f"`{m.group(1)}` agotó su presupuesto de tiempo y siguió con caché.")

    return motivos


def _reporte(a, pasos, motivos, cols, resumen, fin) -> int:
    """El cuerpo del issue: el mismo diagnóstico, más largo y en markdown.

    Acá sí conviene ser verboso — el issue es el registro y se lee después,
    a veces semanas más tarde, cuando nadie se acuerda de qué pasaba esa noche.
    """
    from datetime import datetime, timezone
    out = [f"La corrida del {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} falló."]
    if a.estado == "cancelled":
        out.append("\n> **El job fue cancelado, no falló.** O se comió el tope de 45 "
                   "minutos, o lo cortó alguien. Un job cancelado suele no dejar causa "
                   "en el log: lo que importa es dónde se quedó.")
    if a.fallas > 1:
        out.append(f"\n> **Corrida caída nº {a.fallas}** desde que se abrió este aviso. "
                   f"Si el motivo de abajo es el mismo que el del comentario anterior, "
                   f"es UNA falla que sigue abierta, no {a.fallas} fallas distintas.")

    out.append("\n## Pasos que fallaron\n")
    out += [f"- {p_}" for p_ in pasos] or ["- (no se pudo determinar el paso)"]

    out.append("\n## Qué falló, en concreto\n")
    if motivos:
        for m in motivos:
            cabeza, _, cola = m.partition("\n")
            out.append(f"- `{cabeza}`")
            if cola.strip():
                out.append(f"  > {cola.strip()}")
    elif fin:
        out.append("No se reconoció una causa conocida. El final del log:\n")
        out.append("```\n" + "\n".join(fin) + "\n```")
    else:
        out.append("_No se pudo leer la causa del log. Está en el run._")
    if resumen:
        out.append(f"\nFalló **{resumen}**.")

    out.append("\n## Qué sí anduvo\n")
    if cols:
        glifo = {0: "todo fresco", 1: "mixto fresco/caché", 2: "todo caché — fuente caída"}
        out += [f"- `{n}` → {glifo.get(c, f'exit={c}')}" for n, c in cols]
        out.append("\nLos colectores usan el exit code como dato, no como error: "
                   "un `1` es normal (SAIJ bloquea a los runners casi todas las noches).")
    else:
        out.append("_Sin log de colectores: la corrida se cortó antes o no se pudo leer._")

    out.append("\n## Qué está viendo la gente\n")
    out.append("El snapshot **no se publicó**: producción sigue sirviendo el anterior"
               + (f", generado el {a.sirviendo}" if a.sirviendo else "") + ".")
    out.append("No hay un dato malo publicado — hay un dato viejo.")
    out.append(f"\n{a.url}\n\nEste issue se cierra solo cuando una corrida vuelva a "
               "terminar bien.")
    print("\n".join(out))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["fallo", "reporte", "recuperado", "degradado"])
    p.add_argument("--url", default=os.environ.get("RUN_URL", ""))
    p.add_argument("--pasos", default="")
    p.add_argument("--log", default="")
    p.add_argument("--gates", default="", help="log del gate y de pytest")
    p.add_argument("--fallas", type=int, default=1,
                   help="cuántas corridas caídas seguidas lleva el aviso abierto")
    p.add_argument("--estado", default="failure", help="job.status: failure | cancelled")
    p.add_argument("--sirviendo", default="", help="generated_at de lo que está en producción")
    a = p.parse_args()

    if a.modo in ("fallo", "reporte"):
        pasos = [l.lstrip("- ").strip() for l in a.pasos.splitlines() if l.strip()]
        texto_gates = _leer(a.gates)
        texto_cols = _leer(a.log)
        motivos = causas(texto_gates + "\n" + texto_cols)
        cols = colectores(texto_cols)
        resumen = resumen_pytest(texto_gates)

        if a.modo == "reporte":
            return _reporte(a, pasos, motivos, cols, resumen,
                            cola(texto_gates or texto_cols))

        cancelado = a.estado == "cancelled"
        cabecera = ("🔴 *El pipeline nocturno se cortó sin publicar.*"
                    if cancelado else "🔴 *El pipeline nocturno falló y no publicó.*")
        cuerpo = [cabecera + _racha(a.fallas)]
        if cancelado:
            cuerpo.append(CANCELADO)
        cuerpo.append("*Paso:* " + (", ".join(pasos) or "no se pudo determinar"))
        if motivos:
            cuerpo.append("*Qué falló:*")
            cuerpo += [f"• {m}" for m in motivos[:5]]
            if len(motivos) > 5:
                cuerpo.append(f"  …y {len(motivos) - 5} más, en el run.")
        else:
            fin = cola(texto_gates or texto_cols)
            if fin:
                cuerpo.append("*No se reconoció una causa; el final del log dice:*")
                cuerpo += [f"> {l[:200]}" for l in fin[-3:]]
            else:
                cuerpo.append("_No se pudo leer la causa del log; está en el run._")
        if resumen:
            cuerpo.append(f"*Pruebas:* falló {resumen}.")
        if cols:
            cuerpo.append(f"*Colectores:* {_linea_colectores(cols)}.")
        cuerpo.append(
            "\nLa web sigue mostrando la corrida anterior"
            + (f" ({a.sirviendo})" if a.sirviendo else "")
            + " — no hay dato malo publicado, hay dato viejo."
        )
        cuerpo.append(a.url)
        return publicar("\n".join(cuerpo))

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
