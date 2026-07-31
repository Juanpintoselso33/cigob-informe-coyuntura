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
    # (-inf,-6,100)·(-6,-3,85)·(-3,0,65)·(0,10,40)·(10,inf,10)
    # Cross-fix (post Task 1): esta tabla puntúa sobre "var_vs_2023" (% de
    # variación de eventos ACLED en CABA contra la base 2023), NO sobre el
    # conteo crudo de eventos ("valor") — la tabla original (heredada de
    # movilizacion_cepa, pensada para una escala 0-100) habría interpretado
    # mal un conteo crudo que puede estar en cientos. Menor variación (menos
    # protesta que en 2023) = mejor = puntaje alto: tabla invertida respecto
    # de iaf_transferencias aunque comparta la misma escala %-variación.
    # Anclas recalibradas 2026-07-09 con la serie ACLED ya existente (antes
    # -30/-10/10/30, simétricas y nunca validadas -- ver comentario en
    # BANDAS_ITCP).
    bandas = itcp.BANDAS_ITCP["protestas_caba"]
    assert itcp.puntaje_banda(-50.0, bandas) == 100
    assert itcp.puntaje_banda(-6.0, bandas) == 100    # high inclusivo
    assert itcp.puntaje_banda(-5.99, bandas) == 85    # low exclusivo del siguiente tramo
    assert itcp.puntaje_banda(0.0, bandas) == 65
    assert itcp.puntaje_banda(10.0, bandas) == 40
    assert itcp.puntaje_banda(10.01, bandas) == 10


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


def test_banda_cohesion_bloque_compuesta_recalibrada():
    # ADR-0048 (2026-07-10): cohesion_bloque pasa a ser el COMPUESTO
    # bicameral 65/35 y sus anclas se recalibran contra la serie compuesta
    # reconstruida (31 puntos, dic-2023->jun-2026, rango 90,3-100,0):
    # 99,9/99,0/97,0/95,0 -- distribución 8/4/9/7/3 por banda, las cinco
    # con datos reales. Las anclas anteriores (99,9/99,0/98,0/97,0,
    # ADR-0042) estaban calibradas para Diputados sola.
    bandas = itcp.BANDAS_ITCP["cohesion_bloque"]
    assert itcp.puntaje_banda(99.9, bandas) == 85     # low exclusivo del tramo abierto
    assert itcp.puntaje_banda(99.91, bandas) == 100
    assert itcp.puntaje_banda(99.0, bandas) == 65     # high inclusivo
    assert itcp.puntaje_banda(97.0, bandas) == 40
    assert itcp.puntaje_banda(95.0, bandas) == 10
    assert itcp.puntaje_banda(90.3, bandas) == 10     # mínimo real observado (ago-2025)


def test_banda_cohesion_bloque_compuesta_discrimina_la_serie_real():
    # Valores reales de la serie compuesta que con las anclas de Diputados
    # sola caían casi todos en el piso (menores a 97): con las anclas del
    # compuesto recorren el cuerpo de la escala sin aplanarse.
    import parametrica
    bandas = itcp.BANDAS_ITCP["cohesion_bloque"]
    assert parametrica.puntaje_interpolado(99.7, bandas) < 100.0   # valor live 10-jul-2026
    assert parametrica.puntaje_interpolado(99.7, bandas) > 85.0
    assert 40.0 < parametrica.puntaje_interpolado(97.4, bandas) < 85.0   # mediana real
    assert parametrica.puntaje_interpolado(92.7, bandas) < 40.0   # sep-2025 real
    assert parametrica.puntaje_interpolado(90.3, bandas) == 10.0  # mínimo real


def test_banda_comisiones_caidas_recalibrada():
    # Recalibración 2026-07-09 (ADR-0045, auditoría adversarial) con 32
    # puntos mensuales reales (rango 94,7-99,8): las anclas 30/50/70/85
    # del doc de diseño dejaban los 32 meses en la banda del piso (10) --
    # tensión máxima clavada, cero discriminación.
    bandas = itcp.BANDAS_ITCP["comisiones_caidas"]
    assert itcp.puntaje_banda(96.0, bandas) == 100    # high inclusivo del tramo abierto
    assert itcp.puntaje_banda(96.01, bandas) == 85
    assert itcp.puntaje_banda(97.0, bandas) == 85
    assert itcp.puntaje_banda(98.0, bandas) == 65
    assert itcp.puntaje_banda(99.0, bandas) == 40
    assert itcp.puntaje_banda(99.8, bandas) == 10     # máximo real observado
    import parametrica
    assert parametrica.puntaje_interpolado(97.7, bandas) < 100.0  # valor real de hoy, ya no aplana en 10
    assert parametrica.puntaje_interpolado(97.7, bandas) > 10.0


