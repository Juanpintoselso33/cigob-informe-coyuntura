"""ratio_dnu sin tratados y con el conteo completo de DNU (ADR-0415).

Un tratado con otro país o con un organismo internacional sólo lo aprueba el
Congreso (arts. 75 inc. 22 y 99 inc. 11 de la Constitución): no hay decreto
que lo reemplace, así que esas leyes salen del denominador. Los sumarios son
los reales de InfoLeg; los dudosos son los que Juan decidió el 29-oct-2026.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series  # noqa: E402
import politica  # noqa: E402


# ── La regla de texto ────────────────────────────────────────────────────────

TRATADOS = [
    # tratado bilateral con encabezado TRATADOS
    "TRATADOS TRATADO DE EXTRADICION ENTRE LA REPUBLICA ARGENTINA Y LA REPUBLICA DE CHILE "
    "APRUEBASE EL TRATADO DE EXTRADICION ENTRE LA REPUBLICA ARGENTINA Y LA REPUBLICA DE CHILE, "
    "SUSCRIPTO EN LA CIUDAD DE SANT...",
    # acuerdo comercial del Mercosur
    "MERCOSUR ACUERDO - APROBACION APRUEBASE EL ACUERDO INTERINO DE COMERCIO ENTRE EL MERCADO "
    "COMUN DEL SUR, LA REPUBLICA ARGENTINA, LA REPUBLICA FEDERATIV...",
    # convenio de seguridad social con otro Estado
    "CONVENIOS APROBACION APRUEBANSE EL CONVENIO DE SEGURIDAD SOCIAL ENTRE LA REPUBLICA ARGENTINA "
    "Y LA CONFEDERACION SUIZA, QUE CONSTA DE TREINTA ...",
    # acuerdo con un organismo internacional (la secretaría de un convenio)
    "ACUERDOS APROBACION APRUEBASE EL ACUERDO MARCO ENTRE LA REPUBLICA ARGENTINA Y LA SECRETARIA "
    "DEL CONVENIO DE BASILEA SOBRE EL CONTROL DE LOS ...",
    # convenio multilateral de la Organización Internacional del Trabajo
    "CONVENIOS CONVENIO SOBRE EL TRABAJO EN EL SECTOR PESQUERO APRUEBASE EL CONVENIO SOBRE EL "
    "TRABAJO EN EL SECTOR PESQUERO CONVENIO 188, ADOPTADO POR LA CONFERENCIA GENERAL DE LA O...",
    # sin contraparte nombrada, pero la materia sólo se acuerda con otro Estado
    "ACUERDOS COOPERACION EN LOS USOS PACIFICOS DE LA ENERGIA NUCLEAR ACUERDO SOBRE COOPERACION "
    "EN LOS USOS PACIFICOS DE LA ENERGIA NUCLEAR. APROBACION.",
    # el encabezado CONVENCIONES ya nombra un instrumento internacional
    "CONVENCIONES CONVENCION PARA REDUCIR LOS CASOS DE APATRIDIA CONVENCION PARA REDUCIR LOS "
    "CASOS DE APATRIDIA. APROBACION.",
    # 27.028: el resumen no nombra a la otra parte, pero anota la entrada en
    # vigor conforme a la ley que regula la publicación de los tratados
    "ACUERDOS COOPERACION EN MATERIA DE TELECOMUNICACIONES, SERVICIOS POSTALES Y SEGURIDAD INFO "
    "APRUEBASE ACUERDO SOBRE COOPERACION EN MATERIA DE TELECOMUNICACIONES, SERVICIOS POSTALES Y "
    "SEGURIDAD DE LA INFORMACION Y DE LAS REDES. Observaciones: ENTRADA EN VIGOR: 12/06/2015. "
    "PUBLICACION CONFORME LEY Nº 24.080 - B.O. 19/06/2015, PAG. 67.",
    # 26.986, con el resumen completo: modifica el convenio constitutivo de FONPLATA
    "FONDO FINANCIERO PARA EL DESARROLLO DE LA CUENCA DEL PLATA AUMENTO DE LOS RECURSOS DE CAPITAL "
    "Y MODIFICACIONES AL CONVENIO CONSTITUTIVO - APROBACION APRUEBASE EL AUMENTO DE LOS RECURSOS "
    "DE CAPITAL DEL FONDO FINANCIERO PARA EL DESARROLLO DE LA CUENCA DEL PLATA (FONPLATA) "
    "APRUEBANSE LAS MODIFICACIONES AL CONVENIO CONSTITUTIVO DEL FONDO FINANCIERO PARA EL "
    "DESARROLLO DE LA CUENCA DEL PLATA, CONTENIDAS EN LA RESOLUCION A.G. N° 137/2013.",
    # 27.531, decidido: protocolo de la Unión Postal Universal
    "UNION POSTAL UNIVERSAL APROBACION APRUEBASE EL OCTAVO PROTOCOLO ADICIONAL A LA CONSTITUCION "
    "DE LA UNION POSTAL UNIVERSAL, QUE CONSTA DE DIEZ (10) ARTICULOS, ADOPTADOS POR EL 24° "
    "CONGRESO DE LA UNION POSTAL UNIVERSAL EN LA CIUDAD DE GINEBRA -CONFEDERACION SUIZA-",
    # 27.699, decidido: con el resumen completo dice dónde se suscribió
    "PROTECCION DE LAS PERSONAS CON RESPECTO AL TRATAMIENTO AUTOMATIZADO DE DATOS DE CARACTER "
    "PERSONAL PROTOCOLO - APRUEBASE APRUEBASE EL PROTOCOLO MODIFICATORIO DEL CONVENIO PARA LA "
    "PROTECCION DE LAS PERSONAS CON RESPECTO AL TRATAMIENTO AUTOMATIZADO DE DATOS DE CARACTER "
    "PERSONAL, SUSCRIPTO EN LA CIUDAD DE ESTRASBURGO REPUBLICA FRANCESA EL 10 DE OCTUBRE DE 2018",
]

NO_TRATADOS = [
    # leyes comunes
    "REGIMEN DE ZONA FRIA MODIFICACION SUSTITUYESE EL ARTICULO 75 DE LA LEY 25.565",
    "LEY DE MODERNIZACION LABORAL DISPOSICIONES LEY DE MODERNIZACION LABORAL.",
    "DECLARACIONES OFICIALES CAPITAL SIMBOLICA DE LA REPUBLICA ARGENTINA DECLARASE A LA CIUDAD DE "
    "SAN MIGUEL DE TUCUMAN, PROVINCIA DE TUCUMAN, COMO CAPITA",
    # Nación con una provincia: no es un tratado internacional
    "ACUERDOS ACUERDO - RATIFICASE RATIFICASE EL ACUERDO SUSCRIPTO CON FECHA 1° DE AGOSTO DE 2016 "
    "ENTRE EL ESTADO NACIONAL Y LA PROVINCIA DE SANTA CRUZ, QUE COMO ANEXO I FORMA PARTE",
    # aunque se llame «tratado»: parque interjurisdiccional con una provincia
    "TRATADOS PARQUE INTERJURISDICCIONAL MARINO ISLA PINGÜINO APRUEBASE EL TRATADO DE CREACION "
    "DEL PARQUE INTERJURISDICCIONAL MARINO ISLA PINGÜINO SUSCRIPTO ENTRE EL ESTADO NACIONAL Y LA "
    "PROVINCIA DE SANTA CRUZ.",
    "CONSEJO FEDERAL LEGISLATIVO DE SALUD PACTO FEDERAL LEGISLATIVO - APROBACION APRUEBASE EL "
    "PACTO FEDERAL LEGISLATIVO DE SALUD QUE COMO ANEXO I FORMA PARTE INTEGRANTE DE LA PRESENTE LEY.",
    # Nación con la Ciudad de Buenos Aires (26.935, con el resumen completo)
    "CONVENIOS CONVENIO - RATIFICASE RATIFICASE EL CONVENIO CELEBRADO ENTRE EL ESTADO NACIONAL, "
    "REPRESENTADO POR EL SEÑOR JEFE DE GABINETE DE MINISTROS, Y LA CIUDAD AUTONOMA DE BUENOS "
    "AIRES, REPRESENTADA POR LA SEÑORA VICEJEFA DE GOBIERNO, SUSCRIPTO EL 22 DE ENERO DE 2014.",
    # otorgar jerarquía constitucional no es aprobar un tratado (27.700 y 27.044)
    "CONVENCION INTERAMERICANA SOBRE PROTECCION DE DERECHOS HUMANOS DE LAS PERSONAS MAYORES "
    "JERARQUIA CONSTITUCIONAL - OTORGASE OTORGASE JERARQUIA CONSTITUCIONAL EN LOS TERMINOS DEL "
    "ARTICULO 75 INCISO 22 DE LA CONSTITUCION NACIONAL, A LA CONVENCION INTERAMERICANA SOBRE "
    "PROTECCION DE DERECHOS HUMANOS DE LAS PERSONAS MAYORES, ADOPTADA POR LA ORGANIZACION DE LOS "
    "ESTADOS AMERICANOS Y APROBADA POR LEY 27.360.",
    "JERARQUIA CONSTITUCIONAL CONVENCION SOBRE LOS DERECHOS DE LAS PERSONAS CON DISCAPACIDAD "
    "OTORGASE JERARQUIA CONSTITUCIONAL EN LOS TERMINOS DEL ARTICULO 75, INCISO 22 DE LA "
    "CONSTITUCION NACIONAL, A LA CONVENCION SOBRE LOS DERECHOS DE LAS PERSONAS CON DISCAPACIDAD.",
    # 26.745: aprueba un aumento del aporte al capital del BID, no un instrumento
    "ORGANISMOS INTERNACIONALES CAPITAL AUTORIZADO DEL BANCO INTERAMERICANO DE DESARROLLO - "
    "AUMENTO DEL APORTE APRUEBASE EL AUMENTO DEL APORTE DE LA REPUBLICA ARGENTINA AL CAPITAL "
    "AUTORIZADO DEL BANCO INTERAMERICANO DE DESARROLLO.",
    # un encabezado de instrumento sin verbo de aprobación no alcanza (27.778:
    # sólo corrige el nombre de un convenio de La Haya ya aprobado)
    "CONVENIOS LEY 27.237 - MODIFICACION SUSTITUYESE EN EL ARTICULO 1º DE LA LEY 27.237 LA "
    "DENOMINACION CONVENCION RELATIVA A LA COMPETENCIA, LA LEY APLICABLE, EL RECONOCIMIENTO "
    "POR CONVENIO DE LA HAYA DE 19 DE OCTUBRE DE 1996",
    # 27.818, decidido: conciliación con una empresa extranjera
    "ACUERDOS APROBACION APRUEBASE EL ACUERDO DE CONCILIACION CELEBRADO ENTRE LA REPUBLICA "
    "ARGENTINA Y BAINBRIDGE LTD. QUE COMO ANEXO I (IF-2026-39097258-APN-DSGA#SLYT) FORMA PARTE",
    # 27.668, decidido: operaciones de crédito público con el FMI
    "PROGRAMA DE FACILIDADES EXTENDIDAS DISPOSICIONES APRUEBANSE, DE ACUERDO A LO ESTIPULADO EN EL "
    "ARTICULO 75, INCISO 7, DE LA CONSTITUCION NACIONAL Y EN LOS TERMINOS DEL ARTICULO 2° DE LA "
    "LEY 27.612, LAS OPERACIONES DE CREDITO PUBLICO CONTENIDAS EN EL PROGRAMA DE FACILIDADES "
    "EXTENDIDAS A CELEBRARSE ENTRE EL PODER EJECUTIVO NACIONAL Y EL FONDO MONETARIO INTERNACIONAL",
    # 26.932, decidido: el convenio con Repsol por la expropiación de YPF
    "YACIMIENTOS PETROLIFEROS FISCALES RATIFICASE CONVENIO DECLARASE CUMPLIDO EL OBJETIVO DE LOS "
    "ARTICULOS 7°, 11 Y 12 DE LA LEY 26.741 Y EN CONSECUENCIA RATIFICASE EL CONVENIO DE SOLUCION "
    "AMIGABLE Y AVENIMIENTO DE EXPROPIACION CELEBRADO ENTRE LA REPUBLICA ARGENTINA, REPRESENTADA "
    "POR EL MINISTERIO DE ECONOMIA Y FINANZAS PUBLICAS Y REPSOL S.A.",
]


@pytest.mark.parametrize("sumario", TRATADOS)
def test_aprueba_un_tratado(sumario):
    assert politica.clasificar_ley_tratado(sumario) == "tratado"


@pytest.mark.parametrize("sumario", NO_TRATADOS)
def test_no_aprueba_un_tratado(sumario):
    assert politica.clasificar_ley_tratado(sumario) == "no"


def test_sin_contraparte_queda_indeterminado():
    """Un convenio que no dice con quién no se resuelve adivinando."""
    s = "CONVENIOS CONVENIO DE COLABORACION Y COOPERACION - APROBACION APRUEBASE EL CONVENIO DE COLABORACION"
    assert politica.clasificar_ley_tratado(s) == "indeterminado"


@pytest.mark.parametrize("numero,es", [
    ("26932", False), ("27668", False), ("27818", False), ("27531", True), ("27699", True)])
def test_los_dudosos_decididos_quedan_fijos(numero, es):
    """La tabla fija la decisión aunque InfoLeg reescriba el sumario; con
    un sumario que diga lo contrario, igual manda la tabla."""
    item = {"infoleg_id": "1", "norma": f"Ley {numero} HONORABLE CONGRESO",
            "sumario": "REGIMEN DE ZONA FRIA" if es else "TRATADOS TRATADO ENTRE LA REPUBLICA ARGENTINA Y JAPON"}
    assert politica._es_ley_de_tratado(None, item) is es


# ── Sumario recortado: se lee el resumen completo, y si falla se corta ──────

class _Resp:
    def __init__(self, texto, status=200):
        self.text, self.status_code = texto, status
        self.encoding, self.apparent_encoding = "utf-8", "utf-8"


class _SesFichas:
    def __init__(self, fichas):
        self.fichas, self.pedidos = fichas, []

    def get(self, url, **kw):
        self.pedidos.append(url)
        iid = url.split("id=")[-1]
        if iid not in self.fichas:
            raise politica.requests.ConnectionError("caído")
        return _Resp(f"<html>Ley X Resumen: {self.fichas[iid]} Texto completo de la norma</html>")


@pytest.fixture
def _sin_memoria(monkeypatch):
    monkeypatch.setattr(politica, "_RESUMEN_LEY", {})
    monkeypatch.setattr(politica, "_PAUSA_TEXTO_INFOLEG", 0)


def test_recortado_se_completa_con_la_ficha(_sin_memoria):
    """26.935: la grilla corta antes de decir con quién; la ficha dice la Ciudad."""
    item = {"infoleg_id": "230646", "norma": "Ley 26935 HONORABLE CONGRESO",
            "sumario": "CONVENIOS CONVENIO - RATIFICASE RATIFICASE EL CONVENIO CELEBRADO ENTRE EL "
                       "ESTADO NACIONAL, REPRESENTADO POR EL SEÑOR JEFE DE GABINETE DE MINISTROS, Y LA..."}
    ses = _SesFichas({"230646": "RATIFICASE EL CONVENIO CELEBRADO ENTRE EL ESTADO NACIONAL Y LA "
                                "CIUDAD AUTONOMA DE BUENOS AIRES, SUSCRIPTO EL 22 DE ENERO DE 2014."})
    assert politica._es_ley_de_tratado(ses, item) is False
    assert "verNorma.do?id=230646" in ses.pedidos[0]


def test_recortado_internacional_tambien_se_completa(_sin_memoria):
    item = {"infoleg_id": "427762", "norma": "Ley 27815 HONORABLE CONGRESO",
            "sumario": "ACUERDOS APROBACION APRUEBASE EL ACUERDO SOBRE MEDIDAS DEL ESTADO RECTOR DEL "
                       "PUERTO DESTINADAS A PREVENIR, DESALENTAR Y ELIMINAR LA PESCA IL..."}
    ses = _SesFichas({"427762": "APRUEBASE EL ACUERDO ... CELEBRADO EN ROMA -REPUBLICA ITALIANA- "
                                "EL 22 DE NOVIEMBRE DE 2009."})
    assert politica._es_ley_de_tratado(ses, item) is True


def test_una_ficha_que_no_se_lee_corta_el_conteo(_sin_memoria):
    item = {"infoleg_id": "9", "norma": "Ley 27999 HONORABLE CONGRESO",
            "sumario": "ACUERDOS APROBACION APRUEBASE EL ACUERDO SOBRE ..."}
    with pytest.raises(RuntimeError):
        politica._es_ley_de_tratado(_SesFichas({}), item)


def test_si_ni_la_ficha_dice_con_quien_corta_y_nombra_la_ley(_sin_memoria):
    item = {"infoleg_id": "9", "norma": "Ley 27999 HONORABLE CONGRESO",
            "sumario": "CONVENIOS APROBACION APRUEBASE EL CONVENIO DE COLABORACION ..."}
    ses = _SesFichas({"9": "APRUEBASE EL CONVENIO DE COLABORACION QUE COMO ANEXO FORMA PARTE."})
    with pytest.raises(ValueError, match="27999"):
        politica._es_ley_de_tratado(ses, item)


def test_recortado_con_el_instrumento_antes_del_verbo_lee_la_ficha(_sin_memoria):
    """26.986: el convenio aparece antes del verbo y la grilla corta antes de
    nombrar a la otra parte; recortado, cualquier mención a un instrumento
    manda a la ficha."""
    item = {"infoleg_id": "235937", "norma": "Ley 26986 HONORABLE CONGRESO",
            "sumario": "FONDO FINANCIERO PARA EL DESARROLLO DE LA CUENCA DEL PLATA AUMENTO DE LOS "
                       "RECURSOS DE CAPITAL Y MODIFICACIONES AL CONVENIO CONSTITUTIVO - APROBACION "
                       "APRUEBASE EL AUMENTO DE LOS RECURSOS DE CAPITAL DEL FONDO FINANCIERO PARA "
                       "EL DESARROLLO DE LA CUENCA DEL PLATA (FONPLATA..."}
    ses = _SesFichas({"235937": "APRUEBASE EL AUMENTO DE LOS RECURSOS DE CAPITAL DEL FONDO FINANCIERO "
                                "PARA EL DESARROLLO DE LA CUENCA DEL PLATA (FONPLATA). APRUEBANSE LAS "
                                "MODIFICACIONES AL CONVENIO CONSTITUTIVO DEL FONDO FINANCIERO PARA EL "
                                "DESARROLLO DE LA CUENCA DEL PLATA."})
    assert politica._es_ley_de_tratado(ses, item) is True
    assert ses.pedidos, "tenía que leer la ficha"


def test_un_sumario_completo_no_pide_la_ficha(_sin_memoria):
    ses = _SesFichas({})
    item = {"infoleg_id": "1", "norma": "Ley 27801 HONORABLE CONGRESO",
            "sumario": "REGIMEN PENAL JUVENIL DISPOSICIONES EL OBJETO DE LA PRESENTE LEY ES..."}
    assert politica._es_ley_de_tratado(ses, item) is False
    assert ses.pedidos == []


# ── DNU: la unión de la búsqueda de texto y del rótulo ──────────────────────

def test_los_dnu_sin_la_frase_se_suman(monkeypatch):
    """El 609/2019 no dice «necesidad y urgencia» y la grilla lo rotula DNU:
    entra por el listado completo. Uno repetido en las dos fuentes cuenta una
    vez, y un decreto secreto de 1979 publicado tarde no cuenta."""
    texto = [{"infoleg_id": "1", "norma": "Decreto DNU 70 / 2023", "fecha_pub": "2023-12-21"},
             {"infoleg_id": "2", "norma": "Decreto 710 / 2023", "fecha_pub": "2023-12-22"}]
    rotulados = [{"infoleg_id": "1", "norma": "Decreto DNU 70 / 2023", "fecha_pub": "2023-12-21"},
                 {"infoleg_id": "3", "norma": "Decreto DNU 609 / 2019", "fecha_pub": "2019-09-01"},
                 {"infoleg_id": "4", "norma": "Decreto DNU 179 / 1979", "fecha_pub": "2013-04-29"}]
    monkeypatch.setattr(politica, "_infoleg_listado_completo", lambda *a, **k: list(texto))
    monkeypatch.setattr(politica, "_infoleg_decretos_rotulados_dnu", lambda *a, **k: list(rotulados))
    monkeypatch.setattr(politica, "_es_dnu_infoleg",
                        lambda s, it: politica._RE_INFOLEG_DNU.match(it["norma"]) is not None)
    n, dnus = politica._infoleg_contar_dnus(None, "x", date(2011, 1, 1), date(2023, 12, 31))
    assert n == 2
    assert [d["infoleg_id"] for d in dnus] == ["3", "1"]


def test_el_listado_de_rotulados_va_mes_a_mes(monkeypatch):
    tramos = []

    def fake(ses, au, tipo, desde, hasta, texto="", invisibles_tolerados=0):
        tramos.append((tipo, desde, hasta, texto))
        return [{"infoleg_id": str(len(tramos)), "norma": "Decreto DNU 1 / 2026"},
                {"infoleg_id": "x" + str(len(tramos)), "norma": "Decreto 2 / 2026"}]

    monkeypatch.setattr(politica, "_infoleg_listado_completo", fake)
    out = politica._infoleg_decretos_rotulados_dnu(None, "x", date(2025, 11, 15), date(2026, 1, 10))
    assert [(d, h) for _, d, h, _ in tramos] == [
        (date(2025, 11, 15), date(2025, 11, 30)), (date(2025, 12, 1), date(2025, 12, 31)),
        (date(2026, 1, 1), date(2026, 1, 10))]
    assert all(t == "2" and tx == "" for t, _, _, tx in tramos)
    assert len(out) == 3


# ── Card y serie cuentan con la misma función ───────────────────────────────

def _leyes_fake():
    return [
        {"infoleg_id": "a", "norma": "Ley 27824", "fecha_pub": "2026-09-18",
         "sumario": TRATADOS[0].rstrip(".") + " SUSCRIPTO EN SANTIAGO."},
        {"infoleg_id": "b", "norma": "Ley 27801", "fecha_pub": "2026-03-09",
         "sumario": "REGIMEN PENAL JUVENIL DISPOSICIONES"},
        {"infoleg_id": "c", "norma": "Ley 27818", "fecha_pub": "2026-07-01", "sumario": NO_TRATADOS[7]},
        {"infoleg_id": "d", "norma": "Ley 27700", "fecha_pub": "2025-06-01",
         "sumario": "LEY DE MINISTERIOS MODIFICACION"},
    ]


def _dnus_fake():
    return [{"infoleg_id": str(i), "norma": f"Decreto DNU {i} / 2026", "fecha_pub": f"2026-0{1 + i % 9}-10"}
            for i in range(6)] + [{"infoleg_id": "v", "norma": "Decreto DNU 9 / 2025", "fecha_pub": "2025-06-10"}]


@pytest.fixture
def _infoleg_fake(monkeypatch):
    pedidos = {"leyes": [], "dnus": []}

    def listado(ses, au, tipo, desde, hasta, texto="", invisibles_tolerados=0):
        assert tipo == "1"
        pedidos["leyes"].append((desde, hasta))
        return [dict(it) for it in _leyes_fake() if desde.isoformat() <= it["fecha_pub"] <= hasta.isoformat()]

    def contar(ses, au, desde, hasta):
        pedidos["dnus"].append((desde, hasta))
        d = [it for it in _dnus_fake() if desde.isoformat() <= it["fecha_pub"] <= hasta.isoformat()]
        return len(d), d

    monkeypatch.setattr(politica, "_infoleg_abrir_sesion", lambda: (None, "x"))
    monkeypatch.setattr(politica, "_infoleg_listado_completo", listado)
    monkeypatch.setattr(politica, "_infoleg_contar_dnus", contar)
    monkeypatch.setattr(politica, "_resumen_completo_infoleg", lambda s, it: "")
    return pedidos


def test_la_card_saca_los_tratados_del_denominador(monkeypatch, _infoleg_fake):
    class Hoy(date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 29)

    monkeypatch.setattr(politica, "date", Hoy)
    ind = politica.fetch_ratio_dnu()
    # ventana 30-oct-2025 a 29-oct-2026: 3 leyes publicadas, 1 tratado
    assert ind["leyes_publicadas"] == 3
    assert ind["tratados_excluidos"] == 1
    assert ind["leyes_count"] == 2
    assert ind["dnu_count"] == 6
    assert ind["valor"] == 3.0
    assert [t["ley"] for t in ind["inventario_tratados"]] == ["27824"]
    assert ind["unidad"] == politica.UNIDAD_RATIO_DNU
    assert "tratados internacionales" in ind["detalle_txt"]


def test_la_serie_baja_una_vez_y_su_ultimo_punto_es_la_card(monkeypatch, _infoleg_fake):
    class Hoy(date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 29)

    monkeypatch.setattr(descargar_series, "date", Hoy)
    monkeypatch.setattr(politica, "date", Hoy)
    serie = descargar_series.fetch_ratio_dnu_serie()
    assert len(_infoleg_fake["dnus"]) == 1, "los DNU se bajan una sola vez para toda la serie"
    # una consulta de leyes por año calendario del tramo (ene-2023 a hoy)
    assert [d.year for d, _ in _infoleg_fake["leyes"]] == [2023, 2024, 2025, 2026]
    # los meses cuya ventana no tiene leyes se omiten; el resto, uno por mes
    assert serie[0][0] == "2025-06-01" and serie[-1][0] == "2026-10-01"
    assert len(serie) == 17
    card = politica.fetch_ratio_dnu()
    assert serie[-1][1] == card["valor"]


def test_la_ventana_tiene_que_estar_cubierta():
    ins = {"desde": "2026-01-01", "hasta": "2026-06-30", "leyes": [], "dnus": []}
    with pytest.raises(ValueError):
        politica.ratio_dnu_contar(ins, date(2025, 12, 1), date(2026, 6, 30))


# ── Registros que InfoLeg declara y no muestra ──────────────────────────────

class _RespListado:
    status_code = 200

    def __init__(self, texto):
        self.text = texto

    def raise_for_status(self):
        pass


def test_un_registro_invisible_con_todas_las_paginas_se_tolera(monkeypatch, capsys):
    """Septiembre de 2026: declara 8 leyes, lista 7 en su única página."""
    monkeypatch.setattr(politica, "_DERROTAS_PAUSA_INFOLEG", 0)
    monkeypatch.setattr(politica, "_parsear_listado_infoleg",
                        lambda html: [{"infoleg_id": str(i), "norma": f"Ley {i}"} for i in range(7)])

    class _Ses:
        def post(self, *a, **k):
            return _RespListado("Cantidad de Normas Encontradas: 8 en 1 página.")

    items = politica._infoleg_listado_completo(_Ses(), "x", "1", date(2026, 9, 1), date(2026, 9, 30),
                                               invisibles_tolerados=2)
    assert len(items) == 7
    assert "declara 8" in capsys.readouterr().out
    with pytest.raises(ValueError, match="truncado"):
        politica._infoleg_listado_completo(_Ses(), "x", "1", date(2026, 9, 1), date(2026, 9, 30))


def test_si_faltan_paginas_corta_aunque_se_tolere(monkeypatch):
    monkeypatch.setattr(politica, "_DERROTAS_PAUSA_INFOLEG", 0)
    monkeypatch.setattr(politica, "_parsear_listado_infoleg",
                        lambda html: [{"infoleg_id": str(i), "norma": f"Decreto {i}"} for i in range(50)])

    class _Ses:
        def post(self, *a, **k):
            return _RespListado("Cantidad de Normas Encontradas: 51 en 2 páginas.")

    # la página 2 repite las mismas 50 filas: no aportó la que falta
    with pytest.raises(ValueError, match="truncado"):
        politica._infoleg_listado_completo(_Ses(), "x", "2", date(2026, 9, 1), date(2026, 9, 30),
                                           invisibles_tolerados=2)


# ── Un valor guardado con el método anterior no puntúa ni se publica ────────

def test_el_valor_sin_la_marca_de_metodo_no_puntua():
    viejo = {"valor": 1.156, "dnu_count": 37, "leyes_count": 32}
    nuevo = {**viejo, "valor": 2.643, "metodo": politica.METODO_RATIO_DNU}
    assert politica._valor_itcp("ratio_dnu", viejo) is None
    assert politica._valor_itcp("ratio_dnu", nuevo) == 2.643
    assert politica._resultado_utilizable("ratio_dnu", nuevo)


def test_el_arrastre_del_metodo_anterior_queda_sin_dato(capsys):
    """Primera corrida con InfoLeg caído: la caché trae 37/32 contado CON
    tratados. No se arrastra: el indicador queda sin dato (sin tarjeta y fuera
    del índice, que renormaliza), con un aviso en el log."""
    viejo = {"valor": 1.156, "dnu_count": 37, "leyes_count": 32, "fecha_dato": "2026-10-28"}
    assert politica._arrastre("ratio_dnu", viejo) is None
    assert "método anterior" in capsys.readouterr().out
    # con la marca, el arrastre es el de siempre
    b = politica._arrastre("ratio_dnu", {**viejo, "metodo": politica.METODO_RATIO_DNU})
    assert b["valor"] == 1.156 and b["desactualizado"] is True
    # otros indicadores no cambian
    assert politica._arrastre("veto_quorum", {"valor": 3})["valor"] == 3


def test_el_indice_renormaliza_sin_el_valor_viejo(monkeypatch):
    monkeypatch.setattr(politica.itcp, "cargar_ajustes", lambda *a, **k: {})
    base = {"eficacia_legislativa": {"valor": 27.3}, "insistencias_vetos": {"valor": 0}}
    con_viejo = politica.calcular_itcp_cinturon({**base, "ratio_dnu": {"valor": 1.156}})
    sin = politica.calcular_itcp_cinturon(base)
    assert con_viejo["valor"] == sin["valor"]
    con_nuevo = politica.calcular_itcp_cinturon(
        {**base, "ratio_dnu": {"valor": 2.643, "metodo": politica.METODO_RATIO_DNU}})
    assert con_nuevo["valor"] != sin["valor"]


def test_la_card_fresca_lleva_la_marca(monkeypatch, _infoleg_fake):
    class Hoy(date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 29)

    monkeypatch.setattr(politica, "date", Hoy)
    assert politica.fetch_ratio_dnu()["metodo"] == politica.METODO_RATIO_DNU
