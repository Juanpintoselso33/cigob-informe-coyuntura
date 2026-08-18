# -*- coding: utf-8 -*-
"""Un indicador que anda por caché A PROPÓSITO no es carry-forward (ADR-0210).

`judicializacion` se refresca a mano porque SAIJ bloquea por IP a los runners.
Con la ventana declarada de 45 días de ADR-0191, el gate igual avisaba
`G2 politica: 1/18 en carry-forward` TODAS las noches, y el snapshot publicaba
`desactualizado:politica:judicializacion` desde el primer día. Un aviso que
suena siempre deja de leerse, y ahí se pierden los que sí importan.

Lo que estos tests fijan es el corte: la exención pide ventana **declarada** y
estar **adentro**. Sin declaración no hay ventana — bajarle la guardia a todo
habría dejado muda por dos semanas una caída real, que es exactamente cómo se
perdió `sentimiento_digital` el 9-jul-2026.
"""
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATE = RAIZ / "scripts" / "gate_calidad.py"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from config import (DIAS_SIN_FETCH, DIAS_SIN_FETCH_DEFAULT,  # noqa: E402
                    cache_es_esperable)


def _hace(dias):
    return (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")


def _snapshot(tmp_path, indicador, dias_sin_fetch):
    """Snapshot sano salvo por un indicador servido desde caché.

    `fecha_dato` es de hoy para que lo único que pueda hablar sea el
    carry-forward, y el test no pase ni falle por el motivo equivocado.
    """
    hoy = date.today().isoformat()
    ind = {
        "valor": 1.61, "fecha_dato": hoy, "fuente": "fuente de prueba",
        "unidad": "u", "desactualizado": True,
        "obtenido_en": _hace(dias_sin_fetch),
    }
    def sano():
        return {
            "valor": 2.0, "fecha_dato": hoy, "fuente": "fuente de prueba",
            "unidad": "u", "desactualizado": False, "obtenido_en": _hace(0),
        }
    # Cinco indicadores sanos para que 1 en caché sea el 17% y caiga en el
    # AVISO de carry-forward. Con menos, cruza el tope del 40% y sale por la
    # rama de falla del presupuesto, que es otro chequeo y taparía lo que se
    # está probando acá.
    indicadores = {f"sano_{n}": sano() for n in range(5)}
    indicadores[indicador] = ind
    informe = {
        "schema_version": 1, "generated_at": hoy + "T00:00:00",
        "period": hoy[:7], "score_global": 5.0,
        "cinturones": {"espiritu_epoca": {"score": 5.0, "indicadores": indicadores}},
    }
    (tmp_path / "informe.json").write_text(json.dumps(informe), encoding="utf-8")
    (tmp_path / "series.json").write_text(json.dumps({}), encoding="utf-8")
    return tmp_path


def _correr_gate(directorio):
    r = subprocess.run([sys.executable, str(GATE), "--snapshot", str(directorio)],
                       capture_output=True, text=True, cwd=str(RAIZ))
    return r, r.stdout + r.stderr


# ── el criterio, sin tocar el gate ───────────────────────────────────────────

def test_dentro_de_la_ventana_declarada_no_es_carry_forward():
    assert cache_es_esperable("judicializacion", 1)
    assert cache_es_esperable("judicializacion", 44)


def test_el_borde_exacto_todavia_esta_adentro():
    """45 días es el último día tolerado, no el primero que avisa."""
    tope = DIAS_SIN_FETCH["judicializacion"]
    assert cache_es_esperable("judicializacion", tope)
    assert not cache_es_esperable("judicializacion", tope + 1)


def test_sin_ventana_declarada_no_hay_exencion():
    """El corte que evita enmascarar una fuente recién caída."""
    assert not cache_es_esperable("sentimiento_digital", 1)
    assert not cache_es_esperable("sentimiento_digital", DIAS_SIN_FETCH_DEFAULT - 1)


def test_sin_sello_no_se_concede_ventana():
    """Sin `obtenido_en` no hay medición, y sin medición no hay perdón."""
    assert not cache_es_esperable("judicializacion", None)


# ── el gate de punta a punta ─────────────────────────────────────────────────

def test_el_gate_no_avisa_por_un_cache_esperable():
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(_snapshot(Path(d), "judicializacion", 30))
        assert "carry-forward" not in salida, (
            "judicializacion 30 días en caché está dentro de su ventana "
            "declarada y no debería avisar:\n" + salida)


def test_pasada_la_ventana_vuelve_a_avisar_y_ademas_corta():
    """No es que se calle para siempre: G2b FALLA, que corta la publicación."""
    with tempfile.TemporaryDirectory() as d:
        r, salida = _correr_gate(_snapshot(Path(d), "judicializacion", 60))
        assert "carry-forward" in salida, salida
        assert "[FALLA] G2b" in salida, salida
        assert r.returncode != 0


def test_una_fuente_sin_ventana_avisa_desde_el_primer_dia():
    """La regresión que más importa: que esto no calle una caída real.

    Nombre neutro a propósito: `sentimiento_digital` es el caso histórico pero
    vive en G3_EXCEPCIONES, y sin serie publicada dispara G3b — una falla real
    del gate que no tiene nada que ver con lo que se prueba acá.
    """
    with tempfile.TemporaryDirectory() as d:
        _, salida = _correr_gate(_snapshot(Path(d), "indicador_sin_ventana", 1))
        assert "carry-forward" in salida, (
            "una fuente sin ventana declarada tiene que avisar el primer "
            "día:\n" + salida)


# ── la política tiene un solo dueño ──────────────────────────────────────────

def test_el_gate_consume_la_tabla_de_config_y_no_una_copia():
    """Dos dueños se desincronizan; por eso la tabla se mudó a config.py."""
    from gate_calidad import G2B_MAX_DIAS, G2B_MAX_DIAS_DEFAULT
    assert G2B_MAX_DIAS is DIAS_SIN_FETCH
    assert G2B_MAX_DIAS_DEFAULT == DIAS_SIN_FETCH_DEFAULT


def test_generar_informe_usa_el_mismo_criterio_que_el_gate():
    """El flag del snapshot y el aviso del gate no pueden discrepar."""
    import generar_informe
    assert generar_informe.cache_es_esperable is cache_es_esperable


def test_el_helper_de_dias_tolera_un_sello_ilegible():
    import generar_informe
    assert generar_informe._dias_sin_fetch({}) is None
    assert generar_informe._dias_sin_fetch({"obtenido_en": "no es una fecha"}) is None
    assert generar_informe._dias_sin_fetch({"obtenido_en": _hace(3)}) == 3
