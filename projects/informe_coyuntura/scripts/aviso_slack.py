#!/usr/bin/env python3
"""Avisos del pipeline a Slack (#monitor-alertas, ex #alertas).

Convive con el aviso por issue de GitHub, no lo reemplaza: el issue es el
registro (se abre, acumula y se cierra solo), Slack es la notificación. Entre
el 22 y el 24-ago-2026 el pipeline falló tres noches seguidas, la web sirvió
datos del 21, y el issue se abrió y se cerró a las 3 de la mañana sin que nadie
lo viera. Eso es lo que este aviso resuelve.

**Regla de admisión de #monitor-alertas: sólo lo accionable.** Los deploys y el CI en
verde no entran a propósito — son los que matan estos canales.

Modos:
  fallo      la corrida falló y no publicó: abre o actualiza el hilo `corrida`
  reporte    el mismo diagnóstico en markdown, para el cuerpo del issue
  recuperado cierra el hilo `corrida` (lo hace también `degradado`)
  degradado  revisa el log de colectores y el del espejo en BigQuery, abre un
             hilo por lo inesperado y cierra los que ya no aparecen (ADR-0309)

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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cotejo_manual import avisos as avisos_cotejo
from cotejo_manual import datos as datos_cotejo

CANAL = os.environ.get("SLACK_CANAL_ALERTAS", "")
TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# El canal no tiene por qué ser sólo del Monitor: CiGob tiene más cosas que avisan
# (la landing, el bot). «El pipeline» o «la web» a secas no dicen de qué
# producto se habla, así que todo aviso lo nombra en la cabecera.
MONITOR = "Monitor del Plan de Gobierno"
MONITOR_URL = "https://informe.cigob.org/"          # la misma que aviso_informe.URL_PUBLICA


def _cabecera(glifo: str, texto: str) -> str:
    return f"{glifo} *{MONITOR} — {texto}*"


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

    # Sin deduplicar, una causa que aparezca en los dos logs se lista dos
    # veces. Un aviso que repite se lee como dos problemas, que es justo lo
    # que este parser vino a evitar.
    vistas: set[str] = set()

    def _sumar(texto: str) -> None:
        if texto not in vistas:
            vistas.add(texto)
            fuera.append(texto)

    for m in FALLA_GATE.finditer(log):
        _sumar(f"Gate de calidad · {m.group(1).strip()}")

    for patron in (FALLA_PYTEST, ERROR_PYTEST):
        for m in patron.finditer(log):
            prueba, motivo = m.group(1), (m.group(2) or "").strip()
            if not motivo:
                # En un error de colección el motivo va en una línea `E   ...`
                # aparte, no pegado al nombre del archivo.
                em = re.search(r"^E\s+(\w*Error.*)$", log, re.M)
                motivo = em.group(1).strip() if em else ""
            _sumar(f"{prueba}" + (f"\n    {motivo[:300]}" if motivo else ""))

    for m in ERROR_WORKFLOW.finditer(log):
        texto = m.group(1).strip()
        # "Process completed with exit code 1" es el epitafio genérico que
        # GitHub le pone a TODO paso que falla: repetirlo como causa es decir
        # "falló porque falló". La causa real ya la pusieron los parsers de
        # arriba, o no está en el log.
        if texto and not RUIDO_GENERICO.match(texto):
            _sumar(texto[:300])

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


CANCELADO = (
    "El job fue *cancelado*, no falló: o se comió el tope de 45 minutos, o lo "
    "cortó alguien. Suele no dejar causa en el log — mirá dónde se quedó."
)


def _slack(metodo: str, **datos) -> dict:
    if not TOKEN or not CANAL:
        print("[aviso] sin SLACK_BOT_TOKEN/SLACK_CANAL_ALERTAS: no se avisa", file=sys.stderr)
        return {}
    req = urllib.request.Request(
        f"https://slack.com/api/{metodo}",
        data=json.dumps({"channel": CANAL, "unfurl_links": False, **datos}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        r = json.load(urllib.request.urlopen(req, timeout=15))
    except Exception as e:                                  # noqa: BLE001
        print(f"[aviso] no se pudo avisar ({metodo}): {e}", file=sys.stderr)
        return {}
    if not r.get("ok"):
        print(f"[aviso] Slack rechazó {metodo}: {r.get('error')}", file=sys.stderr)
    return r


def publicar(texto: str, **extra) -> str:
    """Postea y devuelve el ts del mensaje ('' si no salió)."""
    r = _slack("chat.postMessage", text=texto, **extra)
    return r.get("ts", "") if r.get("ok") else ""


def editar(ts: str, texto: str) -> str:
    """Edita un mensaje en su lugar (`chat.update` no notifica a nadie).

    Devuelve '' si salió, o el error de Slack.
    """
    r = _slack("chat.update", ts=ts, text=texto)
    return "" if r.get("ok") else (r.get("error") or "sin_respuesta")


# La raíz ya no existe o no se puede editar (la borraron, cambió el canal, se
# rotó el bot): no tiene sentido reintentar sobre ese ts.
RAIZ_PERDIDA = {"message_not_found", "channel_not_found", "cant_update_message", "edit_window_closed"}


def _eventos(log: str):
    """(tipo, sujeto, detalle) de cada degradación inesperada del log.

    Lo leen `analizar` (texto plano, para el issue y los tests de siempre) y
    `problemas_degradado` (un problema con clave por evento, para Slack): un
    solo lugar que sabe qué cuenta como inesperado.
    """
    for m in re.finditer(rf"^{_cmd('notice')}(\w+) exit=(\d+)", log, re.M):
        if int(m.group(2)) == 2:
            yield "caida", m.group(1), ""
    for m in re.finditer(r"^\s*\[ERR\]\s+([\w.]+):\s*(.+?)(?:\s+--\s|$)", log, re.M):
        ind, msg = m.group(1), m.group(2).strip()
        if ind in DEGRADACION_ESPERADA or RUIDO_DE_RED.search(msg):
            continue
        yield "err", ind, msg
    for m in re.finditer(rf"^{_cmd('warning')}(\w+) agotó su presupuesto", log, re.M):
        yield "presupuesto", m.group(1), ""


def analizar(log: str) -> list[str]:
    """Devuelve los motivos por los que hay que avisar. Vacío = todo esperado."""
    motivos: list[str] = avisos_cotejo(log)
    for tipo, sujeto, detalle in _eventos(log):
        if tipo == "caida":
            motivos.append(f"`{sujeto}` no pudo traer *nada* fresco (exit=2): la fuente está caída entera.")
        elif tipo == "err":
            motivos.append(
                f"`{sujeto}` falló por algo que *no es la fuente*: `{detalle[:150]}`\n"
                f"    Eso se reporta como «fuente caída» y congela la serie. Casi seguro es del código."
            )
        else:
            motivos.append(f"`{sujeto}` agotó su presupuesto de tiempo y siguió con caché.")
    return motivos


# ── El espejo en BigQuery ────────────────────────────────────────────────────
#
# El paso de BigQuery corre con `continue-on-error`: publicar es el camino
# crítico y el archivo no puede frenarlo. El costo es que su falla no se ve en
# ningún lado — el workflow sale en verde. El 8-sep-2026 Google suspendió la
# cuenta de facturación por un pago rechazado; el export falló el 9 y el 10 con
# `billingNotEnabled` y nadie se enteró hasta que alguien preguntó. Las dos
# corridas quedaron fuera del archivo (se recuperan con bigquery_backfill.py
# porque el snapshot sí se commiteó, pero eso hay que saberlo para hacerlo).

ERROR_BIGQUERY = re.compile(r"^\s*(ERROR:.+|EXPORT A BIGQUERY: FALLÓ.*)$", re.M)
SIN_CLAVE_BIGQUERY = re.compile(rf"^{_cmd('warning')}Sin GCP_SA_KEY", re.M)

PISTAS_BIGQUERY = {
    "billingNotEnabled": ("La cuenta de facturación del proyecto está apagada o "
                          "suspendida (mirá el mail de Google Cloud). Sin facturación "
                          "BigQuery no acepta el DELETE que hace idempotente la carga."),
    "invalid_grant": "La clave de la service account (GCP_SA_KEY) venció o fue revocada.",
}


def analizar_bigquery(log: str, estado: str) -> list[str]:
    """Motivos para avisar del espejo en BigQuery. Vacío = quedó archivado.

    `estado` es `steps.<id>.outcome`: con continue-on-error, `outcome` guarda
    la falla real y `conclusion` la disfraza de success.
    """
    if SIN_CLAVE_BIGQUERY.search(log):
        return ["La corrida *no quedó archivada en BigQuery*: falta el secreto "
                "`GCP_SA_KEY`, el paso se saltea sin escribir nada."]
    if estado != "failure":
        return []

    m = ERROR_BIGQUERY.search(log)
    if m:
        detalle = m.group(1).strip()
        pista = ""
        for clave, texto in PISTAS_BIGQUERY.items():
            if clave in log:
                pista = texto
                break
        cabeza = f"La corrida *no quedó archivada en BigQuery*: `{detalle[:220]}`"
        return [cabeza + (f"\n    {pista}" if pista else "")
                + "\n    El snapshot sí se publicó y commiteó: cuando vuelva, se recupera con "
                  "`bigquery_backfill.py`."]

    fin = cola(log, 3)
    texto = ("La corrida *no quedó archivada en BigQuery* y el log no dice una causa "
             "conocida; el final dice:")
    return [texto + "".join(f"\n    > {l[:200]}" for l in fin)
            if fin else texto.replace("; el final dice:", ".")]


# Presupuesto de líneas del 🔴: las causas reales y los cotejos pendientes van
# en secciones separadas, cada una con su tope, para que muchos de una clase
# nunca escondan a la otra. La causa de la falla no se repite a la noche
# siguiente; el cotejo sí, así que es la causa la que no puede quedar afuera.
TOPE_CAUSAS = 5
TOPE_COTEJOS = 3


def _seccion(cuerpo: list[str], titulo: str, items: list[str], tope: int) -> None:
    if not items:
        return
    cuerpo.append(titulo)
    cuerpo += [f"• {m}" for m in items[:tope]]
    if len(items) > tope:
        cuerpo.append(f"  …y {len(items) - tope} más, en el run.")


def _reporte(a, pasos, motivos, cols, resumen, fin, cotejos=()) -> int:
    """El cuerpo del issue: el mismo diagnóstico, más largo y en markdown.

    Acá sí conviene ser verboso — el issue es el registro y se lee después,
    a veces semanas más tarde, cuando nadie se acuerda de qué pasaba esa noche.
    """
    from datetime import datetime, timezone
    out = [f"La corrida del {MONITOR} del {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} falló."]
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

    if cotejos:
        out.append("\n## Cotejo manual pendiente\n")
        for m in cotejos:
            cabeza, _, cola = m.partition("\n")
            out.append(f"- `{cabeza}`")
            if cola.strip():
                out.append(f"  > {cola.strip()}")

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


# ── Un hilo por problema (ADR-0309) ──────────────────────────────────────────
#
# Hasta septiembre de 2026 cada corrida posteaba su aviso suelto: la misma falla
# de `produccion_legislativa` salió tres noches seguidas como tres mensajes
# idénticos, y cuando se arregló no dijo nada — el silencio de una corrida
# limpia no se distingue de un bot que no corrió. El 🟢 existía, pero sólo
# para el 🔴 y como mensaje suelto.
#
# Ahora cada problema tiene una clave estable y un mensaje raíz:
#   · aparece        → mensaje nuevo en el canal
#   · sigue abierto  → se EDITA la raíz ("lleva N corridas"); si cambia el
#                      diagnóstico, respuesta en el hilo. Nada nuevo en el canal.
#   · desaparece     → respuesta en el hilo que también sale en el canal
#                      («✅ se resolvió…») y la raíz pasa a ✅.
#
# El estado (clave → ts, desde, corridas, huella) vive en la cache de Actions y
# no en git: una corrida caída no llega a commitear y es justo la que avisa.

ART = ZoneInfo("America/Argentina/Buenos_Aires")
RAIZ = Path(__file__).resolve().parents[1]
DATOS_TS = RAIZ / "web" / "src" / "lib" / "datos.ts"
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()


def _fecha(d: datetime | None = None) -> str:
    d = d or datetime.now(ART)
    return f"{d.day}-{MESES[d.month - 1]}"


def rotulo(indicador: str) -> str:
    """El nombre que ve la gente en la card, de la tabla LABELS de datos.ts."""
    try:
        m = re.search(r"(?<![\w])" + re.escape(indicador) + r':\s*"([^"]+)"',
                      DATOS_TS.read_text(encoding="utf-8"))
    except OSError:
        m = None
    return m.group(1) if m else indicador


def _ultimo_dato(indicador: str) -> str:
    try:
        cints = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cinturones"]
    except (OSError, ValueError, KeyError):
        return ""
    for c in cints.values():
        ind = (c.get("indicadores") or {}).get(indicador)
        if isinstance(ind, dict) and ind.get("fecha_dato"):
            try:
                d = datetime.strptime(str(ind["fecha_dato"])[:10], "%Y-%m-%d")
            except ValueError:
                return ""
            # Un dato mensual viene fechado el 1: «1-ago» sugeriría un día.
            return (f"{MESES[d.month - 1]}-{d.year}" if d.day == 1
                    else f"{d.day}-{MESES[d.month - 1]}-{d.year}")
    return ""


def _problema(clave, glifo, titulo, resuelto, cuerpo, huella=None) -> dict:
    """`titulo` dice el problema; `resuelto`, cómo se lee cuando se arregla."""
    return dict(clave=clave, glifo=glifo, titulo=titulo, resuelto=resuelto, cuerpo=list(cuerpo),
                huella=huella if huella is not None else "\n".join(cuerpo))


def problemas_degradado(log: str, log_bq: str = "", estado_bq: str = "") -> list[dict]:
    """Cada degradación inesperada como un problema con clave estable."""
    out = []
    for tipo, sujeto, detalle in _eventos(log):
        if tipo == "err":
            dato = _ultimo_dato(sujeto)
            out.append(_problema(
                f"err:{sujeto}", "🟡", f"«{rotulo(sujeto)}» no se está actualizando",
                f"«{rotulo(sujeto)}» vuelve a actualizarse", [
                    f"*Qué ve la gente:* la card sigue mostrando su último dato bueno"
                    + (f" (dato de {dato})" if dato else "") + ". No hay dato malo: hay dato viejo.",
                    f"*Por qué:* `{sujeto}` falló con `{detalle[:150]}`, que no es un error de red: "
                    "casi seguro es del código, no de la fuente.",
                    "*Qué hacer:* revisar el colector en el run. La serie queda congelada hasta que se arregle.",
                ], huella=f"{sujeto}:{detalle[:150]}"))
        elif tipo == "caida":
            out.append(_problema(
                f"caida:{sujeto}", "🟡", f"el colector `{sujeto}` no trae nada fresco",
                f"el colector `{sujeto}` vuelve a traer datos", [
                    f"*Qué ve la gente:* las cards de `{sujeto}` muestran su último dato bueno.",
                    "*Por qué:* no pudo traer ningún dato nuevo (exit=2): la fuente está caída entera.",
                    "*Qué hacer:* si sigue en la próxima corrida, mirar la fuente en el run.",
                ], huella=sujeto))
        else:
            out.append(_problema(
                f"presupuesto:{sujeto}", "🟡", f"`{sujeto}` se queda sin tiempo y usa caché",
                f"`{sujeto}` vuelve a terminar a tiempo", [
                    "*Qué ve la gente:* lo que no llegó a traer queda con el dato anterior.",
                    f"*Por qué:* `{sujeto}` agotó su presupuesto de tiempo.",
                    "*Qué hacer:* si se repite, ver en el run qué fuente se colgó.",
                ], huella=sujeto))

    por_indicador: dict[str, list[dict]] = {}
    for d in datos_cotejo(log):
        por_indicador.setdefault(d["indicador"], []).append(d)
    for ind, items in por_indicador.items():
        n = len(items)
        cuerpo = [
            "*Qué ve la gente:* nada todavía: estos registros no entran al cálculo hasta cotejarlos.",
            f"*Qué hacer:* {items[0]['motivo']}",
        ]
        cuerpo += [f"• `{d['registro']}` — {d['fuente']}" for d in items[:TOPE_COTEJOS]]
        if n > TOPE_COTEJOS:
            cuerpo.append(f"  …y {n - TOPE_COTEJOS} más, en el run.")
        out.append(_problema(
            f"cotejo:{ind}", "🟡",
            f"«{rotulo(ind)}» tiene {n} registro{'s' if n > 1 else ''} para cotejar a mano",
            f"«{rotulo(ind)}» ya no tiene registros para cotejar", cuerpo, huella="\n".join(sorted(d["registro"] for d in items))))

    archivo = analizar_bigquery(log_bq, estado_bq)
    if archivo:
        out.append(_problema(
            "bigquery", "🟡", "la corrida no queda en el archivo histórico (BigQuery)",
            "la corrida vuelve a quedar en el archivo histórico", ["*Qué ve la gente:* nada, la web está al día."] + [f"*Por qué:* {m}" for m in archivo],
            huella="bigquery"))
    return out


def _cargar(ruta: str) -> dict:
    if ruta and os.path.exists(ruta):
        try:
            return json.loads(Path(ruta).read_text(encoding="utf-8"))
        except ValueError:
            print(f"[aviso] estado ilegible en {ruta}: se arranca de cero", file=sys.stderr)
    return {"problemas": {}}


def _pie(reg: dict, url: str) -> str:
    lleva = f" · lleva {reg['corridas']} corridas" if reg["corridas"] > 1 else ""
    run = f" · <{url}|ver la corrida>" if url else ""
    return f"_Desde el {reg['desde']}{lleva}._{run}"


def _texto_raiz(reg: dict, url: str) -> str:
    return "\n".join([_cabecera(reg["glifo"], reg["titulo"]), *reg["cuerpo"], _pie(reg, url)])


def _corridas(n: int) -> str:
    return f"{n} corrida{'s' if n > 1 else ''}"


def _texto_resuelto(reg: dict) -> str:
    """La raíz, una vez cerrada: qué se arregló, cuánto duró y qué había sido."""
    porque = [l for l in reg["cuerpo"] if l.startswith("*Por qué:*")] or reg["cuerpo"][:1]
    return "\n".join([
        _cabecera("✅", reg.get("resuelto") or f"se resolvió: {reg['titulo']}"),
        f"_Estuvo abierto del {reg['desde']} al {_fecha()} · {_corridas(reg['corridas'])} con el problema._",
        f"> _Era:_ {reg['titulo']}",
        *[f"> {l}" for l in porque],
    ])


def sincronizar(ruta: str, actuales: list[dict], alcance, url: str = "") -> int:
    """Lleva cada problema a su hilo. `alcance(clave)` dice qué claves pudo
    medir esta corrida: sólo esas se pueden dar por resueltas. Una corrida
    caída no mide las degradaciones, así que no las cierra."""
    estado = _cargar(ruta)
    abiertos = estado.setdefault("problemas", {})
    vistas = set()
    for p in actuales:
        clave = p["clave"]
        vistas.add(clave)
        reg = abiertos.get(clave)
        if reg:
            reg["corridas"] += 1
            reg.pop("cierre_publicado", None)       # volvió antes de terminar de cerrarse
            cambio = p["huella"] != reg["huella"]
            reg.update(glifo=p["glifo"], titulo=p["titulo"], resuelto=p["resuelto"],
                       cuerpo=p["cuerpo"], huella=p["huella"])
            if editar(reg["ts"], _texto_raiz(reg, url)) in RAIZ_PERDIDA:
                # Sin raíz el problema quedaría mudo: se abre otra con todo el cuerpo.
                ts = publicar(_texto_raiz(reg, url))
                if ts:
                    reg["ts"] = ts
                continue
            if cambio:
                publicar("\n".join(["*Cambió el diagnóstico:*", *p["cuerpo"]]
                                   + ([f"<{url}|ver la corrida>"] if url else [])),
                         thread_ts=reg["ts"])
            continue
        reg = dict(desde=_fecha(), corridas=1, glifo=p["glifo"], titulo=p["titulo"],
                   resuelto=p["resuelto"], cuerpo=p["cuerpo"], huella=p["huella"])
        ts = publicar(_texto_raiz(reg, url))
        if ts:                              # si Slack no respondió, se reintenta como nuevo
            abiertos[clave] = {**reg, "ts": ts}

    for clave in [c for c in abiertos if alcance(c) and c not in vistas]:
        reg = abiertos[clave]
        # Dos pasos, y cada uno se reintenta por separado: el aviso en el canal
        # no se repite si lo que falló fue sólo la edición de la raíz.
        if not reg.get("cierre_publicado"):
            if not publicar(
                _cabecera("✅", reg.get("resuelto") or f"se resolvió: {reg['titulo']}")
                + f"\nAnduvo en la corrida del {_fecha()}, después de {_corridas(reg['corridas'])} con el problema."
                + (f" <{url}|ver la corrida>" if url else ""),
                thread_ts=reg["ts"], reply_broadcast=True):
                continue                    # sin confirmación queda abierto y se reintenta
            reg["cierre_publicado"] = True
        error = editar(reg["ts"], _texto_resuelto(reg))
        if not error or error in RAIZ_PERDIDA:
            del abiertos[clave]

    if ruta:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        Path(ruta).write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def _corte_despues_de_publicar(a, pasos: list[str]) -> dict:
    """El job se cortó con el snapshot ya en main (14-sep-2026: el tope de 45
    minutos lo cortó en el espejo a BigQuery). Decir «no publicó» sería falso:
    el Monitor está al día, lo que falta es lo que venía después del commit.
    Por eso es 🟡 y cierra el hilo `corrida` si había uno abierto."""
    pendientes = ", ".join(pasos) or "no se pudo determinar"
    cuerpo = [
        f"*Qué ve la gente:* <{MONITOR_URL}|el Monitor> está al día"
        + (f" (corrida {a.sirviendo})" if a.sirviendo else "") + ": la corrida sí publicó.",
        f"*Qué quedó sin hacer:* {pendientes}.",
        "*Qué hacer:* si faltó BigQuery, la corrida se recupera con `bigquery_backfill.py`. "
        "Si se repite, la corrida está rozando el tope de 45 minutos: mirar qué paso se alargó.",
    ]
    if a.estado == "cancelled":
        cuerpo.insert(1, CANCELADO)
    return _problema("cierre", "🟡", "la corrida publicó, pero se cortó antes de terminar",
                     "la corrida vuelve a terminar completa", cuerpo, huella=pendientes)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=["fallo", "reporte", "recuperado", "degradado"])
    p.add_argument("--url", default=os.environ.get("RUN_URL", ""))
    p.add_argument("--pasos", default="")
    p.add_argument("--log", default="")
    p.add_argument("--gates", default="", help="log del gate y de pytest")
    p.add_argument("--bigquery", default="", help="log del espejo en BigQuery")
    p.add_argument("--bigquery-estado", default="",
                   help="steps.bigquery.outcome: success | failure | skipped")
    p.add_argument("--fallas", type=int, default=1,
                   help="cuántas corridas caídas seguidas lleva el aviso abierto")
    p.add_argument("--estado", default="failure", help="job.status: failure | cancelled")
    p.add_argument("--sirviendo", default="", help="generated_at de lo que está en producción")
    p.add_argument("--publico", action="store_true",
                   help="el job se cortó DESPUÉS de dejar el snapshot en main")
    p.add_argument("--archivo-estado", default="",
                   help="JSON con los hilos abiertos (ADR-0309); sin él, cada aviso sale suelto")
    a = p.parse_args()

    if a.modo in ("fallo", "reporte"):
        pasos = [l.lstrip("- ").strip() for l in a.pasos.splitlines() if l.strip()]
        texto_gates = _leer(a.gates)
        texto_cols = _leer(a.log)
        motivos = causas(texto_gates + "\n" + texto_cols)
        cotejos = avisos_cotejo(texto_gates + "\n" + texto_cols)
        cols = colectores(texto_cols)
        resumen = resumen_pytest(texto_gates)

        if a.modo == "reporte":
            return _reporte(a, pasos, motivos, cols, resumen,
                            cola(texto_gates or texto_cols), cotejos)

        cancelado = a.estado == "cancelled"
        if a.publico:
            return sincronizar(a.archivo_estado, [_corte_despues_de_publicar(a, pasos)],
                               lambda c: c in ("corrida", "cierre"), a.url)
        cuerpo = []
        if cancelado:
            cuerpo.append(CANCELADO)
        cuerpo.append("*Paso:* " + (", ".join(pasos) or "no se pudo determinar"))
        if motivos:
            _seccion(cuerpo, "*Qué falló:*", motivos, TOPE_CAUSAS)
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
        _seccion(cuerpo, "*Cotejo manual pendiente:*", cotejos, TOPE_COTEJOS)
        cuerpo.append(
            f"*Qué ve la gente:* <{MONITOR_URL}|el Monitor> sigue mostrando la corrida anterior"
            + (f" ({a.sirviendo})" if a.sirviendo else "")
            + ". No hay dato malo publicado: hay dato viejo."
        )
        cuerpo.append("*Qué hacer:* el diagnóstico completo está en el issue `pipeline-caido` y en el run.")
        titulo = ("la corrida nocturna se corta sin publicar" if cancelado
                  else "la corrida nocturna falla y no publica")
        corrida = _problema("corrida", "🔴", titulo, "la corrida nocturna vuelve a publicar", cuerpo,
                            huella="\n".join(pasos + motivos) or titulo)
        return sincronizar(a.archivo_estado, [corrida], lambda c: c == "corrida", a.url)

    if a.modo == "recuperado":
        return sincronizar(a.archivo_estado, [], lambda c: c == "corrida", a.url)

    # Una corrida que publicó midió todo: lo que no aparece, incluida la
    # corrida caída de antes, se da por resuelto.
    return sincronizar(
        a.archivo_estado,
        problemas_degradado(_leer(a.log), _leer(a.bigquery), a.bigquery_estado),
        lambda c: True, a.url)


if __name__ == "__main__":
    raise SystemExit(main())
