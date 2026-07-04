"""Arma el snapshot de datos que consume la web del informe de coyuntura.

Lee output/informe.json + el ultimo vida_cotidiana_*.json + output/series/*.csv
y escribe web/src/data/informe.json (con vida cotidiana enriquecido a ~13
indicadores automaticos) y web/src/data/series.json.
"""
import csv, glob, json, os, re, statistics, sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]          # projects/informe_coyuntura
OUT = ROOT / "output"
DATA = ROOT / "web" / "src" / "data"
DATA.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from config import PESOS_CINTURONES, UMBRALES        # pesos y umbrales del informe
import itcm                                           # bandas y pesos del ITCM macro
import itcg                                           # bandas y pesos del ITCG gestión
import itvc                                           # pesos y rebase del ITVC vida cotidiana
import sensibilidad                                   # rango de robustez (ADR-0019)


def _add(out, key, valor, unidad, fuente, fecha, **extra):
    d = {"valor": valor, "unidad": unidad, "fuente": fuente,
         "fecha_dato": fecha, "desactualizado": False}
    d.update(extra)
    out[key] = d


def build_vida(raw):
    """Mapea el JSON crudo (por fuente) a indicadores estilo informe.json."""
    indec = raw.get("indec", {}); bcra = raw.get("bcra", {})
    utdt = raw.get("utdt", {}); cafam = raw.get("cafam", {})
    ciccra = raw.get("ciccra", {}); snic = raw.get("snic", {})
    trends = raw.get("trends", {})
    ts = raw.get("metadata", {}).get("timestamp", "")[:10]
    out = {}

    bs = indec.get("brecha_salario_cbt", {})
    _add(out, "brecha_salario_cbt", round(bs.get("valor", 0), 2),
         "canastas (RIPTE/CBT)", "Sec. Trabajo (RIPTE) + INDEC (CBT)", bs.get("fecha"),
         detalle_txt=bs.get("nota"))
    al = indec.get("ipc_alimentos", {})
    _add(out, "ipc_alimentos", round(al.get("variacion_mensual_pct", 0), 2),
         "% m/m", "INDEC — IPC alimentos y bebidas (vía datos.gob.ar)", al.get("fecha"))
    cc = bcra.get("credito_consumo_total", {})
    # El crédito de consumo viene en millones de pesos; pasar a billones para
    # que el número no sea gigante (43.560.544 millones = 43,56 billones).
    cc_val = cc.get("valor")
    _add(out, "endeudamiento_familiar",
         round(cc_val / 1e6, 2) if isinstance(cc_val, (int, float)) else cc_val,
         "billones de pesos (consumo)",
         "BCRA — crédito de consumo (API) + Informe sobre Bancos (mora)", cc.get("fecha"))
    reg = indec.get("ipc_regulados", {})
    _add(out, "peso_tarifas", round(reg.get("variacion_mensual_pct", 0), 2),
         "% m/m regulados", "INDEC — IPC precios regulados (vía datos.gob.ar)", reg.get("fecha"))
    carne = ciccra.get("consumo_carne_per_capita", {})
    _add(out, "consumo_carne", carne.get("valor"),
         "kg/hab/año", "CICCRA", carne.get("fecha"))
    inf = indec.get("informalidad_trimestral") or indec.get("informalidad_anual", {})
    _add(out, "informalidad", round(inf.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", inf.get("fecha"))
    ipi = indec.get("ipi", {})
    _add(out, "mortalidad_pymes", round(ipi.get("variacion_mensual_pct", 0), 2),
         "% m/m (IPI desest.)", "INDEC — IPI manufacturero desestacionalizado (vía datos.gob.ar)",
         ipi.get("fecha"))
    isac = indec.get("isac", {})
    _add(out, "despacho_cemento", round(isac.get("valor", 0), 1),
         "índice ISAC", "INDEC — ISAC desestacionalizado (vía datos.gob.ar)", isac.get("fecha"))
    sub = indec.get("subocupacion_demandante", {})
    _add(out, "pluriempleo", round(sub.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", sub.get("fecha"))
    seg = snic.get("inseguridad_snic", {})
    _add(out, "inseguridad", seg.get("total_hechos"),
         "hechos/año", "SNIC — Ministerio de Seguridad (calidad UNODC grado A)",
         str(seg.get("anio")))
    icc = utdt.get("icc_utdt", {})
    _add(out, "icc_utdt", round(icc.get("valor", 0), 1),
         "índice", "UTDT — Índice de Confianza del Consumidor (CIF)", icc.get("fecha"))
    sd = trends.get("sentimiento_digital", {}).get("interes_relativo", {})
    if sd:
        _add(out, "sentimiento_digital", round(sum(sd.values()) / len(sd), 1),
             "interés 0–100", "Google Trends", ts,
             detalle_txt=("El titular es el pulso de los últimos 3 meses (escala relativa "
                          "de esa ventana). El gráfico y el puntaje del ITVC usan la "
                          "canasta mensual de ventana fija desde 2021, cuyo cociente "
                          "contra el 4T-2023 es inmune a la renormalización de Trends."))
    motos = cafam.get("patentamiento_motos", {})
    _add(out, "patentamiento_motos", motos.get("valor"),
         "unidades", "CAFAM", motos.get("fecha"))
    return out


def build_series():
    """Agrupa output/series/*.csv en {indicador: [{fecha, valor}, ...]} asc."""
    series = {}
    for csv_path in sorted(glob.glob(str(OUT / "series" / "*.csv"))):
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ind = row["indicador"]
                try:
                    val = float(row["valor"])
                except (TypeError, ValueError):
                    continue
                series.setdefault(ind, []).append({"fecha": row["fecha"], "valor": val})
    for ind in series:
        # Deduplicar por fecha: si un indicador aparece en más de un CSV de
        # cinturón con la MISMA métrica, colapsar a un punto por fecha. (Las
        # métricas distintas van bajo claves distintas — ej. ipc_total en % m/m
        # vs ipc_nivel como insumo deflactor.)
        por_fecha = {p["fecha"]: p for p in series[ind]}
        series[ind] = sorted(por_fecha.values(), key=lambda p: p["fecha"])
    # Alias: algunos indicadores del informe tienen su serie historica bajo otra
    # clave en los CSV. Exponer la serie tambien bajo la clave del indicador para
    # que el sparkline y el modal la encuentren.
    alias = {
        "despacho_cemento": "isac_construccion",
        "saldo_comercial_12m": "saldo_comercial",
        "clima_electoral": "votometro_ventaja_lla",   # espíritu reusa la serie del Votómetro
    }
    for ind_key, serie_key in alias.items():
        if serie_key in series and ind_key not in series:
            series[ind_key] = series[serie_key]
    return series


# Histórico acumulado: red de seguridad para NO PERDER DATOS. Cada corrida persiste
# el valor actual de todos los indicadores keyed por mes; los que no tienen serie
# oficial (política, vida sin fuente, espíritu, avances de gestión) construyen así
# su serie temporal mes a mes.
HISTORICO_PATH = ROOT / "data" / "historico" / "indicadores.json"


def _valor_historico(ind):
    """Número a persistir de un indicador: el avance si es reforma; si no, el valor."""
    v = ind.get("avance_pct")
    if not isinstance(v, (int, float)):
        v = ind.get("valor")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def acumular_historico(informe):
    """Upserta el valor actual de CADA indicador en data/historico/indicadores.json,
    keyed por mes (YYYY-MM). Aunque la fuente no publique serie, el histórico se va
    armando solo y no se pierde ningún dato."""
    store = {}
    if HISTORICO_PATH.exists():
        store = json.loads(HISTORICO_PATH.read_text(encoding="utf-8"))
    ym = datetime.now().strftime("%Y-%m")
    for c in informe["cinturones"].values():
        for ik, ind in c["indicadores"].items():
            v = _valor_historico(ind)
            if v is not None:
                store.setdefault(ik, {})[ym] = round(v, 4)
    HISTORICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORICO_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return store


def fusionar_historico(series, store):
    """Inyecta el histórico acumulado como serie de los indicadores que NO tienen
    serie oficial (o tienen <2 puntos). No pisa las oficiales (macro, etc.), que
    traen más historia y otra métrica (ej. IPC: el oficial es el índice nivel, no
    la variación). Nota: inseguridad pasó a mensual (IVI, ADR-0032) con store
    persistente propio — el viejo bug del fallback anual (totales con fecha de
    corrida durante el apagón SNIC del 04-jul-2026) ya no aplica."""
    for ik, meses in store.items():
        if len(series.get(ik, [])) >= 2:
            continue
        puntos = [{"fecha": f"{ym}-01", "valor": v} for ym, v in sorted(meses.items())]
        if puntos:
            series[ik] = puntos
    return series


_LOCAL_PATH = re.compile(r"^[A-Za-z]:[\\/]|[\\/]Users[\\/]|\\\\")


def sanitizar_fuentes(informe):
    """Reemplaza rutas locales del filesystem en los campos `fuente` para no
    filtrar paths del equipo en el snapshot publico ni en la lista de fuentes."""
    for cint in informe["cinturones"].values():
        for key, ind in cint["indicadores"].items():
            fuente = ind.get("fuente")
            if isinstance(fuente, str) and _LOCAL_PATH.search(fuente):
                ind["fuente"] = ("Votómetro CIGOB" if "votometro" in key.lower()
                                 else "Elaboración propia — CIGOB")
    return informe


# ── Aporte al score por indicador ──────────────────────────────────────────────
# Fuente única de verdad de la transparencia del scoring: replica EXACTAMENTE las
# fórmulas de tensión documentadas en los colectores (macro.py, politica.py,
# gestion.py). El texto de mapeo viene verbatim de esas docstrings. Un test de
# reconciliación (tests/test_publicar.py) verifica que el promedio de los aportes
# reproduce el score publicado de cada cinturón — si una fórmula cambia, el test
# avisa y esto deja de ser una caja negra.

def _clamp10(x):
    return round(max(0.0, min(10.0, x)), 1)

# Población usada para pasar conteos absolutos a tasa por 100.000 hab (INDEC 2024).
POB_AR = 46_700_000

# clave de indicador → (valor → tensión 0–10, texto de mapeo de referencia)
# Los indicadores macro NO están acá: su puntaje viene del ITCM calculado por
# el colector (macro.py + itcm.py) y se traduce en aplicar_scoring().
SCORING = {
    # ── política ──
    "votometro_ventaja_lla":     (lambda v: 5 - v / 3,          "+15pp → 0 · 0 → 5 · −15pp → 10 (gap LLA−PJ)"),
    "ratio_dnu":                 (lambda v: v * 5,              "0 → 0 · 1,0 → 5 · 2,0+ → 10 (DNU/leyes)"),
    "movilizacion_cepa":         (lambda v: v / 10,             "0 → 0 · 50 → 5 · 100 → 10 (índice)"),
    "iaf_transferencias":        (lambda v: (0.10 - v / 100) * 25, "+10% → 0 · 0% → 2,5 · −10% → 5 · −30% → 10 (var. real i.a.)"),
    "eficacia_legislativa":      (lambda v: (70 - v) / 7,       "70% → 0 · 35% → 5 · 0% → 10"),
    "cohesion_bloque":           (lambda v: (95 - v) / 7,       "95% → 0 · 60% → 5 · 25% → 10"),
    "gobernadores_alineamiento": (lambda v: (80 - v) / 8,       "80% → 0 · 40% → 5 · 0% → 10"),
    "veto_quorum":               (lambda v: v / 3,              "0% → 0 · 15% → 5 · 30%+ → 10 (sesiones caídas)"),
    "comisiones_caidas":         (lambda v: (v - 20) / 4,       "20% → 0 · 40% → 5 · 60%+ → 10"),
    # ── vida cotidiana ── (metodología CIGOB validada may-2026; anclas de dominio)
    "ipc_alimentos":       (lambda v: v,                "0% → 0 · 5% → 5 · 10% → 10 (mensual)"),
    "peso_tarifas":        (lambda v: v,                "0% → 0 · 5% → 5 · 10% → 10 (regulados, m/m)"),
    "brecha_salario_cbt":  (lambda v: (4 - v) * 10 / 3, "4 canastas → 0 · 2,5 → 5 · 1 → 10 (salario formal / CBT)"),
    "consumo_carne":       (lambda v: (55 - v) / 2,     "55 → 0 · 45 → 5 · 35 → 10 (kg/hab/año)"),
    "informalidad":        (lambda v: (v - 25) / 2.5,   "25% → 0 · 37,5% → 5 · 50% → 10"),
    "mortalidad_pymes":    (lambda v: 5 - v,            "+5% → 0 · 0% → 5 · −5% → 10 (IPI m/m)"),
    "despacho_cemento":    (lambda v: (180 - v) / 10,   "180 → 0 · 130 → 5 · 80 → 10 (índice ISAC)"),
    "pluriempleo":         (lambda v: v - 5,            "5% → 0 · 10% → 5 · 15% → 10 (subocupación demandante)"),
    "patentamiento_motos": (lambda v: (70_000 - v) / 5000, "70.000 → 0 · 45.000 → 5 · 20.000 → 10 (unidades/mes)"),
    "icc_utdt":            (lambda v: (60 - v) / 3,     "60 → 0 · 45 → 5 · 30 → 10 (índice de confianza)"),
    # ── espíritu de época ── (comparte icc_utdt y sentimiento_digital con vida)
    "clima_electoral":     (lambda v: 5 - v / 3,        "+15pp → 0 · 0 → 5 · −15pp → 10 (gap LLA−PJ, Votómetro)"),
    "sentimiento_digital": (lambda v: v / 10,           "0 → 0 · 50 → 5 · 100 → 10 (interés en inflación/precios/inseguridad/trabajo: mayor = más preocupación)"),
    "inseguridad":         (lambda v: (v / POB_AR * 100_000 - 3000) / 400,
                                                        "tasa/100k hab (pob. 46,7M): 3.000 → 0 · 5.000 → 5 · 7.000 → 10"),
    # Se puntúa sobre la variación interanual REAL (deflactada), no el stock nominal.
    "endeudamiento_familiar": (lambda v: 5 + v / 4,     "−20% real → 0 · 0% → 5 · +20% real → 10 (var. interanual real del crédito)", "var_real_12m"),
}

VIDA_CONTEXTO = ("Indicador de contexto — no integra el ITVC (paramétrica CIGOB jul-2026) "
                 "o su componente no pudo calcularse en esta corrida.")

MACRO_CONTEXTO = "Indicador de contexto — no integra el ITCM (paramétrica CIGOB may-2026)."
GESTION_CONTEXTO = "Indicador de contexto — no integra el ITCG (paramétrica CIGOB jul-2026)."

SCORE_EXPLICACION = {
    "macro":          ("ITCM (índice paramétrico 0–100, mayor = menos tensión) ponderado por 6 dimensiones: "
                       "estabilidad monetaria 26%, viabilidad fiscal-comercial 24%, financiamiento 16%, "
                       "actividad 11%, competitividad externa 11%, inversión 12%. La tensión del cinturón es (100 − ITCM) / 10."),
    "politica":       "Promedio simple de la tensión (0–10) de sus indicadores. Mayor = más tensión en el capital político.",
    "gestion":        ("ITCG (índice paramétrico 0–100, mayor = agenda de reformas ejecutándose) ponderado por 5 dimensiones: "
                       "reformas económicas 35%, reforma del Estado 25%, reforma laboral 15%, "
                       "privatizaciones e inversión 15%, reforma social y orden 10%. La tensión del cinturón es (100 − ITCG) / 10."),
    "vida_cotidiana": ("ITVC-B100 (índice de seguimiento, 100 = promedio del 4T-2023; mayor = mejora acumulada de la vida "
                       "cotidiana) ponderado por 5 dimensiones: ingresos 35%, precios 25%, vulnerabilidad financiera 10%, "
                       "empleo 15%, confianza y seguridad 15%. La tensión del cinturón es 5 − (ITVC − 100) × 0,2."),
    "espiritu_epoca": ("Promedio simple de la tensión (0–10) de sus proxies (v1 provisional). "
                       "Mayor = más desconexión entre el gobierno y el humor social."),
}


def _estado(score):
    """Réplica de generar_informe._estado: traduce el score 0–10 a estado."""
    if score <= UMBRALES["ESTABLE_MAX"]:
        return "estable"
    if score <= UMBRALES["EN_TENSION_MAX"]:
        return "en_tension"
    return "tensionado"


def recomputar_vida_y_global(informe):
    """Vida cotidiana se puntúa con el ITVC-B100 calculado en aplicar_scoring
    (el colector vida_cotidiana.py sigue emitiendo su score legacy en el cache;
    esta es la fuente de verdad del snapshot publicado). Acá solo se recalcula
    el score global ponderado para que el snapshot sea internamente coherente."""
    num = sum(c["score"] * PESOS_CINTURONES.get(k, 0.0)
              for k, c in informe["cinturones"].items())
    den = sum(PESOS_CINTURONES.get(k, 0.0) for k in informe["cinturones"])
    if den:
        informe["score_global"] = round(num / den, 1)
    return informe


# Umbral de dimensión CRÍTICA (ADR-0020): la agregación lineal compensa entre
# dimensiones; por debajo del umbral la dimensión se marca explícitamente como
# "no compensada" — señal visible en la web, sin tocar la fórmula.
UMBRAL_CRITICO_BANDAS = 30.0    # índices 0-100 por bandas: la peor banda
UMBRAL_CRITICO_BASE100 = 85.0   # base-100: "deterioro sustancial" (escala del doc)


def _marcar_dimensiones_criticas(bloque, umbral):
    for dim in (bloque or {}).get("dimensiones", {}).values():
        dim["critica"] = dim["puntaje"] < umbral


def _scoring_indice(c, clave, mod, contexto_txt, input_txt_fn):
    """Cinturones con índice paramétrico (macro → ITCM, gestión → ITCG): el
    puntaje lo computa el colector; acá solo se traduce cada puntaje 0-100 a
    tensión equivalente (para la semántica 0-10 del modal) y se anota la tabla
    de bandas + peso en el índice. Los indicadores con en_indice=false son
    contexto y no aportan."""
    ajustes = {a["indicador"]: a for a in (c.get(clave) or {}).get("ajustes_aplicados", [])}
    sigla = clave.upper()
    # Rango de robustez (ADR-0019): pesos ±20% + bandas vecinas, MC con semilla
    # fija → p05-p95 publicado junto al valor puntual del índice.
    bloque = c.get(clave)
    if bloque and bloque.get("dimensiones"):
        try:
            bloque["robustez"] = sensibilidad.robustez_compacta(
                bloque, getattr(mod, f"BANDAS_{sigla}"),
                lambda v: round((100 - v) / 10, 1))
        except Exception as e:
            print(f"[WARN] robustez {sigla}: {e}")
        _marcar_dimensiones_criticas(bloque, UMBRAL_CRITICO_BANDAS)
    for ikey, ind in c["indicadores"].items():
        aporte = formula = nota = None
        p = ind.get(f"puntaje_{clave}")
        if ind.get("en_indice") and isinstance(p, (int, float)):
            aporte = round((100 - p) / 10, 1)
            peso = ind.get("peso_efectivo")
            peso_txt = f"; pesa {peso * 100:.1f}%".replace(".", ",") + f" del {sigla}" if peso else ""
            formula = (f"Anclas {sigla}: {mod.texto_bandas(ikey)} "
                       f"(puntaje interpolado entre anclas: {p}{peso_txt})")
            if ikey in ajustes:
                aj = ajustes[ikey]
                origen = "automático" if aj.get("origen") == "automatico" else "del analista"
                nota = f"Ajuste {origen}: banda {aj['de']} → {aj['a']}. {aj.get('justificacion', '')}"
        elif ind.get("en_indice") is False:
            nota = contexto_txt
        ind["aporte_score"] = aporte
        ind["aporte_formula"] = formula
        ind["aporte_nota"] = nota
        ind["aporte_input_txt"] = input_txt_fn(ikey, ind)


def _macro_input_txt(ikey, ind):
    """'Valor usado' que muestra el modal: la descomposición del número que
    realmente se puntúa (no siempre coincide con el valor mostrado)."""
    coma = lambda x: str(x).replace(".", ",")    # decimal es-AR, sin tocar el resto
    if ikey == "rem_ipc_12m" and ind.get("equivalente_mensual") is not None:
        return (f"equiv. mensual {coma(ind['equivalente_mensual'])}% "
                f"(raíz-12 del {coma(ind.get('valor'))}% anual)")
    if ikey == "reservas_bcra" and ind.get("netas_sdds_estricto") is not None:
        return (f"netas {int(ind.get('valor', 0))} = SDDS estricto {int(ind['netas_sdds_estricto'])} "
                f"+ Tesoro {int(ind.get('depositos_tesoro', 0))} "
                f"+ Bopreal {int(ind.get('bopreal_12m', 0))} (M USD)")
    if ikey == "idc" and ind.get("componentes"):
        c, n = ind["componentes"], ind.get("niveles") or {}
        txt = (f"{coma(ind.get('valor'))} σ = precio {coma(c.get('precio'))} · "
               f"volumen {coma(c.get('volumen'))} · asignación {coma(c.get('asignacion'))} "
               f"({ind.get('semaforo', '')})")
        if n:
            txt += (f" — niveles: tasa real {coma(n.get('tasa_real_pp'))} pp · "
                    f"depósitos {coma(n.get('dep_real_ia_pct'))}% i.a. real · "
                    f"holgura {coma(n.get('holgura_pct'))}%")
        return txt
    if ikey == "idm" and ind.get("m3_real_ia") is not None:
        return (f"brecha {coma(ind.get('valor'))} pp = M3 priv. real i.a. "
                f"{coma(ind['m3_real_ia'])}% − M2 priv. real i.a. {coma(ind['m2_real_ia'])}%")
    if ikey == "iai" and ind.get("componentes"):
        c = ind["componentes"]
        partes = [f"ISAC {coma(c.get('isac'))}%", f"BK importados {coma(c.get('bk_importados'))}%"]
        if c.get("patentamientos_comerciales") is not None:
            partes.append(f"patentamientos {coma(c['patentamientos_comerciales'])}%")
        return f"{coma(ind.get('valor'))}% i.a. = " + " · ".join(partes)
    if ikey == "icip" and ind.get("componentes"):
        c = ind["componentes"]
        return (f"{coma(ind.get('valor'))}% i.a. = servicios tech {coma(c.get('servicios_tech'))}% · "
                f"productividad {coma(c.get('productividad'))}%")
    return None


def _gestion_input_txt(ikey, ind):
    """'Valor usado' del modal para gestión: la descomposición del número que
    puntúa (compuestos como el ILCE o el Fondo de Cese exponen componentes)."""
    coma = lambda x: str(x).replace(".", ",")
    if ind.get("detalle_txt"):                       # detalle rico (ej. RIGI oficial)
        return ind["detalle_txt"]
    if ikey == "fal_modernizacion_laboral" and ind.get("componentes"):
        c = ind["componentes"]
        partes = [f"{n} {coma(v)}" for n, v in c.items() if v is not None]
        return f"índice {coma(ind.get('valor'))} = " + " · ".join(partes)
    if ikey == "privatizaciones" and ind.get("etapa_promedio") is not None:
        return (f"etapa promedio {coma(ind['etapa_promedio'])}/4 sobre "
                f"{ind.get('empresas', '?')} empresas de la cartera Ley Bases")
    return None


# ── ITVC (vida cotidiana) — doc 260702, ADR-0018 ──────────────────────────────

AJUSTES_ITVC_PATH = ROOT / "data" / "vida" / "ajustes_itvc.json"
ITVC_BASELINES_PATH = ROOT / "data" / "vida" / "itvc_baselines.json"
ITVC_BASE_MESES = ("2023-10", "2023-11", "2023-12")
ITVC_WINSOR_TOPE = 140.0   # techo de componentes B100 (ADR-0033) — SOLO techo:
                           # un boom (motos 166,7) no compra compensación
                           # ilimitada; las crisis NO se recortan — se señalizan
                           # con el flag de dimensión crítica (ADR-0020)

# Serie transformada (ya rebaseada en descargar_series) → indicador del cinturón
ITVC_SERIES_REBASEADAS = {
    "itvc_alimentos":     "ipc_alimentos",
    "itvc_tarifas":       "peso_tarifas",
    "itvc_ipi":           "mortalidad_pymes",
    "itvc_isac":          "despacho_cemento",
    "itvc_endeudamiento": "endeudamiento_familiar",
}


def _itvc_rebase_movil12(series, skey):
    """Índice base-100 por ACUMULADO MÓVIL de 12 meses (ADR-0024): promedio de
    los últimos 12 meses de la serie vs el promedio de las ventanas móviles que
    terminan en el 4T-2023. Desestacionaliza flujos con calendario fuerte
    (motos: enero ≈ 2× junio) — misma lógica que la carne (CICCRA ya publica
    su PM-12m). Si la serie no alcanza para las ventanas base, devuelve None
    (cae al fallback de baselines)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie if p.get("valor")}
    yms = sorted(vals)

    def ventana(fin):
        i = yms.index(fin) if fin in yms else -1
        if i < 11:
            return None
        win = yms[i - 11:i + 1]
        # 12 meses CONSECUTIVOS (sin huecos): compara el rango real
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) != 11:
            return None
        return sum(vals[k] for k in win) / 12.0

    bases = [v for v in (ventana(f) for f in ITVC_BASE_MESES) if v]
    actual = ventana(yms[-1]) if yms else None
    if not bases or not actual:
        return None
    return round(actual / (sum(bases) / len(bases)) * 100.0, 1)


def _itvc_rebase_de_serie(series, skey, invertido=False, base_meses=None):
    """Índice base-100 del ÚLTIMO punto de una serie vs su promedio 4T-2023.
    En series trimestrales el 4T-2023 es un único punto (2023-10), que coincide
    naturalmente con la base del doc; en mensuales, el promedio oct-nov-dic.
    `base_meses` permite una base DECLARADA distinta cuando la fuente no midió
    el 4T-2023 (ej. IVI: encuesta suspendida 2020-2023, reanudada ene-2024)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie}
    base_vals = [vals[m] for m in (base_meses or ITVC_BASE_MESES) if vals.get(m) is not None]
    if not serie or not base_vals:
        return None
    base = sum(base_vals) / len(base_vals)
    ult = serie[-1]["valor"]
    if not ult or not base:
        return None
    return round((base / ult if invertido else ult / base) * 100.0, 1)


def _itvc_indices(vida_ind, series):
    """Índices base-100 por componente del ITVC (None = componente sin dato)."""
    idx = {}
    for skey, ikey in ITVC_SERIES_REBASEADAS.items():
        serie = series.get(skey) or []
        idx[ikey] = serie[-1]["valor"] if serie else None
    # Rebase directo desde las series oficiales existentes
    idx["brecha_salario_cbt"] = _itvc_rebase_de_serie(series, "brecha_salario_cbt")
    idx["icc_utdt"] = _itvc_rebase_de_serie(series, "icc_utdt")
    idx["pluriempleo"] = _itvc_rebase_de_serie(series, "pluriempleo", invertido=True)
    # Informalidad TRIMESTRAL (52.2_ASDJ, barrido vida 2/13): la 303.1 murió en
    # 2020 pero la 52.2 sigue viva — base = 4T-2023 exacto (punto 2023-10),
    # invertida (menos informalidad = mejora). Reemplaza la excepción anual.
    idx["informalidad"] = _itvc_rebase_de_serie(series, "informalidad", invertido=True)
    # Motos (CAFAM), carne (CICCRA PM-12m) e inseguridad (SNIC anual: su serie
    # emite el total del año en YYYY-12, así el 4T-2023 resuelve al año 2023 —
    # la excepción declarada del doc): rebase de la serie reconstruida.
    # Motos por acumulado móvil 12m (ADR-0024): el flujo mensual crudo tiene
    # estacionalidad fuerte y contra la base fija 4T-2023 mide calendario.
    idx["patentamiento_motos"] = (_itvc_rebase_movil12(series, "patentamiento_motos")
                                  or _itvc_rebase_de_serie(series, "patentamiento_motos"))
    idx["consumo_carne"] = _itvc_rebase_de_serie(series, "consumo_carne")
    # IVI (ADR-0032): base = ene-2024, la primera medición tras la reanudación
    # de la encuesta (suspendida 2020-2023; su ventana de 12 meses captura
    # mayormente el año PRE-mandato, así que aproxima bien el arranque).
    idx["inseguridad"] = _itvc_rebase_de_serie(series, "inseguridad", invertido=True,
                                               base_meses=("2024-01",))
    # Sentimiento digital (ADR-0034): canasta mensual Trends de ventana fija —
    # el cociente intra-consulta es inmune a la renormalización. Invertido:
    # más búsquedas de inflación/precios = más urgencia percibida.
    idx["sentimiento_digital"] = _itvc_rebase_de_serie(series, "sentimiento_digital",
                                                       invertido=True)
    # Fallback: constante 4T-2023 documentada en itvc_baselines.json (con
    # fuente) × valor actual del indicador, si la serie no está disponible.
    try:
        bas = json.loads(ITVC_BASELINES_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        bas = {}
    for ikey, invertido in (("consumo_carne", False), ("inseguridad", True),
                            ("patentamiento_motos", False)):
        if idx[ikey] is not None:
            continue
        b = (bas.get(ikey) or {}).get("valor")
        v = (vida_ind.get(ikey) or {}).get("valor")
        idx[ikey] = (round((b / v if invertido else v / b) * 100.0, 1)
                     if b and isinstance(v, (int, float)) and v else None)
    # WINSORIZACIÓN ASIMÉTRICA (ADR-0033, tratamiento de outliers JRC): los
    # componentes B100 se acotan al TECHO de 140 — un boom puntual (motos
    # 166,7: +67% vs base) no debe comprar compensación ilimitada en la
    # agregación lineal. SIN piso deliberadamente: las crisis (endeudamiento
    # 31,7) no se recortan, se señalizan (flag crítica, ADR-0020). El crudo
    # queda en _winsor para la nota del modal.
    idx["_winsor"] = {}
    for ikey, v in list(idx.items()):
        if ikey.startswith("_") or v is None:
            continue
        if v > ITVC_WINSOR_TOPE:
            idx["_winsor"][ikey] = v
            idx[ikey] = ITVC_WINSOR_TOPE
    return idx


VALIDACION_EXTERNA_PATH = ROOT / "output" / "validacion_externa.json"


def _cargar_validacion():
    try:
        return json.loads(VALIDACION_EXTERNA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _validacion_itvc(bloque, series):
    """Anexa al bloque ITVC la validación externa (ADR-0019 D6): la serie
    mensual del ITVC recalculado SIN su componente ICC (para no ser circular)
    junto a la serie del ICC UTDT, con las correlaciones del estudio
    (scripts/validacion_externa.py — correr ese script actualiza el insumo)."""
    val = _cargar_validacion()
    sin_icc = val.get("serie_itvc_sin_icc") or {}
    icc = {p["fecha"][:7]: p["valor"] for p in (series.get("icc_utdt") or [])}
    comunes = sorted(set(sin_icc) & set(icc))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones", {})
    niveles = corr.get("niveles (ITVC sin ICC vs ICC)") or {}
    difs = corr.get("primeras diferencias (sin ICC)") or {}
    coma = lambda x: str(x).replace(".", ",")
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, sin_icc[m], icc[m]] for m in comunes],
        "plot": "rebase100",
        "titulo": "¿El ITVC acompaña la percepción de la gente?",
        "sub": ("Paso 9 del estándar JRC/OCDE: un índice válido debe co-moverse con variables "
                "externas relacionadas que no lo componen. El ITVC se recalcula sin su componente "
                "de confianza (el ICC pesa 7,5% del índice) para que la comparación no sea "
                "circular, y se contrasta con el ICC de UTDT — percepción del consumidor, "
                "fuente totalmente independiente."),
        "serie_label": "ITVC sin su componente de confianza",
        "externa_label": "ICC (confianza del consumidor, UTDT)",
        "trans_label": "ambas series rebaseadas a 100 en el primer mes",
        "conclusion": (f"Correlación {coma(r_niv)} en niveles y {coma(r_dif)} en los cambios mes "
                       f"a mes: ni redundante (cercana a 1 diría que el índice sobra) ni "
                       f"desconectada (cercana a 0 diría que no capta la experiencia vivida). "
                       f"Las condiciones materiales y el ánimo se mueven juntos, pero miden "
                       f"cosas distintas."),
    }


def _validacion_itcm(bloque):
    """Anexa al bloque ITCM su validación externa: la serie mensual del índice
    (reconstruida por el estudio desde las series de componentes) contra el
    riesgo país (EMBI) — correlación negativa esperada."""
    val = _cargar_validacion()
    serie = val.get("serie_itcm") or {}
    riesgo = val.get("riesgo_pais_mensual") or {}
    comunes = sorted(set(serie) & set(riesgo))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones_itcm", {})
    niveles = corr.get("niveles (ITCM vs riesgo país)") or {}
    difs = corr.get("primeras diferencias (ITCM vs riesgo)") or {}
    coma = lambda x: str(x).replace(".", ",")
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], riesgo[m]] for m in comunes],
        "plot": "minmax_inv",
        "titulo": "¿El ITCM se mueve con el precio del riesgo argentino?",
        "sub": ("El contraste natural del cinturón macro es el mercado: si la tensión "
                "macroeconómica afloja, la Argentina debería pagar menos por su deuda. El ITCM "
                "se reconstruye mes a mes desde las series de diez de sus doce componentes "
                "(sin el capítulo inversión ni los ajustes del analista: el nivel puede diferir "
                "del publicado — lo que valida es su evolución) y se compara con el riesgo "
                "país (EMBI), que no integra el índice. La correlación esperada es negativa: "
                "más ITCM (menos tensión), menos riesgo país."),
        "serie_label": "ITCM (reconstrucción mensual)",
        "externa_label": "riesgo país (EMBI, invertido)",
        "trans_label": "series normalizadas al rango del período; el riesgo país se muestra invertido",
        "conclusion": (f"Correlación {coma(r_niv)} en niveles y {coma(r_dif)} en los cambios mes "
                       f"a mes: el signo negativo es exactamente el esperado — cuando el índice "
                       f"sube (la macro afloja), el mercado cobra menos por el riesgo argentino. "
                       f"En el gráfico el riesgo país se muestra invertido para leer el "
                       f"co-movimiento en la misma dirección."),
    }


