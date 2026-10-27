"""Postura pública del campo: Coninagro, SRA y CRA (ADR-0384).

Todo sin red. Lo que se protege acá es lo de `apoyo_comercio` (que el número
salga del registro, que card y serie sean la misma cuenta, que el material
exista de verdad) más lo propio de esta tanda: **los desacuerdos entre los dos
lectores no los resuelve un agente**. Mientras haya uno sin adjudicar que afecte
el puntaje, el indicador no puntúa; y adjudicarlo es lo único que lo repone. Los 13 que decidían
el puntaje los adjudicó Juan (27-oct-2026), y el saldo es el promedio simple de los
saldos de cada cámara, no el de todas las notas juntas.
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

REGISTRO = json.loads(politica.APOYO_CAMPO_CODIFICACION_PATH.read_text(encoding="utf-8-sig"))
DESACUERDOS = json.loads(politica.APOYO_CAMPO_DESACUERDOS_PATH.read_text(encoding="utf-8-sig"))
CASOS = REGISTRO["casos"]
DATOS_TS = (RAIZ / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
POSTURAS = {"apoyo", "critica", "neutro", "dudoso"}
DESTINATARIOS = {"ejecutivo_nacional", "congreso", "provincias_municipios", "judicial", "externo_o_propio"}
CAMARAS = {"CONINAGRO", "SRA", "CRA"}
VENTANA = ("2025-11-01", "2026-10-31")     # doce meses calendario que terminan en oct-2026


def _comp(p, d):
    return d == "ejecutivo_nacional" and p in ("apoyo", "critica")


# ── el registro ────────────────────────────────────────────────────────────

def test_el_registro_cubre_las_tres_camaras_y_la_fia_no_esta():
    assert {c["camara"] for c in CASOS} == CAMARAS
    assert set(politica.APOYO_CAMPO_CAMARAS) == CAMARAS
    assert REGISTRO["_meta"]["perimetro"]["entra_al_calculo"] == list(politica.APOYO_CAMPO_CAMARAS)


def test_ningun_caso_se_repite_y_todos_son_del_periodo():
    claves = [(c["camara"], c["id"]) for c in CASOS]
    assert len(claves) == len(set(claves))
    assert all(c["fecha"] >= politica.APOYO_CAMPO_DESDE for c in CASOS)


def test_los_textos_existen_y_no_son_una_plantilla():
    """El error de CAME (ADR-0380): el cuerpo de otra nota. Acá título y texto salen
    del mismo registro, y se comprueba que no haya textos repetidos ni vacíos."""
    for camara in CAMARAS:
        txt = [c["texto"] for c in CASOS if c["camara"] == camara]
        assert all(len(t) > 150 for t in txt), f"{camara}: hay textos vacíos o mínimos"
        repetido = max(collections.Counter(t[:200] for t in txt).values())
        assert repetido <= 3, f"{camara}: {repetido} notas abren igual: plantilla del sitio"
        assert not any("COMUNICADO DE PRENSA" in t[:200] and "Compartir" in t[:300] for t in txt)


def test_cada_caso_tiene_las_dos_lecturas_y_los_pendientes_no_tienen_valor():
    for c in CASOS:
        for k in ("pasada_1", "pasada_2"):
            assert c[k]["postura"] in POSTURAS and c[k]["destinatario"] in DESTINATARIOS
        distinto = c["pasada_1"] != c["pasada_2"]
        if distinto:
            # Ningún agente adjudica: o está pendiente (sin valor) o lo resolvió una persona.
            assert c["concordancia"] in ("pendiente_adjudicacion", "adjudicado"), (c["camara"], c["id"])
        else:
            assert c["concordancia"] == "acuerdo"
            assert (c["postura"], c["destinatario"]) == (c["pasada_1"]["postura"], c["pasada_1"]["destinatario"])
        if c["concordancia"] == "pendiente_adjudicacion":
            assert c["postura"] is None and c["destinatario"] is None, "un pendiente no puede puntuar"
        else:
            assert c["postura"] in POSTURAS and c["destinatario"] in DESTINATARIOS


def test_el_archivo_de_desacuerdos_es_el_de_los_casos_pendientes():
    pend = {(c["camara"], c["id"]) for c in CASOS if c["concordancia"] == "pendiente_adjudicacion"}
    des = {(d["camara"], d["id"]) for d in DESACUERDOS["desacuerdos"]}
    sin_adjudicar = {(d["camara"], d["id"]) for d in DESACUERDOS["desacuerdos"] if d["adjudicacion"] is None}
    assert sin_adjudicar == pend
    assert des >= pend and DESACUERDOS["_meta"]["total"] == len(DESACUERDOS["desacuerdos"])
    for d in DESACUERDOS["desacuerdos"]:
        assert d["url"].startswith("https://") and len(d["texto"]) > 150 and d["titulo"]
        assert d["lectura_sonnet"] != d["lectura_opus"] or (d["lectura_sonnet"]["postura"], d["lectura_sonnet"]["destinatario"]) != (
            d["lectura_opus"]["postura"], d["lectura_opus"]["destinatario"])


def test_marcar_que_afecta_el_puntaje_es_correcto():
    """Recalcula la marca de cada desacuerdo: dentro de la ventana y con alguna de las
    dos lecturas = ejecutivo_nacional con apoyo o crítica."""
    ini, fin = VENTANA
    for d in DESACUERDOS["desacuerdos"]:
        s, o = d["lectura_sonnet"], d["lectura_opus"]
        afecta = ini <= d["fecha"] <= fin and (_comp(s["postura"], s["destinatario"]) or _comp(o["postura"], o["destinatario"]))
        assert d["afecta_el_puntaje"] == afecta, (d["camara"], d["id"])


def test_la_concordancia_alcanza_el_umbral_y_se_recalcula_del_registro():
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
    assert meta["desacuerdos"] == len(DESACUERDOS["desacuerdos"])


def test_los_archivados_cumplen_la_regla_y_ninguno_esta_codificado():
    codif = {(c["camara"], c["id"]) for c in CASOS}
    for a in REGISTRO["archivados_estadisticos"]:
        assert (a["camara"], a["id"]) not in codif
        assert politica._es_archivable_campo(a["titulo"], "x" * 10), a["titulo"]
    for c in CASOS:
        assert politica._es_archivable_campo(c["titulo"], c["texto"]) is None, c["titulo"]


# ── el criterio de entrada y la suspensión ─────────────────────────────────

def _conteo_ventana(camara, solo_acuerdos=True):
    ini, fin = VENTANA
    n = 0
    for c in CASOS:
        if c["camara"] != camara or not (ini <= c["fecha"] <= fin):
            continue
        if _comp(c["postura"], c["destinatario"]):
            n += 1
    return n


@pytest.mark.parametrize("camara", sorted(CAMARAS))
def test_las_tres_camaras_cumplen_el_minimo_de_luis_con_las_lecturas_coincidentes(camara):
    assert _conteo_ventana(camara) >= 4


def test_los_13_desacuerdos_que_decidian_el_puntaje_los_adjudico_una_persona():
    """La regla de esta tanda: el campo sólo entra con adjudicación humana. Ninguno de los
    desacuerdos que afectan el puntaje puede quedar pendiente ni haberlo resuelto un agente."""
    afectan = [d for d in DESACUERDOS["desacuerdos"] if d["afecta_el_puntaje"]]
    assert len(afectan) == 13 == DESACUERDOS["_meta"]["adjudicados"]
    por_clave = {(c["camara"], c["id"]): c for c in CASOS}
    for d in afectan:
        adj = d["adjudicacion"]
        assert adj and adj["quien"] == "Juan" and adj["fecha"] == "2026-10-27"
        assert adj["motivo"] == "adjudicación humana de Juan, 27-oct-2026"
        assert adj["destinatario"] == "ejecutivo_nacional" and adj["postura"] in ("apoyo", "critica", "neutro")
        c = por_clave[(d["camara"], d["id"])]
        assert (c["postura"], c["destinatario"], c["concordancia"]) == (adj["postura"], adj["destinatario"], "adjudicado")
        assert c["motivo"] == "adjudicación humana de Juan, 27-oct-2026"
    assert DESACUERDOS["_meta"]["que_afectan_el_puntaje_sin_adjudicar"] == 0
    # los 69 restantes siguen pendientes y no afectan el puntaje
    pend = [d for d in DESACUERDOS["desacuerdos"] if d["adjudicacion"] is None]
    assert len(pend) == 69 == DESACUERDOS["_meta"]["pendientes"] and not any(d["afecta_el_puntaje"] for d in pend)


def test_la_adjudicacion_humana_decidio_asi():
    """Lo que decidió Juan, caso por caso (tabla del 27-oct-2026)."""
    esperado = [("CONINAGRO", "2026-02-13", "neutro"), ("CONINAGRO", "2026-02-17", "neutro"), ("CONINAGRO", "2026-06-30", "neutro"),
                ("CRA", "2025-11-03", "apoyo"), ("CRA", "2025-12-12", "apoyo"), ("CRA", "2026-02-04", "apoyo"),
                ("CRA", "2026-06-20", "critica"), ("CRA", "2026-06-20", "apoyo"), ("CRA", "2026-09-22", "neutro"),
                ("CRA", "2026-10-05", "neutro"), ("CRA", "2026-10-05", "neutro"), ("CRA", "2026-10-12", "neutro"),
                ("SRA", "2025-12-09", "critica")]
    real = [(d["camara"], d["fecha"], d["adjudicacion"]["postura"]) for d in DESACUERDOS["desacuerdos"] if d["afecta_el_puntaje"]]
    assert real == esperado


def test_el_indicador_ya_no_esta_suspendido_y_las_tres_camaras_puntuan():
    assert "apoyo_campo" not in itcp.INDICADORES_SUSPENDIDOS
    efectivos = parametrica.indicadores_vigentes(itcp.DIMENSIONES_ITCP, itcp.INDICADORES_SUSPENDIDOS)
    # ADR-0391: con la construcción, cuatro sectores.
    assert set(efectivos["sector_privado"]) == {"apoyo_empresario", "apoyo_comercio", "apoyo_campo", "apoyo_construccion"}


# ── la cuenta ──────────────────────────────────────────────────────────────

def _saldos_a_mano(fecha):
    ini, fin = politica._apoyo_inicio_ventana(fecha[:7]), f"{fecha[:7]}-31"
    out = {}
    for cam in CAMARAS:
        a = sum(1 for k in CASOS if k["camara"] == cam and k["postura"] == "apoyo" and k["destinatario"] == "ejecutivo_nacional" and ini <= k["fecha"] <= fin)
        c = sum(1 for k in CASOS if k["camara"] == cam and k["postura"] == "critica" and k["destinatario"] == "ejecutivo_nacional" and ini <= k["fecha"] <= fin)
        if a + c >= politica.APOYO_MIN_OBSERVACIONES:
            out[cam] = (a, c, (a - c) / (a + c))
    return out


def test_la_card_es_el_ultimo_punto_de_la_serie():
    serie = politica.apoyo_campo_serie()
    card = politica.fetch_apoyo_campo()
    assert [card["fecha_dato"], card["valor"]] == serie[-1]


def test_el_saldo_es_el_promedio_simple_de_los_saldos_de_cada_camara():
    """Propuesta de Luis («promediando entidades»): cada cámara con el mínimo en la ventana
    aporta su saldo y el indicador es el promedio. Recuento independiente del código."""
    fecha, valor = politica.apoyo_campo_serie()[-1]
    saldos = _saldos_a_mano(fecha)
    assert set(saldos) == CAMARAS
    assert round(sum(s for _, _, s in saldos.values()) / len(saldos), 3) == valor
    card = politica.fetch_apoyo_campo()
    assert card["saldos_por_camara"] == {k: round(v[2], 3) for k, v in saldos.items()}
    assert card["apoyos_ventana"] == sum(v[0] for v in saldos.values())
    assert card["criticas_ventana"] == sum(v[1] for v in saldos.values())


def test_el_promedio_por_camara_no_es_el_saldo_de_todas_las_notas_juntas():
    """La CRA publica varias veces más que las otras dos: sumando todas las notas decidiría
    sola. El promedio por cámara tiene que dar otra cosa."""
    card = politica.fetch_apoyo_campo()
    a, c = card["apoyos_ventana"], card["criticas_ventana"]
    juntas = round((a - c) / (a + c), 3)
    assert card["valor"] != juntas and card["valor"] > juntas
    assert card["saldos_por_camara"]["CRA"] < card["valor"] < card["saldos_por_camara"]["SRA"]


def test_una_camara_que_no_llega_al_minimo_no_promedia(tmp_path):
    reg = tmp_path / "r.json"

    def caso(cam, post, m):
        return {"fecha": f"2026-{m:02d}-10", "postura": post, "destinatario": "ejecutivo_nacional", "camara": cam}
    casos = [caso("A", "apoyo", m) for m in (1, 2, 3)] + [caso("B", "critica", 1), caso("B", "critica", 2)]
    reg.write_text(json.dumps({"casos": casos}), encoding="utf-8")
    serie = politica._apoyo_saldo_serie(reg, ("A", "B"), tmp_path / "n.json", "t", por_camara=True)
    assert dict(serie)["2026-03-01"] == 1.0          # B tiene 2 (< 3): no promedia, y no arrastra a A hacia 0
    juntas = politica._apoyo_saldo_serie(reg, ("A", "B"), tmp_path / "n.json", "t")
    assert dict(juntas)["2026-03-01"] == 0.2          # (3 − 2) / 5: el saldo de todas las notas juntas


def test_dos_camaras_con_el_minimo_promedian(tmp_path):
    reg = tmp_path / "r.json"
    casos = ([{"fecha": f"2026-03-{d:02d}", "postura": "apoyo", "destinatario": "ejecutivo_nacional", "camara": "A"} for d in (1, 2, 3, 4)]
             + [{"fecha": f"2026-03-{d:02d}", "postura": "critica", "destinatario": "ejecutivo_nacional", "camara": "B"} for d in range(1, 21)])
    reg.write_text(json.dumps({"casos": casos}), encoding="utf-8")
    serie = politica._apoyo_saldo_serie(reg, ("A", "B"), tmp_path / "n.json", "t", por_camara=True)
    assert dict(serie)["2026-03-01"] == 0.0           # (+1 y −1) / 2, aunque B publique cinco veces más


def test_los_pendientes_de_adjudicacion_no_entran_a_la_cuenta():
    n_computables = sum(1 for c in CASOS if _comp(c["postura"], c["destinatario"]))
    assert n_computables < sum(1 for c in CASOS if _comp(c["pasada_1"]["postura"], c["pasada_1"]["destinatario"]))


def test_la_serie_arranca_donde_la_ventana_cabe_en_el_archivo_de_la_sra():
    """El sitio de la SRA empieza el 21-ene-2025: un mes cuya ventana arranca antes
    mediría lo que el sitio conserva, no lo que dijo la cámara."""
    serie = politica.apoyo_campo_serie()
    assert politica.APOYO_CAMPO_ARCHIVO_DESDE["SRA"] == "2025-01-21"
    primero = serie[0][0][:7]
    assert politica._apoyo_inicio_ventana(primero) >= "2025-01-21"
    anterior = f"{int(primero[:4]) - (1 if primero[5:] == '01' else 0)}-{(int(primero[5:]) - 2) % 12 + 1:02d}"
    assert politica._apoyo_inicio_ventana(anterior) < "2025-01-21"
    fechas = [f for f, _ in serie]
    assert fechas == sorted(fechas) and all(-1.0 <= v <= 1.0 for _, v in serie)


def test_la_cobertura_recorta_la_serie_de_cualquier_perimetro(tmp_path):
    reg = tmp_path / "r.json"
    casos = [{"fecha": f"2025-{m:02d}-15", "postura": "apoyo", "destinatario": "ejecutivo_nacional", "camara": "X"}
             for m in range(1, 13)] * 3
    reg.write_text(json.dumps({"casos": casos}), encoding="utf-8")
    nov = tmp_path / "n.json"
    sin = politica._apoyo_saldo_serie(reg, ("X",), nov, "t")
    con = politica._apoyo_saldo_serie(reg, ("X",), nov, "t", cobertura_desde="2025-03-01")
    assert sin[0][0] < con[0][0] and con[-1] == sin[-1]
    assert politica._apoyo_inicio_ventana(con[0][0][:7]) >= "2025-03-01"


# ── el índice ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("saldo,esperado", [(1.0, 100), (0.6, 100), (0.0, 65), (-0.6, 10), (-1.0, 10)])
def test_las_bandas_puntuan_el_rango_teorico(saldo, esperado):
    assert parametrica.puntaje_interpolado(saldo, itcp.BANDAS_ITCP["apoyo_campo"]) == esperado


def test_las_bandas_del_campo_son_las_de_la_industria_y_el_comercio():
    assert itcp.BANDAS_ITCP["apoyo_campo"] == itcp.BANDAS_ITCP["apoyo_empresario"] == itcp.BANDAS_ITCP["apoyo_comercio"]


def test_sector_privado_reparte_parejo_entre_los_sectores():
    # Tercios desde ADR-0384; cuartos desde ADR-0391 (entra la construcción).
    dim = itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]
    assert set(dim) == {"apoyo_empresario", "apoyo_comercio", "apoyo_campo", "apoyo_construccion"}
    assert abs(sum(dim.values()) - 1.0) < 1e-9
    assert max(dim.values()) - min(dim.values()) < 0.001
    assert itcp.FAMILIAS_ITCP["apoyo_campo"] == "tension"
    assert itcp.REZAGO_MESES_ITCP["apoyo_campo"] == itcp.REZAGO_MESES_ITCP["apoyo_empresario"] == 6.0


# ── los rótulos ────────────────────────────────────────────────────────────

def test_el_rotulo_nombra_el_sector_y_la_fuente_las_tres_camaras():
    m = re.search(r'^\s*apoyo_campo:\s*"([^"]+)"', DATOS_TS, re.M)
    assert m and m.group(1) == "Postura pública del campo"
    card = politica.fetch_apoyo_campo()
    for nombre in ("Coninagro", "SRA", "CRA"):
        assert nombre in card["fuente"]
    for ajena in ("UIA", "CAC", "CAME", "AEA"):
        assert ajena not in card["fuente"]


def test_la_serie_declara_la_misma_fuente_que_la_card():
    import descargar_series
    fuentes = [f for ind, _u, f, _fn in descargar_series.POLITICA_DERIVADAS if ind == "apoyo_campo"]
    assert fuentes == [politica.fetch_apoyo_campo()["fuente"]]
    assert [fn for ind, _u, _s, fn in descargar_series.POLITICA_DERIVADAS if ind == "apoyo_campo"] == [politica.apoyo_campo_serie]


# ── el detector ────────────────────────────────────────────────────────────

@pytest.fixture
def detector(tmp_path, monkeypatch):
    reg = tmp_path / "codificacion.json"
    reg.write_text(json.dumps({"casos": [], "archivados_estadisticos": [
        {"camara": "CONINAGRO", "id": "1", "titulo": "Semáforo", "motivo": "informe estadístico periódico"}]}), encoding="utf-8")
    nov = tmp_path / "novedades.json"
    monkeypatch.setattr(politica, "APOYO_CAMPO_CODIFICACION_PATH", reg)
    monkeypatch.setattr(politica, "APOYO_CAMPO_NOVEDADES_PATH", nov)
    return nov


def _con(i, titulo, fecha):
    return {"camara": "CONINAGRO", "id": str(i), "fecha": fecha, "titulo": titulo, "texto": "texto " * 50,
            "url": f"https://www.coninagro.org.ar/{i}"}


def _sra(i, titulo, fecha):
    return {"id": str(i), "titulo": titulo, "fecha": fecha, "url": f"https://www.sra.ar/{i}-x"}


def _parchar(monkeypatch, con=(), sra=(), cra=(), bajar_sra=None, bajar_cra=None):
    monkeypatch.setattr(politica, "_coninagro_listado", lambda s, paginas=1: [dict(x) for x in con])
    monkeypatch.setattr(politica, "_sra_listado", lambda s, paginas=2: [dict(x) for x in sra])
    monkeypatch.setattr(politica, "_cra_listado", lambda s, paginas=1: [dict(x) for x in cra])
    monkeypatch.setattr(politica, "_sra_comunicado", bajar_sra or (lambda c, s: {
        "camara": "SRA", "id": c["id"], "fecha": c["fecha"], "titulo": c["titulo"], "texto": "texto " * 50, "url": c["url"]}))
    monkeypatch.setattr(politica, "_cra_comunicado", bajar_cra or (lambda c, s: {
        "camara": "CRA", "id": c["id"], "fecha": "2026-10-20", "titulo": "CRA pide X", "texto": "texto " * 50, "url": c["url"]}))


def test_una_nota_nueva_queda_pendiente_y_corta_la_serie(detector, monkeypatch):
    _parchar(monkeypatch, con=[_con(9, "Coninagro rechaza la medida", "2026-10-20")])
    store = politica.detectar_novedades_campo()
    assert list(store["pendientes"]) == ["CONINAGRO|9"]
    assert store["pendientes"]["CONINAGRO|9"]["postura"] is None
    assert politica._apoyo_tope(date(2026, 10, 27), politica.APOYO_CAMPO_NOVEDADES_PATH) == (2026, 9)


def test_un_informe_estadistico_y_lo_anterior_al_periodo_no_quedan_pendientes(detector, monkeypatch):
    _parchar(monkeypatch, con=[_con(2, "Semáforo de las Economías Regionales: nueva producción en verde", "2026-10-13"),
                               _con(3, "Una nota vieja", "2023-12-09")])
    store = politica.detectar_novedades_campo()
    assert store["pendientes"] == {}
    assert "CONINAGRO|2" in store["revisadas"]


def test_lo_ya_registrado_no_se_vuelve_a_avisar(detector, monkeypatch):
    _parchar(monkeypatch, con=[_con(9, "Coninagro rechaza la medida", "2026-10-20")])
    politica.detectar_novedades_campo()
    politica.detectar_novedades_campo()
    assert len(politica.detectar_novedades_campo()["pendientes"]) == 1


def test_la_sra_baja_la_nota_y_una_pagina_tecnica_no_se_codifica(detector, monkeypatch):
    _parchar(monkeypatch, sra=[_sra(300, "La SRA apoya la baja", "2026-10-25"), _sra(301, "Banner Inicio - Bandera", "2026-10-25")],
             bajar_sra=lambda c, s: {"camara": "SRA", "id": c["id"], "fecha": c["fecha"], "titulo": c["titulo"],
                                     "texto": "corto" if c["id"] == "301" else "texto " * 50, "url": c["url"]})
    store = politica.detectar_novedades_campo()
    assert list(store["pendientes"]) == ["SRA|300"]
    assert "SRA|301" in store["revisadas"]


def test_la_cra_por_slug_se_registra_con_su_id_numerico_y_no_se_baja_dos_veces(detector, monkeypatch):
    llamadas = []

    def bajar(c, s):
        llamadas.append(c["id"])
        return {"camara": "CRA", "id": "31700", "fecha": "2026-10-20", "titulo": "CRA pide X", "texto": "texto " * 50, "url": c["url"]}
    cra = [{"id": "cra-pide-x", "url": "https://www.cra.org.ar/prensa/cra-pide-x/"}]
    _parchar(monkeypatch, cra=cra, bajar_cra=bajar)
    store = politica.detectar_novedades_campo()
    assert list(store["pendientes"]) == ["CRA|31700"]
    politica.detectar_novedades_campo()
    assert llamadas == ["cra-pide-x"]


def test_una_nota_de_cra_de_otra_seccion_no_es_pendiente(detector, monkeypatch):
    _parchar(monkeypatch, cra=[{"id": "31701", "url": "https://www.cra.org.ar/prensa/31701/"}], bajar_cra=lambda c, s: None)
    assert politica.detectar_novedades_campo()["pendientes"] == {}


def test_el_inventario_solo_se_verifica_si_responden_las_tres(detector, monkeypatch):
    _parchar(monkeypatch)
    assert politica.detectar_novedades_campo()["_meta"]["inventario_verificado"] == date.today().isoformat()
    detector.write_text(json.dumps({"_meta": {"inventario_verificado": "2026-08-15"}}), encoding="utf-8")
    _parchar(monkeypatch)

    def cae(s, paginas=2):
        raise RuntimeError("sin red")
    monkeypatch.setattr(politica, "_sra_listado", cae)
    assert politica.detectar_novedades_campo()["_meta"]["inventario_verificado"] == "2026-08-15"
    assert politica._apoyo_tope(date(2026, 10, 27), politica.APOYO_CAMPO_NOVEDADES_PATH) == (2026, 8)


def test_el_perimetro_vacio_no_vigila_nada(detector, monkeypatch):
    monkeypatch.setattr(politica, "APOYO_CAMPO_CAMARAS", ("CRA",))

    def no_listar(*a, **k):
        raise AssertionError("fuera del perímetro: no se consulta")
    _parchar(monkeypatch)
    monkeypatch.setattr(politica, "_coninagro_listado", no_listar)
    monkeypatch.setattr(politica, "_sra_listado", no_listar)
    store = politica.detectar_novedades_campo()
    assert list(store["_meta"]["fuentes"]) == ["CRA"]


# ── los extractores ────────────────────────────────────────────────────────

def test_coninagro_toma_titulo_y_cuerpo_del_mismo_registro():
    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"id": 5, "date": "2026-10-22T17:33:42", "link": "https://www.coninagro.org.ar/x/",
                     "title": {"rendered": "Caminos &amp; rutas"}, "content": {"rendered": "<p>Uno</p><p>Dos</p>"}}]

    class S:
        def get(self, *a, **k):
            return R()
    out = politica._coninagro_listado(S())
    assert out == [{"camara": "CONINAGRO", "id": "5", "fecha": "2026-10-22", "titulo": "Caminos & rutas",
                    "texto": "Uno\n Dos", "url": "https://www.coninagro.org.ar/x/"}]


def test_el_listado_de_la_sra_des_escapa_el_href_y_lee_la_fecha_de_la_tarjeta():
    html = ('<article itemscope="itemscope" class="card"><a href="&#10;&#9;&#9;&#9;/245-comunicado" itemprop="url">'
            '<h2 itemprop="headline">Comunicado</h2><meta itemprop="datePublished" content="2026-09-29T-03:00"/></a></article>'
            '<article class="card"><a href="&#10;&#9;/246-otra" itemprop="url"><h2>Otra &amp; nota</h2>'
            '<meta itemprop="datePublished" content="2026-10-06T-03:00"/></a></article>')

    class R:
        text = html

        def raise_for_status(self):
            pass

    class S:
        def get(self, *a, **k):
            return R()
    out = politica._sra_listado(S(), paginas=1)
    assert [(c["id"], c["titulo"], c["fecha"], c["url"]) for c in out] == [
        ("245", "Comunicado", "2026-09-29", "https://www.sra.ar/245-comunicado"),
        ("246", "Otra & nota", "2026-10-06", "https://www.sra.ar/246-otra")]


def test_la_sra_rechaza_una_pagina_cuyo_titulo_no_es_el_de_la_tarjeta():
    class R:
        status_code = 200
        text = "<h1>Otra cosa</h1><p>texto de otra nota</p></article>"

    class S:
        def get(self, *a, **k):
            return R()
    assert politica._sra_comunicado({"id": "1", "titulo": "Comunicado", "fecha": "2026-01-01", "url": "u"}, S()) is None


def test_la_cra_lee_el_json_ld_y_descarta_lo_que_no_es_prensa():
    def pagina(seccion):
        ld = json.dumps({"@type": "NewsArticle", "headline": "CRA pide X", "datePublished": "2026-10-20T10:00:00-03:00",
                         "articleSection": seccion, "articleBody": "Párrafo uno.\n\nPárrafo dos."})
        return (f'<script type="application/ld+json">{ld}</script><button data-contentID="31700"></button>').encode("utf-8")

    class S:
        def __init__(self, seccion):
            self.seccion = seccion

        def get(self, *a, **k):
            class R:
                status_code = 200
                content = pagina(self.seccion)
            return R()
    c = {"id": "cra-pide-x", "url": "https://www.cra.org.ar/prensa/cra-pide-x/"}
    ok = politica._cra_comunicado(c, S("Prensa"))
    assert (ok["id"], ok["fecha"], ok["titulo"]) == ("31700", "2026-10-20", "CRA pide X") and "Párrafo dos." in ok["texto"]
    assert politica._cra_comunicado(c, S("Actualidad")) is None


def test_el_listado_de_la_cra_toma_los_enlaces_de_la_portada():
    class R:
        text = ('<a href="/prensa/uno-dos/">a</a><a href="/prensa/uno-dos/">b</a><a href="/prensa/30813/">c</a>'
                '<a href="/institucional/x/">d</a>')

        def raise_for_status(self):
            pass

    class S:
        def get(self, *a, **k):
            return R()
    assert [c["id"] for c in politica._cra_listado(S())] == ["uno-dos", "30813"]


# ── el cableado ────────────────────────────────────────────────────────────

def test_el_detector_corre_antes_que_el_colector_de_la_card():
    src = (RAIZ / "scripts" / "politica.py").read_text(encoding="utf-8")
    main = src[src.index("def main() -> None:"):]
    assert main.index("detectar_novedades_campo()") < main.index("fetch_apoyo_campo")
    assert '("apoyo_campo",' in main


def test_el_store_del_campo_esta_en_el_git_add_del_cron():
    wf = (RAIZ.parent.parent / ".github" / "workflows" / "data-pipeline.yml").read_text(encoding="utf-8")
    assert "apoyo_campo_novedades.json" in wf


def test_la_formula_y_la_ficha_existen():
    formulas = (RAIZ / "web" / "src" / "lib" / "formulas.ts").read_text(encoding="utf-8")
    fichas = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
    assert re.search(r"^\s*apoyo_campo:\s*\{\s*\n\s*latex:", formulas, re.M)
    bloque = fichas[fichas.index("  apoyo_campo: {"):fichas.index("  apoyo_comercio: {")]
    assert 'adr: "0384"' in bloque


def test_la_ficha_el_adr_y_la_formula_declaran_el_promedio_por_camara():
    fichas = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
    formulas = (RAIZ / "web" / "src" / "lib" / "formulas.ts").read_text(encoding="utf-8")
    adr = (RAIZ / "docs" / "adr" / "0384-el-campo-entra-a-la-postura-empresaria.md").read_text(encoding="utf-8")
    bloque = fichas[fichas.index("  apoyo_campo: {"):fichas.index("  apoyo_comercio: {")]
    assert "promedio simple de los saldos de las cámaras" in bloque
    f = formulas[formulas.index("  apoyo_campo: {"):formulas.index("  apoyo_comercio: {")]
    assert "promedio simple de los saldos" in f and "\\sum" in f
    assert "promedio simple de los saldos de cada cámara" in adr and "estado: 'aceptado'" in adr
