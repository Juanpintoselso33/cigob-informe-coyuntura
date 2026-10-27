"""La construcción (CAMARCO) y las autopartistas (AFAC) entran a la postura
empresaria; los bancos quedan clasificados afuera (ADR-0391).

Todo sin red. Lo que se protege, además de lo de ADR-0380 y ADR-0384 (el número
sale del registro, card y serie son la misma cuenta, ningún agente adjudica):

- la regla nueva: la crónica de un acto ya contado por su declaración no se
  cuenta de nuevo, y se marca con `duplica_a`, no por fecha;
- los informes periódicos de AFAC se archivan por título y sus desacuerdos no
  se adjudican;
- la industria promedia por cámara la UIA y AFAC;
- sector privado en cuartos, y los bancos fuera del cálculo.
"""
import collections
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

FX = RAIZ / "tests" / "fixtures"


def _leer(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


CONS = _leer(politica.APOYO_CONSTRUCCION_CODIFICACION_PATH)
BANC = _leer(politica.APOYO_BANCOS_CODIFICACION_PATH)
IND = _leer(politica.APOYO_INDUSTRIA_CODIFICACION_PATH)
CORPUS_BC = _leer(politica.APOYO_BANCOS_CAMARCO_CORPUS_PATH)
CORPUS_AFAC = _leer(politica.APOYO_AFAC_CORPUS_PATH)
UIA = _leer(politica.APOYO_CODIFICACION_PATH)
REGISTROS = {"CAMARCO": CONS, "BANCOS": BANC, "AFAC": IND}
POSTURAS = {"apoyo", "critica", "neutro", "dudoso", "mixta"}
DESTINATARIOS = {"ejecutivo_nacional", "congreso", "provincias_municipios", "judicial", "externo_o_propio"}
VENTANA = ("2025-11-01", "2026-10-31")      # doce meses calendario que terminan en oct-2026
MOTIVO_JUAN = "adjudicación de Juan, 27-oct-2026"


def _kappa(pares):
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca = collections.Counter(a for a, _ in pares)
    cb = collections.Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe)


def _conteo(reg, ventana=VENTANA):
    return [c for c in reg["casos"] if ventana[0] <= c["fecha"] <= ventana[1] and politica._apoyo_computable(c)]


# ── los registros ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("cam", sorted(REGISTROS))
def test_cada_registro_es_de_una_sola_entidad_y_no_repite_casos(cam):
    reg = REGISTROS[cam]
    assert {c["camara"] for c in reg["casos"]} == {cam}
    claves = [c["id"] for c in reg["casos"]] + [a["id"] for a in reg["archivados_estadisticos"]]
    assert len(claves) == len(set(claves))
    assert all(c["fecha"] >= "2023-12-10" for c in reg["casos"])


def test_el_registro_de_la_uia_no_se_toco():
    """Sumar una cámara no toca el registro de otra (ADR-0380): AFAC va aparte."""
    assert {c["camara"] for c in UIA["casos"]} == {"UIA", "AEA"}


def test_los_casos_de_camarco_y_bancos_son_los_del_corpus():
    corpus = {(c["camara"], c["id"]): c for c in CORPUS_BC["casos"]}
    for cam in ("CAMARCO", "BANCOS"):
        reg = REGISTROS[cam]
        assert {(c["camara"], c["id"]) for c in reg["casos"]} == {k for k in corpus if k[0] == cam}
        for c in reg["casos"]:
            assert c["titulo"] == corpus[(cam, c["id"])]["titulo"] and c["fecha"] == corpus[(cam, c["id"])]["fecha"]
        arch = {a["id"] for a in CORPUS_BC["archivados_estadisticos"] if a["camara"] == cam}
        assert {a["id"] for a in reg["archivados_estadisticos"]} == arch


def test_el_corpus_de_afac_tiene_el_texto_de_cada_nota_del_registro():
    textos = {c["id"]: c["texto"] for c in CORPUS_AFAC["casos"]}
    ids = [c["id"] for c in IND["casos"]] + [a["id"] for a in IND["archivados_estadisticos"]]
    assert sorted(ids) == sorted(textos) and len(ids) == 41
    assert all(len(textos[i]) > 150 for i in ids)
    assert CORPUS_AFAC["_meta"]["total_en_listado"] == len(CORPUS_AFAC["listado"]) == 171
    assert sum(1 for x in CORPUS_AFAC["listado"] if x["incluido"]) == 41


