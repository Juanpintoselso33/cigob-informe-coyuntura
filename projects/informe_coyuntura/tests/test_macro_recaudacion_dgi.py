"""Tests del indicador de recaudación: fuente DGI (ADR-0127) y métrica de NIVEL
de base imponible real desestacionalizada, nación + provincias (ADR-0152)."""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import itcm
import macro
import parametrica


def test_el_indicador_apunta_a_la_dgi():
    assert macro.INDEC_RECAUDACION_ID == "172.3_SOTAL_DDGI_M_0_0_12"


def test_el_total_y_la_aduana_siguen_disponibles_como_contexto():
    assert macro.INDEC_RECAUDACION_TOTAL_ID == "172.3_TL_RECAION_M_0_0_17"
    assert macro.INDEC_RECAUDACION_DGA_ID == "172.3_SOTAL_DDGA_M_0_0_12"


def test_el_resultado_primario_se_mide_contra_la_recaudacion_TOTAL():
    """El bug que ADR-0127 casi deja pasar: resultado_primario usaba la MISMA
    constante que el indicador de recaudación como denominador ("% de la
    recaudación"). Al apuntar esa constante a la DGI, el resultado primario
    habría pasado a medirse contra una base ~40% más chica sin que nada avisara.

    Se verifica leyendo el código, no el dato: lo que se protege es que el
    denominador esté escrito explícitamente y no herede el cambio de otro
    indicador."""
    fuente = Path(macro.__file__).read_text(encoding="utf-8")
    inicio = fuente.index("def _superavit_sobre_recaudacion_12m")
    cuerpo = fuente[inicio:inicio + 3000]
    assert "INDEC_RECAUDACION_TOTAL_ID" in cuerpo, (
        "el resultado primario dejó de apuntar explícitamente al total")
    assert "_indec_serie(INDEC_RECAUDACION_ID" not in cuerpo, (
        "el resultado primario volvió a compartir la constante del indicador "
        "de recaudación: su denominador cambiaría al cambiar de serie esa card")


def test_las_bandas_son_pasos_de_diez_sobre_la_base_de_la_transicion():
    """ADR-0152 rehizo las bandas porque la métrica dejó de ser una variación.

    Hasta el 29-jul-2026 este test afirmaba lo contrario —que las bandas NO se
    habían tocado al cambiar de serie en ADR-0127, con el cero de la variación
    como punto de referencia— y era correcto mientras la unidad fuera «% real
    interanual». Al pasar a NIVEL de base imponible real con 100 = 4T-2023 esas
    bandas no eran traducibles: el punto con significado de un nivel base-100 es
    el 100, no el 0. Los cortes son pasos de diez puntos de la base real de la
    transición, grilla conceptual y no ajuste a lo observado (ADR-0045).

    Si alguien las mueve, que sea con un ADR propio y no de arrastre.
    """
    assert itcm.BANDAS_ITCM["recaudacion"] == [
        (110.0, float("inf"), 100), (100.0, 110.0, 85), (90.0, 100.0, 60),
        (80.0, 90.0, 35), (float("-inf"), 80.0, 10),
    ]


def test_el_cien_es_el_punto_de_corte_relevante():
    """Igualar o no la base imponible real de la transición separa dos bandas."""
    assert parametrica.puntaje_banda(100.01, itcm.BANDAS_ITCM["recaudacion"]) == 85
    assert parametrica.puntaje_banda(99.99, itcm.BANDAS_ITCM["recaudacion"]) == 60


def test_la_metrica_es_un_nivel_y_no_una_variacion():
    """Guarda contra volver a una variación sin tocar las bandas: un valor
    plausible como variación (+3%) caería en la banda más baja del nivel, y un
    nivel plausible (95) sería un crecimiento absurdo como variación. Los dos
    dominios son incompatibles, así que la unidad publicada tiene que decirlo."""
    assert parametrica.puntaje_banda(3.0, itcm.BANDAS_ITCM["recaudacion"]) == 10
    unidades = Path(REPO / "web/src/lib/datos.ts").read_text(encoding="utf-8")
    assert "recaudacion: \"base 100\"" in unidades, (
        "la unidad corta de la web tiene que declarar que es un nivel base-100")


