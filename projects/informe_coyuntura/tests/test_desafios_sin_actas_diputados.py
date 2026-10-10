"""desafios_legislativos cuando las actas de Diputados no se pueden leer.

Desde el 31-jul-2026 el recorrido de actas de Diputados (votaciones.hcdn.gob.ar)
fallaba desde CI sin escribir nada en el log, y la compuerta de `main` dejaba
el indicador sin calcular. Estos tests fijan: (1) el fallo deja URL y código en
el log; (2) sin actas el indicador igual se calcula, con el tramo provisorio
marcado; (3) con actas disponibles el resultado es el de siempre.

Los temarios de los tests son texto real de www.hcdn.gob.ar (sesiones del
21-ago-2024, 20-ago-2025, 17-sep-2025 y 15-oct-2026, bajados el 10-oct-2026).
"""
import copy
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import politica

FIXTURES = Path(__file__).parent / "fixtures"

TEMARIO_20_AGO_2025 = """TEMARIO
6-PE-2025 COMUNICACION DEL DICTADO DEL DECRETO N° 534 DEL 1 DE
AGOSTO DE 2025, POR EL CUAL SE OBSERVA TOTALMENTE Y
SE DEVUELVE EL PROYECTO DE LEY POR EL CUAL SE
DECLARA LA EMERGENCIA EN DISCAPACIDAD EN TODO EL
TERRITORIO NACIONAL HASTA EL 31 DE DICIEMBRE DE 2027,
REGISTRADO CON EL N° 27793. (DISCAPACIDAD/ ACCIÓN
SOCIAL Y SALUD PÚBLICA/ PRESUPUESTO Y HACIENDA)
21-S-2025 PROYECTO DE LEY POR EL CUAL SE MODIFICA LA LEY 11672,
PERMANENTE DE PRESUPUESTO.
22-S-2025 INSISTIR EN LA SANCIÓN ORIGINAL DEL PROYECTO DE LEY
REGISTRADO BAJO EL NÚMERO 27.790 QUE DECLARA LA EMERGENCIA."""

TEMARIO_21_AGO_2024 = """TEMARIO
76-PE-2024 DNU 656/2024 ASIGNACIÓN ADICIONAL AL PRESUPUESTO
GENERAL DE LA ADMINISTRACIÓN NACIONAL.
BICAMERAL PERMANENTE DE TRAMITE LEGISLATIVO - LEY 26122
3918-D-2024 DE RESOLUCIÓN. DECLARAR NULO DE NULIDAD ABSOLUTA E
INSANABLE EL DECRETO DE NECESIDAD Y URGENCIA Nº
111/2024 POR FALTA DE ADECUACIÓN.
ASUNTOS CONSTITUCIONALES Y PRESUPUESTO Y HACIENDA
3903-D-2024 DE RESOLUCIÓN. EXPRESAR RECHAZO AL DECRETO DE
NECESIDAD Y URGENCIA N° 222/2024 QUE DISPONE UNA
ASIGNACIÓN ADICIONAL."""

TEMARIO_DNU_NUEVO = """TEMARIO
PE 31/26 MENSAJE 0009/26. COMUNICACIÓN DEL DICTADO DEL DECRETO
DE NECESIDAD Y URGENCIA 999/26, SOBRE ALGO.
(BICAMERAL PERMANENTE DE TRÁMITE LEGISLATIVO)
4018-D-2026 DE LEY. LEY 27.793, DE EMERGENCIA NACIONAL EN
DISCAPACIDAD. PRÓRROGA HASTA EL 31 DE DICIEMBRE DE 2027."""


HTML_SESION_REALIZADA = (
    '<iframe src="https://www3.hcdn.gob.ar/visor/pdf/v2.5/web/viewer.html?file='
    'https://www3.hcdn.gob.ar/dependencias/dtaquigrafos/diarios/periodo-144/diario_x.pdf">')
HTML_SESION_SIN_DIARIO = '<html>Usar http para poder ver la versión taquigráfica</html>'
DIARIO_COMPLETO = ("Se vota el decreto 999/26 y 656/2024. Ley 27.792 y 27.790. "
                   "DNU 111/2026 DNU 222/2026 DNU 333/2026")


# ── 1. El fallo de las actas deja rastro en el log ───────────────────────────

class _Resp:
    def __init__(self, code):
        self.status_code = code
        self.content = b""


class _Sesion:
    def __init__(self, resultado):
        self.resultado = resultado

    def get(self, url, **kw):
        if isinstance(self.resultado, Exception):
            raise self.resultado
        return _Resp(self.resultado)


