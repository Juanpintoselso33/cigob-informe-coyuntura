"""El indicador de carne del ITCIS es COMPUESTO y lo que puntúa es el TOTAL.

La ficha de proteína animal (ago-2026) existe porque leer la caída del consumo
de carne vacuna como pérdida de poder adquisitivo es un falso positivo: buena
parte es sustitución hacia pollo y cerdo. Su respuesta fue tratar A (vacuna),
B (total) y C (ratio) como "un único indicador compuesto".

Hasta ADR-0217 se había implementado la EXPLICACIÓN y no el compuesto: puntuaba
la vacuna sola (89,3) mientras el total —que cae mucho menos (95,0)— se
publicaba al lado sin entrar al cálculo. Se sumaban cerdo y pollo para nada.

Este test cuida las cuatro cosas que hacen que eso no vuelva a pasar.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc  # noqa: E402

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
DESCARGAR = (ROOT / "scripts" / "descargar_series.py").read_text(encoding="utf-8")
IND = SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]

# La faena es PRODUCCIÓN y no netea exportaciones, así que la reconstrucción no
# tiene por qué dar igual que el per cápita de SAGYP. Lo que no puede es
# separarse: al 2026-08-20 la brecha era 1,17 pp.
BRECHA_MAX_PP = 3.0


def test_el_que_puntua_es_el_total_no_la_vacuna():
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    assert "consumo_carnes_total" in ingresos, "el compuesto no puntúa"
    assert "consumo_carne" not in ingresos, (
        "volvió a puntuar la vacuna sola, que es el falso positivo que la ficha "
        "vino a desarmar")


def test_la_vacuna_no_es_card_pero_su_serie_sigue():
    """Es el Componente A: diagnóstico dentro de la matriz A×B, no indicador.
    Como card sin puntaje violaría la regla de ADR-0153/0216."""
    assert "consumo_carne" not in IND, "la vacuna volvió como card que no puntúa"
    assert "consumo_carne" in SERIES, "su serie tiene que seguir publicándose"
    assert all(i.get("en_indice") for i in IND.values()), (
        "hay cards que no integran el índice: " +
        ", ".join(k for k, i in IND.items() if not i.get("en_indice")))


def test_la_matriz_ab_explica_el_color_del_total():
    """El descarte de la vacuna va DESPUÉS de `_semaforos`, porque la matriz la
    lee ahí. Hacerlo antes deja al total sin explicación y NADA falla en voz
    alta — probado con VIDA_OCULTOS: el `por_que` quedó vacío y el gate pasó."""
    por_que = (IND["consumo_carnes_total"].get("semaforo") or {}).get("por_que")
    assert por_que, "el total perdió la matriz A×B que explica su color"
    assert "vacuna" in por_que, por_que


def test_la_serie_se_reconstruye_desde_la_faena_del_indec():
    """El tablero de SAGYP es una foto del mes: no tiene historia para
    rebasear al 4T-2023. La faena sí, y desde 2009."""
    for sid in ("40.3_VT_0_M_17", "40.3_PT_0_M_18", "40.3_AT_0_M_14"):
        assert sid in DESCARGAR, f"falta la serie de faena {sid}"
    serie = SERIES.get("consumo_carnes_total") or []
    assert len(serie) >= 30, f"la serie tiene {len(serie)} puntos"
    assert serie[0]["fecha"][:7] <= "2023-10", (
        "la serie no llega al 4T-2023, que es la base del índice")


def test_la_reconstruccion_no_se_separa_de_la_fuente_oficial():
    """La prueba de que la reconstrucción mide lo que dice: su variación
    interanual tiene que parecerse a la que publica SAGYP para el total. Si se
    separan, la faena dejó de aproximar el consumo — probablemente porque
    cambió el peso de las exportaciones, que la faena no netea."""
    d = {p["fecha"][:7]: p["valor"] for p in SERIES["consumo_carnes_total"]}
    meses = sorted(d)
    ult = meses[-1]
    hace_un_año = f"{int(ult[:4]) - 1}-{ult[5:7]}"
    if hace_un_año not in d:
        return  # serie corta: nada que comparar todavía
    ia_propia = (d[ult] / d[hace_un_año] - 1) * 100
    ia_sagyp = (IND["consumo_carnes_total"].get("variaciones") or {}).get("total")
    if ia_sagyp is None:
        return  # el PDF no trajo variaciones esta corrida
    brecha = abs(ia_propia - ia_sagyp)
    assert brecha <= BRECHA_MAX_PP, (
        f"la reconstrucción desde faena da {ia_propia:+.2f}% i.a. y SAGYP "
        f"publica {ia_sagyp:+.2f}%: {brecha:.2f} pp de brecha. No es un bug de "
        f"código — es que la faena dejó de aproximar el consumo. Ver ADR-0217."
    )
