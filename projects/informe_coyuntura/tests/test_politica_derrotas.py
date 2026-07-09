"""Tests de derrotas_legislativas (ADR-0046): registro semilla, conteo de la
ventana móvil de 12 meses, derivación de eventos (cada norma cuenta UNA vez,
fechada en la derrota consumada) y parseo del listado de InfoLeg contra un
fixture REAL (respuesta en vivo del buscador a la frase exacta
'"observase en su totalidad"', capturada 2026-07-09 — los 6 decretos de veto
total con sumario en esa variante).
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica

FIXTURE_INFOLEG = (Path(__file__).parent / "fixtures" / "infoleg_listado_vetos.html").read_text(
    encoding="utf-8", errors="replace")


def _eventos_semilla():
    registro = politica._cargar_derrotas_registro()
    assert registro is not None, "registro semilla ausente o ilegible"
    return politica._derrotas_eventos(registro)


# ── Registro semilla → eventos ────────────────────────────────────────────────

def test_semilla_eventos_totales():
    # 3 vetos insistidos + 7 decretos con al menos un rechazo = 10 derrotas
    # históricas dic-2023→jul-2026 (DNU 179/25 fue APROBADO: no es derrota)
    eventos = _eventos_semilla()
    assert sum(1 for e in eventos if e["tipo"] == "veto_insistido") == 3
    assert sum(1 for e in eventos if e["tipo"] == "decreto_rechazado") == 7
    assert sorted(e["fecha"][:7] for e in eventos) == [
        "2024-03", "2024-08", "2025-08", "2025-08", "2025-08", "2025-08",
        "2025-08", "2025-09", "2025-10", "2025-10",
    ]


def test_decreto_cuenta_una_vez_en_el_primer_rechazo():
    # 656/2024: Diputados lo rechazó el 21-ago-2024 y el Senado el 12-sep-2024
    # — es UNA derrota, fechada en el primer rechazo (agosto)
    eventos = [e for e in _eventos_semilla() if "656" in e["nombre"]]
    assert len(eventos) == 1
    assert eventos[0]["fecha"] == "2024-08-21"


def test_veto_insistido_fecha_de_la_segunda_camara():
    # 27.793: Diputados insistió el 20-ago-2025, el Senado consumó el 04-sep —
    # la derrota se fecha cuando la SEGUNDA cámara completa la insistencia
    eventos = [e for e in _eventos_semilla() if "27.793" in e["nombre"]]
    assert len(eventos) == 1
    assert eventos[0]["fecha"] == "2025-09-04"


def test_vetos_sostenidos_no_son_eventos():
    # 27.756/27.757/27.790/27.791/27.792/27.794 y el parcial 27.739 no tienen
    # insistencia completa: no aportan evento
    nombres = {e["nombre"] for e in _eventos_semilla() if e["tipo"] == "veto_insistido"}
    assert nombres == {"ley 27.793", "ley 27.795", "ley 27.796"}


# ── Ventana móvil de 12 meses ────────────────────────────────────────────────

def test_conteo_12m_hoy_jul_2026():
    # ventana ago-2025..jul-2026: 5 decretos (ago-2025) + 3 vetos (sep/oct-2025)
    total, n_vetos, n_decretos, ultimo = politica._derrotas_conteo_12m(
        _eventos_semilla(), date(2026, 7, 9))
    assert (total, n_vetos, n_decretos) == (8, 3, 5)
    assert ultimo == "2025-10-02"


def test_conteo_12m_cortes_historicos():
    eventos = _eventos_semilla()
    casos = {
        date(2024, 2, 29): 0,    # antes del primer rechazo
        date(2024, 3, 31): 1,    # DNU 70/23 (Senado, 14-mar-2024)
        date(2024, 12, 31): 2,   # 70/23 + 656/24
        date(2025, 3, 31): 1,    # 70/23 (mar-2024) sale de la ventana
        date(2025, 7, 31): 1,    # solo 656/24 (ago-2024) sigue adentro
        date(2025, 8, 31): 5,    # entran los 5 decretos de ago-2025; sale 656/24
        date(2025, 9, 30): 6,    # + insistencia 27.793
        date(2025, 10, 31): 8,   # + insistencias 27.795/27.796 — pico real
        date(2026, 6, 30): 8,    # meseta: sin eventos nuevos, ninguno salió
    }
    for referencia, esperado in casos.items():
        total, _, _, _ = politica._derrotas_conteo_12m(eventos, referencia)
        assert total == esperado, f"{referencia}: esperaba {esperado}, dio {total}"


def test_conteo_12m_cliff_de_salida():
    # aritmética de la ventana, no mejora política: en ago-2026 los 5 decretos
    # de ago-2025 cumplen 12 meses y salen (quedan solo los 3 vetos); en
    # nov-2026 ya no queda nada (limitación declarada en la ficha)
    eventos = _eventos_semilla()
    total_ago, n_vetos_ago, n_decretos_ago, _ = politica._derrotas_conteo_12m(
        eventos, date(2026, 8, 31))
    assert (total_ago, n_vetos_ago, n_decretos_ago) == (3, 3, 0)
    total_nov, _, _, ultimo_nov = politica._derrotas_conteo_12m(eventos, date(2026, 11, 30))
    assert total_nov == 0
    assert ultimo_nov is None


def test_serie_mensual_desde_semilla():
    # la serie de descargar_series usa la MISMA ventana/conteo que la card
    import descargar_series
    puntos = descargar_series.fetch_derrotas_legislativas_mensual()
    assert puntos, "serie vacía"
    assert puntos[0] == ["2023-12-31", 0]
    valores = dict((f, v) for f, v in puntos)
    assert valores["2024-03-31"] == 1
    assert valores["2025-08-31"] == 5
    assert valores["2025-10-31"] == 8
    assert valores["2026-06-30"] == 8


# ── Detalle legible de la card ───────────────────────────────────────────────

def test_detalle_txt_plurales_y_cero():
    assert politica._derrotas_detalle_txt(3, 5) == (
        "3 vetos insistidos por el Congreso + 5 decretos rechazados "
        "en el recinto en los últimos 12 meses")
    assert "1 veto insistido" in politica._derrotas_detalle_txt(1, 0)
    assert "1 decreto rechazado" in politica._derrotas_detalle_txt(0, 1)
    assert politica._derrotas_detalle_txt(0, 0).startswith("sin derrotas legislativas")


# ── Parseo del listado InfoLeg (fixture real, respuesta en vivo 2026-07-09) ──

def test_parsear_listado_infoleg_fixture_real():
    items = politica._parsear_listado_infoleg(FIXTURE_INFOLEG)
    assert len(items) == 6   # los 6 decretos con "OBSERVASE EN SU TOTALIDAD"
    por_id = {i["infoleg_id"]: i for i in items}
    assert set(por_id) == {"417425", "417372", "417371", "414326", "404840", "403575"}
    # decreto + fecha de publicación B.O. + proyecto(s) vetado(s) del sumario
    item = por_id["417425"]
    assert politica._RE_DECRETO_ITEM.search(item["norma"]).groups() == ("652", "2025")
    assert item["fecha_pub"] == "2025-09-12"
    assert politica._proyectos_de_sumario(item["sumario"]) == ["27.794"]
    assert politica._proyectos_de_sumario(por_id["404840"]["sumario"]) == ["27.757"]
    assert por_id["403575"]["fecha_pub"] == "2024-09-02"


def test_proyectos_de_sumario_multiproyecto_y_ruido():
    # caso real 534/2025 (un decreto vetó tres leyes) + códigos administrativos
    # que no deben confundirse con números de proyecto
    sumario = ("VETO PROYECTOS DE LEY NROS. 27.791, 27.792 Y 27.793 - OBSERVA EN SU "
               "TOTALIDAD LOS PROYECTOS DE LEY REGISTRADOS BAJO LOS NROS. 27.791, "
               "27.792 Y 27.793 (IF-2025-95643101-APNDSGA#SLYT).")
    assert politica._proyectos_de_sumario(sumario) == ["27.791", "27.792", "27.793"]
    assert politica._proyectos_de_sumario("SUSTITUYESE EL ANEXO I DEL DECRETO 50/2019") == []


def test_parsear_listado_html_sin_resultados():
    html = "<html><body>No se encontraron normas que cumplan las condiciones de búsqueda indicadas</body></html>"
    assert politica._parsear_listado_infoleg(html) == []


def test_fecha_infoleg():
    assert politica._fecha_infoleg("12-sep-2025") == "2025-09-12"
    assert politica._fecha_infoleg("03-oct-2024") == "2024-10-03"
    assert politica._fecha_infoleg("sin fecha") is None


# ── Clasificación de títulos de actas del Senado ─────────────────────────────

def test_clave_decreto_de_titulo_casos_reales():
    # títulos reales del listado del Senado (verificados en vivo 2026-07-09)
    assert politica._clave_decreto_de_titulo(
        "Rechazo del Decreto del Poder Ejecutivo Nº 70/23, en los términos de la ley 26.122.") == "70/2023"
    assert politica._clave_decreto_de_titulo(
        "Rechazo del decreto de facultades delegadas Nº 351/25 del Poder Ejecutivo Nacional, "
        "en los términos de la ley 26.122.") == "351/2025"
    assert politica._clave_decreto_de_titulo(
        "Decreto de Necesidad de Urgencia Nº 340/25 del Poder Ejecutivo Nacional, "
        "en los términos de la ley 26.122.") == "340/2025"
    # decreto de la gestión anterior (se filtra después por año < 2023)
    assert politica._clave_decreto_de_titulo(
        "Aprobación del Decreto del Poder Ejecutivo Nacional N° 829/19, "
        "en los términos de la ley 26.122.") == "829/2019"
    # sin número con prefijo Nº/N° -> None (el expediente PE-44/25-DC no debe
    # confundirse con el número del decreto)
    assert politica._clave_decreto_de_titulo(
        "Rechazo de un decreto, en los términos de la ley 26.122. PE-44/25-DC") is None


def test_tipo_decreto_de_titulo():
    assert politica._tipo_decreto_de_titulo("Rechazo del decreto de facultades delegadas Nº 351/25") == "delegado"
    assert politica._tipo_decreto_de_titulo("Decreto de Necesidad de Urgencia Nº 340/25") == "DNU"
    assert politica._tipo_decreto_de_titulo("Rechazo del Decreto del Poder Ejecutivo Nº 70/23") == "decreto"


# ── Detección incremental (sin red: mutación del registro en memoria) ────────

def test_detectar_insistencias_ignora_ley_publicada_el_mismo_dia(monkeypatch):
    # 27.739 (veto parcial): la ley existe en InfoLeg publicada el MISMO día
    # que el decreto de promulgación parcial -> NO es una insistencia
    registro = {"vetos": [{"proyecto": "27.739", "fecha_veto": "2024-03-15",
                           "insistencia_completa": None, "fuente_insistencia": None}],
                "decretos": []}
    monkeypatch.setattr(politica, "_infoleg_buscar", lambda *a, **k: "<html>Encontradas: 1</html>")
    monkeypatch.setattr(politica, "_parsear_listado_infoleg",
                        lambda html: [{"infoleg_id": "1", "norma": "Ley 27739 / 2024",
                                       "fecha_pub": "2024-03-15", "sumario": "CODIGO PENAL"}])
    politica._derrotas_detectar_insistencias(None, None, registro)
    assert registro["vetos"][0]["insistencia_completa"] is None


def test_detectar_insistencias_flip_con_fecha_posterior(monkeypatch):
    registro = {"vetos": [{"proyecto": "27.790", "fecha_veto": "2025-06-24",
                           "insistencia_completa": None, "fuente_insistencia": None}],
                "decretos": []}
    monkeypatch.setattr(politica, "_infoleg_buscar", lambda *a, **k: "<html>Encontradas: 1</html>")
    monkeypatch.setattr(politica, "_parsear_listado_infoleg",
                        lambda html: [{"infoleg_id": "9", "norma": "Ley 27790 / 2025",
                                       "fecha_pub": "2026-08-05", "sumario": "EMERGENCIA BAHIA BLANCA"}])
    politica._derrotas_detectar_insistencias(None, None, registro)
    assert registro["vetos"][0]["insistencia_completa"] == "2026-08-05"


def test_detectar_vetos_agrega_solo_proyectos_nuevos(monkeypatch):
    registro = {"vetos": [{"proyecto": "27.794", "fecha_veto": "2025-09-12",
                           "insistencia_completa": None}], "decretos": []}
    monkeypatch.setattr(politica, "_infoleg_buscar",
                        lambda *a, **k: FIXTURE_INFOLEG)
    politica._derrotas_detectar_vetos(None, None, registro)
    proyectos = sorted(v["proyecto"] for v in registro["vetos"])
    # el fixture trae 27.756/27.757/27.790/27.794/27.795/27.796; 27.794 ya
    # estaba y no se duplica (las 3 frases devuelven el mismo fixture acá,
    # la deduplicación por proyecto absorbe la repetición)
    assert proyectos == ["27.756", "27.757", "27.790", "27.794", "27.795", "27.796"]
    nuevo = next(v for v in registro["vetos"] if v["proyecto"] == "27.790")
    assert nuevo["fecha_veto"] == "2025-06-24"
    assert nuevo["insistencia_completa"] is None
    assert nuevo["tipo"] == "total"
