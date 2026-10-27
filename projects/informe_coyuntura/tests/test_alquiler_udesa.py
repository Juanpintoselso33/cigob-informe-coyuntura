"""Alquiler real de UdeSA - Mercado Libre (ADR-0386). Sin red.

Cuatro cosas: el registro versionado está bien formado y cada valor trae su frase,
el cálculo real/índice, el script de carga mensual y el aviso de atraso, y la
composición de la dimensión de precios.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "scripts/vida_cotidiana/collectors"))

import importlib.util  # noqa: E402

import alquiler_udesa as au  # noqa: E402
import itvc  # noqa: E402

# El script de carga vive en scripts/vida_cotidiana/, donde hay un config.py que
# pisaría al de la raíz si esa carpeta entrara al sys.path: se carga por ruta.
_spec = importlib.util.spec_from_file_location(
    "cargar_alquiler_udesa", RAIZ / "scripts/vida_cotidiana/cargar_alquiler_udesa.py")
carga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(carga)


@pytest.fixture
def registro():
    return json.loads(au.REGISTRO.read_text(encoding="utf-8"))


# ── el registro versionado ────────────────────────────────────────────────────
def test_el_registro_valida(registro):
    meses = au.validar_registro(registro)
    assert min(meses) == "2023-01" and max(meses) >= "2026-09"


def test_cada_valor_trae_su_frase_y_el_valor_esta_en_ella(registro):
    """El valor tiene que aparecer en la frase textual: es lo que impide un
    número tipeado sin leer el PDF."""
    con_valor = {m: e for m, e in registro["meses"].items()
                 if e["interanual_deptos_amba_pct"] is not None}
    assert len(con_valor) == 16
    for mes, e in con_valor.items():
        assert f"{e['interanual_deptos_amba_pct']}%" in e["frase"], mes
        assert "interanual" in e["frase"], mes


def test_valor_actual_es_el_del_pdf_de_septiembre_2026(registro):
    e = registro["meses"]["2026-09"]
    assert e["interanual_deptos_amba_pct"] == 20.4
    assert "21.2% y 20.4%" in e["frase"]          # casas primero, departamentos segundo
    assert "septiembre de 2025" in e["frase"]


def test_los_meses_sin_dato_estan_listados_y_no_tienen_valor(registro):
    sin = set(registro["sin_dato"])
    sin_valor = {m for m, e in registro["meses"].items()
                 if e["interanual_deptos_amba_pct"] is None}
    assert sin == sin_valor and len(sin) == 29
    assert max(sin) == "2025-05"       # desde jun-2025 el informe da la interanual de AMBA


# ── validación ────────────────────────────────────────────────────────────────
def entrada(**kw):
    e = {"interanual_deptos_amba_pct": 20.4, "intermensual_deptos_amba_pct": None,
         "frase": "…20.4%.", "url_pdf": "https://drive.google.com/file/d/x/view",
         "cargado_en": "2026-10-27"}
    e.update(kw)
    return e


@pytest.mark.parametrize("mes,kw", [
    ("2026-13", {}), ("2026-9", {}), ("septiembre", {}),
    ("2026-09", {"interanual_deptos_amba_pct": "20,4"}),
    ("2026-09", {"interanual_deptos_amba_pct": 900}),
    ("2026-09", {"interanual_deptos_amba_pct": True}),
    ("2026-09", {"frase": " "}),
    ("2026-09", {"url_pdf": "http://x"}),
    ("2026-09", {"cargado_en": "27/10/2026"}),
])
def test_entradas_mal_formadas_se_rechazan(mes, kw):
    with pytest.raises(ValueError):
        au.validar_entrada(mes, entrada(**kw))


# ── cálculo ───────────────────────────────────────────────────────────────────
def niveles_ipc():
    # IPC con +30% interanual constante desde 2025-01
    n = {}
    for i in range(24):
        a, m = 2025 + (i // 12), i % 12 + 1
        n[f"{a}-{m:02d}"] = 100 * 1.30 ** (i / 12)
    return n


def test_real_es_nominal_deflactado():
    assert au.real_interanual_pct(30.0, 30.0) == pytest.approx(0.0)
    assert au.real_interanual_pct(20.4, 33.5) == pytest.approx(-9.8, abs=0.05)
    assert au.real_interanual_pct(50.0, 20.0) == pytest.approx(25.0)


def test_indice_signo_de_la_dimension_de_precios():
    assert au.indice_componente(0.0) == 100.0
    assert au.indice_componente(-9.84) == 109.8      # más barato en términos reales = alivio
    assert au.indice_componente(12.0) == 88.0        # más caro = deterioro


def test_ipc_interanual_necesita_el_mes_del_año_anterior():
    n = niveles_ipc()
    assert au.ipc_interanual_pct(n, "2026-03") == pytest.approx(30.0)
    assert au.ipc_interanual_pct(n, "2025-03") is None


def test_serie_no_interpola_meses_sin_dato_ni_sin_ipc():
    meses = {"2026-01": entrada(interanual_deptos_amba_pct=30.0),
             "2026-02": entrada(interanual_deptos_amba_pct=None),
             "2026-03": entrada(interanual_deptos_amba_pct=39.0),
             "2027-01": entrada(interanual_deptos_amba_pct=40.0)}     # IPC no publicado
    pts = au.serie(meses, niveles_ipc())
    assert [p["mes"] for p in pts] == ["2026-01", "2026-03"]
    assert pts[0]["real"] == pytest.approx(0.0, abs=0.01)
    assert pts[1]["real"] == pytest.approx(0.0 + (1.39 / 1.30 - 1) * 100, abs=0.01)


def test_tarjeta_es_el_ultimo_punto_y_coincide_con_la_serie():
    meses = {"2026-01": entrada(interanual_deptos_amba_pct=30.0),
             "2026-03": entrada(interanual_deptos_amba_pct=39.0)}
    t = au.tarjeta(meses, niveles_ipc())
    assert t["fecha"] == "2026-03-01"
    assert t["valor"] == au.serie(meses, niveles_ipc())[-1]["real"]
    assert t["indice"] == au.indice_componente(t["valor"])
    assert t["nominal_pct"] == 39.0


def test_tarjeta_sin_ningun_punto_levanta():
    with pytest.raises(ValueError):
        au.tarjeta({"2026-01": entrada(interanual_deptos_amba_pct=None)}, niveles_ipc())


# ── script de carga ───────────────────────────────────────────────────────────
def registro_base():
    return {"meses": {"2026-09": entrada()}, "sin_dato": {"2026-10": "sin dato"}}


def test_carga_agrega_un_mes_y_lo_saca_de_sin_dato():
    r = carga.agregar(registro_base(), "2026-10", 19.8, "https://drive.google.com/file/d/y/view",
                      "…cambios … del 20.0% y 19.8%…", hoy=date(2026, 11, 3))
    assert r["meses"]["2026-10"]["interanual_deptos_amba_pct"] == 19.8
    assert r["meses"]["2026-10"]["cargado_en"] == "2026-11-03"
    assert "2026-10" not in r["sin_dato"]
    assert list(r["meses"]) == sorted(r["meses"])


def test_anotar_sin_dato_retira_el_valor_que_habia():
    r = carga.anotar_sin_dato(registro_base(), "2026-09", "cifra mal atribuida")
    assert "2026-09" not in r["meses"] and r["sin_dato"]["2026-09"] == "cifra mal atribuida"


def test_carga_rechaza_duplicado_futuro_y_sin_frase():
    with pytest.raises(ValueError, match="ya está cargado"):
        carga.agregar(registro_base(), "2026-09", 20.4, "https://x.y/z", "20.4%", hoy=date(2026, 11, 3))
    with pytest.raises(ValueError, match="futuro"):
        carga.agregar(registro_base(), "2027-01", 20.0, "https://x.y/z", "20.0%", hoy=date(2026, 11, 3))
    with pytest.raises(ValueError):
        carga.agregar(registro_base(), "2026-10", 20.0, "https://x.y/z", "  ", hoy=date(2026, 11, 3))
    with pytest.raises(ValueError):
        carga.agregar(registro_base(), "2026-10", 20.0, "no-es-url", "20.0%", hoy=date(2026, 11, 3))


def test_carga_reemplaza_solo_con_la_bandera():
    r = carga.agregar(registro_base(), "2026-09", 20.5, "https://x.y/z", "20.5%",
                      hoy=date(2026, 11, 3), reemplazar=True)
    assert r["meses"]["2026-09"]["interanual_deptos_amba_pct"] == 20.5


def test_cli_escribe_el_archivo_y_valida(tmp_path, capsys):
    ruta = tmp_path / "alquiler.json"
    ruta.write_text(json.dumps(registro_base()), encoding="utf-8")
    hoy = date.today().strftime("%Y-%m")
    rc = carga.main(["--mes", hoy, "--valor", "18.5", "--url", "https://x.y/z",
                     "--frase", "interanual … 18.5%"], path=ruta)
    assert rc == 0 and json.loads(ruta.read_text())["meses"][hoy]["interanual_deptos_amba_pct"] == 18.5
    assert carga.main(["--mes", hoy, "--valor", "1", "--url", "https://x.y/z", "--frase", "1%"], path=ruta) == 2
    assert carga.main(["--mes", "2026-08", "--sin-dato", "no lo trae"], path=ruta) == 0
    assert json.loads(ruta.read_text())["sin_dato"]["2026-08"] == "no lo trae"
    assert carga.main(["--mes", "2026-07", "--valor", "5"], path=ruta) == 2     # sin url ni frase


# ── aviso de atraso ───────────────────────────────────────────────────────────
def test_aviso_a_los_45_dias_sin_carga_y_no_antes():
    meses = {"2026-09": entrada(cargado_en="2026-10-27")}
    avisos = []
    emisor = lambda *a: avisos.append(a)   # noqa: E731
    assert au.avisar_si_atrasado(meses, date(2026, 12, 11), emisor) is False     # 45 días justos
    assert au.avisar_si_atrasado(meses, date(2026, 12, 12), emisor) is True      # 46
    assert len(avisos) == 1
    indicador, registro_, motivo, fuente = avisos[0]
    assert indicador == "alquiler_udesa_real" and "2026-09" in registro_
    assert "cargar_alquiler_udesa.py" in motivo and fuente == au.URL_PAGINA


def test_el_aviso_usa_la_carga_mas_reciente():
    meses = {"2026-08": entrada(cargado_en="2026-09-01"), "2026-09": entrada(cargado_en="2026-10-27")}
    assert au.dias_sin_carga(meses, date(2026, 11, 10)) == 14


# ── composición de la dimensión ───────────────────────────────────────────────
def test_precios_suma_uno_y_no_toca_alimentos_ni_servicios():
    p = itvc.DIMENSIONES_ITVC["precios"]
    assert p["peso"] == 0.25                      # el peso de la dimensión no se mueve
    assert p["indicadores"] == {"ipc_alimentos": 0.35, "peso_tarifas": 0.45,
                                "alquiler_real": 0.10, "alquiler_udesa_real": 0.10}
    assert abs(sum(p["indicadores"].values()) - 1.0) < 1e-9
    # la vivienda sigue pesando lo que fijó ADR-0111
    assert p["indicadores"]["alquiler_real"] + p["indicadores"]["alquiler_udesa_real"] == pytest.approx(0.20)


def test_el_componente_entra_por_su_serie():
    assert itvc.SERIES_REBASEADAS["itvc_alquiler_udesa"] == "alquiler_udesa_real"


def test_efecto_en_la_dimension_con_los_numeros_del_27_oct():
    idx = {"ipc_alimentos": 107.6, "peso_tarifas": 111.3, "alquiler_real": 50.0,
           "alquiler_udesa_real": 109.8}
    r = itvc.calcular_itvc(idx)
    assert r["dimensiones"]["precios"]["puntaje"] == 103.7      # 97,7 antes
    sin = dict(idx)
    sin.pop("alquiler_udesa_real")
    # sin el componente, la dimensión renormaliza sobre los tres que quedan
    r2 = itvc.calcular_itvc(sin)
    esperado = (0.35 * 107.6 + 0.45 * 111.3 + 0.10 * 50.0) / 0.90
    assert r2["dimensiones"]["precios"]["puntaje"] == round(esperado, 1)


def test_config_declara_el_tope_de_demora_de_la_carga_manual():
    import config
    assert config.MAX_DIAS["alquiler_udesa_real"] == 105
    texto = (RAIZ / "config.py").read_text(encoding="utf-8")
    assert "CARGA MANUAL mensual" in texto