def test_las_series_de_control_apuntan_a_iva_y_cheque():
    """ADR-0318: IVA-DGI y créditos/débitos bancarios entran como CONTROL, no
    como cards nuevas — los ids tienen que ser justamente los verificados."""
    assert macro.INDEC_IVA_DGI_ID == "142.3_IVA_D_2001_M_7"
    assert macro.INDEC_CHEQUE_ID == "142.3_CREDI_2001_M_24"


def test_control_tributario_detecta_divergencia_de_sentido():
    """El caso que motiva el control: el agregado sube mientras los dos
    impuestos ligados a actividad caen. Si el guard no mirara el signo de los
    tres, esto pasaría desapercibido."""
    ipc = {f"2025-{m:02d}": 100.0 * 1.02 ** m for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 * 1.02 ** (12 + m) for m in range(1, 9)})
    # Agregado (índice ya real, base 100): sube de un año a otro.
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 90.0 for m in range(1, 8)})
    serie_sa["2026-08"] = 99.0  # +10% i.a. real del agregado

    def nominal_constante_real(base):
        # Nominal tal que, deflactado por el mismo IPC, cae ~10% real i.a.
        return {ym: base * ipc[ym] / 100.0 * (0.9 if ym == "2026-08" else 1.0)
                for ym in ipc}

    iva_nom = nominal_constante_real(1000.0)
    cheque_nom = nominal_constante_real(500.0)

    control = macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08")
    assert control["fecha"] == "2026-08"
    assert control["agregado_var_ia_real"] == 10.0
    assert control["iva_var_ia_real"] == -10.0
    assert control["cheque_var_ia_real"] == -10.0
    assert control["diverge"] is True
    assert control["meses_atraso"] == 0


def test_control_tributario_no_marca_divergencia_falsa_cuando_van_juntos():
    """Control negativo del test anterior: si los tres se mueven en el mismo
    sentido, un guard que devolviera `diverge=True` siempre pasaría el positivo
    igual — este es el que lo discrimina."""
    ipc = {f"2025-{m:02d}": 100.0 for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 for m in range(1, 9)})
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 90.0 for m in range(1, 8)})
    serie_sa["2026-08"] = 99.0  # +10% i.a. real, igual que arriba

    def nominal_sube_parejo(base):
        return {ym: base * (1.1 if ym == "2026-08" else 1.0) for ym in ipc}

    iva_nom = nominal_sube_parejo(1000.0)
    cheque_nom = nominal_sube_parejo(500.0)

    control = macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08")
    assert control["agregado_var_ia_real"] == 10.0
    assert control["iva_var_ia_real"] == 10.0
    assert control["cheque_var_ia_real"] == 10.0
    assert control["diverge"] is False


def test_control_tributario_es_none_sin_mes_comun():
    assert macro._control_tributario({}, {}, {}, {}, "2026-08") is None


def test_control_tributario_tope_de_retroceso():
    """El bug real: `comunes[-1]` podía retroceder sin límite si IVA o cheque
    quedaban rezagados varios meses respecto de la card, y nada lo marcaba. Acá
    IVA/cheque sólo tienen datos hasta 2026-04 pero la card (`ultimo`) ya está
    en 2026-08, cinco meses después — más allá del tope, así que no hay
    descomposición ese mes en vez de publicar un dato viejo sin avisar."""
    ipc = {f"2025-{m:02d}": 100.0 for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 for m in range(1, 9)})
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 99.0 for m in range(1, 9)})

    def nominal_hasta_abril(base):
        return {ym: base for ym in list(ipc)[:16]}  # sólo hasta 2026-04

    iva_nom = nominal_hasta_abril(1000.0)
    cheque_nom = nominal_hasta_abril(500.0)

    assert macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08") is None


