"""El indicador de carne del ITCIS vuelve a separar VACUNA de OTRAS (ADR-0322).

ADR-0217 fusionó vacuna+aviar+porcina en un único componente que puntúa
(`consumo_carnes_total`) porque la vacuna sola exageraba el deterioro del
acceso a proteína. Juan pidió sumarla "por separado" (15-sep-2026). Este
archivo cuida que eso no reabra el problema que ADR-0217 cerró: la faena
vacuna no puede entrar dos veces al índice, y la distinción
sustitución/pérdida de acceso no puede perderse.
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


def test_puntuan_vacuna_y_otras_no_el_total_fusionado():
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    assert "consumo_carne_vacuna" in ingresos, "la vacuna dejó de puntuar"
    assert "consumo_carnes_otras" in ingresos, "el resto (aviar+porcina) dejó de puntuar"
    assert "consumo_carnes_total" not in ingresos, (
        "el total fusionado volvió a puntuar: duplicaría la faena vacuna, que "
        "ya puntúa en consumo_carne_vacuna")


def test_no_duplica_el_peso_del_total_anterior():
    """El peso nominal de las dos partes tiene que sumar EXACTAMENTE el que
    tenía el total fusionado (0,0392): ni más (doble conteo) ni menos (le
    resta peso al resto de la dimensión sin que nadie lo haya decidido)."""
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    vacuna_efectivo = ingresos["consumo_carne_vacuna"]
    otras_efectivo = ingresos["consumo_carnes_otras"]
    # Los dos vienen de la MISMA cesión ×0,80 que sufrió el total antes de
    # partirse (ADR-0225): comparar contra la razón de motorización, que no
    # se tocó, aísla si la cesión se aplicó bien a las dos partes.
    motor = ingresos["motorizacion_total"]
    razon_vieja = 0.0396 / 0.0392   # motorización / carne, antes del split
    razon_nueva = motor / (vacuna_efectivo + otras_efectivo)
    assert abs(razon_nueva - razon_vieja) < 1e-3, (
        f"la suma de vacuna+otras no conserva el peso del total anterior: "
        f"razón {razon_nueva:.6f}, esperada {razon_vieja:.6f}")


def test_las_dos_cards_existen_y_puntuan():
    """Regla ADR-0153/0216: ninguna card puede quedar sin puntuar."""
    assert "consumo_carne_vacuna" in IND
    assert "consumo_carnes_otras" in IND
    assert "consumo_carnes_total" not in IND, (
        "el total fusionado volvió como card: ya no puntúa (ADR-0322), así "
        "que sería una card de contexto — prohibido por ADR-0153/0216")
    assert all(i.get("en_indice") for i in IND.values()), (
        "hay cards que no integran el índice: " +
        ", ".join(k for k, i in IND.items() if not i.get("en_indice")))


def test_la_matriz_explica_el_color_de_las_dos_con_texto_propio():
    """Las dos cards que puntúan comparten la composición (vacuna Y el resto
    aparecen en las dos, para que el lector vea el total desde cualquiera),
    pero el texto de CADA UNA tiene que hablar de SU propio nivel: antes de
    este fix las dos cards publicaban el mismo párrafo, el de la vacuna
    (verificado en `dist/`: ninguna mención a aviar, porcina ni al valor
    67,19 de `consumo_carnes_otras`)."""
    por_que_vacuna = (IND["consumo_carne_vacuna"].get("semaforo") or {}).get("por_que")
    por_que_otras = (IND["consumo_carnes_otras"].get("semaforo") or {}).get("por_que")
    assert por_que_vacuna, "consumo_carne_vacuna perdió la matriz que explica su color"
    assert por_que_otras, "consumo_carnes_otras perdió la matriz que explica su color"

    # Las dos mencionan la vacuna (aparece en las dos como parte del total),
    # pero NO pueden ser el mismo texto: cada una tiene que hablar de lo suyo.
    assert "vacuna" in por_que_vacuna
    assert "vacuna" in por_que_otras
    assert por_que_vacuna != por_que_otras, (
        "las dos cards publican el MISMO texto — control negativo: éste es "
        "exactamente el bug que se está arreglando")

    # La card de otras carnes tiene que nombrar su propio nivel y componentes.
    otras_valor = IND["consumo_carnes_otras"].get("valor")
    assert otras_valor is not None
    assert publicar.coma(round(otras_valor, 1)) in por_que_otras, (
        f"consumo_carnes_otras no menciona su propio valor ({otras_valor}): "
        "sigue publicando el nivel de la vacuna")
    assert "aviar" in por_que_otras.lower(), por_que_otras
    assert "porcina" in por_que_otras.lower(), por_que_otras

    # Control negativo explícito: la card de otras NO puede ser el párrafo
    # "Consumo aparente de carne vacuna" que le corresponde a la otra card.
    assert not por_que_otras.startswith("Consumo aparente de carne vacuna"), (
        "consumo_carnes_otras publica el párrafo de apertura de la vacuna")
    assert por_que_vacuna.startswith("Consumo aparente de carne vacuna")
    assert por_que_otras.startswith("Consumo aparente de aviar")


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