def test_banda_derrotas_legislativas():
    # NUEVO 2026-07-09 (ADR-0046): conteo absoluto 12m de derrotas
    # legislativas consumadas (vetos insistidos + decretos rechazados bajo la
    # ley 26.122), menor = mejor. Anclas 1/3/8/14 calibradas contra la serie
    # reconstruida real de 32 meses (valores observados {0,1,2,5,6,8}; las
    # dos bandas inferiores quedan vacías a propósito como margen).
    bandas = itcp.BANDAS_ITCP["derrotas_legislativas"]
    assert itcp.puntaje_banda(0.0, bandas) == 100
    assert itcp.puntaje_banda(1.0, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(1.01, bandas) == 85   # low exclusivo del siguiente tramo
    assert itcp.puntaje_banda(3.0, bandas) == 85
    assert itcp.puntaje_banda(8.0, bandas) == 65    # pico real observado (oct-2025→)
    assert itcp.puntaje_banda(8.01, bandas) == 40
    assert itcp.puntaje_banda(14.0, bandas) == 40
    assert itcp.puntaje_banda(14.01, bandas) == 10


def test_banda_derrotas_legislativas_interpolada_discrimina_la_serie_real():
    # puntajes interpolados de los valores realmente observados en los 32
    # meses reconstruidos: el indicador varía de verdad (no nace saturado)
    import parametrica
    bandas = itcp.BANDAS_ITCP["derrotas_legislativas"]
    assert parametrica.puntaje_interpolado(0.0, bandas) == 100.0
    assert parametrica.puntaje_interpolado(2.0, bandas) == 85.0
    assert parametrica.puntaje_interpolado(5.0, bandas) == 67.9
    assert parametrica.puntaje_interpolado(6.0, bandas) == 62.7
    assert parametrica.puntaje_interpolado(8.0, bandas) == 53.6   # valor vigente jul-2026


def test_pesos_internos_poder_legislativo_con_bloqueo():
    # Redistribución 2026-07-16 (ADR-0069): entra bloqueo_sostenido con 0.20
    # (cada uno de los 4 previos cede 0.05, orden relativo conservado).
    # Antes 25/30/20/25 (ADR-0064, salida de comisiones_caidas); antes de
    # eso 20/25/15/20/20 (ADR-0046).
    # 2026-07-19 (ADR-0089): derrotas_legislativas sale del índice —medía casi
    # exactamente lo mismo que bloqueo_sostenido (r=-0,984; desde mar-2025, el
    # mismo número mes a mes)— y entra desafios_legislativos. El par acoplado
    # baja de 0.40 a 0.30 combinado; el peso liberado va a eficacia y ratio_dnu,
    # NO a veto_quorum.
    # 2026-07-31 (ADR-0168): entra produccion_legislativa con 0.15 y los cinco
    # existentes ceden proporcionalmente (×0.85). El orden relativo se conserva:
    # eficacia sigue primera, ratio_dnu segunda, los tres restantes parejos.
    dim = itcp.DIMENSIONES_ITCP["poder_legislativo"]
    assert dim["indicadores"] == {
        "ratio_dnu": 0.20, "eficacia_legislativa": 0.27, "veto_quorum": 0.13,
        "desafios_legislativos": 0.13, "bloqueo_sostenido": 0.12,
        "produccion_legislativa": 0.15,
    }
    acoplados = dim["indicadores"]["desafios_legislativos"] + dim["indicadores"]["bloqueo_sostenido"]
    assert acoplados <= 0.30, "el par acoplado no debería recuperar peso sin revisar ADR-0089"
    assert dim["indicadores"]["eficacia_legislativa"] > dim["indicadores"]["ratio_dnu"], (
        "eficacia tiene que seguir primera: es la medida más abarcativa (ADR-0061)")
    assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9


def test_banda_bloqueo_sostenido():
    # (90,inf,100)·(75,90,85)·(50,75,60)·(25,50,35)·(-inf,25,10) — % de
    # normas desafiadas en pie, 12m, mayor = mejor (ADR-0069). Anclas con
    # referencia externa: ninguna insistencia exitosa 2003-2025 (~100%
    # histórico de sostenimiento).
    bandas = itcp.BANDAS_ITCP["bloqueo_sostenido"]
    assert itcp.puntaje_banda(100.0, bandas) == 100
    assert itcp.puntaje_banda(75.0, bandas) == 60    # high inclusivo de (50,75]
    assert itcp.puntaje_banda(80.0, bandas) == 85
    assert itcp.puntaje_banda(54.5, bandas) == 60    # ago-2025 real
    assert itcp.puntaje_banda(33.3, bandas) == 35    # oct-2025 real
    assert itcp.puntaje_banda(20.0, bandas) == 10    # jul-2026 real (card)
def test_banda_rotacion_gabinete():
    # (-inf,1,100)·(1,2,85)·(2,4,65)·(4,6,40)·(6,inf,10) — salidas de rango
    # ministerial acumuladas 12m, menor = mejor (ADR-0047). Anclas calibradas
    # contra la serie real completa de 32 meses (rango 0-7, las 5 bandas con
    # datos: 7/8/9/6/2).
    bandas = itcp.BANDAS_ITCP["rotacion_gabinete"]
    assert itcp.puntaje_banda(0, bandas) == 100
    assert itcp.puntaje_banda(1.0, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(2.0, bandas) == 85
    assert itcp.puntaje_banda(3.0, bandas) == 65
    assert itcp.puntaje_banda(4.0, bandas) == 65    # high inclusivo
    assert itcp.puntaje_banda(5.0, bandas) == 40
    assert itcp.puntaje_banda(6.0, bandas) == 40    # high inclusivo
    assert itcp.puntaje_banda(7, bandas) == 10      # máximo real observado (jun-2026)


def test_banda_rotacion_gabinete_interpolado_discrimina():
    # Puntaje interpolado (motor ADR-0021, anclas 1→100 · 1,5→85 · 3→65 ·
    # 5→40 · 6→10): los valores reales de la serie recorren 10-100 sin
    # aplanarse en el cuerpo — el indicador nace discriminando.
    import parametrica
    bandas = itcp.BANDAS_ITCP["rotacion_gabinete"]
    assert parametrica.puntaje_interpolado(0, bandas) == 100.0
    assert parametrica.puntaje_interpolado(2, bandas) == 78.3   # 2024-05..08 reales
    assert parametrica.puntaje_interpolado(4, bandas) == 52.5   # pico 2024
    assert parametrica.puntaje_interpolado(5, bandas) == 40.0   # dic-2025 (crisis)
    assert parametrica.puntaje_interpolado(7, bandas) == 10.0   # jun-2026 (máximo)


def test_dimension_cohesion_interna_es_solo_el_compuesto():
    # ADR-0048 (revisión editorial 2026-07-10): la dimensión queda en el
    # compuesto bicameral solo; rotacion_gabinete sale a contexto y
    # cohesion_bloque_senado se fusiona adentro del compuesto. Los pesos
    # ENTRE dimensiones (ADR-0036) no se tocan.
    dim = itcp.DIMENSIONES_ITCP["cohesion_interna"]
    assert dim["indicadores"] == {"cohesion_bloque": 1.0}
    assert dim["peso"] == 0.15   # 0.20 → 0.18 (ADR-0088) → 0.15 (ADR-0126)


def test_dimension_conflicto_social_sin_protestas():
    # ADR-0048: protestas_caba salió a contexto. ADR-0052: movilizacion_cepa
    # también (sin backfill posible + acumulado YTD no comparable) —
    # conflictividad_nacional (ACLED país entero) queda sola en la dimensión.
    dim = itcp.DIMENSIONES_ITCP["conflicto_social"]
    assert dim["indicadores"] == {"conflictividad_nacional": 1.0}
    assert dim["peso"] == 0.10   # 0.15 → 0.12 (ADR-0088) → 0.10 (ADR-0126)


def test_indicadores_contexto_declarados_y_fuera_de_las_dimensiones():
    # ADR-0048/0052: seguimiento interno sin puntuar; sus bandas quedan como
    # referencia histórica en BANDAS_ITCP, así que el override de contexto es
    # lo único que los mantiene fuera del en_indice de la card (patrón macro).
    assert set(itcp.INDICADORES_CONTEXTO) == {"rotacion_gabinete", "protestas_caba", "comisiones_caidas",
                                              "movilizacion_cepa", "derrotas_legislativas"}
    en_dimensiones = {k for d in itcp.DIMENSIONES_ITCP.values() for k in d["indicadores"]}
    for contexto in itcp.INDICADORES_CONTEXTO:
        assert contexto not in en_dimensiones
        assert contexto in itcp.BANDAS_ITCP   # referencia histórica, no se borra
    assert "cohesion_bloque_senado" not in en_dimensiones   # fusionado, no contexto


def test_banda_conflictividad_nacional():
    # (-inf,-32,100)·(-32,-29,85)·(-29,-26,65)·(-26,-15,40)·(-15,inf,10) —
    # % var. eventos Protests+Riots país entero vs total 2023, menor = mejor
    # (ADR-0052). Anclas calibradas contra la serie real de 30 puntos
    # (dic-2023→may-2026, rango −34,2 a +2,7): 5/7/8/4/6 por banda, las
    # cinco pobladas, cada corte en un hueco real de los datos.
    bandas = itcp.BANDAS_ITCP["conflictividad_nacional"]
    assert itcp.puntaje_banda(-34.2, bandas) == 100   # mínimo real (nov-2025)
    assert itcp.puntaje_banda(-32.0, bandas) == 100   # high inclusivo
    assert itcp.puntaje_banda(-30.0, bandas) == 85
    assert itcp.puntaje_banda(-29.0, bandas) == 85    # high inclusivo
    assert itcp.puntaje_banda(-27.7, bandas) == 65    # mediana real
    assert itcp.puntaje_banda(-21.4, bandas) == 40    # valor vigente (may-2026)
    assert itcp.puntaje_banda(0.0, bandas) == 10      # dic-2023 (= base)
    assert itcp.puntaje_banda(2.7, bandas) == 10      # máximo real (ene-2024)


def test_pesos_itcp_suman_uno_en_cada_dimension():
    for dkey, dim in itcp.DIMENSIONES_ITCP.items():
        assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9, dkey
    assert abs(sum(d["peso"] for d in itcp.DIMENSIONES_ITCP.values()) - 1.0) < 1e-9


def test_calcular_itcp_pondera_dimensiones():
    valores = {
        "votometro_ventaja_lla": 15.0,       # imagen_voto, puntaje 100
        "ratio_dnu": 0.2,                    # poder_legislativo, puntaje 100
        "eficacia_legislativa": 60.0,        # poder_legislativo, puntaje 100
        "veto_quorum": 2.0,                  # poder_legislativo, puntaje 100
        "derrotas_legislativas": 0.0,        # poder_legislativo, puntaje 100
        "iaf_transferencias": 12.0,          # alianzas_territoriales, puntaje 100
        "alineamiento_senadores_prov": 70.0, # alianzas_territoriales, puntaje 100
        "adhesion_reformas_provincial": 90.0, # alianzas_territoriales, puntaje 100
        "cohesion_bloque": 100.0,            # cohesion_interna, puntaje 100 (compuesto bicameral)
        "conflictividad_nacional": -40.0,    # conflicto_social, puntaje 100 (ADR-0052)
        # rotacion_gabinete / protestas_caba (ADR-0048) / movilizacion_cepa
        # (ADR-0052) / comisiones_caidas (ADR-0064): contexto — aunque
        # lleguen en `valores`, el motor los ignora al no estar en dimensiones
        "rotacion_gabinete": 7.0,
        "protestas_caba": 25.0,
        "movilizacion_cepa": 95.0,
        "comisiones_caidas": 10.0,
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


def test_todo_indicador_del_indice_declara_su_rezago():
    """La card de rezago pondera por peso efectivo (ADR-0092): un indicador sin
    rezago declarado no rompe nada, simplemente desaparece del promedio y lo
    sesga en silencio. Si entra uno nuevo, este test obliga a declararlo."""
    en_indice = {k for d in itcp.DIMENSIONES_ITCP.values() for k in d["indicadores"]}
    faltan = en_indice - set(itcp.REZAGO_MESES_ITCP)
    assert not faltan, f"sin rezago declarado en REZAGO_MESES_ITCP: {sorted(faltan)}"
    sobran = set(itcp.REZAGO_MESES_ITCP) - en_indice
    assert not sobran, f"declaran rezago pero no integran el índice: {sorted(sobran)}"
    assert all(v >= 0 for v in itcp.REZAGO_MESES_ITCP.values())


def test_todo_indicador_del_indice_declara_su_familia():
    """La card de lectura por partes (ADR-0094) reconstruye el índice sumando
    las tres familias. Un indicador sin familia declarada no rompe nada: se
    cae de la descomposición y las tres familias dejan de sumar el total."""
    en_indice = {k for d in itcp.DIMENSIONES_ITCP.values() for k in d["indicadores"]}
    faltan = en_indice - set(itcp.FAMILIAS_ITCP)
    assert not faltan, f"sin familia declarada en FAMILIAS_ITCP: {sorted(faltan)}"
    sobran = set(itcp.FAMILIAS_ITCP) - en_indice
    assert not sobran, f"declaran familia pero no integran el índice: {sorted(sobran)}"
    assert set(itcp.FAMILIAS_ITCP.values()) <= set(itcp.FAMILIAS_ITCP_META)
    # las tres familias tienen que existir: si una queda vacía, la lectura por
    # partes deja de responder la pregunta que la motivó
    assert set(itcp.FAMILIAS_ITCP.values()) == {"tension", "capacidad", "recursos"}