def _validacion_cruzada(informe):
    """Matriz de validación cruzada (ADR-0031, tercer pilar de robustez): los
    tres índices reconstruidos contra los DOS contrastes externos a la vez.
    Validez convergente + discriminante: cada índice debe correlacionar más
    fuerte con su par teórico (ITCM/ITCG ↔ riesgo país · ITVC ↔ ICC) que con
    el contraste ajeno — la prueba de que no miden "todo junto"."""
    try:
        bloques = {
            "ITCM": informe["cinturones"]["macro"]["itcm"]["validacion"]["pares"],
            "ITCG": informe["cinturones"]["gestion"]["itcg"]["validacion"]["pares"],
            "ITVC": informe["cinturones"]["vida_cotidiana"]["itvc"]["validacion"]["pares"],
        }
    except (KeyError, TypeError):
        return
    indices = {k: {p[0]: p[1] for p in v} for k, v in bloques.items()}
    externas = {"riesgo": {p[0]: p[2] for p in bloques["ITCM"]},
                "merval": {p[0]: p[2] for p in bloques["ITCG"]},
                "icc": {p[0]: p[2] for p in bloques["ITVC"]}}

    def _r(a, b):
        comunes = sorted(set(a) & set(b))
        if len(comunes) < 12:
            return None, len(comunes)
        return (round(statistics.correlation([a[m] for m in comunes],
                                             [b[m] for m in comunes]), 2), len(comunes))

    PAR_PROPIO = {"ITCM": "riesgo", "ITCG": "merval", "ITVC": "icc"}
    filas = []
    for ik in ("ITCM", "ITCG", "ITVC"):
        fila = {"indice": ik, "propio": PAR_PROPIO[ik]}
        for ek, ext in externas.items():
            r, n = _r(indices[ik], ext)
            fila[ek] = {"r": r, "n": n}
        filas.append(fila)
    if any(f[e]["r"] is None for f in filas for e in ("riesgo", "merval", "icc")):
        return
    fmt = lambda r: ("+" if r > 0 else "") + str(r).replace(".", ",")
    f_itcm, f_itcg, f_itvc = filas
    informe["validacion_cruzada"] = {
        "filas": filas,
        "externas": [["riesgo", "Riesgo país (EMBI)"], ["merval", "Merval en USD"],
                     ["icc", "Confianza del consumidor (ICC UTDT)"]],
        "titulo": "¿Cada índice mide lo suyo?",
        "sub": ("Los tres índices se reconstruyen mes a mes y se comparan contra los tres "
                "contrastes externos a la vez — cada uno tiene el propio: la macroeconomía "
                "(ITCM) con el precio del riesgo argentino, la gestión (ITCG) con el valor de "
                "las empresas en dólares, la vida cotidiana (ITVC) con la confianza del "
                "consumidor. Si cada índice mide su propio terreno, debería correlacionar con "
                "su par natural al menos tanto como con los ajenos. Es la prueba clásica de "
                "que un indicador no mide \"todo junto\"."),
        "conclusion": (f"Los tres pares propios dan el signo esperado y correlaciones fuertes: "
                       f"ITCM {fmt(f_itcm['riesgo']['r'])} con el riesgo país, ITCG "
                       f"{fmt(f_itcg['merval']['r'])} con el Merval en dólares, ITVC "
                       f"{fmt(f_itvc['icc']['r'])} con la confianza del consumidor. Las celdas "
                       f"cruzadas son del mismo orden (la gestión también correlaciona "
                       f"{fmt(f_itcg['riesgo']['r'])} con el riesgo país): en una muestra de "
                       f"~30 meses en la que toda la economía se movió junta, la matriz separa "
                       f"parcialmente — se declara como límite, no se esconde."),
    }