@pytest.mark.parametrize("cam", sorted(REGISTROS))
def test_cada_caso_tiene_las_dos_lecturas_y_ningun_agente_adjudica(cam):
    for c in REGISTROS[cam]["casos"]:
        for k in ("pasada_1", "pasada_2"):
            assert c[k]["postura"] in POSTURAS and c[k]["destinatario"] in DESTINATARIOS
        iguales = (c["pasada_1"]["postura"], c["pasada_1"]["destinatario"]) == (
            c["pasada_2"]["postura"], c["pasada_2"]["destinatario"])
        if iguales:
            assert c["concordancia"] == "acuerdo"
            assert (c["postura"], c["destinatario"]) == (c["pasada_1"]["postura"], c["pasada_1"]["destinatario"])
        elif c["concordancia"] == "adjudicado":
            assert c["adjudicacion"]["quien"] == "Juan" and c["adjudicacion"]["fecha"] == "2026-10-27"
            assert MOTIVO_JUAN in c["motivo"]
        else:
            assert c["concordancia"] == "pendiente_adjudicacion"
            assert c["postura"] is None and c["destinatario"] is None, "un pendiente no puede puntuar"


# ── la concordancia ────────────────────────────────────────────────────────

@pytest.mark.parametrize("cam,kp,kd", [("CAMARCO", 0.900, 0.853), ("BANCOS", 0.943, 0.918), ("AFAC", 0.864, 0.829)])
def test_el_kappa_se_recalcula_del_registro(cam, kp, kd):
    reg = REGISTROS[cam]
    casos = reg["casos"]
    p = _kappa([(c["pasada_1"]["postura"], c["pasada_2"]["postura"]) for c in casos])
    d = _kappa([(c["pasada_1"]["destinatario"], c["pasada_2"]["destinatario"]) for c in casos])
    meta = reg["_meta"]["concordancia"]
    assert abs(p - meta["kappa_postura"]) < 0.0015 and abs(d - meta["kappa_destinatario"]) < 0.0015
    assert abs(p - kp) < 0.0015 and abs(d - kd) < 0.0015
    assert p >= 0.70 and d >= 0.70 and meta["estado"] == "ALCANZADA"


def test_el_kappa_de_afac_sobre_las_41_con_los_informes_es_el_medido():
    """Antes de archivar los informes periódicos el kappa era 0,805 y 0,773: sale
    de las lecturas descartadas que guarda cada archivado."""
    pares = [(c["pasada_1"], c["pasada_2"]) for c in IND["casos"]] + [
        (a["lecturas_descartadas"]["pasada_1"], a["lecturas_descartadas"]["pasada_2"]) for a in IND["archivados_estadisticos"]]
    assert len(pares) == 41
    assert abs(_kappa([(a["postura"], b["postura"]) for a, b in pares]) - 0.805) < 0.0015
    assert abs(_kappa([(a["destinatario"], b["destinatario"]) for a, b in pares]) - 0.773) < 0.0015


# ── las adjudicaciones ─────────────────────────────────────────────────────

ADJUDICADOS = {
    ("BANCOS", "abappra-2024-07-08"): ("neutro", "ejecutivo_nacional"),
    ("BANCOS", "adeba-44450"): ("apoyo", "ejecutivo_nacional"),
    ("CAMARCO", "38128"): ("neutro", "provincias_municipios"),
    ("CAMARCO", "40769"): ("neutro", "ejecutivo_nacional"),
    ("AFAC", "5549"): ("critica", "congreso"),
    ("AFAC", "5679"): ("neutro", "ejecutivo_nacional"),
    ("AFAC", "5785"): ("mixta", "externo_o_propio"),
}


def test_las_adjudicaciones_son_las_de_juan():
    real = {(c["camara"], c["id"]): (c["postura"], c["destinatario"])
            for reg in REGISTROS.values() for c in reg["casos"] if c["concordancia"] == "adjudicado"}
    assert real == ADJUDICADOS