@pytest.fixture(autouse=False)
def sin_espera(monkeypatch):
    monkeypatch.setattr(politica.time, "sleep", lambda s: None)
    monkeypatch.setattr(politica, "_FALLOS_ACTAS_DIPUTADOS", {"total": 0})


def test_acta_403_deja_url_y_codigo_en_el_log(monkeypatch, capsys, sin_espera):
    r = politica._diputados_acta_pdf(_Sesion(403), 6001)
    assert r is politica._ACTA_FALLO
    out = capsys.readouterr().out
    linea = next(l for l in out.splitlines() if "desafios_legislativos" in l)
    assert linea.startswith("[WARN] politica.desafios_legislativos:")
    assert "https://votaciones.hcdn.gob.ar/pdf/acta/6001" in linea
    assert "HTTP 403" in linea


def test_acta_con_excepcion_de_red_deja_la_excepcion(capsys, sin_espera):
    import requests
    politica._diputados_acta_pdf(_Sesion(requests.ConnectionError("reset by peer")), 6002)
    out = capsys.readouterr().out
    assert "ConnectionError" in out and "reset by peer" in out
    assert "/pdf/acta/6002" in out


def test_control_positivo_acta_ok_y_404_no_avisan(capsys, sin_espera):
    # el aviso discrimina: un 200 y un 404 genuino (hueco de id) no escriben nada
    assert politica._diputados_acta_pdf(_Sesion(404), 6003) is politica._ACTA_NO_EXISTE
    assert isinstance(politica._diputados_acta_pdf(_Sesion(200), 6004), bytes)
    assert "[WARN]" not in capsys.readouterr().out


def test_muchos_fallos_detallan_los_primeros_y_resumen_el_total(capsys, sin_espera):
    for i in range(10):
        politica._diputados_acta_pdf(_Sesion(403), 7000 + i)
    politica._resumen_fallos_actas_diputados()
    out = capsys.readouterr().out
    assert out.count("inaccesible") == politica._MAX_AVISOS_ACTA
    assert "10 descarga(s)" in out


# ── 2. Detección en el temario ───────────────────────────────────────────────

def test_temario_real_15_oct_2026_trae_el_dnu_70_2023():
    html = (FIXTURES / "sesion_hcdn_2026-10-15.html").read_text(encoding="utf-8")
    texto = politica._temario_pdf_desde_sesion_html(html)
    assert "TEMARIO" in texto
    normas = politica._normas_desafiadas_en_temario(texto)
    assert normas == [{"tipo": "decreto", "clave": "70/2023"}]   # no la ley 27.793 de discapacidad


def test_temario_vetos_20_ago_2025():
    normas = politica._normas_desafiadas_en_temario(TEMARIO_20_AGO_2025)
    assert {"tipo": "veto", "ley": "27.793"} in normas
    assert {"tipo": "veto", "ley": "27.790"} in normas
    assert len(normas) == 2      # el presupuesto (21-S-2025) no es un veto


def test_temario_dnu_cuenta_solo_la_via_bicameral():
    # 21-ago-2024: los dos proyectos de resolución que citan el DNU 656/2024 no
    # son su votación; el ítem de la bicameral sí. Una sola norma, no tres.
    assert politica._normas_desafiadas_en_temario(TEMARIO_21_AGO_2024) == [
        {"tipo": "decreto", "clave": "656/2024"}]


def test_temario_sin_veto_ni_dnu_no_devuelve_nada():
    # control negativo: el detector no marca cualquier ley con número
    assert politica._normas_desafiadas_en_temario(
        "TEMARIO\n4018-D-2026 DE LEY. LEY 27.793, DE EMERGENCIA EN DISCAPACIDAD.") == []


# ── 3. El indicador se calcula sin las actas ─────────────────────────────────

@pytest.fixture
def registro_semilla():
    return politica._cargar_derrotas_registro()


@pytest.fixture
def entorno(monkeypatch, registro_semilla):
    guardados = []
    monkeypatch.setattr(politica, "_cargar_derrotas_registro",
                        lambda: copy.deepcopy(registro_semilla))
    monkeypatch.setattr(politica, "_guardar_derrotas_registro",
                        lambda r: guardados.append(copy.deepcopy(r)))
    monkeypatch.setattr(politica, "_bloqueo_detectar_insistencias_senado", lambda r: None)
    monkeypatch.setattr(politica, "_corte_actas_diputados", lambda r: "2026-06-24")
    monkeypatch.setattr(politica, "_sesiones_diputados_registros", lambda: [
        {"id": "0", "fecha": "2026-06-24", "en_minoria": False, "titulo": "ancla",
         "url": "https://www.hcdn.gob.ar/sesiones/sesion.html?id=0"},
        {"id": "1", "fecha": "2026-09-09", "en_minoria": False, "titulo": "t",
         "url": "https://www.hcdn.gob.ar/sesiones/sesion.html?id=1"}])
    monkeypatch.setattr(politica, "_texto_diario_taquigrafico", lambda url: DIARIO_COMPLETO)

    class R:
        text = HTML_SESION_REALIZADA
        def raise_for_status(self): pass
    monkeypatch.setattr(politica.requests, "get", lambda *a, **k: R())
    return guardados