def _validacion_itcg(bloque):
    """Anexa al bloque ITCG su validación externa CONTRA SU PAR PROPIO
    (ADR-0031): el Merval en dólares — el mercado de acciones pricea la
    transformación estructural (convergente, positiva esperada). El riesgo
    país queda como par exclusivo del ITCM (se cruzan en la matriz). El
    contraste con el ICG UTDT sigue como hallazgo DISCRIMINANTE en la
    conclusión: la ejecución se acumula, la popularidad cicla."""
    val = _cargar_validacion()
    serie = val.get("serie_itcg") or {}
    merval = val.get("merval_usd_mensual") or {}
    comunes = sorted(set(serie) & set(merval))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones_itcg", {})
    niveles = corr.get("niveles (ITCG vs Merval USD)") or {}
    difs = corr.get("primeras diferencias (ITCG vs Merval USD)") or {}
    icg_niv = (corr.get("niveles (ITCG vs ICG)") or {}).get("r")
    coma = lambda x: str(x).replace(".", ",")
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    icg_txt = ""
    if icg_niv is not None:
        icg_txt = (f" El contraste discriminante también informa: la confianza en el gobierno "
                   f"(ICG UTDT) diverge del ITCG ({coma(icg_niv)}) — la ejecución se acumula "
                   f"mientras el capital político sigue su propio ciclo. El índice mide "
                   f"gestión, no popularidad.")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], merval[m]] for m in comunes],
        "plot": "minmax",
        "titulo": "¿La transformación se pricea en el valor de las empresas?",
        "sub": ("El contraste natural del cinturón de gestión es el capital de riesgo: si la "
                "agenda de reformas efectivamente se ejecuta, las empresas argentinas deberían "
                "valer más en dólares. El ITCG se reconstruye mes a mes desde las series de sus "
                "componentes (sin los ajustes del analista: el nivel puede diferir del publicado "
                "— lo que valida es su evolución) y se compara con el índice Merval medido en "
                "dólares (cierre mensual sobre el contado con liquidación), que no integra el "
                "índice. La correlación esperada es positiva."),
        "serie_label": "ITCG (reconstrucción mensual)",
        "externa_label": "Merval en dólares",
        "trans_label": "series normalizadas al rango del período",
        "conclusion": (f"Correlación {coma(r_niv)} en niveles: cuando la ejecución de reformas "
                       f"avanza, el mercado revaloriza a las empresas argentinas.{icg_txt}"),
    }


