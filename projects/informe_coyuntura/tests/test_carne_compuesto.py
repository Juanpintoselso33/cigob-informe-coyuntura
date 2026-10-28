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

sys.path.insert(0, str(ROOT / "scripts" / "vida_cotidiana" / "collectors"))
import consumo_carnes  # noqa: E402

# ADR-0392: base del índice (promedio del 4T-2023, kg/hab/año) de cada serie.
BASE_VACUNA = 53.49
BASE_TOTAL = 116.95


def test_puntuan_el_total_y_la_vacuna():
    ingresos = itvc.DIMENSIONES_ITVC["consumo"]["indicadores"]   # ADR-0373
    assert "consumo_carnes_total" in ingresos, "el total de las tres carnes dejó de puntuar"
    assert "consumo_carne_vacuna" in ingresos, "la vacuna (aspiracional) dejó de puntuar"
    assert "consumo_carnes_otras" not in ingresos, (
        "aviar + porcina volvió a puntuar: ya cuenta dentro del total (ADR-0339)")


def test_las_carnes_conservan_el_peso_de_antes_mitad_y_mitad():
    """El total y la vacuna reparten el MISMO 0,0392 que tenían las carnes,
    mitad y mitad: ni más (le quitaría peso al resto de la dimensión sin que
    nadie lo decidiera) ni menos."""
    ingresos = itvc.DIMENSIONES_ITVC["consumo"]["indicadores"]   # ADR-0373
    total, vacuna = ingresos["consumo_carnes_total"], ingresos["consumo_carne_vacuna"]
    assert total == vacuna, f"no es mitad y mitad: total {total}, vacuna {vacuna}"
    motor = ingresos["motorizacion_total"]
    razon_vieja = 0.0396 / 0.0392   # motorización / carnes, antes y después
    razon_nueva = motor / (total + vacuna)
    # 2e-3 y no 1e-3: ADR-0373 reescaló los internos a cuatro decimales sobre
    # una dimensión más chica, y el redondeo mueve la razón 0,001.
    assert abs(razon_nueva - razon_vieja) < 2e-3, (
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


def test_las_series_llegan_al_4t_2023():
    for clave in ("consumo_carne_vacuna", "consumo_carnes_total"):
        serie = SERIES.get(clave) or []
        assert len(serie) >= 30, f"{clave}: la serie tiene {len(serie)} puntos"
        assert serie[0]["fecha"][:7] <= "2023-10", (
            f"{clave}: la serie no llega al 4T-2023, que es la base del índice")


def test_el_titular_y_el_puntaje_son_el_mismo_dato():
    """ADR-0392: la tarjeta muestra kilos y la serie que puntúa es el MISMO
    consumo en índice 4T-2023 = 100. Mismo mes, y el cociente entre los dos
    tiene que dar la base. Con la faena (ADR-0217) esto no se cumplía: eran
    dos fuentes y dos meses distintos."""
    for clave, base in (("consumo_carne_vacuna", BASE_VACUNA),
                        ("consumo_carnes_total", BASE_TOTAL)):
        card = IND[clave]
        if card.get("desactualizado") or card.get("valor") is None:
            continue
        ultimo = (SERIES.get(clave) or [])[-1]
        assert card["fecha_dato"][:7] == ultimo["fecha"][:7], (
            f"{clave}: la tarjeta es de {card['fecha_dato'][:7]} y la serie llega a "
            f"{ultimo['fecha'][:7]}")
        implicita = card["valor"] / ultimo["valor"] * 100
        assert abs(implicita - base) <= 0.15, (
            f"{clave}: {card['valor']} kg contra índice {ultimo['valor']} implica una "
            f"base de {implicita:.2f} kg, no {base}: la tarjeta y el puntaje salen "
            "de datos distintos")


def test_la_base_de_la_vacuna_es_el_4t_2023_reconstruido():
    serie = consumo_carnes.series_por_carne({"vacuna": {}, "aviar": {}, "porcina": {}})
    base = sum(serie["vacuna"][m] for m in ("2023-10", "2023-11", "2023-12")) / 3
    assert round(base, 2) == BASE_VACUNA
    # Un dato real de la fuente gana sobre el ancla.
    serie = consumo_carnes.series_por_carne(
        {"vacuna": {"2023-12": 50.0}, "aviar": {}, "porcina": {}})
    assert serie["vacuna"]["2023-12"] == 50.0


LINEAS_BOVINOS = """COMERCIALIZACION
CARNE BOVINA [Miles de PER CAPITA PER CAPITA - Toneladas eq. US$/ton eq.
2025 2 .315 49,92 853.958 4.347
Noviembre 170 44,63 50,28 7 8.495 4.626
Diciembre 197 50,04 49,93 6 7.001 4.828
2026 1 .560 44,95 675.192 5.416
Enero 179 45,49 49,28 6 4.715 5.032
Octubre
""".splitlines()

LINEAS_PORCINOS = """2025
Dic 831.491 76.921 3.341 10.638 1.167 1.875 80.647 20,47 18,90
Total 2025 8.517.433 812.272 53.475 171.771 11.115 16.150 876.075 18,89
2026
Ene 718.124 67.339 3.072 9.496 1.661 1.893 70.433 17,88 18,97
""".splitlines()


def test_los_lectores_toman_el_promedio_movil():
    """Bovinos trae (consumo, per cápita del mes, móvil, exportaciones): el
    móvil es el segundo decimal. Porcinos trae el móvil al final. Un mes sin
    dato (renglón «Octubre» vacío) no entra, y el renglón de año tampoco."""
    v = consumo_carnes._filas_por_mes(LINEAS_BOVINOS, consumo_carnes.MESES_LARGOS, 1)
    assert v == {"2025-11": 50.28, "2025-12": 49.93, "2026-01": 49.28}
    p = consumo_carnes._filas_por_mes(LINEAS_PORCINOS, consumo_carnes.MESES_CORTOS, -1)
    assert p == {"2025-12": 18.90, "2026-01": 18.97}


def test_el_lector_aviar_usa_la_columna_del_movil(tmp_path):
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["AÑO", "Faena", "Producción", "Consumo Aparente per capita",
               "Consumo Aparente per capita promedio móvil"])
    filas = []
    for anio in ("2024", 2025):     # el año viene como texto o como número
        filas += [[anio, 1, 1, 47.0, 46.0]] + [[m.capitalize(), 1, 1, 45.0, 46.0 + i / 100]
                                               for i, m in enumerate(consumo_carnes.MESES_LARGOS)]
    filas += [[2026, 1, 1, 47.0, 47.7], ["Enero", 1, 1, 49.9, 46.16], ["Febrero", None, None, None, None]]
    for f in filas:
        ws.append(f)
    buf = io.BytesIO()
    wb.save(buf)
    a = consumo_carnes.parsear_aviar(buf.getvalue())
    assert a["2024-01"] == 46.0 and a["2025-12"] == 46.11 and a["2026-01"] == 46.16
    assert "2026-02" not in a


