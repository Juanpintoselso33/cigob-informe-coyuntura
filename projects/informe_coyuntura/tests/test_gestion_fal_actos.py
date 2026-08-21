"""El FAL puntúa lo que RIGE, no lo que se dictó (ADR-0228).

Lo que se protege es la corrección de fondo, no la aritmética: entre el 30 de
marzo y el 23 de abril de 2026 la Ley 27.802 estuvo suspendida con efecto
general por la cautelar de «CGTRA c/ Estado Nacional», que alcanzaba a los
artículos del Fondo, y el indicador de ADR-0142 —que contaba actos DICTADOS—
publicó 100 durante esos días sin que nada pudiera avisarlo.

Cuatro guardas, cada una contra una forma distinta de perder esa corrección:

1. un acto suspendido no cuenta            → la regla, en la card y en la serie
2. la serie puede BAJAR                    → lo que ADR-0142 hizo imposible
3. la adopción no se contamina             → «cese laboral» ≠ «asistencia laboral»
4. la reversión está dicha en la ficha     → un lector tiene que poder discutirla
"""
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import descargar_series  # noqa: E402
import gestion  # noqa: E402
import itcg  # noqa: E402
import parametrica  # noqa: E402

HITOS = json.loads(gestion.FAL_HITOS_PATH.read_text(encoding="utf-8-sig"))


def test_los_dos_actos_siguen_siendo_ley_y_reglamentacion():
    normas = [n for n, _ in gestion.FAL_ACTOS_FUNDAMENTALES]
    assert normas == ["Ley 27.802", "Decreto 408/2026"]


def test_los_dos_actos_estan_en_el_registro_de_hitos():
    """No se inventan fechas: cada acto tiene que estar respaldado por una norma
    publicada en fal_hitos.json, verificable por número en InfoLeg."""
    por_norma = {h["norma"]: h for h in HITOS["construccion"]}
    for norma, _ in gestion.FAL_ACTOS_FUNDAMENTALES:
        assert norma in por_norma, f"{norma} no está en fal_hitos.json"
        assert por_norma[norma]["fecha"] <= date.today().isoformat()
        assert por_norma[norma].get("fuente"), "el hito debe declarar su fuente"


def test_las_tres_etapas_pesan_lo_que_dice_el_adr():
    pesos = (gestion.FAL_PESO_CONSTRUCCION, gestion.FAL_PESO_VIGENCIA,
             gestion.FAL_PESO_ADOPCION)
    assert pesos == (0.50, 0.20, 0.30)
    assert round(sum(pesos), 6) == 1.0


# ── 1 · Un acto suspendido no cuenta ────────────────────────────────────────
def test_la_suspension_judicial_esta_registrada_con_su_fuente():
    """El hecho que motiva todo esto tiene que estar asentado con órgano, fechas
    y fuente — si no, es una afirmación sin respaldo dentro de un índice."""
    susp = HITOS["judicial"]["suspensiones"]
    ley = [s for s in susp if s["norma"] == "Ley 27.802"]
    assert ley, "falta la suspensión de la Ley 27.802 (30-mar → 23-abr-2026)"
    s = ley[0]
    assert s["desde"] == "2026-03-30" and s["hasta"] == "2026-04-23"
    assert s.get("organo") and s.get("levantada_por") and s.get("fuente")
    assert "FAL" in s["alcance"] or "Fondo de Asistencia Laboral" in s["alcance"], (
        "una suspensión que no alcanza a los artículos del Fondo no tiene por "
        "qué mover este indicador")


def test_un_acto_suspendido_no_cuenta_como_construccion():
    """La regla nueva, aislada. Al 15-abr-2026 la ley estaba dictada y frenada:
    ADR-0142 la contaba igual (50 puntos) porque miraba la fecha de la norma."""
    dentro = gestion.fal_estado_actos(HITOS, "2026-04-15")[0]
    assert dentro["dictado"] and dentro["suspendido"] and not dentro["vigente"]

    fuera = gestion.fal_estado_actos(HITOS, "2026-05-15")[0]
    assert fuera["dictado"] and not fuera["suspendido"] and fuera["vigente"]


def test_el_indice_cae_mientras_la_ley_esta_suspendida():
    en_suspension, _, _ = gestion.fal_indice(HITOS, "2026-04-15", 0)
    levantada, _, _ = gestion.fal_indice(HITOS, "2026-05-15", 0)
    assert en_suspension == 0.0, "sin ley vigente no hay construcción que contar"
    assert levantada == 25.0, "la ley sola es la mitad de la construcción"


def test_la_vigencia_del_regimen_no_se_da_por_cumplida_antes_de_tiempo():
    """El 1-nov-2026 lo fijó el artículo 27 del propio decreto reglamentario, que
    difirió cinco meses el arranque. No es un supuesto del proyecto."""
    assert HITOS["vigencia"]["fecha"] == "2026-11-01"
    antes, _, e_antes = gestion.fal_indice(HITOS, "2026-10-31", 0)
    despues, _, e_desp = gestion.fal_indice(HITOS, "2026-11-01", 0)
    assert (e_antes["vigencia"], antes) == (0.0, 50.0)
    assert (e_desp["vigencia"], despues) == (1.0, 70.0)


def test_el_techo_solo_se_alcanza_con_fondos_operando():
    con_fondo, _, _ = gestion.fal_indice(HITOS, "2026-11-01", 1)
    assert con_fondo == 100.0
    sin_fondo, _, _ = gestion.fal_indice(HITOS, "2026-11-01", 0)
    assert sin_fondo == 70.0, "vigente y sin fondos no es el máximo"