def test_quedan_pendientes_42_desacuerdos_y_ninguno_decide_el_puntaje():
    pend = {cam: [c for c in reg["casos"] if c["concordancia"] == "pendiente_adjudicacion"]
            for cam, reg in REGISTROS.items()}
    assert {k: len(v) for k, v in pend.items()} == {"CAMARCO": 40, "BANCOS": 2, "AFAC": 0}
    for cam, casos in pend.items():
        assert REGISTROS[cam]["_meta"]["concordancia"]["pendientes"] == len(casos)
        for c in casos:
            dentro = VENTANA[0] <= c["fecha"] <= VENTANA[1]
            alguna = any(c[k]["destinatario"] == "ejecutivo_nacional" and c[k]["postura"] in ("apoyo", "critica")
                         for k in ("pasada_1", "pasada_2"))
            assert not (dentro and alguna), (cam, c["id"])
            assert c["afecta_el_puntaje"] is False


# ── la regla de la crónica duplicada ──────────────────────────────────────

def test_la_cronica_del_147_consejo_federal_no_se_cuenta_de_nuevo():
    por_id = {c["id"]: c for c in CONS["casos"]}
    cronica, declaracion = por_id["45869"], por_id["45828"]
    assert cronica["titulo"] == "Se celebró el 147° Consejo Federal en Rosario"
    assert declaracion["titulo"] == "Declaración del 147° Consejo Federal"
    assert cronica["duplica_a"] == "CAMARCO|45828" and "duplica_a" not in declaracion
    # las dos lecturas la ven como crítica al Ejecutivo: sin la regla contaría dos veces
    assert politica._apoyo_computable({**cronica, "duplica_a": None})
    assert not politica._apoyo_computable(cronica) and politica._apoyo_computable(declaracion)
    assert "45869" not in [c["id"] for c in _conteo(CONS)]


def test_cada_duplica_a_apunta_a_una_declaracion_del_mismo_registro():
    claves = {f"{c['camara']}|{c['id']}": c for c in CONS["casos"]}
    marcadas = [c for c in CONS["casos"] if c.get("duplica_a")]
    assert len(marcadas) == 4
    for c in marcadas:
        dest = claves[c["duplica_a"]]
        assert "declaraci" in dest["titulo"].lower() and not dest.get("duplica_a")
        assert abs((date.fromisoformat(c["fecha"]) - date.fromisoformat(dest["fecha"])).days) <= 7
    assert {m["cronica"] for m in CONS["_meta"]["regla_cronica_duplicada"]["casos"]} == {
        f"CAMARCO|{c['id']}" for c in marcadas}


def test_la_regla_vale_para_cualquier_registro_y_no_mira_la_fecha(tmp_path):
    reg = tmp_path / "r.json"

    def caso(i, post, dia, **k):
        return {"camara": "X", "id": str(i), "fecha": f"2026-04-{dia:02d}", "postura": post,
                "destinatario": "ejecutivo_nacional", **k}
    casos = [caso(1, "apoyo", 1), caso(2, "apoyo", 2), caso(3, "apoyo", 3), caso(4, "critica", 20),
             caso(5, "critica", 21, duplica_a="X|4"), caso(6, "critica", 20)]   # 6: mismo día, NO duplica
    reg.write_text(json.dumps({"casos": casos}), encoding="utf-8")
    serie = dict(politica._apoyo_saldo_serie(reg, ("X",), tmp_path / "n.json", "t"))
    assert serie["2026-04-01"] == round((3 - 2) / 5, 3)      # sin la crónica: 3 apoyos, 2 críticas


# ── el archivo de informes de AFAC ────────────────────────────────────────

ARCHIVADOS_AFAC = {"5486", "5543", "5558", "5566", "5574", "5587", "5610", "5623", "5695", "5740",
                   "5818", "5994", "6070", "6087", "6106", "6107", "6139", "6203", "6208", "6244"}


def test_los_informes_periodicos_de_afac_se_archivan_por_titulo():
    assert {a["id"] for a in IND["archivados_estadisticos"]} == ARCHIVADOS_AFAC
    for a in IND["archivados_estadisticos"]:
        assert politica._es_archivable_afac(a["titulo"]) == "informe estadístico periódico", a["titulo"]
    for c in IND["casos"]:
        assert politica._es_archivable_afac(c["titulo"]) is None, c["titulo"]


