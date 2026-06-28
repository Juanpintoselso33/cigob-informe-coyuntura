"""Arma el snapshot de datos que consume la web del informe de coyuntura.

Lee output/informe.json + el ultimo vida_cotidiana_*.json + output/series/*.csv
y escribe web/src/data/informe.json (con vida cotidiana enriquecido a ~13
indicadores automaticos) y web/src/data/series.json.
"""
import csv, glob, json, os, re, sys
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
         "canastas (RIPTE/CBT)", "INDEC", bs.get("fecha"))
    al = indec.get("ipc_alimentos", {})
    _add(out, "ipc_alimentos", round(al.get("variacion_mensual_pct", 0), 2),
         "% m/m", "INDEC serie 146.3", al.get("fecha"))
    cc = bcra.get("credito_consumo_total", {})
    # El crédito de consumo viene en millones de pesos; pasar a billones para
    # que el número no sea gigante (43.560.544 millones = 43,56 billones).
    cc_val = cc.get("valor")
    _add(out, "endeudamiento_familiar",
         round(cc_val / 1e6, 2) if isinstance(cc_val, (int, float)) else cc_val,
         "billones de pesos (consumo)", "BCRA API v4.0", cc.get("fecha"))
    reg = indec.get("ipc_regulados", {})
    _add(out, "peso_tarifas", round(reg.get("variacion_mensual_pct", 0), 2),
         "% m/m regulados", "INDEC", reg.get("fecha"))
    carne = ciccra.get("consumo_carne_per_capita", {})
    _add(out, "consumo_carne", carne.get("valor"),
         "kg/hab/año", "CICCRA", carne.get("fecha"))
    inf = indec.get("informalidad_anual", {})
    _add(out, "informalidad", round(inf.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", inf.get("fecha"))
    ipi = indec.get("ipi", {})
    _add(out, "mortalidad_pymes", round(ipi.get("variacion_mensual_pct", 0), 2),
         "% m/m (IPI)", "INDEC", ipi.get("fecha"))
    isac = indec.get("isac", {})
    _add(out, "despacho_cemento", round(isac.get("valor", 0), 1),
         "índice ISAC", "INDEC", isac.get("fecha"))
    sub = indec.get("subocupacion_demandante", {})
    _add(out, "pluriempleo", round(sub.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", sub.get("fecha"))
    seg = snic.get("inseguridad_snic", {})
    _add(out, "inseguridad", seg.get("total_hechos"),
         "hechos/año", "SNIC", str(seg.get("anio")))
    icc = utdt.get("icc_utdt", {})
    _add(out, "icc_utdt", round(icc.get("valor", 0), 1),
         "índice", "UTDT", icc.get("fecha"))
    sd = trends.get("sentimiento_digital", {}).get("interes_relativo", {})
    if sd:
        _add(out, "sentimiento_digital", round(sum(sd.values()) / len(sd), 1),
             "interés 0–100", "Google Trends", ts)
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
        # Deduplicar por fecha: algunos indicadores (ej. ipc_total) se descargan
        # en más de un CSV de cinturón con la misma serie INDEC, lo que produciría
        # puntos repetidos en el sparkline y la tabla histórica. Los valores de una
        # misma fecha son idénticos, así que colapsar a uno por fecha.
        por_fecha = {p["fecha"]: p for p in series[ind]}
        series[ind] = sorted(por_fecha.values(), key=lambda p: p["fecha"])
    # Alias: algunos indicadores del informe tienen su serie historica bajo otra
    # clave en los CSV. Exponer la serie tambien bajo la clave del indicador para
    # que el sparkline y el modal la encuentren.
    alias = {
        "despacho_cemento": "isac_construccion",
        "peso_tarifas": "ipc_regulados",
        "saldo_comercial_12m": "saldo_comercial",
    }
    for ind_key, serie_key in alias.items():
        if serie_key in series and ind_key not in series:
            series[ind_key] = series[serie_key]
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

GESTION_MAPA = ("10 × (1 − avance/100): a mayor avance ejecutado, menor tensión. "
                "100% → 0 · 50% → 5 · 0% → 10.")

VIDA_CONTEXTO = ("Indicador de contexto. No se pudo calcular su variación interanual real "
                 "(falta la serie de crédito), por lo que no incide en el score en esta corrida.")

MACRO_CONTEXTO = "Indicador de contexto — no integra el ITCM (paramétrica CIGOB may-2026)."

SCORE_EXPLICACION = {
    "macro":          ("ITCM (índice paramétrico 0–100, mayor = menos tensión) ponderado por 6 dimensiones: "
                       "estabilidad monetaria 26%, viabilidad fiscal-comercial 24%, financiamiento 16%, "
                       "actividad 11%, competitividad externa 11%, inversión 12%. La tensión del cinturón es (100 − ITCM) / 10."),
    "politica":       "Promedio simple de la tensión (0–10) de sus indicadores. Mayor = más tensión en el capital político.",
    "gestion":        "Promedio simple de la tensión de sus 12 reformas: a mayor avance ejecutado, menor tensión.",
    "vida_cotidiana": "Promedio simple de la tensión (0–10) de sus indicadores con fórmula validada. Mayor = más tensión en el bolsillo y la calle.",
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
    """Vida cotidiana se puntúa ahora con sus propios indicadores (no el legacy de
    3 indicadores del colector): su score es el promedio de los aportes calculados
    acá. Recalculamos su score + estado y, en consecuencia, el score global
    ponderado, para que el snapshot sea internamente coherente.
    (El colector vida_cotidiana.py sigue emitiendo el score legacy en su cache;
    esta es la fuente de verdad del snapshot publicado.)"""
    vida = informe["cinturones"]["vida_cotidiana"]
    aportes = [i["aporte_score"] for i in vida["indicadores"].values()
               if i.get("aporte_score") is not None]
    if aportes:
        vida["score"] = round(sum(aportes) / len(aportes), 1)
        vida["estado"] = _estado(vida["score"])

    num = sum(c["score"] * PESOS_CINTURONES.get(k, 0.0)
              for k, c in informe["cinturones"].items())
    den = sum(PESOS_CINTURONES.get(k, 0.0) for k in informe["cinturones"])
    if den:
        informe["score_global"] = round(num / den, 1)
    return informe


def _scoring_macro_itcm(c):
    """Macro se puntúa con el ITCM que computa el colector: acá solo se traduce
    cada puntaje 0-100 a tensión equivalente (para la semántica 0-10 del modal)
    y se anota la tabla de bandas + peso en el índice. Los indicadores con
    en_indice=false son contexto y no aportan."""
    ajustes = {a["indicador"]: a for a in (c.get("itcm") or {}).get("ajustes_aplicados", [])}
    for ikey, ind in c["indicadores"].items():
        aporte = formula = nota = None
        p = ind.get("puntaje_itcm")
        if ind.get("en_indice") and isinstance(p, (int, float)):
            aporte = round((100 - p) / 10, 1)
            peso = ind.get("peso_efectivo")
            peso_txt = f"; pesa {peso * 100:.1f}%".replace(".", ",") + " del ITCM" if peso else ""
            formula = (f"Banda ITCM: {itcm.texto_bandas(ikey)} "
                       f"(puntos 0–100; puntaje {p}{peso_txt})")
            if ikey in ajustes:
                aj = ajustes[ikey]
                origen = "automático" if aj.get("origen") == "automatico" else "del analista"
                nota = f"Ajuste {origen}: banda {aj['de']} → {aj['a']}. {aj.get('justificacion', '')}"
        elif ind.get("en_indice") is False:
            nota = MACRO_CONTEXTO
        ind["aporte_score"] = aporte
        ind["aporte_formula"] = formula
        ind["aporte_nota"] = nota
        ind["aporte_input_txt"] = _macro_input_txt(ikey, ind)


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
        c = ind["componentes"]
        return (f"índice {coma(ind.get('valor'))} = precio {coma(c.get('precio'))} · "
                f"volumen {coma(c.get('volumen'))} · asignación {coma(c.get('asignacion'))} "
                f"({ind.get('semaforo', '')})")
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


def aplicar_scoring(informe):
    """Anota cada indicador con su aporte de tensión (0–10) y el mapeo que lo
    explica, y cada cinturón con cómo se compone su score."""
    for ckey, c in informe["cinturones"].items():
        c["score_explicacion"] = SCORE_EXPLICACION.get(ckey, "")
        if ckey == "macro":
            _scoring_macro_itcm(c)
            continue
        for ikey, ind in c["indicadores"].items():
            aporte = formula = nota = None
            avance = ind.get("avance_pct")
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
            elif isinstance(avance, (int, float)):
                aporte = _clamp10(10.0 * (1.0 - float(avance) / 100.0))
                formula = GESTION_MAPA
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
                raw.get("bcra", {}).get("credito_consumo_serie"), series.get("ipc_total"))
            if real is not None and "endeudamiento_familiar" in enriquecido:
                enriquecido["endeudamiento_familiar"]["var_real_12m"] = real

    informe = sanitizar_fuentes(informe)
    informe = aplicar_scoring(informe)
    informe = recomputar_vida_y_global(informe)

    (DATA / "informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "series.json").write_text(
        json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot escrito en {DATA}")


if __name__ == "__main__":
    main()