def test_control_tributario_marca_el_desfasaje_dentro_del_tope():
    """Un mes de rezago (dentro del tope) sí publica, pero declarando cuántos
    meses de atraso tiene respecto de la card — la ficha no puede seguir
    afirmando que un rezago deja el control «ausente»: queda presente y viejo."""
    ipc = {f"2025-{m:02d}": 100.0 for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 for m in range(1, 9)})
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 99.0 for m in range(1, 9)})

    def nominal_hasta_julio(base):
        return {ym: base for ym in list(ipc)[:19]}  # hasta 2026-07, la card es 2026-08

    iva_nom = nominal_hasta_julio(1000.0)
    cheque_nom = nominal_hasta_julio(500.0)

    control = macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08")
    assert control is not None
    assert control["fecha"] == "2026-07"
    assert control["meses_atraso"] == 1


def test_control_tributario_banda_muerta_en_cero():
    """El cero no puede marcar divergencia. Tres casos: exactamente cero con
    todo el mismo signo (no debe divergir, ya lo cubre el test de arriba); acá
    el caso trampa: un agregado que redondea a 0,0% con un IVA que también
    redondea a 0,0% pero de signo crudo contrario no puede publicar "van en
    sentidos distintos" con dos números que se muestran como el mismo cero."""
    ipc = {f"2025-{m:02d}": 100.0 for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 for m in range(1, 9)})
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 90.036 for m in range(1, 9)})  # +0.04% i.a.

    def nominal(base, delta_pct):
        return {ym: base * (1 + delta_pct / 100.0 if ym == "2026-08" else 1.0)
                for ym in ipc}

    iva_nom = nominal(1000.0, -0.04)   # -0,04% i.a. real → redondea a -0,0%
    cheque_nom = nominal(500.0, 0.0)

    control = macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08")
    assert control["agregado_var_ia_real"] == 0.0
    assert control["iva_var_ia_real"] == -0.0 or control["iva_var_ia_real"] == 0.0
    assert control["diverge"] is False, (
        "un agregado y un IVA que se publican los dos como 0,0% no pueden "
        "declararse en sentidos distintos")


def test_control_tributario_no_diverge_en_borde_de_banda():
    """Fuera de la banda muerta (0,1% ya no redondea a cero), la divergencia
    real sigue detectándose — control negativo del test anterior, para que la
    banda muerta no termine tapando toda divergencia chica."""
    ipc = {f"2025-{m:02d}": 100.0 for m in range(1, 13)}
    ipc.update({f"2026-{m:02d}": 100.0 for m in range(1, 9)})
    serie_sa = {f"2025-{m:02d}": 90.0 for m in range(1, 13)}
    serie_sa.update({f"2026-{m:02d}": 90.09 for m in range(1, 9)})  # +0.1% i.a.

    def nominal(base, delta_pct):
        return {ym: base * (1 + delta_pct / 100.0 if ym == "2026-08" else 1.0)
                for ym in ipc}

    iva_nom = nominal(1000.0, -0.1)
    cheque_nom = nominal(500.0, -0.1)

    control = macro._control_tributario(serie_sa, iva_nom, cheque_nom, ipc, "2026-08")
    assert control["agregado_var_ia_real"] == 0.1
    assert control["iva_var_ia_real"] == -0.1
    assert control["diverge"] is True


def test_la_serie_y_la_card_comparten_la_constante():
    """Si la serie fijara el id a mano, cambiar la card dejaría el gráfico del
    modal midiendo otra magnitud que el titular — el defecto que persigue
    test_puntaje_unico_camino."""
    import descargar_series as ds
    fuente = Path(ds.__file__).read_text(encoding="utf-8")
    inicio = fuente.index("def fetch_recaudacion_real_serie")
    cuerpo = fuente[inicio:inicio + 900]
    assert "macro.INDEC_RECAUDACION_ID" in cuerpo, cuerpo[:400]
