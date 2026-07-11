"""Tests de Componente B (ADR-0035): datos duros de migración real que
cruzan contra el Componente A (Trends). Todos mockean red -- no hacen
descargas reales en CI."""
import io
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series
import espiritu_epoca


# ── Helpers de fecha ─────────────────────────────────────────────────────────

def test_fiscal_year_eeuu_oct_nov_dic_pasan_al_fy_siguiente():
    assert descargar_series._fiscal_year_eeuu(2024, 10) == 2025
    assert descargar_series._fiscal_year_eeuu(2024, 11) == 2025
    assert descargar_series._fiscal_year_eeuu(2024, 12) == 2025
    assert descargar_series._fiscal_year_eeuu(2025, 1) == 2025
    assert descargar_series._fiscal_year_eeuu(2025, 9) == 2025


def test_meses_desde_excluye_el_mes_en_curso(monkeypatch):
    class _FakeDatetime(datetime):
        @classmethod
        def today(cls):
            return datetime(2024, 3, 15)
    monkeypatch.setattr(descargar_series, "datetime", _FakeDatetime)
    meses = descargar_series._meses_desde(2023, 12)
    assert meses == [(2023, 12), (2024, 1), (2024, 2)]


# ── EEUU NIV/IV: fallback de doble espacio (typo real del sitio, jul-2026) ──

def _xlsx_visas_bytes(filas):
    # Mismo layout que los archivos reales: fila 1 = título, fila 2 = header,
    # fila 3+ = datos (_fetch_visa_mes_argentina arranca en min_row=3).
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nonimmigrant Visa Issuances by Nationality"])
    ws.append(["Nationality", "Visa Class", "Issuances"])
    for fila in filas:
        ws.append(fila)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_fetch_visa_mes_argentina_usa_fallback_doble_espacio(monkeypatch):
    contenido = _xlsx_visas_bytes([
        ["Argentina", "B1/B2", 100],
        ["Argentina", "J1", 20],
        ["Brasil", "B1/B2", 500],
    ])

    class _Resp:
        def __init__(self, status_code, content=b""):
            self.status_code = status_code
            self.content = content
        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    llamadas = []

    def _fake_get(url, **kwargs):
        llamadas.append(url)
        if "%20%20-%20NIV" in url:      # variante de doble espacio: existe
            return _Resp(200, contenido)
        return _Resp(404)               # variante de un solo espacio: 404

    monkeypatch.setattr(descargar_series.requests, "get", _fake_get)
    total = descargar_series._fetch_visa_mes_argentina("niv", 2024, 5)
    assert total == 120
    assert len(llamadas) == 2   # probó un espacio, falló, probó dos espacios


def test_fetch_visa_mes_argentina_sin_datos_devuelve_none(monkeypatch):
    class _Resp:
        status_code = 404
        content = b""
        def raise_for_status(self):
            pass
    monkeypatch.setattr(descargar_series.requests, "get", lambda *a, **k: _Resp())
    assert descargar_series._fetch_visa_mes_argentina("iv", 2030, 1) is None


def test_eeuu_niv_mensual_no_repite_meses_ya_guardados(monkeypatch):
    store = {"eeuu_niv": {"mensual": {"2023-12": 999}}}
    monkeypatch.setattr(descargar_series, "_meses_desde", lambda a, m: [(2023, 12), (2024, 1)])
    pedidos = []

    def _fake_fetch(tipo, anio, mes):
        pedidos.append((anio, mes))
        return 42

    monkeypatch.setattr(descargar_series, "_fetch_visa_mes_argentina", _fake_fetch)
    monkeypatch.setattr(descargar_series.time, "sleep", lambda *_: None)
    resultado = descargar_series.fetch_componente_b_eeuu_niv_mensual(store)
    assert pedidos == [(2024, 1)]              # 2023-12 ya estaba, no se repite
    assert resultado["mensual"] == {"2023-12": 999, "2024-01": 42}


# ── España (INE) ─────────────────────────────────────────────────────────────

