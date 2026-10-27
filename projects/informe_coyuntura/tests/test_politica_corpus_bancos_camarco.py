"""Corpus de bancos (ADEBA, ABA, ABAPPRA) y CAMARCO, sin clasificar (ADR-0391).

Todo sin red, con fixtures chicos de las respuestas reales de cada sitio. Lo que
se protege: que cada extractor tome título, fecha y texto del MISMO registro; que
los shortcodes de CAMARCO no lleguen a los lectores; que un comunicado conjunto
de varias cámaras de bancos cuente una vez con todas las firmantes; que la regla
de títulos archive los informes periódicos y NO una nota con postura; y que nada
de esto toque un perímetro del índice.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import politica  # noqa: E402
import corpus_bancos_camarco  # noqa: E402

FX = RAIZ / "tests" / "fixtures"


class _R:
    def __init__(self, data=None, text="", status=200):
        self._d, self.text, self.status_code = data, text, status
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


class _SesionWP:
    """Devuelve un lote en la página 1 y 400 en la siguiente, como WordPress."""
    def __init__(self, data):
        self.data, self.llamadas = data, []

    def get(self, url, **k):
        self.llamadas.append((url, k.get("params")))
        return _R(self.data) if k["params"]["page"] == 1 else _R([], status=400)


def _fx(nombre):
    return json.loads((FX / nombre).read_text(encoding="utf-8"))


def _nota(cam, fecha, titulo, texto="x" * 300, **k):
    return {"camara": cam, "id": k.pop("id", f"{cam}-{fecha}"), "fecha": fecha, "titulo": titulo,
            "texto": texto, "url": f"https://{cam.lower()}.example/{fecha}", **k}


# ── los extractores ────────────────────────────────────────────────────────

def test_adeba_usa_la_categoria_de_comunicados_y_toma_titulo_y_texto_del_mismo_registro():
    s = _SesionWP(_fx("adeba_posts_chico.json"))
    out = politica._adeba_listado(s)
    assert s.llamadas[0][1]["categories"] == politica.ADEBA_COMUNICADOS_CAT == 255
    assert s.llamadas[0][1]["after"].startswith("2023-12-10")
    assert len(out) == 1 and out[0]["camara"] == "ADEBA"
    assert out[0]["titulo"].startswith("Apoyo del G6") and out[0]["fecha"] == "2026-01-09"
    assert "G6" in out[0]["texto"] and "<" not in out[0]["texto"]


def test_aba_pide_comunicados_gacetillas_y_prensa_y_no_capacitaciones():
    s = _SesionWP(_fx("aba_posts_chico.json"))
    out = politica._aba_listado(s)
    assert s.llamadas[0][1]["categories"] == "103,101,107"
    assert out[0]["camara"] == "ABA" and out[0]["fecha"] == "2025-10-27"
    assert out[0]["titulo"].startswith("ABA felicita")


def test_camarco_quita_los_shortcodes_y_conserva_el_texto():
    s = _SesionWP(_fx("camarco_posts_chico.json"))
    out = {n["titulo"]: n for n in politica._camarco_listado(s)}
    g6 = out["COMUNICADO DEL G6"]
    assert "vc_row" not in g6["texto"] and "[vc_" not in g6["texto"] and "column_border" not in g6["texto"]
    assert g6["texto"].startswith("El Grupo de los Seis (G6) expresa su apoyo")
    assert g6["categorias"] and g6["id"] == str(_fx("camarco_posts_chico.json")[0]["id"])


def test_el_listado_de_abappra_lee_fecha_y_titulo_de_cada_entrada_y_deja_afuera_lo_anterior_al_periodo():
    class S:
        def get(self, *a, **k):
            return _R(text=(FX / "abappra_comunicados_chico.html").read_text(encoding="utf-8"))
    out = politica._abappra_listado(S())
    assert [n["fecha"] for n in out] == ["2025-12-18", "2025-02-05"]    # 2023-07-14 queda afuera; el pie no es una entrada
    assert out[0]["titulo"].startswith("Bancos públicos y privados alertan")
    assert out[1]["titulo"].startswith("COMUNICADO DE ABAPPRA")
    assert out[0]["url"].endswith("#2025-12-18") and out[0]["camara"] == "ABAPPRA"
    assert all("Pie del sitio" not in n["texto"] for n in out)


def test_abappra_no_repite_ids_si_dos_comunicados_comparten_fecha():
    html = ("<h4>COMUNICADOS OFICIALES</h4><p>2025-01-31</p><p><strong>Uno</strong></p><p>cuerpo</p><hr>"
            "<p>2025-01-31</p><p><strong>Dos</strong></p><p>cuerpo</p><footer></footer>")

    class S:
        def get(self, *a, **k):
            return _R(text=html)
    ids = [n["id"] for n in politica._abappra_listado(S())]
    assert ids == ["2025-01-31", "2025-01-31-2"]


# ── la regla de títulos ────────────────────────────────────────────────────

@pytest.mark.parametrize("titulo", [
    "Síntesis normativa del 3 de marzo", "Estadísticas del sistema financiero", "Boletín semanal de ABA",
    "Informe mensual de depósitos", "Ranking de bancos 2025", "Los bancos internacionales lideraron los resultados de 2025"])
def test_la_regla_archiva_los_informes_periodicos_de_bancos(titulo):
    assert politica._es_archivable_bancos(titulo)


@pytest.mark.parametrize("titulo", [
    "ADEBA expresa su apoyo a la iniciativa de la Jefatura de Gabinete", "Bancos advierten sobre el impacto negativo de los cambios en las SGR",
    "Comunicado de prensa", "ABA felicita al Gobierno nacional por el resultado de elecciones legislativas",
    "Apoyo del G6 al Acuerdo de Asociación Estratégica con la Unión Europea"])
def test_la_regla_de_bancos_no_archiva_una_nota_con_postura(titulo):
    assert politica._es_archivable_bancos(titulo) is None


def test_la_regla_de_camarco_archiva_series_por_titulo_y_formacion_por_categoria():
    assert politica._es_archivable_camarco("Indicador CAMARCO MARZO 2026") == "serie periódica por título"
    assert politica._es_archivable_camarco("Flash CAMARCO") == "serie periódica por título"
    assert politica._es_archivable_camarco("Acuerdo Salarial UOCRA") == "serie periódica por título"
    assert "categoría" in politica._es_archivable_camarco("Lean Construction", [46, 272])
    assert politica._es_archivable_camarco("Charlas de Obra Ep. 6", [561, 229])


@pytest.mark.parametrize("titulo,cats", [
    ("COMUNICADO DEL G6", [272]), ("Declaración del 147° Consejo Federal", [229]),
    ("Preocupación del sector por el cierre de Vialidad Nacional", [229]),
    ("Comunicado | Cámara Argentina de la Construcción", [272])])
def test_la_regla_de_camarco_no_archiva_los_comunicados_con_postura(titulo, cats):
    assert politica._es_archivable_camarco(titulo, cats) is None


def test_ninguna_nota_de_camarco_con_comunicado_o_declaracion_cae_en_una_categoria_archivada():
    """La premisa de la regla por categoría: lo que se archiva por ser formación o
    divulgación no contiene comunicados. Se verifica contra el corpus guardado."""
    ruta = politica.APOYO_BANCOS_CAMARCO_CORPUS_PATH
    if not ruta.exists():
        pytest.skip("corpus aún no generado")
    d = json.loads(ruta.read_text(encoding="utf-8"))
    for a in d["archivados_estadisticos"]:
        if a["camara"] == "CAMARCO" and a["motivo"].startswith("publicación"):
            assert not politica.re.search(r"comunicado|declaraci[oó]n|consejo federal", a["titulo"], politica.re.I), a


# ── G6 ─────────────────────────────────────────────────────────────────────

def test_g6_marca_los_comunicados_del_g6_y_no_las_notas_del_cpi_ni_del_j6():
    assert politica._es_g6("COMUNICADO DEL G6", "texto")
    assert politica._es_g6("Comunicado sobre el paro general", "De cara al debate, desde el Grupo de los 6 reafirmamos")
    assert not politica._es_g6("El CPI se presentó en la Expo Rural", "El CPI, conformado por las cámaras del G6, realizó")
    assert not politica._es_g6("Encuentro Anual J6 2026", "El J6 reúne a las nuevas generaciones del G6")
    assert not politica._es_g6("Reunión con el Embajador", "El embajador visitó la cámara. " + "x" * 300 + " G6")


# ── deduplicación ──────────────────────────────────────────────────────────

CONJUNTO = ("Ingresos brutos y altas tasas municipales limitan el acceso a los servicios financieros. "
            "La alta carga de impuestos distorsivos que soporta la actividad financiera es uno de los elementos "
            "que explican el bajo y decreciente nivel de préstamos sobre PBI que muestra la economía argentina. " * 3)


def test_un_comunicado_conjunto_cuenta_una_vez_con_todas_las_firmantes():
    notas = [
        _nota("ADEBA", "2025-01-27", "Ingresos brutos y altas tasas municipales limitan el acceso", CONJUNTO, id="40488"),
        _nota("ABA", "2025-01-27", "Ingresos Brutos y altas tasas municipales limitan el acceso a servicios financieros", CONJUNTO, id="7402"),
        _nota("ABAPPRA", "2025-01-31", "INGRESOS BRUTOS Y ALTAS TASAS MUNICIPALES LIMITAN EL ACCESO", CONJUNTO + " Comunicado. Formato PDF.", id="2025-01-31"),
    ]
    out = politica._deduplicar_bancos(notas)
    assert len(out) == 1
    assert out[0]["firmantes"] == ["ADEBA", "ABA", "ABAPPRA"]
    assert out[0]["camara"] == "BANCOS" and out[0]["fecha"] == "2025-01-27"
    assert set(out[0]["fuentes"]) == {"ADEBA", "ABA", "ABAPPRA"}
    assert out[0]["texto"].endswith("Formato PDF.")             # queda el texto más largo


def test_dos_comunicados_distintos_el_mismo_dia_no_se_fusionan():
    notas = [_nota("ADEBA", "2025-04-11", "ACUERDO ARGENTINA – FMI", "Primer texto sobre el acuerdo con el Fondo. " * 20),
             _nota("ABA", "2025-04-11", "ABA subraya el acuerdo que permite eliminar el cepo cambiario", "Otro texto, de otra redacción y otro contenido. " * 20)]
    assert len(politica._deduplicar_bancos(notas)) == 2


def test_el_mismo_titulo_un_ano_despues_no_se_fusiona_ni_dos_notas_de_la_misma_camara():
    asueto = "Los bancos adhieren al asueto del 24 y 31 de diciembre. " * 6
    a = _nota("ADEBA", "2024-12-19", "Los bancos adhieren al asueto del 24 y 31 de diciembre", asueto)
    b = _nota("ADEBA", "2025-12-16", "Los bancos adhieren al asueto del 24 y 31 de diciembre", asueto)
    c = _nota("ABA", "2025-12-16", "Los bancos adhieren al asueto del 24 y 31 de diciembre", asueto)
    out = politica._deduplicar_bancos([a, b, c])
    assert sorted(len(n["firmantes"]) for n in out) == [1, 2]
    assert not politica._son_el_mismo_comunicado(a, b)
    d = _nota("ADEBA", "2025-12-16", "Los bancos adhieren al asueto del 24 y 31 de diciembre", asueto, id="otro")
    assert not politica._son_el_mismo_comunicado(b, d)         # misma cámara


def test_ids_y_orden_de_la_deduplicacion_son_estables():
    notas = [_nota("ABA", "2025-01-27", "Tasas", CONJUNTO, id="9"), _nota("ADEBA", "2025-01-27", "Tasas", CONJUNTO, id="3")]
    a = politica._deduplicar_bancos(notas)
    b = politica._deduplicar_bancos(list(reversed(notas)))
    assert a[0]["id"] == b[0]["id"] == "adeba3-aba9"


# ── el corpus guardado y los lotes ─────────────────────────────────────────

def test_el_corpus_guardado_no_trae_columnas_de_clasificacion_y_no_toca_ningun_perimetro():
    ruta = politica.APOYO_BANCOS_CAMARCO_CORPUS_PATH
    if not ruta.exists():
        pytest.skip("corpus aún no generado")
    d = json.loads(ruta.read_text(encoding="utf-8"))
    assert d["casos"]
    for c in d["casos"]:
        assert not ({"postura", "destinatario", "concordancia", "lecturas"} & set(c))
        assert c["camara"] in ("BANCOS", "CAMARCO") and isinstance(c["g6"], bool)
        assert c["fecha"] >= politica.APOYO_BANCOS_CAMARCO_DESDE and len(c["texto"]) > 0
        assert "[vc_" not in c["texto"]
    claves = [(c["camara"], c["id"]) for c in d["casos"]]
    assert len(claves) == len(set(claves))
    assert "BANCOS" not in politica.APOYO_COMERCIO_CAMARAS and "CAMARCO" not in politica.APOYO_CAMPO_CAMARAS
    assert "CAMARCO" not in politica.APOYO_COMERCIO_CAMARAS


def test_los_lotes_parten_en_tramos_parejos_de_unas_60_notas_con_los_campos_pedidos(tmp_path):
    res = {"bancos": [_nota("BANCOS", f"2025-01-{i % 28 + 1:02d}", f"t{i}", id=str(i), firmantes=["ABA"]) for i in range(70)],
           "camarco": [_nota("CAMARCO", f"2025-02-{i % 28 + 1:02d}", f"c{i}", id=str(i), firmantes=["CAMARCO"]) for i in range(130)]}
    ind = corpus_bancos_camarco.lotes(res, tmp_path)
    assert len(ind) == 4 and sum(i["notas"] for i in ind) == 200
    assert all(40 <= i["notas"] <= 60 for i in ind)
    fila = json.loads((tmp_path / "lote_01.json").read_text(encoding="utf-8"))[0]
    assert set(fila) == {"id", "entidad", "firmantes", "fecha", "titulo", "texto"}
    assert json.loads((tmp_path / "INDICE.json").read_text(encoding="utf-8"))["manual"] == "data/politica/apoyo_empresario_reglas.json"
    ids = [f["id"] for n in range(1, 5) for f in json.loads((tmp_path / f"lote_{n:02d}.json").read_text(encoding="utf-8"))]
    assert len(ids) == len(set(ids)) == 200