def test_el_registro_de_la_tarjeta_es_el_ultimo_mes_con_las_tres():
    serie = {"vacuna": {"2025-09": 50.0, "2026-09": 45.0},
             "aviar": {"2025-09": 47.0, "2026-09": 47.0, "2026-10": 48.0},
             "porcina": {"2025-09": 18.0, "2026-09": 20.0}}
    r = consumo_carnes.registro_del_mes(serie)
    assert r["mes"] == "2026-09" and r["total"] == 112.0
    assert r["variaciones"]["vacuna"] == -10.0
    assert r["variaciones"]["total"] == round((112 / 115 - 1) * 100, 2)


def test_cada_serie_suma_sus_propias_carnes():
    """El riesgo que ADR-0322 dice evitar: que `consumo_carnes_otras` sume
    también la vacuna (que entraría dos veces al ITCIS). Se mira directo qué
    carnes recibe la función que arma cada serie."""
    categorias_por_llamada = []

    def _fake(categorias):
        categorias_por_llamada.append(tuple(categorias))
        return [["2023-10-01", 100.0]]

    import unittest.mock as mock
    with mock.patch.object(descargar_series, "_fetch_consumo_indice", side_effect=_fake):
        descargar_series.fetch_carne_vacuna_indice_serie()
        descargar_series.fetch_carnes_otras_indice_serie()
        descargar_series.fetch_carnes_total_serie()

    assert categorias_por_llamada == [
        ("vacuna",), ("aviar", "porcina"), ("vacuna", "aviar", "porcina")]
    assert "INDEC — faena" not in DESCARGAR, "la carne volvió a la faena del INDEC"