def _hoy(monkeypatch, d):
    class D(date):
        @classmethod
        def today(cls):
            return d
    monkeypatch.setattr(politica, "date", D)


def test_sin_actas_el_indicador_igual_se_calcula_y_cuenta_el_dnu_nuevo(
        monkeypatch, entorno, registro_semilla, capsys):
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r is not None
    assert r["valor"] == base["valor"] + 1
    assert r["caidas_12m"] == base["caidas_12m"]          # sin acta no se inventa una caída
    assert r["provisorio"] is True and r["provisorio_n"] == 1
    assert r["provisorio_n"] == r["valor"] - base["valor"]       # normas únicas, como valor
    assert "temario" in r["fuente"] and "taquigr" in r["fuente"]
    assert "999/2026" in r["detalle_txt"] and "Provisorio" in r["detalle_txt"]
    assert "desafío PROVISORIO" in capsys.readouterr().out
    # el registro en disco no recibe el dato provisorio
    assert len(entorno) >= 1      # hubo al menos un guardado: la aserción no es vacua
    for guardado in entorno:
        assert "provisorio_sin_acta" not in str(guardado)


def test_sin_actas_y_sin_temas_del_ejecutivo_iguala_al_camino_normal(
        monkeypatch, entorno):
    # control: el tramo sin actas no agrega nada por inercia
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html",
                        lambda h: "TEMARIO\n1-D-2026 DE LEY. OTRA COSA.")
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r["valor"] == base["valor"] and r["provisorio_n"] == 0


def test_sin_actas_veto_sin_insistencia_previa_cuenta_como_desafio(monkeypatch, entorno):
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()
    # 27.792: vetada, nunca tratada en el recinto (no figura en la semilla de desafíos)
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: (
        "TEMARIO\n7-PE-2026 COMUNICACION DEL DICTADO DEL DECRETO N° 1 POR EL CUAL SE OBSERVA "
        "TOTALMENTE Y SE DEVUELVE EL PROYECTO DE LEY REGISTRADO CON EL N° 27792."))
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r["valor"] == base["valor"] + 1 and r["caidas_12m"] == base["caidas_12m"]


def test_indice_de_sesiones_caido_no_acredita_nada(monkeypatch, entorno, capsys):
    def cae():
        raise ConnectionError("hcdn.gob.ar no responde")
    monkeypatch.setattr(politica, "_sesiones_diputados_registros", cae)
    assert politica.fetch_desafios_legislativos_sin_actas() is None
    assert "tramo sin actas no acreditado" in capsys.readouterr().out


def test_sesion_sin_temario_no_acredita_el_tramo(monkeypatch, entorno):
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: None)
    assert politica.fetch_desafios_legislativos_sin_actas() is None


def test_ya_reflejado_en_el_registro_no_se_cuenta_dos_veces(monkeypatch, entorno, registro_semilla):
    # cuando el acta vuelve a ser legible el clasificador registra la votación
    # real; el provisorio de esa misma sesión tiene que desaparecer
    _hoy(monkeypatch, date(2026, 10, 10))
    reg = copy.deepcopy(registro_semilla)
    reg["decretos"].append({"clave": "999/2026", "etiqueta": "DNU 999/2026", "tipo": "DNU",
                            "rechazos": [{"fecha": "2026-09-09", "camara": "Diputados"}]})
    monkeypatch.setattr(politica, "_cargar_derrotas_registro", lambda: copy.deepcopy(reg))
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    assert politica.fetch_desafios_legislativos_sin_actas()["provisorio_n"] == 0


# ── 4. La compuerta: con actas, nada cambia ──────────────────────────────────

def test_con_actas_disponibles_el_resultado_es_el_de_siempre(monkeypatch, entorno):
    _hoy(monkeypatch, date(2026, 10, 10))
    llamado = []
    monkeypatch.setattr(politica, "fetch_desafios_legislativos_sin_actas",
                        lambda: llamado.append(1))
    r = politica.resolver_desafios_legislativos({"valor": 80.0}, True)
    esperado = politica.fetch_desafios_legislativos()
    assert r == esperado and not llamado
    assert "provisorio" not in r


