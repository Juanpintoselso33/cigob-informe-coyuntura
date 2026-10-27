"""Corpus de títulos de prensa argentina que nombran al Presidente.

Insumo del indicador «tono con que la prensa trata al Presidente» (índice
político). Esta fase arma SÓLO el corpus y los lotes para los lectores: no
clasifica. El manual vive en data/politica/prensa_presidente_reglas.json y se
escribió antes de que nadie leyera los títulos de la muestra para clasificar.

Fuente: GDELT GKG en BigQuery (`gdelt-bq.gdeltv2.gkg_partitioned`). Una nota
entra si su dominio es argentino y «milei» aparece en la URL; el título sale de
la etiqueta <PAGE_TITLE> de `Extras`. Es una medida de titulares/URL, no de
menciones en el cuerpo.

Uso:
    .venv/bin/python scripts/prensa_presidente.py --dry-run
    .venv/bin/python scripts/prensa_presidente.py --cache RUTA.json [--lotes DIR]

`--cache` guarda el resultado crudo de BigQuery y lo reutiliza: la consulta
completa cuesta cientos de GB, no se repite para volver a muestrear.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "data" / "politica" / "prensa_presidente_muestra.json"
CORPUS_HISTORIA = RAIZ / "data" / "politica" / "prensa_presidente_historia.json"

PROYECTO_BQ = "cigob-analytics"
TABLA_GKG = "gdelt-bq.gdeltv2.gkg_partitioned"
DESDE = "2023-12-01"
TAMANO_MUESTRA = 200
SEMILLA = "prensa-presidente-v1"
TAMANO_LOTE = 400

# Cómo se armó la lista de dominios: (1) los nacionales grandes que el informe
# ya usa para medir cobertura (consulta de factibilidad del 27-oct-2026,
# politicos_prensa.md): infobae, clarín, perfil, cronista, ámbito, que no
# terminan en .ar; (2) todo lo que GDELT indexa bajo .ar, que incluye La
# Nación, Página/12, TN y la prensa provincial. Se excluyen los .ar que no son
# prensa (gobierno, universidades, militares). La lista efectiva de dominios
# con notas queda registrada en _meta.dominios_observados.
DOMINIOS_NO_AR = ("infobae.com", "clarin.com", "perfil.com", "cronista.com", "ambito.com")
SUFIJOS_EXCLUIDOS = (".gob.ar", ".gov.ar", ".edu.ar", ".mil.ar", ".int.ar")
DOMINIOS_NACIONALES = (
    "infobae.com", "clarin.com", "perfil.com", "cronista.com", "ambito.com",
    "lanacion.com.ar", "pagina12.com.ar", "tn.com.ar", "eleconomista.com.ar",
    "cronica.com.ar", "laprensa.com.ar", "diariopopular.com.ar",
)

# Criterio de cobertura incompleta: el total de artículos .ar que GDELT
# indexó en el mes (con o sin Milei) cae por debajo de esta fracción de la
# mediana de la serie. Junio 2025 tiene ~53 mil contra ~115 mil: 0,46.
UMBRAL_COBERTURA = 0.75

# Presidentes anteriores, para que los cortes de la escala no salgan sólo del
# mandato que se evalúa (la regla de ADR-0388 y ADR-0390). Mismo criterio de
# entrada que Milei: el apellido en la URL. Cada nota se asigna al presidente
# en funciones el día que se publicó, así una nota sobre Macri ya ex
# presidente no entra en el período de Fernández. «alberto» va pegado al
# apellido para no traer a Cristina Fernández de Kirchner.
PRESIDENTES_PREVIOS = (
    ("macri", "Mauricio Macri", "2015-12-10", "2019-12-10", r"macri"),
    ("fernandez", "Alberto Fernández", "2019-12-10", "2023-12-10", r"alberto[-_]?fern"),
)
HISTORIA_DESDE, HISTORIA_HASTA = "2015-12-10", "2023-12-01"
TAMANO_MUESTRA_HISTORIA = 17   # 96 meses x 17 = unos 1.600 títulos


def sql(desde: str, hasta: str, patron: str = "milei") -> str:
    """Una sola pasada: una fila por nota con «milei» en la URL, más una fila
    de totales por mes (para marcar cobertura incompleta)."""
    lista = ", ".join(f"'{d}'" for d in DOMINIOS_NO_AR)
    excl = " AND ".join(f"NOT ENDS_WITH(SourceCommonName, '{s}')" for s in SUFIJOS_EXCLUIDOS)
    return f"""
