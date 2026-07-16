"""Tests de bloqueo_sostenido (ADR-0069): derivación de desafíos desde el
registro semilla, tasa de la ventana móvil de 12 meses evaluada al cierre de
cada mes histórico, clasificación de actas de Diputados (formatos reales
verificados en vivo 2026-07-16: insistencias 2024 por expediente del mensaje,
insistencias 2025+ por número de ley, habilitaciones excluidas, decretos con
dirección de moción estándar) y regla de 2/3 del Senado.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import politica


def _desafios_semilla():
    registro = politica._cargar_derrotas_registro()
    assert registro is not None, "registro semilla ausente o ilegible"
    return politica._bloqueo_desafios(registro)


# ── Registro → desafíos ──────────────────────────────────────────────────────

def test_semilla_desafios_totales():
    # 16 normas desafiadas dic-2023→jul-2026: 8 decretos con votación en el
    # recinto (7 rechazados alguna vez + el 179/25 aprobado) y 8 vetos con
    # insistencia votada (27.739 sin insistencia y 27.792 nunca tratada NO
    # entran: sin desafío votado no hay prueba del bloqueo)
    desafios = _desafios_semilla()
    assert len(desafios) == 16
    nombres = {e["nombre"] for e in desafios}
    assert "ley 27.739" not in nombres
    assert "ley 27.792" not in nombres
    assert "DNU 179/2025" in nombres


def test_decreto_cae_con_la_segunda_camara():
    # 656/2024: Diputados 21-ago + Senado 12-sep — la caída es la SEGUNDA
    # cámara (a diferencia de derrotas, que fecha el PRIMER rechazo)
    e = next(x for x in _desafios_semilla() if "656" in x["nombre"])
    assert e["fecha_desafio"] == "2024-08-21"
    assert e["fecha_caida"] == "2024-09-12"


def test_rechazo_de_una_sola_camara_no_es_caida():
    # DNU 70/2023: rechazado solo por el Senado — desafiado pero EN PIE
    e = next(x for x in _desafios_semilla() if "70/2023" in x["nombre"])
    assert e["fecha_desafio"] == "2024-03-14"
    assert e["fecha_caida"] is None


def test_veto_sostenido_es_desafio_sin_caida():
    # 27.756 (jubilaciones 2024): insistencia rechazada 11-sep-2024 → en pie
    e = next(x for x in _desafios_semilla() if x["nombre"] == "ley 27.756")
    assert e["fecha_desafio"] == "2024-09-11"
    assert e["fecha_caida"] is None


def test_veto_insistido_cae_con_la_insistencia_completa():
    # 27.793: Diputados insistió 20-ago-2025, el Senado consumó 04-sep
    e = next(x for x in _desafios_semilla() if x["nombre"] == "ley 27.793")
    assert e["fecha_desafio"] == "2025-08-20"
    assert e["fecha_caida"] == "2025-09-04"


# ── Tasa 12m evaluada al cierre de cada mes ──────────────────────────────────

def test_tasa_12m_cortes_historicos():
    desafios = _desafios_semilla()
    casos = {
        date(2024, 2, 29): None,          # sin desafíos: sin denominador
        date(2024, 3, 31): 100.0,         # DNU 70 desafiado y en pie
        date(2024, 8, 31): 100.0,         # 656 desafiado, todavía en pie al cierre
        date(2024, 9, 30): 66.7,          # cae 656; 27.756 sostenido (2/3)
        date(2024, 12, 31): 75.0,         # + 27.757 sostenido (3 de 4)
        date(2025, 8, 31): 54.5,          # ola ago-2025: caen los 5 decretos (6/11)
        date(2025, 9, 30): 53.8,          # + cae 27.793; 27.795/27.796 aún en pie (7/13)
        date(2025, 10, 31): 33.3,         # caen 27.795/27.796 (4/12)
        date(2026, 3, 31): 27.3,          # sale el 179/25 de la ventana (3/11)
        date(2026, 7, 16): 20.0,          # hoy: 2 de 10 (también salió 27.790)
    }
    for referencia, esperado in casos.items():
        tasa = politica._bloqueo_tasa_12m(desafios, referencia)
        valor = tasa[0] if tasa else None
        assert valor == esperado, f"{referencia}: esperaba {esperado}, dio {valor}"


def test_tasa_reproducible_al_corte():
    # el estado se evalúa AL CIERRE del mes: al 31-ago-2025 la 27.793 sigue en
    # pie (su caída es del 04-sep) — un punto publicado no cambia después
    desafios = _desafios_semilla()
    _, n_ago, caidas_ago, _ = politica._bloqueo_tasa_12m(desafios, date(2025, 8, 31))
    assert (n_ago, caidas_ago) == (11, 5)
    _, n_sep, caidas_sep, _ = politica._bloqueo_tasa_12m(desafios, date(2025, 9, 30))
    assert (n_sep, caidas_sep) == (13, 6)


def test_serie_mensual_desde_semilla():
    # la serie de descargar_series usa la MISMA ventana/regla que la card, y
    # arranca en mar-2024 (primer desafío votado) — antes no hay denominador
    import descargar_series
    puntos = descargar_series.fetch_bloqueo_sostenido_mensual()
    assert puntos, "serie vacía"
    assert puntos[0][0] == "2024-03-31"
    valores = dict((f, v) for f, v in puntos)
    assert valores["2024-09-30"] == 66.7
    assert valores["2025-10-31"] == 33.3
    assert "2024-02-29" not in valores


# ── Encabezado de actas de Diputados ─────────────────────────────────────────

def test_dedup_tokens_dobles():
    assert politica._dedup_tokens_dobles("NNEEGGAATTIIVVOO") == "NEGATIVO"
    assert politica._dedup_tokens_dobles("MMááss ddee llaa mmiittaadd") == "Más de la mitad"
    assert politica._dedup_tokens_dobles("DDooss tteerrcciiooss") == "Dos tercios"
    # una palabra legítima no entera-en-pares no se toca
    assert politica._dedup_tokens_dobles("Carroza") == "Carroza"


def test_regex_decreto_motivo_casos_reales():
    # motivos reales de actas 5718/5715/5719/5608 (verificados en vivo)
    casos = {
        "EXPTE. 0039-PE-2025. DECRETO DE NECESIDAD Y URGENCIA N° 340/25.": ("340", "25"),
        "EXPTE. 0095-PE-2025. DECRETO DE FACULTADES DELEGADAS N°462/25.": ("462", "25"),
        "EXPTE. 0094-PE-2025. DECRETO N° 461/25.": ("461", "25"),
        "O. D. 759 - DNU 179/2025, QUE APRUEBA LAS OPERACIONES DE CRÉDITO": ("179", "2025"),
    }
    for motivo, esperado in casos.items():
        m = politica._RE_DECRETO_MOTIVO.search(motivo)
        assert m and m.groups() == esperado, motivo
    # el expediente PE no debe confundirse con un número de decreto
    assert politica._RE_DECRETO_MOTIVO.search("EXPTE. 15-PE-2024") is None


def test_regex_expte_pe_motivo():
    assert politica._RE_EXPTE_PE_MOTIVO.search("EXPTE. 15-PE-2024").groups() == ("15", "2024")
    assert politica._RE_EXPTE_PE_MOTIVO.search("EXPTE. 0039-PE-2025. DECRETO").groups() == ("39", "2025")
    assert politica._RE_EXPTE_PE_MOTIVO.search("EXPTE. 0015-S-2024") is None


# ── Clasificación de actas (sin red) ─────────────────────────────────────────

def _clasificar(monkeypatch, registro, encabezado):
    monkeypatch.setattr(politica, "_diputados_acta_pdf", lambda s, i: b"pdf")
    monkeypatch.setattr(politica, "_parsear_encabezado_acta_diputados", lambda c: encabezado)
    return politica._bloqueo_clasificar_acta_diputados(None, registro, 9999)


def test_clasificar_habilitacion_se_excluye(monkeypatch):
    # caso real 20-ago-2025: la habilitación de la 27.791 salió AFIRMATIVA
    # (159-75) y la insistencia real NEGATIVA (160-83) — la habilitación no
    # debe registrarse como insistencia
    registro = {"vetos": [{"proyecto": "27.791"}], "decretos": []}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-08-20", "motivo": "HABILITACIÓN DEL TRATAMIENTO EXPTE. 4-PE-2025.",
        "mayoria": "Dos tercios", "resultado": "AFIRMATIVO", "votos_txt": "159-75-4"})
    assert resuelta and nota is None
    assert "insistencias_votadas" not in registro["vetos"][0]


def test_clasificar_insistencia_formato_2025(monkeypatch):
    # acta 5737: la insistencia real, NEGATIVO (160-83, 65,8% < 2/3)
    registro = {"vetos": [{"proyecto": "27.791"}], "decretos": []}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-08-20", "motivo": "INSISTENCIA PROYECTO DE LEY 27.791.",
        "mayoria": "Dos tercios", "resultado": "NEGATIVO",
        "votos_txt": "160 afirmativos - 83 negativos - 6 abst."})
    assert resuelta and "veto sostenido" in nota
    iv = registro["vetos"][0]["insistencias_votadas"][0]
    assert iv["resultado"] == "insistencia_rechazada"
    assert iv["fecha"] == "2025-08-20"


def test_clasificar_insistencia_formato_2024_via_mensaje(monkeypatch):
    # acta 5354: motivo "EXPTE. 15-PE-2024" + 2/3 → CKAN mapea el mensaje a
    # la ley 27.756
    registro = {"vetos": [{"proyecto": "27.756"}], "decretos": []}
    monkeypatch.setattr(politica, "_mensaje_pe_a_leyes", lambda n, a: ["27.756"])
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2024-09-11", "motivo": "EXPTE. 15-PE-2024",
        "mayoria": "Dos tercios", "resultado": "NEGATIVO",
        "votos_txt": "153 afirmativos - 87 negativos - 8 abst."})
    assert resuelta and "27.756" in nota
    assert registro["vetos"][0]["insistencias_votadas"][0]["resultado"] == "insistencia_rechazada"


def test_clasificar_expte_pelado_2025_es_pendiente(monkeypatch):
    # desde 2025 el formato "expediente a secas" es el de las habilitaciones:
    # si aparece sin palabra clave es un formato inesperado → nunca se adivina
    registro = {"vetos": [], "decretos": []}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-08-20", "motivo": "EXPTE. 4-PE-2025",
        "mayoria": "Dos tercios", "resultado": "AFIRMATIVO", "votos_txt": "x"})
    assert not resuelta and "formato inesperado" in nota


def test_clasificar_decreto_rechazo_estandar(monkeypatch):
    registro = {"vetos": [], "decretos": [
        {"clave": "340/2025", "rechazos": [], "estado": "vigente"}]}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-08-07", "motivo": "EXPTE. 0039-PE-2025. DECRETO DE NECESIDAD Y URGENCIA N° 340/25.",
        "mayoria": "Más de la mitad", "resultado": "AFIRMATIVO",
        "votos_txt": "118 afirmativos - 77 negativos - 8 abst."})
    assert resuelta and "RECHAZO" in nota
    assert registro["decretos"][0]["rechazos"][0]["camara"] == "Diputados"


def test_clasificar_decreto_aprobacion_es_pendiente(monkeypatch):
    # dictamen de aprobación (caso real DNU 179/2025 FMI): dirección ambigua
    registro = {"vetos": [], "decretos": [
        {"clave": "179/2025", "rechazos": [], "estado": "vigente"}]}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-03-19", "motivo": "O. D. 759 - DNU 179/2025, QUE APRUEBA LAS OPERACIONES",
        "mayoria": "Más de la mitad", "resultado": "AFIRMATIVO", "votos_txt": "x"})
    assert not resuelta and "aprobación" in nota


def test_clasificar_decreto_desconocido_es_pendiente(monkeypatch):
    # un número que el registro no conoce puede ser un decreto simple fuera
    # de la 26.122 (caso real 681/25) — no se adivina
    registro = {"vetos": [], "decretos": []}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-10-02", "motivo": "RECHAZO AL DECRETO N° 681/25.",
        "mayoria": "Más de la mitad", "resultado": "AFIRMATIVO", "votos_txt": "x"})
    assert not resuelta and "681/2025" in nota


def test_clasificar_dedup_misma_camara_y_fecha(monkeypatch):
    registro = {"vetos": [], "decretos": [
        {"clave": "340/2025", "estado": "derogado",
         "rechazos": [{"fecha": "2025-08-07", "camara": "Diputados", "acta": "5718"}]}]}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2025-08-07", "motivo": "EXPTE. 0039-PE-2025. DECRETO DE NECESIDAD Y URGENCIA N° 340/25.",
        "mayoria": "Más de la mitad", "resultado": "AFIRMATIVO", "votos_txt": "x"})
    assert resuelta and "ya reflejada" in nota
    assert len(registro["decretos"][0]["rechazos"]) == 1


def test_clasificar_anterior_a_la_gestion(monkeypatch):
    registro = {"vetos": [], "decretos": []}
    resuelta, nota = _clasificar(monkeypatch, registro, {
        "fecha": "2023-11-15", "motivo": "INSISTENCIA PROYECTO DE LEY 27.700.",
        "mayoria": "Dos tercios", "resultado": "AFIRMATIVO", "votos_txt": "x"})
    assert resuelta and nota is None
