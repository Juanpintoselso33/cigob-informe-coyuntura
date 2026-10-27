"""votos_sobre_bancas (ADR-0376): votos ajenos con que se aprueban las leyes.

Todo sin red: actas sintéticas con los conteos que guarda el caché. Lo que se
cuida acá es la definición — qué votaciones entran, cómo se calcula el
excedente, la ventana de 12 meses, el 65/35 y que el indicador entre al ITCP
a medias con la cohesión del bloque.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import itcp  # noqa: E402
import parametrica  # noqa: E402
import politica  # noqa: E402


def dip(titulo="O.D. 10 - REGIMEN X. VOT. EN GRAL.", fecha="2026-06-24", afirmativos=131,
        bancas_lla=94, lla_afirm=93, lla_neg=0, resultado="AFIRMATIVO", bancas_camara=257,
        origen_pe=True):
    return {"fecha": fecha, "titulo": titulo, "resultado": resultado, "afirmativos": afirmativos,
            "bancas_lla": bancas_lla, "lla_afirm": lla_afirm, "lla_neg": lla_neg,
            "bancas_camara": bancas_camara, "origen_pe": origen_pe}


def sen(titulo="Inocencia Fiscal II.", fecha="2026-09-17", etapa="EN GENERAL", expedientes=None,
        ods=("O.D. 372/2026",), afirmativos=44, bancas_lla=21, lla_afirm=20, lla_neg=0,
        resultado="AFIRMATIVO", bancas_camara=72, origen_pe=True):
    return {"fecha": fecha, "titulo": titulo, "etapa": etapa, "expedientes": list(expedientes or []),
            "ods": list(ods), "resultado": resultado, "afirmativos": afirmativos,
            "bancas_lla": bancas_lla, "lla_afirm": lla_afirm, "lla_neg": lla_neg,
            "bancas_camara": bancas_camara, "origen_pe": origen_pe}


# ── el excedente de una votación ─────────────────────────────────────────────

def test_excedente_diputados_a_mano():
    # 131 afirmativos − 94 bancas LLA = 37 votos ajenos, sobre 257 bancas.
    assert politica._vsb_excedente(dip(), "diputados") == pytest.approx(37 / 257 * 100)


def test_excedente_senado_a_mano():
    # 44 − 21 = 23 sobre 72.
    assert politica._vsb_excedente(sen(), "senado") == pytest.approx(23 / 72 * 100)


def test_el_total_de_la_camara_sale_del_acta_y_si_falta_de_la_constante():
    e = dip(bancas_camara=None)
    assert politica._vsb_excedente(e, "diputados") == pytest.approx(37 / 257 * 100)
    assert politica._vsb_excedente(dip(bancas_camara=256), "diputados") == pytest.approx(37 / 256 * 100)


def test_el_bloque_lla_cuenta_ausentes_y_el_excedente_puede_ser_cero_o_negativo():
    # bancas_lla incluye a los ausentes del bloque: no es lo que votó, es lo que tiene.
    assert politica._vsb_excedente(dip(afirmativos=94, bancas_lla=94, lla_afirm=90), "diputados") == 0
    assert politica._vsb_excedente(dip(afirmativos=90, bancas_lla=94, lla_afirm=90), "diputados") < 0


# ── el universo: qué votaciones NO cuentan ───────────────────────────────────

@pytest.mark.parametrize("titulo", [
    "MOCIÓN SOLICITADA POR LA DIP. GIUDICI, SILVANA.",
    "APARTAMIENTO DE REGLAMENTO SOLICITADO POR EL DIP. JULIANO, PABLO.",
    "HABILITACIÓN DEL TRATAMIENTO EXPTE. 9-PE-2025.",
    "INSISTENCIA PROYECTO DE LEY 27.795.",
    "O.D. 595 - PEDIDO DE INFORMES AL P.E. S/ DIVERSAS CUESTIONES. VOT. EN GRAL.",
    "O.D. 939 - COMISIÓN INVESTIGADORA SOBRE CRIPTOMONEDA. MODIF. DICT. DE MAY. VOT. EN GRAL.",
    "O. D. 759 - DNU 179/2025, QUE APRUEBA LAS OPERACIONES DE CRÉDITO PÚBLICO.",
    "EXPTE. 0039-PE-2025. DECRETO DE NECESIDAD Y URGENCIA N° 340/25.",
    "PLAN DE LABOR",
])
def test_diputados_no_cuenta_lo_que_no_es_una_ley_en_general(titulo):
    assert politica._vsb_excedente(dip(titulo=titulo), "diputados") is None


@pytest.mark.parametrize("titulo", [
    "O.D. 149 - RÉGIMEN DE INCENTIVO. CREACIÓN. DICT. DE MAY. CAPÍTULO XII.",
    "O.D. 6 - LEY DE MODERNIZACIÓN LABORAL. DICT. DE MAY. TÍTULO XXVI.",
    "O.D. 786 - EMERGENCIA EN DISCAPACIDAD. ART. 5.",
    "O.D. 924 - LEY DE FINANCIAMIENTO UNIVERSITARIO. DICT. DE MAY. ARTS. 6 Y 7.",
])
def test_diputados_no_cuenta_la_votacion_en_particular(titulo):
    assert politica._vsb_excedente(dip(titulo=titulo), "diputados") is None


@pytest.mark.parametrize("titulo", [
    "O.D. 350 - MODIFICACIONES A LA LEY NACIONAL DE DISCAPACIDAD. VOT. EN GRAL.",
    "O.D. 263 - CÁMARA FEDERAL DE APELACIONES DE TUCUMÁN. REORGANIZACIÓN. VOT. EN GRAL. Y PART.",
    "O.D. 442 - INMUEBLE PROP. DEL ESTADO NAC. TRANSFERENCIA A TÍTULO GRATUITO A LA PROV. DEL CHACO.",
    "EXPTES. 1110-D-2024 / 6391-D-2024. HUSO HORARIO. VOT. EN GRAL. Y PART.",
    "VOTACIÓN EN GRAL. Y PARTICULAR EMERGENCIA PROVINCIAS DE BS.AS. Y SANTA FE.",
])
def test_diputados_cuenta_la_votacion_en_general_y_la_unica(titulo):
    # «A TÍTULO GRATUITO» no es el Título I de una ley.
    assert politica._vsb_excedente(dip(titulo=titulo), "diputados") is not None


def test_una_ley_rechazada_no_cuenta():
    assert politica._vsb_excedente(dip(resultado="NEGATIVO", afirmativos=100), "diputados") is None
    assert politica._vsb_excedente(sen(resultado="NEGATIVO", afirmativos=30), "senado") is None


def test_si_lla_vota_en_contra_o_empata_no_cuenta():
    assert politica._vsb_excedente(dip(lla_afirm=10, lla_neg=80), "diputados") is None
    assert politica._vsb_excedente(dip(lla_afirm=40, lla_neg=40), "diputados") is None
    assert politica._vsb_excedente(sen(lla_afirm=0, lla_neg=15), "senado") is None
    # a favor por la mínima sí
    assert politica._vsb_excedente(dip(lla_afirm=41, lla_neg=40), "diputados") is not None


def test_un_acta_sin_conteos_no_cuenta():
    e = dip()
    for k in ("afirmativos", "bancas_lla"):
        sin = {**e, k: None}
        assert politica._vsb_excedente(sin, "diputados") is None
    solo_cabecera = {k: e[k] for k in ("fecha", "titulo", "resultado")}
    assert politica._vsb_excedente(solo_cabecera, "diputados") is None


def test_senado_solo_cuenta_la_votacion_en_general_de_un_proyecto_de_ley():
    pl = ["PE-159/25-PL"]
    assert politica._vsb_excedente(sen(expedientes=pl, etapa="EN GENERAL"), "senado") is not None
    assert politica._vsb_excedente(sen(expedientes=pl, etapa="EN GENERAL Y EN PARTICULAR"), "senado") is not None
    assert politica._vsb_excedente(sen(expedientes=pl, etapa=""), "senado") is not None   # votación única
    # en particular, moción de orden, tratamiento sobre tablas, "otra"
    for etapa in ("EN PARTICULAR", "MOCIÓN DE ORDEN", "HABILITACIÓN TRAT SOBRE TABLAS", "OTRA"):
        assert politica._vsb_excedente(sen(expedientes=pl, etapa=etapa), "senado") is None
    # pliegos (AC), resoluciones (PR), declaraciones (PD): no son leyes
    for exp in ("PE-175/25-AC", "S-112/26-PR", "S-725/26-PD"):
        assert politica._vsb_excedente(sen(expedientes=[exp], etapa="EN GENERAL Y EN PARTICULAR"), "senado") is None
    # un proyecto de ley entre varios expedientes alcanza
    assert politica._vsb_excedente(sen(expedientes=["PE-1/26-AC", "S-2/26-PL"]), "senado") is not None


def test_senado_sin_expediente_pide_orden_del_dia_y_descarta_designaciones_y_mociones():
    assert politica._vsb_excedente(sen(expedientes=[], ods=["O.D. 363/2026"]), "senado") is not None
    assert politica._vsb_excedente(sen(expedientes=[], ods=[]), "senado") is None
    for titulo in ("Acuerdo para designaciones en el Poder Judicial.",
                   "Acuerdos para el ascenso de diplomáticos.",
                   "Moción de orden para el retorno a comisión.",
                   "Designación de cónsules y vicecónsules honorarios."):
        assert politica._vsb_excedente(sen(titulo=titulo, expedientes=[], ods=["O.D. 1/2026"]), "senado") is None
    # «Acuerdo de conciliación…» es una ley que aprueba un acuerdo, no una designación
    assert politica._vsb_excedente(
        sen(titulo="Acuerdo de conciliación con acreedores de títulos de deuda.", expedientes=[],
            ods=["O.D. 102/2026"]), "senado") is not None


# ── la ventana de 12 meses ───────────────────────────────────────────────────

def test_ventana_de_doce_meses_calendario():
    ref = date(2026, 10, 15)
    assert politica._vsb_desde(ref) == date(2025, 11, 1)
    actas = {
        "a": dip(fecha="2025-10-31", afirmativos=200),   # un día antes de la ventana
        "b": dip(fecha="2025-11-01", afirmativos=131),   # primer día de la ventana
        "c": dip(fecha="2026-10-15", afirmativos=131),   # el día de la referencia
        "d": dip(fecha="2026-10-16", afirmativos=250),   # posterior: no existía todavía
    }
    r = politica.votos_sobre_bancas_camara(actas, "diputados", ref)
    assert r["n_actas"] == 2
    assert r["valor"] == pytest.approx(37 / 257 * 100)
    assert r["fecha_dato"] == "2026-10-15"


def test_la_ventana_no_cruza_la_instalacion_del_congreso():
    # antes del 10-dic-2023 LLA tenía 3 bancas: no es «el bloque propio»
    assert politica._vsb_desde(date(2024, 3, 31)) == date(2023, 12, 10)
    actas = {"a": dip(fecha="2023-12-01", afirmativos=200), "b": dip(fecha="2024-02-02", afirmativos=131)}
    assert politica.votos_sobre_bancas_camara(actas, "diputados", date(2024, 3, 31))["n_actas"] == 1


def test_promedio_simple_por_votacion_no_por_ley():
    actas = {"1": dip(fecha="2026-06-01", afirmativos=131),
             "2": dip(fecha="2026-06-02", afirmativos=131),
             "3": dip(fecha="2026-06-03", afirmativos=200)}
    r = politica.votos_sobre_bancas_camara(actas, "diputados", date(2026, 7, 1))
    esperado = (2 * 37 + 106) / 3 / 257 * 100
    assert r["valor"] == pytest.approx(esperado)


def test_sin_votaciones_en_la_ventana_no_hay_valor():
    assert politica.votos_sobre_bancas_camara({}, "diputados", date(2026, 7, 1)) is None
    assert politica.votos_sobre_bancas_camara(
        {"x": dip(fecha="2024-01-10")}, "diputados", date(2026, 7, 1)) is None


# ── el compuesto 65/35 ───────────────────────────────────────────────────────

def test_compuesto_65_35():
    r = politica.componer_votos_sobre_bancas({
        "diputados": {"valor": 20.0, "n_actas": 10, "fecha_dato": "2026-10-01"},
        "senado": {"valor": 40.0, "n_actas": 5, "fecha_dato": "2026-09-01"},
    })
    assert r["valor"] == pytest.approx(0.65 * 20 + 0.35 * 40)   # 27,0
    assert r["n_actas"] == 15
    assert r["fecha_dato"] == "2026-10-01"
    assert r["camaras_sin_dato"] == []
    assert r["componentes"]["senado"]["valor"] == 40.0


def test_si_falta_una_camara_se_usa_la_otra_sola_y_se_dice():
    r = politica.componer_votos_sobre_bancas({
        "diputados": None, "senado": {"valor": 40.0, "n_actas": 5, "fecha_dato": "2026-09-01"}})
    assert r["valor"] == 40.0
    assert r["camaras_sin_dato"] == ["diputados"]
    r2 = politica.componer_votos_sobre_bancas({
        "diputados": {"valor": 20.0, "n_actas": 3, "fecha_dato": "2026-09-01"}, "senado": None})
    assert r2["valor"] == 20.0 and r2["camaras_sin_dato"] == ["senado"]
    assert politica.componer_votos_sobre_bancas({"diputados": None, "senado": None}) is None


def test_el_valor_de_extremo_a_extremo_usa_el_cache_de_las_dos_camaras():
    cache = {"diputados": {"1": dip(fecha="2026-06-24")},
             "senado": {"9": sen(fecha="2026-09-17")}}
    r = politica.votos_sobre_bancas_valor(cache, date(2026, 10, 15))
    esperado = 0.65 * (37 / 257 * 100) + 0.35 * (23 / 72 * 100)
    assert r["valor"] == pytest.approx(round(esperado, 1))
    assert r["componentes"]["diputados"]["n_actas"] == 1


# ── card y serie son el mismo cálculo ────────────────────────────────────────

def test_la_card_es_el_ultimo_punto_de_la_serie(monkeypatch):
    cache = {"diputados": {"1": dip(fecha="2026-06-24"), "2": dip(fecha="2026-02-10", afirmativos=140)},
             "senado": {"9": sen(fecha="2026-09-17")}}
    monkeypatch.setattr(politica, "votos_sobre_bancas_actualizar", lambda: (cache, True))
    card = politica.fetch_votos_sobre_bancas()
    serie = politica.votos_sobre_bancas_serie()
    assert serie[-1][0] == date.today().isoformat()
    assert card["valor"] == serie[-1][1]
    assert card["unidad"] == "% de las bancas de la cámara"
    assert card["componentes"]["senado"]["n_actas"] == 1
    assert card["fecha_dato"] == date.today().isoformat()
    assert "Diputados: 16,1 % (2 votaciones)" in card["detalle_txt"]   # coma decimal, como el resto del sitio
    assert card["ultima_votacion_incluida"] == "2026-09-17"
    # los puntos son [fecha, valor] ascendentes y arrancan cuando hay primera votación
    fechas = [f for f, _ in serie]
    assert fechas == sorted(fechas)
    assert fechas[0] == "2026-02-28"


def test_lectura_incompleta_no_se_publica_como_actualizacion(monkeypatch):
    cache = {"diputados": {"1": dip()}, "senado": {}}
    monkeypatch.setattr(politica, "votos_sobre_bancas_actualizar", lambda: (cache, False))
    assert politica.fetch_votos_sobre_bancas() is None
    assert politica.votos_sobre_bancas_serie() == []


# ── el cache por acta se escribe de a una y retoma ───────────────────────────

HTML_SENADO = """<html><body>
<p>Acta Nro: 1</p><p>Régimen Penal Juvenil.</p>
<a href="/x">CD-33/25-PL</a>, <a href="/y">O.D. 705/2025</a>
<p>27/02/2026</p><p>- 18:17</p><p>SIMPLE</p><p>AFIRMATIVO</p><p>EN GENERAL</p>
<p>3</p><p>AFIRMATIVOS</p><p>1</p><p>NEGATIVOS</p><p>0</p><p>ABSTENCIONES</p><p>0</p><p>AUSENTES</p>
<p>Datos abiertos:</p>
<table><tr><td></td><td>PEREZ, A</td><td>LA LIBERTAD AVANZA</td><td>CORDOBA</td><td>AFIRMATIVO</td></tr>
<tr><td></td><td>GOMEZ, B</td><td>LA LIBERTAD AVANZA</td><td>JUJUY</td><td>AFIRMATIVO</td></tr>
<tr><td></td><td>RUIZ, C</td><td>JUSTICIALISTA</td><td>LA RIOJA</td><td>AFIRMATIVO</td></tr>
<tr><td></td><td>DIAZ, D</td><td>JUSTICIALISTA</td><td>CHACO</td><td>NEGATIVO</td></tr></table>
</body></html>"""


def test_parser_de_cabecera_del_senado():
    c = politica._parsear_cabecera_acta_senado(HTML_SENADO)
    assert c["titulo"] == "Régimen Penal Juvenil."
    assert c["expedientes"] == ["CD-33/25-PL"] and c["ods"] == ["O.D. 705/2025"]
    assert c["fecha"] == "2026-02-27" and c["resultado"] == "AFIRMATIVO" and c["etapa"] == "EN GENERAL"
    assert c["afirmativos_encabezado"] == 3


HTML_SENADO_MOCION = HTML_SENADO.replace("SIMPLE</p><p>AFIRMATIVO</p><p>EN GENERAL</p>",
                                         "DOS TERCIOS DE MIEMBROS PRESENTES</p><p>CANCELADA LEV.VOT.</p><p>HABILITACIÓN TRAT SOBRE TABLAS</p>")
HTML_SENADO_EMPATE = HTML_SENADO.replace("SIMPLE</p><p>AFIRMATIVO</p><p>EN GENERAL</p>", "SIMPLE</p><p>EMPATE</p><p>OTRA</p>")


def test_cabecera_del_senado_con_resultados_que_no_son_ni_afirmativo_ni_negativo():
    # un acta con resultado raro (empate, votación cancelada) NO puede tumbar la lectura entera
    c = politica._parsear_cabecera_acta_senado(HTML_SENADO_MOCION)
    assert c["resultado"] == "CANCELADA LEV.VOT." and c["etapa"] == "HABILITACIÓN TRAT SOBRE TABLAS"
    c = politica._parsear_cabecera_acta_senado(HTML_SENADO_EMPATE)
    assert c["resultado"] == "EMPATE" and c["etapa"] == "OTRA"
    assert politica._vsb_excedente({**c, "afirmativos": 40, "bancas_lla": 9, "lla_afirm": 9, "lla_neg": 0,
                                    "expedientes": ["S-1/26-PL"]}, "senado") is None


def test_el_senador_con_el_bloque_en_blanco_se_cuenta():
    # Recalde figura sin bloque en varias actas: _parsear_acta lo descarta y los votos totales quedan en 71
    html = HTML_SENADO.replace("<td>DIAZ, D</td><td>JUSTICIALISTA</td>", "<td>DIAZ, D</td><td></td>")
    assert len(politica._parsear_acta(html)) == 3
    filas = politica._vsb_filas_senado(html)
    assert len(filas) == 4
    assert politica._vsb_conteos(filas)["afirmativos"] == 3


def test_una_entrada_vieja_del_cache_del_senado_se_vuelve_a_leer(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "VSB_ACTAS_PATH", tmp_path / "vsb.json")
    pedidos = []

    class R:
        text = HTML_SENADO

    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: (
        [{"id": "2665", "fecha": __import__("datetime").datetime(2026, 2, 27)}] if anio == 2026 else []))
    monkeypatch.setattr(politica, "_paced_get", lambda s, b, path, **k: pedidos.append(path) or R())
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: object())
    cache = politica._vsb_cargar_cache()
    cache["senado"]["2665"] = {"fecha": "2026-02-27", "titulo": "x", "resultado": "AFIRMATIVO"}   # sin "v"
    assert politica._vsb_actualizar_senado(cache) is True
    assert len(pedidos) == 1 and cache["senado"]["2665"]["v"] == politica.VSB_VERSION_SENADO


def test_el_senado_se_guarda_de_a_una_acta_y_no_vuelve_a_pedir_lo_cacheado(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "VSB_ACTAS_PATH", tmp_path / "vsb.json")
    pedidos = []

    class R:
        text = HTML_SENADO

    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: (
        [{"id": "2665", "fecha": __import__("datetime").datetime(2026, 2, 27)}] if anio == 2026 else []))
    monkeypatch.setattr(politica, "_paced_get", lambda s, b, path, **k: pedidos.append(path) or R())
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: object())
    cache = politica._vsb_cargar_cache()
    assert politica._vsb_actualizar_senado(cache) is True
    e = politica._vsb_cargar_cache()["senado"]["2665"]
    assert (e["bancas_lla"], e["lla_afirm"], e["lla_neg"], e["afirmativos"], e["bancas_camara"]) == (2, 2, 0, 3, 4)
    assert politica._vsb_excedente(e, "senado") is None          # sin origen resuelto no cuenta
    assert politica._vsb_excedente({**e, "origen_pe": True}, "senado") == pytest.approx((3 - 2) / 4 * 100)
    n = len(pedidos)
    assert politica._vsb_actualizar_senado(politica._vsb_cargar_cache()) is True
    assert len(pedidos) == n, "una acta ya cacheada no se vuelve a descargar"


def test_si_el_detalle_de_un_acta_falla_la_lectura_queda_incompleta(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "VSB_ACTAS_PATH", tmp_path / "vsb.json")
    monkeypatch.setattr(politica, "_descubrir_actas_senado", lambda s, anio: (
        [{"id": "1", "fecha": __import__("datetime").datetime(2026, 2, 27)}] if anio == 2026 else []))
    monkeypatch.setattr(politica, "_paced_get", lambda *a, **k: None)
    monkeypatch.setattr(politica, "_hcdn_votaciones_session", lambda: object())
    assert politica._vsb_actualizar_senado(politica._vsb_cargar_cache()) is False


# ── la cabecera del PDF de Diputados ─────────────────────────────────────────

TEXTO_PDF = """HHoonnoorraabbllee CCáámmaarraa ddee DDiippuuttaaddooss ddee llaa NNaacciióónn
VVoottaacciióónn NNoommiinnaall
144° - Período Ordinario - 4° Sesión Especial - 5° Reunión
O.D. 149 - RÉGIMEN DE INCENTIVO PARA GRANDES INVERSIONES. DICT. DE MAY. VOT. EN GRAL.
Acta Nº 13 Ult.Mod.Ver 1 Fecha: 24/06/2026 Hora: 23:38
Base Mayoría: VVoottooss EEmmiittiiddooss Tipo Mayoría: MMááss ddee llaa mmiittaadd Miembros del Cuerpo: 257
Resultado de Votación: AAFFIIRRMMAATTIIVVOO Presidente: MMEENNEEMM,, MMAARRTTIINN
Votando Sin votar Total Diputados Presidente Desempate Total
Presentes 240 1 241 Afirmativos 131 0 0 131
Ausentes 16 Negativos 107 0 0 107"""


class _Pagina:
    def extract_text(self):
        return TEXTO_PDF


class _Pdf:
    pages = [_Pagina()]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_cabecera_del_pdf_de_diputados(monkeypatch):
    monkeypatch.setattr(politica.pdfplumber, "open", lambda *_: _Pdf())
    c = politica._cabecera_acta_diputados_pdf(b"%PDF")
    assert c == {"fecha": "2026-06-24", "titulo": "O.D. 149 - RÉGIMEN DE INCENTIVO PARA GRANDES INVERSIONES. DICT. DE MAY. VOT. EN GRAL.",
                 "resultado": "AFIRMATIVO", "bancas_camara": 257, "afirmativos_encabezado": 131}


def test_quitar_duplicado_solo_toca_texto_totalmente_duplicado():
    assert politica._quitar_duplicado("AAFFIIRRMMAATTIIVVOO") == "AFIRMATIVO"
    assert politica._quitar_duplicado("AFIRMATIVO") == "AFIRMATIVO"
    assert politica._quitar_duplicado("O.D. 149 - RÉGIMEN") == "O.D. 149 - RÉGIMEN"


# ── entra al ITCP, a medias con la cohesión ──────────────────────────────────

def test_la_dimension_se_reparte_mitad_y_mitad():
    dim = itcp.DIMENSIONES_ITCP["cohesion_interna"]
    assert dim["indicadores"] == {"cohesion_bloque": 0.5, "votos_sobre_bancas": 0.5}
    assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9
    # cohesión baja a ~8 % del índice (lo que pidió Luis): peso de la dimensión × 0,5
    assert dim["peso"] * 0.5 == pytest.approx(0.0806, abs=1e-3)


def test_votos_sobre_bancas_es_capacidad_tiene_banda_y_rezago():
    assert itcp.FAMILIAS_ITCP["votos_sobre_bancas"] == "capacidad"
    assert "votos_sobre_bancas" in itcp.BANDAS_ITCP
    assert itcp.REZAGO_MESES_ITCP["votos_sobre_bancas"] == 6.0


def test_anclas_convencion_40_30_20_10_5():
    bandas = itcp.BANDAS_ITCP["votos_sobre_bancas"]
    f = parametrica.puntaje_interpolado
    assert f(60.0, bandas) == 100.0 and f(40.0, bandas) == 100.0
    assert f(30.0, bandas) == 85.0
    assert f(20.0, bandas) == 65.0
    assert f(10.0, bandas) == 40.0
    assert f(5.0, bandas) == 10.0 and f(0.0, bandas) == 10.0 and f(-3.0, bandas) == 10.0
    # entre anclas, lineal: 25 % está a mitad de camino entre 65 y 85
    assert f(25.0, bandas) == 75.0
    # más alto = mejor: monótona
    valores = [f(x / 2, bandas) for x in range(0, 100)]
    assert valores == sorted(valores)


def test_el_indicador_pesa_igual_que_la_cohesion_en_el_itcp():
    r = itcp.calcular_itcp({"cohesion_bloque": 97.0, "votos_sobre_bancas": 20.0, "ratio_dnu": 0.5})
    dim = r["dimensiones"]["cohesion_interna"]
    ind = dim["indicadores"]
    assert ind["cohesion_bloque"]["peso_efectivo"] == pytest.approx(ind["votos_sobre_bancas"]["peso_efectivo"])
    # el puntaje de la dimensión es el promedio simple de los dos
    assert dim["puntaje"] == pytest.approx((ind["cohesion_bloque"]["puntaje_aplicado"]
                                           + ind["votos_sobre_bancas"]["puntaje_aplicado"]) / 2, abs=0.1)
    # si falta uno, el otro lleva la dimensión entera (se renormaliza, no se inventa)
    solo = itcp.calcular_itcp({"cohesion_bloque": 97.0, "ratio_dnu": 0.5})["dimensiones"]["cohesion_interna"]
    assert solo["puntaje"] == ind["cohesion_bloque"]["puntaje_aplicado"]


# ── sólo cuentan las leyes cuyo proyecto mandó el Poder Ejecutivo (ADR-0376) ──

def test_una_ley_de_origen_legislativo_no_cuenta():
    # misma votación, mismos números: sólo cambia quién mandó el proyecto
    assert politica._vsb_excedente(dip(origen_pe=True), "diputados") is not None
    assert politica._vsb_excedente(dip(origen_pe=False), "diputados") is None
    assert politica._vsb_excedente(sen(origen_pe=False), "senado") is None
    # origen sin resolver (dictamen todavía no cargado) tampoco cuenta
    assert politica._vsb_excedente(dip(origen_pe=None), "diputados") is None
    sin_campo = dip()
    del sin_campo["origen_pe"]
    assert politica._vsb_excedente(sin_campo, "diputados") is None


def test_el_promedio_ignora_las_leyes_de_consenso_de_origen_legislativo():
    actas = {"1": dip(fecha="2026-06-01", afirmativos=131),
             "2": dip(fecha="2026-06-02", afirmativos=240, origen_pe=False)}   # capital nacional, 240 votos
    r = politica.votos_sobre_bancas_camara(actas, "diputados", date(2026, 7, 1))
    assert r["n_actas"] == 1 and r["valor"] == pytest.approx(37 / 257 * 100)


INDICE = {"ids": {"HCDN1"}, "claves": {("CD", 33, 2025)},
          "dictamenes": {448: [("2026-09-01", "HCDN1")], 7: [("2025-01-10", "HCDN1"), ("2026-03-01", "HCDN9")]}}


def test_origen_en_el_senado():
    f = politica._vsb_origen_pe_senado
    # el Ejecutivo entra por el Senado: la sigla alcanza, sin catálogo
    assert f({"expedientes": ["PE-159/25-PL"]}, None) is True
    assert f({"expedientes": ["JGM-1/25-PL"]}, None) is True
    # viene de Diputados: se mira cómo numera el catálogo ese proyecto
    assert f({"expedientes": ["CD-33/25-PL"]}, INDICE) is True
    assert f({"expedientes": ["CD-34/25-PL"]}, INDICE) is False
    assert f({"expedientes": ["CD-33/25-PL"]}, None) is None
    # una S del Senado no es la S de la numeración de Diputados: no se cruza
    assert f({"expedientes": ["S-33/25-PL"]}, {**INDICE, "claves": {("S", 33, 2025)}}) is False
    # sin expediente propio, el de su Orden del Día
    assert f({"expedientes": [], "expedientes_od": ["CD-33/25-PL"]}, INDICE) is True
    assert f({"expedientes": [], "expedientes_od": []}, INDICE) is False
    # un pliego (-AC) no es proyecto de ley
    assert f({"expedientes": ["PE-175/25-AC"]}, INDICE) is False


def test_origen_en_diputados_cruza_el_numero_de_orden_del_dia():
    f = politica._vsb_origen_pe_diputados
    e = {"titulo": "O.D. 448 - LEY X. VOT. EN GRAL.", "fecha": "2026-10-21"}
    assert f(e, INDICE) is True                                   # dictamen 448 → HCDN1, del Ejecutivo
    assert f({**e, "titulo": "O.D. 999 - LEY X. VOT. EN GRAL."}, INDICE) is None   # dictamen no cargado: se reintenta
    assert f({**e, "titulo": "EMERGENCIA EN BAHÍA BLANCA. VOT. EN GRAL."}, INDICE) is False   # sin O.D. no se cruza
    assert f(e, None) is None
    # la numeración se reinicia cada período: el O.D. 7 de 2025 no es el O.D. 7 de 2026
    assert f({"titulo": "O.D. 7 - LEY Y", "fecha": "2026-04-09"}, INDICE) is False   # dictamen de 2026-03 (HCDN9)
    assert f({"titulo": "O.D. 7 - LEY Y", "fecha": "2026-12-01"}, {**INDICE, "dictamenes": {7: [("2025-01-10", "HCDN1")]}}) is None


def test_el_origen_se_guarda_en_el_cache_y_no_se_vuelve_a_resolver(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "VSB_ACTAS_PATH", tmp_path / "vsb.json")
    llamadas = []
    monkeypatch.setattr(politica, "_vsb_indice_origen_pe", lambda: llamadas.append(1) or INDICE)
    cache = {"diputados": {"1": {**dip(titulo="O.D. 448 - LEY X. VOT. EN GRAL.", fecha="2026-10-21"), "origen_pe": None},
                           "2": {**dip(titulo="MOCIÓN SOLICITADA POR LA DIP. X."), "origen_pe": None}},
             "senado": {}, "diputados_ausentes": []}
    del cache["diputados"]["1"]["origen_pe"], cache["diputados"]["2"]["origen_pe"]
    assert politica._vsb_resolver_origen(cache) is True
    assert cache["diputados"]["1"]["origen_pe"] is True
    assert "origen_pe" not in cache["diputados"]["2"]          # no es candidata: no se resuelve
    assert len(llamadas) == 1
    assert politica._vsb_resolver_origen(cache) is True
    assert len(llamadas) == 1, "lo ya resuelto no vuelve a bajar el catálogo"


def test_si_el_catalogo_de_origen_falla_la_lectura_queda_incompleta(monkeypatch, tmp_path):
    monkeypatch.setattr(politica, "VSB_ACTAS_PATH", tmp_path / "vsb.json")

    def roto():
        raise RuntimeError("CKAN caído")

    monkeypatch.setattr(politica, "_vsb_indice_origen_pe", roto)
    cache = {"diputados": {"1": dip(titulo="O.D. 448 - LEY X. VOT. EN GRAL.", fecha="2026-10-21")},
             "senado": {}, "diputados_ausentes": []}
    del cache["diputados"]["1"]["origen_pe"]
    assert politica._vsb_resolver_origen(cache) is False
    assert "origen_pe" not in cache["diputados"]["1"] or cache["diputados"]["1"]["origen_pe"] is None


def test_clave_de_expediente_en_los_dos_formatos():
    assert politica._vsb_clave_expediente("CD-33/25-PL") == ("CD", 33, 2025)
    assert politica._vsb_clave_expediente("0033-CD-2025") == ("CD", 33, 2025)
    assert politica._vsb_clave_expediente("") is None


# ── tratados y convenios internacionales: fuera, aunque los mande el Ejecutivo ──

@pytest.mark.parametrize("titulo", [
    "O.D. 16 - TRATADO DE EXTRADICIÓN ENTRE LA REP. ARGENTINA Y LA REP. DE POLONIA. APROBACIÓN. VOT. EN GRAL. Y PART.",
    "O.D. 8 - CONVENIO SOBRE COBRO INTERNACIONAL DE ALIMENTOS PARA LOS NIÑOS. APROBACIÓN. VOT. EN GRAL. Y PART.",
    "O.D. 86 - PROTOCOLO DE ENMIENDA AL CONVENIO ENTRE EL GOBIERNO DE LA REP. ARGENTINA Y EL GOB. DE LA REP. FRANCESA. VOT. EN GRAL.",
    "O.D. 87 - ACUERDO SOBRE MEDIDAS DEL ESTADO RECTOR DEL PUERTO. VOT. EN GRAL. Y PART. ACUERDO INTERNACIONAL",
    "O.D. 208 - ACUERDO DE LIBRE COMERCIO E/ EL MERCOSUR Y LA REP. DE SINGAPUR. VOT. EN GRAL. Y PART.",
    "O.D. 88 - CONVENIOS DE SEGURIDAD SOCIAL ENTRE LA REPÚBLICA ARGENTINA Y LA CONFEDERACIÓN SUIZA. VOT. EN GRAL.",
])
def test_una_votacion_de_tratado_no_cuenta_en_diputados(titulo):
    assert politica._vsb_es_tratado(titulo)
    assert politica._vsb_excedente(dip(titulo=titulo, origen_pe=True), "diputados") is None


@pytest.mark.parametrize("titulo", [
    "Aprobación de acuerdo con la República de Turquía, de convenio con la República Popular China.",
    "Aprobación del Convenio Internacional de Nairobi sobre remoción de restos de naufragio.",
    "Protocolo de enmienda al convenio con Francia para eliminar la doble imposición.",
    "Acuerdo de Roma, sobre medidas destinadas a prevenir, desalentar y eliminar la pesca ilegal.",
    "Tratado con Ucrania sobre Traslado de Personas Sentenciadas.",
    "Acuerdo de Libre Comercio entre el Mercosur y la Unión Europea.",
    "Tratados Internacionales con Singapur, Suiza y la República de San Marino.",
])
def test_una_votacion_de_tratado_no_cuenta_en_el_senado(titulo):
    assert politica._vsb_es_tratado(titulo)
    assert politica._vsb_excedente(sen(titulo=titulo, expedientes=["PE-1/26-PL"], origen_pe=True), "senado") is None


@pytest.mark.parametrize("titulo", [
    "Acuerdo de conciliación con acreedores de títulos de deuda.",
    "O.D. 148 - AC. DE CONCILIACIÓN E/ LA REP. ARG. Y BAINBRIDGE LTD. Y E/ LA REP. ARG. Y EL GRUPO DE ACREED. VOT. EN GRAL.",
    "O.D. 90 - ACUERDO CON EL FONDO MONETARIO INTERNACIONAL. APROBACIÓN. VOT. EN GRAL.",
    "O.D. 91 - CONVENIO DE PRÉSTAMO ENTRE LA REP. ARGENTINA Y EL BANCO INTERAMERICANO DE DESARROLLO. VOT. EN GRAL.",
])
def test_los_acuerdos_de_agenda_economica_no_se_excluyen_como_tratados(titulo):
    assert not politica._vsb_es_tratado(titulo)


def test_el_acuerdo_con_acreedores_y_el_del_fmi_cuentan_y_se_listan_aparte():
    fmi = "O.D. 90 - ACUERDO CON EL FONDO MONETARIO INTERNACIONAL. APROBACIÓN. VOT. EN GRAL."
    assert politica._vsb_es_acuerdo_economico(fmi)
    assert politica._vsb_excedente(dip(titulo=fmi), "diputados") is not None
    conciliacion = "O.D. 148 - AC. DE CONCILIACIÓN E/ LA REP. ARG. Y BAINBRIDGE LTD. VOT. EN GRAL."
    assert politica._vsb_es_acuerdo_economico(conciliacion)
    assert politica._vsb_excedente(dip(titulo=conciliacion), "diputados") is not None


@pytest.mark.parametrize("titulo", [
    "O.D. 442 - INMUEBLE PROP. DEL ESTADO NAC. TRANSFERENCIA A TÍTULO GRATUITO A LA PROV. DEL CHACO.",
    "O.D. 12 - CONVENIO ENTRE EL ESTADO NACIONAL Y LA CIUDAD AUTÓNOMA DE BUENOS AIRES. RATIFICACIÓN. VOT. EN GRAL.",
    "O.D. 13 - CONVENIO COLECTIVO DE TRABAJO. HOMOLOGACIÓN. VOT. EN GRAL.",
    "O.D. 211 - CARTA ORGÁNICA DEL BCRA. MODIFICACIÓN. DICT. DE MAY. VOT. EN GRAL.",
    "O.D. 3 - LEY DE INOCENCIA FISCAL. DICT. DE MAY. VOT. EN GRAL.",
])
def test_los_convenios_internos_y_las_leyes_comunes_no_se_toman_por_tratados(titulo):
    assert not politica._vsb_es_tratado(titulo)


def test_sacar_los_tratados_cambia_el_promedio():
    actas = {"1": dip(fecha="2026-06-01", afirmativos=131),
             "2": dip(fecha="2026-06-02", afirmativos=235, titulo="O.D. 17 - TRATADO DE EXTRADICIÓN ENTRE LA REP. ARGENTINA Y LA REP. DE CHILE. VOT. EN GRAL.")}
    r = politica.votos_sobre_bancas_camara(actas, "diputados", date(2026, 7, 1))
    assert r["n_actas"] == 1 and r["valor"] == pytest.approx(37 / 257 * 100)