@pytest.mark.parametrize("titulo,archiva", [
    ("Informe de Actividad del Sector Autopartista (junio 2026)", True),
    ("Informe de Actividad (abril 2024) - Sector Autopartista", True),
    ("Comercio Exterior Autopartista (enero-agosto 2025)", True),
    ("Comercio Exterior de Autopartes 2025", True),
    ("Informe de Comercio Exterior de Autopartes (1° semestre 2026)", True),
    ("Necesidad de generar un punto de quiebre en el comercio exterior de autopartes", False),
    ("Alarmante tendencia del déficit comercial de autopartes", False),
    ("Flota vehicular circulante en Argentina 2025", False),
])
def test_la_regla_de_titulos_de_afac(titulo, archiva):
    assert bool(politica._es_archivable_afac(titulo)) is archiva


def test_los_desacuerdos_sobre_informes_archivados_no_se_adjudican():
    adj = IND["_meta"]["codificadores"]["adjudicacion"]
    archivados_en_desacuerdo = {a["id"] for a in IND["archivados_estadisticos"]
                                if a["lecturas_descartadas"]["pasada_1"] != a["lecturas_descartadas"]["pasada_2"]}
    assert archivados_en_desacuerdo == {"6244", "6087", "5695"}
    assert {x.split("|")[1] for x in adj["archivados_sin_adjudicar"]} == archivados_en_desacuerdo
    assert not archivados_en_desacuerdo & {i for (cam, i) in ADJUDICADOS if cam == "AFAC"}


# ── el criterio de entrada (12 meses calendario) ──────────────────────────

@pytest.mark.parametrize("cam,n,a,c", [("CAMARCO", 4, 3, 1), ("AFAC", 4, 1, 3), ("BANCOS", 3, 3, 0)])
def test_el_conteo_de_doce_meses(cam, n, a, c):
    v = _conteo(REGISTROS[cam])
    assert (len(v), sum(x["postura"] == "apoyo" for x in v), sum(x["postura"] == "critica" for x in v)) == (n, a, c)
    assert REGISTROS[cam]["_meta"]["perimetro"]["conteo_ventana"]["comunicados"] == n
    assert (n >= 4) is (cam in politica.APOYO_CONSTRUCCION_CAMARAS + politica.APOYO_INDUSTRIA_CAMARAS)


def test_camarco_contaria_cinco_sin_la_regla_de_la_cronica():
    sin_regla = [c for c in CONS["casos"] if VENTANA[0] <= c["fecha"] <= VENTANA[1]
                 and politica._apoyo_computable({**c, "duplica_a": None})]
    assert len(sin_regla) == 5


# ── la construcción ────────────────────────────────────────────────────────

def test_la_card_de_la_construccion_es_el_ultimo_punto_de_la_serie():
    serie = politica.apoyo_construccion_serie()
    card = politica.fetch_apoyo_construccion()
    assert [card["fecha_dato"], card["valor"]] == serie[-1]
    assert serie[0][0] >= "2023-12-01" and all(-1.0 <= v <= 1.0 for _, v in serie)
    assert card["fuente"] == "Comunicados de CAMARCO — codificación CIGOB"


def test_las_bandas_de_la_construccion_son_las_de_los_otros_sectores():
    b = itcp.BANDAS_ITCP
    assert b["apoyo_construccion"] == b["apoyo_empresario"] == b["apoyo_comercio"] == b["apoyo_campo"]
    assert itcp.FAMILIAS_ITCP["apoyo_construccion"] == "tension"
    assert itcp.REZAGO_MESES_ITCP["apoyo_construccion"] == 6.0


# ── la industria: UIA + AFAC promediadas por cámara ───────────────────────

def test_la_industria_promedia_la_uia_y_afac():
    fecha, valor = politica.apoyo_empresario_serie()[-1]
    card = politica.fetch_apoyo_empresario()
    assert [card["fecha_dato"], card["valor"]] == [fecha, valor]
    ini, fin = politica._apoyo_inicio_ventana(fecha[:7]), f"{fecha[:7]}-31"
    saldos = {}
    for reg, cam in ((UIA, "UIA"), (IND, "AFAC")):
        v = [c["postura"] for c in reg["casos"] if c["camara"] == cam and politica._apoyo_computable(c)
             and ini <= c["fecha"] <= fin]
        a, k = v.count("apoyo"), v.count("critica")
        if a + k >= politica.APOYO_MIN_OBSERVACIONES:
            saldos[cam] = (a - k) / (a + k)
    assert set(saldos) == {"UIA", "AFAC"}
    assert round(sum(saldos.values()) / 2, 3) == valor
    assert card["saldos_por_camara"] == {k: round(v, 3) for k, v in saldos.items()}
    assert card["fuente"] == "Comunicados de la UIA y AFAC — codificación CIGOB"


