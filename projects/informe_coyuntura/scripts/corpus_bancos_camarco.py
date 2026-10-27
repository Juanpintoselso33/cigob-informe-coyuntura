"""Corpus de bancos (ADEBA, ABA, ABAPPRA) y CAMARCO, sin clasificar (ADR-0391).

Baja los cuatro sitios, deduplica los bancos (un comunicado, una vez, con todas
las firmantes), archiva sin clasificar los informes periódicos por la regla de
título de `politica.py` y escribe:

  data/politica/apoyo_bancos_camarco_corpus.json        notas a clasificar + archivadas
  data/politica/apoyo_bancos_camarco_relevamiento.json  URL y volumen por año y mes
  <--lotes>/lote_NN.json                                tramos de ~60 para los lectores

No toca ningún perímetro ni ningún índice. Uso:

  .venv/bin/python scripts/corpus_bancos_camarco.py --lotes <directorio>
"""
import argparse
import collections
import json
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import politica  # noqa: E402

MANUAL = "data/politica/apoyo_empresario_reglas.json"
TAMANO_LOTE = 60
ENTIDADES = {
    "ADEBA": ("Asociación de Bancos Argentinos", "https://www.adeba.com.ar/category/comunicados/",
              "API WordPress, categoría «comunicados» (id 255); el feed general se descarta por estar lleno de «Síntesis normativa»"),
    "ABA": ("Asociación de Bancos de la Argentina", "https://aba-argentina.com/category/comunicados/",
            "API WordPress, categorías «Comunicados ABA» (103), «Gacetillas» (101) y «Prensa» (107); sin «Capacitaciones», «Informes», «Columnas» ni «Artículos»"),
    "ABAPPRA": ("Asociación de Bancos Públicos y Privados", politica.ABAPPRA_COMUNICADOS_URL,
                "HTML de una sola página, sin paginar; entradas separadas por <hr>, título = primer texto en negrita"),
    "CAMARCO": ("Cámara Argentina de la Construcción", "https://www.camarco.org.ar/noticias",
                "API WordPress /wp-json/wp/v2/posts paginada; mezcla agenda, cursos, delegaciones y comunicados"),
}


def volumen(notas):
    por_anio = collections.Counter(n["fecha"][:4] for n in notas)
    por_mes = collections.Counter(n["fecha"][:7] for n in notas)
    return dict(sorted(por_anio.items())), dict(sorted(por_mes.items()))


def relevamiento(res):
    crudas = res["crudas"]
    cams = {}
    for cam, (nombre, url, metodo) in ENTIDADES.items():
        notas = crudas[cam]
        anio, mes = volumen(notas)
        cams[cam] = {"nombre": nombre, "url_listado": url, "metodo": metodo,
                     "descargadas": len(notas),
                     "desde": min((n["fecha"] for n in notas), default=None),
                     "hasta": max((n["fecha"] for n in notas), default=None),
                     "por_anio": anio, "por_mes": mes}
    bancos, camarco, arch = res["bancos"], res["camarco"], res["archivados"]
    anio_b, mes_b = volumen(bancos)
    anio_c, mes_c = volumen(camarco)
    arch_b = [a for a in arch if a["camara"] == "BANCOS"]
    arch_c = [a for a in arch if a["camara"] == "CAMARCO"]
    descargadas_b = sum(len(crudas[c]) for c in ("ADEBA", "ABA", "ABAPPRA"))
    return {
        "_meta": {
            "descripcion": "Relevamiento del corpus de bancos (ADEBA, ABA, ABAPPRA como un solo sector) y CAMARCO, sin clasificar (ADR-0391).",
            "fecha": date.today().isoformat(),
            "decision": "Juan, 27-oct-2026: los bancos son un solo sector y cada comunicado cuenta una vez aunque lo firmen varias cámaras; CAMARCO se clasifica pero queda fuera del cálculo, como CAME, hasta llegar a 4 comunicados con postura dirigidos al Ejecutivo nacional en 12 meses.",
            "desde": politica.APOYO_BANCOS_CAMARCO_DESDE,
            "estado": "corpus sin clasificar: los dos lectores ciegos todavía no leyeron nada",
        },
        "camaras": cams,
        "bancos_compuesto": {
            "descargadas": descargadas_b,
            "tras_deduplicar": len(bancos) + len(arch_b),
            "duplicados_eliminados": descargadas_b - len(bancos) - len(arch_b),
            "archivadas_por_regla_de_titulo": len(arch_b),
            "a_clasificar": len(bancos),
            "con_mas_de_una_firmante": sum(1 for n in bancos if len(n["firmantes"]) > 1),
            "g6": sum(1 for n in bancos if n["g6"]),
            "por_anio": anio_b, "por_mes": mes_b,
        },
        "camarco": {
            "descargadas": len(crudas["CAMARCO"]),
            "archivadas_por_regla_de_titulo_o_categoria": len(arch_c),
            "a_clasificar": len(camarco),
            "g6": sum(1 for n in camarco if n["g6"]),
            "por_anio": anio_c, "por_mes": mes_c,
        },
    }


