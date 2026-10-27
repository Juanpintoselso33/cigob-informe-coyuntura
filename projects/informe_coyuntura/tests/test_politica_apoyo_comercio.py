"""Postura pública del comercio: CAC y CAME (ADR-0380).

Todo sin red. Lo que se protege acá es lo mismo que en `apoyo_empresario`
(ADR-0150, ADR-0310) —que el número salga del registro codificado, que card y
serie sean la misma cuenta, que el material codificado exista de verdad y que un
comunicado sin clasificar corte la serie— más lo propio del sector: que los dos
rótulos digan lo que miden y que la dimensión reparta a partes iguales.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import itcp  # noqa: E402
import parametrica  # noqa: E402
import politica  # noqa: E402

REGISTRO = json.loads(politica.APOYO_CAMARAS_CODIFICACION_PATH.read_text(encoding="utf-8-sig"))
CASOS = REGISTRO["casos"]
DATOS_TS = (RAIZ / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
POSTURAS = {"apoyo", "critica", "neutro", "dudoso"}
DESTINATARIOS = {"ejecutivo_nacional", "congreso", "provincias_municipios",
                 "judicial", "externo_o_propio"}


# ── el registro ────────────────────────────────────────────────────────────

def test_el_perimetro_es_la_cac_y_la_came_queda_registrada_afuera():
    """ADR-0380. Mismo trato que AEA en la industria (ADR-0334): codificada, no
    puntúa, y nombrarla de nuevo en el perímetro la repone."""
    assert politica.APOYO_COMERCIO_CAMARAS == ("CAC",)
    assert {c["camara"] for c in CASOS} == {"CAC", "CAME"}
    p = REGISTRO["_meta"]["perimetro"]
    assert p["entra_al_calculo"] == list(politica.APOYO_COMERCIO_CAMARAS)
    assert p["codificada_fuera_del_calculo"] == ["CAME"]


def _computables_12m(camara, hasta):
    ini = f"{int(hasta[:4]) - 1}{hasta[4:7]}-01"
    return [c for c in CASOS if c["camara"] == camara and ini <= c["fecha"] <= f"{hasta[:7]}-31"
            and c["destinatario"] == "ejecutivo_nacional" and c["postura"] in ("apoyo", "critica")]


def test_el_perimetro_cumple_el_criterio_de_entrada_de_luis_al_cierre_del_registro():
    """Mínimo de 4 comunicados dirigidos al Ejecutivo con postura en 12 meses.
    Al 27-oct-2026 lo cumple la CAC y no CAME. Si el registro se actualiza y CAME
    llega a 4, este test avisa que hay que reevaluar el perímetro (no lo cambia
    solo)."""
    corte = "2026-10-27"
    for cam in politica.APOYO_COMERCIO_CAMARAS:
        assert len(_computables_12m(cam, corte)) >= 4, f"{cam} no cumple el mínimo de entrada"
    assert len(_computables_12m("CAME", corte)) < 4, "CAME llegó al mínimo: reevaluar el perímetro (ADR-0380)"


def test_los_textos_codificados_existen_y_no_son_una_plantilla():
    """Mismo test que protege a la UIA: en la primera descarga de CAME el
    emparejamiento por posición le puso a varios títulos el cuerpo de otra nota
    (la barra lateral trae enlaces propios) y lo vieron los codificadores, no un
    gate."""
    for camara in ("CAC", "CAME"):
        txt = [c["texto"] for c in CASOS if c["camara"] == camara]
        assert len(set(txt)) == len(txt), f"{camara}: hay textos repetidos"
        assert all(len(t) > 150 for t in txt), f"{camara}: hay textos vacíos o mínimos"
        repetido = max(sum(1 for t in txt if t[:150] == p) for p in {t[:150] for t in txt})
        assert repetido <= 3, f"{camara}: {repetido} comunicados abren igual: plantilla del sitio"
        assert not any("COMUNICADO DE PRENSA" in t[:200] and "Compartir" in t[:300] for t in txt), (
            f"{camara}: el texto conserva el encabezado repetido del sitio")


def test_cada_caso_tiene_los_dos_ejes_y_las_dos_lecturas():
    ids = set()
    for c in CASOS:
        assert c["postura"] in POSTURAS and c["destinatario"] in DESTINATARIOS
        for k in ("pasada_1", "pasada_2"):
            assert c[k]["postura"] in POSTURAS and c[k]["destinatario"] in DESTINATARIOS
        assert c["concordancia"] in ("acuerdo", "adjudicado")
        clave = (c["camara"], c["id"])
        assert clave not in ids, f"comunicado repetido: {clave}"
        ids.add(clave)
        assert c["fecha"] >= politica.APOYO_COMERCIO_DESDE, c["fecha"]


def test_un_caso_con_lecturas_distintas_esta_adjudicado():
    """Ninguno puede entrar al conteo por omisión (ADR-0131)."""
    for c in CASOS:
        distinto = (c["pasada_1"] != c["pasada_2"])
        if distinto:
            assert c["concordancia"] == "adjudicado", f"{c['camara']} {c['id']}: lecturas distintas sin adjudicar"
        else:
            assert c["concordancia"] == "acuerdo"
            assert (c["postura"], c["destinatario"]) == (c["pasada_1"]["postura"], c["pasada_1"]["destinatario"])


def test_la_concordancia_alcanza_el_umbral_y_se_recalcula_del_registro():
    """Los kappas del encabezado no se aceptan de palabra: se recalculan de las
    dos lecturas guardadas en cada caso."""
    import collections

    def kappa(pares):
        n = len(pares)
        po = sum(1 for a, b in pares if a == b) / n
        ca = collections.Counter(a for a, _ in pares)
        cb = collections.Counter(b for _, b in pares)
        pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
        return (po - pe) / (1 - pe)

    meta = REGISTRO["_meta"]["concordancia"]
    kp = kappa([(c["pasada_1"]["postura"], c["pasada_2"]["postura"]) for c in CASOS])
    kd = kappa([(c["pasada_1"]["destinatario"], c["pasada_2"]["destinatario"]) for c in CASOS])
    assert abs(kp - meta["kappa_postura"]) < 0.002 and abs(kd - meta["kappa_destinatario"]) < 0.002
    assert kp >= 0.70 and kd >= 0.70 and meta["estado"] == "ALCANZADA"


def test_ningun_archivado_como_estadistico_esta_codificado_y_todos_cumplen_la_regla():
    arch = REGISTRO["archivados_estadisticos"]
    codif = {(c["camara"], c["id"]) for c in CASOS}
    for a in arch:
        assert (a["camara"], a["id"]) not in codif
        assert politica.APOYO_COMERCIO_ESTADISTICO.search(a["titulo"]), a["titulo"]
    for c in CASOS:
        assert not politica.APOYO_COMERCIO_ESTADISTICO.search(c["titulo"]), (
            f"«{c['titulo']}» está codificado pero la regla lo archivaría")


def test_solo_cuentan_los_dirigidos_al_ejecutivo_con_postura():
    comp = [c for c in CASOS if c["destinatario"] == "ejecutivo_nacional"
            and c["postura"] in ("apoyo", "critica")]
    assert 0 < len(comp) < len(CASOS)


# ── la cuenta ──────────────────────────────────────────────────────────────

def test_la_card_es_el_ultimo_punto_de_la_serie():
    serie = politica.apoyo_comercio_serie()
    card = politica.fetch_apoyo_comercio()
    assert [card["fecha_dato"], card["valor"]] == serie[-1]


def test_el_conteo_de_la_ventana_sale_del_mismo_perimetro_que_el_saldo():
    card = politica.fetch_apoyo_comercio()
    a, c = card["apoyos_ventana"], card["criticas_ventana"]
    assert a + c == card["comunicados_ventana"] >= politica.APOYO_MIN_OBSERVACIONES
    assert round((a - c) / (a + c), 3) == card["valor"]


def test_la_serie_es_mensual_ascendente_sin_cero_de_relleno_ni_antes_del_periodo():
    serie = politica.apoyo_comercio_serie()
    fechas = [f for f, _ in serie]
    assert fechas[0] >= f"{politica.APOYO_DESDE}-01"
    assert fechas == sorted(fechas) and len(fechas) == len(set(fechas))
    assert all(-1.0 <= v <= 1.0 for _, v in serie)


def test_el_saldo_replicado_a_mano_coincide_con_el_ultimo_punto():
    """Recuento independiente del que hace `_apoyo_saldo_serie`."""
    fecha, valor = politica.apoyo_comercio_serie()[-1]
    anio, mes = int(fecha[:4]), int(fecha[5:7])
    ini = f"{anio - 1:04d}-{mes:02d}-01"
    fin = f"{anio:04d}-{mes:02d}-31"
    a = c = 0
    for k in CASOS:
        if (k["camara"] in politica.APOYO_COMERCIO_CAMARAS
                and k["destinatario"] == "ejecutivo_nacional" and ini <= k["fecha"] <= fin):
            a += k["postura"] == "apoyo"
            c += k["postura"] == "critica"
    assert round((a - c) / (a + c), 3) == valor


def test_repuesta_en_el_perimetro_came_suma_a_la_cuenta(monkeypatch):
    """El reingreso es de verdad una línea: con CAME nombrada, la serie y la card
    cuentan sus comunicados (la ventana pasa de 4 comunicados a 6: 5 apoyos y 1 crítica)."""
    solo_cac = politica.fetch_apoyo_comercio()
    monkeypatch.setattr(politica, "APOYO_COMERCIO_CAMARAS", ("CAC", "CAME"))
    con_came = politica.fetch_apoyo_comercio()
    assert solo_cac["comunicados_ventana"] == 4 and con_came["comunicados_ventana"] == 6
    assert con_came["criticas_ventana"] == 1
    assert [con_came["fecha_dato"], con_came["valor"]] == politica.apoyo_comercio_serie()[-1]


def test_el_comercio_no_cambia_el_saldo_de_la_industria():
    """Sumar un sector no puede mover el otro: son archivos y perímetros aparte."""
    industria = {c["camara"] for c in
                 json.loads(politica.APOYO_CODIFICACION_PATH.read_text(encoding="utf-8-sig"))["casos"]}
    assert "CAC" not in industria and "CAME" not in industria
    assert politica.APOYO_CAMARAS_PERIMETRO == ("UIA",)


# ── el índice ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("saldo,esperado", [(1.0, 100), (0.6, 100), (0.0, 65), (-0.6, 10), (-1.0, 10)])
def test_las_bandas_puntuan_el_rango_teorico(saldo, esperado):
    assert parametrica.puntaje_interpolado(saldo, itcp.BANDAS_ITCP["apoyo_comercio"]) == esperado


def test_las_bandas_del_comercio_son_las_de_la_industria():
    """Se fijaron antes de ver la serie (ADR-0045): un sector no tiene bandas
    más indulgentes que otro por tener otro saldo."""
    assert itcp.BANDAS_ITCP["apoyo_comercio"] == itcp.BANDAS_ITCP["apoyo_empresario"]


def test_sector_privado_reparte_a_partes_iguales_industria_y_comercio():
    dim = itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]
    assert dim == {"apoyo_empresario": 0.5, "apoyo_comercio": 0.5}
    assert abs(sum(dim.values()) - 1.0) < 1e-9
    assert itcp.FAMILIAS_ITCP["apoyo_comercio"] == "tension"
    assert itcp.REZAGO_MESES_ITCP["apoyo_comercio"] == itcp.REZAGO_MESES_ITCP["apoyo_empresario"] == 6.0
    assert "apoyo_comercio" not in itcp.INDICADORES_SUSPENDIDOS


# ── los rótulos ────────────────────────────────────────────────────────────

def _rotulo(clave: str) -> str:
    m = re.search(rf'^\s*{clave}:\s*"([^"]+)"', DATOS_TS, re.M)
    assert m, f"no se encontró el rótulo de {clave} en datos.ts"
    return m.group(1)


def test_los_rotulos_nombran_el_sector_y_no_una_camara():
    assert _rotulo("apoyo_empresario") == "Postura pública de la industria"
    assert _rotulo("apoyo_comercio") == "Postura pública del comercio"


def test_la_fuente_publicada_nombra_el_perimetro_y_nada_mas():
    """ADR-0334: la prosa corta que se publica no promete cámaras que no puntúan."""
    fuente = politica.fetch_apoyo_comercio()["fuente"]
    assert "CAC" in fuente
    for ajena in ("CAME", "UIA", "AEA"):
        assert ajena not in fuente
    assert not re.search(r"\bcámaras\b", _rotulo("apoyo_comercio"), re.I)


def test_la_serie_declara_la_misma_fuente_que_la_card():
    import descargar_series
    fuentes = [f for ind, _u, f, _fn in descargar_series.POLITICA_DERIVADAS if ind == "apoyo_comercio"]
    assert fuentes == [politica.fetch_apoyo_comercio()["fuente"]]


# ── el detector ────────────────────────────────────────────────────────────

@pytest.fixture
def detector(tmp_path, monkeypatch):
    """Registro y novedades en un directorio temporal: nada toca data/."""
    reg = tmp_path / "codificacion.json"
    reg.write_text(json.dumps({"casos": [], "archivados_estadisticos": [
        {"camara": "CAC", "id": "ya-archivado", "titulo": "El consumo creció"}]}), encoding="utf-8")
    nov = tmp_path / "novedades.json"
    monkeypatch.setattr(politica, "APOYO_CAMARAS_CODIFICACION_PATH", reg)
    monkeypatch.setattr(politica, "APOYO_CAMARAS_NOVEDADES_PATH", nov)
    return nov


def _cac(slug, fecha):
    return {"slug": slug, "fecha": fecha, "url": f"https://www.cac.com.ar/noticias/{slug}"}


def _came(i, titulo, fecha):
    return {"id": str(i), "titulo": titulo, "fecha": fecha, "url": f"https://www.redcame.org.ar/prensa/{i}/x"}


def _parchar(monkeypatch, cac, came, bajar_cac=None, bajar_came=None):
    monkeypatch.setattr(politica, "_cac_listado", lambda s, paginas=2: cac)
    monkeypatch.setattr(politica, "_came_listado", lambda s, paginas=2: came)
    monkeypatch.setattr(politica, "_cac_comunicado", bajar_cac or (lambda c, s: {
        "camara": "CAC", "id": c["slug"], "fecha": c["fecha"], "titulo": "La CAC apoya X",
        "texto": "texto " * 50, "url": c["url"]}))
    monkeypatch.setattr(politica, "_came_comunicado", bajar_came or (lambda c, s: {
        "camara": "CAME", "id": c["id"], "fecha": c["fecha"], "titulo": c["titulo"],
        "texto": "texto " * 50, "url": c["url"]}))


def test_un_comunicado_nuevo_queda_pendiente_y_corta_la_serie(detector, monkeypatch):
    _parchar(monkeypatch, [_cac("la-cac-apoya-x", "2026-10-20")], [])
    store = politica.detectar_novedades_comercio()
    assert list(store["pendientes"]) == ["CAC|la-cac-apoya-x"]
    assert store["pendientes"]["CAC|la-cac-apoya-x"]["postura"] is None
    # corta en el mes anterior al del pendiente
    assert politica._apoyo_tope(date(2026, 10, 27), politica.APOYO_CAMARAS_NOVEDADES_PATH) == (2026, 9)


def test_un_informe_estadistico_no_se_descarga_ni_queda_pendiente(detector, monkeypatch):
    monkeypatch.setattr(politica, "APOYO_COMERCIO_CAMARAS", ("CAC", "CAME"))

    def no_bajar(*a):
        raise AssertionError("no debía descargar un informe estadístico")
    _parchar(monkeypatch, [_cac("el-consumo-de-hogares-crecio-en-septiembre", "2026-10-18")],
             [_came(9, "Las ventas minoristas pyme aumentaron 0,3% interanual en septiembre", "2026-10-04")],
             no_bajar, no_bajar)
    store = politica.detectar_novedades_comercio()
    assert store["pendientes"] == {}
    assert "CAC|el-consumo-de-hogares-crecio-en-septiembre" in store["revisadas"]


def test_lo_anterior_al_periodo_no_se_avisa(detector, monkeypatch):
    _parchar(monkeypatch, [_cac("la-cac-vieja", "2023-12-09")], [])
    assert politica.detectar_novedades_comercio()["pendientes"] == {}


def test_un_comunicado_avisado_no_se_vuelve_a_avisar(detector, monkeypatch):
    _parchar(monkeypatch, [_cac("la-cac-apoya-x", "2026-10-20")], [])
    politica.detectar_novedades_comercio()
    llamadas = []
    _parchar(monkeypatch, [_cac("la-cac-apoya-x", "2026-10-20")], [],
             lambda c, s: llamadas.append(c) or None)
    politica.detectar_novedades_comercio()
    assert llamadas == []


def test_una_camara_fuera_del_perimetro_no_se_vigila(detector, monkeypatch):
    def no_listar(*a, **k):
        raise AssertionError("CAME está fuera del perímetro: no se consulta")
    _parchar(monkeypatch, [], [])
    monkeypatch.setattr(politica, "_came_listado", no_listar)
    store = politica.detectar_novedades_comercio()
    assert "CAME" not in store["_meta"]["fuentes"]
    assert store["_meta"]["inventario_verificado"] == date.today().isoformat()


def test_la_came_repuesta_en_el_perimetro_se_vigila_y_corta_la_serie(detector, monkeypatch):
    monkeypatch.setattr(politica, "APOYO_COMERCIO_CAMARAS", ("CAC", "CAME"))
    _parchar(monkeypatch, [], [_came(574311999, "CAME ante la reforma", "2026-10-25")])
    store = politica.detectar_novedades_comercio()
    assert list(store["pendientes"]) == ["CAME|574311999"]
    assert politica._apoyo_tope(date(2026, 10, 27), politica.APOYO_CAMARAS_NOVEDADES_PATH) == (2026, 9)


def test_el_inventario_solo_se_verifica_si_responden_todas_las_camaras_del_perimetro(detector, monkeypatch):
    monkeypatch.setattr(politica, "APOYO_COMERCIO_CAMARAS", ("CAC", "CAME"))
    _parchar(monkeypatch, [], [])
    assert politica.detectar_novedades_comercio()["_meta"]["inventario_verificado"] == date.today().isoformat()

    detector.write_text(json.dumps({"_meta": {"inventario_verificado": "2026-08-15"}}), encoding="utf-8")

    def cae(s, paginas=2):
        raise RuntimeError("sin red")
    _parchar(monkeypatch, [], [])
    monkeypatch.setattr(politica, "_came_listado", cae)
    store = politica.detectar_novedades_comercio()
    assert store["_meta"]["inventario_verificado"] == "2026-08-15"
    # y la serie queda cortada en el mes de la última comprobación completa
    assert politica._apoyo_tope(date(2026, 10, 27), politica.APOYO_CAMARAS_NOVEDADES_PATH) == (2026, 8)


def test_el_listado_de_came_empareja_enlace_titulo_y_fecha_dentro_de_la_misma_tarjeta(monkeypatch):
    """El bug de la primera descarga: la barra lateral trae enlaces a /prensa/<id>
    que desplazaban el emparejamiento por posición."""
    html = (
        '<a href="/prensa/111/nota-lateral">lateral</a>'
        '<a href="/prensa/222/primera"><div class="card"><h2 class="prensa">Primera nota</h2>'
        '<em class="date xs">22 de Octubre 2026</em></div></a>'
        '<a href="/prensa/333/segunda"><div class="card"><h2 class="prensa">Segunda &amp; nota</h2>'
        '<em class="date xs">04 de Septiembre 2026</em></div></a>').encode("latin-1")

    class R:
        content = html

        def raise_for_status(self):
            pass

    class S:
        def get(self, *a, **k):
            return R()

    out = politica._came_listado(S(), paginas=1)
    assert [(c["id"], c["titulo"], c["fecha"]) for c in out] == [
        ("222", "Primera nota", "2026-10-22"), ("333", "Segunda & nota", "2026-09-04")]


def test_el_listado_de_cac_lee_el_enlace_de_pagina_siguiente_en_vez_de_fijarlo(monkeypatch):
    pagina1 = ('<a href="/noticias/uno">x</a> <div>7 de octubre de 2026</div>'
               '<a href="?abc123_page=2">siguiente</a>')
    pagina2 = '<a href="/noticias/dos">x</a> <div>29 de septiembre de 2026</div>'
    pedidas = []

    class R:
        def __init__(self, t):
            self.text = t
            self.encoding = None

        def raise_for_status(self):
            pass

    class S:
        def get(self, url, **k):
            pedidas.append(url)
            return R(pagina2 if "abc123_page=2" in url else pagina1)

    out = politica._cac_listado(S(), paginas=2)
    assert [c["slug"] for c in out] == ["uno", "dos"]
    assert pedidas[1].endswith("?abc123_page=2")
    assert out[1]["fecha"] == "2026-09-29"


def test_el_detector_del_comercio_corre_antes_que_el_colector_de_la_card():
    """Mismo orden que el de la industria (ADR-0310): si el detector corriera
    después, un comunicado nuevo cortaría la serie esa noche y la card recién la
    siguiente, y el gate G3 las encontraría distintas."""
    src = (RAIZ / "scripts" / "politica.py").read_text(encoding="utf-8")
    main = src[src.index("def main() -> None:"):]
    assert main.index("detectar_novedades_comercio()") < main.index("fetch_apoyo_comercio")
    assert '("apoyo_comercio",' in main


def test_la_serie_del_comercio_esta_en_el_pipeline_de_series():
    import descargar_series
    assert [f for ind, _u, _s, f in descargar_series.POLITICA_DERIVADAS if ind == "apoyo_comercio"] == [
        politica.apoyo_comercio_serie]


def test_el_store_del_comercio_esta_en_el_git_add_del_cron():
    """Sin esto el runner arranca cada noche sin el inventario y vuelve a avisar
    todo (ADR-0149): el estado vive en git, no en el runner."""
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml").read_text(encoding="utf-8")
    assert "apoyo_camaras_novedades.json" in wf
