# -*- coding: utf-8 -*-
"""El backfill del archivo histórico tiene cuatro formas de arruinar BigQuery en
silencio, y estos tests cubren las cuatro (ADR-0209).

Ninguna se nota al correr: el script imprime "listo" igual. Por eso están acá y
no confiadas a una inspección posterior.

1. Pisar `series`, que se escribe con WRITE_TRUNCATE.
2. Leer los auxiliares del working tree en vez del commit, y estampar las
   correlaciones de hoy con un `generated_at` de junio.
3. Reventar el load con los 175 valores de texto de los indicadores de gestión
   que fueron cualitativos hasta el 2-jul-2026.
4. Marcar como corrida del cron una republicación hecha a mano.

Nada de acá toca BigQuery ni pide credenciales.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import bigquery_backfill as bf  # noqa: E402
import bigquery_export as bq  # noqa: E402


# --------------------------------------------------------------------------
# 3. El valor de texto no puede romper el load
# --------------------------------------------------------------------------

def test_un_valor_de_texto_va_a_valor_txt_y_deja_valor_en_null():
    """Caso real: `concesiones_infraestructura` antes del 2-jul-2026."""
    valor, txt = bq._valor_y_texto("Parcial — corredores viales en licitación")
    assert valor is None
    assert txt == "Parcial — corredores viales en licitación"


def test_un_valor_numerico_no_toca_valor_txt():
    assert bq._valor_y_texto(23.5) == (23.5, None)
    assert bq._valor_y_texto(0) == (0.0, None)      # 0 es un valor, no un vacío
    assert bq._valor_y_texto(-1.1) == (-1.1, None)


def test_un_valor_ausente_no_inventa_texto():
    assert bq._valor_y_texto(None) == (None, None)


def test_un_bool_no_se_cuela_como_numero():
    """bool es subclase de int: sin el corte explícito, True entraría como 1.0."""
    valor, txt = bq._valor_y_texto(True)
    assert valor is None and txt == "True"


def test_el_snapshot_con_indicador_cualitativo_no_pierde_la_fila():
    """El indicador tiene que seguir existiendo en el archivo, con su texto."""
    snap = {
        "generated_at": "2026-06-01T03:00:00+00:00",
        "cinturones": {
            "gestion": {
                "score": 2.0,
                "indicadores": {
                    "privatizaciones": {
                        "valor": "En proceso — Aerolíneas y Correo sin transferencia",
                        "en_indice": True,
                    }
                },
            }
        },
    }
    filas = bq.construir_filas(snap, raiz=RAIZ)
    fila = next(f for f in filas["indicadores"] if f["indicador"] == "privatizaciones")
    assert fila["valor"] is None
    assert fila["valor_txt"].startswith("En proceso")


# --------------------------------------------------------------------------
# 4. `origen` distingue el cron de una republicación a mano
# --------------------------------------------------------------------------

def test_origen_es_cron_solo_dentro_de_github_actions(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert bq.origen_de_esta_corrida() == "cron"


def test_origen_es_manual_fuera_de_ci(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert bq.origen_de_esta_corrida() == "manual"


def test_origen_es_manual_si_la_variable_no_dice_true(monkeypatch):
    """En una shell local `GITHUB_ACTIONS` puede quedar seteada en cualquier cosa."""
    monkeypatch.setenv("GITHUB_ACTIONS", "")
    assert bq.origen_de_esta_corrida() == "manual"


def test_el_origen_explicito_le_gana_al_entorno(monkeypatch):
    """El backfill sabe el origen por el autor del commit; el entorno no aplica."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    snap = {"generated_at": "2026-06-01T03:00:00+00:00", "cinturones": {}}
    filas = bq.construir_filas(snap, raiz=RAIZ, origen="manual")
    assert filas["corridas"][0]["origen"] == "manual"


# --------------------------------------------------------------------------
# 1. `series` no puede entrar al backfill
# --------------------------------------------------------------------------

def test_series_esta_excluida_del_backfill():
    """Se escribe con WRITE_TRUNCATE: una corrida vieja pisaría la tabla entera."""
    assert "series" in bf.TABLAS_EXCLUIDAS


def test_el_exportador_nocturno_si_escribe_series():
    """El backfill la excluye; el pipeline diario NO. Si esto se rompe, la tabla
    de series se congela en la última corrida que la haya escrito."""
    assert "series" not in bq.CINTURONES_CON_SERIE  # sanity: son cinturones, no tablas
    snap = {"generated_at": "2026-08-18T00:00:00+00:00", "cinturones": {}}
    assert "series" in bq.construir_filas(snap, raiz=RAIZ)


# --------------------------------------------------------------------------
# 2. `raiz` tiene que redirigir de verdad la lectura
# --------------------------------------------------------------------------

def test_raiz_redirige_los_auxiliares(tmp_path):
    """Si `raiz` se ignorara, acá saldrían las correlaciones del working tree."""
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "validacion_externa.json").write_text(
        json.dumps({"correlaciones": {"itvc_vs_icc": {"r": 0.42, "n": 7}}}),
        encoding="utf-8",
    )
    filas = bq.construir_filas_analisis("2026-06-01T03:00:00+00:00", raiz=tmp_path)
    assert [(f["par"], f["r"], f["n"]) for f in filas["correlaciones"]] == [
        ("itvc_vs_icc", 0.42, 7)
    ]


def test_una_raiz_sin_auxiliares_no_revienta(tmp_path):
    """Las corridas de mayo y junio son anteriores a validacion_externa.json.
    Es ausencia legítima, no una falla."""
    (tmp_path / "output").mkdir()
    filas = bq.construir_filas_analisis("2026-05-23T12:47:45+00:00", raiz=tmp_path)
    assert all(v == [] for v in filas.values())


def test_raiz_redirige_las_series(tmp_path):
    (tmp_path / "output" / "series").mkdir(parents=True)
    (tmp_path / "output" / "series" / "macro.csv").write_text(
        "fecha,indicador,valor,unidad,fuente\n2026-01-01,ipc_total,2.5,%,INDEC\n",
        encoding="utf-8",
    )
    snap = {"generated_at": "2026-06-01T03:00:00+00:00", "cinturones": {}}
    filas = bq.construir_filas(snap, raiz=tmp_path)
    assert filas["series"] == [{
        "fecha": "2026-01-01", "cinturon": "macro", "indicador": "ipc_total",
        "valor": 2.5, "unidad": "%", "fuente": "INDEC",
    }]


# --------------------------------------------------------------------------
# La historia que el backfill dice recuperar
# --------------------------------------------------------------------------

def test_la_historia_en_git_no_tiene_corridas_rotas():
    """225 corridas, todas parseables, ninguna sin `generated_at` ni origen.

    Es el supuesto sobre el que se apoya todo el backfill; si git deja de poder
    contarlo, quiero enterarme acá y no a mitad de una escritura en BigQuery.
    """
    corridas = bf.corridas_en_git()
    assert len(corridas) >= 225
    assert all(c["generated_at"] for c in corridas)
    assert {c["origen"] for c in corridas} == {"cron", "manual"}
    # ordenadas y sin `generated_at` repetido: es la clave de corrida en BQ
    gens = [c["generated_at"] for c in corridas]
    assert gens == sorted(gens)
    assert len(gens) == len(set(gens))
