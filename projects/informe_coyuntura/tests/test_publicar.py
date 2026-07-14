import json, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # projects/informe_coyuntura
DATA = ROOT / "web" / "src" / "data"
sys.path.insert(0, str(ROOT))                # para importar config.py
sys.path.insert(0, str(ROOT / "scripts"))
import publicar
import itcm


def test_build_vida_agrega_sentimiento_digital_aunque_trends_falle():
    # Regresión (hallazgo real 2026-07-09): cuando Trends devuelve
    # interes_relativo=None (429/timeout), build_vida omitía la llamada a
    # _add() por completo -- el indicador quedaba AUSENTE del dict, no solo
    # con valor=None, así que _carry_forward (que solo repara claves ya
    # presentes) no podía restaurarlo y sentimiento_digital desaparecía del
    # índice entero.
    raw = {"trends": {"sentimiento_digital": {"interes_relativo": None}},
           "metadata": {"timestamp": "2026-07-09T00:00:00"}}
    enriquecido = publicar.build_vida(raw)
    assert "sentimiento_digital" in enriquecido
    assert enriquecido["sentimiento_digital"]["valor"] is None


def test_macro_input_txt_explica_presion_dolarizacion_en_regimen_restringido():
    ind = {
        "valor": 75.15,
        "regimen": "precio",
        "metrica": 50.12,
        "ventana_meses": 3,
        "ventana_parcial": False,
    }
    assert publicar._macro_input_txt("presion_dolarizacion", ind) == (
        "presión 75,15 pts = brecha CCL/mayorista 50,12% "
        "(promedio móvil 3 meses)"
    )


def test_macro_input_txt_explica_transicion_del_regimen_abierto():
    ind = {
        "valor": 42.86,
        "regimen": "flujo",
        "metrica": 5.14,
        "ventana_meses": 1,
        "ventana_parcial": True,
    }
    assert publicar._macro_input_txt("presion_dolarizacion", ind) == (
        "presión 42,86 pts = compras netas de USD de personas humanas "
        "5,14% del M2 privado (ventana de transición: 1 mes)"
    )


def test_macro_input_txt_explica_ventana_movil_del_regimen_abierto():
    ind = {
        "valor": 45.24,
        "regimen": "flujo",
        "metrica": 5.43,
        "ventana_meses": 3,
        "ventana_parcial": False,
    }
    assert publicar._macro_input_txt("presion_dolarizacion", ind) == (
        "presión 45,24 pts = compras netas de USD de personas humanas "
        "5,43% del M2 privado (ventana móvil 3 meses)"
    )


def test_scoring_itcm_pasa_anclas_explicitas_al_monte_carlo(monkeypatch):
    recibidos = {}

    def robustez(*args, **kwargs):
        recibidos.update(kwargs)
        return {"p05": 0.0, "p95": 100.0}

    monkeypatch.setattr(publicar.sensibilidad, "robustez_compacta", robustez)
    cinturon = {
        "itcm": {
            "dimensiones": {
                "estabilidad_monetaria": {
                    "peso": 1.0,
                    "puntaje": 60.0,
                    "indicadores": {},
                }
            }
        },
        "indicadores": {},
    }

    publicar._scoring_indice(
        cinturon,
        "itcm",
        itcm,
        publicar.MACRO_CONTEXTO,
        publicar._macro_input_txt,
    )

    assert recibidos["anclas"] == itcm.ANCLAS_ITCM