def test_compuerta_sin_bloqueo_usa_el_camino_sin_actas_solo_con_registro_al_dia(monkeypatch):
    monkeypatch.setattr(politica, "fetch_desafios_legislativos_sin_actas", lambda: {"v": 1})
    assert politica.resolver_desafios_legislativos(None, True) == {"v": 1}
    assert politica.resolver_desafios_legislativos(None, False) is None


# ── 5. Hallazgos de Codex sobre el #67 ───────────────────────────────────────

def test_item_del_temario_en_sesion_sin_version_taquigrafica_no_cuenta(monkeypatch, entorno):
    # P1: el temario existe antes de la sesión; sin diario no hay prueba de que se votó
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()

    class R:
        text = HTML_SESION_SIN_DIARIO
        def raise_for_status(self): pass
    monkeypatch.setattr(politica.requests, "get", lambda *a, **k: R())
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r["valor"] == base["valor"] and r["provisorio_n"] == 0
    assert "sin versión taquigráfica" in r["detalle_txt"]     # no afirma "no hubo nada"
    assert "ninguna sesión" not in r["detalle_txt"]


def test_item_agendado_pero_no_tratado_en_el_diario_no_cuenta(monkeypatch, entorno):
    # P1: el caso ley 27.790 (20-ago-2025): figura en el temario, la cámara nunca la trató
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    monkeypatch.setattr(politica, "_texto_diario_taquigrafico",
                        lambda url: "se trató otra cosa, el decreto 70/2023 y la ley 27.793")
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r["valor"] == base["valor"] and r["provisorio_n"] == 0
    # control positivo: con el decreto en el diario, el mismo temario sí cuenta
    monkeypatch.setattr(politica, "_texto_diario_taquigrafico",
                        lambda url: "se trató el decreto 999/26")
    assert politica.fetch_desafios_legislativos_sin_actas()["provisorio_n"] == 1


def test_diario_ilegible_no_acredita_el_tramo(monkeypatch, entorno):
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)

    def cae(url):
        raise ConnectionError("diario caído")
    monkeypatch.setattr(politica, "_texto_diario_taquigrafico", cae)
    assert politica.fetch_desafios_legislativos_sin_actas() is None


def test_indice_parcial_sin_la_sesion_del_corte_devuelve_none(monkeypatch, entorno, capsys):
    # P1: un índice truncado que no llega al corte no prueba que el tramo esté vacío
    monkeypatch.setattr(politica, "_sesiones_diputados_registros", lambda: [
        {"id": "9", "fecha": "2026-01-15", "en_minoria": False, "titulo": "vieja",
         "url": "https://www.hcdn.gob.ar/sesiones/sesion.html?id=9"}])
    assert politica.fetch_desafios_legislativos_sin_actas() is None
    assert "tramo sin actas no acreditado" in capsys.readouterr().out


def test_indice_con_la_sesion_del_corte_si_acredita(monkeypatch, entorno):
    # control positivo del anterior: el índice del fixture trae la sesión del corte
    _hoy(monkeypatch, date(2026, 10, 10))
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html",
                        lambda h: "TEMARIO\n1-D-2026 DE LEY. OTRA COSA.")
    assert politica.fetch_desafios_legislativos_sin_actas() is not None


def test_misma_norma_en_dos_temarios_cuenta_una_vez(monkeypatch, entorno):
    # P2: provisorio_n cuenta normas únicas, como `valor`
    _hoy(monkeypatch, date(2026, 10, 10))
    base = politica.fetch_desafios_legislativos()
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    r = politica.fetch_desafios_legislativos_sin_actas()   # sesiones del 24-jun y 9-sep
    assert r["provisorio_n"] == 1 and r["valor"] == base["valor"] + 1
    assert len(r["provisorio_normas"]) == 1


def test_norma_ya_desafiada_antes_no_es_provisoria(monkeypatch, entorno, registro_semilla):
    _hoy(monkeypatch, date(2026, 10, 10))
    reg = copy.deepcopy(registro_semilla)
    reg["decretos"].append({"clave": "999/2026", "etiqueta": "DNU 999/2026", "tipo": "DNU",
                            "rechazos": [{"fecha": "2026-07-01", "camara": "Senado"}]})
    monkeypatch.setattr(politica, "_cargar_derrotas_registro", lambda: copy.deepcopy(reg))
    monkeypatch.setattr(politica, "_temario_pdf_desde_sesion_html", lambda h: TEMARIO_DNU_NUEVO)
    r = politica.fetch_desafios_legislativos_sin_actas()
    assert r["provisorio_n"] == 0 and r["provisorio_normas"] == []
