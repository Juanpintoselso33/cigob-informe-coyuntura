"""Tests del diagnóstico de bandas (ADR-0081).

El test que importa es el primero: verifica que el diagnóstico puntúe con la
misma escala y sobre el mismo valor transformado que el índice publicado. La
primera versión no lo hacía y mandaba a revisar una banda perfecta.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import itcm
import parametrica
import revision_bandas

SNAPSHOT = Path(__file__).parent.parent / "web" / "src" / "data" / "informe.json"


def test_el_diagnostico_puntua_igual_que_el_indice_publicado():
    """El bug que motivó este test: la serie de rem_ipc_12m guarda la
    expectativa ANUAL (24,2%) pero el ITCM puntúa su equivalente MENSUAL
    (1,82%) contra bandas mensuales. Puntuar el crudo daba 10 —el piso— todos
    los meses, y el diagnóstico reportaba 'revisar' sobre una banda que estaba
    bien.

    Acá se compara, para cada indicador del ITCM, el puntaje que produce el
    diagnóstico con el ÚLTIMO valor de su serie contra el puntaje_banda que
    publica el snapshot. Si alguien agrega una transformación previa al
    puntaje y no la refleja acá, este test la delata.
    """
    bloque = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cinturones"]["macro"]["itcm"]
    publicados = {ik: i["puntaje_banda"]
                  for d in bloque["dimensiones"].values()
                  for ik, i in d["indicadores"].items()}

    import json as _json
    series = _json.loads((Path(__file__).parent.parent / "web" / "src" / "data"
                          / "series.json").read_text(encoding="utf-8"))
    valores = revision_bandas._valores_por_indicador("ITCM", series)
    comparados = 0
    for ind, serie in valores.items():
        if ind not in publicados or not serie:
            continue
        del_diagnostico = parametrica.puntaje_de(
            serie[-1], ind, itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM,
            itcm.TRANSFORMACIONES_ITCM)
        # tolerancia amplia: la reconstrucción puede terminar un mes antes que
        # la ficha viva. Lo que se busca es una divergencia de ESCALA, no de mes.
        assert abs(del_diagnostico - publicados[ind]) < 25.0, (
            f"{ind}: el diagnóstico puntúa {del_diagnostico} y el índice publica "
            f"{publicados[ind]} — ¿hay una transformación previa que el "
            f"diagnóstico no aplica?")
        comparados += 1
    assert comparados >= 8, f"solo se compararon {comparados} indicadores"


def test_el_rem_se_transforma_dentro_del_puntaje_y_no_antes():
    """Caso concreto del bug que motivó ADR-0082, pineado aparte.

    La serie del REM guarda el valor ANUAL y así debe llegar a quien puntúe:
    la conversión a equivalente mensual la hace `puntaje_de` a partir de
    TRANSFORMACIONES_ITCM. Si alguien la sacara de ahí, el valor anual se
    puntuaría contra bandas mensuales y el indicador caería al piso siempre."""
    assert "rem_ipc_12m" in itcm.TRANSFORMACIONES_ITCM

    anual = 23.3
    con_transformacion = parametrica.puntaje_de(
        anual, "rem_ipc_12m", itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM,
        itcm.TRANSFORMACIONES_ITCM)
    sin_transformacion = parametrica.puntaje_interpolado(
        anual, itcm.BANDAS_ITCM["rem_ipc_12m"])

    assert sin_transformacion == 10.0, "sin transformar, el REM cae al piso"
    assert con_transformacion > 75.0, con_transformacion


def test_el_diagnostico_no_recomienda_recalibrar_por_si_solo():
    """El estado se llama 'revisar', no 'recalibrar': la decisión es de una
    persona (ADR-0045). Si el vocabulario cambia, alguien podría automatizar
    un cambio de anclas, que es justamente lo que no debe pasar."""
    filas = revision_bandas.diagnosticar()
    estados = {f["estado"] for f in filas}
    assert estados <= {"revisar", "saturado", "historia_corta", "ok"}, estados
    assert "recalibrar" not in estados


def test_una_banda_bien_repartida_no_se_marca():
    """Control negativo: sin saturación no hay aviso."""
    filas = {f["indicador"]: f for f in revision_bandas.diagnosticar()}
    ok = [f for f in filas.values() if f["estado"] == "ok"]
    assert ok, "ningún indicador quedó limpio: el umbral estaría mal puesto"