def _scoring_vida_itvc(c, series):
    """Vida cotidiana se puntúa con el ITVC-B100: cada componente es un índice
    rebaseado a 100 = promedio 4T-2023, agregado con los pesos del doc 260702.
    La tensión del cinturón y el aporte por indicador usan el mapeo lineal
    5 − (índice − 100) × 0,2 (topeado a 0-10)."""
    from datetime import datetime as _dt
    indices = _itvc_indices(c["indicadores"], series)
    winsorizados = indices.pop("_winsor", {})
    ajustes = itvc.cargar_ajustes(AJUSTES_ITVC_PATH, _dt.now().strftime("%Y-%m"))
    resultado = itvc.calcular_itvc(indices, ajustes)
    c["itvc"] = resultado
    if resultado:
        c["score"] = itvc.tension_de_itvc(resultado["valor"])
        c["estado"] = _estado(c["score"])
        try:
            resultado["robustez"] = sensibilidad.robustez_compacta(
                resultado, None, itvc.tension_de_itvc)
        except Exception as e:
            print(f"[WARN] robustez ITVC: {e}")
        _marcar_dimensiones_criticas(resultado, UMBRAL_CRITICO_BASE100)
        _validacion_itvc(resultado, series)

    ajustados = {a["indicador"]: a for a in (resultado or {}).get("ajustes_aplicados", [])}
    por_ind = {}
    if resultado:
        for dkey, dim in resultado["dimensiones"].items():
            for ikey, info in dim["indicadores"].items():
                por_ind[ikey] = (dkey, info)
    en_itvc = {k for d in itvc.DIMENSIONES_ITVC.values() for k in d["indicadores"]}
    coma = lambda x: str(x).replace(".", ",")
    for ikey, ind in c["indicadores"].items():
        aporte = formula = nota = None
        if ikey in por_ind:
            dkey, info = por_ind[ikey]
            ind["en_indice"] = True
            ind["dimension"] = dkey
            ind["indice_itvc"] = info["puntaje_aplicado"]
            ind["peso_efectivo"] = info["peso_efectivo"]
            aporte = itvc.tension_de_itvc(info["puntaje_aplicado"])
            # bases DECLARADAS distintas del 4T-2023 (fuente sin medición en la base del doc)
            base_lbl = {"inseguridad": "ene-2024 (base declarada: la encuesta se reanudó ese mes)"} \
                .get(ikey, "4T-2023")
            formula = (f"Índice base-100 vs {base_lbl}: {coma(info['puntaje_aplicado'])} "
                       f"(100 = arranque del mandato; más = mejora); pesa "
                       f"{coma(round(info['peso_efectivo'] * 100, 1))}% del ITVC. "
                       f"Tensión = 5 − (índice − 100) × 0,2.")
            if ikey in winsorizados:
                nota = (f"Winsorizado (tratamiento de outliers): índice crudo "
                        f"{coma(winsorizados[ikey])} acotado al techo de {coma(ITVC_WINSOR_TOPE)} "
                        f"— un boom puntual de un componente no compra compensación "
                        f"ilimitada en el promedio. El tope es solo hacia arriba: las "
                        f"caídas no se recortan, se señalizan como dimensión crítica.")
            if ikey in ajustados:
                aj = ajustados[ikey]
                nota = f"Ajuste del analista: índice {coma(aj['de'])} → {coma(aj['a'])}. {aj.get('justificacion', '')}"
        else:
            ind["en_indice"] = ikey in en_itvc     # del índice pero sin dato
            if ikey in itvc.INDICADORES_CONTEXTO:
                ind["en_indice"] = False
            if ind["en_indice"] is False:
                nota = VIDA_CONTEXTO
        ind["aporte_score"] = aporte
        ind["aporte_formula"] = formula
        ind["aporte_nota"] = nota


