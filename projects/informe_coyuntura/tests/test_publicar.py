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


def test_publicar_no_toca_el_arbol_cuando_se_le_redirige_la_salida(tmp_path):
    """El guardián de ADR-0178: si alguien saca el redirect, esto lo caza acá y
    no tres archivos de test más adelante como una falla incomprensible."""
    import hashlib

    vigilados = [DATA / "informe.json", DATA / "series.json",
                 ROOT / "data" / "historico" / "indicadores.json"]
    antes = {p: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in vigilados if p.exists()}
    assert antes, "no hay snapshot publicado contra el cual comparar"

    salida = tmp_path / "data"
    salida.mkdir()
    for p in vigilados:
        if p.exists():
            (salida / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    subprocess.run([sys.executable, "scripts/publicar.py"], cwd=ROOT, check=True,
                   env={**os.environ, "CIGOB_SALIDA_WEB": str(salida)})

    movidos = [p.name for p, h in antes.items()
               if hashlib.sha256(p.read_bytes()).hexdigest() != h]
    assert not movidos, (
        f"publicar.py escribió en el árbol pese al redirect: {movidos}. "
        f"Los tests que corran después van a leer esto en vez del snapshot "
        f"publicado (ADR-0178).")
    assert (salida / "informe.json").exists(), "tampoco escribió donde se le pidió"


def test_publicar_genera_snapshot(tmp_path):
    """Corre publicar.py de verdad, pero FUERA del árbol (ADR-0178).

    Hasta el 5-ago-2026 escribía sobre web/src/data/ y data/historico/, así que
    los tests posteriores —de este archivo y de otros— leían lo que este había
    dejado en vez del snapshot publicado. Con el snapshot desactualizado, el
    gate veía diez fallas G3 fantasma y test_macro_itcm_reconcilia y
    test_puntaje_unico_camino pasaban solos y fallaban en conjunto.

    El temporal se SIEMBRA con el snapshot y el histórico vigentes: publicar.py
    los lee para el carry-forward, y con el directorio vacío el test estaría
    ejercitando un camino (primera corrida, sin previo) que no es el real."""
    salida = tmp_path / "data"
    salida.mkdir()
    for origen, destino in ((DATA / "informe.json", "informe.json"),
                            (DATA / "series.json", "series.json"),
                            (ROOT / "data" / "historico" / "indicadores.json",
                             "indicadores.json")):
        if origen.exists():
            (salida / destino).write_text(origen.read_text(encoding="utf-8"),
                                          encoding="utf-8")

    entorno = {**os.environ, "CIGOB_SALIDA_WEB": str(salida)}
    subprocess.run([sys.executable, "scripts/publicar.py"], cwd=ROOT,
                   check=True, env=entorno)
    informe = json.loads((salida / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((salida / "series.json").read_text(encoding="utf-8"))

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
    # ADR-0048 (revisión editorial 2026-07-10) + ADR-0052 (2026-07-11) +
    # ADR-0069 (2026-07-16): 11 indicadores puntúan (la cohesión es UNA card,
    # el compuesto bicameral; conflictividad_nacional reemplaza a
    # movilizacion_cepa en conflicto social; bloqueo_sostenido entra a poder
    # legislativo como la cara ganada del pulso que derrotas no acredita).
    # rotacion_gabinete, protestas_caba, movilizacion_cepa y
    # comisiones_caidas (ADR-0064) quedan OCULTOS del snapshot
    # (POLITICA_OCULTOS, mismo criterio ADR-0022 que los monetarios de
    # macro): se siguen relevando y cacheando, pero el tablero solo muestra
    # lo que integra las dimensiones.
    # cohesion_bloque_senado ya no existe como card (fusionado).
    # ADR-0088 (2026-07-19): entra brecha_obra_publica en la dimensión nueva
    # sector_privado — el único actor del objetivo declarado que no tenía
    # ningún indicador propio.
    # 13 desde 2026-07-25 (ADR-0126: entra cobertura_judicial con la dimensión
    # nueva del Poder Judicial, el otro actor de veto que no se medía).
    # 14 desde 2026-07-27 (ADR-0150): entra apoyo_empresario y sector_privado
    # deja de tener un solo indicador — lo que ADR-0088 había dejado anotado
    # como pendiente al crear la dimensión.
    # 18 desde 2026-07-31 (ADR-0168): entran los cuatro que ADR-0166 desbloqueó
    # al fijar la orientación — produccion_legislativa al bloque legislativo y
    # judicializacion, velocidad_resolucion y paralisis_denuncias al judicial,
    # que deja de colgar de un solo dato.
    assert len(en_indice) == 18, f"esperaba 18 indicadores en el índice, hay {len(en_indice)}"
    for _nuevo in ("produccion_legislativa", "judicializacion",
                   "velocidad_resolucion", "paralisis_denuncias"):
        assert _nuevo in en_indice, f"{_nuevo} tendría que puntuar (ADR-0168)"
    assert "bloqueo_sostenido" in en_indice
    assert "apoyo_empresario" in en_indice
    assert "brecha_obra_publica" in en_indice
    # ADR-0089: derrotas sale del índice, entra desafíos en su lugar
    assert "desafios_legislativos" in en_indice
    assert "derrotas_legislativas" not in en_indice
    faltantes = {"votometro_ventaja_lla", "ratio_dnu", "eficacia_legislativa", "veto_quorum",
                 "iaf_transferencias", "alineamiento_senadores_prov",
                 "adhesion_reformas_provincial", "cohesion_bloque", "conflictividad_nacional",
                 "desafios_legislativos"} - set(en_indice)
    assert not faltantes, f"faltan indicadores que no deberían faltar: {faltantes}"
    assert contexto == {}, f"política no debería publicar contexto: {set(contexto)}"
    for oculto in ("rotacion_gabinete", "protestas_caba", "movilizacion_cepa",
                   "comisiones_caidas", "cohesion_bloque_senado", "derrotas_legislativas"):
        assert oculto not in c["indicadores"], f"{oculto} debería estar oculto del snapshot"
    # El compuesto expone su composición por cámara (patrón Fondo de Cese)
    assert set(c["indicadores"]["cohesion_bloque"].get("componentes", {})) >= {"diputados"}

    ponderado = sum(i["puntaje_itcp"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itcp_val) <= 0.15, f"ponderado {ponderado} != ITCP {itcp_val}"
    assert abs(c["score"] - round((100 - itcp_val) / 10, 1)) <= 0.05

    # Pesos de dimensión: 30/25/20/15/10 desde ADR-0036, reponderados a
    # 25/22/18/12/8 + 15 el 2026-07-19 (ADR-0088) al incorporarse el sector
    # privado, y a 21/19/15/10/7 + 13 + 15 el 2026-07-25 (ADR-0126) al
    # incorporarse el Poder Judicial. En los dos casos las dimensiones previas
    # cedieron PROPORCIONALMENTE, de modo que su orden relativo se conserva.
    pesos = {k: d["peso"] for k, d in c["itcp"]["dimensiones"].items()}
    assert pesos == {"poder_legislativo": 0.21, "alianzas_territoriales": 0.19,
                     "cohesion_interna": 0.15, "conflicto_social": 0.10,
                     "imagen_voto": 0.07, "sector_privado": 0.13,
                     "poder_judicial": 0.15}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9

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
    # 17 desde 2026-07-25 (ADR-0124: entra emae_difusion a la dimensión actividad).
    assert len(en_indice) == 17, f"esperaba 17 indicadores en el índice, hay {len(en_indice)}"
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
    itcm_bloque = informe["cinturones"]["macro"]["itcm"]
    sub = itcm_bloque["validacion"]["sub"]
    # El recuento se DERIVA de la composición vigente: escrito a mano quedaba
    # viejo con cada indicador nuevo (pasó al entrar costo_financiamiento_tesoro,
    # cuando el texto seguía diciendo "once de sus trece").
    total = sum(len(d["indicadores"]) for d in itcm_bloque["dimensiones"].values())
    usados = total - 2                      # IAI e ICIP no entran a la reconstrucción
    assert f"{usados} de sus {total} componentes" in sub, sub
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
    # ADR-0189: todo lo que gestión publica, puntúa. Son 14 — los 13 que ya
    # puntuaban más `asistencia_directa`, que vuelve al cálculo: el ITCG mide
    # avance de propuestas y un índice de avance no puede descartar las
    # cumplidas. `masa_salarial` sigue sin puntuar (duda metodológica sin
    # saldar, ADR-0186) y por eso ahora tampoco se publica.
    assert len(en_indice) == 14, f"esperaba 14 indicadores en el índice, hay {len(en_indice)}"
    assert contexto == {}, ("gestión no publica indicadores que no puntúen: "
                            f"{sorted(contexto)}")
    assert len(c["indicadores"]) == 14, "el snapshot no debe traer cards sin puntaje"
    assert "asistencia_directa" in en_indice, "la promesa cumplida puntúa (ADR-0189)"
    assert "litigiosidad_laboral" in en_indice
    # Los cuatro que no puntúan quedan OCULTOS del snapshot (GESTION_OCULTOS):
    # los 2 de contexto por ADR-0051, y la promesa cumplida y el suspendido por
    # ADR-0189. Nada de esto deja de medirse — colector, stores y series siguen
    # corriendo como seguimiento interno, y las razones de no puntuar siguen
    # documentadas en itcg.INDICADORES_{CONTEXTO,CUMPLIDOS,SUSPENDIDOS}.
    for oculto in ("alertas_manifestacion", "protestas_caba", "masa_salarial"):
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
    5 − (ITVC−100)×0,2. Desde el ADR-0034 todos los indicadores puntúan
    (sentimiento digital dejó de ser contexto); desde el ADR-0067 son 14
    (la mora salió del compuesto de endeudamiento como indicador propio)."""
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    c = informe["cinturones"]["vida_cotidiana"]
    assert c.get("itvc"), "vida sin bloque itvc"
    itvc_val = c["itvc"]["valor"]

    en_indice = {k: i for k, i in c["indicadores"].items() if i.get("en_indice")}
    # 16: ADR-0111 sumó alquiler_real a precios y ADR-0112 indice_lider a
    # empleo. El conteo exacto es deliberado: es el guard que en su momento
    # detectó a sentimiento_digital desapareciendo del snapshot sin que nada
    # más fallara.
    # 17 desde 2026-07-25 (ADR-0130: entra empleo_registrado, el único
    # componente de la dimensión de empleo que mide empleo).
    # 18 desde 2026-07-30 (ADR-0153: entra pobreza_nowcast a la dimensión de
    # ingresos; era una card visible que no puntuaba, patrón dado de baja).
    # 16 el mismo día (ADR-0154: salen endeudamiento_familiar e indice_lider).
    assert len(en_indice) == 16, f"esperaba 16 componentes en el índice, hay {len(en_indice)}"

    ponderado = sum(i["indice_itvc"] * i["peso_efectivo"] for i in en_indice.values())
    assert abs(ponderado - itvc_val) <= 0.2, f"ponderado {ponderado} != ITVC {itvc_val}"
    esperado = round(min(10.0, max(0.0, 5.0 - (itvc_val - 100.0) * 0.2)), 1)
    assert abs(c["score"] - esperado) <= 0.05

    # Los pesos de dimensión llegan publicados. Ya no son los 35/25/10/15/15 del
    # doc 260702: ADR-0115 partió la dimensión de confianza en percepción y
    # seguridad y mudó consumo a ingresos, repartiendo los pesos nominales de
    # modo que el peso EFECTIVO de cada indicador quedara idéntico.
    pesos = {k: d["peso"] for k, d in c["itvc"]["dimensiones"].items()}
    assert pesos == {"ingresos": 0.3725, "precios": 0.25, "vulnerabilidad": 0.10,
                     "empleo": 0.15, "percepcion": 0.0825, "seguridad": 0.045}
    assert abs(sum(pesos.values()) - 1.0) < 1e-9

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
    # reforma_laboral salió de "crítica" el 2026-07-20 (ADR-0098) y volvió a
    # subir el 2026-07-26 (ADR-0142), en los dos casos SIN QUE CAMBIARA LA
    # REALIDAD: primero el FAL pasó a medirse en tres etapas (10 → 30,8) y
    # después a medir sus dos actos fundamentales (30,8 → 100), con lo que la
    # dimensión fue de ~39 a 79,7. El umbral de 30 no se movió en ninguno de
    # los dos casos —mismo criterio que ADR-0045 con las anclas—: lo que se
    # movió fue el indicador, por decisión editorial y declarada.
    laboral = informe["cinturones"]["gestion"]["itcg"]["dimensiones"]["reforma_laboral"]
    assert not laboral["critica"], "reforma_laboral no debería estar marcada crítica con la escala nueva"
    assert informe["cinturones"]["vida_cotidiana"]["itvc"]["dimensiones"]["vulnerabilidad"]["critica"]


def test_la_mora_sostiene_sola_la_vulnerabilidad():
    """Vulnerabilidad (D3 del ITVC) después de ADR-0154.

    ADR-0067 había separado la mora del compuesto I_EC y las dejó 50/50 con el
    endeudamiento, declarando el reparto como provisorio. ADR-0154 saca el
    endeudamiento —redundante (+0,943 con la brecha salarial), clavado en el
    techo de winsorización y de signo equívoco, porque leía el crecimiento de la
    deuda real como acceso al crédito— y la mora queda sola.

    Este test cuida las dos mitades: que el endeudamiento NO se publique como
    card (patrón de ocultos, no card de contexto) y que la mora siga siendo la
    card cuyo titular ES el último punto de su serie.
    """
    informe = json.loads((DATA / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((DATA / "series.json").read_text(encoding="utf-8"))
    vida = informe["cinturones"]["vida_cotidiana"]["indicadores"]

    assert "endeudamiento_familiar" not in vida, (
        "endeudamiento salió del ITVC: va a los ocultos del snapshot, no se "
        "publica como card sin puntuar"
    )
    assert "indice_lider" not in vida, "el índice líder también salió (ADR-0154)"
    # la serie sigue viva: es seguimiento interno, y la del líder además es
    # insumo del validador externo del ITCM
    assert series.get("itvc_endeudamiento"), "la serie de endeudamiento no debe borrarse"
    assert series.get("indice_lider"), "la serie del líder es insumo de validacion_externa"

    mora = vida.get("mora_familias")
    assert mora, "falta la card de mora_familias"
    serie_mora = series.get("mora_familias") or []
    assert serie_mora, "falta la serie mora_familias"
    assert mora["valor"] == serie_mora[-1]["valor"]   # titular = último punto
    assert mora.get("en_indice"), "la mora debe puntuar en el ITVC"
    assert mora.get("indice_itvc") is not None

    dim = informe["cinturones"]["vida_cotidiana"]["itvc"]["dimensiones"]["vulnerabilidad"]
    assert set(dim["indicadores"]) == {"mora_familias"}
    assert dim["indicadores"]["mora_familias"]["peso"] == 1.0
    # el puntaje de la dimensión ES el índice de la mora, sin promedio que lo suavice
    assert abs(dim["puntaje"] - dim["indicadores"]["mora_familias"]["puntaje_aplicado"]) <= 0.05

def test_la_card_de_consistencia_se_publica_aunque_no_haya_pares_altos(monkeypatch, tmp_path):
    """Bug de la auditoría de código: _redundancia_itcm hacía return si
    pares_altos estaba vacío, así que la sección desaparecía justo cuando tenía
    la mejor noticia para dar — 'ningún par se mueve al unísono' es un
    resultado positivo, no la ausencia de resultado."""
    import json as _json
    import publicar as _pub

    archivo = tmp_path / "validacion_externa.json"
    archivo.write_text(_json.dumps({"redundancia_itcm": {
        "umbral": 0.7, "n_indicadores": 14, "n_pares": 91,
        "r_abs_medio": 0.21, "share_altos": 0.0, "share_bajos": 0.62,
        "matriz": {}, "pares_altos": [], "pares_cruzados": 0,
    }}), encoding="utf-8")
    monkeypatch.setattr(_pub, "VALIDACION_EXTERNA_PATH", archivo)

    bloque = {}
    _pub._redundancia_itcm(bloque)

    assert "redundancia" in bloque, "la card no se publicó sin pares altos"
    assert bloque["redundancia"]["top"] == []
    assert "Ningún par supera el umbral" in bloque["redundancia"]["conclusion"]


def test_familias_no_ordenan_empates():
    """La card de lectura por partes llegó a afirmar que «lo más flojo del
    cinturón es tensión externa (63,2)» con capacidad propia en 63,5: tres
    décimas presentadas como hallazgo (ADR-0171). El guard que existía comparaba
    el peor contra el MEJOR —brecha 11,7, pasaba— y no veía el empate de abajo.
    """
    snap = json.loads((ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    for ckey, cin in snap.get("cinturones", {}).items():
        for bloque in cin.values():
            if not isinstance(bloque, dict):
                continue
            fam = bloque.get("familias")
            if not fam or len(fam.get("familias", [])) < 3:
                continue
            orden = sorted(fam["familias"], key=lambda f: f["puntaje"])
            hueco = round(orden[1]["puntaje"] - orden[0]["puntaje"], 1)
            texto = fam.get("conclusion", "")
            if hueco < 2.0:
                assert "empatad" in texto, (
                    f"{ckey}: las dos familias más flojas difieren {hueco} puntos "
                    f"({orden[0]['nombre']} {orden[0]['puntaje']} vs "
                    f"{orden[1]['nombre']} {orden[1]['puntaje']}) y la card las ordena: "
                    f"«{texto[:120]}…»")
            else:
                assert "lo más flojo" in texto, (
                    f"{ckey}: hay una diferencia real de {hueco} puntos y la card "
                    "no la nombra")