def test_espana_anual_filtra_la_serie_correcta(monkeypatch):
    payload = [
        {"Nombre": "Total Nacional. Dato base. Argentina. España. ",
         "Data": [{"Anyo": 2024, "Valor": 999.0}]},
        {"Nombre": "Total Nacional. Dato base. Argentina. Total. ",
         "Data": [{"Anyo": 2025, "Valor": 11291.0}, {"Anyo": 2024, "Valor": 8558.0}]},
    ]

    class _Resp:
        def raise_for_status(self):
            pass
        def json(self):
            return payload

    monkeypatch.setattr(descargar_series.requests, "get", lambda *a, **k: _Resp())
    resultado = descargar_series.fetch_componente_b_espana_anual()
    assert resultado == {"anual": {"2025": 11291, "2024": 8558}}


# ── Italia (ISTAT/AIRE) ──────────────────────────────────────────────────────

def test_italia_aire_anual_filtra_argentina_totale(monkeypatch):
    csv_texto = (
        "Anno;Paese;Sesso;Acquisizioni di cittadinanza\n"
        "2023;Argentina;Maschi;16538\n"
        "2023;Argentina;Femmine;16592\n"
        "2023;Argentina;Totale;33130\n"
        "2023;Brasile;Totale;9999\n"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("AIRE_it.csv", csv_texto)

    class _Resp:
        content = buf.getvalue()
        def raise_for_status(self):
            pass

    monkeypatch.setattr(descargar_series.requests, "get", lambda *a, **k: _Resp())
    resultado = descargar_series.fetch_componente_b_italia_aire_anual()
    assert resultado == {"anual": {"2023": 33130}}


# ── Chile (SERMIG) ───────────────────────────────────────────────────────────

def test_chile_anual_descubre_el_link_vigente_y_suma_por_anio(monkeypatch):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["SEXO", "PAÍS", "AÑO", "TIPO_RESUELTO", "Total"])
    ws.append(["Mujer", "Argentina", 2024, "Otorga", "500"])
    ws.append(["Hombre", "Argentina", 2024, "Otorga", "428"])
    ws.append(["Mujer", "Argentina", 2024, "Rechaza", "50"])
    ws.append(["Mujer", "Bolivia", 2024, "Otorga", "9999"])
    buf = io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    class _RespPagina:
        text = ('<a href="https://serviciomigraciones.cl/wp-content/uploads/estudios/'
                'Datos-abiertos/RD/RD-Resueltas-2o-semestre-2025.xlsx">link</a>')
        def raise_for_status(self):
            pass

    class _RespExcel:
        content = xlsx_bytes
        def raise_for_status(self):
            pass

    llamadas = {"n": 0}

    def _fake_get(url, **kwargs):
        llamadas["n"] += 1
        return _RespPagina() if "datos-abiertos" in url else _RespExcel()

    monkeypatch.setattr(descargar_series.requests, "get", _fake_get)
    resultado = descargar_series.fetch_componente_b_chile_anual()
    assert resultado == {"anual": {"2024": 928}}   # 500 + 428, Rechaza y Bolivia no cuentan


def test_chile_anual_sin_link_lanza_error(monkeypatch):
    class _RespPagina:
        text = "<html>sin links</html>"
        def raise_for_status(self):
            pass
    monkeypatch.setattr(descargar_series.requests, "get", lambda *a, **k: _RespPagina())
    try:
        descargar_series.fetch_componente_b_chile_anual()
        assert False, "debería haber lanzado ValueError"
    except ValueError:
        pass


# ── Store agregador: gate de frescura ───────────────────────────────────────

