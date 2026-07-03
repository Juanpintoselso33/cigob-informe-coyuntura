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
    cinturón (solo política queda como promedio simple: macro/gestión/vida
    usan ITCM/ITCG/ITVC y se testean aparte)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    for ck in ("politica",):
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
    assert len(en_indice) == 11, f"esperaba 11 indicadores en el índice, hay {len(en_indice)}"
    assert set(contexto) == {"badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"}

    ponderado = sum(i["puntaje_itcm"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcm_val) <= 0.15, f"ponderado {ponderado} != ITCM {itcm_val}"
    assert abs(c["score"] - round((100 - itcm_val) / 10, 1)) <= 0.05

    for k, i in contexto.items():
        assert i.get("aporte_score") is None, f"{k} es contexto pero tiene aporte_score"
    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"
        assert abs(i["aporte_score"] - round((100 - i["puntaje_itcm"]) / 10, 1)) <= 0.05


def test_gestion_itcg_reconcilia():
    """Gestión: la suma ponderada de los puntajes ITCG (peso_efectivo) reproduce
    el ITCG publicado, la tensión del cinturón es (100 − ITCG)/10 y los
    indicadores de contexto (litigiosidad SRT) no aportan al score."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["gestion"]
    assert c.get("itcg"), "gestión sin bloque itcg"
    itcg_val = c["itcg"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    contexto = {k: i for k, i in c["indicadores"].items() if i.get("en_indice") is False}
    assert len(en_indice) == 14, f"esperaba 14 indicadores en el índice, hay {len(en_indice)}"
    assert set(contexto) == {"litigiosidad_laboral", "alertas_manifestacion", "protestas_caba"}

    ponderado = sum(i["puntaje_itcg"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcg_val) <= 0.15, f"ponderado {ponderado} != ITCG {itcg_val}"
    assert abs(c["score"] - round((100 - itcg_val) / 10, 1)) <= 0.05

    # Los pesos de dimensión del doc 260702 llegan publicados: 35/25/15/15/10.
    pesos = {k: d["peso"] for k, d in c["itcg"]["dimensiones"].items()}
    assert pesos == {"reformas_economicas": 0.35, "reforma_estado": 0.25,
                     "reforma_laboral": 0.15, "privatizaciones_inversion": 0.15,
                     "social_orden": 0.10}

    for k, i in contexto.items():
        assert i.get("aporte_score") is None, f"{k} es contexto pero tiene aporte_score"
    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"
        assert abs(i["aporte_score"] - round((100 - i["puntaje_itcg"]) / 10, 1)) <= 0.05


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


def test_vida_itvc_reconcilia():
    """Vida: la suma ponderada de los índices base-100 (peso_efectivo)
    reproduce el ITVC publicado, la tensión del cinturón es 5 − (ITVC−100)×0,2
    y el contexto (sentimiento digital) no aporta al score."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["vida_cotidiana"]
    assert c.get("itvc"), "vida sin bloque itvc"
    itvc_val = c["itvc"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    contexto = {k: i for k, i in c["indicadores"].items() if i.get("en_indice") is False}
    assert len(en_indice) == 12, f"esperaba 12 componentes en el índice, hay {len(en_indice)}"
    assert set(contexto) <= {"sentimiento_digital"}

    ponderado = sum(i["indice_itvc"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itvc_val) <= 0.2, f"ponderado {ponderado} != ITVC {itvc_val}"
    esperado = round(min(10.0, max(0.0, 5.0 - (itvc_val - 100.0) * 0.2)), 1)
    assert abs(c["score"] - esperado) <= 0.05

    # Los pesos de dimensión del doc 260702 llegan publicados: 35/25/10/15/15.
    pesos = {k: d["peso"] for k, d in c["itvc"]["dimensiones"].items()}
    assert pesos == {"ingresos": 0.35, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "confianza": 0.15}

    for k, i in contexto.items():
        assert i.get("aporte_score") is None, f"{k} es contexto pero tiene aporte_score"
    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"


def test_robustez_publicada_encierra_el_valor():
    """ADR-0019: los tres índices publican su rango de robustez p05-p95
    (Monte Carlo con semilla fija) y el valor puntual cae dentro del rango."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    for ck, clave in (("macro", "itcm"), ("gestion", "itcg"), ("vida_cotidiana", "itvc")):
        bloque = informe["cinturones"][ck].get(clave)
        assert bloque and bloque.get("robustez"), f"{clave}: sin bloque de robustez"
        r = bloque["robustez"]
        assert r["p05"] <= bloque["valor"] <= r["p95"], \
            f"{clave}: valor {bloque['valor']} fuera del rango [{r['p05']}, {r['p95']}]"
        t_lo, t_hi = r["tension_rango"]
        assert t_lo <= t_hi and 0 <= t_lo and t_hi <= 10


def test_endeudamiento_se_puntua_con_mora():
    """Endeudamiento (D3 del ITVC): su índice viene de la serie itvc_endeudamiento
    (deuda real de familias × corrección por mora, Informe sobre Bancos)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((DATA / "series.json").read_text(encoding="utf-8"))
    end = informe["cinturones"]["vida_cotidiana"]["indicadores"]["endeudamiento_familiar"]
    assert end.get("indice_itvc") is not None, "endeudamiento sin índice ITVC"
    serie = series.get("itvc_endeudamiento") or []
    assert serie, "falta la serie itvc_endeudamiento"
    assert abs(end["indice_itvc"] - serie[-1]["valor"]) <= 0.15