def test_si_una_camara_de_la_industria_no_llega_al_minimo_cuenta_la_otra(tmp_path, monkeypatch):
    uia, afac = tmp_path / "uia.json", tmp_path / "afac.json"

    def caso(cam, post, m):
        return {"camara": cam, "id": f"{cam}{m}{post}", "fecha": f"2026-{m:02d}-10", "postura": post,
                "destinatario": "ejecutivo_nacional"}
    uia.write_text(json.dumps({"casos": [caso("UIA", "critica", m) for m in (1, 2, 3, 4)]}))
    afac.write_text(json.dumps({"casos": [caso("AFAC", "apoyo", 1), caso("AFAC", "apoyo", 2)]}))
    monkeypatch.setattr(politica, "APOYO_CODIFICACION_PATH", uia)
    monkeypatch.setattr(politica, "APOYO_INDUSTRIA_CODIFICACION_PATH", afac)
    monkeypatch.setattr(politica, "APOYO_NOVEDADES_PATH", tmp_path / "n1.json")
    monkeypatch.setattr(politica, "APOYO_INDUSTRIA_NOVEDADES_PATH", tmp_path / "n2.json")
    s = dict(politica.apoyo_empresario_serie())
    assert s["2026-04-01"] == -1.0                 # AFAC tiene 2 (< 3): no promedia
    afac.write_text(json.dumps({"casos": [caso("AFAC", "apoyo", m) for m in (1, 2, 3)]}))
    assert dict(politica.apoyo_empresario_serie())["2026-04-01"] == 0.0   # (−1 + 1) / 2


def test_un_pendiente_de_afac_corta_la_serie_de_la_industria(tmp_path, monkeypatch):
    nov = tmp_path / "afac_nov.json"
    nov.write_text(json.dumps({"pendientes": {"AFAC|9": {"fecha": "2026-08-20"}}}))
    monkeypatch.setattr(politica, "APOYO_INDUSTRIA_NOVEDADES_PATH", nov)
    assert politica.apoyo_empresario_serie()[-1][0] <= "2026-07-01"


# ── la dimensión y los bancos ──────────────────────────────────────────────

def test_sector_privado_en_cuartos_que_suman_uno():
    dim = itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]
    assert dim == {"apoyo_empresario": 0.25, "apoyo_comercio": 0.25, "apoyo_campo": 0.25, "apoyo_construccion": 0.25}
    assert abs(sum(dim.values()) - 1.0) < 1e-12
    efectivos = parametrica.indicadores_vigentes(itcp.DIMENSIONES_ITCP, itcp.INDICADORES_SUSPENDIDOS)
    assert set(efectivos["sector_privado"]) == set(dim)


def test_el_peso_de_la_dimension_no_cambia():
    # El mismo que con tres sectores (ADR-0384): sumar un sector reparte adentro.
    assert itcp.DIMENSIONES_ITCP["sector_privado"]["peso"] == pytest.approx(0.14, abs=0.002)


def test_los_bancos_quedan_clasificados_fuera_del_calculo():
    assert politica.APOYO_BANCOS_CAMARAS == ()
    assert "apoyo_bancos" not in itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]
    assert "apoyo_bancos" not in itcp.BANDAS_ITCP
    with pytest.raises(ValueError):
        politica.apoyo_bancos_serie()
    src = (RAIZ / "scripts" / "politica.py").read_text(encoding="utf-8")
    main = src[src.index("def main() -> None:"):]
    assert '("apoyo_bancos",' not in main
    assert BANC["_meta"]["perimetro"]["entra_al_calculo"] == []


