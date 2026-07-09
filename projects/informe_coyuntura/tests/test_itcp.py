import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcp


def test_banda_votometro_extremos():
    # (15,inf,100)·(5,15,85)·(-5,5,65)·(-15,-5,40)·(-inf,-15,10)
    # Convención low exclusivo/high inclusivo (parametrica.puntaje_banda): en
    # el límite compartido 15.0 el punto cae en la banda que lo incluye por
    # high inclusivo (5,15,85], NO en la banda que lo excluye por low
    # exclusivo (15,inf) — mismo criterio que itcg pinea (ver test_itcg.py,
    # p.ej. protocolo_antipiquetes en 75.01 y no en 75.0 exacto).
    assert itcp.puntaje_banda(20.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 100
    assert itcp.puntaje_banda(15.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 85
    assert itcp.puntaje_banda(14.9, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 85
    assert itcp.puntaje_banda(-20.0, itcp.BANDAS_ITCP["votometro_ventaja_lla"]) == 10


def test_banda_low_exclusivo_high_inclusivo():
    bandas = itcp.BANDAS_ITCP["ratio_dnu"]  # (-inf,0.3,100)·(0.3,0.7,85)·...
    assert itcp.puntaje_banda(0.3, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(0.30001, bandas) == 85  # low exclusivo del siguiente tramo


def test_banda_protestas_caba_var_vs_2023():
    # (-inf,-30,100)·(-30,-10,85)·(-10,10,65)·(10,30,40)·(30,inf,10)
    # Cross-fix (post Task 1): esta tabla puntúa sobre "var_vs_2023" (% de
    # variación de eventos ACLED en CABA contra la base 2023), NO sobre el
    # conteo crudo de eventos ("valor") — la tabla original (heredada de
    # movilizacion_cepa, pensada para una escala 0-100) habría interpretado
    # mal un conteo crudo que puede estar en cientos. Menor variación (menos
    # protesta que en 2023) = mejor = puntaje alto: tabla invertida respecto
    # de iaf_transferencias aunque comparta la misma escala %-variación.
    bandas = itcp.BANDAS_ITCP["protestas_caba"]
    assert itcp.puntaje_banda(-50.0, bandas) == 100
    assert itcp.puntaje_banda(-30.0, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(-29.99, bandas) == 85   # low exclusivo del siguiente tramo
    assert itcp.puntaje_banda(0.0, bandas) == 65
    assert itcp.puntaje_banda(30.0, bandas) == 40
    assert itcp.puntaje_banda(30.01, bandas) == 10


def test_bandas_itcp_tiene_alineamiento_senadores_prov_no_gobernadores_alineamiento():
    assert "alineamiento_senadores_prov" in itcp.BANDAS_ITCP
    dim = itcp.DIMENSIONES_ITCP["alianzas_territoriales"]
    assert "alineamiento_senadores_prov" in dim["indicadores"]
    assert "gobernadores_alineamiento" not in dim["indicadores"]


def test_banda_alineamiento_senadores_prov_recalibrada():
    # Recalibración 2026-07-09 (ADR-0038) con 29 puntos mensuales reales
    # backfilleados: anclas 70/60/50/40 (antes 65/45/25/10, heredadas sin
    # validar de gobernadores_alineamiento).
    bandas = itcp.BANDAS_ITCP["alineamiento_senadores_prov"]
    assert itcp.puntaje_banda(70.0, bandas) == 85    # low exclusivo del tramo abierto
    assert itcp.puntaje_banda(70.01, bandas) == 100
    assert itcp.puntaje_banda(60.0, bandas) == 65    # high inclusivo
    assert itcp.puntaje_banda(50.0, bandas) == 40
    assert itcp.puntaje_banda(40.0, bandas) == 10
    assert itcp.puntaje_banda(19.4, bandas) == 10    # mínimo real observado (ago-2025)


def test_banda_alineamiento_senadores_prov_ya_no_satura_el_valor_live_actual():
    # El hallazgo que motivó la recalibración: bajo las anclas viejas
    # (65,inf,100), el valor live de la card (68.3%) saturaba en puntaje
    # interpolado 100.0 -- una tensión de 0.0/10 pese a no ser el máximo
    # observado en la serie real (que llega a 100.0 en feb-2024). Con las
    # anclas nuevas, 68.3 queda ENTRE el ancla de (65, 85) y (70, 100) --
    # ya no se aplana en el techo.
    import parametrica
    bandas = itcp.BANDAS_ITCP["alineamiento_senadores_prov"]
    puntaje = parametrica.puntaje_interpolado(68.3, bandas)
    assert puntaje < 100.0
    assert puntaje == 94.9


def test_banda_cohesion_bloque_senado_recalibrada():
    # Recalibración 2026-07-09 (ADR-0039) con 29 puntos mensuales reales
    # backfilleados: anclas 95/90/85/80 (antes 90/75/60/40, copiadas sin
    # validar de cohesion_bloque Diputados, que no tiene datos propios).
    bandas = itcp.BANDAS_ITCP["cohesion_bloque_senado"]
    assert itcp.puntaje_banda(95.0, bandas) == 85    # low exclusivo del tramo abierto
    assert itcp.puntaje_banda(95.01, bandas) == 100
    assert itcp.puntaje_banda(90.0, bandas) == 65    # high inclusivo
    assert itcp.puntaje_banda(85.0, bandas) == 40
    assert itcp.puntaje_banda(80.0, bandas) == 10
    assert itcp.puntaje_banda(77.8, bandas) == 10    # mínimo real observado (ago-2025)


def test_banda_cohesion_bloque_senado_ya_no_satura_valores_antes_planos():
    # Bajo las anclas viejas (90,inf,100), cualquier valor >90 saturaba en
    # 100 -- 25 de 29 meses reales caían ahí. Un valor real de esa franja
    # (sep-2024, 92.8%) ya no se aplana en el techo con las anclas nuevas.
    import parametrica
    bandas = itcp.BANDAS_ITCP["cohesion_bloque_senado"]
    puntaje = parametrica.puntaje_interpolado(92.8, bandas)
    assert puntaje < 100.0
    assert puntaje == 86.8


def test_banda_cohesion_bloque_diputados_recalibrada():
    # Recalibración 2026-07-09 (ADR-0042) con 31 puntos mensuales reales
    # backfilleados (dic-2023->jun-2026): anclas 99,9/99,0/98,0/97,0 (antes
    # 90/75/60/40, fórmula ad hoc nunca validada).
    bandas = itcp.BANDAS_ITCP["cohesion_bloque"]
    assert itcp.puntaje_banda(99.9, bandas) == 85     # low exclusivo del tramo abierto
    assert itcp.puntaje_banda(99.91, bandas) == 100
    assert itcp.puntaje_banda(99.0, bandas) == 65     # high inclusivo
    assert itcp.puntaje_banda(98.0, bandas) == 40
    assert itcp.puntaje_banda(97.0, bandas) == 10
    assert itcp.puntaje_banda(96.7, bandas) == 10     # mínimo real observado (dic-2023)


def test_banda_cohesion_bloque_diputados_ya_no_satura_valores_antes_planos():
    # Bajo las anclas viejas (90,inf,100), CUALQUIER valor real observado
    # (96,7-100,0) saturaba en 100 -- 31 de 31 meses, sin excepción. Un valor
    # real de esa franja (ago-2025, 97.5%) ya no se aplana en el techo.
    import parametrica
    bandas = itcp.BANDAS_ITCP["cohesion_bloque"]
    puntaje = parametrica.puntaje_interpolado(97.5, bandas)
    assert puntaje < 100.0


def test_calcular_itcp_pondera_dimensiones():
    valores = {
        "votometro_ventaja_lla": 15.0,       # imagen_voto, puntaje 100
        "ratio_dnu": 0.2,                    # poder_legislativo, puntaje 100
        "eficacia_legislativa": 60.0,        # poder_legislativo, puntaje 100
        "veto_quorum": 2.0,                  # poder_legislativo, puntaje 100
        "comisiones_caidas": 10.0,           # poder_legislativo, puntaje 100
        "iaf_transferencias": 12.0,          # alianzas_territoriales, puntaje 100
        "alineamiento_senadores_prov": 70.0, # alianzas_territoriales, puntaje 100
        "adhesion_reformas_provincial": 90.0, # alianzas_territoriales, puntaje 100
        "cohesion_bloque": 100.0,            # cohesion_interna, puntaje 100
        "cohesion_bloque_senado": 95.0,      # cohesion_interna, puntaje 100
        "movilizacion_cepa": 5.0,            # conflicto_social, puntaje 100
        "protestas_caba": -35.0,             # conflicto_social, puntaje 100 (var_vs_2023, no valor crudo)
    }
    resultado = itcp.calcular_itcp(valores)
    assert resultado is not None
    assert resultado["valor"] == 100.0
    assert resultado["banda"] == "aflojado"


def test_calcular_itcp_renormaliza_ante_faltantes():
    # Solo imagen_voto disponible -> esa dimensión sola determina el índice
    resultado = itcp.calcular_itcp({"votometro_ventaja_lla": 15.0})
    assert resultado is not None
    assert resultado["valor"] == 100.0


def test_calcular_itcp_sin_datos_devuelve_none():
    assert itcp.calcular_itcp({}) is None


def test_calcular_itcp_aplica_ajustes_con_vencimiento(tmp_path):
    ajustes_path = tmp_path / "ajustes_itcp.json"
    ajustes_path.write_text(
        '{"cohesion_bloque": {"puntaje": 50, "justificacion": "test", "vigente_hasta": "2099-12"}}',
        encoding="utf-8",
    )
    ajustes = itcp.cargar_ajustes(ajustes_path, "2026-07")
    resultado = itcp.calcular_itcp({"cohesion_bloque": 95.0}, ajustes)
    assert resultado["dimensiones"]["cohesion_interna"]["indicadores"]["cohesion_bloque"]["puntaje_aplicado"] == 50