def test_acumular_historico_purga_indicador_sustituido(monkeypatch, tmp_path):
    historico = tmp_path / "indicadores.json"
    historico.write_text(
        json.dumps({"dolarizacion_depositos": {"2026-06": 29.07}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(publicar, "HISTORICO_PATH", historico)
    informe = {
        "cinturones": {
            "macro": {
                "indicadores": {
                    "presion_dolarizacion": {"valor": 45.24},
                }
            }
        }
    }

    store = publicar.acumular_historico(informe)

    assert "dolarizacion_depositos" not in store
    assert list(store["presion_dolarizacion"].values()) == [45.24]


def test_carry_forward_restaura_sentimiento_digital_ausente_de_trends():
    enriquecido = {"sentimiento_digital": {"valor": None, "fecha_dato": None, "fuente": None}}
    previo = {"sentimiento_digital": {"valor": 5.8, "fecha_dato": "2026-07-08", "fuente": "Google Trends"}}
    resultado = publicar._carry_forward(enriquecido, previo)
    assert resultado["sentimiento_digital"]["valor"] == 5.8
    assert resultado["sentimiento_digital"]["fecha_dato"] == "2026-07-08"


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
    """El 5º cinturón publica SOLO la intención migratoria (ADR-0049): los 3
    proxies iniciales quedan OCULTOS del snapshot (ESPIRITU_OCULTOS, mismo
    criterio ADR-0022/0048 — se siguen cacheando como seguimiento interno) y
    el score publicado es la tensión de ese único indicador."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    esp = informe["cinturones"]["espiritu_epoca"]
    assert set(esp["indicadores"]) == {"indice_intencion_migratoria"}, \
        f"espíritu de época debería publicar solo la intención migratoria: {set(esp['indicadores'])}"
    mig = esp["indicadores"]["indice_intencion_migratoria"]
    assert mig.get("aporte_score") is not None, "intención migratoria sin aporte_score"
    assert abs(mig["aporte_score"] - esp["score"]) <= 0.1
    # la card conserva el contraste de migración real (Componente B, nunca puntúa)
    assert isinstance(mig.get("contexto_duro"), dict)


def test_politica_itcp_reconcilia():
    """Política: la suma ponderada de los puntajes ITCP (peso_efectivo) reproduce
    el ITCP publicado, la tensión del cinturón es (100 − ITCP)/10 y los pesos de
    dimensión son los del ADR-0036 (política es, con esta corrida, el último de
    los 4 cinturones automatizados en pasar de promedio simple a paramétrica)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["politica"]
    assert c.get("itcp"), "política sin bloque itcp"
    itcp_val = c["itcp"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    contexto = {k: i for k, i in c["indicadores"].items() if i.get("en_indice") is False}
    # ADR-0048 (revisión editorial 2026-07-10) + ADR-0052 (2026-07-11): 11
    # indicadores puntúan (la cohesión es UNA card, el compuesto bicameral;
    # conflictividad_nacional reemplaza a movilizacion_cepa en conflicto
    # social). rotacion_gabinete, protestas_caba y movilizacion_cepa quedan
    # OCULTOS del snapshot (POLITICA_OCULTOS, mismo criterio ADR-0022 que
    # los monetarios de macro): se siguen relevando y cacheando, pero el
    # tablero solo muestra lo que integra las dimensiones.
    # cohesion_bloque_senado ya no existe como card (fusionado).
    assert len(en_indice) == 11, f"esperaba 11 indicadores en el índice, hay {len(en_indice)}"
    faltantes = {"votometro_ventaja_lla", "ratio_dnu", "eficacia_legislativa", "veto_quorum",
                 "comisiones_caidas", "iaf_transferencias", "alineamiento_senadores_prov",
                 "adhesion_reformas_provincial", "cohesion_bloque", "conflictividad_nacional",
                 "derrotas_legislativas"} - set(en_indice)
    assert not faltantes, f"faltan indicadores que no deberían faltar: {faltantes}"
    assert contexto == {}, f"política no debería publicar contexto: {set(contexto)}"
    for oculto in ("rotacion_gabinete", "protestas_caba", "movilizacion_cepa",
                   "cohesion_bloque_senado"):
        assert oculto not in c["indicadores"], f"{oculto} debería estar oculto del snapshot"
    # El compuesto expone su composición por cámara (patrón Fondo de Cese)
    assert set(c["indicadores"]["cohesion_bloque"].get("componentes", {})) >= {"diputados"}

    ponderado = sum(i["puntaje_itcp"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcp_val) <= 0.15, f"ponderado {ponderado} != ITCP {itcp_val}"
    assert abs(c["score"] - round((100 - itcp_val) / 10, 1)) <= 0.05

    # Pesos de dimensión (ADR-0036): 30/25/20/15/10.
    pesos = {k: d["peso"] for k, d in c["itcp"]["dimensiones"].items()}
    assert pesos == {"poder_legislativo": 0.30, "alianzas_territoriales": 0.25,
                     "cohesion_interna": 0.20, "conflicto_social": 0.15,
                     "imagen_voto": 0.10}

    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"
        assert abs(i["aporte_score"] - round((100 - i["puntaje_itcp"]) / 10, 1)) <= 0.05


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
    assert len(en_indice) == 13, f"esperaba 13 indicadores en el índice, hay {len(en_indice)}"
    # ADR-0022: los 4 monetarios nominales quedan OCULTOS del snapshot (siguen
    # en pipeline como insumos de IdC/IDM/TCRM); su señal entra vía credito_privado.
    assert contexto == {}, f"macro no debería publicar contexto: {set(contexto)}"
    for oculto in ("badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"):
        assert oculto not in c["indicadores"], f"{oculto} debería estar oculto"
    assert "credito_privado" in en_indice
    presion = en_indice["presion_dolarizacion"]
    assert presion["peso_efectivo"] == 0.026
    assert presion["aporte_input_txt"] == publicar._macro_input_txt(
        "presion_dolarizacion", presion
    )
    series = json.loads((DATA / "series.json").read_text(encoding="utf-8"))
    assert "dolarizacion_depositos" not in series
    serie_presion = series["presion_dolarizacion"]
    assert serie_presion[0]["fecha"][:7] == "2023-12"
    assert serie_presion[-1]["valor"] == presion["valor"]

    ponderado = sum(i["puntaje_itcm"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcm_val) <= 0.15, f"ponderado {ponderado} != ITCM {itcm_val}"
    assert abs(c["score"] - round((100 - itcm_val) / 10, 1)) <= 0.05

    for k, i in contexto.items():
        assert i.get("aporte_score") is None, f"{k} es contexto pero tiene aporte_score"
    for k, i in en_indice.items():
        assert i.get("aporte_score") is not None, f"{k} integra el índice sin aporte_score"
        assert abs(i["aporte_score"] - round((100 - i["puntaje_itcm"]) / 10, 1)) <= 0.05


def test_validacion_itcm_declara_cobertura_vigente():
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    sub = informe["cinturones"]["macro"]["itcm"]["validacion"]["sub"]
    assert "once de sus trece componentes" in sub
    assert "sin el capítulo inversión" not in sub


def test_gestion_itcg_reconcilia():
    """Gestión: la suma ponderada de los puntajes ITCG (peso_efectivo) reproduce
    el ITCG publicado, la tensión del cinturón es (100 − ITCG)/10 y los
    indicadores de contexto no aportan al score. ADR-0023: litigiosidad SRT
    puntúa (resultado de la reforma laboral, 30% de la dimensión)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["gestion"]
    assert c.get("itcg"), "gestión sin bloque itcg"
    itcg_val = c["itcg"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    contexto = {k: i for k, i in c["indicadores"].items() if i.get("en_indice") is False}
    assert len(en_indice) == 15, f"esperaba 15 indicadores en el índice, hay {len(en_indice)}"
    assert "litigiosidad_laboral" in en_indice
    # ADR-0051: los 2 de contexto (alertas_manifestacion, protestas_caba)
    # quedan OCULTOS del snapshot (GESTION_OCULTOS, mismo criterio que
    # ADR-0022/0048/0049) — siguen en pipeline como seguimiento interno.
    assert contexto == {}, f"gestión no debería publicar contexto: {set(contexto)}"
    for oculto in ("alertas_manifestacion", "protestas_caba"):
        assert oculto not in c["indicadores"], f"{oculto} debería estar oculto del snapshot"

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
    reproduce el ITVC publicado y la tensión del cinturón es
    5 − (ITVC−100)×0,2. Desde el ADR-0034 los 13 indicadores puntúan
    (sentimiento digital dejó de ser contexto)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["vida_cotidiana"]
    assert c.get("itvc"), "vida sin bloque itvc"
    itvc_val = c["itvc"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    assert len(en_indice) == 13, f"esperaba 13 componentes en el índice, hay {len(en_indice)}"

    ponderado = sum(i["indice_itvc"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itvc_val) <= 0.2, f"ponderado {ponderado} != ITVC {itvc_val}"
    esperado = round(min(10.0, max(0.0, 5.0 - (itvc_val - 100.0) * 0.2)), 1)
    assert abs(c["score"] - esperado) <= 0.05

    # Los pesos de dimensión del doc 260702 llegan publicados: 35/25/10/15/15.
    pesos = {k: d["peso"] for k, d in c["itvc"]["dimensiones"].items()}
    assert pesos == {"ingresos": 0.35, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "confianza": 0.15}

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


def test_dimensiones_criticas_marcadas():
    """ADR-0020: toda dimensión publicada trae el flag 'critica' según la
    regla (puntaje < 30 en índices por bandas · < 85 en base-100), y las dos
    críticas vigentes conocidas quedan señaladas."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    for ck, clave, umbral in (("macro", "itcm", 30), ("gestion", "itcg", 30),
                              ("vida_cotidiana", "itvc", 85)):
        for dk, d in informe["cinturones"][ck][clave]["dimensiones"].items():
            assert "critica" in d, f"{clave}.{dk}: sin flag critica"
            assert d["critica"] == (d["puntaje"] < umbral), \
                f"{clave}.{dk}: critica={d['critica']} con puntaje {d['puntaje']} (umbral {umbral})"
    assert informe["cinturones"]["gestion"]["itcg"]["dimensiones"]["reforma_laboral"]["critica"]
    assert informe["cinturones"]["vida_cotidiana"]["itvc"]["dimensiones"]["vulnerabilidad"]["critica"]


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