def test_nombrar_a_los_bancos_repone_su_saldo(monkeypatch):
    monkeypatch.setattr(politica, "APOYO_BANCOS_CAMARAS", ("BANCOS",))
    serie = dict(politica.apoyo_bancos_serie())
    assert serie["2026-10-01"] == 1.0              # 3 apoyos y 0 críticas en la ventana


def test_un_comunicado_de_bancos_firmado_por_varias_cuenta_una_vez():
    ids = [c["id"] for c in BANC["casos"]]
    assert len(ids) == len(set(ids))
    assert any(len(c["firmantes"]) > 1 for c in BANC["casos"])


# ── los detectores ─────────────────────────────────────────────────────────

class _R:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


def _fx(nombre):
    return json.loads((FX / nombre).read_text(encoding="utf-8"))


class _SesionAFAC:
    headers: dict = {}

    def __init__(self):
        self.headers = {}
        self.posts, self.gets = [], []

    def post(self, url, json=None, **k):
        self.posts.append((url, json))
        return _R(_fx("afac_getbyfilter_chico.json"))

    def get(self, url, **k):
        self.gets.append(url)
        return _R(_fx("afac_getbyid_chico.json"))


def test_el_listado_de_afac_sale_de_la_api_de_la_seccion_2():
    s = _SesionAFAC()
    out = politica._afac_listado(s)
    assert s.posts[0][0].endswith("/Noticias/GetByFilter") and s.posts[0][1]["idSeccion"] == 2
    assert [c["id"] for c in out] == ["6244", "6204", "6038"]           # el de antes del período queda afuera
    assert out[1] == {"camara": "AFAC", "id": "6204", "fecha": "2026-08-06",
                      "titulo": "Acuerdo Automotor Argentina-Ecuador",
                      "url": "https://www.afac.org.ar/comunicaciones/comunicadosdeprensa/noticia?id=6204", "adjunto": None}


def test_el_cuerpo_de_afac_des_escapa_el_html_dos_veces():
    c = politica._afac_comunicado({"id": "6204", "fecha": "2026-08-06", "titulo": "x",
                                   "url": "u", "adjunto": None}, _SesionAFAC())
    assert c["titulo"] == "Acuerdo Automotor Argentina-Ecuador"
    assert "celebra la actualización del acuerdo ACE-59" in c["texto"]
    assert "<" not in c["texto"] and "&" not in c["texto"]


@pytest.fixture
def det_afac(tmp_path, monkeypatch):
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps({"casos": [{"camara": "AFAC", "id": "6038"}], "archivados_estadisticos": []}))
    nov = tmp_path / "nov.json"
    monkeypatch.setattr(politica, "APOYO_INDUSTRIA_CODIFICACION_PATH", reg)
    monkeypatch.setattr(politica, "APOYO_INDUSTRIA_NOVEDADES_PATH", nov)
    monkeypatch.setattr(politica.requests, "Session", _SesionAFAC)
    return nov


def test_una_nota_nueva_de_afac_queda_pendiente_y_un_informe_no(det_afac):
    store = politica.detectar_novedades_industria()
    assert list(store["pendientes"]) == ["AFAC|6204"]
    assert store["pendientes"]["AFAC|6204"]["postura"] is None
    assert "informe estadístico" in store["revisadas"]["AFAC|6244"]["origen"]
    assert store["_meta"]["inventario_verificado"] == date.today().isoformat()
    assert politica._apoyo_tope(date(2026, 10, 27), det_afac) == (2026, 7)
    assert len(politica.detectar_novedades_industria()["pendientes"]) == 1     # no se re-avisa


@pytest.fixture
def det_camarco(tmp_path, monkeypatch):
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps({"casos": [{"camara": "CAMARCO", "id": "32965"}], "archivados_estadisticos": []}))
    nov = tmp_path / "nov.json"
    monkeypatch.setattr(politica, "APOYO_CONSTRUCCION_CODIFICACION_PATH", reg)
    monkeypatch.setattr(politica, "APOYO_CONSTRUCCION_NOVEDADES_PATH", nov)
    pedidos = []

    def listar(s, max_paginas=None):
        pedidos.append(max_paginas)
        return [{"camara": "CAMARCO", "id": str(x["id"]), "fecha": x["date"][:10],
                 "titulo": x["title"]["rendered"], "texto": "texto " * 40, "url": "u",
                 "categorias": x.get("categories", [])} for x in _fx("camarco_posts_chico.json")]
    monkeypatch.setattr(politica, "_camarco_listado", listar)
    return nov, pedidos


