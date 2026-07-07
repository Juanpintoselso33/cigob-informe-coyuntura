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


def test_calcular_itcp_pondera_dimensiones():
    valores = {
        "votometro_ventaja_lla": 15.0,       # imagen_voto, puntaje 100
        "ratio_dnu": 0.2,                    # poder_legislativo, puntaje 100
        "eficacia_legislativa": 60.0,        # poder_legislativo, puntaje 100
        "veto_quorum": 2.0,                  # poder_legislativo, puntaje 100
        "comisiones_caidas": 10.0,           # poder_legislativo, puntaje 100
        "iaf_transferencias": 12.0,          # alianzas_territoriales, puntaje 100
        "gobernadores_alineamiento": 70.0,   # alianzas_territoriales, puntaje 100
        "adhesion_reformas_provincial": 90.0, # alianzas_territoriales, puntaje 100
        "cohesion_bloque": 95.0,             # cohesion_interna, puntaje 100
        "cohesion_bloque_senado": 95.0,      # cohesion_interna, puntaje 100
        "movilizacion_cepa": 5.0,            # conflicto_social, puntaje 100
        "protestas_caba": 5.0,               # conflicto_social, puntaje 100
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
