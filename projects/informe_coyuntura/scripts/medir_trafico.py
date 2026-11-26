"""Medición mensual del tráfico del Monitor: GA4 + Search Console (ADR-0440).

Con unos 200 usuarios por mes un A/B no distingue nada del azar, así que se mide
antes y después: un informe por mes, comparado con el anterior y con la lista de
lo que se cambió en el sitio ese mes (los ADR aceptados con esa fecha).

    .venv/bin/python scripts/medir_trafico.py              # el mes anterior
    .venv/bin/python scripts/medir_trafico.py --mes 2026-11

Escribe output/trafico/AAAA-MM.json y AAAA-MM.md. Usa la cuenta de servicio de
GOOGLE_APPLICATION_CREDENTIALS (ga4-informe@cigob-analytics, ADR-0180), que lee
GA4 y Search Console. Habla REST con google-auth: no suma dependencias.
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "output" / "trafico"
ADRS = RAIZ / "docs" / "adr"

PROPIEDAD_GA = "548827028"
HOSTS = ["monitor.cigob.org", "informe.cigob.org", "cigob-informe-coyuntura.vercel.app"]
PROPIEDADES_GSC = ["https://monitor.cigob.org/", "https://informe.cigob.org/"]
EVENTOS = [
    "ver_cinturon", "ver_ficha", "ver_indicador", "ver_dimension", "fijar_dimension",
    "ver_lectura_cinturones", "ver_archivo", "descargar_csv",
    "muro_visto", "muro_cerrado", "muro_enviado", "muro_reconocido",
]
# Preguntas fijas para ver si los asistentes de IA citan al Monitor. Se prueban a
# mano una vez por mes (ChatGPT, Gemini, Perplexity): ninguno da API gratis de
# respuestas con búsqueda, y lo que importa es la misma pregunta mes a mes.
PREGUNTAS_IA = [
    "¿Cómo viene el plan de gobierno de Milei? ¿Hay algún índice que lo mida?",
    "¿Qué indicadores muestran la tensión económica en Argentina este mes?",
    "¿Cuál es la tasa de homicidios en Argentina?",
    "¿Cómo evolucionó el salario real en Argentina en 2026?",
    "¿Cuántas reservas netas tiene el BCRA?",
    "¿Cuántos vetos insistió el Congreso argentino en 2026?",
    "¿Cómo viene el RIGI? ¿Cuántas inversiones aprobó?",
    "¿Qué es el Monitor del Plan de Gobierno de CiGob?",
    "Fundación CiGob monitor",
    "¿Cómo está la gobernabilidad del gobierno argentino según datos?",
]


def rango_del_mes(mes: str) -> tuple[str, str]:
    anio, m = (int(x) for x in mes.split("-"))
    return f"{anio:04d}-{m:02d}-01", f"{anio:04d}-{m:02d}-{calendar.monthrange(anio, m)[1]:02d}"


def mes_anterior(mes: str) -> str:
    anio, m = (int(x) for x in mes.split("-"))
    return f"{anio - 1}-12" if m == 1 else f"{anio:04d}-{m - 1:02d}"


def sesion():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    cred, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/webmasters.readonly",
    ])
    return AuthorizedSession(cred)


def _filtro_hosts() -> dict:
    return {"filter": {"fieldName": "hostName", "inListFilter": {"values": HOSTS}}}


def ga(s, desde: str, hasta: str, dims: list[str], mets: list[str], limite: int = 50, filtro=None) -> list[dict]:
    cuerpo = {
        "dateRanges": [{"startDate": desde, "endDate": hasta}],
        "dimensions": [{"name": d} for d in dims],
        "metrics": [{"name": m} for m in mets],
        "dimensionFilter": filtro or _filtro_hosts(),
        "limit": limite,
    }
    if mets:
        cuerpo["orderBys"] = [{"metric": {"metricName": mets[0]}, "desc": True}]
    r = s.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPIEDAD_GA}:runReport", json=cuerpo)
    r.raise_for_status()
    filas = []
    for f in r.json().get("rows", []):
        fila = {d: v["value"] for d, v in zip(dims, f.get("dimensionValues", []))}
        for m, v in zip(mets, f["metricValues"]):
            fila[m] = round(float(v["value"]), 4)
        filas.append(fila)
    return filas


def _sin_permiso(r) -> bool:
    try:
        error = r.json().get("error", {})
    except ValueError:
        return False
    motivos = {e.get("reason", "") for e in error.get("errors", [])}
    if motivos & {"quotaExceeded", "rateLimitExceeded", "userRateLimitExceeded"}:
        return False
    return "permission" in str(error.get("message", "")).lower() or "forbidden" in motivos


def gsc(s, propiedad: str, desde: str, hasta: str, dims: list[str], limite: int = 20) -> list[dict] | None:
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{quote(propiedad, safe='')}/searchAnalytics/query"
    r = s.post(url, json={"startDate": desde, "endDate": hasta, "dimensions": dims, "rowLimit": limite})
    # Sólo «no tenés esa propiedad» se informa como falta de acceso. Un 403 por cuota
    # o por frecuencia tiene que hacer fallar la corrida, no dejar un informe sin datos.
    if r.status_code == 404 or (r.status_code == 403 and _sin_permiso(r)):
        return None
    r.raise_for_status()
    return [
        {**dict(zip(dims, f.get("keys", []))), "clics": f["clicks"], "impresiones": f["impressions"],
         "ctr": round(f["ctr"], 4), "posicion": round(f["position"], 1)}
        for f in r.json().get("rows", [])
    ]


def medir(s, mes: str) -> dict:
    desde, hasta = rango_del_mes(mes)
    totales = ga(s, desde, hasta, [], ["activeUsers", "newUsers", "sessions", "screenPageViews",
                                       "engagementRate", "averageSessionDuration"])
    eventos = ga(s, desde, hasta, ["eventName"], ["eventCount", "totalUsers"], filtro={"andGroup": {"expressions": [
        _filtro_hosts(), {"filter": {"fieldName": "eventName", "inListFilter": {"values": EVENTOS}}}]}})
    busqueda = {}
    for p in PROPIEDADES_GSC:
        tot = gsc(s, p, desde, hasta, [], 1)
        if tot is None:
            busqueda[p] = None
            continue
        busqueda[p] = {
            "totales": tot[0] if tot else {"clics": 0, "impresiones": 0, "ctr": 0, "posicion": None},
            "consultas": gsc(s, p, desde, hasta, ["query"]),
            "paginas": gsc(s, p, desde, hasta, ["page"]),
        }
    return {
        "mes": mes,
        "totales": totales[0] if totales else {},
        "por_host": ga(s, desde, hasta, ["hostName"], ["activeUsers", "sessions"]),
        "origenes": ga(s, desde, hasta, ["sessionSource", "sessionMedium", "sessionCampaignName"],
                       ["sessions", "activeUsers", "engagementRate"], 25),
        "paginas": ga(s, desde, hasta, ["pagePath"], ["screenPageViews", "activeUsers"], 20),
        "eventos": {e["eventName"]: {"veces": int(e["eventCount"]), "usuarios": int(e["totalUsers"])} for e in eventos},
        "busqueda": busqueda,
        "cambios": cambios_del_mes(mes),
    }


def cambios_del_mes(mes: str) -> list[str]:
    """Los ADR de presentación aceptados ese mes: lo que cambió en el sitio y puede
    explicar una diferencia de tráfico. Los de cálculo mueven números, no visitas."""
    salida = []
    for f in sorted(ADRS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        texto = f.read_text(encoding="utf-8")
        fecha = re.search(r"^fecha:\s*'?(\d{4}-\d{2})", texto, re.M)
        titulo = re.search(r"^# (ADR-\d+ — .+)$", texto, re.M)
        ambito = re.search(r"^ambito:\s*'?Presentaci", texto, re.M)
        if fecha and fecha.group(1) == mes and titulo and ambito:
            salida.append(titulo.group(1))
    return salida


def _variacion(ahora, antes) -> str:
    if antes in (None, 0):
        return ""
    return f" ({(ahora - antes) / antes:+.0%})"


def _origen(o: dict) -> str:
    fuente, medio = o.get("sessionSource", ""), o.get("sessionMedium", "")
    if fuente == "(direct)":
        return "Directo (sin dato de origen)"
    if fuente == "whatsapp":
        return f"WhatsApp · {o.get('sessionCampaignName', '')}"
    if "chatgpt" in fuente or medio == "ai-assistant":
        return f"IA · {fuente}"
    if medio == "organic":
        return f"Buscador · {fuente}"
    return f"{fuente} / {medio}"


def informe_md(d: dict, previo: dict | None) -> str:
    t, tp = d["totales"], (previo or {}).get("totales", {})
    l = [f"# Tráfico del Monitor — {d['mes']}", ""]
    l += ["| | Este mes | Mes anterior |", "|---|---|---|"]
    for clave, rotulo in [("activeUsers", "Usuarios"), ("newUsers", "Nuevos"), ("sessions", "Sesiones"),
                          ("screenPageViews", "Páginas vistas")]:
        a, b = t.get(clave, 0), tp.get(clave)
        l.append(f"| {rotulo} | {a:.0f}{_variacion(a, b)} | {'' if b is None else f'{b:.0f}'} |")
    a, b = t.get("engagementRate", 0), tp.get("engagementRate")
    l.append(f"| Interacción | {a:.0%} | {'' if b is None else f'{b:.0%}'} |")
    l += ["", "## De dónde llegan", "", "| Origen | Sesiones | Usuarios | Interacción |", "|---|---|---|---|"]
    for o in d["origenes"][:12]:
        l.append(f"| {_origen(o)} | {o['sessions']:.0f} | {o['activeUsers']:.0f} | {o['engagementRate']:.0%} |")
    l += ["", "## Búsqueda (Search Console)", ""]
    for p, b in d["busqueda"].items():
        if b is None:
            l.append(f"- {p}: la cuenta de servicio no tiene acceso a esta propiedad.")
            continue
        tt = b["totales"]
        l.append(f"- {p}: {tt['clics']:.0f} clics, {tt['impresiones']:.0f} apariciones, "
                 f"posición media {tt['posicion'] if tt['posicion'] is not None else '—'}.")
        for q in (b["consultas"] or [])[:10]:
            l.append(f"  - «{q['query']}»: {q['clics']:.0f} clics, {q['impresiones']:.0f} apariciones, puesto {q['posicion']}")
    l += ["", "## Páginas más vistas", "", "| Página | Vistas | Usuarios |", "|---|---|---|"]
    for p in d["paginas"][:12]:
        l.append(f"| {p['pagePath']} | {p['screenPageViews']:.0f} | {p['activeUsers']:.0f} |")
    ev, evp = d["eventos"], (previo or {}).get("eventos", {})
    l += ["", "## Eventos y muro", "", "| Evento | Veces | Usuarios | Mes anterior (usuarios) |", "|---|---|---|---|"]
    for e in EVENTOS:
        if e in ev or e in evp:
            a = ev.get(e, {"veces": 0, "usuarios": 0})
            b = evp.get(e, {}).get("usuarios", "")
            l.append(f"| {e} | {a['veces']} | {a['usuarios']} | {b} |")
    vistos, enviados = ev.get("muro_visto", {}).get("usuarios", 0), ev.get("muro_enviado", {}).get("usuarios", 0)
    if vistos:
        l.append(f"\nDel muro: {enviados} de {vistos} personas que lo vieron dejaron el mail ({enviados / vistos:.0%}).")
    l += ["", "## Qué se cambió en el sitio este mes", ""]
    l += [f"- {c}" for c in d["cambios"]] or ["- Ningún cambio de presentación (ADR) con fecha de este mes."]
    l += ["", "## Preguntas fijas a la IA (probar a mano)", "",
          "Hacer cada pregunta en ChatGPT, Gemini y Perplexity y anotar si citan al Monitor y con qué link.", ""]
    l += [f"{i}. {q}" for i, q in enumerate(PREGUNTAS_IA, 1)]
    return "\n".join(l) + "\n"


def main() -> int:
    hoy = date.today()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mes", default=mes_anterior(f"{hoy.year:04d}-{hoy.month:02d}"))
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}", args.mes):
        print("ERROR: --mes va como AAAA-MM", file=sys.stderr)
        return 2
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: falta GOOGLE_APPLICATION_CREDENTIALS", file=sys.stderr)
        return 2

    s = sesion()
    datos = medir(s, args.mes)
    ruta_previa = SALIDA / f"{mes_anterior(args.mes)}.json"
    previo = json.loads(ruta_previa.read_text(encoding="utf-8")) if ruta_previa.exists() else medir(s, mes_anterior(args.mes))
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / f"{args.mes}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SALIDA / f"{args.mes}.md").write_text(informe_md(datos, previo), encoding="utf-8")
    print(f"output/trafico/{args.mes}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