def test_el_detector_de_camarco_mira_la_primera_pagina_y_archiva_el_indicador(det_camarco):
    nov, pedidos = det_camarco
    store = politica.detectar_novedades_construccion()
    assert pedidos == [1]
    assert sorted(store["pendientes"]) == ["CAMARCO|44927", "CAMARCO|45726"]
    assert "serie periódica" in store["revisadas"]["CAMARCO|45804"]["origen"]
    assert "categorias" not in store["pendientes"]["CAMARCO|45726"]
    assert politica._apoyo_tope(date(2026, 10, 27), nov) == (2026, 1)


def test_si_camarco_no_responde_el_inventario_no_se_verifica(det_camarco, monkeypatch):
    nov, _ = det_camarco
    nov.write_text(json.dumps({"_meta": {"inventario_verificado": "2026-08-15"}}))

    def cae(s, max_paginas=None):
        raise RuntimeError("sin red")
    monkeypatch.setattr(politica, "_camarco_listado", cae)
    assert politica.detectar_novedades_construccion()["_meta"]["inventario_verificado"] == "2026-08-15"


def test_los_stores_estan_en_el_git_add_del_cron_y_los_detectores_corren_antes():
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml").read_text(encoding="utf-8")
    assert "apoyo_industria_novedades.json" in wf and "apoyo_construccion_novedades.json" in wf
    src = (RAIZ / "scripts" / "politica.py").read_text(encoding="utf-8")
    main = src[src.index("def main() -> None:"):]
    assert main.index("detectar_novedades_industria()") < main.index("fetch_apoyo_empresario")
    assert main.index("detectar_novedades_construccion()") < main.index("fetch_apoyo_construccion")
    assert '("apoyo_construccion",' in main


# ── la web ─────────────────────────────────────────────────────────────────

WEB = RAIZ / "web" / "src" / "lib"


def test_la_construccion_tiene_rotulo_descripcion_formula_y_ficha():
    datos = (WEB / "datos.ts").read_text(encoding="utf-8")
    m = re.search(r'^\s*apoyo_construccion:\s*"([^"]+)"', datos, re.M)
    assert m and m.group(1) == "Postura pública de la construcción"
    assert re.search(r"^\s*apoyo_construccion:\s*\{", (WEB / "descripciones.ts").read_text(encoding="utf-8"), re.M)
    assert re.search(r"^\s*apoyo_construccion:\s*\{\s*\n\s*latex:", (WEB / "formulas.ts").read_text(encoding="utf-8"), re.M)
    fichas = (WEB / "fichas.ts").read_text(encoding="utf-8")
    i = fichas.index("  apoyo_construccion: {")
    assert 'adr: "0391"' in fichas[i:fichas.index("\n  },\n", i)]


def test_la_ficha_de_la_industria_registra_a_afac():
    fichas = (WEB / "fichas.ts").read_text(encoding="utf-8")
    i = fichas.index("  apoyo_empresario: {")
    bloque = fichas[i:fichas.index("\n  },\n", i)]
    assert 'adr: "0391"' in bloque and "AFAC" in bloque


def test_ningun_texto_dice_tercios_ni_nombra_a_la_uia_sola_como_industria():
    for nombre in ("descripciones.ts", "fichas.ts", "formulas.ts"):
        t = (WEB / nombre).read_text(encoding="utf-8")
        for ind in ("apoyo_empresario", "apoyo_comercio", "apoyo_campo", "apoyo_construccion"):
            if f"  {ind}: {{" not in t:
                continue
            i = t.index(f"  {ind}: {{")
            bloque = t[i:t.index("\n  },\n", i)]
            vigente = re.sub(r"cambios: \[.*", "", bloque, flags=re.S)    # el historial puede citar lo viejo
            assert "un tercio" not in vigente and "en tercios" not in vigente, (nombre, ind)
    desc = (WEB / "descripciones.ts").read_text(encoding="utf-8")
    sp = re.search(r'^\s*sector_privado:\s*"([^"]+)"', desc, re.M).group(1)
    assert "AFAC" in sp and "construcción (CAMARCO)" in sp and "tercio" not in sp
