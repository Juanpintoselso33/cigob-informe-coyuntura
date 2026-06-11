import json, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # projects/informe_coyuntura
DATA = ROOT / "web" / "src" / "data"
sys.path.insert(0, str(ROOT))                # para importar config.py

def test_publicar_genera_snapshot():
    subprocess.run([sys.executable, "scripts/publicar.py"], cwd=ROOT, check=True)
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((DATA / "series.json").read_text(encoding="utf-8"))

    # 5 cinturones presentes
    assert set(informe["cinturones"]) == {"macro", "politica", "vida_cotidiana",
                                          "gestion", "espiritu_epoca"}

    # vida_cotidiana enriquecido: al menos 10 indicadores (no los 3 legacy)
    vida = informe["cinturones"]["vida_cotidiana"]["indicadores"]
    assert len(vida) >= 10, f"vida cotidiana solo tiene {len(vida)} indicadores"
    assert "consumo_carne" in vida and "icc_utdt" in vida

    # cada indicador tiene la forma mínima
    for cint in informe["cinturones"].values():
        for ind in cint["indicadores"].values():
            assert "unidad" in ind and "fecha_dato" in ind and "desactualizado" in ind

    # series: dict de listas {fecha, valor} ordenadas asc
    assert isinstance(series, dict) and "tcrm" in series
    fechas = [p["fecha"] for p in series["tcrm"]]
    assert fechas == sorted(fechas)


def test_espiritu_epoca_presente_y_coherente():
    """El 5º cinturón trae sus 3 proxies v1, cada uno con aporte, y el score
    publicado es el promedio que computa el colector."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    esp = informe["cinturones"]["espiritu_epoca"]
    assert set(esp["indicadores"]) >= {"icc_utdt", "sentimiento_digital", "clima_electoral"}
    aportes = [i["aporte_score"] for i in esp["indicadores"].values()
               if i.get("aporte_score") is not None]
    assert len(aportes) >= 3, "espíritu de época: faltan aportes"
    assert abs(round(sum(aportes) / len(aportes), 1) - esp["score"]) <= 0.1
    # la fuente del clima electoral no debe filtrar rutas locales
    assert esp["indicadores"]["clima_electoral"]["fuente"] == "Votómetro CIGOB"


def test_aporte_score_reconcilia_con_score_publicado():
    """El promedio de los aportes por indicador debe reproducir el score del
    cinturón. Para política/gestión esto compara contra el score que computa
    el colector de forma independiente: si una fórmula deriva, el test falla.
    Para vida el score se computa acá mismo a partir de los aportes (su scoring
    vive en publicar.py), así que la igualdad confirma coherencia interna.
    Macro no es promedio simple (usa el ITCM ponderado) y se testea aparte."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    for ck in ("politica", "gestion", "vida_cotidiana"):
        c = informe["cinturones"][ck]
        aportes = [i["aporte_score"] for i in c["indicadores"].values()
                   if i.get("aporte_score") is not None]
        assert aportes, f"{ck}: ningún indicador tiene aporte_score"
        promedio = round(sum(aportes) / len(aportes), 1)
        assert abs(promedio - c["score"]) <= 0.1, \
            f"{ck}: promedio de aportes {promedio} != score publicado {c['score']}"


def test_macro_itcm_reconcilia():
    """Macro: la suma ponderada de los puntajes ITCM (peso_efectivo) reproduce
    el ITCM publicado, la tensión del cinturón es (100 − ITCM)/10 y los
    indicadores de contexto no aportan al score."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["macro"]
    assert c.get("itcm"), "macro sin bloque itcm"
    itcm_val = c["itcm"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    contexto = {k: i for k, i in c["indicadores"].items() if i.get("en_indice") is False}
    assert len(en_indice) == 7, f"esperaba 7 indicadores en el índice, hay {len(en_indice)}"
    assert set(contexto) == {"tcrm", "prestamos_privados", "base_monetaria", "tc_mayorista"}

    ponderado = sum(i["puntaje_itcm"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcm_val) <= 0.15, f"ponderado {ponderado} != ITCM {itcm_val}"
    assert abs(c["score"] - round((100 - itcm_val) / 10, 1)) <= 0.05

    for k, i in contexto.items():
        assert i.get("aporte_score") is None, f"{k} es contexto pero tiene aporte_score"
    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"
        assert abs(i["aporte_score"] - round((100 - i["puntaje_itcm"]) / 10, 1)) <= 0.05


def test_pesos_por_fase_del_mandato():
    """Marco Conceptual: en los primeros años del mandato, gestión y espíritu
    de época pesan más que en la fase de consolidación. Ambos sets suman 1."""
    from datetime import date
    from config import (pesos_cinturones, fase_mandato, PESOS_FASE_TEMPRANA,
                        PESOS_FASE_CONSOLIDACION, PESOS_CINTURONES)
    assert abs(sum(PESOS_FASE_TEMPRANA.values()) - 1.0) < 1e-9
    assert abs(sum(PESOS_FASE_CONSOLIDACION.values()) - 1.0) < 1e-9
    assert fase_mandato(date(2024, 6, 1)) == "temprana"
    assert fase_mandato(date(2027, 12, 9)) == "temprana"     # < 4 años
    assert fase_mandato(date(2027, 12, 11)) == "consolidacion"
    assert pesos_cinturones(date(2024, 6, 1)) is PESOS_FASE_TEMPRANA
    assert pesos_cinturones(date(2028, 1, 1)) is PESOS_FASE_CONSOLIDACION
    # gestión y espíritu pesan más (o igual que nadie menos) en la fase temprana
    for k in ("gestion", "espiritu_epoca"):
        assert PESOS_FASE_TEMPRANA[k] > PESOS_FASE_CONSOLIDACION[k]
    assert set(PESOS_CINTURONES) == {"macro", "politica", "vida_cotidiana",
                                     "gestion", "espiritu_epoca"}


def test_score_global_reconcilia_con_pesos():
    """El score global debe ser el promedio ponderado de los 4 cinturones."""
    from config import PESOS_CINTURONES
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    num = sum(c["score"] * PESOS_CINTURONES.get(k, 0.0)
              for k, c in informe["cinturones"].items())
    den = sum(PESOS_CINTURONES.get(k, 0.0) for k in informe["cinturones"])
    esperado = round(num / den, 1)
    assert abs(esperado - informe["score_global"]) <= 0.1, \
        f"global {informe['score_global']} != ponderado {esperado}"


def test_vida_indicadores_aportan_al_score():
    """Vida: al menos 12 de 13 indicadores entran al score con fórmula."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    vida = informe["cinturones"]["vida_cotidiana"]["indicadores"]
    con_aporte = [k for k, i in vida.items() if i.get("aporte_score") is not None]
    assert len(con_aporte) >= 12, f"vida: sólo {len(con_aporte)} con aporte"


def test_endeudamiento_se_puntua_por_variacion_real():
    """Endeudamiento se puntúa sobre su variación interanual real (no el stock
    nominal): debe tener var_real_12m y un aporte derivado de ella."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    end = informe["cinturones"]["vida_cotidiana"]["indicadores"]["endeudamiento_familiar"]
    assert isinstance(end.get("var_real_12m"), (int, float)), "falta var_real_12m"
    assert end.get("aporte_score") is not None, "endeudamiento sin aporte"
    # tensión = clamp(5 + var_real/4)
    esperado = max(0.0, min(10.0, round(5 + end["var_real_12m"] / 4, 1)))
    assert abs(end["aporte_score"] - esperado) <= 0.1