# Indicadores macro OCULTOS del snapshot (ADR-0022): siguen en la pipeline
# (colector, cache y series — son insumos del IdC/IDM/TCRM y del crédito
# real), pero no se publican como tiles: su única señal no redundante entra
# al índice vía credito_privado.
MACRO_OCULTOS = {"badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"}


def aplicar_scoring(informe, series):
    """Anota cada indicador con su aporte de tensión (0–10) y el mapeo que lo
    explica, y cada cinturón con cómo se compone su score."""
    for ckey, c in informe["cinturones"].items():
        c["score_explicacion"] = SCORE_EXPLICACION.get(ckey, "")
        if ckey == "macro":
            for oculto in MACRO_OCULTOS:
                c["indicadores"].pop(oculto, None)
            _scoring_indice(c, "itcm", itcm, MACRO_CONTEXTO, _macro_input_txt)
            if c.get("itcm"):
                _validacion_itcm(c["itcm"])
            continue
        if ckey == "gestion":
            _scoring_indice(c, "itcg", itcg, GESTION_CONTEXTO, _gestion_input_txt)
            if c.get("itcg"):
                _validacion_itcg(c["itcg"])
            continue
        if ckey == "vida_cotidiana":
            _scoring_vida_itvc(c, series)
            continue
        for ikey, ind in c["indicadores"].items():
            aporte = formula = nota = None
            if ikey in SCORING:
                spec = SCORING[ikey]
                fn, mapa = spec[0], spec[1]
                campo = spec[2] if len(spec) > 2 else "valor"   # input alternativo
                entrada = ind.get(campo)
                if isinstance(entrada, (int, float)):
                    aporte = _clamp10(fn(float(entrada)))
                    formula = mapa
                    if campo == "var_real_12m":                  # mostrar el input real, no el stock
                        ind["aporte_input_txt"] = f"{entrada:+.1f}% interanual real (no el stock nominal)".replace(".", ",")
                elif ckey == "vida_cotidiana":
                    nota = VIDA_CONTEXTO                          # input ausente → contexto
            elif ckey == "vida_cotidiana":
                nota = VIDA_CONTEXTO
            ind["aporte_score"] = aporte
            ind["aporte_formula"] = formula
            ind["aporte_nota"] = nota
    return informe