# ── 2 · La serie puede bajar ────────────────────────────────────────────────
def test_la_serie_registra_la_caida_de_marzo():
    """La propiedad que ADR-0142 hizo imposible. La serie se evalúa al cierre de
    cada mes: el 31-mar-2026 la ley llevaba un día suspendida."""
    por_fecha = dict(descargar_series.fetch_fal_serie())
    assert por_fecha["2026-02-01"] == 0.0, "antes de la ley"
    assert por_fecha["2026-03-01"] == 0.0, "ley publicada el 6 y suspendida el 30"
    assert por_fecha["2026-04-01"] == 25.0, "cautelar levantada el 23-abr"
    assert por_fecha["2026-06-01"] == 50.0, "Decreto 408/2026 — 01-jun-2026"


def test_el_indice_puede_bajar():
    """El motivo de todo el cambio, dicho como propiedad y no como calendario.

    La serie REAL no muestra una caída porque la suspensión de marzo cayó sobre
    un mes que ya valía cero: la ley se publicó el 6 y se frenó el 30. Por eso
    la guarda no mira la serie publicada —que volvería a pasar si mañana
    alguien la vuelve a hacer monótona— sino la regla: inyectada una suspensión
    posterior, el índice tiene que bajar. Con el conteo de actos dictados de
    ADR-0142 esto era imposible por construcción.
    """
    import copy
    hipotesis = copy.deepcopy(HITOS)
    hipotesis["judicial"]["suspensiones"].append({
        "norma": "Decreto 408/2026", "desde": "2026-07-01", "hasta": None,
        "organo": "(hipotético, sólo para esta guarda)",
        "alcance": "FAL",
    })
    antes, _, _ = gestion.fal_indice(hipotesis, "2026-06-30", 0)
    despues, _, _ = gestion.fal_indice(hipotesis, "2026-07-01", 0)
    assert despues < antes, "el índice no puede bajar: volvió a contar actos dictados"
    assert (antes, despues) == (50.0, 25.0)


def test_una_suspension_sin_fecha_de_fin_sigue_vigente():
    """`hasta: null` es el caso que importa —una suspensión abierta hoy— y es el
    que más fácil se rompe al escribir la comparación de fechas."""
    import copy
    hipotesis = copy.deepcopy(HITOS)
    hipotesis["judicial"]["suspensiones"] = [
        {"norma": "Ley 27.802", "desde": "2026-03-30", "hasta": None, "alcance": "FAL"}]
    assert not gestion.fal_estado_actos(hipotesis, "2030-01-01")[0]["vigente"]


def test_la_card_y_la_serie_usan_la_misma_regla():
    """ADR-0098 y ADR-0142 se desincronizaron dos veces entre la card y la serie.
    Acá las dos pasan por `gestion.fal_indice`."""
    fuente = (RAIZ / "scripts" / "descargar_series.py").read_text(encoding="utf-8")
    i = fuente.index("def fetch_fal_serie")
    cuerpo = fuente[i:fuente.index("\ndef ", i + 10)]
    assert "gestion.fal_indice(" in cuerpo


# ── 3 · La adopción no se contamina con el régimen de la construcción ───────
def test_la_adopcion_no_cuenta_fondos_de_la_construccion():
    """«Fondo de cese laboral» es el régimen de la industria de la construcción
    (Ley 22.250). ADR-0068 ya lo sacó de la consulta al Boletín Oficial; si
    entrara por la CNV valdría treinta puntos del indicador sin ser el FAL."""
    registro = [{"Text": "FONDO DE CESE LABORAL CONSTRUCCION FCI"},
                {"Text": "OTRO FONDO CUALQUIERA"}]
    assert gestion._cnv_fondos_fal(registro) == 0
    assert gestion._cnv_fondos_cese(registro) == 1, "el conteo ancho sí lo ve"

    registro.append({"Text": "FAL ASISTENCIA LABORAL I - FIDEICOMISO"})
    assert gestion._cnv_fondos_fal(registro) == 1


# ── 4 · Bandas y texto público ─────────────────────────────────────────────
def test_las_bandas_describen_los_estados_de_la_escala():
    B = itcg.BANDAS_ITCG
    esperado = {0.0: 10.0, 25.0: 31.2, 50.0: 55.0, 70.0: 74.0, 100.0: 100.0}
    for valor, puntaje in esperado.items():
        assert parametrica.puntaje_de(
            valor, "fal_modernizacion_laboral", B) == puntaje


def test_la_reversion_editorial_esta_declarada_en_la_ficha():
    """ADR-0228 revierte una decisión editorial previa y EMPEORA el número. Un
    lector tiene que poder enterarse sin abrir el repositorio: qué se decidió
    antes, con qué evidencia se cambió y cuánto se movió el índice."""
    ficha = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
    i = ficha.index("fal_modernizacion_laboral: {")
    bloque = ficha[i:i + 12000]
    assert "ADR-0228" in bloque
    assert "revierte la decisión editorial" in bloque
    assert "empeora el número" in bloque
    for hecho in ("Chequeado", "Heritage", "30 de marzo"):
        assert hecho in bloque, f"la ficha no nombra la evidencia: {hecho}"


def test_el_indicador_mide_lo_que_su_nombre_dice():
    """La guarda de ADR-0218 aplicada acá: el compuesto de actos dictados de
    ADR-0142 no puede volver sin ADR."""
    fuente = (RAIZ / "scripts" / "gestion.py").read_text(encoding="utf-8")
    i = fuente.index("def fetch_fal_modernizacion_laboral")
    cuerpo = fuente[i:fuente.index("def fetch_litigiosidad_laboral")]
    assert "fal_indice(" in cuerpo
    assert "actos_cumplidos" not in cuerpo, "volvió el conteo de actos dictados"