def test_fetch_componente_b_store_no_llama_fetchers_si_ya_esta_al_dia(tmp_path, monkeypatch):
    mes_actual = datetime.today().strftime("%Y-%m")
    store_path = tmp_path / "componente_b_migracion.json"
    store_path.write_text(json.dumps({
        "_meta": {"actualizado": f"{mes_actual}-05"},
        "eeuu_niv": {"mensual": {"2024-01": 111}},
    }), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "COMPONENTE_B_STORE", store_path)

    def _falla(*a, **k):
        raise AssertionError("no debería llamar a ningún fetcher si el store ya está al día")
    monkeypatch.setattr(descargar_series, "fetch_componente_b_espana_anual", _falla)

    resultado = descargar_series.fetch_componente_b_store()
    assert resultado["eeuu_niv"]["mensual"] == {"2024-01": 111}


def test_fetch_componente_b_store_con_fuente_fallida_no_avanza_el_gate(tmp_path, monkeypatch):
    # Si una fuente falla, el sello "actualizado" NO avanza al mes actual:
    # si avanzara, el gate de frescura saltearía los reintentos el resto del
    # mes y el dato viejo quedaría presentado bajo fecha de actualización
    # nueva. Las fuentes sanas sí se actualizan en la misma pasada.
    store_path = tmp_path / "componente_b_migracion.json"
    store_path.write_text(json.dumps({
        "_meta": {"actualizado": "2026-06-03"},   # mes PASADO: el gate no corta
        "eeuu_niv": {"mensual": {"2024-01": 111}},
    }), encoding="utf-8")
    monkeypatch.setattr(descargar_series, "COMPONENTE_B_STORE", store_path)

    sanos = {
        "fetch_componente_b_canada_mensual": {"mensual": {"2026-05": 25}},
        "fetch_componente_b_espana_anual": {"anual": {"2025": 11291}},
        "fetch_componente_b_italia_aire_anual": {"anual": {"2024": 33492}},
        "fetch_componente_b_chile_anual": {"anual": {"2025": 580}},
        "fetch_componente_b_eeuu_iv_mensual": {"mensual": {"2025-09": 63}},
    }
    for nombre, retorno in sanos.items():
        monkeypatch.setattr(descargar_series, nombre, lambda *a, _r=retorno, **k: _r)

    def _falla(*a, **k):
        raise RuntimeError("timeout simulado")
    monkeypatch.setattr(descargar_series, "fetch_componente_b_eeuu_niv_mensual", _falla)

    resultado = descargar_series.fetch_componente_b_store()

    persistido = json.loads(store_path.read_text(encoding="utf-8"))
    assert persistido["_meta"]["actualizado"] == "2026-06-03"   # no avanzó
    assert persistido["canada_pr"]["mensual"] == {"2026-05": 25}   # sana: actualizada
    assert persistido["eeuu_niv"]["mensual"] == {"2024-01": 111}   # fallida: conserva lo anterior
    assert resultado["_meta"]["actualizado"] == "2026-06-03"


# ── espiritu_epoca.py: contexto_duro en la card ─────────────────────────────

def test_contexto_duro_componente_b_toma_el_ultimo_periodo_de_cada_fuente(monkeypatch):
    fake_store = {
        "_meta": {"actualizado": "2026-07-10"},
        "eeuu_niv": {"mensual": {"2025-08": 1, "2025-09": 2}},
        "espana_nacionalidad": {"anual": {"2023": 10, "2024": 20, "2025": 30}},
        "chile_residencia": {"anual": {}},   # fuente sin datos: se omite
    }

    class _FakeDS:
        @staticmethod
        def fetch_componente_b_store():
            return fake_store

    monkeypatch.setitem(sys.modules, "descargar_series", _FakeDS())
    contexto = espiritu_epoca._contexto_duro_componente_b()
    assert contexto == {
        "eeuu_niv": {"periodo": "2025-09", "valor": 2},
        "espana_nacionalidad": {"periodo": "2025", "valor": 30},
    }


def test_contexto_duro_componente_b_si_falla_devuelve_vacio(monkeypatch):
    class _FakeDS:
        @staticmethod
        def fetch_componente_b_store():
            raise RuntimeError("sin red en test")
    monkeypatch.setitem(sys.modules, "descargar_series", _FakeDS())
    assert espiritu_epoca._contexto_duro_componente_b() == {}