def _val_en(serie, objetivo_ym):
    """Último valor de `serie` (lista {fecha, valor}) con mes <= objetivo (YYYY-MM)."""
    cand = [d for d in serie if d["fecha"][:7] <= objetivo_ym]
    return cand[-1]["valor"] if cand else (serie[0]["valor"] if serie else None)


def var_real_credito_12m(cc_serie, ipc_serie):
    """Variación interanual REAL del crédito de consumo, deflactada por IPC.
    Ancla al último mes de IPC disponible para comparar exactamente el mismo
    período en ambas series. Devuelve % real o None si faltan datos."""
    if not cc_serie or not ipc_serie:
        return None
    anchor = ipc_serie[-1]["fecha"][:7]                  # ej '2026-03'
    prev = f"{int(anchor[:4]) - 1}{anchor[4:]}"          # mismo mes, año previo
    cc_now, cc_old = _val_en(cc_serie, anchor), _val_en(cc_serie, prev)
    ipc_now, ipc_old = ipc_serie[-1]["valor"], _val_en(ipc_serie, prev)
    if not all(isinstance(x, (int, float)) and x for x in (cc_now, cc_old, ipc_now, ipc_old)):
        return None
    return round(((cc_now / cc_old) / (ipc_now / ipc_old) - 1) * 100, 1)