WITH b AS (
  SELECT SAFE_CAST(DATE AS INT64) AS fecha_n, SourceCommonName AS dominio,
         DocumentIdentifier AS url, Extras AS extras
  FROM `{TABLA_GKG}`
  WHERE _PARTITIONTIME >= TIMESTAMP("{desde}") AND _PARTITIONTIME < TIMESTAMP("{hasta}")
    AND (ENDS_WITH(SourceCommonName, '.ar') OR SourceCommonName IN ({lista}))
    AND {excl}
)
SELECT 'total' AS tipo, CAST(DIV(fecha_n, 100000000) AS STRING) AS mes,
       NULL AS fecha, NULL AS dominio, NULL AS url, NULL AS titulo, COUNT(*) AS n
FROM b GROUP BY mes
UNION ALL
SELECT 'nota', CAST(DIV(MIN(fecha_n), 100000000) AS STRING),
       CAST(DIV(MIN(fecha_n), 1000000) AS STRING), ANY_VALUE(dominio), url,
       MAX(NULLIF(TRIM(REGEXP_EXTRACT(extras, r'<PAGE_TITLE>(.*?)</PAGE_TITLE>')), '')), COUNT(*)
FROM b WHERE REGEXP_CONTAINS(LOWER(url), r'{patron}')
GROUP BY url
""".strip()


# ---------------------------------------------------------------- BigQuery
def _cliente():
    from google.cloud import bigquery
    return bigquery.Client(project=PROYECTO_BQ)


def dry_run(desde: str, hasta: str, cliente=None, patron: str = "milei") -> int:
    from google.cloud import bigquery
    cliente = cliente or _cliente()
    job = cliente.query(sql(desde, hasta, patron), job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    return int(job.total_bytes_processed)


def consultar(desde: str, hasta: str, cliente=None, patron: str = "milei") -> dict:
    """Devuelve {'filas': [...], 'bytes_facturados': int}."""
    cliente = cliente or _cliente()
    job = cliente.query(sql(desde, hasta, patron))
    filas = [dict(r.items()) for r in job.result()]
    return {"filas": filas, "bytes_facturados": int(job.total_bytes_billed or 0)}


# ------------------------------------------------------------ procesamiento
def _mes(m: str) -> str:
    m = str(m)
    return f"{m[:4]}-{m[4:6]}"


def _fecha(f: str) -> str:
    f = str(f)
    return f"{f[:4]}-{f[4:6]}-{f[6:8]}"


def normalizar_url(url: str) -> str:
    u = url.strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.split(r"[?#]", u)[0]
    return u.rstrip("/")


def normalizar_titulo(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(t)).strip().lower()


def limpiar_titulo(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def id_nota(url: str) -> str:
    return hashlib.sha256(normalizar_url(url).encode()).hexdigest()[:12]


def depurar(filas: list[dict]) -> tuple[list[dict], dict]:
    """Descarta sin título, deduplica por URL (en toda la serie) y por título
    idéntico (dentro del mes: el mismo titular de agencia en otro mes es otra
    nota). Conserva la más antigua. Devuelve (notas, conteos por mes)."""
    conteo = defaultdict(lambda: {"crudas": 0, "sin_titulo": 0, "duplicadas_url": 0,
                                  "duplicadas_titulo": 0, "universo": 0})
    notas = sorted((f for f in filas if f["tipo"] == "nota"),
                   key=lambda f: (str(f["fecha"]), normalizar_url(f["url"])))
    vistas_url, vistos_titulo, salida = set(), set(), []
    for f in notas:
        mes = _mes(f["mes"])
        c = conteo[mes]
        c["crudas"] += 1
        titulo = limpiar_titulo(f["titulo"]) if f.get("titulo") else ""
        if not titulo:
            c["sin_titulo"] += 1
            continue
        u = normalizar_url(f["url"])
        if u in vistas_url:
            c["duplicadas_url"] += 1
            continue
        clave_t = (mes, normalizar_titulo(titulo))
        if clave_t in vistos_titulo:
            c["duplicadas_titulo"] += 1
            continue
        vistas_url.add(u)
        vistos_titulo.add(clave_t)
        c["universo"] += 1
        salida.append({"id": id_nota(f["url"]), "mes": mes, "fecha": _fecha(f["fecha"]),
                       "dominio": f["dominio"], "url": f["url"].strip(), "titulo": titulo})
    return salida, dict(conteo)


def _orden(id_: str, mes: str, semilla: str) -> str:
    return hashlib.sha256(f"{semilla}|{mes}|{id_}".encode()).hexdigest()


def muestrear_mes(notas: list[dict], n: int, semilla: str, mes: str) -> list[dict]:
    """Muestra estratificada por dominio, proporcional a su peso en el mes
    (método del mayor resto). Dentro de cada dominio se toman las notas de
    menor hash(semilla|mes|id): no depende del orden de entrada ni del estado
    de ningún generador, así que es estable entre corridas y máquinas."""
    if len(notas) <= n:
        return sorted(notas, key=lambda x: x["id"])
    por_dom = defaultdict(list)
    for x in notas:
        por_dom[x["dominio"]].append(x)
    total = len(notas)
    cupo = {d: n * len(v) / total for d, v in por_dom.items()}
    base = {d: int(c) for d, c in cupo.items()}
    resto = n - sum(base.values())
    for d in sorted(cupo, key=lambda d: (-(cupo[d] - base[d]), _orden(d, mes, semilla)))[:resto]:
        base[d] += 1
    elegidas = []
    for d, v in por_dom.items():
        v.sort(key=lambda x: _orden(x["id"], mes, semilla))
        elegidas.extend(v[:base[d]])
    return sorted(elegidas, key=lambda x: x["id"])


def meses_incompletos(totales: dict[str, int]) -> dict[str, dict]:
    if not totales:
        return {}
    med = statistics.median(totales.values())
    return {m: {"articulos_ar": t, "fraccion_de_la_mediana": round(t / med, 2)}
            for m, t in sorted(totales.items()) if t < UMBRAL_COBERTURA * med}


def armar_corpus(crudo: dict, desde: str, hasta: str, n: int = TAMANO_MUESTRA,
                 semilla: str = SEMILLA) -> dict:
    filas = crudo["filas"]
    notas, conteo = depurar(filas)
    totales = {_mes(f["mes"]): int(f["n"]) for f in filas if f["tipo"] == "total"}
    incompletos = meses_incompletos(totales)
    por_mes = defaultdict(list)
    for x in notas:
        por_mes[x["mes"]].append(x)
    muestra, meses = [], {}
    for mes in sorted(conteo):
        m = muestrear_mes(por_mes[mes], n, semilla, mes)
        muestra.extend(m)
        meses[mes] = {**conteo[mes], "muestra": len(m), "articulos_ar_gdelt": totales.get(mes),
                      "cobertura_incompleta": mes in incompletos}
    return {
        "_meta": {
            "descripcion": "Títulos de notas de medios argentinos que nombran a Milei en la URL, muestra mensual para clasificar el tono hacia el Presidente o su Gobierno. Sólo título: sin texto completo.",
            "fuente": f"GDELT GKG en BigQuery ({TABLA_GKG})",
            "periodo": {"desde": desde, "hasta_exclusivo": hasta},
            "consulta": sql(desde, hasta),
            "titulo": "etiqueta <PAGE_TITLE> de Extras; sin título la nota se descarta y se cuenta (sin_titulo)",
            "deduplicacion": "por URL normalizada (sin esquema, www, query ni barra final) en toda la serie; por título idéntico (sin mayúsculas ni espacios de más) dentro del mes. Se conserva la nota más antigua.",
            "muestreo": {
                "tamano_por_mes": n,
                "semilla": semilla,
                "regla": "estratificada por dominio, proporcional al peso del dominio en el universo del mes (mayor resto). Dentro de cada dominio se toman las notas de menor sha256(semilla|mes|id), estable e independiente del orden. Mes con universo <= tamano: se toma todo. Un dominio chico puede quedar sin notas en la muestra.",
                "por_que_proporcional": "el universo es lo que la prensa publicó; la muestra proporcional lo reproduce en chico. Un medio grande pesa en la muestra lo que pesa en la cobertura, no más.",
            },
            "criterio_cobertura_incompleta": f"el total de artículos .ar indexados por GDELT en el mes es menor a {UMBRAL_COBERTURA} de la mediana de la serie (junio 2025 llega a 0,46). Esos meses se muestrean igual pero se marcan.",
            "dominios_filtro": {
                "no_ar_incluidos": list(DOMINIOS_NO_AR),
                "sufijo_incluido": ".ar",
                "sufijos_excluidos": list(SUFIJOS_EXCLUIDOS),
                "nacionales_grandes": list(DOMINIOS_NACIONALES),
            },
            "dominios_observados": dict(Counter(x["dominio"] for x in notas).most_common()),
            "meses_incompletos": incompletos,
            "meses": meses,
            "bytes_facturados": crudo.get("bytes_facturados"),
            "id": "sha256 de la URL normalizada, 12 caracteres",
        },
        "notas": muestra,
    }


def titulo_desde_url(url: str) -> str:
    """Título reconstruido del slug de la URL, para las notas sin <PAGE_TITLE>
    (GDELT lo guarda recién desde sep-2019). Toma el tramo con más palabras
    separadas por guiones, saca ids, fechas y extensiones. Devuelve "" si
    quedan menos de cinco palabras: un slug corto no alcanza para leer tono."""
    u = re.split(r"[?#]", url)[0] if "option=com_content" not in url else url
    m = re.search(r"id=\d+:([^&]+)", u)
    tramos = [m.group(1)] if m else re.split(r"/", re.sub(r"^https?://[^/]+", "", u))
    mejor = ""
    for t in tramos:
        t = re.sub(r"\.(html?|phtml|php|aspx?)$", "", t, flags=re.I)
        t = re.sub(r"_0_\d+$|-[A-Z]{2}\d+$|,[a-z0-9]+$", "", t)
        palabras = [p for p in re.split(r"[-_]+", t) if p and not re.fullmatch(r"[a-z]?\d+[a-z]?\d*|n\d+", p.lower())]
        if len(palabras) > len(mejor.split()):
            mejor = " ".join(palabras)
    mejor = mejor.lower()
    return mejor[:1].upper() + mejor[1:] if len(mejor.split()) >= 5 else ""


def agregar_meses(corpus: dict, nuevo: dict) -> dict:
    """Suma al corpus del mandato los meses de `nuevo` (la carga mensual), sin
    volver a consultar la serie entera. Un mes ya presente no se pisa. La
    cobertura incompleta del mes nuevo se juzga contra la mediana de toda la
    serie, no contra sí mismo."""
    meta, meses = corpus["_meta"], corpus["_meta"]["meses"]
    agregados = [m for m in sorted(nuevo["_meta"]["meses"]) if m not in meses]
    ids = {x["id"] for x in corpus["notas"]}
    totales = {m: v["articulos_ar_gdelt"] for m, v in meses.items() if v.get("articulos_ar_gdelt")}
    for m in agregados:
        meses[m] = nuevo["_meta"]["meses"][m]
        if meses[m].get("articulos_ar_gdelt"):
            totales[m] = meses[m]["articulos_ar_gdelt"]
    incompletos = meses_incompletos(totales)
    for m in agregados:
        meses[m]["cobertura_incompleta"] = m in incompletos
    meta["meses_incompletos"] = {m: v for m, v in incompletos.items()}
    corpus["notas"].extend(x for x in nuevo["notas"] if x["mes"] in agregados and x["id"] not in ids)
    meta["periodo"]["hasta_exclusivo"] = max(meta["periodo"]["hasta_exclusivo"], nuevo["_meta"]["periodo"]["hasta_exclusivo"])
    meta.setdefault("cargas_mensuales", []).append({"meses": agregados, "bytes_facturados": nuevo["_meta"].get("bytes_facturados")})
    return corpus


def patron_historia() -> str:
    return "|".join(p[4] for p in PRESIDENTES_PREVIOS)


def presidente_de(fecha: str, url: str) -> str | None:
    """El presidente en funciones ese día, si la URL lo nombra; si no, None."""
    for clave, _, desde, hasta, patron in PRESIDENTES_PREVIOS:
        if desde <= fecha < hasta:
            return clave if re.search(patron, url.lower()) else None
    return None


def armar_historia(crudo: dict, n: int = TAMANO_MUESTRA_HISTORIA, semilla: str = SEMILLA) -> dict:
    """Mismo depurado y muestreo que el mandato, con las notas filtradas al
    presidente en funciones. Se reutiliza armar_corpus para no duplicar reglas."""
    filas = []
    for f in crudo["filas"]:
        if f["tipo"] == "nota":
            clave = presidente_de(_fecha(f["fecha"]), f["url"])
            if clave is None:
                continue
            f = {**f, "presidente": clave}
            if not (f.get("titulo") or "").strip():
                f["titulo"] = titulo_desde_url(f["url"])
                f["titulo_de_url"] = True
        filas.append(f)
    corpus = armar_corpus({**crudo, "filas": filas}, HISTORIA_DESDE, HISTORIA_HASTA, n, semilla)
    pres = {}
    for f in filas:
        if f["tipo"] == "nota":
            pres[id_nota(f["url"])] = f["presidente"]
    de_url = {id_nota(f["url"]) for f in filas if f.get("titulo_de_url")}
    for x in corpus["notas"]:
        x["presidente"] = pres[x["id"]]
        if x["id"] in de_url:
            x["titulo_de_url"] = True
    m = corpus["_meta"]
    m["descripcion"] = ("Títulos de notas de medios argentinos que nombran en la URL al presidente en funciones "
                        "(Macri o Alberto Fernández), muestra mensual para fijar la escala con la historia previa al mandato.")
    m["consulta"] = sql(HISTORIA_DESDE, HISTORIA_HASTA, patron_historia())
    m["titulo_de_url"] = ("GDELT guarda <PAGE_TITLE> recién desde sep-2019. Antes, el título se reconstruye del slug "
                          "de la URL (titulo_desde_url), en minúsculas y sin tildes; los slugs de menos de cinco palabras se "
                          "descartan. Las notas así marcadas llevan titulo_de_url=true.")
    m["presidentes"] = [{"clave": c, "nombre": n_, "desde": d, "hasta_exclusivo": h, "patron_url": p}
                        for c, n_, d, h, p in PRESIDENTES_PREVIOS]
    return corpus


def escribir_lotes(corpus: dict, destino: Path, tamano: int = TAMANO_LOTE, semilla: str = SEMILLA) -> int:
    """Lotes de unos `tamano` títulos, mezclados con la semilla para que un lote
    no sea un solo mes ni un solo medio. Sin URL, para no sesgar por medio."""
    destino.mkdir(parents=True, exist_ok=True)
    notas = sorted(corpus["notas"], key=lambda x: _orden(x["id"], "lotes", semilla))
    k = max(1, round(len(notas) / tamano))
    indice = []
    for i in range(k):
        parte = notas[i::k]
        nombre = f"lote_{i + 1:02d}.json"
        (destino / nombre).write_text(json.dumps(
            [{"id": x["id"], "mes": x["mes"], "dominio": x["dominio"], "titulo": x["titulo"],
              **({"presidente": x["presidente"]} if "presidente" in x else {})} for x in parte],
            ensure_ascii=False, indent=1), encoding="utf-8")
        indice.append({"archivo": nombre, "titulos": len(parte)})
    (destino / "INDICE.json").write_text(json.dumps(
        {"total_titulos": len(notas), "lotes": indice}, ensure_ascii=False, indent=1), encoding="utf-8")
    return k


def ultimo_mes_cerrado_fin(hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    return hoy.replace(day=1).isoformat()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--desde", default=DESDE)
    ap.add_argument("--hasta", default=None, help="exclusivo; por defecto el 1.º del mes en curso")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache", type=Path, help="JSON con el resultado crudo; se reutiliza si existe")
    ap.add_argument("--lotes", type=Path)
    ap.add_argument("--salida", type=Path, default=None)
    ap.add_argument("--historico", action="store_true", help="Macri y Alberto Fernández (2015-12 a 2023-11)")
    ap.add_argument("--mes", help="carga mensual AAAA-MM: consulta sólo ese mes y lo suma al corpus del mandato")
    a = ap.parse_args(argv)
    hasta = a.hasta or ultimo_mes_cerrado_fin()
    patron = "milei"
    if a.historico:
        a.desde, hasta, patron = HISTORIA_DESDE, HISTORIA_HASTA, patron_historia()
    a.salida = a.salida or (CORPUS_HISTORIA if a.historico else CORPUS)
    if a.mes:
        y, m = map(int, a.mes.split("-"))
        a.desde = f"{y}-{m:02d}-01"
        hasta = f"{y + (m == 12)}-{m % 12 + 1:02d}-01"
    if a.dry_run:
        b = dry_run(a.desde, hasta, patron=patron)
        print(f"dry run: {b} bytes ({b / 1e9:.1f} GB)")
        return 0
    if a.cache and a.cache.exists():
        crudo = json.loads(a.cache.read_text(encoding="utf-8"))
    else:
        crudo = consultar(a.desde, hasta, patron=patron)
        if a.cache:
            a.cache.write_text(json.dumps(crudo, ensure_ascii=False, default=str), encoding="utf-8")
    corpus = armar_historia(crudo) if a.historico else armar_corpus(crudo, a.desde, hasta)
    if a.mes:
        lote = corpus
        corpus = agregar_meses(json.loads(a.salida.read_text(encoding="utf-8")), corpus)
        if a.lotes:   # el lote del mes para los dos lectores, no el corpus entero
            print(f"{escribir_lotes(lote, a.lotes)} lotes del mes en {a.lotes}")
            a.lotes = None
    a.salida.write_text(json.dumps(corpus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(corpus['notas'])} títulos en {a.salida}")
    if a.lotes:
        print(f"{escribir_lotes(corpus, a.lotes)} lotes en {a.lotes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
