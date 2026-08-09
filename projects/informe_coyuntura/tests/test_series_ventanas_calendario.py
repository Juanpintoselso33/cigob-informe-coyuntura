"""Las ventanas móviles se arman por CALENDARIO, no por posición en la lista.

Bug encontrado por auditoría de código (18-jul-2026): varios derivados
dividían o promediaban posiciones adyacentes de la lista ordenada. Con la serie
completa da el mismo resultado, pero si la fuente saltea un mes —o si se acota
la ventana descargada— el cociente entre observaciones separadas por dos meses
se publicaba como variación mensual, y el promedio de "tres meses" abarcaba
cuatro o más. Silencioso: no rompe nada, devuelve un número sutilmente mal.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import descargar_series
import macro


# ── Aritmética de meses ─────────────────────────────────────────────────────

def test_mes_previo_cruza_el_cambio_de_anio():
    assert descargar_series._mes_previo("2026-03") == "2026-02"
    assert descargar_series._mes_previo("2026-01") == "2025-12"
    assert descargar_series._mes_previo("2026-01", 2) == "2025-11"
    assert descargar_series._mes_previo("2026-02", 14) == "2024-12"


# ── Variación mensual ───────────────────────────────────────────────────────

def test_la_variacion_mensual_omite_los_meses_con_hueco():
    """Si falta febrero, marzo NO se emite: publicar (marzo/enero − 1) como
    variación mensual sobreestimaría la inflación de ese mes."""
    niveles = {"2025-12": 100.0, "2026-01": 102.0, "2026-03": 108.0}
    var = descargar_series._var_mensual(niveles)
    assert set(var) == {"2026-01"}, var
    assert var["2026-01"] == 2.0


def test_la_variacion_mensual_es_correcta_sin_huecos():
    niveles = {"2026-01": 100.0, "2026-02": 103.0, "2026-03": 106.09}
    var = descargar_series._var_mensual(niveles)
    assert var == {"2026-02": 3.0, "2026-03": 3.0}, var


def test_un_nivel_en_cero_no_rompe_la_division():
    niveles = {"2026-01": 0.0, "2026-02": 100.0}
    assert descargar_series._var_mensual(niveles) == {}


# ── Promedio móvil del IPI ──────────────────────────────────────────────────

def test_el_promedio_movil_del_ipi_exige_ventana_completa(monkeypatch):
    """Dos cosas a la vez: con un mes faltante no se emite el promedio, y los
    primeros meses de la serie —que no tienen tres meses detrás— tampoco. La
    versión anterior promediaba sobre ventanas parciales dividiendo por el
    largo parcial, sin ninguna marca que lo señalara."""
    # niveles tales que la i.a. exista para 2025-01..2025-06, salteando 2025-04
    niveles = {}
    for mes in range(1, 13):
        niveles[f"2024-{mes:02d}"] = 100.0
    for mes in (1, 2, 3, 5, 6):
        niveles[f"2025-{mes:02d}"] = 110.0

    monkeypatch.setattr(macro, "_indec_serie",
                        lambda *a, **k: [[f"{ym}-01", v] for ym, v in sorted(niveles.items())])
    s = macro._ipi_ia_por_mes()

    assert "2025-01" not in s, "el primer mes no tiene tres meses detrás"
    assert "2025-02" not in s, "el segundo mes tampoco"
    assert "2025-03" in s, "con tres meses completos sí debe emitirse"
    assert "2025-05" not in s, "falta 2025-04: la ventana está incompleta"
    assert "2025-06" not in s, "2025-04 sigue dentro de la ventana de junio"


def test_el_ipi_ia_no_deja_huecos_de_calendario():
    """Reemplaza a un test que fijaba un valor puntual (-1.07) y quedó rojo en
    `main` sin que nadie tocara `macro.py`. Estaba mal planteado por dos
    razones independientes, no por una sola:

    1. Indexaba con `max(...)`: el mes más nuevo. Cada vez que el INDEC
       publica un mes nuevo la aserción pasa a hablar de un mes distinto; el
       18-jul-2026 el máximo era 2026-05, hoy es 2026-06.
    2. Aunque se fijara un mes en vez del máximo, el INDEC revisa los niveles
       ya publicados: 2026-05 valía -1.07 cuando se escribió el test y hoy,
       sobre la misma serie real, vale -0.98 sin que el código haya cambiado.
       Verificado recorriendo los 112 meses de la serie vigente: ningún mes
       vale ya -1.07.

    Fijar un número contra una fuente que se revisa está roto por diseño, no
    por bug: no hay valor que se pueda dejar escrito y seguir siendo cierto
    mañana. Lo que hay que proteger es el invariante del refactor —ventanas
    por CALENDARIO, no por posición—, y eso sí sobrevive a que la fuente
    agregue meses o revise historia: la serie emitida no puede tener saltos de
    mes. `test_el_promedio_movil_del_ipi_exige_ventana_completa` ya prueba,
    con datos sintéticos, que un hueco real se excluye; este test corre lo
    mismo contra la fuente real para agarrar un problema que uno sintético no
    puede: que la aritmética de calendario (cruce de año, formato de fecha del
    INDEC, etc.) se rompa con datos reales aunque el caso sintético pase."""
    s = macro._ipi_ia_por_mes()
    meses = sorted(s)
    assert len(meses) > 12, "la serie real tiene que traer más de un año de datos"
    for anterior, siguiente in zip(meses, meses[1:]):
        assert descargar_series._mes_previo(siguiente) == anterior, (
            f"hueco de calendario entre {anterior} y {siguiente}: la serie "
            "real no tiene huecos, así que uno acá sería un bug de armado de "
            "ventanas, no un hueco de la fuente"
        )


# ── Cuenta corriente como acompañante del saldo comercial (ADR-0080) ────────

def test_la_cuenta_corriente_acumula_cuatro_trimestres():
    """Se acumula a 4 trimestres para ser comparable con el saldo comercial de
    12 meses. Contra un trimestre suelto el contraste mezclaría escalas."""
    serie = descargar_series.fetch_cuenta_corriente_serie()
    assert len(serie) >= 8, len(serie)
    fechas = [f for f, _ in serie]
    assert fechas == sorted(fechas)
    assert all(f.endswith("-01") for f in fechas)
    # trimestral: los meses van de 3 en 3
    meses = [int(f[5:7]) for f in fechas]
    assert set(meses) <= {1, 4, 7, 10}, meses


def test_la_cuenta_corriente_no_puntua():
    """Es contexto: no tiene bandas ni entra a ninguna dimensión del ITCM."""
    import itcm
    assert "cuenta_corriente" not in itcm.BANDAS_ITCM
    del_indice = {i for d in itcm.DIMENSIONES_ITCM.values() for i in d["indicadores"]}
    assert "cuenta_corriente" not in del_indice