def _carry_forward(enriquecido, previo):
    """Si una fuente falla y un indicador de vida viene sin valor (None), mantener
    el último dato publicado en lugar de perderlo. Evita que un outage puntual
    (ej. SNIC, cuyo dato es anual y sin novedad) haga caer el indicador del score.
    `previo` = indicadores de vida del snapshot publicado anterior."""
    for key, ind in enriquecido.items():
        if ind.get("valor") is None and key in previo and previo[key].get("valor") is not None:
            prev = previo[key]
            ind["valor"] = prev.get("valor")
            ind["fecha_dato"] = prev.get("fecha_dato")
            if prev.get("fuente"):
                ind["fuente"] = prev["fuente"]
            print(f"[carry-forward] vida.{key}: sin dato nuevo, se mantiene {prev.get('valor')} ({prev.get('fecha_dato')})")
    return enriquecido


def main():
    informe = json.loads((OUT / "informe.json").read_text(encoding="utf-8"))
    series = build_series()

    # Snapshot publicado anterior → fuente para carry-forward ante outages.
    prev_vida = {}
    prev_path = DATA / "informe.json"
    if prev_path.exists():
        try:
            prev_snap = json.loads(prev_path.read_text(encoding="utf-8"))
            prev_vida = prev_snap["cinturones"]["vida_cotidiana"]["indicadores"]
        except (json.JSONDecodeError, KeyError):
            prev_vida = {}

    vida_files = sorted(glob.glob(str(ROOT / "scripts" / "vida_cotidiana" / "data" / "vida_cotidiana_*.json")))
    if vida_files:
        raw = json.loads(Path(vida_files[-1]).read_text(encoding="utf-8"))
        enriquecido = build_vida(raw)
        if enriquecido:
            enriquecido = _carry_forward(enriquecido, prev_vida)
            vida = informe["cinturones"]["vida_cotidiana"]
            vida["indicadores"] = enriquecido
            vida["fuente_enriquecida"] = os.path.basename(vida_files[-1])
            # Endeudamiento: scoreable vía variación interanual real del crédito.
            real = var_real_credito_12m(
                raw.get("bcra", {}).get("credito_consumo_serie"), series.get("ipc_nivel"))
            if real is not None and "endeudamiento_familiar" in enriquecido:
                enriquecido["endeudamiento_familiar"]["var_real_12m"] = real
            # Inseguridad: la card muestra el IVI mensual (LICIP-UTDT), la
            # métrica del ITVC desde el ADR-0032. El SNIC anual (denuncias
            # registradas) queda como contraste declarado en el detalle.
            ivi = series.get("inseguridad") or []
            if ivi and enriquecido.get("inseguridad"):
                ins = enriquecido["inseguridad"]
                snic_txt = ""
                v_snic = ins.get("valor")
                if isinstance(v_snic, (int, float)) and v_snic > 10000:
                    snic_txt = (f" — contraste SNIC (denuncias registradas, año "
                                f"{ins.get('fecha_dato')}): "
                                f"{format(int(v_snic), ',').replace(',', '.')} hechos")
                ult = ivi[-1]
                ins.update({
                    "valor": ult["valor"],
                    "unidad": "% de hogares víctimas (últimos 12 meses)",
                    "fuente": "UTDT — Índice de Victimización (LICIP)",
                    "fecha_dato": ult["fecha"][:7],
                    "detalle_txt": ("Encuesta mensual de victimización en 40 centros urbanos: "
                                    "incluye los delitos NO denunciados (la cifra negra)"
                                    + snic_txt),
                })

    informe = sanitizar_fuentes(informe)
    informe = aplicar_scoring(informe, series)
    informe = recomputar_vida_y_global(informe)
    _validacion_cruzada(informe)   # matriz discriminante (ADR-0031): necesita los 3 bloques

    # Red de seguridad: persistir el valor de cada indicador y construir su serie
    # histórica mes a mes (los que no tienen serie oficial la arman así).
    store = acumular_historico(informe)
    series = fusionar_historico(series, store)

    (DATA / "informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "series.json").write_text(
        json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot escrito en {DATA} · histórico: {len(store)} indicadores en {HISTORICO_PATH.name}")


if __name__ == "__main__":
    main()