def lotes(res, destino: Path):
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob("lote_*.json"):
        viejo.unlink()
    filas = []
    for n in sorted(res["bancos"] + res["camarco"], key=lambda n: (n["camara"], n["fecha"], n["id"])):
        filas.append({"id": f"{n['camara']}:{n['id']}", "entidad": n["camara"],
                      "firmantes": n["firmantes"], "fecha": n["fecha"], "titulo": n["titulo"],
                      "texto": n["texto"]})
    n_lotes = max(1, -(-len(filas) // TAMANO_LOTE))
    tam = -(-len(filas) // n_lotes)             # tramos parejos, de unas 60 notas
    indice = []
    for i in range(n_lotes):
        tramo = filas[i * tam:(i + 1) * tam]
        nombre = f"lote_{i + 1:02d}.json"
        (destino / nombre).write_text(json.dumps(tramo, ensure_ascii=False, indent=1), encoding="utf-8")
        indice.append({"archivo": nombre, "notas": len(tramo),
                       "entidades": dict(collections.Counter(f["entidad"] for f in tramo))})
    (destino / "INDICE.json").write_text(json.dumps({"manual": MANUAL, "lotes": indice}, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    return indice


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lotes", required=True, help="directorio de salida de los lotes para los lectores")
    args = ap.parse_args()
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    res = politica.construir_corpus_bancos_camarco(s)
    corpus = {
        "_meta": {
            "descripcion": "Corpus SIN clasificar de bancos (ADEBA + ABA + ABAPPRA, deduplicado) y CAMARCO (ADR-0391). Sin columnas de postura ni destinatario: las agregan los dos lectores ciegos y la adjudicación. Mismo formato que los registros del comercio y el campo.",
            "fecha": date.today().isoformat(),
            "manual": MANUAL,
            "regla_informes_bancos": politica.APOYO_BANCOS_ESTADISTICO.pattern,
            "regla_informes_camarco": {"titulo": politica.APOYO_CAMARCO_ESTADISTICO.pattern,
                                       "categorias_wordpress": sorted(politica.APOYO_CAMARCO_CATEGORIAS_ARCHIVADAS)},
            "g6": "g6: true marca los comunicados del G6 publicados en estos sitios; no se excluyen todavía.",
        },
        "casos": res["bancos"] + res["camarco"],
        "archivados_estadisticos": res["archivados"],
    }
    politica.APOYO_BANCOS_CAMARCO_CORPUS_PATH.write_text(json.dumps(corpus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rel = relevamiento(res)
    politica.APOYO_BANCOS_CAMARCO_RELEVAMIENTO_PATH.write_text(json.dumps(rel, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ind = lotes(res, Path(args.lotes))
    print(json.dumps({"crudas": {c: len(v) for c, v in res["crudas"].items()}, "bancos_a_clasificar": len(res["bancos"]),
                      "camarco_a_clasificar": len(res["camarco"]), "archivados": len(res["archivados"]),
                      "lotes": len(ind), "rel_bancos": rel["bancos_compuesto"]["duplicados_eliminados"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
