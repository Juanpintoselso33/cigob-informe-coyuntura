"""Tests sin red de scripts/prensa_presidente.py: BigQuery se reemplaza por filas."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import prensa_presidente as pp  # noqa: E402


def _nota(i, mes="202601", dia="20260110", dom="a.com.ar", titulo=None, url=None):
    return {"tipo": "nota", "mes": mes, "fecha": dia, "dominio": dom, "n": 1,
            "url": url or f"https://{dom}/milei-{i}",
            "titulo": f"Titular {i}" if titulo is None else titulo}


def _crudo(notas, total=100000, mes="202601"):
    return {"filas": notas + [{"tipo": "total", "mes": mes, "n": total, "fecha": None,
                               "dominio": None, "url": None, "titulo": None}],
            "bytes_facturados": 1}


def test_muestreo_estable_y_independiente_del_orden():
    notas = [_nota(i, dom=f"d{i % 4}.com.ar") for i in range(1000)]
    a = pp.armar_corpus(_crudo(notas), "2026-01-01", "2026-02-01")
    b = pp.armar_corpus(_crudo(list(reversed(notas))), "2026-01-01", "2026-02-01")
    assert [x["id"] for x in a["notas"]] == [x["id"] for x in b["notas"]]
    assert len(a["notas"]) == pp.TAMANO_MUESTRA
    c = pp.armar_corpus(_crudo(notas), "2026-01-01", "2026-02-01", semilla="otra")
    assert [x["id"] for x in a["notas"]] != [x["id"] for x in c["notas"]]


def test_estratificacion_proporcional():
    notas = [_nota(i, dom="grande.com.ar") for i in range(750)] + \
            [_nota(1000 + i, dom="chico.com.ar") for i in range(250)]
    c = pp.armar_corpus(_crudo(notas), "2026-01-01", "2026-02-01")
    por = {}
    for x in c["notas"]:
        por[x["dominio"]] = por.get(x["dominio"], 0) + 1
    assert por == {"grande.com.ar": 150, "chico.com.ar": 50}


def test_mes_chico_toma_todo():
    c = pp.armar_corpus(_crudo([_nota(i) for i in range(30)]), "2026-01-01", "2026-02-01")
    assert len(c["notas"]) == 30


def test_deduplicacion_y_sin_titulo():
    notas = [
        _nota(1, url="https://a.com.ar/milei-x"),
        _nota(2, url="http://www.a.com.ar/milei-x/?utm=1"),   # misma URL normalizada
        _nota(3, titulo="Mismo  titular"),
        _nota(4, titulo="mismo titular"),                       # título idéntico en el mes
        _nota(5, titulo=None),                                  # sin título
        _nota(6, titulo="  "),
        _nota(7, titulo="Otro &amp; titular"),
    ]
    notas[4]["titulo"] = None
    c = pp.armar_corpus(_crudo(notas), "2026-01-01", "2026-02-01")
    m = c["_meta"]["meses"]["2026-01"]
    assert (m["crudas"], m["sin_titulo"], m["duplicadas_url"], m["duplicadas_titulo"], m["universo"]) == (7, 2, 1, 1, 3)
    assert "Otro & titular" in {x["titulo"] for x in c["notas"]}


def test_mismo_titulo_en_otro_mes_no_es_duplicado():
    notas = [_nota(1, titulo="Igual"), _nota(2, mes="202602", dia="20260205", titulo="Igual")]
    crudo = _crudo(notas)
    crudo["filas"].append({"tipo": "total", "mes": "202602", "n": 100000})
    c = pp.armar_corpus(crudo, "2026-01-01", "2026-03-01")
    assert len(c["notas"]) == 2


def test_mes_incompleto_marcado():
    tot = {f"2025{m:02d}": 115000 for m in range(1, 12)}
    tot["202506"] = 53000
    assert list(pp.meses_incompletos(tot)) == ["202506"] or list(pp.meses_incompletos(tot)) == ["2025-06"]


def test_formato_del_corpus_y_lotes(tmp_path):
    notas = [_nota(i, dom=f"d{i % 5}.com.ar") for i in range(1000)]
    c = pp.armar_corpus(_crudo(notas), "2026-01-01", "2026-02-01")
    for x in c["notas"]:
        assert set(x) == {"id", "mes", "fecha", "dominio", "url", "titulo"}
        assert len(x["id"]) == 12 and x["id"] == pp.id_nota(x["url"])
        assert x["mes"] == "2026-01" and x["fecha"] == "2026-01-10"
    for k in ("consulta", "muestreo", "dominios_filtro", "meses", "meses_incompletos"):
        assert k in c["_meta"]
    assert c["_meta"]["muestreo"]["semilla"] == pp.SEMILLA
    ids = [x["id"] for x in c["notas"]]
    assert len(ids) == len(set(ids))
    k = pp.escribir_lotes(c, tmp_path, tamano=100)
    assert k == 2
    indice = json.loads((tmp_path / "INDICE.json").read_text())
    assert indice["total_titulos"] == 200
    for lote in tmp_path.glob("lote_*.json"):
        for x in json.loads(lote.read_text()):
            assert set(x) == {"id", "mes", "dominio", "titulo"}


def test_consulta_mockeada():
    class Job:
        total_bytes_billed = 42
        def result(self):
            class R:
                def items(s): return [("tipo", "total"), ("mes", "202601"), ("n", 5)]
            return [R()]
    class Cli:
        def query(self, q, **kw):
            assert "milei" in q.lower() and "gkg_partitioned" in q
            return Job()
    out = pp.consultar("2026-01-01", "2026-02-01", cliente=Cli())
    assert out == {"filas": [{"tipo": "total", "mes": "202601", "n": 5}], "bytes_facturados": 42}


def test_el_corpus_versionado_es_coherente():
    p = RAIZ / "data" / "politica" / "prensa_presidente_muestra.json"
    c = json.loads(p.read_text())
    por_mes = {}
    for x in c["notas"]:
        por_mes[x["mes"]] = por_mes.get(x["mes"], 0) + 1
    for mes, m in c["_meta"]["meses"].items():
        assert por_mes[mes] == m["muestra"] <= m["universo"]
    assert "2025-06" in c["_meta"]["meses_incompletos"]


def test_titulo_desde_url_reconstruye_el_slug_y_descarta_los_cortos():
    assert pp.titulo_desde_url(
        "http://www.ambito.com/836139-macri-califico-de-arbitraria-ley-de-la-oposicion-para-frenar-despidos"
    ) == "Macri califico de arbitraria ley de la oposicion para frenar despidos"
    assert pp.titulo_desde_url(
        "http://www.diariouno.com.ar/pais/macri-se-mostro-desacuerdo-legalizar-el-aborto-pero-le-abrio-la-puerta-la-marihuana-20160731-n1200468"
    ).endswith("la marihuana")
    assert pp.titulo_desde_url("https://www.lanacion.com.ar/politica/mauricio-macri-nid12345") == ""


def test_presidente_de_asigna_por_fecha_y_exige_el_apellido():
    assert pp.presidente_de("2018-05-01", "https://x.com.ar/macri-anuncio") == "macri"
    assert pp.presidente_de("2021-05-01", "https://x.com.ar/macri-critico") is None
    assert pp.presidente_de("2021-05-01", "https://x.com.ar/alberto-fernandez-anuncio") == "fernandez"
    assert pp.presidente_de("2021-05-01", "https://x.com.ar/cristina-fernandez-hablo") is None


def test_agregar_meses_suma_el_mes_nuevo_sin_pisar_los_viejos():
    viejo = {"_meta": {"meses": {"2026-08": {"articulos_ar_gdelt": 100}, "2026-09": {"articulos_ar_gdelt": 100}},
                       "periodo": {"desde": "2023-12-01", "hasta_exclusivo": "2026-10-01"}, "meses_incompletos": {}},
             "notas": [{"id": "a", "mes": "2026-09"}]}
    nuevo = {"_meta": {"meses": {"2026-09": {"articulos_ar_gdelt": 1}, "2026-10": {"articulos_ar_gdelt": 40}},
                       "periodo": {"desde": "2026-09-01", "hasta_exclusivo": "2026-11-01"}},
             "notas": [{"id": "b", "mes": "2026-09"}, {"id": "c", "mes": "2026-10"}]}
    r = pp.agregar_meses(viejo, nuevo)
    assert [x["id"] for x in r["notas"]] == ["a", "c"]
    assert r["_meta"]["meses"]["2026-09"]["articulos_ar_gdelt"] == 100
    assert r["_meta"]["meses"]["2026-10"]["cobertura_incompleta"] is True   # 40 < 0,75 x mediana 100
    assert r["_meta"]["periodo"]["hasta_exclusivo"] == "2026-11-01"
