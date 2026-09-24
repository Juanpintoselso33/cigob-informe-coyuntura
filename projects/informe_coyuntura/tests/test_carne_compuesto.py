"""Puntúan el TOTAL de las tres carnes y, aparte, la VACUNA (ADR-0339).

ADR-0217 fusionó vacuna+aviar+porcina en un único componente; ADR-0322 lo
partió en vacuna y aviar+porcina. El equipo pedía otra cosa: conservar el total
y sumar la vacuna como indicador aspiracional. La vacuna entra dos veces —dentro
del total y sola— a propósito, con el mismo peso total que ya tenían las carnes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc  # noqa: E402
import publicar  # noqa: E402
import descargar_series  # noqa: E402

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


def test_puntuan_el_total_y_la_vacuna():
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    assert "consumo_carnes_total" in ingresos, "el total de las tres carnes dejó de puntuar"
    assert "consumo_carne_vacuna" in ingresos, "la vacuna (aspiracional) dejó de puntuar"
    assert "consumo_carnes_otras" not in ingresos, (
        "aviar + porcina volvió a puntuar: ya cuenta dentro del total (ADR-0339)")


def test_las_carnes_conservan_el_peso_de_antes_mitad_y_mitad():
    """El total y la vacuna reparten el MISMO 0,0392 que tenían las carnes,
    mitad y mitad: ni más (le quitaría peso al resto de la dimensión sin que
    nadie lo decidiera) ni menos."""
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    total, vacuna = ingresos["consumo_carnes_total"], ingresos["consumo_carne_vacuna"]
    assert total == vacuna, f"no es mitad y mitad: total {total}, vacuna {vacuna}"
    motor = ingresos["motorizacion_total"]
    razon_vieja = 0.0396 / 0.0392   # motorización / carnes, antes y después
    razon_nueva = motor / (total + vacuna)
    assert abs(razon_nueva - razon_vieja) < 1e-3, (
        f"las carnes no conservan su peso: razón {razon_nueva:.6f}, esperada {razon_vieja:.6f}")


def test_las_dos_cards_existen_y_puntuan():
    """Regla ADR-0153/0216: ninguna card puede quedar sin puntuar."""
    assert "consumo_carnes_total" in IND
    assert "consumo_carne_vacuna" in IND
    assert "consumo_carnes_otras" not in IND, (
        "aviar + porcina volvió como card: ya no puntúa (ADR-0339), así que "
        "sería una card de contexto — prohibido por ADR-0153/0216")
    assert all(i.get("en_indice") for i in IND.values()), (
        "hay cards que no integran el índice: " +
        ", ".join(k for k, i in IND.items() if not i.get("en_indice")))


def test_la_matriz_explica_el_color_de_las_dos_con_texto_propio():
    """Las dos cards comparten los números, pero cada texto habla de SU nivel:
    el total cuenta la composición de las tres carnes; la vacuna, su nivel
    contra ese total. Control negativo: no pueden publicar el mismo párrafo."""
    por_que_vacuna = (IND["consumo_carne_vacuna"].get("semaforo") or {}).get("por_que")
    por_que_total = (IND["consumo_carnes_total"].get("semaforo") or {}).get("por_que")
    assert por_que_vacuna, "consumo_carne_vacuna perdió la matriz que explica su color"
    assert por_que_total, "consumo_carnes_total perdió la matriz que explica su color"
    assert por_que_vacuna != por_que_total, "las dos cards publican el MISMO texto"

    total_valor = IND["consumo_carnes_total"].get("valor")
    assert total_valor is not None
    assert publicar.coma(round(total_valor, 1)) in por_que_total, (
        f"consumo_carnes_total no menciona su propio valor ({total_valor})")
    assert "aviar" in por_que_total.lower() and "porcina" in por_que_total.lower(), por_que_total
    assert por_que_vacuna.startswith("Consumo aparente de carne vacuna")
    assert por_que_total.startswith("Consumo aparente de las tres carnes")


def test_las_series_se_reconstruyen_desde_la_faena_del_indec():
    """El tablero de SAGYP es una foto del mes: no tiene historia para
    rebasear al 4T-2023. La faena sí, y desde 2009."""
    for sid in ("40.3_VT_0_M_17", "40.3_PT_0_M_18", "40.3_AT_0_M_14"):
        assert sid in DESCARGAR, f"falta la serie de faena {sid}"
    for clave in ("consumo_carne_vacuna", "consumo_carnes_otras"):
        serie = SERIES.get(clave) or []
        assert len(serie) >= 30, f"{clave}: la serie tiene {len(serie)} puntos"
        assert serie[0]["fecha"][:7] <= "2023-10", (
            f"{clave}: la serie no llega al 4T-2023, que es la base del índice")


def test_la_reconstruccion_no_se_separa_de_la_fuente_oficial():
    """La prueba de que la reconstrucción mide lo que dice: reconstruyendo el
    total como vacuna_abs + otras_abs (en NIVEL, no índice, usando el ratio
    publicado por SAGYP), su variación interanual tiene que parecerse a la que
    publica SAGYP para el total. Si se separan, la faena dejó de aproximar el
    consumo."""
    variaciones = (IND.get("consumo_carne_vacuna") or {}).get("variaciones") or {}
    ia_sagyp = variaciones.get("total")
    if ia_sagyp is None:
        return  # el PDF no trajo variaciones esta corrida

    def variacion_ia(clave):
        d = {p["fecha"][:7]: p["valor"] for p in (SERIES.get(clave) or [])}
        meses = sorted(d)
        if not meses:
            return None
        ult = meses[-1]
        hace_un_anio = f"{int(ult[:4]) - 1}-{ult[5:7]}"
        if hace_un_anio not in d:
            return None
        return (d[ult] / d[hace_un_anio] - 1) * 100

    ia_v, ia_o = variacion_ia("consumo_carne_vacuna"), variacion_ia("consumo_carnes_otras")
    if ia_v is None or ia_o is None:
        return  # serie corta: nada que comparar todavía
    # Ponderado por el peso relativo que cada una tenía dentro del total al
    # 4T-2023 (52,3%/47,7%, ver ADR-0322): aproxima la variación del total sin
    # tener que reconstruirlo como serie propia.
    ia_propia = ia_v * 0.523 + ia_o * 0.477
    brecha = abs(ia_propia - ia_sagyp)
    assert brecha <= BRECHA_MAX_PP, (
        f"la reconstrucción desde faena da {ia_propia:+.2f}% i.a. y SAGYP "
        f"publica {ia_sagyp:+.2f}%: {brecha:.2f} pp de brecha. No es un bug de "
        f"código — es que la faena dejó de aproximar el consumo. Ver ADR-0217/0322."
    )


def test_otras_no_se_reconstruye_con_las_categorias_del_total():
    """El riesgo exacto que ADR-0322 dice evitar: que `consumo_carnes_otras`
    termine reconstruida con la faena de las TRES carnes (contando la vacuna
    dos veces, una en `consumo_carne_vacuna` y otra acá).

    Antes de este test, sustituir en memoria las categorías de la serie de
    `consumo_carnes_otras` por las del total (`vacuna+aviar+porcina`) dejaba
    pasar `test_la_reconstruccion_no_se_separa_de_la_fuente_oficial` y
    `test_las_series_se_reconstruyen_desde_la_faena_del_indec` igual —
    ninguna de las dos mira QUÉ categorías entran a la reconstrucción, sólo
    el resultado agregado. Éste sí las mira, directo en la función que arma
    la serie.
    """
    categorias_por_llamada = []

    def _fake_fetch_faena_indice(categorias):
        categorias_por_llamada.append(tuple(categorias))
        return [["2023-10-01", 100.0]]

    import unittest.mock as mock
    with mock.patch.object(descargar_series, "_fetch_faena_indice",
                            side_effect=_fake_fetch_faena_indice):
        descargar_series.fetch_carne_vacuna_indice_serie()
        descargar_series.fetch_carnes_otras_indice_serie()

    assert categorias_por_llamada[0] == ("vacuna",), (
        f"consumo_carne_vacuna se reconstruye con {categorias_por_llamada[0]}, "
        "no sólo con la faena vacuna")
    assert categorias_por_llamada[1] == ("aviar", "porcina"), (
        f"consumo_carnes_otras se reconstruye con {categorias_por_llamada[1]}: "
        "si esto alguna vez incluye 'vacuna', la faena vacuna entra dos veces "
        "al ITCIS — exactamente lo que ADR-0322 dice evitar")
    assert "vacuna" not in categorias_por_llamada[1], (
        "control positivo del control negativo: esta línea tiene que fallar "
        "si alguien sustituye la tupla de consumo_carnes_otras por la del "
        "total (probado a mano rompiéndolo antes de este commit)")
